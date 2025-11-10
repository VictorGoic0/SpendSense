"""
Users Router

Endpoints for retrieving user lists with pagination and filtering.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, Optional, List

from app.database import get_db
from app.models import User, Persona
from app.schemas import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", include_in_schema=False)
@router.get("/")
async def get_users(
    limit: int = Query(default=25, ge=1, le=100, description="Number of users to return"),
    offset: int = Query(default=0, ge=0, description="Number of users to skip"),
    user_type: Optional[str] = Query(default=None, description="Filter by user type (customer or operator)"),
    consent_status: Optional[bool] = Query(default=None, description="Filter by consent status"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get list of users with pagination and filtering.
    
    Args:
        limit: Maximum number of users to return (1-100)
        offset: Number of users to skip for pagination
        user_type: Optional filter by user type
        consent_status: Optional filter by consent status
        db: Database session
    
    Returns:
        Dictionary with users list, total count, limit, and offset
    """
    try:
        # Build query with filters
        query = db.query(User)
        
        if user_type:
            query = query.filter(User.user_type == user_type)
        
        if consent_status is not None:
            query = query.filter(User.consent_status == consent_status)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        users = query.offset(offset).limit(limit).all()
        
        # Query personas for 30d window for all users
        user_ids = [user.user_id for user in users]
        personas_30d = {}
        if user_ids:
            persona_query = db.query(Persona).filter(
                Persona.user_id.in_(user_ids),
                Persona.window_days == 30
            )
            for persona in persona_query.all():
                personas_30d[persona.user_id] = {
                    "persona_type": persona.persona_type,
                    "confidence_score": persona.confidence_score,
                    "assigned_at": persona.assigned_at.isoformat() if persona.assigned_at else None,
                    "window_days": persona.window_days
                }
        
        # Build response with personas
        users_list = []
        for user in users:
            user_dict = {
                "user_id": user.user_id,
                "full_name": user.full_name,
                "email": user.email,
                "user_type": user.user_type,
                "consent_status": user.consent_status,
                "consent_granted_at": user.consent_granted_at.isoformat() if user.consent_granted_at else None,
                "consent_revoked_at": user.consent_revoked_at.isoformat() if user.consent_revoked_at else None,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
            
            # Add persona if available
            if user.user_id in personas_30d:
                user_dict["personas"] = [personas_30d[user.user_id]]
            else:
                user_dict["personas"] = []
            
            users_list.append(user_dict)
        
        return {
            "users": users_list,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a single user by ID with personas for both 30d and 180d windows.
    
    Args:
        user_id: User ID to fetch
        db: Database session
    
    Returns:
        Dictionary with user data and personas
    """
    try:
        # Query user by ID
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found")
        
        # Query personas for both windows
        personas = db.query(Persona).filter(
            Persona.user_id == user_id
        ).all()
        
        # Build personas list
        personas_list = []
        for persona in personas:
            personas_list.append({
                "persona_type": persona.persona_type,
                "confidence_score": persona.confidence_score,
                "assigned_at": persona.assigned_at.isoformat() if persona.assigned_at else None,
                "window_days": persona.window_days,
                "reasoning": persona.reasoning
            })
        
        # Build response
        return {
            "user_id": user.user_id,
            "full_name": user.full_name,
            "email": user.email,
            "user_type": user.user_type,
            "consent_status": user.consent_status,
            "consent_granted_at": user.consent_granted_at.isoformat() if user.consent_granted_at else None,
            "consent_revoked_at": user.consent_revoked_at.isoformat() if user.consent_revoked_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "personas": personas_list
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")

