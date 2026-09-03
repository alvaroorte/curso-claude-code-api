from pathlib import Path

from alembic.config import Config
from fastapi.testclient import TestClient

from alembic import command
from app.main import app

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"

client = TestClient(app)


def _alembic_config() -> Config:
    return Config(str(ALEMBIC_INI))


def test_get_states_returns_ordered_catalog_with_exact_schema() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    first = client.get("/states")
    second = client.get("/states")

    assert first.status_code == 200
    assert second.status_code == 200

    body = first.json()
    assert body == second.json()
    assert [state["code"] for state in body] == [
        "PENDIENTE",
        "EN_CURSO",
        "BLOQUEADA",
        "HECHA",
    ]
    for state in body:
        assert set(state.keys()) == {"id", "code"}

    command.downgrade(config, "base")
