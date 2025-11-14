"""add_v4_tenant_user_workspace_and_rls

Revision ID: a4c9b2f7d3e1
Revises: f8a82d1a01e2
Create Date: 2025-11-14 15:12:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql


# revision identifiers, used by Alembic.
revision: str = 'a4c9b2f7d3e1'
down_revision: Union[str, None] = 'f8a82d1a01e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create v4 tenants table (lightweight schema for monolith APIs)
    op.create_table(
        'tenants_v4',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('subscription_status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Users v4 (scoped to tenants_v4)
    op.create_table(
        'users_v4',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('tenant_id', psql.UUID(as_uuid=True), sa.ForeignKey('tenants_v4.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_users_email_per_tenant'),
    )

    # Workspaces (scoped to tenants_v4)
    op.create_table(
        'workspaces',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('tenant_id', psql.UUID(as_uuid=True), sa.ForeignKey('tenants_v4.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # -----------------------------------------------------------------
    # Row-Level Security (RLS) policies for tenant isolation
    # -----------------------------------------------------------------
    # Enable RLS on all tenant-scoped tables
    op.execute("ALTER TABLE tenants_v4 ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users_v4 ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY")

    # Tenants: restrict to the current tenant row
    op.execute(
        """
        CREATE POLICY tenants_v4_isolate
        ON tenants_v4
        FOR ALL
        TO PUBLIC
        USING (id = current_setting('app.current_tenant')::uuid)
        WITH CHECK (id = current_setting('app.current_tenant')::uuid)
        """
    )

    # Users: restrict by tenant_id
    op.execute(
        """
        CREATE POLICY users_v4_isolate
        ON users_v4
        FOR ALL
        TO PUBLIC
        USING (tenant_id = current_setting('app.current_tenant')::uuid)
        WITH CHECK (tenant_id = current_setting('app.current_tenant')::uuid)
        """
    )

    # Workspaces: restrict by tenant_id
    op.execute(
        """
        CREATE POLICY workspaces_isolate
        ON workspaces
        FOR ALL
        TO PUBLIC
        USING (tenant_id = current_setting('app.current_tenant')::uuid)
        WITH CHECK (tenant_id = current_setting('app.current_tenant')::uuid)
        """
    )


def downgrade() -> None:
    # Drop RLS policies first
    op.execute("DROP POLICY IF EXISTS workspaces_isolate ON workspaces")
    op.execute("DROP POLICY IF EXISTS users_v4_isolate ON users_v4")
    op.execute("DROP POLICY IF EXISTS tenants_v4_isolate ON tenants_v4")

    # Disable RLS (optional)
    op.execute("ALTER TABLE workspaces DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users_v4 DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants_v4 DISABLE ROW LEVEL SECURITY")

    # Drop tables (workspaces depends on tenants_v4)
    op.drop_table('workspaces')
    op.drop_table('users_v4')
    op.drop_table('tenants_v4')
