"""Wrap model failures consistently without exposing runtime exceptions."""

from errors import ModelGenerationError


def generate_text(model, messages: list[dict]) -> str:
    try:
        answer = model.generate(messages)

        if not isinstance(answer, str) or not answer.strip():
            raise ValueError(
                "The model returned an empty or non-string response"
            )

        return answer.strip()

    except Exception as error:
        raise ModelGenerationError("Qwen generation failed") from error