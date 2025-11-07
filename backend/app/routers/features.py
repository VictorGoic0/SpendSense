"""
Features Router

Endpoints for computing and retrieving user behavioral features.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.models import User
from app.services.feature_detection import compute_all_features

router = APIRouter(prefix="/features", tags=["features"])


@router.post("/compute/{user_id}")
async def compute_features(
    user_id: str,
    window_days: int = Query(default=30, ge=1, le=365, description="Time window in days"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Compute all behavioral features for a user.
    
    Args:
        user_id: User ID to compute features for
        window_days: Time window in days (default: 30, max: 365)
        db: Database session
    
    Returns:
        Dictionary with all computed features
    
    Raises:
        404: If user not found
    """
    # Check if user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    # Compute features
    features = compute_all_features(db, user_id, window_days)
    
    return {
        "user_id": user_id,
        "window_days": window_days,
        "features": features
    }

