"""
Guardrails Service

Provides validation functions for recommendations:
- Tone validation (forbidden phrases, empowering language)
- Consent checks
- Eligibility validation (income, credit, accounts)
- Partner offer filtering
- Mandatory disclosure appending
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Dict, Any, List, Optional
import logging
import json

from app.models import User, UserFeature, Account, ProductOffer

logger = logging.getLogger(__name__)


# ============================================================================
# Tone Validation
# ============================================================================

def validate_tone(content: str) -> Dict[str, Any]:
    """
    Validates content for tone compliance.
    
    Checks for:
    - Forbidden shaming phrases (CRITICAL - RED in operator UI)
    - Empowering language presence (NOTABLE - YELLOW in operator UI)
    
    Args:
        content: Content string to validate
    
    Returns:
        {
            "is_valid": bool,  # True if no warnings, False if any warnings exist
            "validation_warnings": [
                {
                    "severity": "critical" | "notable",
                    "type": "forbidden_phrase" | "lacks_empowering_language",
                    "message": str  # Human-readable description
                }
            ]
        }
    
    Examples:
        # Valid content (no warnings)
        {
            "is_valid": True,
            "validation_warnings": []
        }
        
        # Invalid: Contains forbidden phrase
        {
            "is_valid": False,
            "validation_warnings": [
                {
                    "severity": "critical",
                    "type": "forbidden_phrase",
                    "message": "Contains shaming language: 'you're overspending'"
                }
            ]
        }
        
        # Invalid: Lacks empowering language
        {
            "is_valid": False,
            "validation_warnings": [
                {
                    "severity": "notable",
                    "type": "lacks_empowering_language",
                    "message": "Content lacks empowering tone - no empowering keywords found"
                }
            ]
        }
    """
    warnings = []
    
    # Convert content to lowercase for checking
    content_lower = content.lower()
    
    # Forbidden phrases (CRITICAL - RED in operator UI)
    forbidden_phrases = [
        "you're overspending",
        "bad habit",
        "poor financial decision",
        "irresponsible",
        "wasteful spending",
        "you should stop",
        "you need to"
    ]
    
    # Loop through forbidden phrases
    for phrase in forbidden_phrases:
        if phrase in content_lower:
            warnings.append({
                "severity": "critical",
                "type": "forbidden_phrase",
                "message": f"Contains shaming language: '{phrase}'"
            })
            logger.warning(f"Tone validation failed: Found forbidden phrase '{phrase}'")
    
    # Empowering language check (NOTABLE - YELLOW in operator UI)
    empowering_keywords = [
        "you can",
        "let's",
        "many people",
        "common challenge",
        "opportunity",
        "consider",
        "explore"
    ]
    
    # Check if at least one empowering keyword present
    has_empowering_language = any(keyword in content_lower for keyword in empowering_keywords)
    
    if not has_empowering_language:
        warnings.append({
            "severity": "notable",
            "type": "lacks_empowering_language",
            "message": "Content lacks empowering tone - no empowering keywords found"
        })
        logger.warning("Tone validation failed: Lacks empowering language")
    
    # Return result dict
    result = {
        "is_valid": len(warnings) == 0,
        "validation_warnings": warnings
    }
    
    if result["is_valid"]:
        logger.debug("Tone validation passed")
    else:
        logger.info(f"Tone validation found {len(warnings)} warning(s)")
    
    return result


# ============================================================================
# Consent Validation
# ============================================================================

def check_consent(db: Session, user_id: str) -> bool:
    """
    Check if user has granted consent for recommendations.
    
    Args:
        db: Database session
        user_id: User ID to check
    
    Returns:
        True if consent_status == True, False otherwise
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        logger.warning(f"User {user_id} not found for consent check")
        return False
    
    consent_status = user.consent_status or False
    
    if consent_status:
        logger.debug(f"User {user_id} has granted consent")
    else:
        logger.info(f"User {user_id} has not granted consent")
    
    return consent_status


# ============================================================================
# Eligibility Validation
# ============================================================================

def check_income_eligibility(db: Session, user_id: str, min_income: float) -> bool:
    """
    Check if user meets minimum income requirement.
    
    Args:
        db: Database session
        user_id: User ID to check
        min_income: Minimum monthly income required
    
    Returns:
        True if avg_monthly_income >= min_income, False otherwise
    """
    # Query UserFeature for user (30d window)
    user_feature = db.query(UserFeature).filter(
        and_(
            UserFeature.user_id == user_id,
            UserFeature.window_days == 30
        )
    ).first()
    
    if not user_feature:
        logger.warning(f"User {user_id} has no features computed for income eligibility check")
        return False
    
    avg_monthly_income = user_feature.avg_monthly_income or 0.0
    
    is_eligible = avg_monthly_income >= min_income
    
    if is_eligible:
        logger.debug(f"User {user_id} meets income requirement: ${avg_monthly_income:.2f} >= ${min_income:.2f}")
    else:
        logger.info(f"User {user_id} does not meet income requirement: ${avg_monthly_income:.2f} < ${min_income:.2f}")
    
    return is_eligible


def check_credit_eligibility(db: Session, user_id: str, max_utilization: float) -> bool:
    """
    Check if user meets maximum credit utilization requirement.
    
    Args:
        db: Database session
        user_id: User ID to check
        max_utilization: Maximum utilization threshold (0.0-1.0)
    
    Returns:
        True if max_utilization <= threshold, False otherwise
    """
    # Query UserFeature for user (30d window)
    user_feature = db.query(UserFeature).filter(
        and_(
            UserFeature.user_id == user_id,
            UserFeature.window_days == 30
        )
    ).first()
    
    if not user_feature:
        logger.warning(f"User {user_id} has no features computed for credit eligibility check")
        return False
    
    user_max_utilization = user_feature.max_utilization or 0.0
    
    is_eligible = user_max_utilization <= max_utilization
    
    if is_eligible:
        logger.debug(f"User {user_id} meets credit requirement: {user_max_utilization:.2%} <= {max_utilization:.2%}")
    else:
        logger.info(f"User {user_id} does not meet credit requirement: {user_max_utilization:.2%} > {max_utilization:.2%}")
    
    return is_eligible


def check_account_exists(db: Session, user_id: str, account_type: str) -> bool:
    """
    Check if user has at least one account of the specified type.
    
    Args:
        db: Database session
        user_id: User ID to check
        account_type: Account type to check for (e.g., "checking", "savings", "credit card")
    
    Returns:
        True if at least one account found, False otherwise
    """
    # Query Account records for user
    accounts = db.query(Account).filter(
        and_(
            Account.user_id == user_id,
            Account.type == account_type
        )
    ).all()
    
    has_account = len(accounts) > 0
    
    if has_account:
        logger.debug(f"User {user_id} has {len(accounts)} {account_type} account(s)")
    else:
        logger.info(f"User {user_id} does not have any {account_type} accounts")
    
    return has_account


# ============================================================================
# Product Eligibility Checking
# ============================================================================

def check_product_eligibility(
    db: Session,
    user_id: str,
    product: ProductOffer,
    features: UserFeature
) -> tuple[bool, str]:
    """
    Check if user is eligible for a product based on eligibility criteria.
    
    Checks:
    - Income requirement (min_income)
    - Credit utilization requirement (max_credit_utilization)
    - Existing savings requirement (requires_no_existing_savings)
    - Existing investment requirement (requires_no_existing_investment)
    - Category-specific rules (e.g., balance_transfer requires meaningful utilization)
    
    Args:
        db: Database session
        user_id: User ID to check
        product: ProductOffer model instance
        features: UserFeature model instance (30d window)
    
    Returns:
        Tuple of (is_eligible: bool, reason: str)
        - If eligible: (True, "Eligible")
        - If not eligible: (False, reason_string)
    """
    # Query user's accounts for account type checking
    accounts = db.query(Account).filter(
        Account.user_id == user_id
    ).all()
    
    # Check income requirement
    if product.min_income and product.min_income > 0:
        user_monthly_income = features.avg_monthly_income or 0.0
        if user_monthly_income < product.min_income:
            reason = f"Income below minimum requirement (${user_monthly_income:.2f} < ${product.min_income:.2f})"
            logger.info(f"Product {product.product_id} eligibility failed for user {user_id}: {reason}")
            return (False, reason)
    
    # Check credit utilization requirement
    if product.max_credit_utilization and product.max_credit_utilization < 1.0:
        user_avg_utilization = features.avg_utilization or 0.0
        if user_avg_utilization > product.max_credit_utilization:
            reason = f"Credit utilization too high ({user_avg_utilization:.1%} > {product.max_credit_utilization:.1%})"
            logger.info(f"Product {product.product_id} eligibility failed for user {user_id}: {reason}")
            return (False, reason)
    
    # Check existing savings requirement
    if product.requires_no_existing_savings:
        savings_types = {"savings", "money market", "cash management", "HSA"}
        has_savings = any(acc.type in savings_types for acc in accounts)
        if has_savings:
            reason = "Already has savings account"
            logger.info(f"Product {product.product_id} eligibility failed for user {user_id}: {reason}")
            return (False, reason)
    
    # Check existing investment requirement
    if product.requires_no_existing_investment:
        has_investment = any(acc.type == "investment" for acc in accounts)
        if has_investment:
            reason = "Already has investment account"
            logger.info(f"Product {product.product_id} eligibility failed for user {user_id}: {reason}")
            return (False, reason)
    
    # Check category-specific rules
    if product.category == "balance_transfer":
        # Require avg_utilization >= 0.3 (only show if meaningful balance to transfer)
        user_avg_utilization = features.avg_utilization or 0.0
        if user_avg_utilization < 0.3:
            reason = f"Balance transfer not beneficial at current utilization ({user_avg_utilization:.1%} < 30%)"
            logger.info(f"Product {product.product_id} eligibility failed for user {user_id}: {reason}")
            return (False, reason)
    
    # All checks passed
    logger.debug(f"Product {product.product_id} eligibility passed for user {user_id}")
    return (True, "Eligible")


def filter_eligible_products(
    db: Session,
    user_id: str,
    products: List[Dict[str, Any]],
    features: UserFeature
) -> List[Dict[str, Any]]:
    """
    Filter list of product matches to only include eligible products.
    
    Args:
        db: Database session
        user_id: User ID to filter products for
        products: List of product match dictionaries (from match_products)
        features: UserFeature model instance (30d window)
    
    Returns:
        Filtered list of eligible products
    """
    eligible_products = []
    
    for product_match in products:
        # Get product_id from match dict
        product_id = product_match.get("product_id")
        if not product_id:
            logger.warning(f"Product match missing product_id, skipping")
            continue
        
        # Query ProductOffer from database
        product = db.query(ProductOffer).filter(
            ProductOffer.product_id == product_id
        ).first()
        
        if not product:
            logger.warning(f"Product {product_id} not found in database, skipping")
            continue
        
        # Check eligibility
        is_eligible, reason = check_product_eligibility(db, user_id, product, features)
        
        if is_eligible:
            eligible_products.append(product_match)
        else:
            logger.debug(
                f"Product {product_id} ({product.product_name}) filtered: {reason}"
            )
    
    logger.info(
        f"Filtered {len(products)} products to {len(eligible_products)} eligible "
        f"products for user {user_id}"
    )
    
    return eligible_products


# ============================================================================
# Partner Offer Filtering
# ============================================================================

def filter_partner_offers(db: Session, user_id: str, offers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter partner offers based on user eligibility requirements.
    
    Each offer should have eligibility requirements in its metadata:
    - min_income: Optional minimum monthly income
    - max_utilization: Optional maximum credit utilization (0.0-1.0)
    - required_account_type: Optional account type that must exist
    
    Args:
        db: Database session
        user_id: User ID to filter offers for
        offers: List of offer dictionaries with eligibility metadata
    
    Returns:
        Filtered list of offers (only those user is eligible for)
    """
    filtered_offers = []
    
    for offer in offers:
        is_eligible = True
        
        # Check eligibility requirements if present in offer metadata
        metadata = offer.get("metadata", {})
        
        # Check income requirement
        if "min_income" in metadata:
            min_income = metadata["min_income"]
            if not check_income_eligibility(db, user_id, min_income):
                is_eligible = False
                logger.debug(f"Offer {offer.get('offer_id', 'unknown')} filtered: income requirement not met")
        
        # Check credit requirement
        if "max_utilization" in metadata:
            max_utilization = metadata["max_utilization"]
            if not check_credit_eligibility(db, user_id, max_utilization):
                is_eligible = False
                logger.debug(f"Offer {offer.get('offer_id', 'unknown')} filtered: credit requirement not met")
        
        # Check account existence requirement
        if "required_account_type" in metadata:
            account_type = metadata["required_account_type"]
            if not check_account_exists(db, user_id, account_type):
                is_eligible = False
                logger.debug(f"Offer {offer.get('offer_id', 'unknown')} filtered: required account type not found")
        
        if is_eligible:
            filtered_offers.append(offer)
        else:
            logger.info(f"Offer {offer.get('offer_id', 'unknown')} removed from list for user {user_id}")
    
    logger.info(f"Filtered {len(offers)} offers to {len(filtered_offers)} eligible offers for user {user_id}")
    
    return filtered_offers


# ============================================================================
# Mandatory Disclosure
# ============================================================================

MANDATORY_DISCLOSURE = "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."


def append_disclosure(content: str) -> str:
    """
    Append mandatory disclosure to content.
    
    Args:
        content: Original content string
    
    Returns:
        Content with disclosure appended
    """
    # Add disclosure to end of content
    if content.strip().endswith("."):
        # Content ends with period, add space and disclosure
        return f"{content}\n\n{MANDATORY_DISCLOSURE}"
    else:
        # Content doesn't end with period, add period then disclosure
        return f"{content}.\n\n{MANDATORY_DISCLOSURE}"

