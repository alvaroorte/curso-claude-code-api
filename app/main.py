from fastapi import FastAPI
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
