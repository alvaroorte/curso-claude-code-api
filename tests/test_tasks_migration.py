from pathlib import Path

from alembic.config import Config
from sqlalchemy import inspect

from alembic import command
from app.db import engine

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def _alembic_config() -> Config:
    return Config(str(ALEMBIC_INI))


def test_upgrade_creates_tasks_table_and_downgrade_removes_it() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")

    command.upgrade(config, "head")
    with engine.connect() as connection:
        assert "tasks" in inspect(connection).get_table_names()

    command.downgrade(config, "base")
    with engine.connect() as connection:
        assert "tasks" not in inspect(connection).get_table_names()
