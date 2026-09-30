from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.engine import Engine

from database.connection import engine


class WriteRepository:
    table: str
    primary_key: str
    fields: dict[str, str]

    def __init__(self, db_engine: Engine | None = None):
        self.engine = db_engine if db_engine is not None else engine

    @contextmanager
    def _transaction(self):
        with self.engine.connect() as connection:
            if connection.dialect.name == "sqlite":
                connection.exec_driver_sql("PRAGMA foreign_keys=ON")
                connection.commit()
            with connection.begin():
                yield connection

    def _values(self, data: dict) -> dict[str, object]:
        unknown = data.keys() - self.fields.keys()
        if unknown:
            raise ValueError(f"Unsupported fields: {', '.join(sorted(unknown))}")
        if not data:
            raise ValueError("At least one field is required")
        return data

    def _create(self, data: dict) -> dict:
        values = self._values(data)
        columns = ", ".join(f'"{self.fields[name]}"' for name in values)
        placeholders = ", ".join(f":{name}" for name in values)
        statement = text(
            f'INSERT INTO "{self.table}" ({columns}) VALUES ({placeholders})'
        )

        with self._transaction() as connection:
            result = connection.execute(statement, values)
            record_id = values.get(self.primary_key, result.lastrowid)
            return {"rowcount": result.rowcount, "record_id": record_id}

    def _update(self, record_id: str | int, data: dict) -> dict:
        values = self._values(data)
        if self.primary_key in values:
            raise ValueError("Primary key cannot be updated")

        assignments = ", ".join(
            f'"{self.fields[name]}" = :{name}' for name in values
        )
        statement = text(
            f'UPDATE "{self.table}" SET {assignments} '
            f'WHERE "{self.fields[self.primary_key]}" = :_record_id'
        )

        with self._transaction() as connection:
            result = connection.execute(
                statement, {**values, "_record_id": record_id}
            )
            return {"rowcount": result.rowcount, "record_id": record_id}

    def _delete(self, record_id: str | int) -> dict:
        statement = text(
            f'DELETE FROM "{self.table}" '
            f'WHERE "{self.fields[self.primary_key]}" = :_record_id'
        )

        with self._transaction() as connection:
            result = connection.execute(
                statement, {"_record_id": record_id}
            )
            return {"rowcount": result.rowcount, "record_id": record_id}