"""add deployment_url column

Revision ID: add_deployment_url
Revises: add_building_status
Create Date: 2025-12-10 23:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_deployment_url'
down_revision = 'add_building_status'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('deployments', sa.Column('deployment_url', sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column('deployments', 'deployment_url')
