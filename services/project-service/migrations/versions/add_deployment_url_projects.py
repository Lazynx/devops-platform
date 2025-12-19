"""add deployment_url to projects

Revision ID: add_deployment_url_projects
Revises: add_deployment_config_id
Create Date: 2025-12-11 19:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_deployment_url_projects'
down_revision = '19a8a188c953'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('deployment_url', sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column('projects', 'deployment_url')
