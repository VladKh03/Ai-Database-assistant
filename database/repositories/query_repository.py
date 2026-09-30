from sqlalchemy import text
from app_logging import log_event
from sqlalchemy.engine import Engine

from database.connection import engine
from database.validator import validate_select_query


class QueryRepository:
    """Check model SQL before reading from SQLite"""
    def __init__(self, db_engine: Engine | None = None):
        self.engine = db_engine if db_engine is not None else engine

    def select(self, sql: str, params: dict | None = None) -> list[dict]:
        """Validate one SELECT query and return rows as dictionaries"""
        log_event("generated_sql", sql=sql)
        validated_sql = validate_select_query(sql)

        log_event("validated_sql", sql=validated_sql)
        with self.engine.connect() as connection:
            result = connection.execute(text(validated_sql), params or {})
            return [dict(row) for row in result.mappings()]
