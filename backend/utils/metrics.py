"""
Custom Prometheus metrics for Dyocense v4.0

Provides domain-specific metrics for:
- Evidence engine operations
- Authentication and authorization
- Tenant activity
- API performance
"""

from typing import Optional
from functools import wraps
import time

try:
    from prometheus_client import Counter, Histogram, Gauge, Info
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False


# =============================================================================
# EVIDENCE ENGINE METRICS
# =============================================================================

if METRICS_ENABLED:
    # Correlation analysis
    evidence_correlations_total = Counter(
        "evidence_correlations_total",
        "Total correlation analyses performed",
        ["tenant_id", "num_series"],
    )
    
    evidence_correlation_duration_seconds = Histogram(
        "evidence_correlation_duration_seconds",
        "Time to compute correlations",
        ["num_series"],
        buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    )
    
    # Granger causality
    evidence_granger_total = Counter(
        "evidence_granger_total",
        "Total Granger causality tests performed",
        ["tenant_id"],
    )
    
    evidence_granger_duration_seconds = Histogram(
        "evidence_granger_duration_seconds",
        "Time to compute Granger causality",
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    )
    
    # What-if analysis
    evidence_whatif_total = Counter(
        "evidence_whatif_total",
        "Total what-if analyses performed",
        ["tenant_id"],
    )
    
    evidence_whatif_duration_seconds = Histogram(
        "evidence_whatif_duration_seconds",
        "Time to compute what-if scenarios",
        buckets=[0.01, 0.05, 0.1, 0.5, 1.0],
    )
    
    # Driver inference
    evidence_drivers_total = Counter(
        "evidence_drivers_total",
        "Total driver inference operations",
        ["tenant_id", "num_drivers"],
    )
    
    evidence_drivers_duration_seconds = Histogram(
        "evidence_drivers_duration_seconds",
        "Time to infer drivers",
        ["num_drivers"],
        buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0],
    )
    
    # Result quality metrics
    evidence_correlation_strength = Histogram(
        "evidence_correlation_strength",
        "Distribution of correlation coefficients",
        buckets=[-1.0, -0.8, -0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
    )
    
    evidence_model_r2 = Histogram(
        "evidence_model_r2",
        "R² values from linear models",
        buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0],
    )


# =============================================================================
# AUTHENTICATION METRICS
# =============================================================================

if METRICS_ENABLED:
    auth_login_attempts_total = Counter(
        "auth_login_attempts_total",
        "Total login attempts",
        ["tenant_id", "status"],  # status: success, invalid_credentials, user_not_found
    )
    
    auth_login_duration_seconds = Histogram(
        "auth_login_duration_seconds",
        "Time to process login",
        buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0],
    )
    
    auth_token_validations_total = Counter(
        "auth_token_validations_total",
        "JWT token validations",
        ["status"],  # status: valid, expired, invalid
    )
    
    auth_active_sessions = Gauge(
        "auth_active_sessions",
        "Number of active user sessions",
    )


# =============================================================================
# TENANT METRICS
# =============================================================================

if METRICS_ENABLED:
    tenant_api_requests_total = Counter(
        "tenant_api_requests_total",
        "API requests by tenant",
        ["tenant_id", "endpoint", "method", "status_code"],
    )
    
    tenant_api_duration_seconds = Histogram(
        "tenant_api_duration_seconds",
        "API request duration by tenant",
        ["tenant_id", "endpoint"],
        buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    )
    
    tenant_database_queries_total = Counter(
        "tenant_database_queries_total",
        "Database queries by tenant",
        ["tenant_id", "query_type"],
    )
    
    tenant_users_total = Gauge(
        "tenant_users_total",
        "Number of users per tenant",
        ["tenant_id"],
    )
    
    tenant_workspaces_total = Gauge(
        "tenant_workspaces_total",
        "Number of workspaces per tenant",
        ["tenant_id"],
    )


# =============================================================================
# API PERFORMANCE METRICS
# =============================================================================

if METRICS_ENABLED:
    api_errors_total = Counter(
        "api_errors_total",
        "Total API errors",
        ["endpoint", "error_type", "status_code"],
    )
    
    api_validation_errors_total = Counter(
        "api_validation_errors_total",
        "Request validation errors",
        ["endpoint", "field"],
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def record_evidence_correlation(tenant_id: str, num_series: int, duration: float, results: list):
    """Record correlation analysis metrics."""
    if not METRICS_ENABLED:
        return
    
    evidence_correlations_total.labels(
        tenant_id=tenant_id,
        num_series=str(num_series)
    ).inc()
    
    evidence_correlation_duration_seconds.labels(
        num_series=str(num_series)
    ).observe(duration)
    
    # Record correlation strength distribution
    for result in results:
        if "corr" in result:
            evidence_correlation_strength.observe(result["corr"])


def record_evidence_whatif(tenant_id: str, duration: float, r2: Optional[float] = None):
    """Record what-if analysis metrics."""
    if not METRICS_ENABLED:
        return
    
    evidence_whatif_total.labels(tenant_id=tenant_id).inc()
    evidence_whatif_duration_seconds.observe(duration)
    
    if r2 is not None:
        evidence_model_r2.observe(r2)


def record_evidence_drivers(tenant_id: str, num_drivers: int, duration: float):
    """Record driver inference metrics."""
    if not METRICS_ENABLED:
        return
    
    evidence_drivers_total.labels(
        tenant_id=tenant_id,
        num_drivers=str(num_drivers)
    ).inc()
    
    evidence_drivers_duration_seconds.labels(
        num_drivers=str(num_drivers)
    ).observe(duration)


def record_evidence_granger(tenant_id: str, duration: float):
    """Record Granger causality metrics."""
    if not METRICS_ENABLED:
        return
    
    evidence_granger_total.labels(tenant_id=tenant_id).inc()
    evidence_granger_duration_seconds.observe(duration)


def record_auth_login(tenant_id: str, status: str, duration: float):
    """Record login attempt metrics."""
    if not METRICS_ENABLED:
        return
    
    auth_login_attempts_total.labels(
        tenant_id=tenant_id,
        status=status
    ).inc()
    
    auth_login_duration_seconds.observe(duration)


def record_api_request(tenant_id: str, endpoint: str, method: str, status_code: int, duration: float):
    """Record API request metrics."""
    if not METRICS_ENABLED:
        return
    
    tenant_api_requests_total.labels(
        tenant_id=tenant_id,
        endpoint=endpoint,
        method=method,
        status_code=str(status_code)
    ).inc()
    
    tenant_api_duration_seconds.labels(
        tenant_id=tenant_id,
        endpoint=endpoint
    ).observe(duration)


def record_api_error(endpoint: str, error_type: str, status_code: int):
    """Record API error."""
    if not METRICS_ENABLED:
        return
    
    api_errors_total.labels(
        endpoint=endpoint,
        error_type=error_type,
        status_code=str(status_code)
    ).inc()


# =============================================================================
# DECORATORS
# =============================================================================

def track_evidence_operation(operation_type: str):
    """
    Decorator to track evidence engine operations.
    
    Usage:
        @track_evidence_operation("correlation")
        async def correlations(payload: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not METRICS_ENABLED:
                return await func(*args, **kwargs)
            
            start_time = time.time()
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Extract tenant_id from kwargs or args if available
            tenant_id = kwargs.get("tenant_id", "unknown")
            
            # Record based on operation type
            if operation_type == "correlation":
                # Assume result has results list
                num_series = len(kwargs.get("payload", {}).get("series", {}))
                results = getattr(result, "results", [])
                record_evidence_correlation(tenant_id, num_series, duration, results)
            elif operation_type == "whatif":
                r2 = getattr(result, "r2", None)
                record_evidence_whatif(tenant_id, duration, r2)
            elif operation_type == "drivers":
                num_drivers = len(kwargs.get("payload", {}).get("drivers", {}))
                record_evidence_drivers(tenant_id, num_drivers, duration)
            elif operation_type == "granger":
                record_evidence_granger(tenant_id, duration)
            
            return result
        return wrapper
    return decorator
