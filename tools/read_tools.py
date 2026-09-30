from errors import error_info
from database.repositories import QueryRepository
from api.schemas import ToolResult


def query_database(sql: str, repository: QueryRepository | None = None) -> dict:
    """Run a checked SELECT query and return a safe result"""

    try:
        rows = (repository or QueryRepository()).select(sql)

        return ToolResult(
            success=True,
            rows=rows,
            row_count=len(rows)
        ).model_dump(exclude_none=True)

    except Exception as error:
        return ToolResult(success=False, **error_info(error)).model_dump(
            exclude_none=True
        )
