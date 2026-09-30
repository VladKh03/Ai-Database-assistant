from pathlib import Path
from errors import error_info

from sqlalchemy import create_engine, text


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "data" / "northwind.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


# Share one engine across repositories and allow backend threads
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
)

def check_database_connection():
    """Check if SQLite can run a simple query"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True

    except Exception as error:
        error_info(error)
        return False
