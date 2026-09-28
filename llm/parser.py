import json
import re
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from api.schemas import ToolCall
from agent.tool_registry import UnknownToolError, get_tool


class LLMOutputError(Exception):
    """
    Raised when LLM output cannot be parsed or validated
    """
    pass


class UnknownActionError(LLMOutputError):
    """Raised for an action outside the executable tool allowlist."""


@dataclass
class AgentAction:
    action: str
    query: str | None = None
    arguments: dict[str, Any] | None = None


def extract_json(text: str) -> str:
    """
    Extract first JSON object from model output
    """

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
    """
    Parse JSON from raw model output
    """

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
    """
    Validate agent JSON structure
    """

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

    return AgentAction(
        action=tool_call.action,
        query=tool_call.query,
        arguments=tool_call.arguments
    )


def parse_agent_output(
    text: str,
    allowed_actions: set[str] | None = None
) -> AgentAction:
    """
    Parse and validate raw LLM output
    """

    data = parse_json(text)

    return validate_agent_output(
        data,
        allowed_actions=allowed_actions
    )

def repair_agent_output(
    model,
    invalid_output: str,
    error_message: str
) -> str:
    """
    Ask model once to repair invalid JSON output
    """

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

    return model.generate(messages)

def generate_and_parse(
    model,
    messages: list[dict],
    allowed_actions: set[str]
) -> AgentAction:
    """
    Generate agent output and retry parsing once
    """

    raw_output = model.generate(messages)

    try:
        return parse_agent_output(
            raw_output,
            allowed_actions
        )

    except UnknownActionError:
        # Never turn an unregistered action into an executable one via repair.
        raise

    except LLMOutputError as first_error:
        repaired_output = repair_agent_output(
            model=model,
            invalid_output=raw_output,
            error_message=str(first_error)
        )

        return parse_agent_output(
            repaired_output,
            allowed_actions
        )
