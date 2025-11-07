"""
Profile Router

Endpoints for retrieving user profiles with features and personas.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List

from app.database import get_db
from app.models import User, UserFeature, Persona
from app.schemas import UserFeatureResponse, PersonaResponse

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/{user_id}")
async def get_user_profile(
    user_id: str,
    window: Optional[int] = Query(default=None, ge=1, le=365, description="Optional window filter (30 or 180)"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get user profile with features and personas.
    
    Args:
        user_id: User ID to get profile for
        window: Optional window filter (30 or 180). If not provided, returns both.
        db: Database session
    
    Returns:
        Dictionary with user info, features (30d and/or 180d), and personas
    
    Raises:
        404: If user not found
    """
    # Check if user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    # Query UserFeature records for user
    feature_query = db.query(UserFeature).filter(UserFeature.user_id == user_id)
    
    if window:
        feature_query = feature_query.filter(UserFeature.window_days == window)
    
    user_features = feature_query.all()
    
    # Query Persona records for user
    persona_query = db.query(Persona).filter(Persona.user_id == user_id)
    
    if window:
        persona_query = persona_query.filter(Persona.window_days == window)
    
    personas = persona_query.all()
    
    # Convert features to dict format
    features_dict = {}
    for feature in user_features:
        features_dict[f"{feature.window_days}d"] = {
            "recurring_merchants": feature.recurring_merchants,
            "monthly_recurring_spend": feature.monthly_recurring_spend,
            "subscription_spend_share": feature.subscription_spend_share,
            "net_savings_inflow": feature.net_savings_inflow,
            "savings_growth_rate": feature.savings_growth_rate,
            "emergency_fund_months": feature.emergency_fund_months,
            "avg_utilization": feature.avg_utilization,
            "max_utilization": feature.max_utilization,
            "utilization_30_flag": feature.utilization_30_flag,
            "utilization_50_flag": feature.utilization_50_flag,
            "utilization_80_flag": feature.utilization_80_flag,
            "minimum_payment_only_flag": feature.minimum_payment_only_flag,
            "interest_charges_present": feature.interest_charges_present,
            "any_overdue": feature.any_overdue,
            "payroll_detected": feature.payroll_detected,
            "median_pay_gap_days": feature.median_pay_gap_days,
            "income_variability": feature.income_variability,
            "cash_flow_buffer_months": feature.cash_flow_buffer_months,
            "avg_monthly_income": feature.avg_monthly_income,
            "investment_account_detected": feature.investment_account_detected,
            "computed_at": feature.computed_at.isoformat() if feature.computed_at else None
        }
    
    # Convert personas to dict format
    personas_list = []
    for persona in personas:
        personas_list.append({
            "persona_type": persona.persona_type,
            "window_days": persona.window_days,
            "confidence_score": persona.confidence_score,
            "assigned_at": persona.assigned_at.isoformat() if persona.assigned_at else None,
            "reasoning": persona.reasoning
        })
    
    return {
        "user_id": user.user_id,
        "full_name": user.full_name,
        "email": user.email,
        "consent_status": user.consent_status,
        "features": features_dict,
        "personas": personas_list
    }

