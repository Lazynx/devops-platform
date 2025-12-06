from alembic import op
import sqlalchemy as sa


revision = 'initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('log_entries',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    sa.Column('service_name', sa.Enum('AUTH_SERVICE', 'PROJECT_SERVICE', 'CI_SERVICE', 'DEPLOYMENT_SERVICE', 'SECRETS_SERVICE', 'OBSERVABILITY_SERVICE', name='servicename'), nullable=False),
    sa.Column('level', sa.Enum('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', name='loglevel'), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('trace_id', sa.String(length=255), nullable=True),
    sa.Column('context', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_level_timestamp', 'log_entries', ['level', 'timestamp'], unique=False)
    op.create_index('idx_service_timestamp', 'log_entries', ['service_name', 'timestamp'], unique=False)
    op.create_index(op.f('ix_log_entries_level'), 'log_entries', ['level'], unique=False)
    op.create_index(op.f('ix_log_entries_service_name'), 'log_entries', ['service_name'], unique=False)
    op.create_index(op.f('ix_log_entries_timestamp'), 'log_entries', ['timestamp'], unique=False)
    op.create_index(op.f('ix_log_entries_trace_id'), 'log_entries', ['trace_id'], unique=False)
    op.create_table('metric_entries',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    sa.Column('service_name', sa.Enum('AUTH_SERVICE', 'PROJECT_SERVICE', 'CI_SERVICE', 'DEPLOYMENT_SERVICE', 'SECRETS_SERVICE', 'OBSERVABILITY_SERVICE', name='servicename'), nullable=False),
    sa.Column('metric_name', sa.String(length=255), nullable=False),
    sa.Column('metric_type', sa.Enum('COUNTER', 'GAUGE', 'HISTOGRAM', 'SUMMARY', name='metrictype'), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('unit', sa.String(length=50), nullable=True),
    sa.Column('tags', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_metric_service_timestamp', 'metric_entries', ['service_name', 'metric_name', 'timestamp'], unique=False)
    op.create_index(op.f('ix_metric_entries_metric_name'), 'metric_entries', ['metric_name'], unique=False)
    op.create_index(op.f('ix_metric_entries_service_name'), 'metric_entries', ['service_name'], unique=False)
    op.create_index(op.f('ix_metric_entries_timestamp'), 'metric_entries', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_metric_entries_timestamp'), table_name='metric_entries')
    op.drop_index(op.f('ix_metric_entries_service_name'), table_name='metric_entries')
    op.drop_index(op.f('ix_metric_entries_metric_name'), table_name='metric_entries')
    op.drop_index('idx_metric_service_timestamp', table_name='metric_entries')
    op.drop_table('metric_entries')
    op.drop_index(op.f('ix_log_entries_trace_id'), table_name='log_entries')
    op.drop_index(op.f('ix_log_entries_timestamp'), table_name='log_entries')
    op.drop_index(op.f('ix_log_entries_service_name'), table_name='log_entries')
    op.drop_index(op.f('ix_log_entries_level'), table_name='log_entries')
    op.drop_index('idx_service_timestamp', table_name='log_entries')
    op.drop_index('idx_level_timestamp', table_name='log_entries')
    op.drop_table('log_entries')
