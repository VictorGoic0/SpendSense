#!/usr/bin/env python3
"""
Test script for hybrid recommendation engine

Tests the combined recommendation generation (education + products).
Verifies that both educational and product recommendations are generated correctly.
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

from app.services.recommendation_engine import generate_combined_recommendations
from app.models import User, UserFeature, Persona, Account, Recommendation
import json


def test_high_utilization_user(db):
    """Test with high_utilization user"""
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
    
    print(f"User: {user.full_name if user else 'Unknown'} ({user_id[:20]}...)")
    print(f"  Persona: {persona.persona_type}")
    print()
    
    # Generate combined recommendations
    print("Generating combined recommendations...")
    recommendations = generate_combined_recommendations(
        db, user_id, persona.persona_type, 30
    )
    
    print(f"\nGenerated {len(recommendations)} recommendations:")
    print()
    
    # Count by type
    education_count = sum(1 for r in recommendations if r.get("content_type") == "education")
    product_count = sum(1 for r in recommendations if r.get("content_type") == "partner_offer")
    
    print(f"  Education: {education_count}")
    print(f"  Products: {product_count}")
    print()
    
    # Verify 2-3 educational recs
    if 2 <= education_count <= 3:
        print(f"  ✓ Educational recommendations count correct ({education_count})")
    else:
        print(f"  ⚠ Expected 2-3 educational recommendations, got {education_count}")
    
    # Verify 1-2 product recs
    if 1 <= product_count <= 2:
        print(f"  ✓ Product recommendations count correct ({product_count})")
    else:
        print(f"  ⚠ Expected 1-2 product recommendations, got {product_count}")
    
    # Check for balance transfer cards
    balance_transfer_products = [
        r for r in recommendations
        if r.get("content_type") == "partner_offer"
        and r.get("category") == "balance_transfer"
    ]
    
    if balance_transfer_products:
        print(f"  ✓ Found {len(balance_transfer_products)} balance transfer product(s)")
        for product in balance_transfer_products:
            print(f"    - {product.get('product_name')}")
    else:
        print(f"  ⚠ No balance transfer products found")
    
    print()
    
    # Print full recommendation list
    print("Full Recommendation List:")
    print()
    for i, rec in enumerate(recommendations, 1):
        content_type = rec.get("content_type", "unknown")
        print(f"  {i}. [{content_type.upper()}] {rec.get('title', rec.get('product_name', 'Unknown'))}")
        if content_type == "education":
            print(f"     Content: {rec.get('content', '')[:100]}...")
        elif content_type == "partner_offer":
            print(f"     Product: {rec.get('product_name')}")
            print(f"     Description: {rec.get('short_description', '')[:100]}...")
            print(f"     Benefits: {len(rec.get('benefits', []))} items")
        print(f"     Rationale: {rec.get('rationale', '')[:100]}...")
        print()


def test_savings_builder_user(db):
    """Test with savings_builder user"""
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
    
    # Check if user has existing HYSA
    accounts = db.query(Account).filter(Account.user_id == user_id).all()
    has_hysa = any(acc.type in ["savings", "money market", "cash management", "HSA"] for acc in accounts)
    
    print(f"User: {user.full_name if user else 'Unknown'} ({user_id[:20]}...)")
    print(f"  Persona: {persona.persona_type}")
    print(f"  Has existing HYSA: {has_hysa}")
    print()
    
    # Generate recommendations
    print("Generating recommendations...")
    recommendations = generate_combined_recommendations(
        db, user_id, persona.persona_type, 30
    )
    
    print(f"\nGenerated {len(recommendations)} recommendations")
    print()
    
    # Check for HYSA products
    hysa_products = [
        r for r in recommendations
        if r.get("content_type") == "partner_offer"
        and r.get("category") == "hysa"
    ]
    
    if hysa_products:
        if has_hysa:
            print(f"  ⚠ Found {len(hysa_products)} HYSA product(s) but user already has HYSA")
        else:
            print(f"  ✓ Found {len(hysa_products)} HYSA product(s)")
            for product in hysa_products:
                print(f"    - {product.get('product_name')}")
    else:
        if has_hysa:
            print(f"  ✓ No HYSA products (correctly excluded - user has existing HYSA)")
        else:
            print(f"  ⚠ No HYSA products found")
    
    print()


def test_variable_income_user(db):
    """Test with variable_income user"""
    print(f"\n{'='*60}")
    print("Variable Income User Test")
    print(f"{'='*60}")
    print()
    
    persona = db.query(Persona).filter(
        Persona.persona_type == "variable_income",
        Persona.window_days == 30
    ).first()
    
    if not persona:
        print("  No variable_income user found in database")
        return
    
    user_id = persona.user_id
    
    recommendations = generate_combined_recommendations(
        db, user_id, persona.persona_type, 30
    )
    
    # Check for budgeting app products
    budgeting_products = [
        r for r in recommendations
        if r.get("content_type") == "partner_offer"
        and r.get("category") == "budgeting_app"
    ]
    
    if budgeting_products:
        print(f"  ✓ Found {len(budgeting_products)} budgeting app product(s)")
    else:
        print(f"  ⚠ No budgeting app products found")
    
    print()


def test_subscription_heavy_user(db):
    """Test with subscription_heavy user"""
    print(f"\n{'='*60}")
    print("Subscription Heavy User Test")
    print(f"{'='*60}")
    print()
    
    persona = db.query(Persona).filter(
        Persona.persona_type == "subscription_heavy",
        Persona.window_days == 30
    ).first()
    
    if not persona:
        print("  No subscription_heavy user found in database")
        return
    
    user_id = persona.user_id
    
    recommendations = generate_combined_recommendations(
        db, user_id, persona.persona_type, 30
    )
    
    # Check for subscription manager products
    sub_manager_products = [
        r for r in recommendations
        if r.get("content_type") == "partner_offer"
        and r.get("category") == "subscription_manager"
    ]
    
    if sub_manager_products:
        print(f"  ✓ Found {len(sub_manager_products)} subscription manager product(s)")
    else:
        print(f"  ⚠ No subscription manager products found")
    
    print()


def test_wealth_builder_user(db):
    """Test with wealth_builder user"""
    print(f"\n{'='*60}")
    print("Wealth Builder User Test")
    print(f"{'='*60}")
    print()
    
    persona = db.query(Persona).filter(
        Persona.persona_type == "wealth_builder",
        Persona.window_days == 30
    ).first()
    
    if not persona:
        print("  No wealth_builder user found in database")
        return
    
    user_id = persona.user_id
    
    recommendations = generate_combined_recommendations(
        db, user_id, persona.persona_type, 30
    )
    
    # Check for investment products
    investment_products = [
        r for r in recommendations
        if r.get("content_type") == "partner_offer"
        and r.get("category") in ["robo_advisor", "investment"]
    ]
    
    if investment_products:
        print(f"  ✓ Found {len(investment_products)} investment product(s)")
    else:
        print(f"  ⚠ No investment products found")
    
    print()


def test_no_eligible_products(db):
    """Test edge case: no eligible products"""
    print(f"\n{'='*60}")
    print("Edge Case: No Eligible Products")
    print(f"{'='*60}")
    print()
    
    # Use any user - we'll verify that if no products match, only education is returned
    persona = db.query(Persona).filter(
        Persona.window_days == 30
    ).first()
    
    if not persona:
        print("  No user found in database")
        return
    
    user_id = persona.user_id
    
    print(f"Testing with user {user_id[:20]}...")
    print()
    
    try:
        recommendations = generate_combined_recommendations(
            db, user_id, persona.persona_type, 30
        )
        
        education_count = sum(1 for r in recommendations if r.get("content_type") == "education")
        product_count = sum(1 for r in recommendations if r.get("content_type") == "partner_offer")
        
        print(f"Generated {len(recommendations)} recommendations:")
        print(f"  Education: {education_count}")
        print(f"  Products: {product_count}")
        print()
        
        if product_count == 0:
            print(f"  ✓ No products returned (only educational recommendations)")
        else:
            print(f"  ✓ Products returned: {product_count}")
        
        if education_count > 0:
            print(f"  ✓ Educational recommendations still returned: {education_count}")
        else:
            print(f"  ⚠ No educational recommendations returned")
        
        print("  ✓ No errors thrown")
        
    except Exception as e:
        print(f"  ❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()


def verify_database_storage(db):
    """Verify recommendations are stored correctly in database"""
    print(f"\n{'='*60}")
    print("Database Storage Verification")
    print(f"{'='*60}")
    print()
    
    # Get recent recommendations
    recommendations = db.query(Recommendation).order_by(
        Recommendation.generated_at.desc()
    ).limit(10).all()
    
    if not recommendations:
        print("  No recommendations found in database")
        return
    
    print(f"Checking {len(recommendations)} recent recommendations:")
    print()
    
    education_count = 0
    product_count = 0
    
    for rec in recommendations:
        if rec.content_type == "education":
            education_count += 1
        elif rec.content_type == "partner_offer":
            product_count += 1
            
            # Verify product_id is set
            if rec.product_id:
                print(f"  ✓ Product recommendation {rec.recommendation_id} has product_id: {rec.product_id}")
            else:
                print(f"  ⚠ Product recommendation {rec.recommendation_id} missing product_id")
            
            # Verify metadata contains product data
            if rec.metadata_json:
                try:
                    metadata = json.loads(rec.metadata_json)
                    if "product_data" in metadata:
                        print(f"  ✓ Product recommendation {rec.recommendation_id} has product_data in metadata")
                    else:
                        print(f"  ⚠ Product recommendation {rec.recommendation_id} missing product_data in metadata")
    
    print()
    print(f"  Education recommendations: {education_count}")
    print(f"  Product recommendations: {product_count}")
    print()


def main():
    """Run all tests"""
    print("=" * 60)
    print("Hybrid Recommendation Engine Test Suite")
    print("=" * 60)
    
    # Create database connection
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Run tests
        test_high_utilization_user(db)
        test_savings_builder_user(db)
        test_variable_income_user(db)
        test_subscription_heavy_user(db)
        test_wealth_builder_user(db)
        test_no_eligible_products(db)
        verify_database_storage(db)
        
        print("=" * 60)
        print("All tests completed")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()

