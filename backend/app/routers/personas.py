"""
Personas Router

Endpoints for assigning and retrieving user personas.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.models import User, Persona
from app.schemas import PersonaResponse
from app.services.persona_assignment import assign_and_save_persona

router = APIRouter(prefix="/personas", tags=["personas"])


@router.post("/{user_id}/assign", response_model=PersonaResponse)
async def assign_persona(
    user_id: str,
    window_days: int = Query(default=30, ge=1, le=365, description="Time window in days (default: 30)"),
    db: Session = Depends(get_db)
) -> PersonaResponse:
    """
    Assign persona to a user based on computed features.
    
    Args:
        user_id: User ID to assign persona for
        window_days: Time window in days (default: 30, typically 30 or 180)
        db: Database session
    
    Returns:
        PersonaResponse with assigned persona details
    
    Raises:
        404: If user not found
        400: If features not computed for this user/window
        500: If server error occurs
    """
    # Check if user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    try:
        # Assign and save persona
        persona = assign_and_save_persona(db, user_id, window_days)
        return PersonaResponse(
            persona_id=persona.persona_id,
            user_id=persona.user_id,
            window_days=persona.window_days,
            persona_type=persona.persona_type,
            confidence_score=persona.confidence_score,
            assigned_at=persona.assigned_at,
            reasoning=persona.reasoning
        )
    except ValueError as e:
        # Features not computed
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Server error
        raise HTTPException(status_code=500, detail=f"Error assigning persona: {str(e)}")


@router.get("/{user_id}", response_model=List[PersonaResponse])
async def get_personas(
    user_id: str,
    window: Optional[int] = Query(default=None, ge=1, le=365, description="Optional window filter (30 or 180)"),
    db: Session = Depends(get_db)
) -> List[PersonaResponse]:
    """
    Get persona(s) for a user.
    
    Args:
        user_id: User ID to get personas for
        window: Optional window filter (30 or 180). If not provided, returns both.
        db: Database session
    
    Returns:
        List of PersonaResponse objects
    
    Raises:
        404: If user not found
    """
    # Check if user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    # Query Persona records for user
    persona_query = db.query(Persona).filter(Persona.user_id == user_id)
    
    if window:
        persona_query = persona_query.filter(Persona.window_days == window)
    
    personas = persona_query.all()
    
    # Convert to response format
    return [
        PersonaResponse(
            persona_id=p.persona_id,
            user_id=p.user_id,
            window_days=p.window_days,
            persona_type=p.persona_type,
            confidence_score=p.confidence_score,
            assigned_at=p.assigned_at,
            reasoning=p.reasoning
        )
        for p in personas
    ]

