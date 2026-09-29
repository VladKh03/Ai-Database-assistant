"""Shared validation and result formatting for repository-backed write tools."""

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
            error=None if changed else "Record not found",
        ).model_dump(exclude_none=True)
    except Exception as error:
        return ToolResult(success=False, error=str(error)).model_dump(exclude_none=True)