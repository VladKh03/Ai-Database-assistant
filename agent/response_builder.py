from agent.prompts import build_result_prompt
from llm.model import qwen_model


def build_natural_response(
    user_query: str,
    tool_result
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
            "content": prompt
        }
    ]

    response = qwen_model.generate(messages)

    return response.strip()