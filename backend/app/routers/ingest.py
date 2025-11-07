from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import time
from typing import List

from app.database import get_db
from app.models import User, Account, Transaction, Liability
from app.schemas import IngestRequest, IngestResponse

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/", response_model=IngestResponse)
async def ingest_data(
    request: IngestRequest,
    db: Session = Depends(get_db)
):
    """
    Bulk ingest users, accounts, transactions, and liabilities into the database.
    
    Handles data in the following order:
    1. Users (must be inserted first due to foreign key constraints)
    2. Accounts (depends on users)
    3. Transactions (depends on accounts and users)
    4. Liabilities (depends on accounts and users)
    
    Transactions are processed in batches of 1000 for performance.
    """
    start_time = time.time()
    
    try:
        ingested_counts = {
            "users": 0,
            "accounts": 0,
            "transactions": 0,
            "liabilities": 0
        }
        
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
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        return IngestResponse(
            status="success",
            ingested=ingested_counts,
            duration_ms=duration_ms
        )
    
    except IntegrityError as e:
        db.rollback()
        # Handle duplicate key errors gracefully (idempotency)
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        if "UNIQUE constraint" in error_msg or "duplicate key" in error_msg.lower():
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate data detected. Some records may already exist. Error: {error_msg}"
            )
        raise HTTPException(
            status_code=400,
            detail=f"Database integrity error: {error_msg}"
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error ingesting data: {str(e)}"
        )

