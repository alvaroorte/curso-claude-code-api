from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import text

from app.db import engine

app = FastAPI()


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
