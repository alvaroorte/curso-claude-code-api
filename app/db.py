import os

from sqlalchemy import URL, Engine, create_engine


def get_database_url() -> URL:
    return URL.create(
        drivername="postgresql+psycopg",
        username=os.environ.get("POSTGRES_USER", "taskflow"),
        password=os.environ.get("POSTGRES_PASSWORD", "taskflow-local-dev"),
        host="localhost",
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        database=os.environ.get("POSTGRES_DB", "taskflow"),
    )


engine: Engine = create_engine(get_database_url())
