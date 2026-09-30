"""Keep recent messages and tool results for each session"""

import json
from collections import OrderedDict, deque
from threading import Lock


MAX_HISTORY_MESSAGES = 10
MAX_SESSIONS = 100


def compact_value(value) -> str:
    """Shorten values before adding them to chat history"""
    if isinstance(value, bytes):
        return f"<{len(value)} binary bytes>"
    return str(value)[:120]


class ConversationHistory:
    """Keep a short, separate history for each session"""
    def __init__(self):
        self._sessions: OrderedDict[str, deque[dict[str, str]]] = OrderedDict()
        self._lock = Lock()

    def get(self, session_id: str) -> list[dict[str, str]]:
        """Return message copies so callers cannot change saved history"""
        with self._lock:
            messages = self._sessions.get(session_id)
            if messages is None:
                return []
            self._sessions.move_to_end(session_id)
            return [message.copy() for message in messages]

    def add_turn(self, session_id: str, user_message: str, result: dict) -> None:
        """Save the user message, tool results and answer"""
        messages = [{"role": "user", "content": user_message[:1200]}]

        # Keep short tool results so the next prompt stays small
        for step in result.get("tool_results", [])[-5:]:
            tool = step["result"]
            summary = {
                "step": step["step"],
                "action": step["action"],
                "success": tool.get("success", False),
                "arguments": step.get("arguments"),
                "query": str(step.get("query") or "")[:500],
                "row_count": tool.get("row_count"),
                "rows": [
                    {str(key): compact_value(value) for key, value in row.items()}
                    for row in tool.get("rows", [])[:3]
                ],
                "error": str(tool.get("error") or "")[:200],
            }
            messages.append({
                "role": "tool",
                "content": json.dumps(summary, ensure_ascii=False)[:1200],
            })

        if not result.get("tool_results") and result.get("action") and result.get("rows") is not None:
            tool_result = {
                "action": result["action"],
                "success": result.get("success", False),
                "row_count": result.get("row_count"),
                "rows": [
                    {str(key): compact_value(value) for key, value in row.items()}
                    for row in result.get("rows", [])[:3]
                ],
            }
            if result.get("query"):
                tool_result["query"] = str(result["query"])[:500]
            if result.get("error"):
                tool_result["error"] = str(result["error"])[:200]
            messages.append({
                "role": "tool",
                "content": json.dumps(tool_result, ensure_ascii=False)[:1200],
            })
        elif result.get("action") and result.get("request_type") in {"CREATE", "UPDATE", "DELETE"}:
            tool_result = {
                "action": result["action"],
                "arguments": {
                    str(key): compact_value(value)
                    for key, value in (result.get("arguments") or {}).items()
                },
                "success": result.get("success", False),
                "rowcount": result.get("rowcount", 0),
                "record_id": result.get("record_id"),
                "requires_confirmation": result.get("requires_confirmation", False),
            }
            if result.get("error"):
                tool_result["error"] = str(result["error"])[:200]
            messages.append({
                "role": "tool",
                "content": json.dumps(tool_result, ensure_ascii=False)[:1200],
            })

        messages.append({"role": "assistant", "content": str(result.get("answer", ""))[:1200]})

        with self._lock:
            history = self._sessions.setdefault(
                session_id, deque(maxlen=MAX_HISTORY_MESSAGES)
            )
            history.extend(messages)
            self._sessions.move_to_end(session_id)
            # Drop the least recently used session when storage is full
            while len(self._sessions) > MAX_SESSIONS:
                self._sessions.popitem(last=False)

    def clear(self, session_id: str) -> bool:
        """Remove all messages for one session"""
        with self._lock:
            return self._sessions.pop(session_id, None) is not None


def format_history(history: list[dict[str, str]] | None) -> str:
    """Add recent messages as context for the current request"""
    if not history:
        return ""
    lines = ["Recent conversation (context only):"]
    for message in history[-MAX_HISTORY_MESSAGES:]:
        lines.append(f"{message['role'].upper()}: {message['content']}")
    return "\n".join(lines) + "\n\n"


conversation_history = ConversationHistory()
