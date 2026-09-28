from database.queries import execute_select_query
from database.validator import SQLValidationError
from api.schemas import ToolResult


def query_database(sql: str) -> dict:
    """
    Execute a validated read-only database query.
    """

    try:
        rows = execute_select_query(sql)

        return ToolResult(
            success=True,
            rows=rows,
            row_count=len(rows)
        ).model_dump(exclude_none=True)

    except SQLValidationError as error:
        return ToolResult(success=False, error=str(error)).model_dump(
            exclude_none=True
        )

    except Exception as error:
        return ToolResult(success=False, error=str(error)).model_dump(
            exclude_none=True
        )