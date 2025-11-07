#!/usr/bin/env python3
"""
Test script for persona assignment service

Tests the persona assignment logic with users from the database.
Verifies that personas are assigned correctly based on computed features.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Get the correct database path (backend/spendsense.db)
backend_dir = Path(__file__).parent.parent / "backend"
database_path = backend_dir / "spendsense.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{database_path.absolute()}"

from app.services.persona_assignment import (
    check_high_utilization,
    check_variable_income,
    check_subscription_heavy,
    check_savings_builder,
    check_wealth_builder,
    assign_persona,
    assign_and_save_persona,
    get_total_savings_balance
)
from app.models import User, UserFeature, Persona
import json


def test_persona_checks(db, user_features):
    """Test individual persona check functions"""
    print(f"\n{'='*60}")
    print("Persona Check Functions Test")
    print(f"{'='*60}")
    print()
    
    for feature in user_features:
        user = db.query(User).filter(User.user_id == feature.user_id).first()
        if not user:
            continue
        
        print(f"User: {user.full_name} ({feature.user_id[:20]}...)")
        print(f"  Window: {feature.window_days} days")
        
        # Test each check function
        high_util = check_high_utilization(feature)
        variable_inc = check_variable_income(feature)
        sub_heavy = check_subscription_heavy(feature)
        savings_build = check_savings_builder(feature)
        wealth_build = check_wealth_builder(db, feature)
        
        print(f"  High Utilization: {high_util}")
        print(f"  Variable Income: {variable_inc}")
        print(f"  Subscription Heavy: {sub_heavy}")
        print(f"  Savings Builder: {savings_build}")
        print(f"  Wealth Builder: {wealth_build}")
        
        # Show relevant feature values
        if high_util:
            print(f"    → Max utilization: {feature.max_utilization:.2%}")
            print(f"    → Interest charges: {feature.interest_charges_present}")
            print(f"    → Min payment only: {feature.minimum_payment_only_flag}")
            print(f"    → Overdue: {feature.any_overdue}")
        
        if variable_inc:
            print(f"    → Median pay gap: {feature.median_pay_gap_days} days")
            print(f"    → Cash flow buffer: {feature.cash_flow_buffer_months:.2f} months")
        
        if sub_heavy:
            print(f"    → Recurring merchants: {feature.recurring_merchants}")
            print(f"    → Monthly recurring spend: ${feature.monthly_recurring_spend:.2f}")
            print(f"    → Subscription spend share: {feature.subscription_spend_share:.2%}")
        
        if savings_build:
            print(f"    → Savings growth rate: {feature.savings_growth_rate:.2%}")
            print(f"    → Net savings inflow: ${feature.net_savings_inflow:.2f}")
            print(f"    → Avg utilization: {feature.avg_utilization:.2%}")
        
        if wealth_build:
            savings_balance = get_total_savings_balance(db, feature.user_id)
            print(f"    → Avg monthly income: ${feature.avg_monthly_income:,.2f}")
            print(f"    → Savings balance: ${savings_balance:,.2f}")
            print(f"    → Max utilization: {feature.max_utilization:.2%}")
            print(f"    → Investment accounts: {feature.investment_account_detected}")
        
        print()


def test_persona_assignment(db, user_features):
    """Test persona assignment logic"""
    print(f"\n{'='*60}")
    print("Persona Assignment Test")
    print(f"{'='*60}")
    print()
    
    persona_counts = {}
    
    for feature in user_features:
        user = db.query(User).filter(User.user_id == feature.user_id).first()
        if not user:
            continue
        
        # Assign persona
        persona_type, confidence, reasoning = assign_persona(
            db, feature.user_id, feature.window_days
        )
        
        # Count personas
        if persona_type not in persona_counts:
            persona_counts[persona_type] = 0
        persona_counts[persona_type] += 1
        
        print(f"User: {user.full_name} ({feature.user_id[:20]}...)")
        print(f"  Window: {feature.window_days} days")
        print(f"  Assigned Persona: {persona_type}")
        print(f"  Confidence: {confidence:.2f}")
        
        # Show reasoning
        if reasoning.get('matched_criteria'):
            print(f"  Matched Criteria:")
            for criterion in reasoning['matched_criteria']:
                print(f"    - {criterion}")
        
        if reasoning.get('all_matched_personas'):
            print(f"  All Matched Personas: {', '.join(reasoning['all_matched_personas'])}")
        
        print()


def test_persona_save(db, user_ids, window_days):
    """Test saving personas to database"""
    print(f"\n{'='*60}")
    print("Persona Save Test")
    print(f"{'='*60}")
    print()
    
    for user_id in user_ids[:5]:  # Test with first 5 users
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            continue
        
        print(f"User: {user.full_name} ({user_id[:20]}...)")
        
        # Assign and save persona
        persona = assign_and_save_persona(db, user_id, window_days)
        
        print(f"  Saved Persona: {persona.persona_type}")
        print(f"  Confidence: {persona.confidence_score:.2f}")
        print(f"  Assigned At: {persona.assigned_at}")
        
        # Parse and display reasoning
        if persona.reasoning:
            reasoning = json.loads(persona.reasoning)
            if reasoning.get('matched_criteria'):
                print(f"  Matched Criteria:")
                for criterion in reasoning['matched_criteria'][:3]:  # Show first 3
                    print(f"    - {criterion}")
        
        print()


def verify_persona_records(db, window_days):
    """Verify persona records in database"""
    print(f"\n{'='*60}")
    print(f"Persona Records Verification - Window: {window_days} days")
    print(f"{'='*60}")
    print()
    
    personas = db.query(Persona).filter(Persona.window_days == window_days).all()
    
    if not personas:
        print(f"No persona records found for {window_days}-day window")
        return
    
    persona_distribution = {}
    for persona in personas:
        if persona.persona_type not in persona_distribution:
            persona_distribution[persona.persona_type] = 0
        persona_distribution[persona.persona_type] += 1
    
    print(f"Total personas: {len(personas)}")
    print(f"\nPersona Distribution:")
    for persona_type, count in sorted(persona_distribution.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(personas)) * 100
        print(f"  {persona_type}: {count} ({percentage:.1f}%)")
    
    print()


def main():
    """Main test function"""
    # Create database session
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("Persona Assignment Test")
        print("=" * 60)
        print()
        
        # Get users with computed features
        user_features_30d = db.query(UserFeature).filter(
            UserFeature.window_days == 30
        ).limit(10).all()
        
        user_features_180d = db.query(UserFeature).filter(
            UserFeature.window_days == 180
        ).limit(10).all()
        
        if not user_features_30d and not user_features_180d:
            print("No user features found in database.")
            print("Please run feature computation first: python scripts/compute_all_features.py")
            return
        
        # Test persona checks
        if user_features_30d:
            print("\nTesting with 30-day window features...")
            test_persona_checks(db, user_features_30d)
        
        # Test persona assignment
        if user_features_30d:
            print("\nTesting persona assignment with 30-day window...")
            test_persona_assignment(db, user_features_30d)
        
        # Test saving personas
        if user_features_30d:
            user_ids = [f.user_id for f in user_features_30d]
            print("\nTesting persona save to database...")
            test_persona_save(db, user_ids, 30)
        
        # Verify persona records
        print("\nVerifying persona records in database...")
        verify_persona_records(db, 30)
        
        if user_features_180d:
            verify_persona_records(db, 180)
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

