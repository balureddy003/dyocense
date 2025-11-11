"""Deployment mode configuration for Dyocense platform.

Supports two deployment tiers:
    - SMB (unified): Cost-optimized single-process deployment
    - Enterprise (microservices): Full-scale distributed deployment

Configuration via environment variables:
    - DEPLOYMENT_MODE=unified|microservices
    - Feature flags for individual services
    - Resource limits per tier
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class DeploymentMode(str, Enum):
    """Deployment mode options."""
    UNIFIED = "unified"
    MICROSERVICES = "microservices"


class PlanTier(str, Enum):
    """Plan tier options."""
    SMB_STARTER = "smb_starter"
    SMB_GROWTH = "smb_growth"
    ENTERPRISE = "enterprise"


def _resolve_plan_tier(value: str) -> PlanTier:
    """Map legacy/new plan tier strings to PlanTier enum."""
    if not value:
        return PlanTier.SMB_STARTER
    try:
        return PlanTier(value)
    except ValueError:
        mapping = {
            "free": PlanTier.SMB_STARTER,
            "silver": PlanTier.SMB_GROWTH,
            "gold": PlanTier.ENTERPRISE,
            "platinum": PlanTier.ENTERPRISE,
        }
        return mapping.get(value, PlanTier.SMB_STARTER)


@dataclass
class ResourceLimits:
    """Resource limits for a plan tier."""
    max_users: int
    max_projects: int
    max_runs_per_month: int
    max_connectors: int
    max_storage_gb: int
    max_concurrent_runs: int
    max_api_requests_per_minute: int
    features: list[str]


# Plan tier resource limits
PLAN_LIMITS: Dict[PlanTier, ResourceLimits] = {
    PlanTier.SMB_STARTER: ResourceLimits(
        max_users=10,
        max_projects=50,
        max_runs_per_month=1000,
        max_connectors=10,
        max_storage_gb=10,
        max_concurrent_runs=2,
        max_api_requests_per_minute=60,
        features=[
            "basic_analytics",
            "email_support",
            "standard_connectors",
            "basic_playbooks"
        ]
    ),
    PlanTier.SMB_GROWTH: ResourceLimits(
        max_users=50,
        max_projects=200,
        max_runs_per_month=5000,
        max_connectors=50,
        max_storage_gb=50,
        max_concurrent_runs=10,
        max_api_requests_per_minute=300,
        features=[
            "advanced_analytics",
            "priority_support",
            "all_connectors",
            "custom_playbooks",
            "api_access",
            "webhooks"
        ]
    ),
    PlanTier.ENTERPRISE: ResourceLimits(
        max_users=1000,
        max_projects=10000,
        max_runs_per_month=100000,
        max_connectors=1000,
        max_storage_gb=1000,
        max_concurrent_runs=100,
        max_api_requests_per_minute=10000,
        features=[
            "advanced_analytics",
            "dedicated_support",
            "all_connectors",
            "custom_playbooks",
            "api_access",
            "webhooks",
            "multi_region",
            "data_residency",
            "sso",
            "audit_logs",
            "custom_integrations",
            "sla_guarantee"
        ]
    )
}


@dataclass
class DeploymentConfig:
    """Deployment configuration."""
    mode: DeploymentMode
    persistence_backend: str
    
    # Service feature flags
    enable_accounts: bool = True
    enable_chat: bool = True
    enable_compiler: bool = True
    enable_forecast: bool = True
    enable_policy: bool = True
    enable_optimiser: bool = True
    enable_diagnostician: bool = True
    enable_explainer: bool = True
    enable_connectors: bool = True
    enable_knowledge: bool = True
    enable_evidence: bool = True
    enable_marketplace: bool = True
    enable_scenario: bool = True
    
    # Performance settings
    worker_count: int = 2
    max_concurrent_runs: int = 10
    event_processing_interval: int = 1
    orchestration_interval: int = 2
    
    # Observability
    enable_telemetry: bool = True
    enable_metrics: bool = True
    log_level: str = "INFO"
    
    # External services
    enable_email: bool = True
    enable_blob_storage: bool = False  # Use local filesystem by default in SMB
    
    @classmethod
    def from_env(cls) -> DeploymentConfig:
        """Load configuration from environment variables."""
        mode_str = os.getenv("DEPLOYMENT_MODE", "unified").lower()
        mode = DeploymentMode.UNIFIED if mode_str == "unified" else DeploymentMode.MICROSERVICES
        
        persistence_backend = os.getenv("PERSISTENCE_BACKEND", "postgres" if mode == DeploymentMode.UNIFIED else "mongodb")
        
        return cls(
            mode=mode,
            persistence_backend=persistence_backend,
            
            # Service flags (all enabled by default, can be disabled individually)
            enable_accounts=cls._get_bool("ENABLE_ACCOUNTS_SERVICE", True),
            enable_chat=cls._get_bool("ENABLE_CHAT_SERVICE", True),
            enable_compiler=cls._get_bool("ENABLE_COMPILER_SERVICE", True),
            enable_forecast=cls._get_bool("ENABLE_FORECAST_SERVICE", True),
            enable_policy=cls._get_bool("ENABLE_POLICY_SERVICE", True),
            enable_optimiser=cls._get_bool("ENABLE_OPTIMISER_SERVICE", True),
            enable_diagnostician=cls._get_bool("ENABLE_DIAGNOSTICIAN_SERVICE", True),
            enable_explainer=cls._get_bool("ENABLE_EXPLAINER_SERVICE", True),
            enable_connectors=cls._get_bool("ENABLE_CONNECTORS_SERVICE", True),
            enable_knowledge=cls._get_bool("ENABLE_KNOWLEDGE_SERVICE", True),
            enable_evidence=cls._get_bool("ENABLE_EVIDENCE_SERVICE", True),
            enable_marketplace=cls._get_bool("ENABLE_MARKETPLACE_SERVICE", True),
            enable_scenario=cls._get_bool("ENABLE_SCENARIO_SERVICE", True),
            
            # Performance
            worker_count=int(os.getenv("WORKER_COUNT", "2")),
            max_concurrent_runs=int(os.getenv("MAX_CONCURRENT_RUNS", "10")),
            event_processing_interval=int(os.getenv("EVENT_PROCESSING_INTERVAL", "1")),
            orchestration_interval=int(os.getenv("ORCHESTRATION_INTERVAL", "2")),
            
            # Observability
            enable_telemetry=cls._get_bool("ENABLE_TELEMETRY", True),
            enable_metrics=cls._get_bool("ENABLE_METRICS", True),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            
            # External services
            enable_email=cls._get_bool("ENABLE_EMAIL", True),
            enable_blob_storage=cls._get_bool("ENABLE_BLOB_STORAGE", False)
        )
    
    @staticmethod
    def _get_bool(key: str, default: bool) -> bool:
        """Get boolean environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")
    
    def is_service_enabled(self, service_name: str) -> bool:
        """Check if a service is enabled."""
        attr_name = f"enable_{service_name.lower()}"
        return getattr(self, attr_name, False)
    
    def get_enabled_services(self) -> list[str]:
        """Get list of enabled service names."""
        services = []
        for attr in dir(self):
            if attr.startswith("enable_") and getattr(self, attr):
                service_name = attr.replace("enable_", "")
                services.append(service_name)
        return services


@dataclass
class DatabaseConfig:
    """Database configuration."""
    backend: str
    
    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "dyocense"
    postgres_user: str = "dyocense"
    postgres_password: str = ""
    postgres_min_pool_size: int = 2
    postgres_max_pool_size: int = 10
    
    # MongoDB
    mongo_uri: Optional[str] = None
    mongo_host: str = "localhost"
    mongo_port: int = 27017
    mongo_db: str = "dyocense"
    mongo_username: Optional[str] = None
    mongo_password: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> DatabaseConfig:
        """Load database configuration from environment."""
        backend = os.getenv("PERSISTENCE_BACKEND", "postgres")
        
        return cls(
            backend=backend,
            
            # PostgreSQL
            postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
            postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
            postgres_db=os.getenv("POSTGRES_DB", "dyocense"),
            postgres_user=os.getenv("POSTGRES_USER", "dyocense"),
            postgres_password=os.getenv("POSTGRES_PASSWORD", ""),
            postgres_min_pool_size=int(os.getenv("POSTGRES_MIN_POOL_SIZE", "2")),
            postgres_max_pool_size=int(os.getenv("POSTGRES_MAX_POOL_SIZE", "10")),
            
            # MongoDB
            mongo_uri=os.getenv("MONGO_URI"),
            mongo_host=os.getenv("MONGO_HOST", "localhost"),
            mongo_port=int(os.getenv("MONGO_PORT", "27017")),
            mongo_db=os.getenv("MONGO_DB_NAME", "dyocense"),
            mongo_username=os.getenv("MONGO_USERNAME"),
            mongo_password=os.getenv("MONGO_PASSWORD")
        )


# Global configuration instances
_deployment_config: Optional[DeploymentConfig] = None
_database_config: Optional[DatabaseConfig] = None


def get_deployment_config() -> DeploymentConfig:
    """Get or create deployment configuration."""
    global _deployment_config
    if _deployment_config is None:
        _deployment_config = DeploymentConfig.from_env()
    return _deployment_config


def get_database_config() -> DatabaseConfig:
    """Get or create database configuration."""
    global _database_config
    if _database_config is None:
        _database_config = DatabaseConfig.from_env()
    return _database_config


def get_plan_limits(plan_tier: PlanTier) -> ResourceLimits:
    """Get resource limits for a plan tier."""
    return PLAN_LIMITS[plan_tier]


def should_migrate_to_enterprise(tenant_usage: Dict[str, int]) -> bool:
    """Check if tenant should migrate from SMB to enterprise tier."""
    smb_growth_limits = PLAN_LIMITS[PlanTier.SMB_GROWTH]
    
    # Check multiple criteria
    criteria_met = 0
    
    if tenant_usage.get("users_count", 0) >= smb_growth_limits.max_users * 0.8:
        criteria_met += 1
    
    if tenant_usage.get("runs_this_month", 0) >= smb_growth_limits.max_runs_per_month * 0.8:
        criteria_met += 1
    
    if tenant_usage.get("storage_used_gb", 0) >= smb_growth_limits.max_storage_gb * 0.8:
        criteria_met += 1
    
    if tenant_usage.get("connectors_count", 0) >= smb_growth_limits.max_connectors * 0.8:
        criteria_met += 1
    
    # Suggest migration if 2+ criteria met
    return criteria_met >= 2


def validate_tenant_limits(tenant: Dict[str, any], action: str) -> tuple[bool, Optional[str]]:
    """Validate if tenant can perform an action based on their limits.
    
    Returns:
        (is_allowed, error_message)
    """
    plan_tier = _resolve_plan_tier(tenant.get("plan_tier", "smb_starter"))
    limits = get_plan_limits(plan_tier)
    usage = tenant.get("usage", {})
    
    if action == "create_user":
        if usage.get("users_count", 0) >= limits.max_users:
            return False, f"User limit reached ({limits.max_users}). Upgrade to add more users."
    
    elif action == "create_project":
        if usage.get("projects_count", 0) >= limits.max_projects:
            return False, f"Project limit reached ({limits.max_projects}). Upgrade to add more projects."
    
    elif action == "create_run":
        if usage.get("runs_this_month", 0) >= limits.max_runs_per_month:
            return False, f"Monthly run limit reached ({limits.max_runs_per_month}). Upgrade or wait until next month."
    
    elif action == "create_connector":
        if usage.get("connectors_count", 0) >= limits.max_connectors:
            return False, f"Connector limit reached ({limits.max_connectors}). Upgrade to add more connectors."
    
    return True, None
