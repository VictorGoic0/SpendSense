#!/usr/bin/env python3
"""
Test script for recommendation engine context builder

Tests the build_user_context function with multiple user IDs from the database.
Verifies all required fields are present and data looks realistic.
"""

import sys
import json
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

from app.services.recommendation_engine import build_user_context, validate_context
from app.models import User, UserFeature, Persona, Account, Transaction


def estimate_token_count(text: str) -> int:
    """
    Rough estimate of token count (1 token ≈ 4 characters for English text).
    
    Args:
        text: Text to estimate tokens for
    
    Returns:
        Estimated token count
    """
    return len(text) // 4


def test_context_builder(db, user_id: str, window_days: int):
    """Test context building for a specific user"""
    print(f"\n{'='*80}")
    print(f"Testing Context Builder")
    print(f"User ID: {user_id[:30]}...")
    print(f"Window: {window_days} days")
    print(f"{'='*80}\n")
    
    try:
        # Build context
        context = build_user_context(db, user_id, window_days)
        
        # Validate context
        is_valid = validate_context(context)
        
        if not is_valid:
            print("❌ Context validation FAILED")
            return False
        
        print("✅ Context validation PASSED\n")
        
        # Print context structure
        print("Context Structure:")
        print(f"  - user_id: {context['user_id']}")
        print(f"  - window_days: {context['window_days']}")
        print(f"  - persona_type: {context['persona_type']}")
        
        # Print subscription signals
        print(f"\n  Subscription Signals:")
        sub_signals = context['subscription_signals']
        print(f"    - recurring_merchants: {sub_signals['recurring_merchants']}")
        print(f"    - monthly_recurring_spend: ${sub_signals['monthly_recurring_spend']:.2f}")
        print(f"    - subscription_spend_share: {sub_signals['subscription_spend_share']:.2%}")
        
        # Print savings signals
        print(f"\n  Savings Signals:")
        sav_signals = context['savings_signals']
        print(f"    - net_savings_inflow: ${sav_signals['net_savings_inflow']:.2f}/month")
        print(f"    - savings_growth_rate: {sav_signals['savings_growth_rate']:.2%}")
        print(f"    - emergency_fund_months: {sav_signals['emergency_fund_months']:.2f} months")
        
        # Print credit signals
        print(f"\n  Credit Signals:")
        cred_signals = context['credit_signals']
        print(f"    - avg_utilization: {cred_signals['avg_utilization']:.2%}")
        print(f"    - max_utilization: {cred_signals['max_utilization']:.2%}")
        print(f"    - utilization_30_flag: {cred_signals['utilization_30_flag']}")
        print(f"    - utilization_50_flag: {cred_signals['utilization_50_flag']}")
        print(f"    - utilization_80_flag: {cred_signals['utilization_80_flag']}")
        print(f"    - minimum_payment_only_flag: {cred_signals['minimum_payment_only_flag']}")
        print(f"    - interest_charges_present: {cred_signals['interest_charges_present']}")
        print(f"    - any_overdue: {cred_signals['any_overdue']}")
        
        # Print income signals
        print(f"\n  Income Signals:")
        inc_signals = context['income_signals']
        print(f"    - payroll_detected: {inc_signals['payroll_detected']}")
        print(f"    - median_pay_gap_days: {inc_signals['median_pay_gap_days']}")
        print(f"    - income_variability: {inc_signals['income_variability']}")
        print(f"    - cash_flow_buffer_months: {inc_signals['cash_flow_buffer_months']:.2f} months")
        print(f"    - avg_monthly_income: ${inc_signals['avg_monthly_income']:.2f}")
        
        # Print accounts
        print(f"\n  Accounts ({len(context['accounts'])}):")
        for i, account in enumerate(context['accounts'][:5], 1):
            print(f"    {i}. {account['name']}")
            print(f"       Type: {account['type']}")
            print(f"       Balance: ${account['balance']:,.2f}")
            if 'limit' in account:
                print(f"       Limit: ${account['limit']:,.2f}")
        
        # Print recent transactions
        print(f"\n  Recent Transactions ({len(context['recent_transactions'])}):")
        for i, txn in enumerate(context['recent_transactions'][:5], 1):
            print(f"    {i}. {txn['date']} - {txn['merchant']}")
            print(f"       {txn['type']}: ${abs(txn['amount']):,.2f}")
        
        # Print high utilization cards if present
        if 'high_utilization_cards' in context:
            print(f"\n  High Utilization Credit Cards ({len(context['high_utilization_cards'])}):")
            for i, card in enumerate(context['high_utilization_cards'], 1):
                print(f"    {i}. Card ending in {card['last_4_digits']}")
                print(f"       Balance: ${card['current_balance']:,.2f}")
                print(f"       Limit: ${card['credit_limit']:,.2f}")
                print(f"       Utilization: {card['utilization_percentage']:.1f}%")
                if 'estimated_monthly_interest' in card:
                    print(f"       Est. Monthly Interest: ${card['estimated_monthly_interest']:.2f}")
        
        # Print recurring merchants if present
        if 'recurring_merchants' in context:
            print(f"\n  Recurring Merchants ({len(context['recurring_merchants'])}):")
            for merchant in context['recurring_merchants'][:5]:
                print(f"    - {merchant}")
        
        # Print savings accounts info if present
        if 'savings_accounts' in context:
            sav_info = context['savings_accounts']
            print(f"\n  Savings Accounts Info:")
            print(f"    - Count: {sav_info['count']}")
            print(f"    - Total Balance: ${sav_info['total_balance']:,.2f}")
            print(f"    - Growth Rate: {sav_info['growth_rate']:.2%}")
            print(f"    - Emergency Fund: {sav_info['emergency_fund_months']:.2f} months")
        
        # Convert to JSON and estimate token count
        context_json = json.dumps(context, indent=2)
        token_estimate = estimate_token_count(context_json)
        
        print(f"\n  Token Estimate: ~{token_estimate} tokens")
        if token_estimate > 2000:
            print(f"  ⚠️  Warning: Context exceeds 2000 token target (current: {token_estimate})")
        else:
            print(f"  ✅ Token count within target (<2000)")
        
        # Verify all required fields present
        required_fields = [
            "user_id",
            "window_days",
            "persona_type",
            "subscription_signals",
            "savings_signals",
            "credit_signals",
            "income_signals",
            "accounts",
            "recent_transactions",
        ]
        
        print(f"\n  Required Fields Check:")
        all_present = True
        for field in required_fields:
            if field in context:
                print(f"    ✅ {field}")
            else:
                print(f"    ❌ {field} - MISSING")
                all_present = False
        
        # Verify data looks realistic
        print(f"\n  Data Quality Checks:")
        
        # Check account balances are reasonable
        if context['accounts']:
            max_balance = max(acc['balance'] for acc in context['accounts'])
            if max_balance > 1000000:
                print(f"    ⚠️  Very high account balance detected: ${max_balance:,.2f}")
            else:
                print(f"    ✅ Account balances look reasonable")
        
        # Check transaction count
        if len(context['recent_transactions']) > 0:
            print(f"    ✅ Recent transactions present ({len(context['recent_transactions'])})")
        else:
            print(f"    ⚠️  No recent transactions found")
        
        # Check persona type is valid
        valid_personas = [
            'high_utilization',
            'variable_income',
            'subscription_heavy',
            'savings_builder',
            'wealth_builder'
        ]
        if context['persona_type'] in valid_personas or context['persona_type'] is None:
            print(f"    ✅ Persona type valid: {context['persona_type']}")
        else:
            print(f"    ⚠️  Unexpected persona type: {context['persona_type']}")
        
        return all_present
        
    except Exception as e:
        print(f"❌ Error building context: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function"""
    # Create database session
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("Recommendation Engine Context Builder Test")
        print("=" * 80)
        
        # Get users with personas assigned
        users_with_personas = db.query(User).join(Persona).filter(
            User.user_type == 'customer'
        ).distinct().limit(5).all()
        
        if not users_with_personas:
            print("\nNo users with personas found. Testing with any users...")
            users_with_personas = db.query(User).filter(
                User.user_type == 'customer'
            ).limit(5).all()
        
        if not users_with_personas:
            print("No users found in database. Please run data ingestion first.")
            return
        
        print(f"\nTesting context builder for {len(users_with_personas)} users...")
        
        # Test with 30-day window
        window_days = 30
        success_count = 0
        fail_count = 0
        
        for user in users_with_personas:
            try:
                # Check if user has features computed
                feature = db.query(UserFeature).filter(
                    UserFeature.user_id == user.user_id,
                    UserFeature.window_days == window_days
                ).first()
                
                if not feature:
                    print(f"\n⚠️  Skipping user {user.user_id[:20]}... (no features computed for {window_days}d window)")
                    continue
                
                success = test_context_builder(db, user.user_id, window_days)
                if success:
                    success_count += 1
                else:
                    fail_count += 1
                    
            except Exception as e:
                print(f"\n❌ Error testing user {user.user_id[:20]}...: {e}")
                fail_count += 1
        
        print("\n" + "=" * 80)
        print("Test Summary")
        print("=" * 80)
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {fail_count}")
        print(f"Total: {success_count + fail_count}")
        
        if fail_count == 0:
            print("\n✅ All tests passed!")
        else:
            print(f"\n⚠️  {fail_count} test(s) failed")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

