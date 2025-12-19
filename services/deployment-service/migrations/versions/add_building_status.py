"""add building status to deploymentstatus enum

Revision ID: add_building_status
Revises: 
Create Date: 2025-12-10 22:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_building_status'
down_revision = 'initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE deploymentstatus ADD VALUE IF NOT EXISTS 'building'")


def downgrade() -> None:
    # Removing enum values is not directly supported in Postgres without recreating the type
    pass
