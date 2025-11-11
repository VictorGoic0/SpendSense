#!/usr/bin/env python3
"""
Test script for product matching service

Tests the product matching logic with users from the database.
Verifies that products are matched correctly based on persona and features.
"""

import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Add backend to path (where app/ module lives)
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use DATABASE_URL env var if available, otherwise use local database
database_path = backend_dir / "spendsense.db"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{database_path.absolute()}")

from app.services.product_matcher import match_products
from app.models import User, UserFeature, Persona, Account, ProductOffer
import json


def test_high_utilization_user(db):
    """Test product matching for high utilization user"""
    print(f"\n{'='*60}")
    print("High Utilization User Test")
    print(f"{'='*60}")
    print()
    
    # Find user with high utilization persona
    persona = db.query(Persona).filter(
        Persona.persona_type == "high_utilization",
        Persona.window_days == 30
    ).first()
    
    if not persona:
        print("  No high_utilization user found in database")
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
    print(f"  Avg Utilization: {features.avg_utilization:.2%}" if features.avg_utilization else "  Avg Utilization: N/A")
    print(f"  Interest Charges: {features.interest_charges_present}")
    print()
    
    # Match products
    matches = match_products(db, user_id, persona.persona_type, features)
    
    print(f"Matched {len(matches)} products:")
    print()
    for i, match in enumerate(matches, 1):
        print(f"  {i}. {match['product_name']}")
        print(f"     Category: {match['category']}")
        print(f"     Relevance Score: {match['relevance_score']:.2f}")
        print(f"     Rationale: {match['rationale']}")
        print()
    
    # Verify balance transfer cards ranked high
    balance_transfer_matches = [
        m for m in matches if m['category'] == 'balance_transfer'
    ]
    if balance_transfer_matches:
        print(f"  ✓ Found {len(balance_transfer_matches)} balance transfer product(s)")
    else:
        print(f"  ⚠ No balance transfer products matched")
    print()


def test_savings_builder_user(db):
    """Test product matching for savings builder user"""
    print(f"\n{'='*60}")
    print("Savings Builder User Test")
    print(f"{'='*60}")
    print()
    
    # Find user with savings_builder persona
    persona = db.query(Persona).filter(
        Persona.persona_type == "savings_builder",
        Persona.window_days == 30
    ).first()
    
    if not persona:
        print("  No savings_builder user found in database")
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
    print(f"  Net Savings Inflow: ${features.net_savings_inflow:.2f}" if features.net_savings_inflow else "  Net Savings Inflow: $0.00")
    print(f"  Emergency Fund Months: {features.emergency_fund_months:.1f}" if features.emergency_fund_months else "  Emergency Fund Months: 0.0")
    print()
    
    # Match products
    matches = match_products(db, user_id, persona.persona_type, features)
    
    print(f"Matched {len(matches)} products:")
    print()
    for i, match in enumerate(matches, 1):
        print(f"  {i}. {match['product_name']}")
        print(f"     Category: {match['category']}")
        print(f"     Relevance Score: {match['relevance_score']:.2f}")
        print(f"     Rationale: {match['rationale']}")
        print()
    
    # Verify HYSA products ranked high
    hysa_matches = [m for m in matches if m['category'] == 'hysa']
    if hysa_matches:
        print(f"  ✓ Found {len(hysa_matches)} HYSA product(s)")
    else:
        print(f"  ⚠ No HYSA products matched")
    print()


def test_variable_income_user(db):
    """Test product matching for variable income user"""
    print(f"\n{'='*60}")
    print("Variable Income User Test")
    print(f"{'='*60}")
    print()
    
    # Find user with variable_income persona
    persona = db.query(Persona).filter(
        Persona.persona_type == "variable_income",
        Persona.window_days == 30
    ).first()
    
    if not persona:
        print("  No variable_income user found in database")
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
    print(f"  Income Variability: {features.income_variability:.2%}" if features.income_variability else "  Income Variability: N/A")
    buffer_days = features.cash_flow_buffer_months * 30 if features.cash_flow_buffer_months else 0
    print(f"  Cash Flow Buffer: {buffer_days:.0f} days")
    print()
    
    # Match products
    matches = match_products(db, user_id, persona.persona_type, features)
    
    print(f"Matched {len(matches)} products:")
    print()
    for i, match in enumerate(matches, 1):
        print(f"  {i}. {match['product_name']}")
        print(f"     Category: {match['category']}")
        print(f"     Relevance Score: {match['relevance_score']:.2f}")
        print(f"     Rationale: {match['rationale']}")
        print()
    
    # Verify budgeting apps ranked high
    budgeting_matches = [m for m in matches if m['category'] == 'budgeting_app']
    if budgeting_matches:
        print(f"  ✓ Found {len(budgeting_matches)} budgeting app product(s)")
    else:
        print(f"  ⚠ No budgeting app products matched")
    print()


def test_subscription_heavy_user(db):
    """Test product matching for subscription heavy user"""
    print(f"\n{'='*60}")
    print("Subscription Heavy User Test")
    print(f"{'='*60}")
    print()
    
    # Find user with subscription_heavy persona
    persona = db.query(Persona).filter(
        Persona.persona_type == "subscription_heavy",
        Persona.window_days == 30
    ).first()
    
    if not persona:
        print("  No subscription_heavy user found in database")
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
    print(f"  Recurring Merchants: {features.recurring_merchants}")
    print(f"  Subscription Spend Share: {features.subscription_spend_share:.2%}" if features.subscription_spend_share else "  Subscription Spend Share: 0%")
    print()
    
    # Match products
    matches = match_products(db, user_id, persona.persona_type, features)
    
    print(f"Matched {len(matches)} products:")
    print()
    for i, match in enumerate(matches, 1):
        print(f"  {i}. {match['product_name']}")
        print(f"     Category: {match['category']}")
        print(f"     Relevance Score: {match['relevance_score']:.2f}")
        print(f"     Rationale: {match['rationale']}")
        print()
    
    # Verify subscription managers ranked high
    sub_mgr_matches = [m for m in matches if m['category'] == 'subscription_manager']
    if sub_mgr_matches:
        print(f"  ✓ Found {len(sub_mgr_matches)} subscription manager product(s)")
    else:
        print(f"  ⚠ No subscription manager products matched")
    print()


def test_wealth_builder_user(db):
    """Test product matching for wealth builder user"""
    print(f"\n{'='*60}")
    print("Wealth Builder User Test")
    print(f"{'='*60}")
    print()
    
    # Find user with wealth_builder persona
    persona = db.query(Persona).filter(
        Persona.persona_type == "wealth_builder",
        Persona.window_days == 30
    ).first()
    
    if not persona:
        print("  No wealth_builder user found in database")
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
    print(f"  Monthly Income: ${features.avg_monthly_income:.2f}" if features.avg_monthly_income else "  Monthly Income: $0.00")
    print(f"  Avg Utilization: {features.avg_utilization:.2%}" if features.avg_utilization else "  Avg Utilization: 0%")
    print(f"  Emergency Fund Months: {features.emergency_fund_months:.1f}" if features.emergency_fund_months else "  Emergency Fund Months: 0.0")
    print()
    
    # Match products
    matches = match_products(db, user_id, persona.persona_type, features)
    
    print(f"Matched {len(matches)} products:")
    print()
    for i, match in enumerate(matches, 1):
        print(f"  {i}. {match['product_name']}")
        print(f"     Category: {match['category']}")
        print(f"     Relevance Score: {match['relevance_score']:.2f}")
        print(f"     Rationale: {match['rationale']}")
        print()
    
    # Verify investment products ranked high
    investment_matches = [m for m in matches if m['category'] == 'robo_advisor']
    if investment_matches:
        print(f"  ✓ Found {len(investment_matches)} investment product(s)")
    else:
        print(f"  ⚠ No investment products matched")
    print()


def test_edge_case_no_matching_products(db):
    """Test edge case: user with no matching products"""
    print(f"\n{'='*60}")
    print("Edge Case: User with No Matching Products")
    print(f"{'='*60}")
    print()
    
    # Find a user with features but potentially no matching products
    # (e.g., user with very low scores)
    features = db.query(UserFeature).filter(
        UserFeature.window_days == 30
    ).first()
    
    if not features:
        print("  No user features found in database")
        return
    
    user_id = features.user_id
    persona = db.query(Persona).filter(
        Persona.user_id == user_id,
        Persona.window_days == 30
    ).first()
    
    if not persona:
        print(f"  User {user_id} has no persona assigned")
        return
    
    print(f"User ID: {user_id[:20]}...")
    print(f"  Persona: {persona.persona_type}")
    print()
    
    # Match products
    matches = match_products(db, user_id, persona.persona_type, features)
    
    if len(matches) == 0:
        print("  ✓ Correctly returned 0 products (all below relevance threshold)")
    else:
        print(f"  Matched {len(matches)} products (all above relevance threshold)")
        for match in matches:
            print(f"    - {match['product_name']}: {match['relevance_score']:.2f}")
    print()


def test_rationale_specificity(db):
    """Test that rationale text is specific and cites user data"""
    print(f"\n{'='*60}")
    print("Rationale Specificity Test")
    print(f"{'='*60}")
    print()
    
    # Test with a few different users
    personas = db.query(Persona).filter(
        Persona.window_days == 30
    ).limit(3).all()
    
    for persona in personas:
        user_id = persona.user_id
        features = db.query(UserFeature).filter(
            UserFeature.user_id == user_id,
            UserFeature.window_days == 30
        ).first()
        
        if not features:
            continue
        
        matches = match_products(db, user_id, persona.persona_type, features)
        
        if matches:
            print(f"User: {persona.persona_type}")
            print(f"  Top match: {matches[0]['product_name']}")
            print(f"  Rationale: {matches[0]['rationale']}")
            
            # Check if rationale contains specific numbers
            rationale = matches[0]['rationale']
            has_numbers = any(char.isdigit() for char in rationale)
            has_percent = '%' in rationale
            has_dollar = '$' in rationale
            
            if has_numbers or has_percent or has_dollar:
                print(f"  ✓ Rationale cites specific user data")
            else:
                print(f"  ⚠ Rationale may be too generic")
            print()


def main():
    """Run all product matching tests"""
    print("="*60)
    print("Product Matching Service Tests")
    print("="*60)
    
    # Create database connection
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if products exist
        product_count = db.query(ProductOffer).filter(ProductOffer.active == True).count()
        print(f"\nActive products in database: {product_count}")
        
        if product_count == 0:
            print("\n⚠ No active products found. Please run seed_product_catalog.py first.")
            return
        
        # Run tests
        test_high_utilization_user(db)
        test_savings_builder_user(db)
        test_variable_income_user(db)
        test_subscription_heavy_user(db)
        test_wealth_builder_user(db)
        test_edge_case_no_matching_products(db)
        test_rationale_specificity(db)
        
        print("="*60)
        print("All tests completed")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()

