"""Store the tools that the agent is allowed to call"""

from collections.abc import Callable
from typing import Any
from time import perf_counter
from app_logging import log_event

from tools.read_tools import query_database
from tools.customer_tools import (
    get_customer, search_customers,
    create_customer, update_customer, delete_customer,
)
from tools.product_tools import (
    get_product, search_products,
    create_product, update_product, delete_product,
)
from tools.order_tools import (
    get_order, get_customer_orders,
    create_order, update_order, delete_order,
)


TOOLS: dict[str, Callable[..., dict]] = {
    "query_database": query_database,
    "get_customer": get_customer,
    "search_customers": search_customers,
    "get_product": get_product,
    "search_products": search_products,
    "get_order": get_order,
    "get_customer_orders": get_customer_orders,
    "create_customer": create_customer,
    "update_customer": update_customer,
    "delete_customer": delete_customer,
    "create_product": create_product,
    "update_product": update_product,
    "delete_product": delete_product,
    "create_order": create_order,
    "update_order": update_order,
    "delete_order": delete_order,
}


class UnknownToolError(ValueError):
    """Report a tool name that is not registered"""


def get_tool(action: str) -> Callable[..., dict]:
    """Find a tool in the allowed list or raise an error"""
    try:
        return TOOLS[action]
    except (KeyError, TypeError) as error:
        raise UnknownToolError(f"Unknown action: {action}") from error


def execute_tool(action: str, **arguments: Any) -> dict:
    """Call the selected tool and log its result status and run time"""
    started = perf_counter()
    log_event("tool_call", action=action, arguments=arguments)
    try:
        result = get_tool(action)(**arguments)
        log_event("tool_completed", action=action, success=result.get("success", False),
                  error_code=result.get("error_code"),
                  duration_ms=round((perf_counter() - started) * 1000, 2))
        return result
    except Exception as error:
        log_event("tool_failed", action=action, error_type=type(error).__name__,
                  duration_ms=round((perf_counter() - started) * 1000, 2))
        raise
