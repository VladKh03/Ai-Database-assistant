"""Central allowlist and dispatcher for executable database tools."""

from collections.abc import Callable
from typing import Any

from tools.read_tools import query_database


TOOLS: dict[str, Callable[..., dict]] = {
    "query_database": query_database,
}


class UnknownToolError(ValueError):
    """Raised when an action is not registered as an executable tool."""


def get_tool(action: str) -> Callable[..., dict]:
    try:
        return TOOLS[action]
    except (KeyError, TypeError) as error:
        raise UnknownToolError(f"Unknown action: {action}") from error


def execute_tool(action: str, **arguments: Any) -> dict:
    """Execute a registered tool with its validated arguments."""
    return get_tool(action)(**arguments)