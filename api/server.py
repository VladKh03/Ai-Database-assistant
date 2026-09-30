from uuid import uuid4
from app_logging import setup_logging

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from errors import failure, error_info, MESSAGES

from api.schemas import ChatRequest, ChatResponse, ResetRequest, ConfirmationRequest
from agent.history import conversation_history
from agent.confirmation import pending_confirmations
from database.connection import check_database_connection
from database.schema import get_database_schema


setup_logging()
app = FastAPI(title="AI Database Assistant")


@app.exception_handler(RequestValidationError)
async def invalid_request(request, error):
    # Keep input values and internal error details out of the response
    """Return a safe message for invalid HTTP input"""
    code = "malformed_json" if any(item["type"] == "json_invalid" for item in error.errors()) else "invalid_arguments"
    message = (
        "Тіло запиту містить некоректний JSON."
        if code == "malformed_json" else MESSAGES[code]
    )
    return JSONResponse(status_code=422, content={
        "success": False, "error_code": code, "detail": message,
    })


@app.exception_handler(Exception)
async def unexpected_error(request, error):
    """Return a safe message for an unexpected server error"""
    problem = failure(error)
    return JSONResponse(status_code=500, content={
        "success": False, "error_code": problem["error_code"],
        "detail": problem["answer"],
    })


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    # Load the agent here so health and schema checks do not need Qwen
    """Create or reuse a session and pass the message to the agent"""
    session_id = request.session_id or uuid4().hex
    try:
        from agent.agent import database_agent

        result = database_agent.run(request.message, session_id=session_id)
    except Exception as error:
        error_info(error)
        raise HTTPException(
            status_code=503, detail="Помічник недоступний. Перевірте запуск Qwen."
        ) from error

    return ChatResponse(
        success=result.get("success", False), error_code=result.get("error_code"),
        answer=result.get("answer", ""),
        action=result.get("action"),
        session_id=session_id,
        requires_confirmation=result.get("requires_confirmation", False),
        operation_id=result.get("operation_id"),
    )


@app.get("/health")
def health() -> dict:
    """Check if the database accepts a simple query"""
    if not check_database_connection():
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ok", "database": "connected"}


@app.get("/schema")
def schema() -> dict:
    """Return the current database structure"""
    try:
        return get_database_schema()
    except Exception as error:
        error_info(error)
        raise HTTPException(status_code=503, detail="Database unavailable") from error


@app.post("/confirm", response_model=ChatResponse)
def confirm(request: ConfirmationRequest) -> ChatResponse:
    """Confirm or cancel a pending delete request"""
    try:
        from agent.agent import database_agent
        result = database_agent.confirm(request.session_id, request.operation_id, request.confirmed)
    except Exception as error:
        result = failure(error)
    return ChatResponse(
        success=result.get("success", False), error_code=result.get("error_code"),
        answer=result["answer"], action=result.get("action"), session_id=request.session_id,
    )


@app.post("/reset")
def reset(request: ResetRequest | None = None) -> dict:
    """Clear chat history and cancel the pending delete request"""
    if request is None:
        return {"success": True, "cleared": False}
    cancelled = pending_confirmations.clear(request.session_id)
    cleared = conversation_history.clear(request.session_id)
    return {"success": True, "cleared": cleared, "cancelled": cancelled}
