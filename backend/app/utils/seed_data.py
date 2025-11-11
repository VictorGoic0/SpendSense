"""
Utility function to seed database with synthetic data from JSON files.
Used on Lambda cold start to pre-populate the database.
"""
import json
import logging
import time
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from app.models import User, Account, Transaction, Liability
from app.schemas import IngestRequest

logger = logging.getLogger(__name__)


def get_data_path() -> Path:
    """
    Get the path to the data directory.
    Works in both local development and Lambda environments.
    """
    # In Lambda, the code is in /var/task
    # The data directory is copied to backend/data/ during build
    current_path = Path(__file__).resolve()
    # current_path is backend/app/utils/seed_data.py
    # Go up to backend/ directory
    backend_dir = current_path.parent.parent.parent
    
    # Try backend/data/ first (data is now in backend/data/)
    backend_data_path = backend_dir / "data"
    if backend_data_path.exists():
        return backend_data_path
    
    # Try /var/task/data (Lambda absolute path)
    lambda_path = Path("/var/task/data")
    if lambda_path.exists():
        return lambda_path
    
    # Fall back to project root data/ (for backwards compatibility)
    project_root = backend_dir.parent
    data_path = project_root / "data"
    
    return data_path


def is_database_empty(db: Session) -> bool:
    """Check if database has any users (indicates if it's been seeded)"""
    try:
        user_count = db.query(User).count()
        return user_count == 0
    except Exception as e:
        logger.warning(f"Error checking database: {e}")
        # If we can't check, assume it's empty and try to seed
        return True


def _ingest_data_sync(request: IngestRequest, db: Session) -> dict:
    """
    Synchronous version of ingest logic for use in seeding.
    Returns dict with ingested counts and duration_ms.
    """
    start_time = time.time()
    ingested_counts = {
        "users": 0,
        "accounts": 0,
        "transactions": 0,
        "liabilities": 0,
        "products": 0
    }
    
    try:
        # Process Users
        if request.users:
            user_objects = []
            for user_data in request.users:
                user_obj = User(
                    user_id=user_data.user_id,
                    full_name=user_data.full_name,
                    email=user_data.email,
                    user_type=user_data.user_type,
                    consent_status=user_data.consent_status,
                    consent_granted_at=user_data.consent_granted_at,
                    consent_revoked_at=user_data.consent_revoked_at,
                    created_at=user_data.created_at or datetime.utcnow()
                )
                user_objects.append(user_obj)
            
            db.bulk_save_objects(user_objects)
            db.commit()
            ingested_counts["users"] = len(user_objects)
        
        # Process Accounts
        if request.accounts:
            account_objects = []
            for account_data in request.accounts:
                account_obj = Account(
                    account_id=account_data.account_id,
                    user_id=account_data.user_id,
                    type=account_data.type,
                    subtype=account_data.subtype,
                    balance_available=account_data.balance_available,
                    balance_current=account_data.balance_current,
                    balance_limit=account_data.balance_limit,
                    iso_currency_code=account_data.iso_currency_code,
                    holder_category=account_data.holder_category,
                    created_at=account_data.created_at or datetime.utcnow()
                )
                account_objects.append(account_obj)
            
            db.bulk_save_objects(account_objects)
            db.commit()
            ingested_counts["accounts"] = len(account_objects)
        
        # Process Transactions (in batches of 1000)
        if request.transactions:
            batch_size = 1000
            total_transactions = 0
            
            for i in range(0, len(request.transactions), batch_size):
                batch = request.transactions[i:i + batch_size]
                transaction_objects = []
                
                for transaction_data in batch:
                    transaction_obj = Transaction(
                        transaction_id=transaction_data.transaction_id,
                        account_id=transaction_data.account_id,
                        user_id=transaction_data.user_id,
                        date=transaction_data.date,
                        amount=transaction_data.amount,
                        merchant_name=transaction_data.merchant_name,
                        merchant_entity_id=transaction_data.merchant_entity_id,
                        payment_channel=transaction_data.payment_channel,
                        category_primary=transaction_data.category_primary,
                        category_detailed=transaction_data.category_detailed,
                        pending=transaction_data.pending,
                        created_at=transaction_data.created_at or datetime.utcnow()
                    )
                    transaction_objects.append(transaction_obj)
                
                db.bulk_save_objects(transaction_objects)
                db.commit()
                total_transactions += len(transaction_objects)
            
            ingested_counts["transactions"] = total_transactions
        
        # Process Liabilities
        if request.liabilities:
            liability_objects = []
            for liability_data in request.liabilities:
                liability_obj = Liability(
                    liability_id=liability_data.liability_id,
                    account_id=liability_data.account_id,
                    user_id=liability_data.user_id,
                    liability_type=liability_data.liability_type,
                    apr_purchase=liability_data.apr_purchase,
                    apr_balance_transfer=liability_data.apr_balance_transfer,
                    apr_cash_advance=liability_data.apr_cash_advance,
                    minimum_payment_amount=liability_data.minimum_payment_amount,
                    last_payment_amount=liability_data.last_payment_amount,
                    is_overdue=liability_data.is_overdue,
                    next_payment_due_date=liability_data.next_payment_due_date,
                    last_statement_balance=liability_data.last_statement_balance,
                    interest_rate=liability_data.interest_rate,
                    created_at=liability_data.created_at or datetime.utcnow()
                )
                liability_objects.append(liability_obj)
            
            db.bulk_save_objects(liability_objects)
            db.commit()
            ingested_counts["liabilities"] = len(liability_objects)
        
        duration_ms = int((time.time() - start_time) * 1000)
        ingested_counts["duration_ms"] = duration_ms
        
        return ingested_counts
        
    except IntegrityError as e:
        db.rollback()
        # Handle duplicate key errors gracefully (idempotency)
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        if "UNIQUE constraint" in error_msg or "duplicate key" in error_msg.lower():
            logger.warning(f"Duplicate data detected during seed: {error_msg}")
            # Return what we've ingested so far
            duration_ms = int((time.time() - start_time) * 1000)
            ingested_counts["duration_ms"] = duration_ms
            return ingested_counts
        raise
    except Exception as e:
        db.rollback()
        raise


def seed_database(db: Session) -> bool:
    """
    Seed database with synthetic data from JSON files.
    Returns True if seeding was successful, False otherwise.
    """
    try:
        # Check if database is already seeded
        if not is_database_empty(db):
            logger.info("Database already contains data, skipping seed")
            return True
        
        logger.info("Database is empty, starting seed process...")
        
        # Get path to data directory
        data_path = get_data_path()
        
        # Load JSON files
        users_file = data_path / "synthetic_users.json"
        accounts_file = data_path / "synthetic_accounts.json"
        transactions_file = data_path / "synthetic_transactions.json"
        liabilities_file = data_path / "synthetic_liabilities.json"
        
        # Check if files exist
        missing_files = []
        for file_path, name in [
            (users_file, "synthetic_users.json"),
            (accounts_file, "synthetic_accounts.json"),
            (transactions_file, "synthetic_transactions.json"),
            (liabilities_file, "synthetic_liabilities.json"),
        ]:
            if not file_path.exists():
                missing_files.append(name)
        
        if missing_files:
            logger.warning(
                f"Seed data files not found: {', '.join(missing_files)}. "
                f"Data directory: {data_path}. Skipping seed."
            )
            return False
        
        # Load JSON data
        logger.info(f"Loading seed data from {data_path}")
        with open(users_file, 'r') as f:
            users_data = json.load(f)
        with open(accounts_file, 'r') as f:
            accounts_data = json.load(f)
        with open(transactions_file, 'r') as f:
            transactions_data = json.load(f)
        with open(liabilities_file, 'r') as f:
            liabilities_data = json.load(f)
        
        logger.info(
            f"Loaded: {len(users_data)} users, {len(accounts_data)} accounts, "
            f"{len(transactions_data)} transactions, {len(liabilities_data)} liabilities"
        )
        
        # Convert dict data to Pydantic models
        from app.schemas import UserCreate, AccountCreate, TransactionCreate, LiabilityCreate
        
        users = [UserCreate(**u) for u in users_data]
        accounts = [AccountCreate(**a) for a in accounts_data]
        transactions = [TransactionCreate(**t) for t in transactions_data]
        liabilities = [LiabilityCreate(**l) for l in liabilities_data]
        
        # Create ingest request
        ingest_request = IngestRequest(
            users=users,
            accounts=accounts,
            transactions=transactions,
            liabilities=liabilities,
            products=None  # Products can be ingested separately if needed
        )
        
        # Ingest data synchronously
        result = _ingest_data_sync(ingest_request, db)
        
        logger.info(
            f"✅ Database seeded successfully: {result} "
            f"(took {result.get('duration_ms', 0)}ms)"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}", exc_info=True)
        return False

