from pathlib import Path

from alembic.config import Config
from fastapi.testclient import TestClient

from alembic import command
from app.main import app

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"

client = TestClient(app)


def _alembic_config() -> Config:
    return Config(str(ALEMBIC_INI))


def _create_project(name: str = "Casa") -> int:
    return client.post("/projects", json={"name": name}).json()["id"]


def _pendiente_state_id() -> int:
    states = client.get("/states").json()
    return next(state["id"] for state in states if state["code"] == "PENDIENTE")


def test_create_task_returns_201_with_exact_schema() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    project_id = _create_project()
    state_id = _pendiente_state_id()

    response = client.post(
        "/tasks",
        json={
            "title": "Regar las plantas",
            "description": "Todas las macetas",
            "project_id": project_id,
            "state_id": state_id,
            "due_at": "2026-03-01T09:00:00+00:00",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == {
        "id",
        "title",
        "description",
        "project_id",
        "state_id",
        "due_at",
    }
    assert body["title"] == "Regar las plantas"
    assert body["description"] == "Todas las macetas"
    assert body["project_id"] == project_id
    assert body["state_id"] == state_id
    assert body["due_at"] == "2026-03-01T09:00:00Z"

    command.downgrade(config, "base")


def test_create_task_without_optional_fields_returns_null() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    project_id = _create_project()
    state_id = _pendiente_state_id()

    response = client.post(
        "/tasks",
        json={"title": "Tarea simple", "project_id": project_id, "state_id": state_id},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["description"] is None
    assert body["due_at"] is None

    command.downgrade(config, "base")


def test_create_task_rejects_blank_title_with_422() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    project_id = _create_project()
    state_id = _pendiente_state_id()

    response = client.post(
        "/tasks",
        json={"title": "   ", "project_id": project_id, "state_id": state_id},
    )

    assert response.status_code == 422

    command.downgrade(config, "base")


def test_create_task_rejects_title_with_only_invisible_characters() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    project_id = _create_project()
    state_id = _pendiente_state_id()

    response = client.post(
        "/tasks",
        json={"title": "\u200b\u200b", "project_id": project_id, "state_id": state_id},
    )

    assert response.status_code == 422

    command.downgrade(config, "base")


def test_create_task_with_nonexistent_project_returns_404() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    state_id = _pendiente_state_id()

    response = client.post(
        "/tasks",
        json={"title": "Tarea", "project_id": 999999, "state_id": state_id},
    )

    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}

    command.downgrade(config, "base")


def test_create_task_with_nonexistent_state_returns_404() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    project_id = _create_project()

    response = client.post(
        "/tasks",
        json={"title": "Tarea", "project_id": project_id, "state_id": 999999},
    )

    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}

    command.downgrade(config, "base")


def test_create_task_with_due_at_without_timezone_returns_422() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    project_id = _create_project()
    state_id = _pendiente_state_id()

    response = client.post(
        "/tasks",
        json={
            "title": "Tarea",
            "project_id": project_id,
            "state_id": state_id,
            "due_at": "2026-03-01T09:00:00",
        },
    )

    assert response.status_code == 422

    command.downgrade(config, "base")
