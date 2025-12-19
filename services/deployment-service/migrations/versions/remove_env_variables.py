"""remove env_variables

Revision ID: remove_env_variables
Revises: add_deployment_url
Create Date: 2025-12-12 22:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'remove_env_variables'
down_revision: Union[str, None] = 'add_deployment_url'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('deployment_configs', 'env_variables')


def downgrade() -> None:
    op.add_column('deployment_configs', sa.Column('env_variables', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False, server_default=sa.text("'{}'::json")))
