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


def test_list_projects_returns_ordered_by_id_with_exact_schema() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    first_id = client.post("/projects", json={"name": "Casa"}).json()["id"]
    second_id = client.post("/projects", json={"name": "Trabajo"}).json()["id"]

    first = client.get("/projects")
    second = client.get("/projects")

    assert first.status_code == 200
    assert first.json() == second.json()
    assert [project["id"] for project in first.json()] == sorted(
        [first_id, second_id]
    )
    for project in first.json():
        assert set(project.keys()) == {"id", "name", "description"}

    command.downgrade(config, "base")


def test_get_project_by_id_returns_200_when_it_exists() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    created = client.post("/projects", json={"name": "Casa"}).json()

    response = client.get(f"/projects/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created

    command.downgrade(config, "base")


def test_get_project_by_id_returns_404_when_it_does_not_exist() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    response = client.get("/projects/999999")

    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}

    command.downgrade(config, "base")


def test_patch_updates_only_name_and_keeps_description() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    created = client.post(
        "/projects", json={"name": "Casa", "description": "Tareas del hogar"}
    ).json()

    response = client.patch(f"/projects/{created['id']}", json={"name": "Casa Grande"})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Casa Grande"
    assert body["description"] == "Tareas del hogar"

    command.downgrade(config, "base")


def test_patch_sets_description_to_null_when_sent_explicitly() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    created = client.post(
        "/projects", json={"name": "Casa", "description": "Tareas del hogar"}
    ).json()

    response = client.patch(f"/projects/{created['id']}", json={"description": None})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Casa"
    assert body["description"] is None

    command.downgrade(config, "base")


def test_patch_on_nonexistent_id_returns_404() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    response = client.patch("/projects/999999", json={"name": "Cualquiera"})

    assert response.status_code == 404
    assert set(response.json().keys()) == {"detail"}

    command.downgrade(config, "base")


def test_patch_rejects_null_name_with_422() -> None:
    config = _alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    created = client.post("/projects", json={"name": "Casa"}).json()

    response = client.patch(f"/projects/{created['id']}", json={"name": None})

    assert response.status_code == 422

    command.downgrade(config, "base")
