"""Read-only repository for validated SQLite queries."""

from sqlalchemy import text
from sqlalchemy.engine import Engine

from database.connection import engine
from database.validator import validate_select_query


class QueryRepository:
    def __init__(self, db_engine: Engine | None = None):
        self.engine = db_engine if db_engine is not None else engine

    def select(self, sql: str, params: dict | None = None) -> list[dict]:
        """Validate and execute one SELECT, returning rows as dictionaries."""
        validated_sql = validate_select_query(sql)

        with self.engine.connect() as connection:
            result = connection.execute(text(validated_sql), params or {})
            return [dict(row) for row in result.mappings()]