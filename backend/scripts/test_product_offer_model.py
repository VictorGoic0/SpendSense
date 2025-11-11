#!/usr/bin/env python3
"""Test script to verify ProductOffer model creation and queries"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.database import SessionLocal, init_db
from backend.app.models import ProductOffer

def test_model_creation():
    """Test that ProductOffer model can be created and queried"""
    print("=" * 60)
    print("Testing ProductOffer Model")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    print("   ✓ Database initialized")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Test 1: Create a sample product
        print("\n2. Creating sample product...")
        sample_product = ProductOffer(
            product_id="test_prod_001",
            product_name="Test High-Yield Savings Account",
            product_type="savings_account",
            category="hysa",
            persona_targets=json.dumps(["savings_builder", "wealth_builder"]),
            short_description="A test high-yield savings account for testing",
            benefits=json.dumps([
                "4.5% APY on all balances",
                "No monthly fees",
                "FDIC insured up to $250,000"
            ]),
            typical_apy_or_fee="4.5% APY",
            partner_link="https://example.com/test",
            disclosure="This is educational content, not financial advice. Product terms, rates, and availability subject to change. SpendSense may receive compensation from partners. Consult a licensed financial advisor for personalized guidance.",
            partner_name="Test Bank",
            min_income=0.0,
            max_credit_utilization=1.0,
            requires_no_existing_savings=False,
            requires_no_existing_investment=False,
            min_credit_score=None,
            commission_rate=0.0,
            priority=1,
            active=True
        )
        
        db.add(sample_product)
        db.commit()
        print("   ✓ Sample product created and committed")
        
        # Test 2: Query the product
        print("\n3. Querying product...")
        queried_product = db.query(ProductOffer).filter(ProductOffer.product_id == "test_prod_001").first()
        
        if queried_product:
            print(f"   ✓ Product found: {queried_product.product_name}")
            print(f"   ✓ Product type: {queried_product.product_type}")
            print(f"   ✓ Category: {queried_product.category}")
            print(f"   ✓ Active: {queried_product.active}")
            print(f"   ✓ Created at: {queried_product.created_at}")
        else:
            print("   ✗ Product not found!")
            return False
        
        # Test 3: Query by active status
        print("\n4. Querying active products...")
        active_products = db.query(ProductOffer).filter(ProductOffer.active == True).all()
        print(f"   ✓ Found {len(active_products)} active product(s)")
        
        # Test 4: Query by product type
        print("\n5. Querying by product type...")
        savings_accounts = db.query(ProductOffer).filter(ProductOffer.product_type == "savings_account").all()
        print(f"   ✓ Found {len(savings_accounts)} savings account(s)")
        
        # Test 5: Parse JSON fields
        print("\n6. Testing JSON field parsing...")
        persona_list = json.loads(queried_product.persona_targets)
        benefits_list = json.loads(queried_product.benefits)
        print(f"   ✓ Persona targets: {persona_list}")
        print(f"   ✓ Benefits count: {len(benefits_list)}")
        
        # Test 6: Test __repr__ method
        print("\n7. Testing __repr__ method...")
        repr_str = repr(queried_product)
        print(f"   ✓ __repr__: {repr_str}")
        
        # Cleanup: Delete test product
        print("\n8. Cleaning up test data...")
        db.delete(queried_product)
        db.commit()
        print("   ✓ Test product deleted")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_model_creation()
    sys.exit(0 if success else 1)

