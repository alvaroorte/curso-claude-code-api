"""Construcción y lanzamiento centralizados de los errores de la API.

Agrupa aquí las validaciones y comprobaciones que hoy se repiten (o podrían
repetirse) entre los endpoints de `app/main.py`, para que cada endpoint
delegue el "cómo" del error y solo decida "cuándo" dispararlo.
"""

import unicodedata
from datetime import UTC, datetime

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import Connection

_INVISIBLE_TITLE_CATEGORIES = {"Cc", "Cf", "Zl", "Zp", "Zs"}


def normalize_title(title: str) -> str:
    stripped = title.strip()
    if all(unicodedata.category(char) in _INVISIBLE_TITLE_CATEGORIES for char in stripped):
        raise HTTPException(
            status_code=422, detail="title must contain a visible character"
        )
    return stripped


def validate_due_at(due_at: datetime | None) -> datetime | None:
    if due_at is None:
        return None
    if due_at.tzinfo is None:
        raise HTTPException(status_code=422, detail="due_at must include a timezone")
    return due_at.astimezone(UTC)


def require_project(connection: Connection, project_id: int) -> None:
    exists = connection.execute(
        text("SELECT 1 FROM projects WHERE id = :id"), {"id": project_id}
    ).one_or_none()
    if exists is None:
        raise HTTPException(status_code=404, detail=f"project {project_id} not found")


def require_state(connection: Connection, state_id: int) -> None:
    exists = connection.execute(
        text("SELECT 1 FROM states WHERE id = :id"), {"id": state_id}
    ).one_or_none()
    if exists is None:
        raise HTTPException(status_code=404, detail=f"state {state_id} not found")


def not_found(resource: str, resource_id: int) -> HTTPException:
    """Error 404 para un recurso inexistente, identificado por nombre e id."""
    return HTTPException(status_code=404, detail=f"{resource} {resource_id} not found")


def conflict_has_tasks(resource: str, resource_id: int) -> HTTPException:
    """Error 409 para un recurso que no puede borrarse por tener tareas."""
    return HTTPException(status_code=409, detail=f"{resource} {resource_id} has tasks")


def field_cannot_be_null(field: str) -> HTTPException:
    """Error 422 para un campo que el contrato no permite recibir como null."""
    return HTTPException(status_code=422, detail=f"{field} cannot be null")


class ErrorDetail(BaseModel):
    detail: str


MIXED_422_RESPONSE = {
    422: {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "schema": {
                    "oneOf": [
                        {"$ref": "#/components/schemas/HTTPValidationError"},
                        {"$ref": "#/components/schemas/ErrorDetail"},
                    ]
                }
            }
        },
    }
}
