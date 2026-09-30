from llm.generation import generate_text
from agent.prompts import build_result_prompt
from agent.history import format_history
from llm.model import qwen_model


def build_natural_response(
    user_query: str,
    tool_result,
    history: list[dict[str, str]] | None = None
) -> str:
    """
    Convert database/tool result into a natural-language answer.
    """

    prompt = build_result_prompt(
        user_query=user_query,
        result=tool_result
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a database assistant. "
                "Answer using only the provided database result. "
                "Do not invent missing information."
            )
        },
        {
            "role": "user",
                "content": format_history(history) + "Current result:\n" + prompt
        }
    ]

    response = generate_text(qwen_model, messages)

    return response.strip()
