import unicodedata
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, field_serializer
from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.db import engine

app = FastAPI()

_INVISIBLE_TITLE_CATEGORIES = {"Cc", "Cf", "Zl", "Zp", "Zs"}


def _normalize_title(title: str) -> str:
    stripped = title.strip()
    if all(unicodedata.category(char) in _INVISIBLE_TITLE_CATEGORIES for char in stripped):
        raise HTTPException(
            status_code=422, detail="title must contain a visible character"
        )
    return stripped


def _validate_due_at(due_at: datetime | None) -> datetime | None:
    if due_at is None:
        return None
    if due_at.tzinfo is None:
        raise HTTPException(status_code=422, detail="due_at must include a timezone")
    return due_at.astimezone(UTC)


def _require_project(connection: Connection, project_id: int) -> None:
    exists = connection.execute(
        text("SELECT 1 FROM projects WHERE id = :id"), {"id": project_id}
    ).one_or_none()
    if exists is None:
        raise HTTPException(status_code=404, detail=f"project {project_id} not found")


def _require_state(connection: Connection, state_id: int) -> None:
    exists = connection.execute(
        text("SELECT 1 FROM states WHERE id = :id"), {"id": state_id}
    ).one_or_none()
    if exists is None:
        raise HTTPException(status_code=404, detail=f"state {state_id} not found")


class State(BaseModel):
    id: int
    code: str


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class Project(BaseModel):
    id: int
    name: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    project_id: int
    state_id: int
    due_at: datetime | None = None


class Task(BaseModel):
    id: int
    title: str
    description: str | None = None
    project_id: int
    state_id: int
    due_at: datetime | None = None

    @field_serializer("due_at")
    def _serialize_due_at(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.astimezone(UTC).replace(microsecond=0).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/states")
def list_states() -> list[State]:
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT id, code FROM states ORDER BY sort_order, id")
        )
        return [State(id=row.id, code=row.code) for row in rows]


@app.post("/projects", status_code=201)
def create_project(payload: ProjectCreate) -> Project:
    with engine.begin() as connection:
        row = connection.execute(
            text(
                "INSERT INTO projects (name, description) "
                "VALUES (:name, :description) "
                "RETURNING id, name, description"
            ),
            {"name": payload.name, "description": payload.description},
        ).one()
    return Project(id=row.id, name=row.name, description=row.description)


@app.get("/projects")
def list_projects() -> list[Project]:
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT id, name, description FROM projects ORDER BY id")
        )
        return [
            Project(id=row.id, name=row.name, description=row.description)
            for row in rows
        ]


@app.get("/projects/{project_id}")
def get_project(project_id: int) -> Project:
    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT id, name, description FROM projects WHERE id = :id"),
            {"id": project_id},
        ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail=f"project {project_id} not found")
    return Project(id=row.id, name=row.name, description=row.description)


@app.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: int) -> Response:
    with engine.begin() as connection:
        result = connection.execute(
            text("DELETE FROM projects WHERE id = :id"), {"id": project_id}
        )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"project {project_id} not found")
    return Response(status_code=204)


@app.patch("/projects/{project_id}")
def update_project(project_id: int, payload: ProjectUpdate) -> Project:
    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates and updates["name"] is None:
        raise HTTPException(status_code=422, detail="name cannot be null")

    with engine.begin() as connection:
        if updates:
            set_clause = ", ".join(f"{field} = :{field}" for field in updates)
            row = connection.execute(
                text(
                    f"UPDATE projects SET {set_clause} WHERE id = :id "
                    "RETURNING id, name, description"
                ),
                {**updates, "id": project_id},
            ).one_or_none()
        else:
            row = connection.execute(
                text("SELECT id, name, description FROM projects WHERE id = :id"),
                {"id": project_id},
            ).one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail=f"project {project_id} not found")
    return Project(id=row.id, name=row.name, description=row.description)


def _task_from_row(row) -> Task:
    return Task(
        id=row.id,
        title=row.title,
        description=row.description,
        project_id=row.project_id,
        state_id=row.state_id,
        due_at=row.due_at,
    )


@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate) -> Task:
    title = _normalize_title(payload.title)
    due_at = _validate_due_at(payload.due_at)

    with engine.begin() as connection:
        _require_project(connection, payload.project_id)
        _require_state(connection, payload.state_id)
        row = connection.execute(
            text(
                "INSERT INTO tasks (title, description, project_id, state_id, due_at) "
                "VALUES (:title, :description, :project_id, :state_id, :due_at) "
                "RETURNING id, title, description, project_id, state_id, due_at"
            ),
            {
                "title": title,
                "description": payload.description,
                "project_id": payload.project_id,
                "state_id": payload.state_id,
                "due_at": due_at,
            },
        ).one()
    return _task_from_row(row)


@app.get("/tasks")
def list_tasks(project_id: int | None = None, state_id: int | None = None) -> list[Task]:
    filters = []
    params: dict[str, int] = {}
    if project_id is not None:
        filters.append("project_id = :project_id")
        params["project_id"] = project_id
    if state_id is not None:
        filters.append("state_id = :state_id")
        params["state_id"] = state_id

    query = "SELECT id, title, description, project_id, state_id, due_at FROM tasks"
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY id"

    with engine.connect() as connection:
        rows = connection.execute(text(query), params)
        return [_task_from_row(row) for row in rows]


@app.get("/tasks/{task_id}")
def get_task(task_id: int) -> Task:
    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT id, title, description, project_id, state_id, due_at "
                "FROM tasks WHERE id = :id"
            ),
            {"id": task_id},
        ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail=f"task {task_id} not found")
    return _task_from_row(row)
