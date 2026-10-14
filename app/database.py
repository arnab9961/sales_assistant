import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.config import settings

logger = logging.getLogger("sales_ops.database")

Base = declarative_base()


def get_engine_args(url: str):
    args = {}
    if url.startswith("sqlite"):
        args["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url or "mode=memory" in url:
            args["poolclass"] = StaticPool
    else:
        # PostgreSQL pool configuration
        args["pool_size"] = 10
        args["max_overflow"] = 20
        args["pool_pre_ping"] = True
        args["pool_recycle"] = 1800
    return args


def _create_safe_engine(url: str, is_ro: bool = False):
    try:
        eng = create_engine(url, **get_engine_args(url))
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"Connected to database successfully ({url.split('@')[-1] if '@' in url else url}).")
        return eng
    except Exception as e:
        logger.warning(f"Could not connect to configured DB ({e}). Falling back to local SQLite database.")
        sqlite_url = "sqlite:///./sales_ops.db"
        return create_engine(sqlite_url, **get_engine_args(sqlite_url))

# Primary engine (admin/read-write)
engine = _create_safe_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Read-only engine for analytics endpoints
ro_url = settings.DATABASE_RO_URL or settings.DATABASE_URL
engine_ro = _create_safe_engine(ro_url, is_ro=True)
SessionRO = sessionmaker(autocommit=False, autoflush=False, bind=engine_ro)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_ro_db() -> Generator[Session, None, None]:
    db = SessionRO()
    try:
        # Enforce read-only transaction on postgresql if supported
        if not settings.DATABASE_URL.startswith("sqlite"):
            try:
                db.execute(text("SET TRANSACTION READ ONLY"))
            except Exception:
                pass
        yield db
    finally:
        db.close()


def test_connection(use_ro: bool = False) -> bool:
    target_engine = engine_ro if use_ro else engine
    try:
        with target_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Database connection check failed: {e}")
        return False
