import re


MAX_ROWS = 100
DEFAULT_LIMIT = 20


class SQLValidationError(Exception):
    pass


FORBIDDEN_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "ATTACH",
    "DETACH",
    "PRAGMA",
    "REPLACE",
    "TRUNCATE",
    "VACUUM"
}


AGGREGATE_FUNCTIONS = {
    "COUNT",
    "SUM",
    "AVG",
    "MIN",
    "MAX"
}


def remove_sql_comments(sql: str) -> str:
    sql = re.sub(
        r"--.*?$",
        "",
        sql,
        flags=re.MULTILINE
    )

    sql = re.sub(
        r"/\*.*?\*/",
        "",
        sql,
        flags=re.DOTALL
    )

    return sql.strip()


def check_multiple_statements(sql: str) -> None:
    cleaned = sql.strip()

    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()

    if ";" in cleaned:
        raise SQLValidationError(
            "Multiple SQL statements are not allowed"
        )


def check_select_only(sql: str) -> None:
    if not re.match(
        r"^\s*SELECT\b",
        sql,
        flags=re.IGNORECASE
    ):
        raise SQLValidationError(
            "Only SELECT queries are allowed"
        )


def check_forbidden_keywords(sql: str) -> None:
    uppercase_sql = sql.upper()

    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(
            rf"\b{re.escape(keyword)}\b",
            uppercase_sql
        ):
            raise SQLValidationError(
                f"Forbidden SQL keyword: {keyword}"
            )


def is_aggregate_query(sql: str) -> bool:
    """
    Check whether query mainly returns an aggregate result
    """

    uppercase_sql = sql.upper()

    for function in AGGREGATE_FUNCTIONS:
        if re.search(
            rf"\b{function}\s*\(",
            uppercase_sql
        ):
            return True

    return False


def apply_limit(
    sql: str,
    default_limit: int = DEFAULT_LIMIT,
    max_rows: int = MAX_ROWS
) -> str:
    """
    Add default LIMIT to queries.
    Reject negative LIMIT values.
    Clamp LIMIT values above MAX_ROWS.
    """

    sql = sql.strip().rstrip(";").strip()

    # Block negative LIMIT values, e.g. LIMIT -1
    negative_limit = re.search(
        r"\bLIMIT\s+-\d+\b",
        sql,
        flags=re.IGNORECASE
    )

    if negative_limit:
        raise SQLValidationError(
            "Negative LIMIT is not allowed"
        )

    limit_match = re.search(
        r"\bLIMIT\s+(\d+)\b",
        sql,
        flags=re.IGNORECASE
    )

    if limit_match:
        current_limit = int(
            limit_match.group(1)
        )

        if current_limit > max_rows:
            start, end = limit_match.span(1)

            sql = (
                sql[:start]
                + str(max_rows)
                + sql[end:]
            )

        return sql

    return f"{sql} LIMIT {default_limit}"


def validate_select_query(
    sql: str,
    add_limit: bool = True
) -> str:
    if not isinstance(sql, str):
        raise SQLValidationError(
            "SQL query must be a string"
        )

    sql = sql.strip()

    if not sql:
        raise SQLValidationError(
            "SQL query is empty"
        )

    sql = remove_sql_comments(sql)

    check_multiple_statements(sql)
    check_select_only(sql)
    check_forbidden_keywords(sql)

    if add_limit:
        sql = apply_limit(sql)

    return sql