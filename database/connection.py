from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "data" / "northwind.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)


def get_connection():
    """
    Return raw SQLAlchemy connection
    """
    return engine.connect()


def get_session():
    """
    Create database session

    Automatically closes session after usage
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def execute_query(query: str, params: dict | None = None):
    """
    Execute read-only query and return rows as dictionaries
    """
    params = params or {}

    with engine.connect() as connection:
        result = connection.execute(
            text(query),
            params
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]


def execute_write(query: str, params: dict | None = None):
    """
    Execute INSERT, UPDATE or DELETE

    Automatically commits transaction
    Rolls back if an error occurs
    """
    params = params or {}

    connection = engine.connect()
    transaction = connection.begin()

    try:
        result = connection.execute(
            text(query),
            params
        )

        transaction.commit()

        return {
            "success": True,
            "rowcount": result.rowcount
        }

    except Exception:
        transaction.rollback()
        raise

    finally:
        connection.close()


def check_database_connection():
    """
    Check whether SQLite database is available
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True

    except Exception:
        return False