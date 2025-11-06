"""Centralized configuration management for Dyocense platform.

This module provides type-safe configuration access with environment variable
support, feature flags, and sensible defaults for both development and production.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class MongoDBConfig:
    """MongoDB connection configuration."""
    
    uri: Optional[str] = None
    host: str = "localhost"
    port: int = 27017
    username: Optional[str] = None
    password: Optional[str] = None
    auth_db: str = "admin"
    database: str = "dyocense"
    replica_set: Optional[str] = None
    use_tls: bool = False
    tls_ca_file: Optional[str] = None
    
    # Connection pool settings
    max_pool_size: int = 50
    min_pool_size: int = 10
    max_idle_time_ms: int = 45000
    wait_queue_timeout_ms: int = 5000
    
    @classmethod
    def from_env(cls) -> MongoDBConfig:
        """Load configuration from environment variables."""
        return cls(
            uri=os.getenv("MONGO_URI"),
            host=os.getenv("MONGO_HOST", "localhost"),
            port=int(os.getenv("MONGO_PORT", "27017")),
            username=os.getenv("MONGO_USERNAME"),
            password=os.getenv("MONGO_PASSWORD"),
            auth_db=os.getenv("MONGO_AUTH_DB", "admin"),
            database=os.getenv("MONGO_DB_NAME", "dyocense"),
            replica_set=os.getenv("MONGO_REPLICA_SET"),
            use_tls=os.getenv("MONGO_TLS", "false").lower() == "true",
            tls_ca_file=os.getenv("MONGO_TLS_CA_FILE"),
            max_pool_size=int(os.getenv("MONGO_MAX_POOL_SIZE", "50")),
            min_pool_size=int(os.getenv("MONGO_MIN_POOL_SIZE", "10")),
        )


@dataclass
class Neo4jConfig:
    """Neo4j graph database configuration."""
    
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = "password"
    database: str = "neo4j"
    max_connection_lifetime: int = 3600
    max_connection_pool_size: int = 50
    connection_timeout: float = 2.0
    max_retry_time: float = 2.0
    
    @classmethod
    def from_env(cls) -> Neo4jConfig:
        """Load configuration from environment variables."""
        return cls(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            username=os.getenv("NEO4J_USERNAME", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password"),
            database=os.getenv("NEO4J_DATABASE", "neo4j"),
            max_connection_lifetime=int(os.getenv("NEO4J_MAX_CONNECTION_LIFETIME", "3600")),
            max_connection_pool_size=int(os.getenv("NEO4J_MAX_POOL_SIZE", "50")),
        )


@dataclass
class QdrantConfig:
    """Qdrant vector database configuration."""
    
    url: str = "http://localhost:6333"
    api_key: Optional[str] = None
    collection_name: str = "dyocense_knowledge"
    vector_size: int = 1536  # OpenAI embedding size
    distance_metric: str = "cosine"
    
    @classmethod
    def from_env(cls) -> QdrantConfig:
        """Load configuration from environment variables."""
        return cls(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name=os.getenv("QDRANT_COLLECTION", "dyocense_knowledge"),
            vector_size=int(os.getenv("QDRANT_VECTOR_SIZE", "1536")),
            distance_metric=os.getenv("QDRANT_DISTANCE", "cosine"),
        )


@dataclass
class KeycloakConfig:
    """Keycloak authentication configuration."""
    
    server_url: str = "http://localhost:8080"
    realm: str = "dyocense"
    client_id: str = "dyocense-api"
    client_secret: Optional[str] = None
    admin_username: Optional[str] = None
    admin_password: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> KeycloakConfig:
        """Load configuration from environment variables."""
        return cls(
            server_url=os.getenv("KEYCLOAK_SERVER_URL", "http://localhost:8080"),
            realm=os.getenv("KEYCLOAK_REALM", "dyocense"),
            client_id=os.getenv("KEYCLOAK_CLIENT_ID", "dyocense-api"),
            client_secret=os.getenv("KEYCLOAK_CLIENT_SECRET"),
            admin_username=os.getenv("KEYCLOAK_ADMIN_USERNAME"),
            admin_password=os.getenv("KEYCLOAK_ADMIN_PASSWORD"),
        )


@dataclass
class LLMConfig:
    """LLM service configuration (Azure OpenAI or OpenAI)."""
    
    provider: str = "azure"  # "azure" or "openai"
    
    # Azure OpenAI
    azure_endpoint: Optional[str] = None
    azure_api_key: Optional[str] = None
    azure_deployment: str = "gpt-4"
    azure_api_version: str = "2024-02-15-preview"
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_organization: Optional[str] = None
    
    # Common settings
    temperature: float = 0.7
    max_tokens: int = 4000
    timeout: int = 30
    
    @classmethod
    def from_env(cls) -> LLMConfig:
        """Load configuration from environment variables."""
        provider = os.getenv("LLM_PROVIDER", "azure").lower()
        return cls(
            provider=provider,
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4"),
            azure_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4"),
            openai_organization=os.getenv("OPENAI_ORGANIZATION"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4000")),
            timeout=int(os.getenv("LLM_TIMEOUT", "30")),
        )


@dataclass
class FeatureFlags:
    """Feature flags for enabling/disabling functionality."""
    
    # Deployment mode: 'smb' or 'platform'
    # SMB mode: Simplified stack, SMB-focused UX, faster decisions
    # Platform mode: Full stack with all enterprise features
    deployment_mode: str = "smb"
    
    # Force in-memory mode for all services (development/testing)
    force_inmemory: bool = False
    
    # Enable/disable specific external dependencies
    use_mongodb: bool = True
    use_neo4j: bool = False  # Disabled by default for SMB mode
    use_qdrant: bool = False  # Disabled by default for SMB mode
    use_keycloak: bool = False  # Simplified auth for SMB mode
    use_llm: bool = True
    
    # Strict mode - fail if dependencies unavailable
    strict_mode: bool = False
    
    # Enable advanced features
    enable_transactions: bool = False
    enable_caching: bool = True
    enable_metrics: bool = True
    enable_evidence_graph: bool = False  # Platform feature
    enable_vector_search: bool = False  # Platform feature
    
    @classmethod
    def from_env(cls) -> FeatureFlags:
        """Load feature flags from environment variables."""
        mode = os.getenv("DEPLOYMENT_MODE", "smb").lower()
        
        # Auto-configure based on deployment mode
        if mode == "platform":
            # Platform mode: Enable all features
            return cls(
                deployment_mode="platform",
                force_inmemory=os.getenv("FORCE_INMEMORY_MODE", "false").lower() == "true",
                use_mongodb=os.getenv("USE_MONGODB", "true").lower() == "true",
                use_neo4j=os.getenv("USE_NEO4J", "true").lower() == "true",
                use_qdrant=os.getenv("USE_QDRANT", "true").lower() == "true",
                use_keycloak=os.getenv("USE_KEYCLOAK", "true").lower() == "true",
                use_llm=os.getenv("USE_LLM", "true").lower() == "true",
                strict_mode=os.getenv("STRICT_MODE", "false").lower() == "true",
                enable_transactions=os.getenv("ENABLE_TRANSACTIONS", "true").lower() == "true",
                enable_caching=os.getenv("ENABLE_CACHING", "true").lower() == "true",
                enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
                enable_evidence_graph=True,
                enable_vector_search=True,
            )
        else:
            # SMB mode: Simplified stack for faster decisions
            return cls(
                deployment_mode="smb",
                force_inmemory=os.getenv("FORCE_INMEMORY_MODE", "false").lower() == "true",
                use_mongodb=os.getenv("USE_MONGODB", "true").lower() == "true",
                use_neo4j=os.getenv("USE_NEO4J", "false").lower() == "true",
                use_qdrant=os.getenv("USE_QDRANT", "false").lower() == "true",
                use_keycloak=os.getenv("USE_KEYCLOAK", "false").lower() == "true",
                use_llm=os.getenv("USE_LLM", "true").lower() == "true",
                strict_mode=os.getenv("STRICT_MODE", "false").lower() == "true",
                enable_transactions=False,
                enable_caching=True,
                enable_metrics=True,
                enable_evidence_graph=False,
                enable_vector_search=False,
            )
    
    def is_smb_mode(self) -> bool:
        """Check if running in SMB mode."""
        return self.deployment_mode == "smb"
    
    def is_platform_mode(self) -> bool:
        """Check if running in platform mode."""
        return self.deployment_mode == "platform"


@dataclass
class AppConfig:
    """Top-level application configuration."""
    
    mongodb: MongoDBConfig
    neo4j: Neo4jConfig
    qdrant: QdrantConfig
    keycloak: KeycloakConfig
    llm: LLMConfig
    features: FeatureFlags
    
    # Application settings
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    
    @classmethod
    def load(cls) -> AppConfig:
        """Load complete application configuration from environment."""
        return cls(
            mongodb=MongoDBConfig.from_env(),
            neo4j=Neo4jConfig.from_env(),
            qdrant=QdrantConfig.from_env(),
            keycloak=KeycloakConfig.from_env(),
            llm=LLMConfig.from_env(),
            features=FeatureFlags.from_env(),
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() in ("production", "prod")
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() in ("development", "dev", "local")


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get global configuration instance (singleton pattern)."""
    global _config
    if _config is None:
        _config = AppConfig.load()
    return _config


def reload_config() -> AppConfig:
    """Force reload of configuration from environment."""
    global _config
    _config = AppConfig.load()
    return _config


__all__ = [
    "AppConfig",
    "MongoDBConfig",
    "Neo4jConfig",
    "QdrantConfig",
    "KeycloakConfig",
    "LLMConfig",
    "FeatureFlags",
    "get_config",
    "reload_config",
]
