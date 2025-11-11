#!/usr/bin/env python3
"""
Test script for feature detection service - Subscription and Savings Signals

Tests the subscription and savings detection logic with users from the database.
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

from app.services.feature_detection import (
    compute_subscription_signals,
    compute_savings_signals,
    compute_credit_signals,
    compute_income_signals,
    detect_investment_accounts,
    get_accounts_by_type,
    get_transactions_in_window
)
from app.models import User, Transaction, Account, Liability
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


def test_credit_detection(db, users, window_days):
    """Test credit detection with users from database"""
    print(f"\n{'='*60}")
    print(f"Credit Signals - Window: {window_days} days")
    print(f"{'='*60}")
    print()
    
    users_with_credit = 0
    users_without_credit = 0
    high_utilization_count = 0
    low_utilization_count = 0
    min_payment_only_count = 0
    overdue_count = 0
    
    for user in users:
        # Check if user has credit card accounts
        credit_accounts = get_accounts_by_type(db, user.user_id, ['credit card'])
        
        # Compute credit signals
        signals = compute_credit_signals(db, user.user_id, window_days)
        
        # Display results
        print(f"User: {user.full_name} ({user.user_id[:20]}...)")
        
        if credit_accounts:
            users_with_credit += 1
            print(f"  Credit card accounts: {len(credit_accounts)}")
            
            # Show account details
            for account in credit_accounts:
                balance = account.balance_current or 0.0
                limit = account.balance_limit or 0.0
                utilization = (balance / limit * 100) if limit > 0 else 0.0
                print(f"    - Account {account.account_id[:20]}...: ${balance:,.2f} / ${limit:,.2f} ({utilization:.1f}%)")
            
            # Show liability details
            liabilities = db.query(Liability).filter(
                Liability.user_id == user.user_id,
                Liability.liability_type == 'credit_card'
            ).all()
            
            if liabilities:
                print(f"  Liabilities: {len(liabilities)}")
                for liab in liabilities:
                    min_payment = liab.minimum_payment_amount or 0.0
                    last_payment = liab.last_payment_amount or 0.0
                    overdue = "Yes" if liab.is_overdue else "No"
                    print(f"    - Min payment: ${min_payment:.2f}, Last payment: ${last_payment:.2f}, Overdue: {overdue}")
        else:
            users_without_credit += 1
            print(f"  Credit card accounts: 0 (no credit cards)")
        
        print(f"  Average utilization: {signals['avg_utilization']:.2%}")
        print(f"  Max utilization: {signals['max_utilization']:.2%}")
        print(f"  Utilization flags:")
        print(f"    - ≥30%: {signals['utilization_30_flag']}")
        print(f"    - ≥50%: {signals['utilization_50_flag']}")
        print(f"    - ≥80%: {signals['utilization_80_flag']}")
        print(f"  Minimum payment only: {signals['minimum_payment_only_flag']}")
        print(f"  Interest charges present: {signals['interest_charges_present']}")
        print(f"  Any overdue: {signals['any_overdue']}")
        
        # Track statistics
        if signals['max_utilization'] > 0.50:
            high_utilization_count += 1
        elif signals['max_utilization'] > 0 and signals['max_utilization'] < 0.30:
            low_utilization_count += 1
        
        if signals['minimum_payment_only_flag']:
            min_payment_only_count += 1
        
        if signals['any_overdue']:
            overdue_count += 1
        
        print()
    
    print(f"Summary:")
    print(f"  Users with credit cards: {users_with_credit}")
    print(f"  Users without credit cards: {users_without_credit}")
    print(f"  Users with high utilization (>50%): {high_utilization_count}")
    print(f"  Users with low utilization (<30%): {low_utilization_count}")
    print(f"  Users making minimum payments only: {min_payment_only_count}")
    print(f"  Users with overdue accounts: {overdue_count}")


def test_income_detection(db, users, window_days):
    """Test income detection with users from database"""
    print(f"\n{'='*60}")
    print(f"Income Signals - Window: {window_days} days")
    print(f"{'='*60}")
    print()
    
    users_with_payroll = 0
    users_without_payroll = 0
    regular_income_count = 0
    irregular_income_count = 0
    high_variability_count = 0
    low_buffer_count = 0
    
    for user in users:
        # Compute income signals
        signals = compute_income_signals(db, user.user_id, window_days)
        
        # Detect investment accounts
        has_investments = detect_investment_accounts(db, user.user_id)
        
        # Display results
        print(f"User: {user.full_name} ({user.user_id[:20]}...)")
        print(f"  Payroll detected: {signals['payroll_detected']}")
        
        if signals['payroll_detected']:
            users_with_payroll += 1
            print(f"  Median pay gap: {signals['median_pay_gap_days']} days")
            print(f"  Income variability: {signals['income_variability']:.3f}")
            print(f"  Average monthly income: ${signals['avg_monthly_income']:,.2f}")
            print(f"  Cash flow buffer: {signals['cash_flow_buffer_months']:.2f} months")
            
            # Track statistics
            if signals['median_pay_gap_days']:
                if 13 <= signals['median_pay_gap_days'] <= 15:
                    regular_income_count += 1  # Biweekly (~14 days)
                elif signals['median_pay_gap_days'] > 20 or signals['median_pay_gap_days'] < 10:
                    irregular_income_count += 1
            
            if signals['income_variability'] > 0.2:
                high_variability_count += 1
            
            if signals['cash_flow_buffer_months'] < 1.0:
                low_buffer_count += 1
        else:
            users_without_payroll += 1
            print(f"  No payroll detected (<2 payroll transactions)")
        
        print(f"  Investment accounts: {'Yes' if has_investments else 'No'}")
        print()
    
    print(f"Summary:")
    print(f"  Users with payroll detected: {users_with_payroll}")
    print(f"  Users without payroll: {users_without_payroll}")
    print(f"  Users with regular biweekly income: {regular_income_count}")
    print(f"  Users with irregular income: {irregular_income_count}")
    print(f"  Users with high income variability (>0.2): {high_variability_count}")
    print(f"  Users with low cash flow buffer (<1 month): {low_buffer_count}")


def main():
    """Main test function"""
    # Create database session
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("Feature Detection Test - Subscription, Savings, Credit & Income Signals")
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
            
            # Test credit detection
            test_credit_detection(db, users, window_days)
            
            # Test income detection
            test_income_detection(db, users, window_days)
        
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
