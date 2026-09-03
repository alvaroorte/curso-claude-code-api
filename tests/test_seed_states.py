from pathlib import Path

from alembic.config import Config
from sqlalchemy import text

from alembic import command
from app.db import engine

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"

EXPECTED_CODES = {"PENDIENTE", "EN_CURSO", "BLOQUEADA", "HECHA"}


def _alembic_config() -> Config:
    return Config(str(ALEMBIC_INI))


def test_seed_migration_is_idempotent() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    command.downgrade(config, "-1")
    command.upgrade(config, "head")

    with engine.connect() as connection:
        codes = connection.execute(text("SELECT code FROM states")).scalars().all()

    assert len(codes) == 4
    assert set(codes) == EXPECTED_CODES

    command.downgrade(config, "base")
