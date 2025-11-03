from __future__ import annotations

import io
import logging
import os
from typing import Any, Dict, Iterable, List

import pandas as pd

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import boto3

    HAS_BOTO3 = True
except Exception:  # pragma: no cover - boto3 optional
    HAS_BOTO3 = False


def load_series_from_sources(sources: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Load time-series definitions from a set of source configs.

    Each source config must declare a ``type``. Supported types:

    - ``csv``: local CSV file (expects ``path`` or ``filepath``).
    - ``minio``: S3-compatible object storage (MinIO); requires ``bucket`` and ``key``.
    - ``google_sheets``: pass a ``csv_url`` export link or sheet parameters.

    Returns a list of dictionaries suitable for constructing ``ForecastSeries``.
    """

    loaded: List[Dict[str, Any]] = []
    for source in sources:
        source_type = (source.get("type") or "").lower()
        if source_type == "csv":
            loaded.extend(_load_from_csv(source))
        elif source_type == "minio":
            loaded.extend(_load_from_minio(source))
        elif source_type in {"google_sheets", "sheets"}:
            loaded.extend(_load_from_google_sheets(source))
        else:
            raise ValueError(f"Unsupported data source type '{source_type}'")
    return loaded


def _load_from_csv(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    path = cfg.get("path") or cfg.get("filepath")
    if not path:
        raise ValueError("CSV source requires 'path'")

    delimiter = cfg.get("delimiter") or ","
    df = pd.read_csv(path, delimiter=delimiter)
    return _extract_series_from_frame(df, cfg)


def _load_from_minio(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not HAS_BOTO3:
        logger.warning("boto3 not installed; skipping MinIO source '%s'", cfg.get("key"))
        return []

    endpoint = cfg.get("endpoint_url") or os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    access_key = cfg.get("access_key") or os.getenv("MINIO_ACCESS_KEY")
    secret_key = cfg.get("secret_key") or os.getenv("MINIO_SECRET_KEY")
    bucket = cfg.get("bucket")
    key = cfg.get("key")
    if not bucket or not key:
        raise ValueError("MinIO source requires 'bucket' and 'key'")

    session_kwargs = {
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
        "region_name": cfg.get("region", "us-east-1"),
    }
    # Filter out None values to allow env-based credentials (IAM/kube secrets)
    session_kwargs = {k: v for k, v in session_kwargs.items() if v}

    session = boto3.session.Session(**session_kwargs)
    resource = session.resource(
        "s3",
        endpoint_url=endpoint,
        config=cfg.get("config"),
        verify=cfg.get("verify", True),
    )

    obj = resource.Object(bucket, key)
    body = obj.get()["Body"].read()
    df = pd.read_csv(io.BytesIO(body), delimiter=cfg.get("delimiter", ","))
    return _extract_series_from_frame(df, cfg)


def _load_from_google_sheets(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    csv_url = cfg.get("csv_url")
    if not csv_url:
        sheet_id = cfg.get("sheet_id")
        gid = cfg.get("gid") or cfg.get("worksheet_gid", "0")
        if not sheet_id:
            raise ValueError("Google Sheets source requires 'csv_url' or 'sheet_id'")
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

    df = pd.read_csv(csv_url)
    return _extract_series_from_frame(df, cfg)


def _extract_series_from_frame(df: pd.DataFrame, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert a DataFrame into series definitions.

    Configuration supports either:
    - ``name``: single series name; ``value_column`` for values.
    - ``name_column``: column containing series name for multi-series rows.
    - ``value_column``: column containing numeric values (default ``value``).
    - ``pivot": bool to pivot on columns representing series.
    """

    value_col = cfg.get("value_column", "value")
    name = cfg.get("name")
    name_column = cfg.get("name_column")
    pivot = cfg.get("pivot", False)

    if pivot:
        df = df.set_index(cfg.get("index_column") or df.columns[0])
        series_list: List[Dict[str, Any]] = []
        for column in df.columns:
            values = df[column].dropna().tolist()
            series_list.append({"name": str(column), "values": [float(v) for v in values]})
        return series_list

    if name_column:
        grouped = df.groupby(df[name_column])
        series_list = []
        for series_name, group in grouped:
            values = group[value_col].dropna().tolist()
            series_list.append({"name": str(series_name), "values": [float(v) for v in values]})
        return series_list

    if name:
        values = df[value_col].dropna().tolist()
        return [{"name": name, "values": [float(v) for v in values]}]

    # Fallback: treat each numeric column as a separate series
    numeric_cols = df.select_dtypes(include="number").columns
    series_list = []
    for column in numeric_cols:
        values = df[column].dropna().tolist()
        series_list.append({"name": str(column), "values": [float(v) for v in values]})
    if not series_list:
        raise ValueError("Unable to infer series from dataset; specify 'name' or 'name_column'")
    return series_list
