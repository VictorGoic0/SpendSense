from pathlib import Path

from sqlalchemy import create_engine, event, text, inspect
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
from dotenv import load_dotenv

# backend/ (parent of app/) — stable anchor for .env and SQLite paths regardless of cwd
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_BACKEND_ROOT / ".env")
load_dotenv()  # optional overrides from cwd

_raw_db_url = os.getenv("DATABASE_URL", "sqlite:///./spendsense.db")


def _normalize_sqlite_url(url: str) -> str:
    """Resolve relative SQLite file paths against backend/ so scripts work from repo root."""
    if not url.startswith("sqlite:///"):
        return url
    rest = url[len("sqlite:///") :]
    if rest == ":memory:" or not rest:
        return url
    path = Path(rest)
    if not path.is_absolute():
        path = (_BACKEND_ROOT / path).resolve()
    # Absolute path: sqlite:/// + /abs/path → four slashes after sqlite:
    return f"sqlite:///{path.as_posix()}"


SQLALCHEMY_DATABASE_URL = (
    _normalize_sqlite_url(_raw_db_url)
    if _raw_db_url.startswith("sqlite")
    else _raw_db_url
)

# SQLite connection args
connect_args = {}
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    connect_args["check_same_thread"] = False

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args=connect_args
)

# Enable WAL (Write-Ahead Logging) mode for SQLite to improve concurrency
# This allows multiple readers while a writer is active
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    if "sqlite" in SQLALCHEMY_DATABASE_URL:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

logger = logging.getLogger(__name__)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def apply_migrations():
    """Apply database migrations for schema changes"""
    if "sqlite" not in SQLALCHEMY_DATABASE_URL:
        # Only apply migrations for SQLite (PostgreSQL would use Alembic)
        return
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        
        # Migration 1: Add product_id column to recommendations table
        if "recommendations" in inspector.get_table_names():
            columns = [col["name"] for col in inspector.get_columns("recommendations")]
            if "product_id" not in columns:
                logger.info("Applying migration: Adding product_id column to recommendations table")
                try:
                    conn.execute(text("ALTER TABLE recommendations ADD COLUMN product_id TEXT"))
                    conn.commit()
                    logger.info("✓ Added product_id column to recommendations table")
                except Exception as e:
                    logger.warning(f"Migration failed (may already be applied): {e}")
                    conn.rollback()
        
        # Migration 2: Make content column nullable in recommendations table
        # Note: SQLite doesn't support ALTER COLUMN to change nullability
        # This migration was already applied via table recreation
        # New databases will be created correctly from model definitions
        # No action needed for existing databases (already migrated)
        
        # Migration 3: Add 'loan' to product_type constraint in product_offers table
        # Note: SQLite doesn't support modifying CHECK constraints
        # This migration was already applied via table recreation
        # New databases will be created correctly from model definitions
        # No action needed for existing databases (already migrated)


def init_db():
    """Initialize database by creating all tables and applying migrations."""
    def _create_all():
        Base.metadata.create_all(bind=engine)

    # SQLite + multiple Uvicorn workers: each process runs startup; concurrent
    # create_all() races (both pass checkfirst before either commits). Retry after
    # "already exists" so this worker's second pass no-ops on existing tables.
    if "sqlite" in SQLALCHEMY_DATABASE_URL:
        try:
            _create_all()
        except OperationalError as e:
            orig = getattr(e, "orig", e)
            msg = str(orig) if orig is not None else str(e)
            if "already exists" not in msg.lower():
                raise
            logger.debug("SQLite create_all race (multi-worker startup): %s", msg)
            _create_all()
    else:
        _create_all()

    apply_migrations()

