"""Keep delete requests until the user confirms or cancels them"""

from collections import OrderedDict
from copy import deepcopy
from threading import Lock
from time import monotonic
from uuid import uuid4


class ConfirmationStore:
    """Keep one pending delete request per session"""
    def __init__(self, ttl_seconds: int = 300, max_sessions: int = 100):
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions
        self._pending = OrderedDict()
        self._lock = Lock()

    def put(self, session_id: str, operation: dict) -> str:
        """Save a copy of the action and return its confirmation ID"""
        # Give each pending action a new ID
        operation_id = uuid4().hex
        with self._lock:
            # Keep only the latest pending action for this session
            self._pending.pop(session_id, None)
            self._pending[session_id] = {
                **deepcopy(operation),
                "operation_id": operation_id,
                "expires_at": monotonic() + self.ttl_seconds,
            }
            while len(self._pending) > self.max_sessions:
                self._pending.popitem(last=False)
        return operation_id

    def get(self, session_id: str) -> dict | None:
        """Return a copy if the request has not expired"""
        with self._lock:
            operation = self._pending.get(session_id)
            if operation is not None and operation["expires_at"] <= monotonic():
                self._pending.pop(session_id)
                return None
            return deepcopy(operation)

    def take(self, session_id: str, operation_id: str) -> dict | None:
        """Remove and return a valid request so it can run only once"""
        with self._lock:
            operation = self._pending.get(session_id)
            if operation is None or operation["operation_id"] != operation_id:
                return None
            # Remove it while locked to block a second confirmation
            self._pending.pop(session_id)
            if operation["expires_at"] <= monotonic():
                return None
            return deepcopy(operation)

    def clear(self, session_id: str) -> bool:
        """Cancel the pending request for this session"""
        with self._lock:
            return self._pending.pop(session_id, None) is not None


pending_confirmations = ConfirmationStore()