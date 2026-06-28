from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Initialized by create_app(); tests override via dependency_overrides.
engine = None
SessionLocal: sessionmaker | None = None


def init_db(database_url: str, **engine_kwargs) -> None:
    global engine, SessionLocal
    engine = create_engine(database_url, **engine_kwargs)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_engine():
    return engine


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
