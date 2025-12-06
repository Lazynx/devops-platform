from alembic import op
import sqlalchemy as sa


revision = 'initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('deployment_configs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('project_id', sa.String(length=255), nullable=False),
    sa.Column('github_repo_url', sa.String(length=512), nullable=False),
    sa.Column('environment', sa.Enum('DEVELOPMENT', 'STAGING', 'PRODUCTION', name='environment'), nullable=False),
    sa.Column('instance_count', sa.Integer(), nullable=False),
    sa.Column('cpu_limit', sa.Float(), nullable=False),
    sa.Column('memory_limit', sa.Integer(), nullable=False),
    sa.Column('auto_scaling_enabled', sa.Boolean(), nullable=False),
    sa.Column('min_instances', sa.Integer(), nullable=False),
    sa.Column('max_instances', sa.Integer(), nullable=False),
    sa.Column('port', sa.Integer(), nullable=False),
    sa.Column('health_check_path', sa.String(length=255), nullable=False),
    sa.Column('env_variables', sa.JSON(), nullable=False),
    sa.Column('dockerfile_path', sa.String(length=255), nullable=False),
    sa.Column('docker_build_context', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('deployments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('config_id', sa.UUID(), nullable=False),
    sa.Column('project_id', sa.String(length=255), nullable=False),
    sa.Column('version', sa.String(length=255), nullable=False),
    sa.Column('commit_sha', sa.String(length=255), nullable=True),
    sa.Column('image_url', sa.String(length=512), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'DEPLOYING', 'RUNNING', 'FAILED', 'STOPPED', name='deploymentstatus'), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('stopped_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['config_id'], ['deployment_configs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('deployments')
    op.drop_table('deployment_configs')
