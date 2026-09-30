from app_logging import log_event
from llm.generation import generate_text
import json
import re
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from api.schemas import ToolCall
from agent.tool_registry import UnknownToolError, get_tool


class LLMOutputError(Exception):
    """Report model output that cannot be read or validated"""
    pass


class UnknownActionError(LLMOutputError):
    """Report an action that is not allowed"""


@dataclass
class AgentAction:
    """Store one validated tool name and its input"""
    action: str
    query: str | None = None
    arguments: dict[str, Any] | None = None


def extract_json(text: str) -> str:
    """Find the JSON object in the model response"""

    text = text.strip()

    if text.startswith("{") and text.endswith("}"):
        return text

    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL
    )

    if not match:
        raise LLMOutputError(
            "No JSON object found in model output"
        )

    return match.group(0)


def parse_json(text: str) -> dict:
    """Convert the model JSON text into Python data"""

    json_text = extract_json(text)

    try:
        return json.loads(json_text)

    except json.JSONDecodeError as error:
        raise LLMOutputError(
            f"Invalid JSON: {error}"
        ) from error


def validate_agent_output(
    data: dict,
    allowed_actions: set[str] | None = None
) -> AgentAction:
    """Check that the action and its arguments are allowed"""

    if not isinstance(data, dict):
        raise LLMOutputError(
            "Agent output must be a JSON object"
        )

    action = data.get("action")

    if not action:
        raise LLMOutputError(
            "Missing 'action' field"
        )

    if not isinstance(action, str):
        raise LLMOutputError(
            "'action' must be a string"
        )

    try:
        get_tool(action)
    except UnknownToolError as error:
        raise UnknownActionError(str(error)) from error

    if allowed_actions is not None and action not in allowed_actions:
        raise UnknownActionError(f"Action not allowed in this mode: {action}")

    try:
        tool_call = ToolCall.model_validate(data)
    except ValidationError as error:
        raise LLMOutputError(str(error)) from error

    log_event("parsed_action", action=tool_call.action, query=tool_call.query, arguments=tool_call.arguments)
    return AgentAction(
        action=tool_call.action,
        query=tool_call.query,
        arguments=tool_call.arguments
    )


def repair_agent_output(
    model,
    invalid_output: str,
    error_message: str
) -> str:
    """Ask the model once to fix an invalid JSON response"""

    messages = [
        {
            "role": "system",
            "content": """
You repair malformed agent outputs.

Return valid JSON only.

Do not explain anything.
Do not use markdown.
Do not change the intended action unless required.
"""
        },
        {
            "role": "user",
            "content": f"""
The following output is invalid:

{invalid_output}

Validation error:

{error_message}

Return a corrected valid JSON object.
"""
        }
    ]

    return generate_text(model, messages)
