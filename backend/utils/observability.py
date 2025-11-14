"""
Observability utilities for Dyocense v4.0

- OpenTelemetry tracing (Jaeger)
- Prometheus metrics
"""

from typing import Optional

from backend.config import settings


def setup_tracing(app, service_name: str, endpoint: str) -> None:
    """
    Setup OpenTelemetry distributed tracing.
    
    Args:
        service_name: Service identifier (e.g., "dyocense-backend")
        endpoint: Jaeger OTLP endpoint (e.g., "http://localhost:4318")
    """
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        
        # Create resource
        resource = Resource.create({"service.name": service_name})
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Create OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")
        
        # Add span processor
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        # Instrument FastAPI automatically
        FastAPIInstrumentor().instrument_app(app)
        
        # Instrument SQLAlchemy
        SQLAlchemyInstrumentor().instrument()
        
    except ImportError as e:
        import logging
        logging.warning(f"OpenTelemetry not installed, tracing disabled: {e}")


def setup_metrics() -> None:
    """
    Setup Prometheus metrics collection.
    
    Metrics collected:
    - HTTP request rate, latency, status codes
    - Database query time
    - LLM API calls (count, latency, cost, tokens)
    - Cache hit/miss rates
    - Business metrics (goals, queries, optimizations, forecasts)
    - Cost tracking (LLM, infrastructure)
    """
    try:
        from prometheus_client import Counter, Histogram, Gauge, Info
        
        # HTTP metrics (FastAPI middleware will populate these)
        http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
        )
        
        http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request latency",
            ["method", "endpoint"],
        )
        
        # Database metrics
        db_query_duration_seconds = Histogram(
            "db_query_duration_seconds",
            "Database query latency",
            ["query_type"],
        )
        
        db_connections = Gauge(
            "db_connections",
            "Active database connections",
        )
        
        # LLM metrics
        llm_requests_total = Counter(
            "llm_requests_total",
            "Total LLM requests",
            ["tenant_id", "model", "provider"],
        )
        
        llm_request_duration_seconds = Histogram(
            "llm_request_duration_seconds",
            "LLM request latency",
            ["tenant_id", "model", "provider"],
        )
        
        # Cache metrics
        cache_hits_total = Counter(
            "cache_hits_total",
            "Cache hits",
            ["cache_type"],
        )
        
        cache_misses_total = Counter(
            "cache_misses_total",
            "Cache misses",
            ["cache_type"],
        )
        
        # Business metrics
        active_tenants = Gauge(
            "active_tenants",
            "Number of active tenants",
        )
        
        goals_created_total = Counter(
            "goals_created_total",
            "Total SMART goals created",
            ["tenant_id", "goal_type"],
        )
        
        smart_goals_total = Counter(
            "smart_goals_total",
            "SMART goals by status",
            ["tenant_id", "status"],
        )
        
        coach_queries_total = Counter(
            "coach_queries_total",
            "Total AI coach queries",
            ["tenant_id", "intent"],
        )
        
        optimizations_run_total = Counter(
            "optimizations_run_total",
            "Optimization runs",
            ["tenant_id", "type"],
        )
        
        forecasts_generated_total = Counter(
            "forecasts_generated_total",
            "Forecasts generated",
            ["tenant_id", "model_type"],
        )
        
        connector_syncs_total = Counter(
            "connector_syncs_total",
            "Connector synchronizations",
            ["tenant_id", "connector_type", "status"],
        )
        
        # Cost tracking metrics
        llm_cost_total = Counter(
            "llm_cost_total",
            "Cumulative LLM costs (USD)",
            ["tenant_id", "provider", "model"],
        )
        
        infrastructure_cost_total = Counter(
            "infrastructure_cost_total",
            "Infrastructure costs (USD)",
            ["component"],
        )
        
        llm_tokens_total = Counter(
            "llm_tokens_total",
            "LLM tokens consumed",
            ["tenant_id", "provider", "token_type"],
        )
        
        # App info
        app_info = Info("dyocense_app", "Dyocense application info")
        app_info.info({
            "version": "4.0.0",
            "environment": settings.ENVIRONMENT,
        })
        
    except ImportError as e:
        import logging
        logging.warning(f"prometheus_client not installed, metrics disabled: {e}")
