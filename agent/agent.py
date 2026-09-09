from agent.router import (
    route_request,
    ActionType
)

from agent.read_pipeline import (
    run_read_pipeline
)

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

    def run(
        self,
        user_message: str
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

        try:
            action_type = route_request(
                user_message
            )

            if action_type == ActionType.READ:
                return self._handle_read(
                    user_message
                )

            if action_type == ActionType.CREATE:
                return self._handle_create(
                    user_message
                )

            if action_type == ActionType.UPDATE:
                return self._handle_update(
                    user_message
                )

            if action_type == ActionType.DELETE:
                return self._handle_delete(
                    user_message
                )

            return self._handle_general(
                user_message
            )

        except Exception as error:
            return {
                "success": False,
                "action": None,
                "error": str(error),
                "answer": (
                    "An error occurred while "
                    "processing the request."
                )
            }

    def _handle_read(
        self,
        user_message: str
    ) -> dict:
        """
        Handle database READ request
        """

        result = run_read_pipeline(
            user_message
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
        user_message: str
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
                "content": user_message
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