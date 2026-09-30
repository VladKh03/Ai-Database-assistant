from app_logging import log_event, request_context
from time import perf_counter
from errors import failure
from llm.generation import generate_text
from agent.router import (
    route_request,
    ActionType
)

from agent.read_pipeline import (
    run_read_pipeline
)
from agent.history import conversation_history, format_history
from agent.write_pipeline import run_write_pipeline, confirm_write
from agent.confirmation import pending_confirmations

from llm.model import qwen_model


class DatabaseAgent:
    """
    Main database agent orchestrator.

    Responsibilities:
    - receive user message
    - determine request type
    - route request to correct pipeline
    - return final response

    The agent does not contain SQL logic.
    """

    def __init__(self):
        self.model = qwen_model
        self.history = conversation_history

    def run(self, user_message: str, session_id: str = "default") -> dict:
        with request_context(session_id):
            started = perf_counter()
            log_event("user_request", message=user_message)
            try:
                result = self._run(user_message, session_id)
                log_event("request_completed", success=result.get("success", False),
                          action=result.get("action"), error_code=result.get("error_code"),
                          duration_ms=round((perf_counter() - started) * 1000, 2))
                return result
            except Exception:
                log_event("request_failed", duration_ms=round((perf_counter() - started) * 1000, 2))
                raise

    def _run(
        self,
        user_message: str,
        session_id: str = "default"
    ) -> dict:
        """
        Process user request
        """

        if not isinstance(user_message, str):
            return {
                "success": False,
                "action": None,
                "answer": "User message must be a string."
            }

        user_message = user_message.strip()

        if not user_message:
            return {
                "success": False,
                "action": None,
                "answer": "User message is empty."
            }

        pending = pending_confirmations.get(session_id)
        decision = user_message.casefold().strip(" .!?")
        if pending and decision in {"так", "підтверджую", "підтвердити", "yes", "confirm", "ні", "скасувати", "no", "cancel"}:
            return self.confirm(
                session_id, pending["operation_id"],
                decision in {"так", "підтверджую", "підтвердити", "yes", "confirm"},
            )
        pending_confirmations.clear(session_id)
        recent = self.history.get(session_id)

        try:
            action_type = route_request(
                user_message,
                history=recent
            )

            if action_type == ActionType.READ:
                result = self._handle_read(
                    user_message, recent
                )
            elif action_type == ActionType.CREATE:
                result = self._handle_write(user_message, "CREATE", recent, session_id)
            elif action_type == ActionType.UPDATE:
                result = self._handle_write(user_message, "UPDATE", recent, session_id)
            elif action_type == ActionType.DELETE:
                result = self._handle_write(user_message, "DELETE", recent, session_id)
            else:
                result = self._handle_general(user_message, recent)

        except Exception as error:
            result = {"action": None, **failure(error)}

        self.history.add_turn(session_id, user_message, result)
        return result

    def _handle_read(
        self,
        user_message: str,
        history: list[dict[str, str]]
    ) -> dict:
        """
        Handle database READ request
        """

        result = run_read_pipeline(
            user_message,
            history=history
        )

        result["request_type"] = "READ"

        return result

    def _handle_write(
        self, user_message: str, request_type: str,
        history: list[dict[str, str]], session_id: str,
    ) -> dict:
        """Execute writes or prepare a mandatory DELETE confirmation."""
        return run_write_pipeline(user_message, request_type, history, session_id)

    def confirm(self, session_id: str, operation_id: str, confirmed: bool) -> dict:
        with request_context(session_id):
            started = perf_counter()
            log_event("confirmation_request", confirmed=confirmed)
            result = self._confirm(session_id, operation_id, confirmed)
            log_event("confirmation_completed", success=result.get("success", False),
                      error_code=result.get("error_code"),
                      duration_ms=round((perf_counter() - started) * 1000, 2))
            return result

    def _confirm(self, session_id: str, operation_id: str, confirmed: bool) -> dict:
        try:
            result = confirm_write(session_id, operation_id, confirmed)
        except Exception as error:
            result = {"action": None, **failure(error)}
        self.history.add_turn(session_id, "Підтверджую" if confirmed else "Скасувати", result)
        return result

    def _handle_general(
        self,
        user_message: str,
        history: list[dict[str, str]]
    ) -> dict:
        """
        Handle request that does not require
        database access
        """

        messages = [
            {
                "role": "system",
                "content": """
You are an AI database assistant.

Answer general questions clearly and concisely.

Do not claim that you accessed or modified the database
unless a database tool was actually executed.
"""
            },
            {
                "role": "user",
                "content": format_history(history) + "Current user request:\n" + user_message
            }
        ]

        answer = generate_text(self.model, 
            messages
        )

        return {
            "success": True,
            "request_type": "GENERAL",
            "action": None,
            "answer": answer.strip()
        }


database_agent = DatabaseAgent()
