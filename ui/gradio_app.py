"""Gradio frontend communicating with the FastAPI backend over HTTP."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import gradio as gr


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT_SECONDS = 180


def ask_backend(message: str) -> str:
    """Send one user message to POST /chat and return the agent's answer."""
    request = Request(
        f"{API_BASE_URL}/chat",
        data=json.dumps({"message": message}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            try:
                payload = json.load(response)
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

    if not isinstance(payload, dict) or not isinstance(payload.get("answer"), str):
        raise RuntimeError("The backend returned an invalid response.")

    return payload["answer"]


def send_message(message: str, history: list[dict] | None) -> tuple[str, list[dict]]:
    """Update the visible conversation using only the FastAPI response."""
    message = message.strip()
    history = list(history or [])
    if not message:
        return "", history

    history.append({"role": "user", "content": message})
    try:
        answer = ask_backend(message)
    except RuntimeError as error:
        answer = str(error)
    history.append({"role": "assistant", "content": answer})
    return "", history


def clear_chat() -> tuple[str, list[dict]]:
    """Clear this browser session's chat and input field."""
    return "", []


def build_app() -> gr.Blocks:
    with gr.Blocks() as demo:
        gr.Markdown("# AI Database Assistant")
        chatbot = gr.Chatbot(label="Chat", height=500)
        with gr.Row():
            message = gr.Textbox(
                label="Message",
                placeholder="Покажи всі замовлення клієнта ALFKI",
                scale=8,
            )
            send = gr.Button("Send", variant="primary", scale=1)
            clear = gr.Button("Clear", scale=1)

        send.click(send_message, inputs=[message, chatbot], outputs=[message, chatbot])
        message.submit(
            send_message, inputs=[message, chatbot], outputs=[message, chatbot]
        )
        clear.click(clear_chat, outputs=[message, chatbot], queue=False)

    return demo


if __name__ == "__main__":
    build_app().launch(server_name="127.0.0.1", server_port=7860)