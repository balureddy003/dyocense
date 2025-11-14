"""
Dyocense v4.0 Configuration

Consolidated configuration from 19 microservices into a single Pydantic settings class.
Uses environment variables with sensible defaults.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings - loaded from environment variables"""
    
    # =================================================================
    # ENVIRONMENT & DEPLOYMENT
    # =================================================================
    
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    
    # =================================================================
    # DATABASE (PostgreSQL with extensions)
    # =================================================================
    
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://dyocense:dyocense@localhost:5432/dyocense",
        description="PostgreSQL connection string (asyncpg driver)"
    )
    
    DB_POOL_SIZE: int = Field(default=20, ge=5, le=100)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    DB_POOL_TIMEOUT: int = Field(default=30, ge=10, le=120)
    DB_ECHO: bool = Field(default=False, description="Log SQL queries")
    
    # =================================================================
    # REDIS (Caching - Optional)
    # =================================================================
    
    REDIS_URL: str | None = Field(
        default=None,
        description="Redis connection string for caching (optional)"
    )
    
    CACHE_TTL_SECONDS: int = Field(default=3600, description="Default cache TTL")
    LLM_CACHE_TTL_SECONDS: int = Field(default=86400, description="LLM response cache TTL (24h)")
    
    # =================================================================
    # AUTHENTICATION & SECURITY
    # =================================================================
    
    SECRET_KEY: str = Field(
        default="change-this-in-production-use-strong-random-key",
        description="JWT signing key"
    )
    
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175",
            "http://localhost:5176",
            "http://localhost:5177",
            "http://localhost:5178",
            "http://localhost:8001"
        ],
        description="Allowed CORS origins"
    )
    
    # =================================================================
    # LLM CONFIGURATION (Hybrid Routing)
    # =================================================================
    
    # Local LLM (Ollama or vLLM)
    ENABLE_LOCAL_LLM: bool = Field(default=True, description="Use local LLM for cost savings")
    LOCAL_LLM_URL: str = Field(
        default="http://localhost:11434",
        description="Ollama or vLLM endpoint"
    )
    LOCAL_LLM_MODEL: str = Field(
        default="llama3:8b",
        description="Local model name (Ollama format)"
    )
    LOCAL_LLM_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0)
    LOCAL_LLM_MAX_TOKENS: int = Field(default=2048, ge=100, le=8000)
    LOCAL_LLM_TIMEOUT: int = Field(default=30, description="Timeout for local LLM (seconds)")
    
    # Cloud LLM (OpenAI, Anthropic, etc.)
    OPENAI_API_KEY: str | None = Field(default=None, description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-4o", description="Cloud model for complex queries")
    OPENAI_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0)
    OPENAI_MAX_TOKENS: int = Field(default=2000, ge=100, le=4000)
    
    # LLM Routing
    LLM_COMPLEXITY_THRESHOLD: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Complexity threshold: >threshold uses cloud LLM"
    )
    LLM_LOCAL_PROBABILITY: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Target % of requests to route to local LLM"
    )
    
    LLM_TARGET_LOCAL_RATIO: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Target: 70% local, 30% cloud"
    )
    
    # =================================================================
    # OBSERVABILITY
    # =================================================================
    
    # Prometheus
    ENABLE_PROMETHEUS: bool = Field(default=True, description="Enable Prometheus metrics")
    
    # OpenTelemetry (Jaeger)
    ENABLE_TRACING: bool = Field(default=True, description="Enable distributed tracing")
    OTEL_SERVICE_NAME: str = "dyocense-backend"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(
        default="http://localhost:4318",
        description="Jaeger OTLP endpoint"
    )
    
    # Logging
    ENABLE_JSON_LOGGING: bool = Field(
        default=True,
        description="Use structured JSON logging (for Loki)"
    )
    
    LOG_FILE: str | None = Field(default=None, description="Log file path (optional)")
    
    # =================================================================
    # OPTIMIZATION ENGINE
    # =================================================================
    
    OPTIMIZATION_SOLVER: Literal["PULP", "ORTOOLS", "CPLEX"] = Field(
        default="ORTOOLS",
        description="Optimization solver backend"
    )
    
    OPTIMIZATION_TIMEOUT_SECONDS: int = Field(
        default=30,
        description="Max solver time for optimization problems"
    )
    
    # =================================================================
    # FORECASTING
    # =================================================================
    
    FORECAST_MIN_HISTORY_DAYS: int = Field(
        default=90,
        description="Minimum historical data required for forecasting"
    )
    
    FORECAST_DEFAULT_HORIZON_DAYS: int = Field(
        default=30,
        description="Default forecast horizon"
    )
    
    FORECAST_CONFIDENCE_LEVEL: float = Field(
        default=0.95,
        ge=0.5,
        le=0.99,
        description="Confidence interval level (95% default)"
    )
    
    # =================================================================
    # EXTERNAL DATA SOURCES
    # =================================================================
    
    FRED_API_KEY: str | None = Field(
        default=None,
        description="Federal Reserve Economic Data API key"
    )
    
    IBISWORLD_API_KEY: str | None = Field(
        default=None,
        description="IBISWorld industry data API key"
    )
    
    # =================================================================
    # CONNECTORS
    # =================================================================
    
    ERPNEXT_ENABLED: bool = Field(default=True, description="Enable ERPNext connector")
    QUICKBOOKS_ENABLED: bool = Field(default=True, description="Enable QuickBooks connector")
    STRIPE_ENABLED: bool = Field(default=True, description="Enable Stripe connector")
    
    # =================================================================
    # FEATURE FLAGS
    # =================================================================
    
    ENABLE_COACH: bool = Field(default=True, description="Enable AI coach feature")
    ENABLE_OPTIMIZER: bool = Field(default=True, description="Enable optimization engine")
    ENABLE_FORECASTER: bool = Field(default=True, description="Enable forecasting")
    ENABLE_EVIDENCE: bool = Field(default=True, description="Enable causal inference")
    ENABLE_BENCHMARKS: bool = Field(default=False, description="Enable external benchmarks")
    
    # =================================================================
    # PERFORMANCE & LIMITS
    # =================================================================
    
    MAX_CONCURRENT_REQUESTS: int = Field(
        default=100,
        description="Max concurrent requests per tenant"
    )
    
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        description="API rate limit per tenant"
    )
    
    MAX_QUERY_COMPLEXITY: int = Field(
        default=10,
        description="Max query complexity score"
    )
    
    # =================================================================
    # VALIDATORS
    # =================================================================
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure asyncpg driver is used"""
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use postgresql+asyncpg:// driver")
        return v
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # =================================================================
    # MODEL CONFIG
    # =================================================================
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra environment variables
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
