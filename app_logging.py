import json
import logging
import os
import re
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import Lock
from uuid import uuid4


REDACTED = "[REDACTED]"
_context = ContextVar("log_context", default={})
_setup_lock = Lock()
_logger = logging.getLogger("db_assistant")

_SECRET_NAMES = (
    r"[a-z0-9_-]*(?:secret|token|password|api[_-]?key|access[_-]?key)[a-z0-9_-]*|"
    r"passwd|pwd|authorization|cookie|credentials|private[_-]?key|пароль|токен|секрет"
)

_ASSIGNMENT = re.compile(
    rf'''(?i)(["']?\b(?:{_SECRET_NAMES})\b["']?\s*[:=]\s*)(?:"[^"\n]*"|'[^'\n]*'|[^\s,;}}\]]+)'''
)


def secret_key(key: str) -> bool:
    """Check if a field name may contain a secret"""
    if any(
        part in key.casefold()
        for part in ("парол", "токен", "секрет")
    ):
        return True

    normalized = re.sub(r"[^a-z0-9]", "", key.casefold())

    return normalized in {"passwd", "pwd"} or any(
        part in normalized
        for part in (
            "password", "secret", "token", "apikey", "accesskey",
            "privatekey", "authorization", "cookie", "credentials",
        )
    )


def redact(value):
    """Hide known secrets in text and nested values"""
    if isinstance(value, dict):
        return {
            str(key): (
                REDACTED if secret_key(str(key)) else redact(item)
            )
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]

    if isinstance(value, bytes):
        return "<binary>"

    if not isinstance(value, str):
        return (
            value
            if value is None or isinstance(value, (int, float, bool))
            else f"<{type(value).__name__}>"
        )

    # Hide known secret values even when no field name is given
    for key, secret in os.environ.items():
        if secret_key(key) and secret:
            value = value.replace(secret, REDACTED)

    value = re.sub(
        r"(?i)((?:cookie|set-cookie)\s*:\s*)[^\r\n]*",
        r"\1" + REDACTED,
        value,
    )
    value = re.sub(
        r"(?i)\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+",
        "Bearer " + REDACTED,
        value,
    )
    value = re.sub(
        r"(?i)([a-z][a-z0-9+.-]*://)[^/\s@]+@",
        r"\1" + REDACTED + "@",
        value,
    )
    value = re.sub(
        r"-----BEGIN [^-]*PRIVATE KEY-----[\s\S]*?"
        r"-----END [^-]*PRIVATE KEY-----",
        REDACTED,
        value,
    )
    value = re.sub(
        r"\b(?:hf_|sk-|ghp_|github_pat_)[A-Za-z0-9_-]{8,}\b",
        REDACTED,
        value,
    )
    value = re.sub(
        r"(?i)([?&](?:X-Amz-[^=&\s]+|sig|signature|se|sp|sv)\s*=)"
        r"[^&\s]+",
        r"\1" + REDACTED,
        value,
    )

    return _ASSIGNMENT.sub(
        lambda match: match.group(1) + REDACTED,
        value,
    )


class SafeJSONFormatter(logging.Formatter):
    """Write log records as JSON after hiding secrets"""
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "time": datetime.fromtimestamp(
                record.created, timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
            **getattr(record, "event_fields", {}),
        }

        # Keep tracebacks and raw SQL parameters out of logs
        return json.dumps(
            redact(payload),
            ensure_ascii=False,
            default=str,
        )


def setup_logging() -> None:
    """Add console and rotating file logs once"""
    with _setup_lock:
        if _logger.handlers:
            return

        level = os.getenv("LOG_LEVEL", "INFO").upper()
        _logger.setLevel(getattr(logging, level, logging.INFO))
        _logger.propagate = False

        formatter = SafeJSONFormatter()

        console = logging.StreamHandler()
        console.setFormatter(formatter)
        _logger.addHandler(console)

        path = Path(os.getenv(
            "LOG_FILE",
            str(
                Path(__file__).resolve().parent
                / "logs"
                / "assistant.log"
            ),
        ))

        try:
            path.parent.mkdir(parents=True, exist_ok=True)

            handler = RotatingFileHandler(
                path,
                maxBytes=5_000_000,
                backupCount=3,
                encoding="utf-8",
            )
            handler.setFormatter(formatter)
            _logger.addHandler(handler)

        except OSError:
            _logger.warning("file_logging_unavailable")


def log_event(
    event: str,
    *,
    level: int = logging.INFO,
    **fields,
) -> None:
    """Write an event with the current request context"""
    setup_logging()
    _logger.log(
        level,
        event,
        extra={
            "event_fields": {
                **_context.get(),
                **fields,
            },
        },
    )


@contextmanager
def request_context(session_id: str):
    """Keep request details separate for each running request"""
    token = _context.set({
        "request_id": _context.get().get(
            "request_id", uuid4().hex
        ),
        "session_id": session_id,
    })

    try:
        yield
    finally:
        _context.reset(token)