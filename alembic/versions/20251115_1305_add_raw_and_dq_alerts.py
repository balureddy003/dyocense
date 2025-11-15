"""add_raw_and_dq_alerts

Revision ID: raw_dq_20251115
Revises: f8a82d1a01e2
Create Date: 2025-11-15 13:05:00+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'raw_dq_20251115'
down_revision: Union[str, None] = 'f8a82d1a01e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # raw_connector_data table (ELT stage 1)
    op.create_table(
        'raw_connector_data',
        sa.Column('raw_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('source_id', sa.UUID(), nullable=False),  # FK to data_sources.source_id
        sa.Column('source_type', sa.String(length=100), nullable=False),
        sa.Column('source_record_id', sa.String(length=255), nullable=True),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('ingested_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('processed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.PrimaryKeyConstraint('raw_id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id']),
        sa.ForeignKeyConstraint(['source_id'], ['data_sources.source_id']),
    )
    op.create_index('idx_raw_tenant_ingested', 'raw_connector_data', ['tenant_id', sa.text('ingested_at DESC')], unique=False)
    op.create_index('idx_raw_source_record', 'raw_connector_data', ['source_id', 'source_record_id'], unique=True)

    # data_quality_alerts table
    op.create_table(
        'data_quality_alerts',
        sa.Column('alert_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('metric_id', sa.UUID(), nullable=True),  # references business_metrics.metric_id
        sa.Column('alert_type', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False, server_default='warning'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('alert_id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id']),
        # Optional link to business_metrics if present
        sa.ForeignKeyConstraint(['metric_id'], ['business_metrics.metric_id']),
    )
    op.create_index(
        'idx_dq_alerts_open',
        'data_quality_alerts',
        ['tenant_id', sa.text('created_at DESC')],
        unique=False,
        postgresql_where=sa.text('NOT resolved')
    )


def downgrade() -> None:
    op.drop_index('idx_dq_alerts_open', table_name='data_quality_alerts')
    op.drop_table('data_quality_alerts')
    op.drop_index('idx_raw_source_record', table_name='raw_connector_data')
    op.drop_index('idx_raw_tenant_ingested', table_name='raw_connector_data')
    op.drop_table('raw_connector_data')
