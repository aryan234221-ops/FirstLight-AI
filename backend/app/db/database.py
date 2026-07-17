from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Base


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = PROJECT_ROOT / "backend" / "data" / "firstlight.db"
DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
