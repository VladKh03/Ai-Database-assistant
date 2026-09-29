"""Central allowlist and dispatcher for executable database tools."""

from collections.abc import Callable
from typing import Any

from tools.read_tools import query_database
from tools.customer_tools import (
    get_customer, search_customers,
    create_customer, update_customer, delete_customer,
)
from tools.product_tools import (
    get_product, search_products,
    create_product, update_product, delete_product,
)
from tools.write_tools import (
    create_order, update_order,
)


TOOLS: dict[str, Callable[..., dict]] = {
    "query_database": query_database,
    "get_customer": get_customer,
    "search_customers": search_customers,
    "get_product": get_product,
    "search_products": search_products,
    "create_customer": create_customer,
    "update_customer": update_customer,
    "delete_customer": delete_customer,
    "create_product": create_product,
    "update_product": update_product,
    "delete_product": delete_product,
    "create_order": create_order,
    "update_order": update_order,
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