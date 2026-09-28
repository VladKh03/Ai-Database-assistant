from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from database.connection import check_database_connection
from database.schema import get_database_schema


app = FastAPI(title="AI Database Assistant")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    answer: str
    action: str | None


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message must not be empty")

    # The model is loaded on the first chat request; health and schema remain
    # available even on a machine without model weights or a GPU.
    try:
        from agent.agent import database_agent

        result = database_agent.run(message)
    except Exception as error:
        raise HTTPException(
            status_code=503, detail="The assistant is unavailable"
        ) from error

    return ChatResponse(
        answer=result.get("answer", ""),
        action=result.get("action"),
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
def reset() -> dict:
    # The current agent keeps no conversation or pending-operation state.
    return {"success": True, "cleared": False}