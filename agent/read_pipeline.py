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
    "query_database"
}


def build_read_messages(
    user_query: str,
    history: list[dict[str, str]] | None = None
) -> list[dict]:
    """
    Build messages for READ SQL generation
    """

    system_prompt = (
        get_system_prompt()
        + "\n\n"
        + AGENT_OUTPUT_PROMPT
        + """

For this request you are in READ mode.

You must:
- use action "query_database"
- generate exactly one SELECT query
- never generate INSERT, UPDATE or DELETE
- return valid JSON only
- use recent conversation and tool results to resolve references in the current request
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
    -> SELECT
    -> validation
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

        # 2. Extract generated SELECT query
        sql = action.query

        if not sql:
            return {
                "success": False,
                "answer": (
                    "The model did not generate "
                    "a database query."
                )
            }

        # 3. Execute through read tool
        # Registry dispatches to query_database, which validates the SQL.
        database_result = execute_tool(action.action, sql=sql)

        # 4. Check database execution
        if not database_result.get(
            "success",
            False
        ):
            return {
                "success": False,
                "query": sql,
                "error": database_result.get(
                    "error"
                ),
                "answer": (
                    "The database query could "
                    "not be executed."
                )
            }

        # 5. Convert database result
        # into natural-language response
        answer = build_natural_response(
            user_query=user_query,
            tool_result=database_result,
            history=history
        )

        return {
            "success": True,
            "action": action.action,
            "query": sql,
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
