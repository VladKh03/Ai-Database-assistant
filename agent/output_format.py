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

For CREATE, UPDATE or DELETE operations return:

{
  "action": "<tool_name>",
  "arguments": {
    "<argument>": "<value>"
  }
}

Rules:

1. Return exactly one JSON object.

2. READ requests must use:
   "action": "query_database"

3. READ requests must include:
   "query"

4. CREATE, UPDATE and DELETE requests must include:
   "arguments"

5. Do not include both "query" and "arguments".

6. Never generate INSERT, UPDATE or DELETE SQL directly.

7. For write operations use the appropriate tool action.

8. Use only tool names provided to you.

9. Use only tables and columns from the database schema.

10. Do not invent missing values.
"""