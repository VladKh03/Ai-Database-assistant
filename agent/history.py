"""Short, session-scoped conversation context for the database agent."""

import json
from collections import OrderedDict, deque
from threading import Lock


MAX_HISTORY_MESSAGES = 10
MAX_SESSIONS = 100


def compact_value(value) -> str:
    if isinstance(value, bytes):
        return f"<{len(value)} binary bytes>"
    return str(value)[:120]


class ConversationHistory:
    def __init__(self):
        self._sessions: OrderedDict[str, deque[dict[str, str]]] = OrderedDict()
        self._lock = Lock()

    def get(self, session_id: str) -> list[dict[str, str]]:
        with self._lock:
            messages = self._sessions.get(session_id)
            if messages is None:
                return []
            self._sessions.move_to_end(session_id)
            return [message.copy() for message in messages]

    def add_turn(self, session_id: str, user_message: str, result: dict) -> None:
        messages = [{"role": "user", "content": user_message[:1200]}]

        if result.get("query"):
            tool_result = {
                "query": str(result["query"])[:500],
                "success": result.get("success", False),
                "row_count": result.get("row_count"),
                "rows": [
                    {str(key): compact_value(value) for key, value in row.items()}
                    for row in result.get("rows", [])[:3]
                ],
            }
            if result.get("error"):
                tool_result["error"] = str(result["error"])[:200]
            messages.append({
                "role": "tool",
                "content": json.dumps(tool_result, ensure_ascii=False)[:1200],
            })

        messages.append({
            "role": "assistant",
            "content": str(result.get("answer", ""))[:1200],
        })

        with self._lock:
            history = self._sessions.setdefault(
                session_id, deque(maxlen=MAX_HISTORY_MESSAGES)
            )
            history.extend(messages)
            self._sessions.move_to_end(session_id)
            while len(self._sessions) > MAX_SESSIONS:
                self._sessions.popitem(last=False)

    def clear(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None


def format_history(history: list[dict[str, str]] | None) -> str:
    """Place recent context before the latest request in a user message."""
    if not history:
        return ""
    lines = ["Recent conversation (context only):"]
    for message in history[-MAX_HISTORY_MESSAGES:]:
        lines.append(f"{message['role'].upper()}: {message['content']}")
    return "\n".join(lines) + "\n\n"


conversation_history = ConversationHistory()