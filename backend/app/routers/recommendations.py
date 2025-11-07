"""
Recommendations Router

Endpoints for generating AI-powered financial recommendations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Dict, Any, List, Optional, Literal
import uuid
import json
import time
import logging

from app.database import get_db
from app.models import User, Persona, Recommendation, OperatorAction
from app.schemas import RecommendationApprove, RecommendationOverride, RecommendationReject, BulkApproveRequest, BulkApproveResponse
from app.services.recommendation_engine import (
    build_user_context,
    validate_context,
    generate_recommendations_via_openai
)
from app.services.guardrails import (
    check_consent,
    validate_tone,
    append_disclosure,
    MANDATORY_DISCLOSURE
)
from datetime import datetime

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
logger = logging.getLogger(__name__)


@router.post("/generate/{user_id}")
async def generate_recommendations(
    user_id: str,
    window_days: int = Query(default=30, ge=1, le=365, description="Time window in days"),
    force_regenerate: bool = Query(default=False, description="Force regeneration even if recommendations exist"),
    db: Session = Depends(get_db),
    response: Response = None
) -> Dict[str, Any]:
    """
    Generate AI-powered financial recommendations for a user.
    
    This endpoint:
    1. Validates user exists and has consent
    2. Checks for existing recommendations (unless force_regenerate=True)
    3. Gets user persona for the window
    4. Builds comprehensive user context
    5. Calls OpenAI to generate recommendations
    6. Validates tone for each recommendation
    7. Saves all recommendations to database (status='pending_approval')
    8. Returns generated recommendations
    
    Args:
        user_id: User ID to generate recommendations for
        window_days: Time window in days (default: 30)
        force_regenerate: If True, regenerate even if recommendations exist
        db: Database session
    
    Returns:
        Dictionary with:
        - user_id: User ID
        - persona: Persona type
        - recommendations: List of recommendation objects
        - generation_time_ms: Total generation time in milliseconds
    
    Raises:
        403: User has not granted consent
        404: User not found
        400: No persona assigned or invalid request
        500: Server error (OpenAI failure, database error)
    """
    start_time = time.time()
    
    try:
        # ========================================================================
        # Validation
        # ========================================================================
        
        # Check if user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found")
        
        # Check consent using guardrails.check_consent()
        if not check_consent(db, user_id):
            raise HTTPException(
                status_code=403,
                detail=f"User '{user_id}' has not granted consent for recommendations"
            )
        
        # ========================================================================
        # Check Existing Recommendations
        # ========================================================================
        
        # Query existing recommendations for user + window
        existing_recommendations = db.query(Recommendation).filter(
            and_(
                Recommendation.user_id == user_id,
                Recommendation.window_days == window_days,
                Recommendation.status == 'pending_approval'
            )
        ).all()
        
        # If recommendations exist and not force_regenerate, return existing
        if existing_recommendations and not force_regenerate:
            logger.info(f"Returning {len(existing_recommendations)} existing recommendations for user {user_id}, window {window_days}d")
            
            recommendations_list = []
            for rec in existing_recommendations:
                recommendations_list.append({
                    "recommendation_id": rec.recommendation_id,
                    "title": rec.title,
                    "content": rec.content,
                    "rationale": rec.rationale,
                    "status": rec.status,
                    "persona_type": rec.persona_type,
                    "generation_time_ms": rec.generation_time_ms,
                    "generated_at": rec.generated_at.isoformat() if rec.generated_at else None,
                    "metadata_json": rec.metadata_json
                })
            
            # Get persona for response
            persona = db.query(Persona).filter(
                and_(
                    Persona.user_id == user_id,
                    Persona.window_days == window_days
                )
            ).first()
            
            # Return 200 for cached results
            if response is not None:
                response.status_code = status.HTTP_200_OK
            
            return {
                "user_id": user_id,
                "persona": persona.persona_type if persona else None,
                "recommendations": recommendations_list,
                "generation_time_ms": 0,  # Not regenerated
                "cached": True
            }
        
        # ========================================================================
        # Get Context
        # ========================================================================
        
        # Get user persona for window
        persona = db.query(Persona).filter(
            and_(
                Persona.user_id == user_id,
                Persona.window_days == window_days
            )
        ).first()
        
        if not persona:
            raise HTTPException(
                status_code=400,
                detail=f"No persona assigned for user '{user_id}' with window {window_days}d. Please assign a persona first."
            )
        
        persona_type = persona.persona_type
        
        # Build user context using build_user_context()
        logger.info(f"Building context for user {user_id}, window {window_days}d, persona {persona_type}")
        user_context = build_user_context(db, user_id, window_days)
        
        # Validate context
        if not validate_context(user_context):
            raise HTTPException(
                status_code=400,
                detail="Invalid user context - required fields missing or incorrect data types"
            )
        
        # ========================================================================
        # Call OpenAI
        # ========================================================================
        
        # Call generate_recommendations_via_openai() with persona and context
        logger.info(f"Generating recommendations via OpenAI for user {user_id}, persona {persona_type}")
        generation_start = time.time()
        
        try:
            generated_recommendations = generate_recommendations_via_openai(persona_type, user_context)
        except Exception as e:
            logger.error(f"OpenAI call failed for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate recommendations: {str(e)}"
            )
        
        generation_end = time.time()
        generation_time_ms = int((generation_end - generation_start) * 1000)
        
        if not generated_recommendations:
            raise HTTPException(
                status_code=500,
                detail="OpenAI returned no valid recommendations"
            )
        
        logger.info(f"Generated {len(generated_recommendations)} recommendations for user {user_id} in {generation_time_ms}ms")
        
        # ========================================================================
        # Validate Tone
        # ========================================================================
        
        # For each generated recommendation, validate tone
        recommendations_to_save = []
        
        for rec_dict in generated_recommendations:
            # Extract content field
            content = rec_dict.get("content", "")
            
            # Call guardrails.validate_tone() → returns {"is_valid": bool, "validation_warnings": [...]}
            tone_result = validate_tone(content)
            validation_warnings = tone_result.get("validation_warnings", [])
            
            # Store validation_warnings in recommendation metadata
            # Initialize metadata dict if not present
            metadata = rec_dict.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
            
            # IMPORTANT: Strip token_usage and estimated_cost_usd from metadata before saving
            # These are for logging/review only, not stored in database
            metadata.pop("token_usage", None)
            metadata.pop("estimated_cost_usd", None)
            
            # Set validation_warnings in metadata
            metadata["validation_warnings"] = validation_warnings
            
            # Log warnings if any (for monitoring)
            if validation_warnings:
                logger.warning(
                    f"Recommendation for user {user_id} has {len(validation_warnings)} tone validation warning(s): "
                    f"{[w.get('message', '') for w in validation_warnings]}"
                )
            
            # IMPORTANT: Do NOT skip recommendations with warnings - persist all for operator review
            recommendations_to_save.append({
                "title": rec_dict.get("title"),
                "content": rec_dict.get("content"),
                "rationale": rec_dict.get("rationale"),
                "metadata": metadata,
                "generation_time_ms": rec_dict.get("generation_time_ms", generation_time_ms)
            })
        
        # ========================================================================
        # Save to Database
        # ========================================================================
        
        # For each recommendation (including those with warnings):
        recommendation_objects = []
        current_time = time.time()
        
        for rec_data in recommendations_to_save:
            # Generate recommendation_id (rec_{uuid})
            recommendation_id = f"rec_{uuid.uuid4().hex[:16]}"
            
            # Append mandatory disclosure to content
            content_with_disclosure = append_disclosure(rec_data["content"])
            
            # Serialize metadata dict (includes validation_warnings) to JSON string
            metadata_json = json.dumps(rec_data["metadata"])
            
            # Create Recommendation model instance
            recommendation = Recommendation(
                recommendation_id=recommendation_id,
                user_id=user_id,
                persona_type=persona_type,
                window_days=window_days,
                content_type="education",  # All AI-generated recommendations are education type
                title=rec_data["title"],
                content=content_with_disclosure,
                rationale=rec_data["rationale"],
                status="pending_approval",  # All recommendations start pending, regardless of warnings
                generation_time_ms=rec_data["generation_time_ms"],
                metadata_json=metadata_json
            )
            
            recommendation_objects.append(recommendation)
        
        # Bulk insert recommendations
        db.add_all(recommendation_objects)
        
        # Commit transaction
        db.commit()
        
        # Refresh objects to get generated_at timestamps
        for rec in recommendation_objects:
            db.refresh(rec)
        
        logger.info(f"Saved {len(recommendation_objects)} recommendations to database for user {user_id}")
        
        # ========================================================================
        # Response
        # ========================================================================
        
        # Query newly created recommendations
        # Convert to schema objects
        recommendations_list = []
        for rec in recommendation_objects:
            recommendations_list.append({
                "recommendation_id": rec.recommendation_id,
                "title": rec.title,
                "content": rec.content,
                "rationale": rec.rationale,
                "status": rec.status,
                "persona_type": rec.persona_type,
                "window_days": rec.window_days,
                "content_type": rec.content_type,
                "generation_time_ms": rec.generation_time_ms,
                "generated_at": rec.generated_at.isoformat() if rec.generated_at else None,
                "metadata_json": rec.metadata_json
            })
        
        # Calculate total generation time
        end_time = time.time()
        total_generation_time_ms = int((end_time - start_time) * 1000)
        
        # Return 201 for newly created recommendations
        if response is not None:
            response.status_code = status.HTTP_201_CREATED
        
        # Return JSON response
        return {
            "user_id": user_id,
            "persona": persona_type,
            "recommendations": recommendations_list,
            "generation_time_ms": total_generation_time_ms
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Rollback database transaction on error
        db.rollback()
        logger.error(f"Error generating recommendations for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )


@router.get("/{user_id}")
async def get_recommendations(
    user_id: str,
    status: Optional[Literal["pending_approval", "approved", "overridden", "rejected"]] = Query(
        default=None,
        description="Filter by recommendation status"
    ),
    window_days: Optional[int] = Query(
        default=None,
        ge=1,
        le=365,
        description="Filter by window_days (default: return all)"
    ),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get recommendations for a user.
    
    This endpoint:
    1. Validates user exists
    2. Queries recommendations with optional filters (status, window_days)
    3. Returns recommendations ordered by generated_at (newest first)
    4. Limits results to 50 recommendations
    
    Note: Access control will be implemented when authentication is added.
    
    Args:
        user_id: User ID to get recommendations for
        status: Optional status filter (pending_approval, approved, overridden, rejected)
        window_days: Optional window_days filter (default: return all)
        db: Database session
    
    Returns:
        Dictionary with:
        - recommendations: List of recommendation objects
        - total: Total count of recommendations
    
    Raises:
        404: User not found
        500: Server error (database error)
    """
    try:
        # ========================================================================
        # Validation
        # ========================================================================
        
        # Check if user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found")
        
        # ========================================================================
        # Query Recommendations
        # ========================================================================
        # TODO: Future authentication will enforce access control properly
        # For now, return all recommendations when no status filter is provided
        
        # Build base query
        query = db.query(Recommendation).filter(Recommendation.user_id == user_id)
        
        # Apply status filter if provided
        if status:
            query = query.filter(Recommendation.status == status)
        
        # Apply window_days filter if provided
        if window_days is not None:
            query = query.filter(Recommendation.window_days == window_days)
        
        # Order by generated_at descending (newest first)
        query = query.order_by(Recommendation.generated_at.desc())
        
        # Limit to 50 recommendations (pagination could be added later)
        recommendations = query.limit(50).all()
        
        # Get total count before limiting (for pagination info)
        total_query = db.query(Recommendation).filter(Recommendation.user_id == user_id)
        if status:
            total_query = total_query.filter(Recommendation.status == status)
        if window_days is not None:
            total_query = total_query.filter(Recommendation.window_days == window_days)
        total_count = total_query.count()
        
        logger.info(
            f"Retrieved {len(recommendations)} recommendations for user {user_id} "
            f"(status={status}, window_days={window_days}, total={total_count})"
        )
        
        # ========================================================================
        # Response Formatting
        # ========================================================================
        
        # Convert recommendation models to schema objects
        recommendations_list = []
        for rec in recommendations:
            recommendations_list.append({
                "recommendation_id": rec.recommendation_id,
                "title": rec.title,
                "content": rec.content,
                "rationale": rec.rationale,
                "status": rec.status,
                "persona_type": rec.persona_type,
                "generated_at": rec.generated_at.isoformat() if rec.generated_at else None,
                "approved_by": rec.approved_by,
                "approved_at": rec.approved_at.isoformat() if rec.approved_at else None,
            })
        
        # Return JSON response with recommendations list and total count
        return {
            "recommendations": recommendations_list,
            "total": total_count
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Handle database errors
        logger.error(f"Error getting recommendations for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )


@router.post("/{recommendation_id}/approve")
async def approve_recommendation(
    recommendation_id: str,
    request: RecommendationApprove,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Approve a recommendation.
    
    This endpoint:
    1. Validates recommendation exists
    2. Validates recommendation is in pending_approval status
    3. Updates recommendation status to 'approved'
    4. Sets approved_by and approved_at
    5. Creates OperatorAction record for audit trail
    6. Returns updated recommendation
    
    Args:
        recommendation_id: Recommendation ID to approve
        request: ApproveRequest with operator_id and optional notes
        db: Database session
    
    Returns:
        Dictionary with updated recommendation object
    
    Raises:
        404: Recommendation not found
        400: Recommendation already approved or rejected
        500: Server error (database error)
    """
    try:
        # ========================================================================
        # Validation
        # ========================================================================
        
        # Query Recommendation by recommendation_id
        recommendation = db.query(Recommendation).filter(
            Recommendation.recommendation_id == recommendation_id
        ).first()
        
        if not recommendation:
            logger.warning(f"Recommendation not found: {recommendation_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Recommendation with ID '{recommendation_id}' not found"
            )
        
        # If already approved → 400 error with message
        if recommendation.status == 'approved':
            logger.warning(
                f"Attempt to approve already approved recommendation: {recommendation_id}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Recommendation '{recommendation_id}' is already approved"
            )
        
        # If status is 'rejected' → 400 error (can't approve rejected rec)
        if recommendation.status == 'rejected':
            logger.warning(
                f"Attempt to approve rejected recommendation: {recommendation_id}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Cannot approve recommendation '{recommendation_id}' - it has been rejected"
            )
        
        # ========================================================================
        # Update Recommendation
        # ========================================================================
        
        # Update recommendation:
        # - Set status='approved'
        # - Set approved_by=operator_id
        # - Set approved_at=current timestamp
        recommendation.status = 'approved'
        recommendation.approved_by = request.operator_id
        recommendation.approved_at = datetime.utcnow()
        
        # Commit transaction
        db.commit()
        
        # Refresh to get updated timestamp
        db.refresh(recommendation)
        
        logger.info(
            f"Approved recommendation {recommendation_id} by operator {request.operator_id}"
        )
        
        # ========================================================================
        # Log Operator Action
        # ========================================================================
        
        # Create OperatorAction record:
        # - operator_id
        # - action_type='approve'
        # - recommendation_id
        # - user_id (from recommendation)
        # - reason=notes (if provided)
        # - timestamp=now
        operator_action = OperatorAction(
            operator_id=request.operator_id,
            action_type='approve',
            recommendation_id=recommendation_id,
            user_id=recommendation.user_id,
            reason=request.notes,
            timestamp=datetime.utcnow()
        )
        
        db.add(operator_action)
        
        # Commit transaction
        db.commit()
        
        logger.info(
            f"Logged operator action: approve for recommendation {recommendation_id}"
        )
        
        # ========================================================================
        # Response
        # ========================================================================
        
        # Query updated recommendation (already have it, but format response)
        # Return recommendation with updated status
        return {
            "recommendation_id": recommendation.recommendation_id,
            "title": recommendation.title,
            "content": recommendation.content,
            "rationale": recommendation.rationale,
            "status": recommendation.status,
            "persona_type": recommendation.persona_type,
            "generated_at": recommendation.generated_at.isoformat() if recommendation.generated_at else None,
            "approved_by": recommendation.approved_by,
            "approved_at": recommendation.approved_at.isoformat() if recommendation.approved_at else None,
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Rollback database transaction on error
        db.rollback()
        logger.error(
            f"Error approving recommendation {recommendation_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )


@router.post("/{recommendation_id}/override")
async def override_recommendation(
    recommendation_id: str,
    request: RecommendationOverride,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Override a recommendation with new content.
    
    This endpoint:
    1. Validates recommendation exists
    2. Validates at least one of new_title or new_content provided
    3. Stores original content in original_content field
    4. Updates recommendation with new content
    5. Validates tone of new content
    6. Creates OperatorAction record for audit trail
    7. Returns updated recommendation
    
    Args:
        recommendation_id: Recommendation ID to override
        request: OverrideRequest with operator_id, optional new_title, optional new_content, required reason
        db: Database session
    
    Returns:
        Dictionary with updated recommendation object
    
    Raises:
        404: Recommendation not found
        400: Neither new_title nor new_content provided, or tone validation fails
        500: Server error (database error)
    """
    try:
        # ========================================================================
        # Validation
        # ========================================================================
        
        # Query Recommendation by ID
        recommendation = db.query(Recommendation).filter(
            Recommendation.recommendation_id == recommendation_id
        ).first()
        
        if not recommendation:
            logger.warning(f"Recommendation not found: {recommendation_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Recommendation with ID '{recommendation_id}' not found"
            )
        
        # Validate at least one of new_title or new_content provided → 400 if neither
        if not request.new_title and not request.new_content:
            logger.warning(
                f"Override request for {recommendation_id} provided neither new_title nor new_content"
            )
            raise HTTPException(
                status_code=400,
                detail="At least one of 'new_title' or 'new_content' must be provided"
            )
        
        # ========================================================================
        # Store Original Content
        # ========================================================================
        
        # Create original_content dict with:
        # - original_title
        # - original_content
        # - overridden_at timestamp
        original_content_dict = {
            "original_title": recommendation.title,
            "original_content": recommendation.content,
            "overridden_at": datetime.utcnow().isoformat()
        }
        
        # Convert to JSON string
        original_content_json = json.dumps(original_content_dict)
        
        # Store in recommendation.original_content field
        recommendation.original_content = original_content_json
        
        # ========================================================================
        # Update Recommendation
        # ========================================================================
        
        # Update recommendation:
        # - Set status='overridden'
        # - Update title if new_title provided
        # - Update content if new_content provided
        # - Append disclosure to new content if modified
        # - Set override_reason=reason
        # - Validate new content tone if modified
        recommendation.status = 'overridden'
        recommendation.override_reason = request.reason
        
        if request.new_title:
            recommendation.title = request.new_title
        
        if request.new_content:
            # Validate new content tone if modified
            tone_result = validate_tone(request.new_content)
            
            # If tone validation fails → 400 error
            if not tone_result.get("is_valid", False):
                validation_warnings = tone_result.get("validation_warnings", [])
                critical_warnings = [w for w in validation_warnings if w.get("severity") == "critical"]
                
                if critical_warnings:
                    logger.warning(
                        f"Tone validation failed for override of recommendation {recommendation_id}: "
                        f"{[w.get('message') for w in critical_warnings]}"
                    )
                    raise HTTPException(
                        status_code=400,
                        detail=f"New content failed tone validation: {critical_warnings[0].get('message', 'Contains forbidden phrases')}"
                    )
            
            # Append disclosure to new content if modified
            content_with_disclosure = append_disclosure(request.new_content)
            recommendation.content = content_with_disclosure
        else:
            # If only title changed, ensure existing content still has disclosure
            # (disclosure should already be there from generation, but check to be safe)
            if MANDATORY_DISCLOSURE not in recommendation.content:
                recommendation.content = append_disclosure(recommendation.content)
        
        # Commit transaction
        db.commit()
        
        # Refresh to get updated data
        db.refresh(recommendation)
        
        logger.info(
            f"Overridden recommendation {recommendation_id} by operator {request.operator_id}"
        )
        
        # ========================================================================
        # Log Operator Action
        # ========================================================================
        
        # Create OperatorAction record with action_type='override'
        # Include reason in operator action
        operator_action = OperatorAction(
            operator_id=request.operator_id,
            action_type='override',
            recommendation_id=recommendation_id,
            user_id=recommendation.user_id,
            reason=request.reason,
            timestamp=datetime.utcnow()
        )
        
        db.add(operator_action)
        
        # Commit transaction
        db.commit()
        
        logger.info(
            f"Logged operator action: override for recommendation {recommendation_id}"
        )
        
        # ========================================================================
        # Response
        # ========================================================================
        
        # Return updated recommendation with:
        # - New content
        # - original_content field
        # - override_reason
        return {
            "recommendation_id": recommendation.recommendation_id,
            "title": recommendation.title,
            "content": recommendation.content,
            "rationale": recommendation.rationale,
            "status": recommendation.status,
            "persona_type": recommendation.persona_type,
            "generated_at": recommendation.generated_at.isoformat() if recommendation.generated_at else None,
            "original_content": recommendation.original_content,
            "override_reason": recommendation.override_reason,
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Rollback database transaction on error
        db.rollback()
        logger.error(
            f"Error overriding recommendation {recommendation_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )


@router.post("/{recommendation_id}/reject")
async def reject_recommendation(
    recommendation_id: str,
    request: RecommendationReject,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reject a recommendation.
    
    This endpoint:
    1. Validates recommendation exists
    2. Validates recommendation is not already approved (can't reject approved recs)
    3. Updates recommendation status to 'rejected'
    4. Sets metadata with rejection reason
    5. Creates OperatorAction record for audit trail
    6. Returns updated recommendation
    
    Args:
        recommendation_id: Recommendation ID to reject
        request: RejectRequest with operator_id and required reason
        db: Database session
    
    Returns:
        Dictionary with updated recommendation object
    
    Raises:
        404: Recommendation not found
        400: Recommendation already approved and visible to user
        500: Server error (database error)
    """
    try:
        # ========================================================================
        # Validation
        # ========================================================================
        
        # Query Recommendation by ID
        recommendation = db.query(Recommendation).filter(
            Recommendation.recommendation_id == recommendation_id
        ).first()
        
        if not recommendation:
            logger.warning(f"Recommendation not found: {recommendation_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Recommendation with ID '{recommendation_id}' not found"
            )
        
        # If already approved and visible to user → 400 (shouldn't reject approved recs)
        if recommendation.status == 'approved':
            logger.warning(
                f"Attempt to reject already approved recommendation: {recommendation_id}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Cannot reject recommendation '{recommendation_id}' - it has already been approved and is visible to the user"
            )
        
        # ========================================================================
        # Update Recommendation
        # ========================================================================
        
        # Update status='rejected'
        recommendation.status = 'rejected'
        
        # Set metadata with rejection reason
        # Parse existing metadata if present, otherwise create new dict
        if recommendation.metadata_json:
            try:
                metadata = json.loads(recommendation.metadata_json)
            except (json.JSONDecodeError, TypeError):
                metadata = {}
        else:
            metadata = {}
        
        # Add rejection reason to metadata
        metadata["rejection_reason"] = request.reason
        metadata["rejected_by"] = request.operator_id
        metadata["rejected_at"] = datetime.utcnow().isoformat()
        
        # Update metadata_json field
        recommendation.metadata_json = json.dumps(metadata)
        
        # Commit transaction
        db.commit()
        
        # Refresh to get updated data
        db.refresh(recommendation)
        
        logger.info(
            f"Rejected recommendation {recommendation_id} by operator {request.operator_id}"
        )
        
        # ========================================================================
        # Log Reject Action
        # ========================================================================
        
        # Create OperatorAction record with action_type='reject'
        # Include reason
        operator_action = OperatorAction(
            operator_id=request.operator_id,
            action_type='reject',
            recommendation_id=recommendation_id,
            user_id=recommendation.user_id,
            reason=request.reason,
            timestamp=datetime.utcnow()
        )
        
        db.add(operator_action)
        
        # Commit transaction
        db.commit()
        
        logger.info(
            f"Logged operator action: reject for recommendation {recommendation_id}"
        )
        
        # ========================================================================
        # Response
        # ========================================================================
        
        # Return updated recommendation
        return {
            "recommendation_id": recommendation.recommendation_id,
            "title": recommendation.title,
            "content": recommendation.content,
            "rationale": recommendation.rationale,
            "status": recommendation.status,
            "persona_type": recommendation.persona_type,
            "generated_at": recommendation.generated_at.isoformat() if recommendation.generated_at else None,
            "metadata_json": recommendation.metadata_json,
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Rollback database transaction on error
        db.rollback()
        logger.error(
            f"Error rejecting recommendation {recommendation_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )


@router.post("/bulk-approve", response_model=BulkApproveResponse)
async def bulk_approve_recommendations(
    request: BulkApproveRequest,
    db: Session = Depends(get_db)
) -> BulkApproveResponse:
    """
    Bulk approve multiple recommendations.
    
    This endpoint:
    1. Accepts a list of recommendation IDs
    2. Processes each recommendation individually
    3. Approves only those in 'pending_approval' status
    4. Logs operator actions for each approval
    5. Commits all changes in a single transaction
    6. Returns summary of approved and failed counts
    
    Args:
        request: BulkApproveRequest with operator_id and list of recommendation_ids
        db: Database session
    
    Returns:
        BulkApproveResponse with:
        - approved: Count of successfully approved recommendations
        - failed: Count of failed recommendations
        - errors: List of error messages for failed recommendations
    
    Raises:
        400: If all recommendations failed
        500: Server error (database error)
    """
    try:
        # ========================================================================
        # Initialize Counters
        # ========================================================================
        
        approved_count = 0
        failed_count = 0
        errors = []
        recommendations_to_update = []
        operator_actions_to_create = []
        
        logger.info(
            f"Bulk approve request from operator {request.operator_id} "
            f"for {len(request.recommendation_ids)} recommendations"
        )
        
        # ========================================================================
        # Process Each Recommendation
        # ========================================================================
        
        for recommendation_id in request.recommendation_ids:
            try:
                # Query recommendation by ID
                recommendation = db.query(Recommendation).filter(
                    Recommendation.recommendation_id == recommendation_id
                ).first()
                
                # Skip if not found
                if not recommendation:
                    failed_count += 1
                    error_msg = f"Recommendation '{recommendation_id}' not found"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                    continue
                
                # Skip if not in pending_approval status
                if recommendation.status != 'pending_approval':
                    failed_count += 1
                    error_msg = (
                        f"Recommendation '{recommendation_id}' is not in 'pending_approval' status "
                        f"(current status: '{recommendation.status}')"
                    )
                    errors.append(error_msg)
                    logger.warning(error_msg)
                    continue
                
                # Update recommendation:
                # - Set status='approved'
                # - Set approved_by=operator_id
                # - Set approved_at=current timestamp
                recommendation.status = 'approved'
                recommendation.approved_by = request.operator_id
                recommendation.approved_at = datetime.utcnow()
                
                recommendations_to_update.append(recommendation)
                
                # Create OperatorAction record
                operator_action = OperatorAction(
                    operator_id=request.operator_id,
                    action_type='approve',
                    recommendation_id=recommendation_id,
                    user_id=recommendation.user_id,
                    reason=None,  # Bulk approve doesn't include notes
                    timestamp=datetime.utcnow()
                )
                
                operator_actions_to_create.append(operator_action)
                
                approved_count += 1
                
                logger.debug(
                    f"Prepared approval for recommendation {recommendation_id} "
                    f"by operator {request.operator_id}"
                )
            
            except Exception as e:
                # Catch and log any errors per recommendation
                failed_count += 1
                error_msg = f"Error processing recommendation '{recommendation_id}': {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg, exc_info=True)
                continue
        
        # ========================================================================
        # Batch Commit
        # ========================================================================
        
        # If we have any recommendations to approve, commit them
        if recommendations_to_update:
            try:
                # Add all operator actions
                db.add_all(operator_actions_to_create)
                
                # Commit all changes in single transaction
                db.commit()
                
                logger.info(
                    f"Bulk approve completed: {approved_count} approved, {failed_count} failed"
                )
            except Exception as e:
                # Rollback on commit failure
                db.rollback()
                logger.error(f"Error committing bulk approve transaction: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to commit bulk approve transaction: {str(e)}"
                )
        
        # ========================================================================
        # Response
        # ========================================================================
        
        # Return 200 if any succeeded, 400 if all failed
        if approved_count == 0:
            logger.warning(
                f"Bulk approve failed for all {len(request.recommendation_ids)} recommendations"
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "All recommendations failed to approve",
                    "approved": approved_count,
                    "failed": failed_count,
                    "errors": errors
                }
            )
        
        # Return BulkApproveResponse
        return BulkApproveResponse(
            approved=approved_count,
            failed=failed_count,
            errors=errors
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Rollback database transaction on error
        db.rollback()
        logger.error(f"Error in bulk approve: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )

