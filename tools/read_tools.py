from database.queries import execute_select_query
from database.validator import SQLValidationError


def query_database(sql: str) -> dict:
    """
    Execute a validated read-only database query.
    """

    try:
        rows = execute_select_query(sql)

        return {
            "success": True,
            "rows": rows,
            "row_count": len(rows)
        }

    except SQLValidationError as error:
        return {
            "success": False,
            "error": str(error)
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }