"""Shared validation and result formatting for repository-backed write tools."""

from errors import error_info, MESSAGES
from collections.abc import Callable

from pydantic import BaseModel

from api.schemas import ToolResult


def write_result(model: type[BaseModel], operation: Callable[[dict], dict], arguments: dict) -> dict:
    try:
        request = model.model_validate(arguments)
        result = operation(request.model_dump(exclude_unset=True, mode="json"))
        changed = result["rowcount"] > 0
        return ToolResult(
            success=changed,
            rowcount=result["rowcount"],
            record_id=result.get("record_id"),
            error=None if changed else MESSAGES["record_not_found"],
            error_code=None if changed else "record_not_found",
        ).model_dump(exclude_none=True)
    except Exception as error:
        return ToolResult(success=False, **error_info(error)).model_dump(exclude_none=True)


def read_result(rows: list[dict], *, required: bool = False) -> dict:
    if required and not rows:
        return ToolResult(
            success=False, rows=[], row_count=0,
            error_code="record_not_found", error=MESSAGES["record_not_found"],
        ).model_dump(exclude_none=True)
    return ToolResult(success=True, rows=rows, row_count=len(rows)).model_dump(exclude_none=True)
