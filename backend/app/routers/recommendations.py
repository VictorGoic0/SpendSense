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
from app.models import User, Persona, Recommendation
from app.services.recommendation_engine import (
    build_user_context,
    validate_context,
    generate_recommendations_via_openai
)
from app.services.guardrails import (
    check_consent,
    validate_tone,
    append_disclosure
)

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

