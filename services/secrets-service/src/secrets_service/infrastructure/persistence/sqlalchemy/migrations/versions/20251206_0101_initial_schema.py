import sqlalchemy as sa
from alembic import op

revision = 'initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('secret_metadata',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('project_id', sa.String(length=255), nullable=False),
    sa.Column('deployment_id', sa.String(length=255), nullable=True),
    sa.Column('key', sa.String(length=255), nullable=False),
    sa.Column('vault_path', sa.String(length=512), nullable=False),
    sa.Column('secret_type', sa.Enum('ENV_VAR', 'API_KEY', 'DATABASE_URL', 'CERTIFICATE', name='secrettype'), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_secret_metadata_deployment_id'), 'secret_metadata', ['deployment_id'], unique=False)
    op.create_index(op.f('ix_secret_metadata_project_id'), 'secret_metadata', ['project_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_secret_metadata_project_id'), table_name='secret_metadata')
    op.drop_index(op.f('ix_secret_metadata_deployment_id'), table_name='secret_metadata')
    op.drop_table('secret_metadata')
