from agent.router import (
    route_request,
    ActionType
)

from agent.read_pipeline import (
    run_read_pipeline
)
from agent.history import conversation_history, format_history

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

    def run(
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
                result = self._handle_create(
                    user_message
                )
            elif action_type == ActionType.UPDATE:
                result = self._handle_update(
                    user_message
                )
            elif action_type == ActionType.DELETE:
                result = self._handle_delete(
                    user_message
                )
            else:
                result = self._handle_general(user_message, recent)

        except Exception as error:
            result = {
                "success": False,
                "action": None,
                "error": str(error),
                "answer": (
                    "An error occurred while "
                    "processing the request."
                )
            }

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

    def _handle_create(
        self,
        user_message: str
    ) -> dict:
        """
        Handle CREATE request.

        Tool Registry will be connected later.
        """

        return {
            "success": False,
            "request_type": "CREATE",
            "action": None,
            "answer": (
                "CREATE operations are not "
                "implemented yet."
            )
        }

    def _handle_update(
        self,
        user_message: str
    ) -> dict:
        """
        Handle UPDATE request.

        Tool Registry will be connected later.
        """

        return {
            "success": False,
            "request_type": "UPDATE",
            "action": None,
            "answer": (
                "UPDATE operations are not "
                "implemented yet."
            )
        }

    def _handle_delete(
        self,
        user_message: str
    ) -> dict:
        """
        Handle DELETE request.

        Confirmation and Tool Registry
        will be connected later.
        """

        return {
            "success": False,
            "request_type": "DELETE",
            "action": None,
            "answer": (
                "DELETE operations are not "
                "implemented yet."
            )
        }

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

        answer = self.model.generate(
            messages
        )

        return {
            "success": True,
            "request_type": "GENERAL",
            "action": None,
            "answer": answer.strip()
        }


database_agent = DatabaseAgent()
