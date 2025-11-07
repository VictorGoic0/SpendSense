"""
Operator Router

Endpoints for operator dashboard and operator-specific functionality.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, Any, List

from app.database import get_db
from app.models import User, Persona, Recommendation, UserFeature, Transaction, Account, Liability
from app.services.feature_detection import (
    get_transactions_in_window,
    get_accounts_by_type,
    is_recurring_pattern
)

router = APIRouter(prefix="/operator", tags=["operator"])


@router.get("/dashboard")
async def get_operator_dashboard(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get operator dashboard metrics and statistics.
    
    Returns:
        Dictionary with:
        - total_users: Total number of users
        - users_with_consent: Number of users with consent_status=True
        - persona_distribution: Count of users per persona type (30d window)
        - recommendations: Count of recommendations per status
        - metrics: Performance metrics (avg_latency_ms)
    """
    try:
        # Total users count
        total_users = db.query(func.count(User.user_id)).scalar()
        
        # Users with consent count
        users_with_consent = db.query(func.count(User.user_id)).filter(
            User.consent_status == True
        ).scalar()
        
        # Persona distribution (30d window)
        persona_distribution = {}
        personas_30d = db.query(
            Persona.persona_type,
            func.count(Persona.persona_id).label('count')
        ).filter(
            Persona.window_days == 30
        ).group_by(Persona.persona_type).all()
        
        for persona_type, count in personas_30d:
            persona_distribution[persona_type] = count
        
        # Recommendation status breakdown
        recommendations = {}
        rec_statuses = db.query(
            Recommendation.status,
            func.count(Recommendation.recommendation_id).label('count')
        ).group_by(Recommendation.status).all()
        
        for status, count in rec_statuses:
            recommendations[status] = count
        
        # Average latency from recommendations
        avg_latency_result = db.query(
            func.avg(Recommendation.generation_time_ms)
        ).filter(
            Recommendation.generation_time_ms.isnot(None)
        ).scalar()
        
        avg_latency_ms = round(avg_latency_result, 2) if avg_latency_result else 0.0
        
        return {
            "total_users": total_users or 0,
            "users_with_consent": users_with_consent or 0,
            "persona_distribution": persona_distribution,
            "recommendations": recommendations,
            "metrics": {
                "avg_latency_ms": avg_latency_ms
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")


def get_recurring_merchant_names(db: Session, user_id: str, window_days: int) -> List[str]:
    """
    Get list of recurring merchant names for a user in the specified window.
    
    Args:
        db: Database session
        user_id: User ID
        window_days: Time window in days
    
    Returns:
        List of merchant names that show recurring patterns
    """
    transactions = get_transactions_in_window(db, user_id, window_days)
    
    # Group transactions by merchant name
    merchant_transactions = {}
    for txn in transactions:
        if txn.merchant_name:
            if txn.merchant_name not in merchant_transactions:
                merchant_transactions[txn.merchant_name] = []
            merchant_transactions[txn.merchant_name].append(txn)
    
    # Filter to merchants with ≥3 transactions showing recurring pattern
    recurring_merchant_names = []
    for merchant_name, txn_list in merchant_transactions.items():
        if len(txn_list) >= 3:
            dates = sorted([txn.date for txn in txn_list])
            if is_recurring_pattern(dates):
                recurring_merchant_names.append(merchant_name)
    
    return recurring_merchant_names


def get_credit_card_details(db: Session, user_id: str) -> List[Dict[str, Any]]:
    """
    Get credit card details for a user.
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        List of credit card dictionaries with last_four, utilization, balance, limit
    """
    credit_card_accounts = get_accounts_by_type(db, user_id, ['credit card'])
    
    cards = []
    for account in credit_card_accounts:
        balance = account.balance_current or 0.0
        limit = account.balance_limit or 0.0
        utilization = balance / limit if limit > 0 else 0.0
        
        # Extract last four digits from account_id (assuming format like "acc_1234567890")
        # If account_id doesn't have a standard format, use last 4 chars
        account_id_str = str(account.account_id)
        if len(account_id_str) >= 4:
            last_four = account_id_str[-4:]
        else:
            last_four = account_id_str
        
        cards.append({
            "last_four": last_four,
            "utilization": round(utilization, 4),
            "balance": round(balance, 2),
            "limit": round(limit, 2)
        })
    
    return cards


def calculate_income_frequency(db: Session, user_id: str, window_days: int) -> str:
    """
    Calculate income frequency from transaction patterns.
    
    Args:
        db: Database session
        user_id: User ID
        window_days: Time window in days
    
    Returns:
        Income frequency string: "biweekly", "monthly", or "unknown"
    """
    transactions = get_transactions_in_window(db, user_id, window_days)
    
    # Filter to income transactions (positive amounts, likely deposits)
    # Check for payroll-related transactions
    income_transactions = []
    for txn in transactions:
        if txn.amount > 0:  # Deposits
            # Check if it's likely payroll (category or merchant name)
            is_payroll = False
            if txn.category_primary and 'income' in txn.category_primary.lower():
                is_payroll = True
            elif txn.merchant_name:
                merchant_upper = txn.merchant_name.upper()
                if 'PAYROLL' in merchant_upper or 'SALARY' in merchant_upper:
                    is_payroll = True
            
            if is_payroll:
                income_transactions.append(txn)
    
    if len(income_transactions) < 2:
        return "unknown"
    
    # Sort by date and calculate gaps
    income_transactions.sort(key=lambda x: x.date)
    dates = [txn.date for txn in income_transactions]
    
    # Calculate gaps between consecutive income transactions
    gaps = []
    for i in range(len(dates) - 1):
        gap = (dates[i + 1] - dates[i]).days
        gaps.append(gap)
    
    if not gaps:
        return "unknown"
    
    # Calculate average gap
    avg_gap = sum(gaps) / len(gaps)
    
    # Determine frequency based on average gap
    if 12 <= avg_gap <= 16:  # Approximately biweekly (14 days)
        return "biweekly"
    elif 28 <= avg_gap <= 32:  # Approximately monthly (30 days)
        return "monthly"
    else:
        return "unknown"


def build_signals_response(db: Session, user_id: str, window_days: int, feature: UserFeature) -> Dict[str, Any]:
    """
    Build signals response for a specific window.
    
    Args:
        db: Database session
        user_id: User ID
        window_days: Time window in days
        feature: UserFeature object
    
    Returns:
        Dictionary with subscriptions, savings, credit, and income signals
    """
    # Get recurring merchant names
    recurring_merchants = get_recurring_merchant_names(db, user_id, window_days)
    
    # Get credit card details
    credit_cards = get_credit_card_details(db, user_id)
    
    # Calculate income frequency
    income_frequency = calculate_income_frequency(db, user_id, window_days)
    
    return {
        "subscriptions": {
            "recurring_merchants": recurring_merchants,
            "monthly_spend": round(feature.monthly_recurring_spend, 2),
            "spend_share": round(feature.subscription_spend_share, 4)
        },
        "savings": {
            "net_inflow": round(feature.net_savings_inflow, 2),
            "growth_rate": round(feature.savings_growth_rate, 4),
            "emergency_fund_months": round(feature.emergency_fund_months, 2)
        },
        "credit": {
            "cards": credit_cards
        },
        "income": {
            "payroll_detected": feature.payroll_detected,
            "avg_monthly": round(feature.avg_monthly_income, 2),
            "frequency": income_frequency
        }
    }


@router.get("/users/{user_id}/signals")
async def get_user_signals(
    user_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed signals for a user for operator view.
    
    Returns signals for both 30d and 180d windows, including:
    - Subscriptions: recurring merchants, monthly spend, spend share
    - Savings: net inflow, growth rate, emergency fund months
    - Credit: credit card details with utilization
    - Income: payroll detection, average monthly income, frequency
    
    Args:
        user_id: User ID to fetch signals for
        db: Database session
    
    Returns:
        Dictionary with user info, 30d_signals, 180d_signals, and personas
    """
    try:
        # Query user
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found")
        
        # Query UserFeature records for both windows
        feature_30d = db.query(UserFeature).filter(
            and_(
                UserFeature.user_id == user_id,
                UserFeature.window_days == 30
            )
        ).first()
        
        feature_180d = db.query(UserFeature).filter(
            and_(
                UserFeature.user_id == user_id,
                UserFeature.window_days == 180
            )
        ).first()
        
        if not feature_30d:
            raise HTTPException(
                status_code=400,
                detail=f"Features not computed for user '{user_id}' for 30-day window"
            )
        
        if not feature_180d:
            raise HTTPException(
                status_code=400,
                detail=f"Features not computed for user '{user_id}' for 180-day window"
            )
        
        # Query Persona records
        persona_30d = db.query(Persona).filter(
            and_(
                Persona.user_id == user_id,
                Persona.window_days == 30
            )
        ).first()
        
        persona_180d = db.query(Persona).filter(
            and_(
                Persona.user_id == user_id,
                Persona.window_days == 180
            )
        ).first()
        
        # Build signals for both windows
        signals_30d = build_signals_response(db, user_id, 30, feature_30d)
        signals_180d = build_signals_response(db, user_id, 180, feature_180d)
        
        # Build response
        response = {
            "user_id": user.user_id,
            "user_name": user.full_name,
            "consent_status": user.consent_status,
            "30d_signals": signals_30d,
            "180d_signals": signals_180d,
            "persona_30d": persona_30d.persona_type if persona_30d else None,
            "persona_180d": persona_180d.persona_type if persona_180d else None
        }
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user signals: {str(e)}")

