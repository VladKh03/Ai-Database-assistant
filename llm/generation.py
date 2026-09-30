from errors import ModelGenerationError
from app_logging import log_event
from time import perf_counter


def generate_text(model, messages: list[dict]) -> str:
    """Log the model output and reject empty or failed responses"""
    started = perf_counter()
    try:
        answer = model.generate(messages)
        log_event("llm_raw_output", output=answer, duration_ms=round((perf_counter() - started) * 1000, 2))
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("The model returned an empty or non-string response")
        return answer.strip()
    except Exception as error:
        log_event("llm_generation_failed", error_type=type(error).__name__,
                  duration_ms=round((perf_counter() - started) * 1000, 2))
        raise ModelGenerationError("Qwen generation failed") from error
