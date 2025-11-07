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
from typing import List, Dict, Optional, Any
import logging

from app.models import Transaction, Account, Liability

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


# ============================================================================
# Credit Detection
# ============================================================================

def compute_credit_signals(db: Session, user_id: str, window_days: int) -> Dict[str, Any]:
    """
    Compute credit-related behavioral signals for a user.
    
    Detects:
    - Credit utilization (average and max across all cards)
    - Utilization flags (30%, 50%, 80% thresholds)
    - Minimum payment only pattern
    - Interest charges presence
    - Overdue account status
    
    Args:
        db: Database session
        user_id: User ID to analyze
        window_days: Time window in days (30 or 180)
    
    Returns:
        Dictionary with:
        - avg_utilization: float (0-1, average utilization across cards)
        - max_utilization: float (0-1, highest single card utilization)
        - utilization_30_flag: bool (any card >= 30%)
        - utilization_50_flag: bool (any card >= 50%)
        - utilization_80_flag: bool (any card >= 80%)
        - minimum_payment_only_flag: bool (making minimum payments only)
        - interest_charges_present: bool (interest charges in window)
        - any_overdue: bool (any overdue accounts)
    """
    # Query all credit card accounts for user
    credit_card_accounts = get_accounts_by_type(db, user_id, ['credit card'])
    
    # If no credit cards, return zero/false values
    if not credit_card_accounts:
        logger.debug(f"No credit cards found for user {user_id}")
        return {
            "avg_utilization": 0.0,
            "max_utilization": 0.0,
            "utilization_30_flag": False,
            "utilization_50_flag": False,
            "utilization_80_flag": False,
            "minimum_payment_only_flag": False,
            "interest_charges_present": False,
            "any_overdue": False
        }
    
    # Get account IDs for joining with liabilities
    account_ids = [acc.account_id for acc in credit_card_accounts]
    
    # Query liabilities for these credit card accounts
    liabilities = db.query(Liability).filter(
        and_(
            Liability.user_id == user_id,
            Liability.account_id.in_(account_ids),
            Liability.liability_type == 'credit_card'
        )
    ).all()
    
    # Create a mapping of account_id to liability for easy lookup
    liability_by_account = {liab.account_id: liab for liab in liabilities}
    
    # Calculate utilization for each credit card
    utilizations = []
    max_utilization = 0.0
    utilization_30_flag = False
    utilization_50_flag = False
    utilization_80_flag = False
    
    for account in credit_card_accounts:
        balance_current = account.balance_current or 0.0
        balance_limit = account.balance_limit or 0.0
        
        # Handle division by zero (limit = 0)
        if balance_limit > 0:
            utilization = balance_current / balance_limit
            utilizations.append(utilization)
            
            # Track max utilization
            if utilization > max_utilization:
                max_utilization = utilization
            
            # Set utilization flags
            if utilization >= 0.80:
                utilization_80_flag = True
            if utilization >= 0.50:
                utilization_50_flag = True
            if utilization >= 0.30:
                utilization_30_flag = True
        else:
            logger.warning(f"Credit card account {account.account_id} has zero or null balance_limit")
    
    # Calculate average utilization
    avg_utilization = sum(utilizations) / len(utilizations) if utilizations else 0.0
    
    # Check minimum payment patterns
    minimum_payment_only_flag = False
    for account in credit_card_accounts:
        liability = liability_by_account.get(account.account_id)
        if liability:
            minimum_payment = liability.minimum_payment_amount
            last_payment = liability.last_payment_amount
            
            if minimum_payment is not None and last_payment is not None:
                # Check if last_payment <= minimum_payment (with $5 tolerance)
                tolerance = 5.0
                if last_payment <= (minimum_payment + tolerance):
                    minimum_payment_only_flag = True
                    break
    
    # Query transactions for interest charges in window
    cutoff_date = date.today() - timedelta(days=window_days)
    interest_transactions = db.query(Transaction).filter(
        and_(
            Transaction.user_id == user_id,
            Transaction.account_id.in_(account_ids),
            Transaction.date >= cutoff_date,
            Transaction.category_detailed.ilike('%interest%')
        )
    ).all()
    
    interest_charges_present = len(interest_transactions) > 0
    
    # Check for overdue accounts
    any_overdue = False
    for liability in liabilities:
        if liability.is_overdue:
            any_overdue = True
            break
    
    logger.debug(
        f"Credit signals for user {user_id}: "
        f"avg_util={avg_utilization:.2%}, max_util={max_utilization:.2%}, "
        f"min_payment_only={minimum_payment_only_flag}, interest={interest_charges_present}, "
        f"overdue={any_overdue}"
    )
    
    return {
        "avg_utilization": avg_utilization,
        "max_utilization": max_utilization,
        "utilization_30_flag": utilization_30_flag,
        "utilization_50_flag": utilization_50_flag,
        "utilization_80_flag": utilization_80_flag,
        "minimum_payment_only_flag": minimum_payment_only_flag,
        "interest_charges_present": interest_charges_present,
        "any_overdue": any_overdue
    }

