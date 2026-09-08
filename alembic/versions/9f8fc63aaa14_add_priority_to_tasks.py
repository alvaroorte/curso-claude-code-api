"""add priority to tasks

Revision ID: 9f8fc63aaa14
Revises: e70c34e05f8a
Create Date: 2026-09-07 20:31:38.175188

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9f8fc63aaa14'
down_revision: str | Sequence[str] | None = 'e70c34e05f8a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("tasks", sa.Column("priority", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tasks", "priority")
