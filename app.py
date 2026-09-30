"""Start the database, model, agent, FastAPI and Gradio as one application."""

import os
import threading
import time
from urllib.error import URLError
from urllib.request import urlopen

import uvicorn
from app_logging import setup_logging


def start_backend(port: int, timeout: float = 15) -> tuple[uvicorn.Server, threading.Thread]:
    """Run FastAPI in a background thread and wait until /health responds."""
    from api.server import app as fastapi_app

    server = uvicorn.Server(
        uvicorn.Config(fastapi_app, host="127.0.0.1", port=port, log_level="info")
    )
    thread = threading.Thread(target=server.run, name="fastapi-backend", daemon=True)
    thread.start()

    deadline = time.monotonic() + timeout
    health_url = f"http://127.0.0.1:{port}/health"
    while time.monotonic() < deadline and thread.is_alive():
        if server.started:
            try:
                with urlopen(health_url, timeout=1) as response:
                    if response.status == 200:
                        return server, thread
            except (URLError, TimeoutError):
                pass
        time.sleep(0.1)

    server.should_exit = True
    thread.join(timeout=5)
    raise RuntimeError(f"FastAPI did not start successfully at {health_url}")


def main() -> None:
    setup_logging()
    from database.connection import DATABASE_PATH, check_database_connection

    if not DATABASE_PATH.is_file() or not check_database_connection():
        raise RuntimeError(f"Database is unavailable: {DATABASE_PATH}")
    print(f"Database ready: {DATABASE_PATH}")

    print("Loading Qwen...")
    from llm.model import qwen_model

    print("Creating agent...")
    from agent.agent import database_agent

    if database_agent.model is not qwen_model:
        raise RuntimeError("Agent and backend must use the same Qwen model")

    api_port = int(os.getenv("API_PORT", "8000"))
    gradio_port = int(os.getenv("GRADIO_PORT", "7860"))
    server, thread = start_backend(api_port)
    os.environ["API_BASE_URL"] = f"http://127.0.0.1:{api_port}"

    # A share link lets a Colab notebook reach its local Gradio server.
    share_default = "COLAB_RELEASE_TAG" in os.environ
    share = os.getenv("GRADIO_SHARE", str(share_default)).lower() in {"1", "true", "yes"}

    try:
        from ui.gradio_app import build_app

        build_app().launch(
            server_name="127.0.0.1",
            server_port=gradio_port,
            share=share,
            prevent_thread_lock=False,
        )
    finally:
        server.should_exit = True
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
