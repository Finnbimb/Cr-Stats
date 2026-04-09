from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'crstats.db'}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def ensure_schema():
    with engine.begin() as connection:
        users_table = connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()

        if not users_table:
            return

        columns = {
            row[1] for row in connection.exec_driver_sql("PRAGMA table_info(users)").fetchall()
        }

        if "location_id" not in columns:
            connection.exec_driver_sql("ALTER TABLE users ADD COLUMN location_id INTEGER")

        if "location" not in columns:
            connection.exec_driver_sql("ALTER TABLE users ADD COLUMN location VARCHAR")
            
        if "clan_ranking" not in columns:
            connection.exec_driver_sql("ALTER TABLE users ADD COLUMN clan_ranking INTEGER")
