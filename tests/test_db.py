from sqlalchemy import text

from app.db import engine


def test_select_1_returns_1() -> None:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        assert result.scalar_one() == 1
