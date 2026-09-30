# Keep the model response format the same for all tool calls
AGENT_OUTPUT_PROMPT = """
You must return valid JSON only.

Do not use markdown.
Do not use code fences.
Do not add explanations before or after JSON.

For READ operations return:

{
  "action": "query_database",
  "query": "SELECT ..."
}

For an exact customer ID return:

{
  "action": "get_customer",
  "arguments": {"customer_id": "ALFKI"}
}

For a customer search return one or more filters:

{
  "action": "search_customers",
  "arguments": {"name": "Alfreds", "country": "Germany"}
}

For an exact product ID return:

{
  "action": "get_product",
  "arguments": {"product_id": 1}
}

For a product name search return:

{
  "action": "search_products",
  "arguments": {"name": "Chai"}
}

For an order with its items return:

{
  "action": "get_order",
  "arguments": {"order_id": 10248}
}

For a customer's orders return:

{
  "action": "get_customer_orders",
  "arguments": {"customer_id": "ALFKI"}
}

For CREATE, UPDATE or DELETE operations return:

{
  "action": "<tool_name>",
  "arguments": {
    "<argument>": "<value>"
  }
}

Rules:

1. Return exactly one JSON object.

2. General READ requests must use "query_database".
   Customer lookup/search may use "get_customer" or "search_customers".
   Product lookup/search may use "get_product" or "search_products".
   Order lookup may use "get_order" or "get_customer_orders".

3. "query_database" requires "query". Fixed read tools require "arguments".

4. CREATE, UPDATE and DELETE requests must include:
   "arguments"

5. Do not include both "query" and "arguments".

6. Never generate INSERT, UPDATE or DELETE SQL directly.

7. For write operations use the appropriate tool action.

8. Use only tool names provided to you.

9. Use only tables and columns from the database schema.

10. Do not invent missing values.
"""
