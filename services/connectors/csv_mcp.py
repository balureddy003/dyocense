#!/usr/bin/env python3
"""
CSV MCP Server for Dyocense
Provides Model Context Protocol interface to CSV data files
"""

import csv
import json
import logging
import os
from pathlib import Path
from typing import Any, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Optional MCP import; use minimal constructor signature for widest compatibility
try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("csv-server")  # Most versions accept just the name as positional
    MCP_AVAILABLE = True
except Exception as exc:  # Broad catch to handle ImportError or TypeError
    logger.warning("CSV MCP server disabled (%s)", exc)
    mcp = None
    MCP_AVAILABLE = False

# Get CSV directory from environment
# Use a writable directory for CSV data
# In production, set CSV_DATA_DIR env var to a persistent volume
_default_csv_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "csv")
CSV_DATA_DIR = os.getenv("CSV_DATA_DIR", _default_csv_dir)

# Tenant and connector context (set via CLI args)
TENANT_ID: Optional[str] = None
CONNECTOR_ID: Optional[str] = None


def _parse_filename_metadata(filename: str) -> dict[str, str]:
    """
    Parse connector metadata from CSV filename.
    
    Expected format: {connector_id}_{data_type}.csv
    Example: conn-abc123xyz_sales_data.csv
    
    Returns:
        Dict with connector_id, data_type, and source_description
    """
    try:
        # Remove .csv extension
        name_without_ext = filename.replace('.csv', '')
        
        # Split on first underscore to separate connector_id from data_type
        parts = name_without_ext.split('_', 1)
        
        if len(parts) == 2:
            connector_id, data_type = parts
            return {
                "connector_id": connector_id,
                "data_type": data_type,
                "source_description": f"{data_type.replace('_', ' ').title()} from connector {connector_id}"
            }
        else:
            # Fallback for non-standard filenames
            return {
                "connector_id": "unknown",
                "data_type": name_without_ext,
                "source_description": f"Data from {filename}"
            }
    except Exception as e:
        logger.warning(f"Failed to parse filename metadata: {e}")
        return {
            "connector_id": "unknown",
            "data_type": "unknown",
            "source_description": f"Data from {filename}"
        }


def _get_tenant_csv_dir() -> Path:
    """Get the tenant-specific CSV directory."""
    base_path = Path(CSV_DATA_DIR)
    if TENANT_ID:
        return base_path / TENANT_ID
    return base_path


def _get_csv_path(filename: str) -> Path:
    """Resolve CSV file path, ensuring it's within the tenant's data directory."""
    base_path = _get_tenant_csv_dir().resolve()
    file_path = (base_path / filename).resolve()
    
    # Security: ensure path is within tenant's CSV directory
    if not str(file_path).startswith(str(base_path)):
        raise ValueError(f"Access denied: {filename} is outside data directory")
    
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {filename}. Available files: {_get_available_files()}")
    
    return file_path


def _load_csv(filename: str, **kwargs) -> pd.DataFrame:
    """Load CSV file into pandas DataFrame."""
    path = _get_csv_path(filename)
    return pd.read_csv(path, **kwargs)


def _get_available_files() -> List[str]:
    """List all CSV files in the tenant's data directory."""
    base_path = _get_tenant_csv_dir()
    if not base_path.exists():
        return []
    
    csv_files = []
    for file_path in base_path.rglob("*.csv"):
        relative_path = file_path.relative_to(base_path)
        csv_files.append(str(relative_path))
    
    return sorted(csv_files)


# ===== Resources =====

RESOURCE_ERROR = "CSV MCP server disabled because mcp package is not installed."


def _resource_unavailable() -> str:
    raise RuntimeError(RESOURCE_ERROR)


def _tool_unavailable(*args: object, **kwargs: object) -> dict[str, object]:
    raise RuntimeError(RESOURCE_ERROR)


def _list_csv_files_payload() -> str:
    files = _get_available_files()
    
    # Enrich file list with metadata
    enriched_files = []
    for filename in files:
        metadata = _parse_filename_metadata(filename)
        enriched_files.append({
            "filename": filename,
            "connector_id": metadata["connector_id"],
            "data_type": metadata["data_type"],
            "description": metadata["source_description"],
        })
    
    return json.dumps(
        {
            "tenant_id": TENANT_ID,
            "data_directory": CSV_DATA_DIR,
            "files": enriched_files,
            "count": len(files),
        },
        indent=2,
    )


def _get_csv_info_payload(filename: str) -> str:
    df = _load_csv(filename, nrows=5)
    metadata = _parse_filename_metadata(filename)

    info = {
        "filename": filename,
        "connector_id": metadata["connector_id"],
        "data_type": metadata["data_type"],
        "source_description": metadata["source_description"],
        "columns": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "sample_rows": df.to_dict(orient="records"),
    }

    try:
        full_df = _load_csv(filename)
        info["total_rows"] = len(full_df)
        info["memory_usage_mb"] = full_df.memory_usage(deep=True).sum() / 1024 / 1024
    except Exception as exc:
        logger.warning("Could not get full file info: %s", exc)
        info["total_rows"] = "unknown"

    return json.dumps(info, indent=2, default=str)


def _get_csv_data_payload(filename: str) -> str:
    df = _load_csv(filename)
    return json.dumps(
        {
            "filename": filename,
            "total_rows": len(df),
            "columns": df.columns.tolist(),
            "data": df.to_dict(orient="records"),
        },
        indent=2,
        default=str,
    )


def _query_csv_payload(
    filename: str,
    columns: list[str] | None = None,
    filters: dict[str, object] | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, object]:
    df = _load_csv(filename)
    metadata = _parse_filename_metadata(filename)

    if filters:
        for col, value in filters.items():
            if col in df.columns:
                df = df[df[col] == value]

    if columns:
        missing_cols = set(columns) - set(df.columns)
        if missing_cols:
            return {"error": f"Columns not found: {missing_cols}"}
        df = df[columns]

    total_rows = len(df)
    df = df.iloc[offset : offset + limit]

    return {
        "filename": filename,
        "connector_id": metadata["connector_id"],
        "data_type": metadata["data_type"],
        "source_description": metadata["source_description"],
        "total_rows": total_rows,
        "returned_rows": len(df),
        "offset": offset,
        "limit": limit,
        "columns": df.columns.tolist(),
        "data": df.to_dict(orient="records"),
    }


def _analyze_csv_payload(filename: str, analysis_type: str = "summary") -> dict[str, object]:
    df = _load_csv(filename)
    metadata = _parse_filename_metadata(filename)

    if analysis_type == "summary":
        return {
            "filename": filename,
            "connector_id": metadata["connector_id"],
            "data_type": metadata["data_type"],
            "source_description": metadata["source_description"],
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
        }

    if analysis_type == "describe":
        desc = df.describe(include="all").to_dict()
        return {
            "filename": filename,
            "connector_id": metadata["connector_id"],
            "data_type": metadata["data_type"],
            "source_description": metadata["source_description"],
            "analysis_type": "describe",
            "describe": desc,
        }

    if analysis_type == "missing":
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)
        return {
            "filename": filename,
            "connector_id": metadata["connector_id"],
            "data_type": metadata["data_type"],
            "source_description": metadata["source_description"],
            "total_rows": len(df),
            "missing_values": {
                col: {"count": int(count), "percentage": float(missing_pct[col])}
                for col, count in missing.items()
                if count > 0
            },
        }

    if analysis_type == "unique":
        unique_counts = {col: int(df[col].nunique()) for col in df.columns}
        return {
            "filename": filename,
            "connector_id": metadata["connector_id"],
            "data_type": metadata["data_type"],
            "source_description": metadata["source_description"],
            "unique_value_counts": unique_counts,
        }

    return {"error": f"Unknown analysis type: {analysis_type}"}


def _aggregate_csv_payload(
    filename: str,
    group_by: list[str],
    aggregations: dict[str, str],
) -> dict[str, object]:
    df = _load_csv(filename)
    metadata = _parse_filename_metadata(filename)

    missing_cols = set(group_by) - set(df.columns)
    if missing_cols:
        return {"error": f"Group by columns not found: {missing_cols}"}

    missing_agg_cols = set(aggregations.keys()) - set(df.columns)
    if missing_agg_cols:
        return {"error": f"Aggregation columns not found: {missing_agg_cols}"}

    try:
        result = df.groupby(group_by).agg(aggregations).reset_index()
        return {
            "filename": filename,
            "connector_id": metadata["connector_id"],
            "data_type": metadata["data_type"],
            "source_description": metadata["source_description"],
            "group_by": group_by,
            "aggregations": aggregations,
            "total_groups": len(result),
            "data": result.to_dict(orient="records"),
        }
    except Exception as exc:
        return {"error": f"Aggregation failed: {str(exc)}"}


def _search_csv_payload(
    filename: str,
    search_column: str,
    search_term: str,
    match_type: str = "contains",
    limit: int = 100,
) -> dict[str, object]:
    df = _load_csv(filename)

    if search_column not in df.columns:
        return {"error": f"Column not found: {search_column}"}

    col_data = df[search_column].astype(str)

    if match_type == "contains":
        mask = col_data.str.contains(search_term, case=False, na=False)
    elif match_type == "startswith":
        mask = col_data.str.startswith(search_term, na=False)
    elif match_type == "endswith":
        mask = col_data.str.endswith(search_term, na=False)
    elif match_type == "exact":
        mask = col_data.str.lower() == search_term.lower()
    else:
        return {"error": f"Unknown match type: {match_type}"}

    result = df[mask].head(limit)

    return {
        "filename": filename,
        "search_column": search_column,
        "search_term": search_term,
        "match_type": match_type,
        "total_matches": int(mask.sum()),
        "returned_rows": len(result),
        "data": result.to_dict(orient="records"),
    }


def _column_values_payload(
    filename: str,
    column: str,
    unique_only: bool = True,
    limit: int = 1000,
) -> dict[str, object]:
    df = _load_csv(filename)

    if column not in df.columns:
        return {"error": f"Column not found: {column}"}

    if unique_only:
        values = df[column].unique()[:limit]
        value_list = [v for v in values if pd.notna(v)]
    else:
        values = df[column].head(limit)
        value_list = [v for v in values if pd.notna(v)]

    return {
        "filename": filename,
        "column": column,
        "unique_only": unique_only,
        "total_values": len(value_list),
        "values": value_list,
    }


def _analyze_data_prompt(filename: str) -> str:
    return f"""
Analyze the CSV file '{filename}':
1. Get file info including columns and data types
2. Check for missing values or data quality issues
3. Provide descriptive statistics for numeric columns
4. Identify any interesting patterns or anomalies
5. Suggest potential use cases or insights
"""


def _find_patterns_prompt(filename: str, target_column: str) -> str:
    return f"""
Find patterns in the '{target_column}' column of '{filename}':
1. Get unique values and their frequencies
2. Check for trends or distributions
3. Identify outliers or unusual values
4. Suggest grouping or categorization strategies
5. Recommend data transformations if needed
"""


def _compare_segments_prompt(filename: str, segment_column: str, metric_column: str) -> str:
    return f"""
Compare segments in '{filename}':
1. Group by '{segment_column}'
2. Calculate statistics for '{metric_column}' in each segment
3. Identify top and bottom performing segments
4. Find significant differences between segments
5. Provide actionable insights
"""


if mcp:
    # Resource decorators: use positional uri to avoid signature mismatches
    @mcp.resource("csv://files")
    def list_csv_files() -> str:
        return _list_csv_files_payload()

    @mcp.resource("csv://file/{filename}/info")
    def get_csv_info(filename: str) -> str:
        return _get_csv_info_payload(filename)

    @mcp.resource("csv://file/{filename}/data")
    def get_csv_data(filename: str) -> str:
        return _get_csv_data_payload(filename)

    @mcp.tool()
    def query_csv(
        filename: str,
        columns: list[str] | None = None,
        filters: dict[str, object] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, object]:
        return _query_csv_payload(filename, columns, filters, limit, offset)

    @mcp.tool()
    def analyze_csv(filename: str, analysis_type: str = "summary") -> dict[str, object]:
        return _analyze_csv_payload(filename, analysis_type)

    @mcp.tool()
    def aggregate_csv(
        filename: str,
        group_by: list[str],
        aggregations: dict[str, str],
    ) -> dict[str, object]:
        return _aggregate_csv_payload(filename, group_by, aggregations)

    @mcp.tool()
    def search_csv(
        filename: str,
        search_column: str,
        search_term: str,
        match_type: str = "contains",
        limit: int = 100,
    ) -> dict[str, object]:
        return _search_csv_payload(filename, search_column, search_term, match_type, limit)

    @mcp.tool()
    def get_column_values(
        filename: str,
        column: str,
        unique_only: bool = True,
        limit: int = 1000,
    ) -> dict[str, object]:
        return _column_values_payload(filename, column, unique_only, limit)

    @mcp.prompt(title="Analyze CSV data", description="Get insights from CSV file data")
    def analyze_data_prompt(filename: str) -> str:
        return _analyze_data_prompt(filename)

    @mcp.prompt(title="Find data patterns", description="Search for patterns in CSV data")
    def find_patterns_prompt(filename: str, target_column: str) -> str:
        return _find_patterns_prompt(filename, target_column)

    @mcp.prompt(title="Compare data segments", description="Compare different segments of CSV data")
    def compare_segments_prompt(filename: str, segment_column: str, metric_column: str) -> str:
        return _compare_segments_prompt(filename, segment_column, metric_column)
else:
    def list_csv_files() -> str:
        return _resource_unavailable()

    def get_csv_info(filename: str) -> str:
        return _resource_unavailable()

    def get_csv_data(filename: str) -> str:
        return _resource_unavailable()

    def query_csv(
        filename: str,
        columns: list[str] | None = None,
        filters: dict[str, object] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, object]:
        return _tool_unavailable()

    def analyze_csv(filename: str, analysis_type: str = "summary") -> dict[str, object]:
        return _tool_unavailable()

    def aggregate_csv(
        filename: str,
        group_by: list[str],
        aggregations: dict[str, str],
    ) -> dict[str, object]:
        return _tool_unavailable()

    def search_csv(
        filename: str,
        search_column: str,
        search_term: str,
        match_type: str = "contains",
        limit: int = 100,
    ) -> dict[str, object]:
        return _tool_unavailable()

    def get_column_values(
        filename: str,
        column: str,
        unique_only: bool = True,
        limit: int = 1000,
    ) -> dict[str, object]:
        return _tool_unavailable()

    def analyze_data_prompt(filename: str) -> str:
        return _resource_unavailable()

    def find_patterns_prompt(filename: str, target_column: str) -> str:
        return _resource_unavailable()

    def compare_segments_prompt(filename: str, segment_column: str, metric_column: str) -> str:
        return _resource_unavailable()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    import argparse
    
    parser = argparse.ArgumentParser(description="CSV MCP Server for Dyocense")
    parser.add_argument("--tenant", type=str, required=True, help="Tenant ID")
    parser.add_argument("--connector", type=str, required=True, help="Connector ID")
    args = parser.parse_args()
    
    # Set global tenant/connector context
    TENANT_ID = args.tenant
    CONNECTOR_ID = args.connector
    
    logger.info(f"Starting CSV MCP server for tenant={TENANT_ID}, connector={CONNECTOR_ID}")
    logger.info(f"CSV data directory: {_get_tenant_csv_dir()}")
    logger.info(f"Available CSV files: {_get_available_files()}")
    
    if mcp:
        mcp.run()
    else:
        logger.error("CSV MCP server not available; install the mcp package to enable it.")

