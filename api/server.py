"""Local HTTP interface for the database assistant."""

from uuid import uuid4

from fastapi import FastAPI, HTTPException

from api.schemas import ChatRequest, ChatResponse, ResetRequest
from agent.history import conversation_history
from database.connection import check_database_connection
from database.schema import get_database_schema


app = FastAPI(title="AI Database Assistant")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    # The model is loaded on the first chat request; health and schema remain
    # available even on a machine without model weights or a GPU.
    session_id = request.session_id or uuid4().hex
    try:
        from agent.agent import database_agent

        result = database_agent.run(request.message, session_id=session_id)
    except Exception as error:
        raise HTTPException(
            status_code=503, detail="The assistant is unavailable"
        ) from error

    return ChatResponse(
        answer=result.get("answer", ""),
        action=result.get("action"),
        session_id=session_id,
    )


@app.get("/health")
def health() -> dict:
    if not check_database_connection():
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ok", "database": "connected"}


@app.get("/schema")
def schema() -> dict:
    try:
        return get_database_schema()
    except Exception as error:
        raise HTTPException(status_code=503, detail="Database unavailable") from error


@app.post("/confirm")
def confirm() -> dict:
    # Write operations are not implemented yet, so nothing can be pending.
    raise HTTPException(status_code=409, detail="No pending operation to confirm")


@app.post("/reset")
def reset(request: ResetRequest | None = None) -> dict:
    if request is None:
        return {"success": True, "cleared": False}
    return {
        "success": True,
        "cleared": conversation_history.clear(request.session_id),
    }