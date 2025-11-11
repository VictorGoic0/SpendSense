#!/usr/bin/env python3
"""
Test script for product eligibility checking

Tests the eligibility logic for products:
- Income requirements
- Credit utilization requirements
- Existing account requirements
- Category-specific rules
- Full flow: match + filter
"""

import sys
from pathlib import Path

# Add backend to path (where app/ module lives)
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Get the correct database path (backend/spendsense.db)
database_path = backend_dir / "spendsense.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{database_path.absolute()}"

from app.services.guardrails import check_product_eligibility, filter_eligible_products
from app.services.product_matcher import match_products
from app.models import User, UserFeature, Persona, Account, ProductOffer
import json


def test_income_requirement(db):
    """Test income requirement eligibility"""
    print(f"\n{'='*60}")
    print("Income Requirement Test")
    print(f"{'='*60}")
    print()
    
    # Find a user with features
    features = db.query(UserFeature).filter(
        UserFeature.window_days == 30
    ).first()
    
    if not features:
        print("  No users with features found")
        return
    
    user_id = features.user_id
    user = db.query(User).filter(User.user_id == user_id).first()
    
    print(f"User: {user.full_name if user else 'Unknown'} ({user_id[:20]}...)")
    print(f"  Monthly Income: ${features.avg_monthly_income:.2f}")
    print()
    
    # Find products with income requirements
    products = db.query(ProductOffer).filter(
        ProductOffer.min_income > 0
    ).limit(5).all()
    
    if not products:
        print("  No products with income requirements found")
        return
    
    print("Testing products with income requirements:")
    print()
    for product in products:
        is_eligible, reason = check_product_eligibility(
            db, user_id, product, features
        )
        status = "✓ Eligible" if is_eligible else "✗ Not Eligible"
        print(f"  {status}: {product.product_name}")
        print(f"    Min Income: ${product.min_income:.2f}")
        print(f"    Reason: {reason}")
        print()
    
    # Test with product requiring higher income
    high_income_product = db.query(ProductOffer).filter(
        ProductOffer.min_income > features.avg_monthly_income
    ).first()
    
    if high_income_product:
        print(f"Testing product requiring higher income:")
        print(f"  Product: {high_income_product.product_name}")
        print(f"  Required: ${high_income_product.min_income:.2f}")
        print(f"  User has: ${features.avg_monthly_income:.2f}")
        is_eligible, reason = check_product_eligibility(
            db, user_id, high_income_product, features
        )
        print(f"  Result: {'✓ Eligible' if is_eligible else '✗ Not Eligible'}")
        print(f"  Reason: {reason}")
        print()


def test_credit_utilization_requirement(db):
    """Test credit utilization requirement eligibility"""
    print(f"\n{'='*60}")
    print("Credit Utilization Requirement Test")
    print(f"{'='*60}")
    print()
    
    # Find user with high utilization
    features = db.query(UserFeature).filter(
        UserFeature.window_days == 30,
        UserFeature.avg_utilization > 0.5
    ).first()
    
    if not features:
        print("  No users with high utilization found")
        return
    
    user_id = features.user_id
    user = db.query(User).filter(User.user_id == user_id).first()
    
    print(f"User: {user.full_name if user else 'Unknown'} ({user_id[:20]}...)")
    print(f"  Avg Utilization: {features.avg_utilization:.1%}")
    print()
    
    # Find balance transfer products (typically have max_utilization requirements)
    products = db.query(ProductOffer).filter(
        ProductOffer.category == "balance_transfer",
        ProductOffer.max_credit_utilization < 1.0
    ).limit(5).all()
    
    if not products:
        print("  No balance transfer products found")
        return
    
    print("Testing balance transfer products:")
    print()
    for product in products:
        is_eligible, reason = check_product_eligibility(
            db, user_id, product, features
        )
        status = "✓ Eligible" if is_eligible else "✗ Not Eligible"
        print(f"  {status}: {product.product_name}")
        print(f"    Max Utilization: {product.max_credit_utilization:.1%}")
        print(f"    Reason: {reason}")
        print()
    
    # Test with product requiring lower utilization
    low_util_product = db.query(ProductOffer).filter(
        ProductOffer.max_credit_utilization < features.avg_utilization,
        ProductOffer.max_credit_utilization < 1.0
    ).first()
    
    if low_util_product:
        print(f"Testing product requiring lower utilization:")
        print(f"  Product: {low_util_product.product_name}")
        print(f"  Max Allowed: {low_util_product.max_credit_utilization:.1%}")
        print(f"  User has: {features.avg_utilization:.1%}")
        is_eligible, reason = check_product_eligibility(
            db, user_id, low_util_product, features
        )
        print(f"  Result: {'✓ Eligible' if is_eligible else '✗ Not Eligible'}")
        print(f"  Reason: {reason}")
        print()


def test_existing_account_requirements(db):
    """Test existing account requirement eligibility"""
    print(f"\n{'='*60}")
    print("Existing Account Requirements Test")
    print(f"{'='*60}")
    print()
    
    # Find user with savings account
    user_with_savings = db.query(User).join(Account).filter(
        Account.type.in_(["savings", "money market", "cash management", "HSA"])
    ).first()
    
    if user_with_savings:
        features = db.query(UserFeature).filter(
            UserFeature.user_id == user_with_savings.user_id,
            UserFeature.window_days == 30
        ).first()
        
        if features:
            print(f"User with savings: {user_with_savings.full_name}")
            print(f"  User ID: {user_with_savings.user_id[:20]}...")
            
            # Get accounts
            accounts = db.query(Account).filter(
                Account.user_id == user_with_savings.user_id
            ).all()
            savings_accounts = [a for a in accounts if a.type in ["savings", "money market", "cash management", "HSA"]]
            print(f"  Savings Accounts: {len(savings_accounts)}")
            print()
            
            # Find HYSA product requiring no existing savings
            hysa_product = db.query(ProductOffer).filter(
                ProductOffer.category == "hysa",
                ProductOffer.requires_no_existing_savings == True
            ).first()
            
            if hysa_product:
                print(f"Testing HYSA product requiring no existing savings:")
                print(f"  Product: {hysa_product.product_name}")
                is_eligible, reason = check_product_eligibility(
                    db, user_with_savings.user_id, hysa_product, features
                )
                print(f"  Result: {'✓ Eligible' if is_eligible else '✗ Not Eligible'}")
                print(f"  Reason: {reason}")
                print()
    
    # Find user without savings account
    all_user_ids = {u.user_id for u in db.query(User).all()}
    users_with_savings_ids = {
        a.user_id for a in db.query(Account).filter(
            Account.type.in_(["savings", "money market", "cash management", "HSA"])
        ).all()
    }
    users_without_savings_ids = all_user_ids - users_with_savings_ids
    
    if users_without_savings_ids:
        user_id_no_savings = list(users_without_savings_ids)[0]
        user_no_savings = db.query(User).filter(User.user_id == user_id_no_savings).first()
        features = db.query(UserFeature).filter(
            UserFeature.user_id == user_id_no_savings,
            UserFeature.window_days == 30
        ).first()
        
        if features and user_no_savings:
            print(f"User without savings: {user_no_savings.full_name}")
            print(f"  User ID: {user_id_no_savings[:20]}...")
            print()
            
            # Find HYSA product requiring no existing savings
            hysa_product = db.query(ProductOffer).filter(
                ProductOffer.category == "hysa",
                ProductOffer.requires_no_existing_savings == True
            ).first()
            
            if hysa_product:
                print(f"Testing HYSA product requiring no existing savings:")
                print(f"  Product: {hysa_product.product_name}")
                is_eligible, reason = check_product_eligibility(
                    db, user_id_no_savings, hysa_product, features
                )
                print(f"  Result: {'✓ Eligible' if is_eligible else '✗ Not Eligible'}")
                print(f"  Reason: {reason}")
                print()
    
    # Test investment account requirement
    user_with_investment = db.query(User).join(Account).filter(
        Account.type == "investment"
    ).first()
    
    if user_with_investment:
        features = db.query(UserFeature).filter(
            UserFeature.user_id == user_with_investment.user_id,
            UserFeature.window_days == 30
        ).first()
        
        if features:
            print(f"User with investment account: {user_with_investment.full_name}")
            
            # Find investment product requiring no existing investment
            investment_product = db.query(ProductOffer).filter(
                ProductOffer.category == "robo_advisor",
                ProductOffer.requires_no_existing_investment == True
            ).first()
            
            if investment_product:
                print(f"Testing investment product requiring no existing investment:")
                print(f"  Product: {investment_product.product_name}")
                is_eligible, reason = check_product_eligibility(
                    db, user_with_investment.user_id, investment_product, features
                )
                print(f"  Result: {'✓ Eligible' if is_eligible else '✗ Not Eligible'}")
                print(f"  Reason: {reason}")
                print()


def test_category_specific_rules(db):
    """Test category-specific eligibility rules"""
    print(f"\n{'='*60}")
    print("Category-Specific Rules Test")
    print(f"{'='*60}")
    print()
    
    # Test balance transfer rule (requires utilization >= 0.3)
    # Find user with low utilization
    low_util_features = db.query(UserFeature).filter(
        UserFeature.window_days == 30,
        UserFeature.avg_utilization < 0.3
    ).first()
    
    if low_util_features:
        user_id = low_util_features.user_id
        user = db.query(User).filter(User.user_id == user_id).first()
        
        print(f"User with low utilization: {user.full_name if user else 'Unknown'}")
        print(f"  Avg Utilization: {low_util_features.avg_utilization:.1%}")
        print()
        
        # Find balance transfer product
        balance_transfer_product = db.query(ProductOffer).filter(
            ProductOffer.category == "balance_transfer"
        ).first()
        
        if balance_transfer_product:
            print(f"Testing balance transfer product:")
            print(f"  Product: {balance_transfer_product.product_name}")
            is_eligible, reason = check_product_eligibility(
                db, user_id, balance_transfer_product, low_util_features
            )
            print(f"  Result: {'✓ Eligible' if is_eligible else '✗ Not Eligible'}")
            print(f"  Reason: {reason}")
            print()
    
    # Test with user with high utilization (should be eligible)
    high_util_features = db.query(UserFeature).filter(
        UserFeature.window_days == 30,
        UserFeature.avg_utilization >= 0.3
    ).first()
    
    if high_util_features:
        user_id = high_util_features.user_id
        user = db.query(User).filter(User.user_id == user_id).first()
        
        print(f"User with high utilization: {user.full_name if user else 'Unknown'}")
        print(f"  Avg Utilization: {high_util_features.avg_utilization:.1%}")
        print()
        
        # Find balance transfer product
        balance_transfer_product = db.query(ProductOffer).filter(
            ProductOffer.category == "balance_transfer"
        ).first()
        
        if balance_transfer_product:
            print(f"Testing balance transfer product:")
            print(f"  Product: {balance_transfer_product.product_name}")
            is_eligible, reason = check_product_eligibility(
                db, user_id, balance_transfer_product, high_util_features
            )
            print(f"  Result: {'✓ Eligible' if is_eligible else '✗ Not Eligible'}")
            print(f"  Reason: {reason}")
            print()


def test_full_flow(db):
    """Test full flow: match products then filter by eligibility"""
    print(f"\n{'='*60}")
    print("Full Flow Test: Match + Filter")
    print(f"{'='*60}")
    print()
    
    # Find user with persona
    persona = db.query(Persona).filter(
        Persona.window_days == 30
    ).first()
    
    if not persona:
        print("  No users with personas found")
        return
    
    user_id = persona.user_id
    user = db.query(User).filter(User.user_id == user_id).first()
    features = db.query(UserFeature).filter(
        UserFeature.user_id == user_id,
        UserFeature.window_days == 30
    ).first()
    
    if not features:
        print(f"  User {user_id} has no features computed")
        return
    
    print(f"User: {user.full_name if user else 'Unknown'} ({user_id[:20]}...)")
    print(f"  Persona: {persona.persona_type}")
    print(f"  Monthly Income: ${features.avg_monthly_income:.2f}")
    print(f"  Avg Utilization: {features.avg_utilization:.1%}" if features.avg_utilization else "  Avg Utilization: N/A")
    print()
    
    # Match products
    print("Step 1: Matching products by relevance...")
    matches = match_products(db, user_id, persona.persona_type, features)
    print(f"  Matched {len(matches)} products")
    print()
    
    # Show all matches
    print("Matched Products (before eligibility filtering):")
    for i, match in enumerate(matches, 1):
        print(f"  {i}. {match['product_name']} ({match['category']})")
        print(f"     Relevance Score: {match['relevance_score']:.2f}")
    
    print()
    
    # Apply eligibility filtering manually to show what gets filtered
    print("Step 2: Applying eligibility filtering...")
    eligible_matches = filter_eligible_products(db, user_id, matches, features)
    print(f"  Eligible products: {len(eligible_matches)}")
    print()
    
    # Show eligible matches
    if eligible_matches:
        print("Eligible Products (after filtering):")
        for i, match in enumerate(eligible_matches, 1):
            print(f"  {i}. {match['product_name']} ({match['category']})")
            print(f"     Relevance Score: {match['relevance_score']:.2f}")
            print(f"     Rationale: {match['rationale']}")
    else:
        print("  No eligible products found")
    print()
    
    # Show filtered out products
    filtered_out = [m for m in matches if m['product_id'] not in {e['product_id'] for e in eligible_matches}]
    if filtered_out:
        print("Filtered Out Products:")
        for match in filtered_out:
            # Get product to check eligibility
            product = db.query(ProductOffer).filter(
                ProductOffer.product_id == match['product_id']
            ).first()
            if product:
                is_eligible, reason = check_product_eligibility(
                    db, user_id, product, features
                )
                print(f"  - {match['product_name']} ({match['category']})")
                print(f"    Reason: {reason}")
        print()


def main():
    """Run all eligibility tests"""
    print("="*60)
    print("Product Eligibility Testing")
    print("="*60)
    
    # Create database session
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Run tests
        test_income_requirement(db)
        test_credit_utilization_requirement(db)
        test_existing_account_requirements(db)
        test_category_specific_rules(db)
        test_full_flow(db)
        
        print(f"\n{'='*60}")
        print("All tests completed")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()

