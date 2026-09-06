from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import text

from app.db import engine

app = FastAPI()


class State(BaseModel):
    id: int
    code: str


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
