"""
Operator Router

Endpoints for operator dashboard and operator-specific functionality.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any

from app.database import get_db
from app.models import User, Persona, Recommendation

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

