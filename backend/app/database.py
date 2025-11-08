from sqlalchemy import create_engine, event, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./spendsense.db")

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
    """Initialize database by creating all tables and applying migrations"""
    # Create all tables from models
    Base.metadata.create_all(bind=engine)
    
    # Apply any pending migrations
    apply_migrations()

