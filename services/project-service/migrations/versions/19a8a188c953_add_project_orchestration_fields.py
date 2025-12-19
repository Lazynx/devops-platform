"""initial migration

Revision ID: 19a8a188c953
Revises: 
Create Date: 2025-12-07 00:30:52.109173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '19a8a188c953'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy.dialects.postgresql import ENUM

def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Create Enums using DO blocks for idempotency
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'projectstatus') THEN
            CREATE TYPE projectstatus AS ENUM ('initializing', 'secrets_pending', 'deployment_pending', 'ready', 'active', 'paused', 'deleted', 'failed');
        ELSE
            -- Attempt to add values if they don't exist
            NULL;
        END IF;
    END
    $$;
    """)

    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'secretsstatus') THEN
            CREATE TYPE secretsstatus AS ENUM ('pending', 'creating', 'ready', 'failed');
        END IF;
    END
    $$;
    """)

    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'deploymentstatus') THEN
            CREATE TYPE deploymentstatus AS ENUM ('pending', 'creating', 'ready', 'failed');
        END IF;
    END
    $$;
    """)

    # Create Table if it doesn't exist
    if not inspector.has_table('projects'):
        op.create_table(
            'projects',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('owner_id', sa.String(255), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('github_repo_url', sa.String(512), nullable=True),
            sa.Column('github_webhook_id', sa.Integer(), nullable=True),
            sa.Column('github_webhook_secret', sa.String(512), nullable=True),
            sa.Column('language', sa.String(255), nullable=True),
            sa.Column('framework', sa.String(255), nullable=True),
            sa.Column('root_directory', sa.String(255), nullable=False, server_default='./'),
            sa.Column('install_command', sa.String(255), nullable=True),
            sa.Column('build_command', sa.String(255), nullable=True),
            sa.Column('start_command', sa.String(255), nullable=True),
            sa.Column('status', ENUM('initializing', 'secrets_pending', 'deployment_pending', 'ready', 'active', 'paused', 'deleted', 'failed', name='projectstatus', create_type=False), nullable=False),
            sa.Column('deployment_config_id', sa.UUID(), nullable=True),
            sa.Column('secrets_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('secrets_status', ENUM('pending', 'creating', 'ready', 'failed', name='secretsstatus', create_type=False), nullable=True),
            sa.Column('deployment_status', ENUM('pending', 'creating', 'ready', 'failed', name='deploymentstatus', create_type=False), nullable=True),
            sa.Column('last_error_message', sa.Text(), nullable=True),
            sa.Column('last_error_step', sa.String(50), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )
        
        op.create_index('ix_projects_secrets_status', 'projects', ['secrets_status'])
        op.create_index('ix_projects_deployment_status', 'projects', ['deployment_status'])
    else:
        # If table exists, ensure columns exist
        existing_columns = [c['name'] for c in inspector.get_columns('projects')]
        
        if 'deployment_config_id' not in existing_columns:
            op.add_column('projects', sa.Column('deployment_config_id', sa.UUID(), nullable=True))
        if 'secrets_count' not in existing_columns:
            op.add_column('projects', sa.Column('secrets_count', sa.Integer(), nullable=False, server_default='0'))
        if 'secrets_status' not in existing_columns:
            op.add_column('projects', sa.Column('secrets_status', ENUM('pending', 'creating', 'ready', 'failed', name='secretsstatus', create_type=False), nullable=True))
            op.create_index('ix_projects_secrets_status', 'projects', ['secrets_status'])
        if 'deployment_status' not in existing_columns:
            op.add_column('projects', sa.Column('deployment_status', ENUM('pending', 'creating', 'ready', 'failed', name='deploymentstatus', create_type=False), nullable=True))
            op.create_index('ix_projects_deployment_status', 'projects', ['deployment_status'])
        if 'last_error_message' not in existing_columns:
            op.add_column('projects', sa.Column('last_error_message', sa.Text(), nullable=True))
        if 'last_error_step' not in existing_columns:
            op.add_column('projects', sa.Column('last_error_step', sa.String(50), nullable=True))


def downgrade() -> None:
    # We can't easily idempotent downgrade without similar checks, 
    # but usually downgrade is destructive anyway.
    op.drop_index('ix_projects_deployment_status', 'projects')
    op.drop_index('ix_projects_secrets_status', 'projects')
    op.drop_table('projects')
    op.execute("DROP TYPE deploymentstatus")
    op.execute("DROP TYPE secretsstatus")
    op.execute("DROP TYPE projectstatus")
