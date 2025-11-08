"""
Product Matching Service

Matches users to relevant financial products based on persona and behavioral signals.
Products are scored for relevance and filtered by eligibility criteria.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Dict, Any, List, Optional
import logging
import json

from app.models import ProductOffer, UserFeature, Account
from app.services.guardrails import filter_eligible_products

logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================

def get_account_types(accounts: List[Account]) -> set[str]:
    """
    Extract account types from list of accounts.
    
    Args:
        accounts: List of Account model instances
    
    Returns:
        Set of unique account type strings
    """
    return {acc.type for acc in accounts if acc.type}


def has_hysa(accounts: List[Account]) -> bool:
    """
    Check if user has a high-yield savings account.
    
    Looks for savings accounts with high interest indicators.
    For MVP, we check for savings account types that might be HYSA.
    
    Args:
        accounts: List of Account model instances
    
    Returns:
        True if user has savings account, False otherwise
    """
    savings_types = {"savings", "money market", "cash management", "HSA"}
    return any(acc.type in savings_types for acc in accounts)


def has_investment_account(accounts: List[Account]) -> bool:
    """
    Check if user has an investment account.
    
    Args:
        accounts: List of Account model instances
    
    Returns:
        True if user has investment account, False otherwise
    """
    return any(acc.type == "investment" for acc in accounts)


# ============================================================================
# Relevance Scoring Logic
# ============================================================================

def calculate_relevance_score(
    product: ProductOffer,
    features: UserFeature,
    accounts: List[Account]
) -> float:
    """
    Calculate relevance score for a product based on user features.
    
    Scoring rules by category:
    - balance_transfer: High utilization, interest charges
    - hysa: Savings activity, low emergency fund
    - budgeting_app: Income variability, low buffer
    - subscription_manager: High recurring merchants
    - robo_advisor: High income, low utilization, good emergency fund
    
    Args:
        product: ProductOffer model instance
        features: UserFeature model instance (30d window)
        accounts: List of Account model instances
    
    Returns:
        Relevance score between 0.0 and 1.0
    """
    # Initialize base score
    score = 0.5
    
    category = product.category
    
    # Balance transfer products
    if category == "balance_transfer":
        avg_util = features.avg_utilization or 0.0
        if avg_util > 0.5:
            score += 0.3
        if features.interest_charges_present:
            score += 0.2
        if avg_util > 0.7:
            score += 0.2  # Bonus for very high utilization
    
    # HYSA products
    elif category == "hysa":
        net_savings = features.net_savings_inflow or 0.0
        emergency_months = features.emergency_fund_months or 0.0
        
        if net_savings > 0 and emergency_months < 3:
            score += 0.4
        if features.savings_growth_rate and features.savings_growth_rate > 0.02:
            score += 0.2
        if has_hysa(accounts):
            score -= 0.5  # Penalize if already has HYSA
    
    # Budgeting app products
    elif category == "budgeting_app":
        income_var = features.income_variability or 0.0
        buffer_days = features.cash_flow_buffer_months * 30 if features.cash_flow_buffer_months else 0
        
        if income_var > 0.3:
            score += 0.3
        if buffer_days < 30:
            score += 0.3
        # Calculate expense volatility from features (approximate)
        # For MVP, use income variability as proxy
        if income_var > 0.25:
            score += 0.2
    
    # Subscription manager products
    elif category == "subscription_manager":
        recurring_count = features.recurring_merchants or 0
        sub_share = features.subscription_spend_share or 0.0
        
        if recurring_count >= 5:
            score += 0.4
        if sub_share > 0.2:
            score += 0.3
    
    # Robo advisor / investment products
    elif category == "robo_advisor":
        monthly_income = features.avg_monthly_income or 0.0
        avg_util = features.avg_utilization or 0.0
        emergency_months = features.emergency_fund_months or 0.0
        
        if monthly_income > 5000 and avg_util < 0.3:
            score += 0.4
        if emergency_months >= 3:
            score += 0.3
        if has_investment_account(accounts):
            score -= 0.4  # Penalize if already has investment account
    
    # Clamp score to [0.0, 1.0]
    score = max(0.0, min(1.0, score))
    
    logger.debug(
        f"Relevance score for product {product.product_id} ({category}): {score:.2f}"
    )
    
    return score


# ============================================================================
# Product Rationale Generation
# ============================================================================

def generate_product_rationale(
    product: ProductOffer,
    features: UserFeature
) -> str:
    """
    Generate rationale text explaining why product is relevant to user.
    
    Args:
        product: ProductOffer model instance
        features: UserFeature model instance (30d window)
    
    Returns:
        Rationale string explaining product relevance
    """
    category = product.category
    
    # Balance transfer products
    if category == "balance_transfer":
        avg_util = features.avg_utilization or 0.0
        util_pct = avg_util * 100
        
        # Estimate monthly interest savings (rough calculation)
        # Assume average balance and interest rate
        # For MVP, use simplified calculation
        estimated_savings = 50.0  # Placeholder - could be calculated from actual balances
        
        return (
            f"With your credit utilization at {util_pct:.0f}%, this card could "
            f"save you approximately ${estimated_savings:.0f}/month in interest."
        )
    
    # HYSA products
    elif category == "hysa":
        net_savings = features.net_savings_inflow or 0.0
        emergency_months = features.emergency_fund_months or 0.0
        
        # Extract APY from typical_apy_or_fee (e.g., "4.5% APY")
        apy_str = product.typical_apy_or_fee or "4.5% APY"
        apy_value = 0.045  # Default
        try:
            # Try to extract number from string
            import re
            match = re.search(r'(\d+\.?\d*)%', apy_str)
            if match:
                apy_value = float(match.group(1)) / 100
        except:
            pass
        
        # Calculate annual interest earnings
        monthly_savings = net_savings if net_savings > 0 else 500  # Fallback
        annual_earnings = monthly_savings * 12 * apy_value
        
        return (
            f"Your ${monthly_savings:.0f}/month savings in a HYSA earning {apy_str} "
            f"could generate approximately ${annual_earnings:.0f} extra per year."
        )
    
    # Budgeting app products
    elif category == "budgeting_app":
        income_var = features.income_variability or 0.0
        buffer_days = features.cash_flow_buffer_months * 30 if features.cash_flow_buffer_months else 0
        
        if income_var > 0.3:
            return (
                f"With variable income (variability: {income_var:.0%}) and only "
                f"{buffer_days:.0f} days of buffer, this app helps manage irregular cash flow."
            )
        else:
            return (
                f"With only {buffer_days:.0f} days of cash flow buffer, this app "
                f"helps you track expenses and build financial stability."
            )
    
    # Subscription manager products
    elif category == "subscription_manager":
        recurring_count = features.recurring_merchants or 0
        monthly_recurring = features.monthly_recurring_spend or 0.0
        
        return (
            f"You have {recurring_count} recurring subscriptions totaling "
            f"${monthly_recurring:.0f}/month - this tool can help identify savings."
        )
    
    # Investment products
    elif category == "robo_advisor":
        monthly_income = features.avg_monthly_income or 0.0
        emergency_months = features.emergency_fund_months or 0.0
        
        return (
            f"With ${monthly_income:.0f}/month income and {emergency_months:.1f} months "
            f"emergency fund, you're ready to start investing."
        )
    
    # Default rationale
    return (
        f"This product aligns with your financial profile and could help you "
        f"achieve your goals."
    )


# ============================================================================
# Main Product Matching Function
# ============================================================================

def match_products(
    db: Session,
    user_id: str,
    persona_type: str,
    features: UserFeature
) -> List[Dict[str, Any]]:
    """
    Match products to user based on persona and features.
    
    Process:
    1. Parse persona_type (handle 30d/180d suffixes if present)
    2. Query active products targeting user's persona
    3. Calculate relevance scores for each product
    4. Generate rationales
    5. Filter by relevance threshold (>= 0.5)
    6. Sort by score descending
    7. Return top 3 products
    
    Args:
        db: Database session
        user_id: User ID to match products for
        persona_type: Persona type (e.g., "high_utilization" or "high_utilization_30d")
        features: UserFeature model instance (30d window)
    
    Returns:
        List of product match dictionaries with:
        - product_id, product_name, product_type, category
        - short_description, benefits, typical_apy_or_fee
        - partner_name, partner_link
        - relevance_score, rationale
    """
    # Parse persona_type (remove _30d or _180d suffix if present)
    base_persona = persona_type
    if persona_type.endswith("_30d") or persona_type.endswith("_180d"):
        base_persona = persona_type.rsplit("_", 1)[0]
    
    logger.info(f"Matching products for user {user_id} with persona {base_persona}")
    
    # Query user's accounts
    accounts = db.query(Account).filter(
        Account.user_id == user_id
    ).all()
    
    # Query active products
    active_products = db.query(ProductOffer).filter(
        ProductOffer.active == True
    ).all()
    
    # Filter products by persona_targets
    candidate_products = []
    for product in active_products:
        # Parse persona_targets JSON
        try:
            if isinstance(product.persona_targets, str):
                target_personas = json.loads(product.persona_targets)
            else:
                target_personas = product.persona_targets
            
            if not isinstance(target_personas, list):
                logger.warning(
                    f"Product {product.product_id} has invalid persona_targets format"
                )
                continue
            
            # Check if user's persona is in target list
            if base_persona in target_personas:
                candidate_products.append(product)
        except json.JSONDecodeError:
            logger.warning(
                f"Product {product.product_id} has invalid persona_targets JSON"
            )
            continue
    
    logger.debug(f"Found {len(candidate_products)} candidate products for persona {base_persona}")
    
    # Calculate relevance scores and generate rationales
    product_matches = []
    for product in candidate_products:
        # Calculate relevance score
        relevance_score = calculate_relevance_score(product, features, accounts)
        
        # Generate rationale
        rationale = generate_product_rationale(product, features)
        
        # Parse benefits JSON
        benefits = []
        try:
            if isinstance(product.benefits, str):
                benefits = json.loads(product.benefits)
            else:
                benefits = product.benefits
            if not isinstance(benefits, list):
                benefits = []
        except json.JSONDecodeError:
            logger.warning(f"Product {product.product_id} has invalid benefits JSON")
            benefits = []
        
        # Create product match dict
        match_dict = {
            "product_id": product.product_id,
            "product_name": product.product_name,
            "product_type": product.product_type,
            "category": product.category,
            "short_description": product.short_description,
            "benefits": benefits,
            "typical_apy_or_fee": product.typical_apy_or_fee,
            "partner_name": product.partner_name,
            "partner_link": product.partner_link,
            "disclosure": product.disclosure,
            "relevance_score": relevance_score,
            "rationale": rationale,
        }
        
        product_matches.append(match_dict)
    
    # Filter by relevance threshold (>= 0.5)
    filtered_matches = [
        match for match in product_matches
        if match["relevance_score"] >= 0.5
    ]
    
    logger.debug(
        f"Filtered {len(product_matches)} products to {len(filtered_matches)} "
        f"with relevance >= 0.5"
    )
    
    # Sort by relevance score descending
    filtered_matches.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    # Apply eligibility filtering
    eligible_matches = filter_eligible_products(db, user_id, filtered_matches, features)
    
    # Return top 3 eligible products
    top_products = eligible_matches[:3]
    
    logger.info(
        f"Matched {len(top_products)} eligible products for user {user_id} "
        f"(persona: {base_persona})"
    )
    
    return top_products

