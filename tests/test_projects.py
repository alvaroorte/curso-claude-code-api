from pathlib import Path

from alembic.config import Config
from fastapi.testclient import TestClient

from alembic import command
from app.main import app

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"

client = TestClient(app)


def _alembic_config() -> Config:
    return Config(str(ALEMBIC_INI))


def test_create_project_returns_201_with_exact_schema() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    response = client.post(
        "/projects", json={"name": "Casa", "description": "Tareas del hogar"}
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == {"id", "name", "description"}
    assert body["name"] == "Casa"
    assert body["description"] == "Tareas del hogar"
    assert isinstance(body["id"], int)

    command.downgrade(config, "base")


def test_create_project_without_description_returns_null() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    response = client.post("/projects", json={"name": "Jardín"})

    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == {"id", "name", "description"}
    assert body["description"] is None

    command.downgrade(config, "base")
