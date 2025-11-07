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
import logging

from app.models import Transaction, Account

logger = logging.getLogger(__name__)


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


# ============================================================================
# Savings Detection
# ============================================================================

def compute_savings_signals(db: Session, user_id: str, window_days: int) -> Dict[str, float]:
    """
    Compute savings-related behavioral signals for a user.
    
    Detects:
    - Net savings inflow (deposits - withdrawals, normalized to monthly)
    - Savings growth rate (percentage change in balance over window)
    - Emergency fund months (savings balance / monthly expenses)
    
    Args:
        db: Database session
        user_id: User ID to analyze
        window_days: Time window in days (30 or 180)
    
    Returns:
        Dictionary with:
        - net_savings_inflow: float (monthly average)
        - savings_growth_rate: float (0-1, average growth rate across accounts)
        - emergency_fund_months: float (months of expenses covered)
    """
    # Get savings-type accounts
    savings_account_types = ['savings', 'money market', 'cash management', 'HSA']
    savings_accounts = get_accounts_by_type(db, user_id, savings_account_types)
    
    # If no savings accounts, return zero values
    if not savings_accounts:
        # No logging needed for normal case
        return {
            "net_savings_inflow": 0.0,
            "savings_growth_rate": 0.0,
            "emergency_fund_months": 0.0
        }
    
    # Calculate net inflow for each savings account
    total_net_inflow = 0.0
    account_growth_rates = []
    
    for account in savings_accounts:
        # Get all transactions for this account in window
        cutoff_date = date.today() - timedelta(days=window_days)
        account_transactions = db.query(Transaction).filter(
            and_(
                Transaction.account_id == account.account_id,
                Transaction.date >= cutoff_date
            )
        ).all()
        
        # Separate deposits and withdrawals
        deposits = [txn.amount for txn in account_transactions if txn.amount > 0]
        withdrawals = [txn.amount for txn in account_transactions if txn.amount < 0]
        
        # Calculate net inflow for this account
        account_net_inflow = sum(deposits) + sum(withdrawals)  # withdrawals are already negative
        total_net_inflow += account_net_inflow
        
        # Calculate growth rate for this account
        current_balance = account.balance_current or 0.0
        start_balance = current_balance - account_net_inflow
        
        if start_balance > 0:
            growth_rate = (current_balance - start_balance) / start_balance
            account_growth_rates.append(growth_rate)
        elif start_balance == 0 and current_balance > 0:
            # Account started at 0, grew to current_balance
            account_growth_rates.append(1.0)  # 100% growth (or could use a different calculation)
        # If start_balance < 0, skip (invalid state)
    
    # Calculate monthly net inflow
    months_in_window = window_days / 30.0
    net_savings_inflow = total_net_inflow / months_in_window if months_in_window > 0 else 0.0
    
    # Calculate average growth rate
    savings_growth_rate = sum(account_growth_rates) / len(account_growth_rates) if account_growth_rates else 0.0
    
    # Calculate total savings balance
    total_savings_balance = sum(account.balance_current or 0.0 for account in savings_accounts)
    
    # Calculate emergency fund months
    # Get checking account transactions to estimate monthly expenses
    checking_accounts = get_accounts_by_type(db, user_id, ['checking'])
    
    avg_monthly_expenses = 0.0
    if checking_accounts:
        # Get all checking account transactions in window
        checking_transactions = []
        for checking_account in checking_accounts:
            cutoff_date = date.today() - timedelta(days=window_days)
            account_transactions = db.query(Transaction).filter(
                and_(
                    Transaction.account_id == checking_account.account_id,
                    Transaction.date >= cutoff_date
                )
            ).all()
            checking_transactions.extend(account_transactions)
        
        # Filter to expense transactions (amount < 0)
        expenses = [abs(txn.amount) for txn in checking_transactions if txn.amount < 0]
        total_expenses = sum(expenses)
        
        # Calculate average monthly expenses
        if months_in_window > 0:
            avg_monthly_expenses = total_expenses / months_in_window
    
    # Calculate emergency fund months
    if avg_monthly_expenses > 0:
        emergency_fund_months = total_savings_balance / avg_monthly_expenses
    else:
        # Edge case: no expenses detected
        emergency_fund_months = 0.0
    
    return {
        "net_savings_inflow": net_savings_inflow,
        "savings_growth_rate": savings_growth_rate,
        "emergency_fund_months": emergency_fund_months
    }

