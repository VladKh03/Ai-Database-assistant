from sqlalchemy import text

from database.connection import engine
from database.validator import validate_select_query


def execute_select_query(
    sql: str,
    params: dict | None = None
) -> list[dict]:
    """
    Validate and execute a read-only SELECT query.

    Returns rows as a list of dictionaries.
    """

    params = params or {}

    validated_sql = validate_select_query(sql)

    with engine.connect() as connection:
        result = connection.execute(
            text(validated_sql),
            params
        )

        rows = result.mappings().all()

    return [
        dict(row)
        for row in rows
    ]