"""READ entry point for the bounded agent loop."""

from agent.loop import run_agent_loop


def run_read_pipeline(
    user_query: str,
    history: list[dict[str, str]] | None = None,
) -> dict:
    return run_agent_loop(user_query, "READ", history)
