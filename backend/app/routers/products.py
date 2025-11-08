"""
Products Router

Endpoints for managing product catalog (CRUD operations).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Dict, Any, List, Optional
import json
import uuid
import logging
from datetime import datetime

from app.database import get_db
from app.models import ProductOffer
from app.schemas import ProductBase, ProductResponse

router = APIRouter(prefix="/products", tags=["products"])
logger = logging.getLogger(__name__)


def _parse_json_fields(product: ProductOffer) -> Dict[str, Any]:
    """Parse JSON fields from ProductOffer model to dict"""
    result = {
        "product_id": product.product_id,
        "product_name": product.product_name,
        "product_type": product.product_type,
        "category": product.category,
        "short_description": product.short_description,
        "disclosure": product.disclosure,
        "partner_name": product.partner_name,
        "min_income": product.min_income,
        "max_credit_utilization": product.max_credit_utilization,
        "requires_no_existing_savings": product.requires_no_existing_savings,
        "requires_no_existing_investment": product.requires_no_existing_investment,
        "min_credit_score": product.min_credit_score,
        "typical_apy_or_fee": product.typical_apy_or_fee,
        "partner_link": product.partner_link,
        "commission_rate": product.commission_rate,
        "priority": product.priority,
        "active": product.active,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }
    
    # Parse JSON fields
    try:
        result["persona_targets"] = json.loads(product.persona_targets) if product.persona_targets else []
    except (json.JSONDecodeError, TypeError):
        result["persona_targets"] = []
    
    try:
        result["benefits"] = json.loads(product.benefits) if product.benefits else []
    except (json.JSONDecodeError, TypeError):
        result["benefits"] = []
    
    return result


@router.get("/", response_model=Dict[str, Any])
async def list_products(
    active_only: bool = Query(default=False, description="Filter to only active products"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    persona_type: Optional[str] = Query(default=None, description="Filter by persona type (must be in persona_targets)"),
    skip: int = Query(default=0, ge=0, description="Number of products to skip"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of products to return"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List products with optional filtering and pagination.
    
    This endpoint:
    1. Accepts query parameters for filtering (active_only, category, persona_type)
    2. Supports pagination (skip, limit)
    3. Parses JSON fields (persona_targets, benefits)
    4. Returns list of products with total count
    
    Args:
        active_only: If True, only return active products
        category: Optional category filter
        persona_type: Optional persona type filter (checks persona_targets JSON)
        skip: Number of products to skip for pagination
        limit: Maximum number of products to return (1-100)
        db: Database session
    
    Returns:
        Dictionary with:
        - products: List of product objects
        - total: Total count of products matching filters
        - skip: Number skipped
        - limit: Maximum returned
    
    Raises:
        500: Server error (database error)
    """
    try:
        # Build base query
        query = db.query(ProductOffer)
        
        # Apply filters
        if active_only:
            query = query.filter(ProductOffer.active == True)
        
        if category:
            query = query.filter(ProductOffer.category == category)
        
        if persona_type:
            # Filter products where persona_type is in persona_targets JSON array
            # SQLite JSON support: use LIKE to check if persona_type appears in JSON array
            # This is a simple approach; for production, consider using JSON functions
            query = query.filter(
                ProductOffer.persona_targets.like(f'%"{persona_type}"%')
            )
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        products = query.order_by(ProductOffer.created_at.desc()).offset(skip).limit(limit).all()
        
        # Parse JSON fields and format response
        products_list = []
        for product in products:
            products_list.append(_parse_json_fields(product))
        
        logger.info(
            f"Retrieved {len(products_list)} products "
            f"(active_only={active_only}, category={category}, persona_type={persona_type}, "
            f"skip={skip}, limit={limit}, total={total_count})"
        )
        
        return {
            "products": products_list,
            "total": total_count,
            "skip": skip,
            "limit": limit
        }
    
    except Exception as e:
        logger.error(f"Error listing products: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )


@router.get("/{product_id}", response_model=Dict[str, Any])
async def get_product(
    product_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a single product by ID.
    
    This endpoint:
    1. Queries product by product_id
    2. Parses JSON fields (persona_targets, benefits)
    3. Returns product data
    
    Args:
        product_id: Product ID to retrieve
        db: Database session
    
    Returns:
        Dictionary with product data
    
    Raises:
        404: Product not found
        500: Server error (database error)
    """
    try:
        # Query product by product_id
        product = db.query(ProductOffer).filter(
            ProductOffer.product_id == product_id
        ).first()
        
        if not product:
            logger.warning(f"Product not found: {product_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Product with ID '{product_id}' not found"
            )
        
        # Parse JSON fields and return
        product_dict = _parse_json_fields(product)
        
        logger.info(f"Retrieved product: {product_id}")
        
        return product_dict
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )


@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductBase,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new product.
    
    This endpoint:
    1. Accepts ProductBase in request body
    2. Generates product_id (prod_XXX format)
    3. Converts persona_targets and benefits to JSON strings
    4. Creates ProductOffer model instance
    5. Saves to database
    6. Returns created product
    
    Args:
        product_data: ProductBase schema with product details
        db: Database session
    
    Returns:
        Dictionary with created product data (201 Created)
    
    Raises:
        400: Invalid product data
        500: Server error (database error)
    """
    try:
        # Generate product_id (prod_XXX format)
        product_id = f"prod_{uuid.uuid4().hex[:16]}"
        
        # Convert persona_targets and benefits to JSON strings
        persona_targets_json = json.dumps(product_data.persona_targets)
        benefits_json = json.dumps(product_data.benefits)
        
        # Create ProductOffer model instance
        product = ProductOffer(
            product_id=product_id,
            product_name=product_data.product_name,
            product_type=product_data.product_type,
            category=product_data.category,
            persona_targets=persona_targets_json,
            short_description=product_data.short_description,
            benefits=benefits_json,
            disclosure=product_data.disclosure,
            partner_name=product_data.partner_name,
            min_income=product_data.min_income,
            max_credit_utilization=product_data.max_credit_utilization,
            requires_no_existing_savings=product_data.requires_no_existing_savings,
            requires_no_existing_investment=product_data.requires_no_existing_investment,
            min_credit_score=product_data.min_credit_score,
            typical_apy_or_fee=product_data.typical_apy_or_fee,
            partner_link=product_data.partner_link,
            commission_rate=product_data.commission_rate,
            priority=product_data.priority,
            active=product_data.active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to database
        db.add(product)
        db.commit()
        
        # Refresh to get generated timestamps
        db.refresh(product)
        
        logger.info(f"Created product: {product_id} ({product.product_name})")
        
        # Parse JSON fields and return
        product_dict = _parse_json_fields(product)
        
        return product_dict
    
    except Exception as e:
        # Rollback database transaction on error
        db.rollback()
        logger.error(f"Error creating product: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )


@router.put("/{product_id}", response_model=Dict[str, Any])
async def update_product(
    product_id: str,
    product_data: ProductBase,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update an existing product.
    
    This endpoint:
    1. Queries existing product by product_id
    2. Returns 404 if not found
    3. Updates fields from request body
    4. Updates updated_at timestamp
    5. Commits changes
    6. Returns updated product
    
    Args:
        product_id: Product ID to update
        product_data: ProductBase schema with updated product details
        db: Database session
    
    Returns:
        Dictionary with updated product data
    
    Raises:
        404: Product not found
        500: Server error (database error)
    """
    try:
        # Query existing product by product_id
        product = db.query(ProductOffer).filter(
            ProductOffer.product_id == product_id
        ).first()
        
        if not product:
            logger.warning(f"Product not found for update: {product_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Product with ID '{product_id}' not found"
            )
        
        # Update fields from request body
        product.product_name = product_data.product_name
        product.product_type = product_data.product_type
        product.category = product_data.category
        product.persona_targets = json.dumps(product_data.persona_targets)
        product.short_description = product_data.short_description
        product.benefits = json.dumps(product_data.benefits)
        product.disclosure = product_data.disclosure
        product.partner_name = product_data.partner_name
        product.min_income = product_data.min_income
        product.max_credit_utilization = product_data.max_credit_utilization
        product.requires_no_existing_savings = product_data.requires_no_existing_savings
        product.requires_no_existing_investment = product_data.requires_no_existing_investment
        product.min_credit_score = product_data.min_credit_score
        product.typical_apy_or_fee = product_data.typical_apy_or_fee
        product.partner_link = product_data.partner_link
        product.commission_rate = product_data.commission_rate
        product.priority = product_data.priority
        product.active = product_data.active
        product.updated_at = datetime.utcnow()
        
        # Commit changes
        db.commit()
        
        # Refresh to get updated timestamp
        db.refresh(product)
        
        logger.info(f"Updated product: {product_id} ({product.product_name})")
        
        # Parse JSON fields and return
        product_dict = _parse_json_fields(product)
        
        return product_dict
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Rollback database transaction on error
        db.rollback()
        logger.error(f"Error updating product {product_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_product(
    product_id: str,
    db: Session = Depends(get_db)
):
    """
    Deactivate a product (soft delete).
    
    This endpoint:
    1. Queries product by product_id
    2. Returns 404 if not found
    3. Sets active = False (soft delete)
    4. Updates updated_at timestamp
    5. Commits changes
    6. Returns 204 No Content
    
    Args:
        product_id: Product ID to deactivate
        db: Database session
    
    Returns:
        204 No Content
    
    Raises:
        404: Product not found
        500: Server error (database error)
    """
    try:
        # Query product by product_id
        product = db.query(ProductOffer).filter(
            ProductOffer.product_id == product_id
        ).first()
        
        if not product:
            logger.warning(f"Product not found for deactivation: {product_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Product with ID '{product_id}' not found"
            )
        
        # Set active = False (soft delete)
        product.active = False
        product.updated_at = datetime.utcnow()
        
        # Commit changes
        db.commit()
        
        logger.info(f"Deactivated product: {product_id} ({product.product_name})")
        
        # Return 204 No Content
        return None
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Rollback database transaction on error
        db.rollback()
        logger.error(f"Error deactivating product {product_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )

