"""
Recommendation Engine Service

Builds user context from database queries and generates AI recommendations.
Context includes user features, accounts, transactions, and persona-specific data.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, List
import logging
import os
from dotenv import load_dotenv

from app.models import User, UserFeature, Persona, Account, Transaction, Liability
from app.utils.prompt_loader import load_prompt

load_dotenv()

logger = logging.getLogger(__name__)


# ============================================================================
# OpenAI Client Setup
# ============================================================================

def get_openai_client():
    """
    Get OpenAI client instance with API key from environment.
    
    Returns:
        OpenAI client instance
    
    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("OpenAI package not installed. Run: pip install openai")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    return OpenAI(api_key=api_key)


# ============================================================================
# User Context Builder
# ============================================================================

def build_user_context(db: Session, user_id: str, window_days: int) -> Dict[str, Any]:
    """
    Build comprehensive user context for recommendation generation.
    
    Queries:
    - User record
    - UserFeature record for window
    - Persona record for window
    - Account records (top 5 by balance)
    - Recent transactions (last 10, last 30 days)
    - Credit card details for high utilization
    - Recurring merchants list
    - Savings account growth info
    
    Args:
        db: Database session
        user_id: User ID to build context for
        window_days: Time window in days (30 or 180)
    
    Returns:
        Dictionary with complete user context
    """
    # Query User record
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    # Query UserFeature record for window
    user_feature = db.query(UserFeature).filter(
        and_(
            UserFeature.user_id == user_id,
            UserFeature.window_days == window_days
        )
    ).first()
    
    # Query Persona record for window
    persona = db.query(Persona).filter(
        and_(
            Persona.user_id == user_id,
            Persona.window_days == window_days
        )
    ).first()
    
    # Create base context dict
    context = {
        "user_id": user_id,
        "window_days": window_days,
        "persona_type": persona.persona_type if persona else None,
    }
    
    # Add features to context dict
    if user_feature:
        # Subscription signals
        context["subscription_signals"] = {
            "recurring_merchants": user_feature.recurring_merchants or 0,
            "monthly_recurring_spend": round(user_feature.monthly_recurring_spend or 0.0, 2),
            "subscription_spend_share": round(user_feature.subscription_spend_share or 0.0, 2),
        }
        
        # Savings signals
        context["savings_signals"] = {
            "net_savings_inflow": round(user_feature.net_savings_inflow or 0.0, 2),
            "savings_growth_rate": round(user_feature.savings_growth_rate or 0.0, 2),
            "emergency_fund_months": round(user_feature.emergency_fund_months or 0.0, 2),
        }
        
        # Credit signals
        context["credit_signals"] = {
            "avg_utilization": round(user_feature.avg_utilization or 0.0, 2),
            "max_utilization": round(user_feature.max_utilization or 0.0, 2),
            "utilization_30_flag": user_feature.utilization_30_flag or False,
            "utilization_50_flag": user_feature.utilization_50_flag or False,
            "utilization_80_flag": user_feature.utilization_80_flag or False,
            "minimum_payment_only_flag": user_feature.minimum_payment_only_flag or False,
            "interest_charges_present": user_feature.interest_charges_present or False,
            "any_overdue": user_feature.any_overdue or False,
        }
        
        # Income signals
        context["income_signals"] = {
            "payroll_detected": user_feature.payroll_detected or False,
            "median_pay_gap_days": user_feature.median_pay_gap_days,
            "income_variability": round(user_feature.income_variability or 0.0, 2) if user_feature.income_variability else None,
            "cash_flow_buffer_months": round(user_feature.cash_flow_buffer_months or 0.0, 2),
            "avg_monthly_income": round(user_feature.avg_monthly_income or 0.0, 2),
        }
    else:
        # Default values if no features found
        context["subscription_signals"] = {
            "recurring_merchants": 0,
            "monthly_recurring_spend": 0.0,
            "subscription_spend_share": 0.0,
        }
        context["savings_signals"] = {
            "net_savings_inflow": 0.0,
            "savings_growth_rate": 0.0,
            "emergency_fund_months": 0.0,
        }
        context["credit_signals"] = {
            "avg_utilization": 0.0,
            "max_utilization": 0.0,
            "utilization_30_flag": False,
            "utilization_50_flag": False,
            "utilization_80_flag": False,
            "minimum_payment_only_flag": False,
            "interest_charges_present": False,
            "any_overdue": False,
        }
        context["income_signals"] = {
            "payroll_detected": False,
            "median_pay_gap_days": None,
            "income_variability": None,
            "cash_flow_buffer_months": 0.0,
            "avg_monthly_income": 0.0,
        }
    
    # Query Account records for user
    accounts = db.query(Account).filter(
        Account.user_id == user_id
    ).order_by(desc(Account.balance_current)).limit(5).all()
    
    # Create account info dicts
    account_list = []
    for account in accounts:
        # Mask account ID for privacy (show last 4 digits)
        account_id_masked = f"****{account.account_id[-4:]}" if len(account.account_id) >= 4 else "****"
        account_name = f"{account.type.title()} {account_id_masked}"
        
        account_info = {
            "type": account.type,
            "name": account_name,
            "balance": round(account.balance_current or 0.0, 2),
        }
        
        # Add limit for credit cards
        if account.type == "credit card" and account.balance_limit:
            account_info["limit"] = round(account.balance_limit, 2)
        
        account_list.append(account_info)
    
    context["accounts"] = account_list
    
    # Query Transaction records for user in last 30 days
    cutoff_date = date.today() - timedelta(days=30)
    transactions = db.query(Transaction).filter(
        and_(
            Transaction.user_id == user_id,
            Transaction.date >= cutoff_date
        )
    ).order_by(desc(Transaction.date)).limit(10).all()
    
    # Create transaction dicts
    transaction_list = []
    for txn in transactions:
        transaction_info = {
            "date": txn.date.isoformat(),
            "merchant": txn.merchant_name or "Unknown",
            "amount": round(txn.amount, 2),
            "type": "deposit" if txn.amount > 0 else "expense",
        }
        transaction_list.append(transaction_info)
    
    context["recent_transactions"] = transaction_list
    
    # For credit cards with high utilization, add detailed info
    if user_feature and user_feature.max_utilization and user_feature.max_utilization >= 0.50:
        credit_card_accounts = db.query(Account).filter(
            and_(
                Account.user_id == user_id,
                Account.type == "credit card"
            )
        ).all()
        
        high_utilization_cards = []
        for account in credit_card_accounts:
            balance = account.balance_current or 0.0
            limit = account.balance_limit or 0.0
            
            if limit > 0:
                utilization = balance / limit
                if utilization >= 0.50:  # High utilization threshold
                    # Get liability info if available
                    liability = db.query(Liability).filter(
                        and_(
                            Liability.account_id == account.account_id,
                            Liability.user_id == user_id
                        )
                    ).first()
                    
                    card_info = {
                        "last_4_digits": account.account_id[-4:] if len(account.account_id) >= 4 else "****",
                        "current_balance": round(balance, 2),
                        "credit_limit": round(limit, 2),
                        "utilization_percentage": round(utilization * 100, 2),
                    }
                    
                    # Add interest info if available
                    if liability:
                        if liability.interest_rate:
                            card_info["interest_rate"] = round(liability.interest_rate, 2)
                        if liability.minimum_payment_amount:
                            card_info["minimum_payment"] = round(liability.minimum_payment_amount, 2)
                        
                        # Estimate monthly interest charges
                        if liability.interest_rate and balance > 0:
                            monthly_interest = (balance * liability.interest_rate / 100) / 12
                            card_info["estimated_monthly_interest"] = round(monthly_interest, 2)
                    
                    high_utilization_cards.append(card_info)
        
        if high_utilization_cards:
            context["high_utilization_cards"] = high_utilization_cards
    
    # For recurring merchants, add list of merchant names
    if user_feature and user_feature.recurring_merchants and user_feature.recurring_merchants > 0:
        # Get transactions in window to find recurring merchants
        window_cutoff = date.today() - timedelta(days=window_days)
        window_transactions = db.query(Transaction).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.date >= window_cutoff,
                Transaction.merchant_name.isnot(None)
            )
        ).all()
        
        # Group by merchant and count occurrences
        merchant_counts = {}
        for txn in window_transactions:
            merchant = txn.merchant_name
            if merchant:
                merchant_counts[merchant] = merchant_counts.get(merchant, 0) + 1
        
        # Get merchants with 3+ transactions (likely recurring)
        recurring_merchants = [
            merchant for merchant, count in merchant_counts.items()
            if count >= 3
        ]
        
        if recurring_merchants:
            context["recurring_merchants"] = recurring_merchants[:10]  # Limit to top 10
    
    # For savings accounts, add growth trend info
    if user_feature and user_feature.savings_growth_rate:
        savings_accounts = db.query(Account).filter(
            and_(
                Account.user_id == user_id,
                Account.type.in_(["savings", "money market", "cash management", "HSA"])
            )
        ).all()
        
        if savings_accounts:
            total_savings_balance = sum(acc.balance_current or 0.0 for acc in savings_accounts)
            context["savings_accounts"] = {
                "count": len(savings_accounts),
                "total_balance": round(total_savings_balance, 2),
                "growth_rate": round(user_feature.savings_growth_rate, 2),
                "emergency_fund_months": round(user_feature.emergency_fund_months, 2),
            }
    
    logger.info(f"Built context for user {user_id}, window {window_days}d")
    return context


# ============================================================================
# Context Validation
# ============================================================================

def validate_context(context: Dict[str, Any]) -> bool:
    """
    Validate that context dict has required fields and correct data types.
    
    Args:
        context: Context dictionary to validate
    
    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        "user_id",
        "window_days",
        "persona_type",
        "subscription_signals",
        "savings_signals",
        "credit_signals",
        "income_signals",
        "accounts",
        "recent_transactions",
    ]
    
    # Check required fields present
    for field in required_fields:
        if field not in context:
            logger.error(f"Missing required field in context: {field}")
            return False
    
    # Check data types
    if not isinstance(context["user_id"], str):
        logger.error(f"Invalid user_id type: {type(context['user_id'])}")
        return False
    
    if not isinstance(context["window_days"], int):
        logger.error(f"Invalid window_days type: {type(context['window_days'])}")
        return False
    
    if context["persona_type"] is not None and not isinstance(context["persona_type"], str):
        logger.error(f"Invalid persona_type type: {type(context['persona_type'])}")
        return False
    
    if not isinstance(context["accounts"], list):
        logger.error(f"Invalid accounts type: {type(context['accounts'])}")
        return False
    
    if not isinstance(context["recent_transactions"], list):
        logger.error(f"Invalid recent_transactions type: {type(context['recent_transactions'])}")
        return False
    
    # Check signal dicts
    signal_fields = ["subscription_signals", "savings_signals", "credit_signals", "income_signals"]
    for field in signal_fields:
        if not isinstance(context[field], dict):
            logger.error(f"Invalid {field} type: {type(context[field])}")
            return False
    
    logger.debug(f"Context validation passed for user {context['user_id']}")
    return True

