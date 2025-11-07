"""
Persona Assignment Service

Assigns user personas based on computed behavioral features:
- high_utilization: Credit card debt and utilization issues
- variable_income: Irregular income patterns
- subscription_heavy: High recurring subscription spend
- savings_builder: Active savings behavior
- wealth_builder: High income, savings, and investment accounts
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta, date
from typing import Tuple, Dict, Any, Optional
import json
import logging

from app.models import UserFeature, Persona, Account, Transaction

logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================

def get_total_savings_balance(db: Session, user_id: str) -> float:
    """
    Get total savings balance for a user across all savings-type accounts.
    
    Args:
        db: Database session
        user_id: User ID to query
    
    Returns:
        Total balance_current across all savings accounts
    """
    savings_account_types = ['savings', 'money market', 'cash management', 'HSA']
    savings_accounts = db.query(Account).filter(
        and_(
            Account.user_id == user_id,
            Account.type.in_(savings_account_types)
        )
    ).all()
    
    total_balance = sum(account.balance_current or 0.0 for account in savings_accounts)
    return total_balance


def has_overdraft_or_late_fees(db: Session, user_id: str, window_days: int) -> bool:
    """
    Check if user has any overdraft or late fee transactions in the window.
    
    Args:
        db: Database session
        user_id: User ID to query
        window_days: Number of days to look back
    
    Returns:
        True if any fee transactions found, False otherwise
    """
    cutoff_date = date.today() - timedelta(days=window_days)
    
    # Query transactions with fee-related categories
    fee_transactions = db.query(Transaction).filter(
        and_(
            Transaction.user_id == user_id,
            Transaction.date >= cutoff_date,
            Transaction.amount < 0,  # Fees are negative
            (
                func.lower(Transaction.category_detailed).like('%fee%') |
                func.lower(Transaction.category_detailed).like('%overdraft%') |
                func.lower(Transaction.category_detailed).like('%late%') |
                func.lower(Transaction.merchant_name).like('%overdraft%') |
                func.lower(Transaction.merchant_name).like('%late fee%')
            )
        )
    ).first()
    
    return fee_transactions is not None


# ============================================================================
# Persona Check Functions
# ============================================================================

def check_high_utilization(features: UserFeature) -> bool:
    """
    Check if user matches high_utilization persona.
    
    Criteria:
    - max_utilization >= 0.50
    - OR interest_charges_present == True
    - OR minimum_payment_only_flag == True
    - OR any_overdue == True
    
    Args:
        features: UserFeature object
    
    Returns:
        True if matches criteria, False otherwise
    """
    if features.max_utilization is None:
        max_util = 0.0
    else:
        max_util = features.max_utilization
    
    return (
        max_util >= 0.50 or
        features.interest_charges_present == True or
        features.minimum_payment_only_flag == True or
        features.any_overdue == True
    )


def check_variable_income(features: UserFeature) -> bool:
    """
    Check if user matches variable_income persona.
    
    Criteria:
    - median_pay_gap_days > 45
    - AND cash_flow_buffer_months < 1
    
    Args:
        features: UserFeature object
    
    Returns:
        True if matches criteria, False otherwise
    """
    if features.median_pay_gap_days is None:
        return False
    
    median_gap = features.median_pay_gap_days
    buffer_months = features.cash_flow_buffer_months or 0.0
    
    return median_gap > 45 and buffer_months < 1


def check_subscription_heavy(features: UserFeature) -> bool:
    """
    Check if user matches subscription_heavy persona.
    
    Criteria:
    - recurring_merchants >= 3
    - AND (monthly_recurring_spend >= 50 OR subscription_spend_share >= 0.10)
    
    Args:
        features: UserFeature object
    
    Returns:
        True if matches criteria, False otherwise
    """
    recurring_count = features.recurring_merchants or 0
    monthly_spend = features.monthly_recurring_spend or 0.0
    spend_share = features.subscription_spend_share or 0.0
    
    return (
        recurring_count >= 3 and
        (monthly_spend >= 50.0 or spend_share >= 0.10)
    )


def check_savings_builder(features: UserFeature) -> bool:
    """
    Check if user matches savings_builder persona.
    
    Criteria:
    - (savings_growth_rate >= 0.02 OR net_savings_inflow >= 200)
    - AND avg_utilization < 0.30
    
    Args:
        features: UserFeature object
    
    Returns:
        True if matches criteria, False otherwise
    """
    growth_rate = features.savings_growth_rate or 0.0
    net_inflow = features.net_savings_inflow or 0.0
    avg_util = features.avg_utilization or 0.0
    
    return (
        (growth_rate >= 0.02 or net_inflow >= 200.0) and
        avg_util < 0.30
    )


def check_wealth_builder(db: Session, features: UserFeature) -> bool:
    """
    Check if user matches wealth_builder persona.
    
    Criteria:
    - avg_monthly_income > 10000
    - AND savings_balance > 25000 (query from accounts)
    - AND max_utilization <= 0.20
    - AND no overdrafts/late fees (check from transactions)
    - AND investment_account_detected == True
    
    Args:
        db: Database session
        features: UserFeature object
    
    Returns:
        True if matches criteria, False otherwise
    """
    avg_income = features.avg_monthly_income or 0.0
    if avg_income <= 10000:
        return False
    
    savings_balance = get_total_savings_balance(db, features.user_id)
    if savings_balance <= 25000:
        return False
    
    max_util = features.max_utilization or 0.0
    if max_util > 0.20:
        return False
    
    # Check for overdrafts/late fees (use 180-day window for wealth builder check)
    has_fees = has_overdraft_or_late_fees(db, features.user_id, 180)
    if has_fees:
        return False
    
    investment_detected = features.investment_account_detected or False
    if not investment_detected:
        return False
    
    return True


# ============================================================================
# Persona Assignment Logic
# ============================================================================

def assign_persona(db: Session, user_id: str, window_days: int) -> Tuple[str, float, Dict[str, Any]]:
    """
    Assign persona to user based on computed features.
    
    Checks personas in priority order:
    1. wealth_builder (priority 1.0)
    2. high_utilization (priority 0.95 if util>=80%, else 0.8)
    3. savings_builder (priority 0.7)
    4. variable_income (priority 0.6)
    5. subscription_heavy (priority 0.5)
    
    If no matches, returns 'savings_builder' with low confidence (0.1 if no features, 0.2 if features exist but no match).
    
    Args:
        db: Database session
        user_id: User ID to assign persona for
        window_days: Time window (30 or 180)
    
    Returns:
        Tuple of (persona_type, confidence_score, reasoning_dict)
    """
    # Query UserFeature for user and window
    features = db.query(UserFeature).filter(
        and_(
            UserFeature.user_id == user_id,
            UserFeature.window_days == window_days
        )
    ).first()
    
    # If no features found, return savings_builder as fallback with very low confidence
    if not features:
        logger.warning(f"No features found for user {user_id}, window {window_days}d - assigning savings_builder as fallback")
        return ('savings_builder', 0.1, {
            'matched_criteria': [],
            'feature_values': {},
            'timestamp': datetime.now().isoformat(),
            'reason': 'No features computed for this user/window - fallback assignment'
        })
    
    # Create list of matched personas with priorities
    matched_personas = []
    
    # Check wealth_builder first (priority 1.0)
    if check_wealth_builder(db, features):
        matched_personas.append({
            'type': 'wealth_builder',
            'priority': 1.0,
            'criteria': [
                f'avg_monthly_income={features.avg_monthly_income:.2f} > 10000',
                f'savings_balance={get_total_savings_balance(db, user_id):.2f} > 25000',
                f'max_utilization={features.max_utilization:.2%} <= 0.20',
                'no_overdraft_or_late_fees=True',
                f'investment_account_detected={features.investment_account_detected}'
            ],
            'feature_values': {
                'avg_monthly_income': features.avg_monthly_income,
                'savings_balance': get_total_savings_balance(db, user_id),
                'max_utilization': features.max_utilization,
                'investment_account_detected': features.investment_account_detected
            }
        })
    
    # Check high_utilization (priority 0.95 if util>=80%, else 0.8)
    if check_high_utilization(features):
        max_util = features.max_utilization or 0.0
        priority = 0.95 if max_util >= 0.80 else 0.8
        
        criteria = []
        if max_util >= 0.50:
            criteria.append(f'max_utilization={max_util:.2%} >= 0.50')
        if features.interest_charges_present:
            criteria.append('interest_charges_present=True')
        if features.minimum_payment_only_flag:
            criteria.append('minimum_payment_only_flag=True')
        if features.any_overdue:
            criteria.append('any_overdue=True')
        
        matched_personas.append({
            'type': 'high_utilization',
            'priority': priority,
            'criteria': criteria,
            'feature_values': {
                'max_utilization': features.max_utilization,
                'interest_charges_present': features.interest_charges_present,
                'minimum_payment_only_flag': features.minimum_payment_only_flag,
                'any_overdue': features.any_overdue
            }
        })
    
    # Check savings_builder (priority 0.7)
    if check_savings_builder(features):
        criteria = []
        if features.savings_growth_rate and features.savings_growth_rate >= 0.02:
            criteria.append(f'savings_growth_rate={features.savings_growth_rate:.2%} >= 0.02')
        if features.net_savings_inflow and features.net_savings_inflow >= 200:
            criteria.append(f'net_savings_inflow={features.net_savings_inflow:.2f} >= 200')
        if features.avg_utilization and features.avg_utilization < 0.30:
            criteria.append(f'avg_utilization={features.avg_utilization:.2%} < 0.30')
        
        matched_personas.append({
            'type': 'savings_builder',
            'priority': 0.7,
            'criteria': criteria,
            'feature_values': {
                'savings_growth_rate': features.savings_growth_rate,
                'net_savings_inflow': features.net_savings_inflow,
                'avg_utilization': features.avg_utilization
            }
        })
    
    # Check variable_income (priority 0.6)
    if check_variable_income(features):
        matched_personas.append({
            'type': 'variable_income',
            'priority': 0.6,
            'criteria': [
                f'median_pay_gap_days={features.median_pay_gap_days} > 45',
                f'cash_flow_buffer_months={features.cash_flow_buffer_months:.2f} < 1'
            ],
            'feature_values': {
                'median_pay_gap_days': features.median_pay_gap_days,
                'cash_flow_buffer_months': features.cash_flow_buffer_months
            }
        })
    
    # Check subscription_heavy (priority 0.5)
    if check_subscription_heavy(features):
        criteria = []
        if features.recurring_merchants and features.recurring_merchants >= 3:
            criteria.append(f'recurring_merchants={features.recurring_merchants} >= 3')
        if features.monthly_recurring_spend and features.monthly_recurring_spend >= 50:
            criteria.append(f'monthly_recurring_spend={features.monthly_recurring_spend:.2f} >= 50')
        if features.subscription_spend_share and features.subscription_spend_share >= 0.10:
            criteria.append(f'subscription_spend_share={features.subscription_spend_share:.2%} >= 0.10')
        
        matched_personas.append({
            'type': 'subscription_heavy',
            'priority': 0.5,
            'criteria': criteria,
            'feature_values': {
                'recurring_merchants': features.recurring_merchants,
                'monthly_recurring_spend': features.monthly_recurring_spend,
                'subscription_spend_share': features.subscription_spend_share
            }
        })
    
    # If no matches, return savings_builder as fallback with low confidence
    if not matched_personas:
        logger.info(f"No persona criteria matched for user {user_id}, window {window_days}d - assigning savings_builder as fallback")
        return ('savings_builder', 0.2, {
            'matched_criteria': [],
            'feature_values': {},
            'timestamp': datetime.now().isoformat(),
            'reason': 'No persona criteria matched - fallback assignment'
        })
    
    # Sort matched personas by priority (descending)
    matched_personas.sort(key=lambda x: x['priority'], reverse=True)
    
    # Return highest priority persona
    top_persona = matched_personas[0]
    
    reasoning_dict = {
        'matched_criteria': top_persona['criteria'],
        'feature_values': top_persona['feature_values'],
        'timestamp': datetime.now().isoformat(),
        'priority': top_persona['priority'],
        'all_matched_personas': [p['type'] for p in matched_personas]
    }
    
    return (top_persona['type'], top_persona['priority'], reasoning_dict)


def create_or_update_persona(
    db: Session,
    user_id: str,
    window_days: int,
    persona_type: str,
    confidence: float,
    reasoning: Dict[str, Any]
) -> Persona:
    """
    Create or update Persona record in database.
    
    Args:
        db: Database session
        user_id: User ID
        window_days: Time window (30 or 180)
        persona_type: Persona type string
        confidence: Confidence score (0.0-1.0)
        reasoning: Reasoning dictionary (will be JSON-serialized)
    
    Returns:
        Persona object (created or updated)
    """
    # Check if Persona record exists for user + window
    existing_persona = db.query(Persona).filter(
        and_(
            Persona.user_id == user_id,
            Persona.window_days == window_days
        )
    ).first()
    
    # Serialize reasoning dict to JSON string
    reasoning_json = json.dumps(reasoning)
    
    if existing_persona:
        # Update existing record
        existing_persona.persona_type = persona_type
        existing_persona.confidence_score = confidence
        existing_persona.reasoning = reasoning_json
        existing_persona.assigned_at = datetime.now()
        db.commit()
        db.refresh(existing_persona)
        logger.info(f"Updated persona for user {user_id}, window {window_days}d: {persona_type}")
        return existing_persona
    else:
        # Create new Persona record
        new_persona = Persona(
            user_id=user_id,
            window_days=window_days,
            persona_type=persona_type,
            confidence_score=confidence,
            reasoning=reasoning_json,
            assigned_at=datetime.now()
        )
        db.add(new_persona)
        db.commit()
        db.refresh(new_persona)
        logger.info(f"Created persona for user {user_id}, window {window_days}d: {persona_type}")
        return new_persona


def assign_and_save_persona(db: Session, user_id: str, window_days: int) -> Persona:
    """
    Main function to assign and save persona for a user.
    
    Args:
        db: Database session
        user_id: User ID to assign persona for
        window_days: Time window (30 or 180)
    
    Returns:
        Persona object (created or updated)
    """
    # Call assign_persona() to get type, confidence, reasoning
    persona_type, confidence, reasoning = assign_persona(db, user_id, window_days)
    
    # Call create_or_update_persona() to save
    persona = create_or_update_persona(db, user_id, window_days, persona_type, confidence, reasoning)
    
    return persona

