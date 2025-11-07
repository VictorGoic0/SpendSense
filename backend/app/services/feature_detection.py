"""
Feature Detection Service

Detects behavioral patterns from transaction data:
- Subscription signals (recurring merchants, monthly spend, spend share)
- Savings signals (net inflow, growth rate, emergency fund)
- Credit signals (utilization, payment patterns)
- Income signals (payroll detection, variability)
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta, date
from collections import Counter
from typing import List, Dict, Optional

from app.models import Transaction, Account


# ============================================================================
# Helper Functions
# ============================================================================

def get_transactions_in_window(db: Session, user_id: str, window_days: int) -> List[Transaction]:
    """
    Get all transactions for a user within the specified time window.
    
    Args:
        db: Database session
        user_id: User ID to query
        window_days: Number of days to look back from today
    
    Returns:
        List of Transaction objects ordered by date ascending
    """
    cutoff_date = date.today() - timedelta(days=window_days)
    
    transactions = db.query(Transaction).filter(
        and_(
            Transaction.user_id == user_id,
            Transaction.date >= cutoff_date
        )
    ).order_by(Transaction.date.asc()).all()
    
    return transactions


def get_accounts_by_type(db: Session, user_id: str, account_types: List[str]) -> List[Account]:
    """
    Get accounts for a user filtered by account types.
    
    Args:
        db: Database session
        user_id: User ID to query
        account_types: List of account types to filter (e.g., ['checking', 'savings'])
    
    Returns:
        List of Account objects matching the types
    """
    accounts = db.query(Account).filter(
        and_(
            Account.user_id == user_id,
            Account.type.in_(account_types)
        )
    ).all()
    
    return accounts


# ============================================================================
# Subscription Detection
# ============================================================================

def is_recurring_pattern(dates: List[date], tolerance_days: int = 5) -> bool:
    """
    Check if a list of transaction dates shows a recurring pattern.
    
    Detects patterns for:
    - Weekly subscriptions (~7 days)
    - Monthly subscriptions (~30 days)
    - Quarterly subscriptions (~90 days)
    
    Args:
        dates: List of transaction dates (must be sorted chronologically)
        tolerance_days: Allowed variance in days (±tolerance_days)
    
    Returns:
        True if a recurring pattern is detected, False otherwise
    """
    if len(dates) < 3:
        return False
    
    # Calculate gaps between consecutive dates
    gaps = []
    for i in range(len(dates) - 1):
        gap = (dates[i + 1] - dates[i]).days
        gaps.append(gap)
    
    # Check for common subscription intervals
    common_intervals = [7, 30, 90]  # weekly, monthly, quarterly
    
    for interval in common_intervals:
        # Check if most gaps are within tolerance of this interval
        matching_gaps = [g for g in gaps if abs(g - interval) <= tolerance_days]
        
        # If at least 60% of gaps match the pattern, consider it recurring
        if len(matching_gaps) >= len(gaps) * 0.6:
            return True
    
    return False


def compute_subscription_signals(db: Session, user_id: str, window_days: int) -> Dict[str, float]:
    """
    Compute subscription-related behavioral signals for a user.
    
    Detects:
    - Recurring merchants (merchants with ≥3 transactions showing recurring pattern)
    - Monthly recurring spend (sum of recurring merchant transactions / months in window)
    - Subscription spend share (recurring spend / total spend)
    
    Args:
        db: Database session
        user_id: User ID to analyze
        window_days: Time window in days (30 or 180)
    
    Returns:
        Dictionary with:
        - recurring_merchants: int (count of recurring merchants)
        - monthly_recurring_spend: float (monthly average)
        - subscription_spend_share: float (0-1, ratio of recurring to total spend)
    """
    # Get all transactions in window
    transactions = get_transactions_in_window(db, user_id, window_days)
    
    if not transactions:
        return {
            "recurring_merchants": 0,
            "monthly_recurring_spend": 0.0,
            "subscription_spend_share": 0.0
        }
    
    # Group transactions by merchant_name
    merchant_transactions = {}
    for txn in transactions:
        if txn.merchant_name:
            if txn.merchant_name not in merchant_transactions:
                merchant_transactions[txn.merchant_name] = []
            merchant_transactions[txn.merchant_name].append(txn)
    
    # Filter to merchants with ≥3 transactions
    recurring_merchants = []
    recurring_merchant_names = []
    
    for merchant_name, txn_list in merchant_transactions.items():
        if len(txn_list) >= 3:
            # Extract and sort dates
            dates = sorted([txn.date for txn in txn_list])
            
            # Check if pattern is recurring
            if is_recurring_pattern(dates):
                recurring_merchants.append(txn_list)
                recurring_merchant_names.append(merchant_name)
    
    # Calculate recurring spend
    recurring_spend = 0.0
    for txn_list in recurring_merchants:
        for txn in txn_list:
            # Use absolute value since amounts can be negative
            recurring_spend += abs(txn.amount)
    
    # Calculate total spend in window
    total_spend = sum(abs(txn.amount) for txn in transactions)
    
    # Calculate monthly recurring spend
    months_in_window = window_days / 30.0
    monthly_recurring_spend = recurring_spend / months_in_window if months_in_window > 0 else 0.0
    
    # Calculate subscription spend share
    subscription_spend_share = recurring_spend / total_spend if total_spend > 0 else 0.0
    
    return {
        "recurring_merchants": len(recurring_merchants),
        "monthly_recurring_spend": monthly_recurring_spend,
        "subscription_spend_share": subscription_spend_share
    }

