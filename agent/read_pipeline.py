"""Start the read workflow"""

from agent.loop import run_agent_loop


def run_read_pipeline(
    user_query: str,
    history: list[dict[str, str]] | None = None,
) -> dict:
    """Start the agent loop with read tools only"""
    return run_agent_loop(user_query, "READ", history)
