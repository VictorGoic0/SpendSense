"""
Consent Router

Endpoints for managing user consent for personalized recommendations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime
import logging

from app.database import get_db
from app.models import User, ConsentLog
from app.schemas import ConsentRequest, ConsentResponse, ConsentHistoryItem

router = APIRouter(prefix="/consent", tags=["consent"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=ConsentResponse)
async def update_consent(
    request: ConsentRequest,
    db: Session = Depends(get_db)
) -> ConsentResponse:
    """
    Update user consent status (grant or revoke).
    
    Args:
        request: Consent request with user_id and action
        db: Database session
    
    Returns:
        ConsentResponse with updated consent status
    """
    try:
        # Get user
        user = db.query(User).filter(User.user_id == request.user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID '{request.user_id}' not found")
        
        # Note: IP address and user agent tracking can be added later if needed
        # For now, we'll log without them
        ip_address = None
        user_agent = None
        
        # Determine action string for log
        action_str = "granted" if request.action == "grant" else "revoked"
        
        # Update consent based on action
        now = datetime.utcnow()
        
        if request.action == "grant":
            if user.consent_status:
                logger.info(f"User {request.user_id} already has consent granted")
            else:
                user.consent_status = True
                user.consent_granted_at = now
                user.consent_revoked_at = None
                logger.info(f"User {request.user_id} granted consent")
        elif request.action == "revoke":
            if not user.consent_status:
                logger.info(f"User {request.user_id} already has consent revoked")
            else:
                user.consent_status = False
                user.consent_revoked_at = now
                logger.info(f"User {request.user_id} revoked consent")
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action '{request.action}'. Must be 'grant' or 'revoke'"
            )
        
        # Create consent log entry
        consent_log = ConsentLog(
            user_id=request.user_id,
            action=action_str,
            timestamp=now,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(consent_log)
        
        # Commit changes
        db.commit()
        db.refresh(user)
        
        # Build response (history will be empty for update endpoint)
        return ConsentResponse(
            user_id=user.user_id,
            consent_status=user.consent_status,
            consent_granted_at=user.consent_granted_at.isoformat() if user.consent_granted_at else None,
            consent_revoked_at=user.consent_revoked_at.isoformat() if user.consent_revoked_at else None,
            history=[]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating consent for user {request.user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating consent: {str(e)}")


@router.get("/{user_id}", response_model=ConsentResponse)
async def get_consent(
    user_id: str,
    db: Session = Depends(get_db)
) -> ConsentResponse:
    """
    Get user consent status and history.
    
    Args:
        user_id: User ID to fetch consent for
        db: Database session
    
    Returns:
        ConsentResponse with consent status and history
    """
    try:
        # Get user
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found")
        
        # Get consent history
        consent_logs = db.query(ConsentLog).filter(
            ConsentLog.user_id == user_id
        ).order_by(ConsentLog.timestamp.desc()).all()
        
        # Build history list
        history = [
            ConsentHistoryItem(
                action=log.action,
                timestamp=log.timestamp.isoformat() if log.timestamp else None
            )
            for log in consent_logs
        ]
        
        # Build response
        response = ConsentResponse(
            user_id=user.user_id,
            consent_status=user.consent_status,
            consent_granted_at=user.consent_granted_at.isoformat() if user.consent_granted_at else None,
            consent_revoked_at=user.consent_revoked_at.isoformat() if user.consent_revoked_at else None,
            history=history
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching consent for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching consent: {str(e)}")

