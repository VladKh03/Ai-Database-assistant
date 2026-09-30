"""Local HTTP interface for the database assistant."""

from uuid import uuid4

from fastapi import FastAPI, HTTPException

from api.schemas import ChatRequest, ChatResponse, ResetRequest, ConfirmationRequest
from agent.history import conversation_history
from agent.confirmation import pending_confirmations
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
        requires_confirmation=result.get("requires_confirmation", False),
        operation_id=result.get("operation_id"),
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


@app.post("/confirm", response_model=ChatResponse)
def confirm(request: ConfirmationRequest) -> ChatResponse:
    from agent.agent import database_agent

    result = database_agent.confirm(request.session_id, request.operation_id, request.confirmed)
    return ChatResponse(
        answer=result["answer"], action=result.get("action"), session_id=request.session_id,
    )


@app.post("/reset")
def reset(request: ResetRequest | None = None) -> dict:
    if request is None:
        return {"success": True, "cleared": False}
    cancelled = pending_confirmations.clear(request.session_id)
    cleared = conversation_history.clear(request.session_id)
    return {"success": True, "cleared": cleared, "cancelled": cancelled}
