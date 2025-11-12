from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, Form
from pydantic import BaseModel, Field

from packages.kernel_common.deps import require_auth
from packages.kernel_common.logging import configure_logging

logger = configure_logging("analyze-service")

app = FastAPI(
    title="Dyocense Analyze Service",
    version="0.6.0",
    description="Sales data ingestion, schema inference and first insight generation for SMB flow.",
)


# ----------------------------- API MODELS ---------------------------------- #

class MappingSuggestion(BaseModel):
    date: Optional[str] = Field(None, description="Detected date column name")
    amount: Optional[str] = Field(None, description="Detected sales amount column name")
    product: Optional[str] = Field(None, description="Detected product/sku column name")
    candidates: Dict[str, List[str]] = Field(default_factory=dict, description="Other candidate columns by role")


class Insight(BaseModel):
    id: str
    title: str
    summary: str
    metric: float | int | None
    confidence: float | None


class AnalyzeResponse(BaseModel):
    generated_at: str
    rows: int
    columns: int
    mapping: MappingSuggestion
    preview: List[Dict[str, Any]]
    insights: List[Insight]
    missing_values: int
    notes: List[str] = Field(default_factory=list)


# --------------------------- IMPLEMENTATION -------------------------------- #

DATE_HINTS = {"date", "dt", "day", "timestamp", "order_date", "invoice_date"}
AMOUNT_HINTS = {"amount", "sales", "revenue", "net_sales", "price", "total"}
PRODUCT_HINTS = {"product", "item", "sku", "name"}


def _detect_mapping(df: pd.DataFrame) -> MappingSuggestion:
    lower_cols = {c.lower(): c for c in df.columns}

    def pick(hints: set[str]) -> Optional[str]:
        for h in hints:
            if h in lower_cols:
                return lower_cols[h]
        # fallback: contains the hint as substring
        for raw in df.columns:
            l = raw.lower()
            if any(h in l for h in hints):
                return raw
        return None

    date_col = pick(DATE_HINTS)
    amount_col = pick(AMOUNT_HINTS)
    product_col = pick(PRODUCT_HINTS)

    candidates: Dict[str, List[str]] = {
        "date": [c for c in df.columns if any(h in c.lower() for h in DATE_HINTS)],
        "amount": [c for c in df.columns if any(h in c.lower() for h in AMOUNT_HINTS)],
        "product": [c for c in df.columns if any(h in c.lower() for h in PRODUCT_HINTS)],
    }

    return MappingSuggestion(
        date=date_col,
        amount=amount_col,
        product=product_col,
        candidates=candidates,
    )


def _basic_insights(df: pd.DataFrame, mapping: MappingSuggestion) -> List[Insight]:
    insights: List[Insight] = []
    try:
        if mapping.amount and mapping.date and mapping.product and mapping.amount in df.columns:
            # Convert date
            ts = pd.to_datetime(df[mapping.date], errors="coerce")
            amt = pd.to_numeric(df[mapping.amount], errors="coerce")
            prod = df[mapping.product].astype(str)
            working = pd.DataFrame({"date": ts, "amount": amt, "product": prod})
            working = working.dropna(subset=["date", "amount"])  # keep rows with valid date & numeric amount

            if not working.empty:
                total_sales = float(working["amount"].sum())
                insights.append(
                    Insight(
                        id="total_sales",
                        title="Total Sales",
                        summary=f"Aggregate sales amount across {len(working)} valid rows.",
                        metric=round(total_sales, 2),
                        confidence=1.0,
                    )
                )
                # Trend: compare last period vs previous (naive)
                by_date = working.groupby(working["date"].dt.date)["amount"].sum().sort_index()
                if len(by_date) >= 2:
                    last = by_date.iloc[-1]
                    prev = by_date.iloc[-2]
                    if prev != 0:
                        change_pct = (last - prev) / prev * 100.0
                        insights.append(
                            Insight(
                                id="trend_last_period",
                                title="Latest Period Trend",
                                summary=f"Sales {('increased' if change_pct >= 0 else 'decreased')} {abs(change_pct):.1f}% vs previous period.",
                                metric=round(change_pct, 2),
                                confidence=0.6,
                            )
                        )
                # Top product
                top_prod = working.groupby("product")["amount"].sum().sort_values(ascending=False).head(1)
                if len(top_prod):
                    insights.append(
                        Insight(
                            id="top_product",
                            title="Top Product",
                            summary=f"'{top_prod.index[0]}' leads sales with {top_prod.iloc[0]:.2f} units.",
                            metric=float(top_prod.iloc[0]),
                            confidence=0.7,
                        )
                    )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Insight generation failed: %s", exc)
    return insights


def _load_sample() -> pd.DataFrame:
    # Reuse restaurant_menu.csv if exists as sample revenue data
    import os
    root = os.getenv("DYOCENSE_ROOT", "./")
    candidates = [
        f"{root}/examples/restaurant_inventory.csv",  # has product-like columns
        f"{root}/examples/restaurant_menu.csv",
        f"{root}/examples/sample_inventory_data.csv",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return pd.read_csv(path)
            except Exception:
                continue
    raise FileNotFoundError("No sample dataset found in examples directory")


@app.post("/v1/analyze", response_model=AnalyzeResponse)
async def analyze(
    file: UploadFile | None = File(None),
    use_sample: bool = Form(False),
    # Optional mapping overrides supplied by client UI
    date_col: Optional[str] = Form(None),
    amount_col: Optional[str] = Form(None),
    product_col: Optional[str] = Form(None),
    connector_id: Optional[str] = Form(None),
    data_type: Optional[str] = Form(None),
    identity: dict = Depends(require_auth),
) -> AnalyzeResponse:
    """Ingest sales data, infer schema and produce first insights.

    Either a CSV/Excel file must be provided or use_sample=true.
    """
    if not use_sample and file is None:
        raise HTTPException(status_code=400, detail="Provide a file or set use_sample=true")

    try:
        if use_sample:
            df = _load_sample()
            notes = ["Loaded built-in sample dataset"]
        else:
            if file is None:
                raise HTTPException(status_code=400, detail="File missing")
            content = await file.read()
            filename = file.filename or "uploaded"
            lower_name = filename.lower()
            if lower_name.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(content))
            elif lower_name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(io.BytesIO(content))
            else:
                raise HTTPException(status_code=415, detail="Unsupported file type; upload CSV or XLSX")
            notes = [f"Parsed file '{filename}'"]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {exc}")

    # Basic limits
    if df.shape[0] == 0:
        raise HTTPException(status_code=400, detail="Empty dataset")
    if df.shape[1] > 1000:
        notes.append("Dataset has unusually high column count")

    mapping = _detect_mapping(df)
    # Apply overrides if present
    if date_col:
        mapping.date = date_col
    if amount_col:
        mapping.amount = amount_col
    if product_col:
        mapping.product = product_col
    # Ensure keys are strings for Pydantic model typing
    preview_records = df.head(10).to_dict(orient="records")
    preview_rows: List[Dict[str, Any]] = [
        {str(k): v for k, v in row.items()} for row in preview_records
    ]
    missing_values = int(df.isna().sum().sum())
    insights = _basic_insights(df, mapping)

    resp = AnalyzeResponse(
        generated_at=datetime.now(tz=timezone.utc).isoformat(),
        rows=int(df.shape[0]),
        columns=int(df.shape[1]),
        mapping=mapping,
        preview=preview_rows,
        insights=insights,
        missing_values=missing_values,
        notes=notes,
    )

    # ------------------------------------------------------------------
    # Optional persistence into connectors.connector_data if connector_id provided
    # ------------------------------------------------------------------
    try:
        if connector_id:
            inferred_type = data_type or _infer_data_type(df)
            _persist_connector_data(
                tenant_id=identity.get("tenant_id"),
                connector_id=connector_id,
                data_type=inferred_type,
                # Cast records to dict[str, Any] for typing consistency
                records=[{str(k): v for k, v in r.items()} for r in df.to_dict(orient="records")],
                source_notes=notes,
            )
            resp.notes.append(f"Persisted {df.shape[0]} records as '{inferred_type}' for connector {connector_id}")
    except Exception as persist_exc:
        # Non-fatal: append note and continue
        resp.notes.append(f"Persistence skipped: {persist_exc}")

    logger.info(
        "Analyze completed rows=%d cols=%d tenant=%s insights=%d",
        resp.rows,
        resp.columns,
        identity.get("tenant_id"),
        len(resp.insights),
    )
    return resp


# ----------------------------------------------------------------------
# Persistence helpers
# ----------------------------------------------------------------------
def _infer_data_type(df: "pd.DataFrame") -> str:
    """Heuristically infer data_type from columns.

    Priority order based on presence of distinguishing columns.
    This is intentionally lightweight; improve as needed.
    """
    cols = {c.lower() for c in df.columns}
    if {"order_id", "order", "total"} & cols or "order_id" in cols:
        return "orders"
    if {"sku", "stock", "quantity", "qty"} & cols:
        return "inventory"
    if {"customer_id", "email", "first_name", "last_name"} & cols:
        return "customers"
    if {"product_id", "price", "category"} & cols:
        return "products"
    return "generic"


def _persist_connector_data(
    tenant_id: Optional[str],
    connector_id: str,
    data_type: str,
    records: list[dict[str, Any]],
    source_notes: list[str],
) -> None:
    """Insert or upsert data into connectors.connector_data via postgres backend pool."""
    if not tenant_id:
        raise ValueError("tenant_id missing from identity for persistence")
    from packages.kernel_common.persistence_v2 import get_backend, PostgresBackend
    backend = get_backend()
    if not isinstance(backend, PostgresBackend):
        raise RuntimeError("PostgresBackend required for connector data persistence")
    from psycopg2.extras import Json
    with backend.get_connection() as conn:  # type: ignore[attr-defined]
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO connectors.connector_data
                (tenant_id, connector_id, data_type, data, record_count, synced_at, metadata)
                VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                ON CONFLICT (tenant_id, connector_id, data_type)
                DO UPDATE SET
                  data = EXCLUDED.data,
                  record_count = EXCLUDED.record_count,
                  synced_at = NOW(),
                  metadata = EXCLUDED.metadata
                """,
                (
                    tenant_id,
                    connector_id,
                    data_type,
                    Json(records),
                    len(records),
                    Json({"notes": source_notes[:5]}),
                ),
            )
        conn.commit()


@app.get("/v1/analyze/sample", response_model=AnalyzeResponse)
def analyze_sample(identity: dict = Depends(require_auth)) -> AnalyzeResponse:
    df = _load_sample()
    mapping = _detect_mapping(df)
    insights = _basic_insights(df, mapping)
    return AnalyzeResponse(
        generated_at=datetime.now(tz=timezone.utc).isoformat(),
        rows=int(df.shape[0]),
        columns=int(df.shape[1]),
        mapping=mapping,
        preview=[{str(k): v for k, v in row.items()} for row in df.head(10).to_dict(orient="records")],
        insights=insights,
        missing_values=int(df.isna().sum().sum()),
        notes=["Loaded sample via GET endpoint"],
    )
