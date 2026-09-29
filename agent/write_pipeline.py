"""Generate, validate, and execute one structured database write."""

from agent.history import format_history
from agent.output_format import AGENT_OUTPUT_PROMPT
from agent.prompts import get_system_prompt
from agent.tool_registry import execute_tool
from llm.model import qwen_model
from llm.parser import LLMOutputError, generate_and_parse


WRITE_ACTIONS = {
    "CREATE": {"create_customer", "create_product", "create_order"},
    "UPDATE": {"update_customer", "update_product", "update_order"},
    "DELETE": {"delete_customer"},
}

WRITE_TOOL_GUIDE = """
Available write tools and their arguments:
- create_customer: customer_id, company_name; optional contact_name,
  contact_title, address, city, region, postal_code, country, phone, fax
- update_customer: customer_id and at least one field to change from the list above
- delete_customer: customer_id
- create_product: product_name; optional supplier_id, category_id,
  quantity_per_unit, unit_price, units_in_stock, units_on_order,
  reorder_level, discontinued
- update_product: product_id and at least one product field to change
- create_order: customer_id; optional employee_id, order_date, required_date,
  shipped_date, ship_via, freight, ship_name, ship_address, ship_city,
  ship_region, ship_postal_code, ship_country
- update_order: order_id and at least one order field to change

Return one JSON object with action and arguments. Never return SQL.
Only include fields the user actually supplied. Never invent missing IDs or values.
If a requested write has no matching tool, do not substitute a different action.
"""


def build_write_messages(
    user_message: str, request_type: str,
    history: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                get_system_prompt() + "\n" + AGENT_OUTPUT_PROMPT
                + "\nYou are in " + request_type + " mode.\n"
                + WRITE_TOOL_GUIDE
                + "\nAllowed actions for this request: "
                + ", ".join(sorted(WRITE_ACTIONS[request_type]))
            ),
        },
        {
            "role": "user",
            "content": format_history(history) + "Current user request:\n" + user_message,
        },
    ]


def run_write_pipeline(
    user_message: str, request_type: str,
    history: list[dict[str, str]] | None = None,
) -> dict:
    if request_type not in WRITE_ACTIONS:
        raise ValueError(f"Unsupported write request type: {request_type}")

    try:
        action = generate_and_parse(
            model=qwen_model,
            messages=build_write_messages(user_message, request_type, history),
            allowed_actions=WRITE_ACTIONS[request_type],
        )
    except LLMOutputError as error:
        return {
            "success": False,
            "request_type": request_type,
            "action": None,
            "error": str(error),
            "answer": "The request could not be converted into a supported write action.",
        }

    # ToolCall validates the action and arguments before this dispatch.
    # Each tool validates again and its repository owns the parameterized SQL.
    try:
        tool_result = execute_tool(action.action, **action.arguments)
    except Exception as error:
        tool_result = {"success": False, "error": str(error)}

    result = {
        "success": tool_result.get("success", False),
        "request_type": request_type,
        "action": action.action,
        "arguments": action.arguments,
        "rowcount": tool_result.get("rowcount", 0),
        "record_id": tool_result.get("record_id"),
    }
    if not result["success"]:
        result["error"] = tool_result.get("error", "Database write failed")
        result["answer"] = f"The database was not changed: {result['error']}"
        return result

    # The database commit has completed. Never retry the write just because
    # the response model fails; return a truthful fallback in that case.
    try:
        answer = qwen_model.generate([
            {
                "role": "system",
                "content": (
                    "The database write succeeded. Answer briefly in the user's language. "
                    "Use only the confirmed action, arguments and database result. "
                    "Do not claim any other changes."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"User request: {user_message}\n"
                    f"Confirmed action: {action.action}\n"
                    f"Validated arguments: {action.arguments}\n"
                    f"Database result: {tool_result}"
                ),
            },
        ]).strip()
        result["answer"] = answer or f"{action.action} succeeded (record {result['record_id']})."
    except Exception:
        result["answer"] = f"{action.action} succeeded (record {result['record_id']})."
    return result