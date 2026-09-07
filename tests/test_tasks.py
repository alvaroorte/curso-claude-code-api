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


def test_list_tasks_returns_ordered_by_id_with_exact_schema() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    project_id = _create_project()
    state_id = _pendiente_state_id()

    first_id = client.post(
        "/tasks", json={"title": "Primera", "project_id": project_id, "state_id": state_id}
    ).json()["id"]
    second_id = client.post(
        "/tasks", json={"title": "Segunda", "project_id": project_id, "state_id": state_id}
    ).json()["id"]

    first = client.get("/tasks")
    second = client.get("/tasks")

    assert first.status_code == 200
    assert first.json() == second.json()
    assert [task["id"] for task in first.json()] == sorted([first_id, second_id])
    for task in first.json():
        assert set(task.keys()) == {
            "id",
            "title",
            "description",
            "project_id",
            "state_id",
            "due_at",
        }

    command.downgrade(config, "base")


def test_list_tasks_filters_by_project_id_and_state_id_alone_and_combined() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    states = client.get("/states").json()
    pendiente_id = next(s["id"] for s in states if s["code"] == "PENDIENTE")
    en_curso_id = next(s["id"] for s in states if s["code"] == "EN_CURSO")

    project_a = _create_project("Proyecto A")
    project_b = _create_project("Proyecto B")

    task_a_pendiente = client.post(
        "/tasks",
        json={"title": "A pendiente", "project_id": project_a, "state_id": pendiente_id},
    ).json()["id"]
    task_a_en_curso = client.post(
        "/tasks",
        json={"title": "A en curso", "project_id": project_a, "state_id": en_curso_id},
    ).json()["id"]
    task_b_pendiente = client.post(
        "/tasks",
        json={"title": "B pendiente", "project_id": project_b, "state_id": pendiente_id},
    ).json()["id"]

    by_project = client.get(f"/tasks?project_id={project_a}").json()
    assert {task["id"] for task in by_project} == {task_a_pendiente, task_a_en_curso}

    by_state = client.get(f"/tasks?state_id={pendiente_id}").json()
    assert {task["id"] for task in by_state} == {task_a_pendiente, task_b_pendiente}

    combined = client.get(f"/tasks?project_id={project_a}&state_id={pendiente_id}").json()
    assert {task["id"] for task in combined} == {task_a_pendiente}

    command.downgrade(config, "base")


def test_list_tasks_with_nonexistent_filter_returns_empty_list() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    project_id = _create_project()
    state_id = _pendiente_state_id()
    client.post(
        "/tasks", json={"title": "Tarea", "project_id": project_id, "state_id": state_id}
    )

    response = client.get("/tasks?project_id=999999")

    assert response.status_code == 200
    assert response.json() == []

    command.downgrade(config, "base")


def test_get_task_by_id_returns_200_when_it_exists() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    project_id = _create_project()
    state_id = _pendiente_state_id()
    created = client.post(
        "/tasks", json={"title": "Tarea", "project_id": project_id, "state_id": state_id}
    ).json()

    response = client.get(f"/tasks/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created

    command.downgrade(config, "base")


def test_get_task_by_id_returns_404_when_it_does_not_exist() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    response = client.get("/tasks/999999")

    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}

    command.downgrade(config, "base")


def test_patch_task_updates_one_field_and_keeps_the_rest() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    project_id = _create_project()
    state_id = _pendiente_state_id()
    created = client.post(
        "/tasks",
        json={
            "title": "Regar las plantas",
            "description": "Todas",
            "project_id": project_id,
            "state_id": state_id,
        },
    ).json()

    response = client.patch(f"/tasks/{created['id']}", json={"title": "Regar el jardín"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Regar el jardín"
    assert body["description"] == "Todas"
    assert body["project_id"] == project_id
    assert body["state_id"] == state_id

    command.downgrade(config, "base")


def test_patch_task_sets_due_at_to_null_when_sent_explicitly() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    project_id = _create_project()
    state_id = _pendiente_state_id()
    created = client.post(
        "/tasks",
        json={
            "title": "Tarea",
            "project_id": project_id,
            "state_id": state_id,
            "due_at": "2026-03-01T09:00:00+00:00",
        },
    ).json()

    response = client.patch(f"/tasks/{created['id']}", json={"due_at": None})

    assert response.status_code == 200
    assert response.json()["due_at"] is None

    command.downgrade(config, "base")


def test_patch_task_rejects_blank_title_with_422() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    project_id = _create_project()
    state_id = _pendiente_state_id()
    created = client.post(
        "/tasks", json={"title": "Tarea", "project_id": project_id, "state_id": state_id}
    ).json()

    response = client.patch(f"/tasks/{created['id']}", json={"title": "   "})

    assert response.status_code == 422

    command.downgrade(config, "base")


def test_patch_task_with_nonexistent_project_returns_404() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    project_id = _create_project()
    state_id = _pendiente_state_id()
    created = client.post(
        "/tasks", json={"title": "Tarea", "project_id": project_id, "state_id": state_id}
    ).json()

    response = client.patch(f"/tasks/{created['id']}", json={"project_id": 999999})

    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}

    command.downgrade(config, "base")


def test_patch_task_with_nonexistent_state_returns_404() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    project_id = _create_project()
    state_id = _pendiente_state_id()
    created = client.post(
        "/tasks", json={"title": "Tarea", "project_id": project_id, "state_id": state_id}
    ).json()

    response = client.patch(f"/tasks/{created['id']}", json={"state_id": 999999})

    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}

    command.downgrade(config, "base")


def test_patch_task_on_nonexistent_id_returns_404() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    response = client.patch("/tasks/999999", json={"title": "Cualquiera"})

    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}

    command.downgrade(config, "base")
