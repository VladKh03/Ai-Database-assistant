from agent.prompts import get_system_prompt
from agent.history import format_history
from agent.output_format import AGENT_OUTPUT_PROMPT
from agent.response_builder import build_natural_response
from agent.tool_registry import execute_tool

from llm.model import qwen_model
from llm.parser import (
    LLMOutputError,
    generate_and_parse
)

ALLOWED_READ_ACTIONS = {
    "query_database", "get_customer", "search_customers",
    "get_product", "search_products",
    "get_order", "get_customer_orders",
}


def build_read_messages(
    user_query: str,
    history: list[dict[str, str]] | None = None
) -> list[dict]:
    """
    Build messages for validated READ tool selection
    """

    system_prompt = (
        get_system_prompt()
        + "\n\n"
        + AGENT_OUTPUT_PROMPT
        + """

For this request you are in READ mode.

You must:
- use "get_customer" with {"customer_id": "..."} for an exact customer ID
- use "search_customers" with at least one of name, country, city to find customers
- use "get_product" with {"product_id": 1} for an exact product ID
- use "search_products" with name or category_id to find products
- use "get_order" with {"order_id": 10248} to show one order and its items
- use "get_customer_orders" with {"customer_id": "ALFKI"} to list a customer's orders
- otherwise use "query_database" and generate exactly one SELECT query
- never generate INSERT, UPDATE or DELETE
- return valid JSON only
- use recent conversation and tool results to resolve references in the current request

For fixed customer, product and order tools, return an "arguments" object, not a "query".
"""
    )

    return [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": format_history(history) + "Current user request:\n" + user_query
        }
    ]


def generate_read_action(
    user_query: str,
    history: list[dict[str, str]] | None = None
):
    messages = build_read_messages(
        user_query,
        history=history
    )

    return generate_and_parse(
        model=qwen_model,
        messages=messages,
        allowed_actions=ALLOWED_READ_ACTIONS
    )


def run_read_pipeline(
    user_query: str,
    history: list[dict[str, str]] | None = None
) -> dict:
    """
    Full READ pipeline:

    User
    -> Qwen
    -> SELECT or fixed customer lookup
    -> tool validation
    -> SQLite
    -> result
    -> Qwen
    -> natural-language response
    """

    if not isinstance(user_query, str):
        return {
            "success": False,
            "answer": "User query must be a string."
        }

    user_query = user_query.strip()

    if not user_query:
        return {
            "success": False,
            "answer": "User query is empty."
        }

    try:
        # 1. Qwen generates structured READ action
        action = generate_read_action(
            user_query,
            history=history
        )

        # 2. Dispatch either validated SELECT or fixed customer lookup.
        if action.action == "query_database":
            database_result = execute_tool(action.action, sql=action.query)
        else:
            database_result = execute_tool(action.action, **action.arguments)

        # 3. Check database execution
        if not database_result.get(
            "success",
            False
        ):
            return {
                "success": False,
                "query": action.query,
                "error": database_result.get(
                    "error"
                ),
                "answer": (
                    "The database query could "
                    "not be executed."
                )
            }

        # 4. Convert database result
        # into natural-language response
        answer = build_natural_response(
            user_query=user_query,
            tool_result=database_result,
            history=history
        )

        return {
            "success": True,
            "action": action.action,
            "query": action.query,
            "rows": database_result.get(
                "rows",
                []
            ),
            "row_count": database_result.get(
                "row_count",
                0
            ),
            "answer": answer
        }

    except LLMOutputError as error:
        return {
            "success": False,
            "error": str(error),
            "answer": (
                "The model returned an invalid "
                "structured response."
            )
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error),
            "answer": (
                "An error occurred while "
                "processing the database request."
            )
        }
