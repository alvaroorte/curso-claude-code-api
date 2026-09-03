"""seed states catalog

Revision ID: f84889a78c54
Revises: 65c1e1fe2aac
Create Date: 2026-09-02 20:11:20.382573

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f84889a78c54'
down_revision: str | Sequence[str] | None = '65c1e1fe2aac'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

states_table = sa.table(
    "states",
    sa.column("code", sa.String),
    sa.column("sort_order", sa.Integer),
)

STATES = [
    {"code": "PENDIENTE", "sort_order": 1},
    {"code": "EN_CURSO", "sort_order": 2},
    {"code": "BLOQUEADA", "sort_order": 3},
    {"code": "HECHA", "sort_order": 4},
]


def upgrade() -> None:
    """Upgrade schema."""
    stmt = pg_insert(states_table).values(STATES).on_conflict_do_nothing(
        index_elements=["code"]
    )
    op.execute(stmt)


def downgrade() -> None:
    """Downgrade schema."""
    codes = [state["code"] for state in STATES]
    op.execute(states_table.delete().where(states_table.c.code.in_(codes)))
