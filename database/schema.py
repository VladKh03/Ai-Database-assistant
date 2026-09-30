from sqlalchemy import inspect

from database.connection import engine


def get_database_schema() -> dict:
    """
    Return full database schema

    Includes:
    - tables
    - columns
    - data types
    - primary keys
    - foreign keys
    """
    inspector = inspect(engine)

    schema = {}

    table_names = inspector.get_table_names()

    for table_name in table_names:
        columns = inspector.get_columns(table_name)
        primary_key = inspector.get_pk_constraint(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)

        schema[table_name] = {
            "columns": [],
            "primary_keys": primary_key.get("constrained_columns", []),
            "foreign_keys": []
        }

        for column in columns:
            schema[table_name]["columns"].append({
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column.get("nullable", True),
                "default": column.get("default")
            })

        for foreign_key in foreign_keys:
            constrained_columns = foreign_key.get(
                "constrained_columns",
                []
            )

            referred_table = foreign_key.get(
                "referred_table"
            )

            referred_columns = foreign_key.get(
                "referred_columns",
                []
            )

            schema[table_name]["foreign_keys"].append({
                "columns": constrained_columns,
                "references_table": referred_table,
                "references_columns": referred_columns
            })

    return schema


def format_schema_for_llm(schema: dict | None = None) -> str:
    """
    Convert database schema into compact text
    suitable for LLM context
    """
    if schema is None:
        schema = get_database_schema()

    lines = []

    for table_name, table_info in schema.items():
        lines.append(f"TABLE: {table_name}")

        primary_keys = set(
            table_info["primary_keys"]
        )

        foreign_key_map = {}

        for fk in table_info["foreign_keys"]:
            for column, reference_column in zip(
                fk["columns"],
                fk["references_columns"]
            ):
                foreign_key_map[column] = (
                    f"{fk['references_table']}."
                    f"{reference_column}"
                )

        for column in table_info["columns"]:
            column_name = column["name"]
            column_type = column["type"]

            attributes = []

            if column_name in primary_keys:
                attributes.append("PRIMARY KEY")

            if column_name in foreign_key_map:
                attributes.append(
                    f"FOREIGN KEY -> "
                    f"{foreign_key_map[column_name]}"
                )

            if not column["nullable"]:
                attributes.append("NOT NULL")

            attributes_text = ""

            if attributes:
                attributes_text = (
                    " [" + ", ".join(attributes) + "]"
                )

            lines.append(
                f"- {column_name}: "
                f"{column_type}"
                f"{attributes_text}"
            )

        lines.append("")

    return "\n".join(lines)
