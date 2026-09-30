"""Generate, validate, and execute one structured database write."""

from llm.generation import generate_text
from errors import failure, error_info
from agent.confirmation import pending_confirmations
from agent.tool_registry import execute_tool
from api.schemas import ToolCall
from llm.model import qwen_model
from llm.parser import AgentAction


WRITE_ACTIONS = {
    "CREATE": {"create_customer", "create_product", "create_order"},
    "UPDATE": {"update_customer", "update_product", "update_order"},
    "DELETE": {"delete_customer", "delete_product", "delete_order"},
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
- update_product: product_id OR lookup_name (the existing product name),
  plus at least one product field to change. For "Change the price of Chai",
  use {"lookup_name": "Chai", "unit_price": 25}. Do not guess product_id.
  To rename by name, use lookup_name for the old name and product_name for the new name.
- delete_product: product_id
- create_order: customer_id; optional employee_id, order_date, required_date,
  shipped_date, ship_via, freight, ship_name, ship_address, ship_city,
  ship_region, ship_postal_code, ship_country, items. Each item requires
  product_id OR product_name and quantity; unit_price and discount (0 to 1)
  are optional. If price is omitted, the tool uses the product's current price.
  Example: {"customer_id":"ALFKI","items":[{"product_name":"Chai","quantity":2}]}.
- update_order: order_id and at least one order field to change
- delete_order: order_id; its Order Details are deleted in the same transaction

Return one JSON object with action and arguments. Never return SQL.
Only include fields the user actually supplied. Never invent missing IDs or values.
If a requested write has no matching tool, do not substitute a different action.
Example for a named product:
{"action": "update_product", "arguments": {"lookup_name": "Chai", "unit_price": 25}}
"""


def run_write_pipeline(
    user_message: str, request_type: str,
    history: list[dict[str, str]] | None = None,
    session_id: str = "default",
) -> dict:
    from agent.loop import run_agent_loop

    if request_type not in WRITE_ACTIONS:
        raise ValueError(f"Unsupported write request type: {request_type}")
    return run_agent_loop(user_message, request_type, history, session_id)


def prepare_write_action(
    action: AgentAction, request_type: str,
    user_message: str, session_id: str,
) -> dict:
    """Execute one validated write, or prepare DELETE confirmation."""
    if action.action not in WRITE_ACTIONS.get(request_type, set()):
        raise ValueError(f"Action not allowed in {request_type} mode: {action.action}")
    action.arguments = ToolCall.model_validate({
        "action": action.action, "arguments": action.arguments,
    }).arguments

    lookup_name = action.arguments.get("lookup_name") if action.action == "update_product" else None
    if lookup_name is not None:
        lookup = execute_tool("search_products", name=lookup_name, exact_name=True)
        matches = lookup.get("rows", []) if lookup.get("success") else []
        if len(matches) != 1:
            problem = (
                {"success": False, "error": lookup["error"],
                 "error_code": lookup.get("error_code", "database_error"),
                 "answer": lookup["error"]}
                if not lookup.get("success")
                else failure(code="ambiguous_record" if matches else "record_not_found")
            )
            return {**problem, "request_type": request_type,
                    "action": action.action, "arguments": action.arguments}
        resolved_arguments = {
            **{key: value for key, value in action.arguments.items() if key != "lookup_name"},
            "product_id": matches[0]["ProductID"],
        }
        # Revalidate as the normal ID-based action before executing a write.
        action.arguments = ToolCall.model_validate({
            "action": "update_product", "arguments": resolved_arguments,
        }).arguments

    if request_type == "DELETE":
        lookup_tools = {
            "delete_customer": ("get_customer", "customer_id", "CompanyName", "клієнта"),
            "delete_product": ("get_product", "product_id", "ProductName", "продукт"),
            "delete_order": ("get_order", "order_id", "CustomerID", "замовлення"),
        }
        tool, id_field, label_field, entity = lookup_tools[action.action]
        lookup = execute_tool(tool, **action.arguments)
        rows = lookup.get("rows", [])
        if not lookup.get("success") or not rows:
            return {
                "success": False, "action": action.action,
                "request_type": "DELETE",
                "answer": lookup.get("error", "Запис не знайдено. Видалення не виконано."),
                "error_code": lookup.get("error_code", "record_not_found"),
            }
        record_id = action.arguments[id_field]
        label = rows[0].get(label_field, "")
        operation_id = pending_confirmations.put(session_id, {
            "action": action.action, "arguments": action.arguments,
            "user_message": user_message,
        })
        return {
            "success": False, "action": action.action,
            "request_type": "DELETE", "requires_confirmation": True,
            "arguments": action.arguments, "record_id": record_id,
            "operation_id": operation_id,
            "answer": (
                f"Ви хочете видалити {entity} #{record_id} — {label}. "
                + ("Позиції замовлення також будуть видалені. " if action.action == "delete_order" else "")
                + "Підтвердити? Натисніть Confirm delete або напишіть «підтверджую»; «скасувати» — для скасування."
            ),
        }
    return execute_write_action(action, request_type, user_message)


def confirm_write(session_id: str, operation_id: str, confirmed: bool) -> dict:
    operation = pending_confirmations.take(session_id, operation_id)
    if operation is None:
        return {"success": False, "action": None,
                "answer": "Підтвердження відсутнє, застаріло або вже використане."}
    if not confirmed:
        return {"success": True, "action": None, "answer": "Видалення скасовано."}
    call = ToolCall.model_validate({
        "action": operation["action"], "arguments": operation["arguments"],
    })
    action = AgentAction(action=call.action, arguments=call.arguments)
    return execute_write_action(action, "DELETE", operation["user_message"])


def execute_write_action(action: AgentAction, request_type: str, user_message: str) -> dict:
    # ToolCall validates the action and arguments before this dispatch.
    # Each tool validates again and its repository owns the parameterized SQL.
    try:
        tool_result = execute_tool(action.action, **action.arguments)
    except Exception as error:
        tool_result = failure(error)

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
        result["error_code"] = tool_result.get("error_code", "database_error")
        result["answer"] = "Базу даних не змінено. " + result["error"]
        return result

    # The database commit has completed. Never retry the write just because
    # the response model fails; return a truthful fallback in that case.
    try:
        answer = generate_text(qwen_model, [
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
        ])
        result["answer"] = answer
    except Exception as error:
        error_info(error)
        result["answer"] = (
            f"Операцію {action.action} виконано для запису {result['record_id']}. "
            "Зміни збережено, але Qwen не вдалося сформувати пояснення."
        )
    return result
