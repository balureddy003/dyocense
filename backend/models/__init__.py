"""
SQLAlchemy Database Models for Dyocense v4.0

Consolidated from 19 microservices into a single schema.
Uses PostgreSQL with TimescaleDB, pgvector, and Apache AGE extensions.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()


# =================================================================
# TENANT & USER MANAGEMENT
# =================================================================

class Tenant(Base):
    """
    Multi-tenant isolation.
    
    Each SMB is a separate tenant with isolated data via RLS.
    """
    __tablename__ = "tenants"
    
    tenant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    owner_email = Column(String(255), nullable=False)
    plan_tier = Column(String(50), nullable=False, default="free")  # free, starter, growth, enterprise
    api_token = Column(String(255), unique=True, nullable=False)
    status = Column(String(50), nullable=False, default="active")  # active, suspended, cancelled
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    tenant_metadata = Column(JSONB, default={})  # Renamed from 'metadata' (reserved word)
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    goals = relationship("SmartGoal", back_populates="tenant", cascade="all, delete-orphan")
    metrics = relationship("BusinessMetric", back_populates="tenant", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_tenants_status", status),
        Index("idx_tenants_plan_tier", plan_tier),
    )


class User(Base):
    """
    Users within a tenant (SMB employees).
    """
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    email = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), nullable=False, default="member")  # owner, admin, member, viewer
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime)
    extra_data = Column(JSONB, default={})  # Renamed from 'metadata' (reserved by SQLAlchemy)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    coaching_sessions = relationship("CoachingSession", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_tenant_user_email"),
        Index("idx_users_tenant_id", tenant_id),
        Index("idx_users_email", email),
    )


# =================================================================
# SMART GOALS & METRICS
# =================================================================

class SmartGoal(Base):
    """
    SMART goals tracked for each tenant.
    
    Goals are decomposed by AI coach into actionable sub-goals.
    """
    __tablename__ = "smart_goals"
    
    goal_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # revenue, cost, customer, operations
    target_value = Column(Float)
    current_value = Column(Float)
    unit = Column(String(50))  # $, %, count
    deadline = Column(DateTime)
    status = Column(String(50), nullable=False, default="active")  # active, achieved, abandoned
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    parent_goal_id = Column(UUID(as_uuid=True), ForeignKey("smart_goals.goal_id"))
    extra_data = Column(JSONB, default={})  # Renamed from 'metadata' (reserved by SQLAlchemy)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="goals")
    parent = relationship("SmartGoal", remote_side=[goal_id], backref="sub_goals")
    
    __table_args__ = (
        Index("idx_goals_tenant_id", tenant_id),
        Index("idx_goals_status", status),
    )


class BusinessMetric(Base):
    """
    Time-series business metrics (TimescaleDB hypertable).
    
    Stores KPIs like revenue, costs, inventory levels, etc.
    """
    __tablename__ = "business_metrics"
    
    metric_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    metric_name = Column(String(255), nullable=False)
    metric_type = Column(String(100))  # revenue, cost, quantity, ratio
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    source = Column(String(100))  # manual, erpnext, quickbooks, stripe
    extra_data = Column(JSONB, default={})  # Renamed from 'metadata' (reserved by SQLAlchemy)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="metrics")
    
    __table_args__ = (
        Index("idx_metrics_tenant_timestamp", tenant_id, timestamp.desc()),
        Index("idx_metrics_name", metric_name),
        # TimescaleDB hypertable will be created via extensions.sql
    )


# =================================================================
# AI COACH
# =================================================================

class CoachingSession(Base):
    """
    AI coach conversation history.
    
    Stores messages with embeddings for semantic search (pgvector).
    """
    __tablename__ = "coaching_sessions"
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    messages = Column(JSONB, nullable=False, default=[])  # Array of {role, content, timestamp}
    summary = Column(Text)  # Session summary generated by LLM
    embedding = Column(Vector(1536))  # OpenAI embedding dimension
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_data = Column(JSONB, default={})  # Renamed from 'metadata' (reserved by SQLAlchemy)
    
    # Relationships
    user = relationship("User", back_populates="coaching_sessions")
    
    __table_args__ = (
        Index("idx_coaching_tenant_user", tenant_id, user_id),
        Index("idx_coaching_updated", updated_at.desc()),
        # HNSW index on embedding will be created via extensions.sql
    )


# =================================================================
# DATA CONNECTORS
# =================================================================

class DataSource(Base):
    """
    External data source connections (ERPNext, QuickBooks, Stripe, etc.).
    """
    __tablename__ = "data_sources"
    
    source_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    connector_type = Column(String(100), nullable=False)  # erpnext, quickbooks, stripe
    name = Column(String(255), nullable=False)
    credentials = Column(JSONB, nullable=False)  # Encrypted credentials
    config = Column(JSONB, default={})
    status = Column(String(50), nullable=False, default="active")  # active, error, disabled
    last_sync = Column(DateTime)
    sync_frequency = Column(String(50), default="daily")  # hourly, daily, weekly
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    extra_data = Column(JSONB, default={})  # Renamed from 'metadata' (reserved by SQLAlchemy)
    
    __table_args__ = (
        Index("idx_datasources_tenant", tenant_id),
        Index("idx_datasources_type", connector_type),
    )


# =================================================================
# EVIDENCE & CAUSAL INFERENCE
# =================================================================

class EvidenceGraph(Base):
    """
    Causal relationships between metrics (Apache AGE graph or JSONB).
    
    Stores causal edges: metric_a -> metric_b (correlation, granger causality, etc.)
    """
    __tablename__ = "evidence_graph"
    
    edge_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    source_metric = Column(String(255), nullable=False)
    target_metric = Column(String(255), nullable=False)
    relationship_type = Column(String(100))  # correlation, granger_cause, propensity_match
    strength = Column(Float)  # Correlation coefficient or causal effect size
    confidence = Column(Float)  # Statistical confidence (p-value)
    evidence = Column(JSONB)  # Supporting evidence (statistical tests, etc.)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_evidence_tenant", tenant_id),
        Index("idx_evidence_source", source_metric),
        Index("idx_evidence_target", target_metric),
    )


# =================================================================
# FORECASTS
# =================================================================

class Forecast(Base):
    """
    Generated forecasts for business metrics.
    """
    __tablename__ = "forecasts"
    
    forecast_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    metric_name = Column(String(255), nullable=False)
    model_type = Column(String(100))  # arima, prophet, xgboost, ensemble
    horizon_days = Column(Integer)
    predictions = Column(JSONB, nullable=False)  # Array of {timestamp, value, lower_bound, upper_bound}
    accuracy_metrics = Column(JSONB)  # MAPE, RMSE, etc.
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    extra_data = Column(JSONB, default={})  # Renamed from 'metadata' (reserved by SQLAlchemy)
    
    __table_args__ = (
        Index("idx_forecasts_tenant_metric", tenant_id, metric_name),
        Index("idx_forecasts_created", created_at.desc()),
    )


# =================================================================
# OPTIMIZATION RUNS
# =================================================================

class OptimizationRun(Base):
    """
    Optimization problem runs (inventory, staffing, budget).
    """
    __tablename__ = "optimization_runs"
    
    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    problem_type = Column(String(100), nullable=False)  # inventory, staffing, budget
    input_data = Column(JSONB, nullable=False)
    solution = Column(JSONB)  # Optimal solution
    objective_value = Column(Float)  # Objective function value
    solver_status = Column(String(100))  # optimal, feasible, infeasible
    solve_time_seconds = Column(Float)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    extra_data = Column(JSONB, default={})  # Renamed from 'metadata' (reserved by SQLAlchemy)
    
    __table_args__ = (
        Index("idx_optimization_tenant_type", tenant_id, problem_type),
        Index("idx_optimization_created", created_at.desc()),
    )


# =================================================================
# EXTERNAL BENCHMARKS
# =================================================================

class ExternalBenchmark(Base):
    """
    External industry benchmarks (FRED, IBISWorld, Census).
    """
    __tablename__ = "external_benchmarks"
    
    benchmark_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(100), nullable=False)  # fred, ibisworld, census
    industry = Column(String(255))
    metric_name = Column(String(255), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    timestamp = Column(DateTime, nullable=False)
    geography = Column(String(100))  # US, CA-ON, etc.
    extra_data = Column(JSONB, default={})  # Renamed from 'metadata' (reserved by SQLAlchemy)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_benchmarks_source_metric", source, metric_name),
        Index("idx_benchmarks_industry", industry),
    )
