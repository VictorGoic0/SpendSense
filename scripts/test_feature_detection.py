#!/usr/bin/env python3
"""
Test script for feature detection service - Subscription and Savings Signals

Tests the subscription and savings detection logic with users from the database.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import SQLALCHEMY_DATABASE_URL
from app.services.feature_detection import (
    compute_subscription_signals,
    compute_savings_signals,
    get_accounts_by_type,
    get_transactions_in_window
)
from app.models import User, Transaction, Account
from collections import defaultdict


def test_subscription_detection(db, users, window_days):
    """Test subscription detection with users from database"""
    print(f"\n{'='*60}")
    print(f"Subscription Signals - Window: {window_days} days")
    print(f"{'='*60}")
    print()
    
    for user in users:
        # Get transaction count for this user
        txn_count = db.query(Transaction).filter(
            Transaction.user_id == user.user_id
        ).count()
        
        if txn_count == 0:
            continue
        
        # Compute subscription signals
        signals = compute_subscription_signals(db, user.user_id, window_days)
        
        # Display results
        print(f"User: {user.full_name} ({user.user_id[:20]}...)")
        print(f"  Transactions in window: {txn_count}")
        print(f"  Recurring merchants: {signals['recurring_merchants']}")
        print(f"  Monthly recurring spend: ${signals['monthly_recurring_spend']:.2f}")
        print(f"  Subscription spend share: {signals['subscription_spend_share']:.2%}")
        
        # Show merchants if recurring detected
        if signals['recurring_merchants'] > 0:
            # Get transactions to find recurring merchants
            transactions = get_transactions_in_window(db, user.user_id, window_days)
            
            # Group by merchant
            merchant_counts = defaultdict(int)
            for txn in transactions:
                if txn.merchant_name:
                    merchant_counts[txn.merchant_name] += 1
            
            # Show merchants with 3+ transactions
            recurring_merchants_list = [
                (merchant, count) 
                for merchant, count in merchant_counts.items() 
                if count >= 3
            ]
            
            if recurring_merchants_list:
                print(f"  Recurring merchant examples:")
                for merchant, count in recurring_merchants_list[:5]:  # Show top 5
                    print(f"    - {merchant}: {count} transactions")
        
        print()


def test_savings_detection(db, users, window_days):
    """Test savings detection with users from database"""
    print(f"\n{'='*60}")
    print(f"Savings Signals - Window: {window_days} days")
    print(f"{'='*60}")
    print()
    
    users_with_savings = 0
    users_without_savings = 0
    
    for user in users:
        # Check if user has savings accounts
        savings_accounts = get_accounts_by_type(db, user.user_id, ['savings', 'money market', 'cash management', 'HSA'])
        
        # Compute savings signals
        signals = compute_savings_signals(db, user.user_id, window_days)
        
        # Display results
        print(f"User: {user.full_name} ({user.user_id[:20]}...)")
        
        if savings_accounts:
            users_with_savings += 1
            print(f"  Savings accounts: {len(savings_accounts)}")
            total_balance = sum(acc.balance_current or 0.0 for acc in savings_accounts)
            print(f"  Total savings balance: ${total_balance:,.2f}")
        else:
            users_without_savings += 1
            print(f"  Savings accounts: 0 (no savings accounts)")
        
        print(f"  Net savings inflow: ${signals['net_savings_inflow']:.2f}/month")
        print(f"  Savings growth rate: {signals['savings_growth_rate']:.2%}")
        print(f"  Emergency fund months: {signals['emergency_fund_months']:.2f}")
        
        # Validate calculations
        if savings_accounts and signals['net_savings_inflow'] != 0:
            print(f"  ✓ Net inflow calculated")
        if savings_accounts and signals['savings_growth_rate'] != 0:
            print(f"  ✓ Growth rate calculated")
        if signals['emergency_fund_months'] > 0:
            print(f"  ✓ Emergency fund calculated")
        
        print()
    
    print(f"Summary:")
    print(f"  Users with savings accounts: {users_with_savings}")
    print(f"  Users without savings accounts: {users_without_savings}")


def main():
    """Main test function"""
    # Create database session
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("Feature Detection Test - Subscription & Savings Signals")
        print("=" * 60)
        print()
        
        # Get all users
        users = db.query(User).filter(User.user_type == 'customer').limit(10).all()
        
        if not users:
            print("No users found in database. Please run data ingestion first.")
            return
        
        print(f"Testing feature detection for {len(users)} users...")
        
        # Test both 30-day and 180-day windows
        windows = [30, 180]
        
        for window_days in windows:
            print(f"\n{'='*80}")
            print(f"WINDOW: {window_days} DAYS")
            print(f"{'='*80}")
            
            # Test subscription detection
            test_subscription_detection(db, users, window_days)
            
            # Test savings detection
            test_savings_detection(db, users, window_days)
        
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
