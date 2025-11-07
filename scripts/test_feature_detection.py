#!/usr/bin/env python3
"""
Test script for feature detection service - Subscription Signals

Tests the subscription detection logic with users from the database.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import SQLALCHEMY_DATABASE_URL
from app.services.feature_detection import compute_subscription_signals
from app.models import User, Transaction

def test_subscription_detection():
    """Test subscription detection with users from database"""
    
    # Create database session
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("Feature Detection Test - Subscription Signals")
        print("=" * 60)
        print()
        
        # Get all users
        users = db.query(User).filter(User.user_type == 'customer').limit(10).all()
        
        if not users:
            print("No users found in database. Please run data ingestion first.")
            return
        
        print(f"Testing subscription detection for {len(users)} users...")
        print()
        
        # Test both 30-day and 180-day windows
        windows = [30, 180]
        
        for window_days in windows:
            print(f"\n{'='*60}")
            print(f"Window: {window_days} days")
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
                    from app.services.feature_detection import get_transactions_in_window
                    transactions = get_transactions_in_window(db, user.user_id, window_days)
                    
                    # Group by merchant
                    from collections import defaultdict
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
        
        print("=" * 60)
        print("✅ Test completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    test_subscription_detection()

