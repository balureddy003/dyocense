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
from typing import Any, Dict, List, Optional

import pandas as pd
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name="csv-server",
    version="1.0.0",
    description="Provides access to CSV data files with query and analysis capabilities",
)

# Get CSV directory from environment
CSV_DATA_DIR = os.getenv("CSV_DATA_DIR", "/data/csv")


def _get_csv_path(filename: str) -> Path:
    """Resolve CSV file path, ensuring it's within the data directory."""
    base_path = Path(CSV_DATA_DIR).resolve()
    file_path = (base_path / filename).resolve()
    
    # Security: ensure path is within CSV_DATA_DIR
    if not str(file_path).startswith(str(base_path)):
        raise ValueError(f"Access denied: {filename} is outside data directory")
    
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {filename}")
    
    return file_path


def _load_csv(filename: str, **kwargs) -> pd.DataFrame:
    """Load CSV file into pandas DataFrame."""
    path = _get_csv_path(filename)
    return pd.read_csv(path, **kwargs)


def _get_available_files() -> List[str]:
    """List all CSV files in the data directory."""
    base_path = Path(CSV_DATA_DIR)
    if not base_path.exists():
        return []
    
    csv_files = []
    for file_path in base_path.rglob("*.csv"):
        relative_path = file_path.relative_to(base_path)
        csv_files.append(str(relative_path))
    
    return sorted(csv_files)


# ===== Resources =====

@mcp.resource(uri_template="csv://files")
def list_csv_files() -> str:
    """List all available CSV files in the data directory."""
    files = _get_available_files()
    return json.dumps({
        "data_directory": CSV_DATA_DIR,
        "files": files,
        "count": len(files),
    }, indent=2)


@mcp.resource(uri_template="csv://file/{filename}/info")
def get_csv_info(filename: str) -> str:
    """Get metadata about a CSV file (columns, row count, sample data)."""
    df = _load_csv(filename, nrows=5)
    
    info = {
        "filename": filename,
        "columns": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "sample_rows": df.to_dict(orient="records"),
    }
    
    # Try to get full row count without loading entire file
    try:
        full_df = _load_csv(filename)
        info["total_rows"] = len(full_df)
        info["memory_usage_mb"] = full_df.memory_usage(deep=True).sum() / 1024 / 1024
    except Exception as e:
        logger.warning(f"Could not get full file info: {e}")
        info["total_rows"] = "unknown"
    
    return json.dumps(info, indent=2, default=str)


@mcp.resource(uri_template="csv://file/{filename}/data")
def get_csv_data(filename: str) -> str:
    """Get full CSV data (use with caution for large files)."""
    df = _load_csv(filename)
    
    return json.dumps({
        "filename": filename,
        "total_rows": len(df),
        "columns": df.columns.tolist(),
        "data": df.to_dict(orient="records"),
    }, indent=2, default=str)


# ===== Tools =====

@mcp.tool()
def query_csv(
    filename: str,
    columns: Optional[List[str]] = None,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Query CSV file with optional column selection and filtering.
    
    Args:
        filename: Name of the CSV file
        columns: List of columns to return (None = all columns)
        filters: Dictionary of column:value pairs for exact match filtering
        limit: Maximum number of rows to return
        offset: Number of rows to skip (for pagination)
    
    Returns:
        Dictionary with query results
    """
    df = _load_csv(filename)
    
    # Apply filters
    if filters:
        for col, value in filters.items():
            if col in df.columns:
                df = df[df[col] == value]
    
    # Select columns
    if columns:
        missing_cols = set(columns) - set(df.columns)
        if missing_cols:
            return {"error": f"Columns not found: {missing_cols}"}
        df = df[columns]
    
    # Apply pagination
    total_rows = len(df)
    df = df.iloc[offset:offset + limit]
    
    return {
        "filename": filename,
        "total_rows": total_rows,
        "returned_rows": len(df),
        "offset": offset,
        "limit": limit,
        "columns": df.columns.tolist(),
        "data": df.to_dict(orient="records"),
    }


@mcp.tool()
def analyze_csv(filename: str, analysis_type: str = "summary") -> Dict[str, Any]:
    """
    Perform statistical analysis on CSV data.
    
    Args:
        filename: Name of the CSV file
        analysis_type: Type of analysis - 'summary', 'describe', 'missing', 'unique'
    
    Returns:
        Analysis results
    """
    df = _load_csv(filename)
    
    if analysis_type == "summary":
        return {
            "filename": filename,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
        }
    
    elif analysis_type == "describe":
        # Get descriptive statistics for numeric columns
        desc = df.describe(include="all").to_dict()
        return {
            "filename": filename,
            "statistics": desc,
        }
    
    elif analysis_type == "missing":
        # Find missing values
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)
        return {
            "filename": filename,
            "total_rows": len(df),
            "missing_values": {
                col: {"count": int(count), "percentage": float(missing_pct[col])}
                for col, count in missing.items()
                if count > 0
            },
        }
    
    elif analysis_type == "unique":
        # Get unique value counts for each column
        unique_counts = {col: int(df[col].nunique()) for col in df.columns}
        return {
            "filename": filename,
            "unique_value_counts": unique_counts,
        }
    
    else:
        return {"error": f"Unknown analysis type: {analysis_type}"}


@mcp.tool()
def aggregate_csv(
    filename: str,
    group_by: List[str],
    aggregations: Dict[str, str],
) -> Dict[str, Any]:
    """
    Perform groupby aggregation on CSV data.
    
    Args:
        filename: Name of the CSV file
        group_by: List of columns to group by
        aggregations: Dictionary mapping column names to aggregation functions
                     (e.g., {"sales": "sum", "quantity": "mean"})
    
    Returns:
        Aggregated results
    """
    df = _load_csv(filename)
    
    # Validate group_by columns
    missing_cols = set(group_by) - set(df.columns)
    if missing_cols:
        return {"error": f"Group by columns not found: {missing_cols}"}
    
    # Validate aggregation columns
    missing_agg_cols = set(aggregations.keys()) - set(df.columns)
    if missing_agg_cols:
        return {"error": f"Aggregation columns not found: {missing_agg_cols}"}
    
    try:
        # Perform aggregation
        result = df.groupby(group_by).agg(aggregations).reset_index()
        
        return {
            "filename": filename,
            "group_by": group_by,
            "aggregations": aggregations,
            "total_groups": len(result),
            "data": result.to_dict(orient="records"),
        }
    except Exception as e:
        return {"error": f"Aggregation failed: {str(e)}"}


@mcp.tool()
def search_csv(
    filename: str,
    search_column: str,
    search_term: str,
    match_type: str = "contains",
    limit: int = 100,
) -> Dict[str, Any]:
    """
    Search for rows matching a search term.
    
    Args:
        filename: Name of the CSV file
        search_column: Column to search in
        search_term: Term to search for
        match_type: Type of match - 'contains', 'startswith', 'endswith', 'exact'
        limit: Maximum number of results
    
    Returns:
        Matching rows
    """
    df = _load_csv(filename)
    
    if search_column not in df.columns:
        return {"error": f"Column not found: {search_column}"}
    
    # Convert to string for searching
    col_data = df[search_column].astype(str)
    
    # Apply search
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
        "total_matches": mask.sum(),
        "returned_rows": len(result),
        "data": result.to_dict(orient="records"),
    }


@mcp.tool()
def get_column_values(
    filename: str,
    column: str,
    unique_only: bool = True,
    limit: int = 1000,
) -> Dict[str, Any]:
    """
    Get values from a specific column.
    
    Args:
        filename: Name of the CSV file
        column: Column name to extract
        unique_only: Return only unique values
        limit: Maximum number of values to return
    
    Returns:
        Column values
    """
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


# ===== Prompts =====

@mcp.prompt(title="Analyze CSV data", description="Get insights from CSV file data")
def analyze_data_prompt(filename: str) -> str:
    return f"""
Analyze the CSV file '{filename}':
1. Get file info including columns and data types
2. Check for missing values or data quality issues
3. Provide descriptive statistics for numeric columns
4. Identify any interesting patterns or anomalies
5. Suggest potential use cases or insights
"""


@mcp.prompt(title="Find data patterns", description="Search for patterns in CSV data")
def find_patterns_prompt(filename: str, target_column: str) -> str:
    return f"""
Find patterns in the '{target_column}' column of '{filename}':
1. Get unique values and their frequencies
2. Check for trends or distributions
3. Identify outliers or unusual values
4. Suggest grouping or categorization strategies
5. Recommend data transformations if needed
"""


@mcp.prompt(title="Compare data segments", description="Compare different segments of CSV data")
def compare_segments_prompt(filename: str, segment_column: str, metric_column: str) -> str:
    return f"""
Compare segments in '{filename}':
1. Group by '{segment_column}'
2. Calculate statistics for '{metric_column}' in each segment
3. Identify top and bottom performing segments
4. Find significant differences between segments
5. Provide actionable insights
"""


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    mcp.run()
