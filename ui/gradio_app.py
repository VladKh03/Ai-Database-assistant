"""Gradio frontend communicating with the FastAPI backend over HTTP."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import gradio as gr


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT_SECONDS = 180


def ask_backend(message: str, session_id: str | None = None) -> tuple[str, str]:
    """Send one message over HTTP and retain the backend session ID."""
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id

    request = Request(
        f"{API_BASE_URL}/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            try:
                result = json.load(response)
            except ValueError as error:
                raise RuntimeError("The backend returned an invalid response.") from error
    except HTTPError as error:
        try:
            detail = json.load(error).get("detail", "Request failed")
        except (ValueError, AttributeError):
            detail = "Request failed"
        raise RuntimeError(f"Backend error ({error.code}): {detail}") from error
    except (URLError, TimeoutError) as error:
        raise RuntimeError("Cannot connect to the backend. Start FastAPI first.") from error

    if (
        not isinstance(result, dict)
        or not isinstance(result.get("answer"), str)
        or not isinstance(result.get("session_id"), str)
    ):
        raise RuntimeError("The backend returned an invalid response.")

    return result["answer"], result["session_id"]


def send_message(
    message: str,
    history: list[dict] | None,
    session_id: str | None,
) -> tuple[str, list[dict], str | None]:
    """Update the visible conversation using only the FastAPI response."""
    message = message.strip()
    history = list(history or [])
    if not message:
        return "", history, session_id

    history.append({"role": "user", "content": message})
    try:
        answer, session_id = ask_backend(message, session_id)
    except RuntimeError as error:
        answer = str(error)

    history.append({"role": "assistant", "content": answer})
    return "", history, session_id


def clear_chat(session_id: str | None) -> tuple[str, list[dict], None]:
    """Clear visible chat and discard its backend history."""
    if session_id:
        request = Request(
            f"{API_BASE_URL}/reset",
            data=json.dumps({"session_id": session_id}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=3):
                pass
        except (URLError, TimeoutError):
            # Dropping the ID still starts a fresh session on the next message.
            pass

    return "", [], None


def build_app() -> gr.Blocks:
    with gr.Blocks() as demo:
        gr.Markdown("# AI Database Assistant")
        chatbot = gr.Chatbot(label="Chat", height=500)
        session_id = gr.State(value=None)

        with gr.Row():
            message = gr.Textbox(
                label="Message",
                placeholder="Show first order of client ALFKI",
                scale=8,
            )
            send = gr.Button("Send", variant="primary", scale=1)
            clear = gr.Button("Clear", scale=1)

        send.click(
            send_message,
            inputs=[message, chatbot, session_id],
            outputs=[message, chatbot, session_id],
        )
        message.submit(
            send_message,
            inputs=[message, chatbot, session_id],
            outputs=[message, chatbot, session_id],
        )
        clear.click(
            clear_chat,
            inputs=[session_id],
            outputs=[message, chatbot, session_id],
            queue=False,
        )

    return demo


if __name__ == "__main__":
    build_app().launch(server_name="127.0.0.1", server_port=7860)