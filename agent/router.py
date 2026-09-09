from enum import Enum

from llm.model import qwen_model


class ActionType(str, Enum):
    READ = "READ"
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    GENERAL = "GENERAL"


ROUTER_PROMPT = """
You are a request router for an AI SQLite database assistant.

Your only task is to classify the user's request into exactly one category.

Available categories:

READ
The user wants to retrieve, search, calculate, count, aggregate or analyze data
from the database.

Examples:
- Show all products
- How many customers are from Germany?
- Who made the most orders?
- What product was sold most often?
- Find customer ALFKI
- Calculate total revenue

CREATE
The user wants to add or create a new database record.

Examples:
- Add a new customer
- Create a new product
- Add an order

UPDATE
The user wants to modify an existing database record.

Examples:
- Change the price of product 10
- Update customer ALFKI phone number
- Change the order status

DELETE
The user wants to delete an existing database record.

Examples:
- Delete customer TEST1
- Remove product 15
- Delete this order

GENERAL
The request does not require reading or modifying database data.

Examples:
- What is SQL?
- Hello
- What can you do?
- Explain what a database is

RULES:

1. Return exactly one category.

2. Allowed outputs:
READ
CREATE
UPDATE
DELETE
GENERAL

3. Do not return explanations.

4. Do not generate SQL.

5. Do not answer the user's request.

6. Determine the user's intent, not individual keywords.

7. Questions about existing database data are READ.

8. Requests to calculate statistics from database data are READ.

9. Requests that add records are CREATE.

10. Requests that change existing records are UPDATE.

11. Requests that remove records are DELETE.

12. Everything unrelated to database operations is GENERAL.
"""


def route_request(user_message: str) -> ActionType:
    """
    Determine the type of user request
    """

    messages = [
        {
            "role": "system",
            "content": ROUTER_PROMPT
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    response = qwen_model.generate(messages)

    action = response.strip().upper()

    try:
        return ActionType(action)

    except ValueError:
        return ActionType.GENERAL