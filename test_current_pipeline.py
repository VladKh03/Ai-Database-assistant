from database.connection import check_database_connection
from database.schema import format_schema_for_llm
from database.validator import validate_select_query, SQLValidationError
from database.queries import execute_select_query

from tools.read_tools import query_database

from agent.router import route_request
from agent.agent import database_agent


def separator(title):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


# ==================================================
# 1. DATABASE CONNECTION
# ==================================================

separator("1. DATABASE CONNECTION")

connected = check_database_connection()

print("Connected:", connected)

assert connected, "Database connection failed"


# ==================================================
# 2. DATABASE SCHEMA
# ==================================================

separator("2. DATABASE SCHEMA")

schema = format_schema_for_llm()

print(schema[:3000])

assert "Products" in schema
assert "Customers" in schema
assert "Orders" in schema


# ==================================================
# 3. SQL VALIDATOR
# ==================================================

separator("3. SQL VALIDATOR")


valid_queries = [
    "SELECT * FROM Products LIMIT 5",
    "SELECT COUNT(*) AS count FROM Customers",
    """
    SELECT Country, COUNT(*) AS customers
    FROM Customers
    GROUP BY Country
    ORDER BY customers DESC
    LIMIT 1
    """
]


for sql in valid_queries:
    validated = validate_select_query(sql)

    print()
    print("INPUT:")
    print(sql)

    print("VALIDATED:")
    print(validated)


separator("3.1 INVALID SQL")


invalid_queries = [
    "DELETE FROM Products",
    "UPDATE Products SET UnitPrice = 0",
    "DROP TABLE Products",
    "SELECT * FROM Products; DELETE FROM Products;"
]


for sql in invalid_queries:
    try:
        validate_select_query(sql)

        raise AssertionError(
            f"Unsafe query was accepted: {sql}"
        )

    except SQLValidationError as error:
        print(f"BLOCKED: {sql}")
        print(f"Reason: {error}")
        print()


# ==================================================
# 4. DATABASE QUERY EXECUTOR
# ==================================================

separator("4. DATABASE QUERY EXECUTOR")


rows = execute_select_query(
    """
    SELECT ProductID, ProductName, UnitPrice
    FROM Products
    ORDER BY UnitPrice DESC
    LIMIT 5
    """
)

print(rows)

assert isinstance(rows, list)
assert len(rows) <= 5

if rows:
    assert isinstance(rows[0], dict)


# ==================================================
# 5. READ TOOL
# ==================================================

separator("5. READ TOOL")


result = query_database(
    """
    SELECT ProductName, UnitsInStock
    FROM Products
    LIMIT 5
    """
)

print(result)

assert result["success"] is True
assert "rows" in result
assert "row_count" in result


# ==================================================
# 6. ROUTER
# ==================================================

separator("6. ROUTER")


router_tests = [
    "Покажи всі продукти",
    "Скільки клієнтів з Німеччини?",
    "Додай нового клієнта",
    "Зміни ціну продукту 10",
    "Видали клієнта TEST1",
    "Що таке SQL?"
]


for question in router_tests:
    action = route_request(question)

    print(
        f"{question} -> {action.value}"
    )


# ==================================================
# 7. FULL READ AGENT PIPELINE
# ==================================================

separator("7. FULL READ AGENT PIPELINE")


questions = [
    "Скільки клієнтів є в базі?",
    "Яка країна має найбільше клієнтів?",
    "Які 5 продуктів найдорожчі?",
    "Скільки продуктів є в базі?",
    "Який продукт має найбільшу ціну?"
]


for question in questions:

    separator(f"QUESTION: {question}")

    result = database_agent.run(
        question
    )

    print("SUCCESS:")
    print(result.get("success"))

    print()

    print("REQUEST TYPE:")
    print(result.get("request_type"))

    print()

    print("ACTION:")
    print(result.get("action"))

    print()

    print("GENERATED SQL:")
    print(result.get("query"))

    print()

    print("DATABASE ROWS:")
    print(result.get("rows"))

    print()

    print("FINAL ANSWER:")
    print(result.get("answer"))

    print()

    if result.get("error"):
        print("ERROR:")
        print(result["error"])


separator("TESTS FINISHED")