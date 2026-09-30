"""Public error messages; technical exception details stay in server logs."""

import logging
import sqlite3

from pydantic import ValidationError


from app_logging import log_event


class ModelGenerationError(RuntimeError):
    pass


class InvalidForeignKeyError(ValueError):
    pass


MESSAGES = {

    "invalid_sql": (
        "Failed to execute the SQL query: it is invalid "
        "or contains a prohibited operation."
    ),

    "column_not_found": (
        "The requested column does not exist in the database. "
        "Please check the field name."
    ),

    "table_not_found": (
        "The requested table does not exist in the database. "
        "Please check the table name."
    ),

    "malformed_json": (
        "The model returned an invalid structured response. "
        "Try rephrasing your request."
    ),

    "tool_not_found": (
        "The requested tool is unavailable or prohibited "
        "for this type of request."
    ),

    "database_locked": (
        "The database is currently busy with another operation. "
        "Please try again later."
    ),

    "record_not_found": (
        "No record with the specified ID was found. "
        "Please check the ID."
    ),

    "invalid_foreign_key": (
        "The related record does not exist or this record is referenced "
        "by other records. Please check the ID and relationships."
    ),

    "duplicate_primary_key": (
        "A record with this ID or another unique value already exists."
    ),

    "invalid_arguments": (
        "Invalid or incomplete operation arguments. "
        "Please check the ID, values, and required fields."
    ),

    "ambiguous_record": (
        "Multiple matching records were found. Please specify the exact ID."
    ),

    "generation_failed": (
        "Qwen failed to generate a response. "
        "Try again or simplify your request."
    ),

    "database_error": (
        "Failed to perform the database operation. Please try again later."
    ),

    "internal_error": (
        "Failed to process the request. Please try again."
    ),

}


def error_info(error: Exception) -> dict:
    original = getattr(error, "orig", error)
    message = str(original).lower()
    name = type(error).__name__
    sqlite_code = getattr(original, "sqlite_errorcode", None)

    if isinstance(error, ModelGenerationError):
        code = "generation_failed"
    elif isinstance(error, InvalidForeignKeyError):
        code = "invalid_foreign_key"
    elif name in {"UnknownToolError", "UnknownActionError"}:
        code = "tool_not_found"
    elif name in {"LLMOutputError", "JSONDecodeError"}:
        code = "malformed_json"
    elif isinstance(error, ValidationError):
        code = "invalid_arguments"
    elif name == "SQLValidationError":
        code = "invalid_sql"
    elif sqlite_code is not None and sqlite_code & 255 in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED}:
        code = "database_locked"
    elif "database is locked" in message or "database table is locked" in message:
        code = "database_locked"
    elif "no such column" in message:
        code = "column_not_found"
    elif "no such table" in message:
        code = "table_not_found"
    elif "foreign key constraint failed" in message:
        code = "invalid_foreign_key"
    elif "unique constraint failed" in message or "primary key" in message:
        code = "duplicate_primary_key"
    elif "syntax error" in message or "incomplete input" in message or "misuse of" in message or "unrecognized token" in message:
        code = "invalid_sql"
    elif isinstance(error, ValueError):
        code = ("ambiguous_record" if "ambiguous" in message else
                "record_not_found" if "not found" in message else "invalid_arguments")
    elif isinstance(original, sqlite3.DatabaseError) or type(error).__module__.startswith("sqlalchemy"):
        code = "database_error"
    else:
        code = "internal_error"
    log_event("database_error" if code in {
        "invalid_sql", "column_not_found", "table_not_found", "database_locked",
        "invalid_foreign_key", "duplicate_primary_key", "database_error",
    } else "operation_error", level=logging.ERROR,
              error_code=code, error_type=name, sqlite_error_code=sqlite_code)
    return {"error_code": code, "error": MESSAGES[code]}


def failure(error: Exception | None = None, *, code: str = "internal_error") -> dict:
    info = error_info(error) if error is not None else {"error_code": code, "error": MESSAGES[code]}
    return {"success": False, **info, "answer": info["error"]}
