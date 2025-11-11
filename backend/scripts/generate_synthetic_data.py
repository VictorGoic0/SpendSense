"""
Synthetic Data Generation Script for SpendSense

This script generates realistic synthetic financial data for testing and development.
The output is saved as JSON files that can be used as seed data for both local
SQLite databases and production databases.

Data Generation Assumptions:
- Users: 71 customers (95%) and 4 operators (5%)
- Consent: 30% of users have consent_status=True
- Accounts: Each user has 2-4 accounts (checking, savings, credit cards, investments)
- Transactions: 150-300 transactions per user over 180-day window
- Persona Patterns: Distributed across users to create realistic behavioral signals
  - High credit card usage
  - Recurring subscriptions
  - Regular savings deposits
  - Irregular income patterns
  - Regular biweekly payroll
- Credit Utilization: 20% high (>50%), 30% medium (30-50%), 50% low (<30%)

Output Files:
- backend/data/synthetic_users.json: User records
- backend/data/synthetic_accounts.json: Account records
- backend/data/synthetic_transactions.json: Transaction records
- backend/data/synthetic_liabilities.json: Credit card liability records
"""
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from faker import Faker

# Set random seed for reproducibility
random.seed(42)

# Initialize Faker instance
fake = Faker()


def generate_users(count=75):
    """
    Generate synthetic user data.
    
    Args:
        count: Total number of users to generate (default: 75)
    
    Returns:
        List of user dictionaries
    """
    users = []
    emails = set()  # Track emails to ensure uniqueness
    
    # Calculate date range (6 months ago to now)
    now = datetime.now()
    six_months_ago = now - timedelta(days=180)
    
    # Generate 71 customers (95%) and 4 operators (5%)
    num_customers = 71
    num_operators = 4
    
    # Generate customers
    for i in range(num_customers):
        # Generate unique email
        email = fake.email()
        while email in emails:
            email = fake.email()
        emails.add(email)
        
        # Generate created_at (random date in last 6 months)
        days_ago = random.randint(0, 180)
        created_at = (now - timedelta(days=days_ago)).isoformat()
        
        # Generate consent_status (30% True, 70% False)
        consent_status = random.random() < 0.3
        
        # Generate consent_granted_at if consent_status is True
        consent_granted_at = None
        if consent_status:
            # Random recent date (within last 30 days)
            days_ago_consent = random.randint(0, 30)
            consent_granted_at = (now - timedelta(days=days_ago_consent)).isoformat()
        
        user = {
            'user_id': f'usr_{uuid.uuid4()}',
            'full_name': fake.name(),
            'email': email,
            'created_at': created_at,
            'consent_status': consent_status,
            'consent_granted_at': consent_granted_at,
            'user_type': 'customer'
        }
        users.append(user)
    
    # Generate operators
    for i in range(num_operators):
        # Generate unique email
        email = fake.email()
        while email in emails:
            email = fake.email()
        emails.add(email)
        
        # Generate created_at (random date in last 6 months)
        days_ago = random.randint(0, 180)
        created_at = (now - timedelta(days=days_ago)).isoformat()
        
        # Generate consent_status (30% True, 70% False)
        consent_status = random.random() < 0.3
        
        # Generate consent_granted_at if consent_status is True
        consent_granted_at = None
        if consent_status:
            # Random recent date (within last 30 days)
            days_ago_consent = random.randint(0, 30)
            consent_granted_at = (now - timedelta(days=days_ago_consent)).isoformat()
        
        user = {
            'user_id': f'usr_{uuid.uuid4()}',
            'full_name': fake.name(),
            'email': email,
            'created_at': created_at,
            'consent_status': consent_status,
            'consent_granted_at': consent_granted_at,
            'user_type': 'operator'
        }
        users.append(user)
    
    return users


def generate_accounts(users):
    """
    Generate synthetic account data for users.
    
    Args:
        users: List of user dictionaries
    
    Returns:
        List of account dictionaries
    """
    accounts = []
    now = datetime.now()
    
    # Account type definitions with subtypes
    account_types = {
        'checking': ['checking', 'premium checking'],
        'savings': ['savings', 'high yield savings'],
        'credit card': ['visa', 'mastercard', 'amex', 'discover'],
        'brokerage': ['brokerage'],
        '401k': ['401k'],
        'ira': ['ira', 'roth ira']
    }
    
    for user in users:
        user_id = user['user_id']
        user_accounts = []
        
        # Determine if user is high-income (for investment account probability)
        # We'll use a simple heuristic: random 20% of users are "high-income"
        is_high_income = random.random() < 0.2
        
        # 1-2 checking accounts (100% of users)
        num_checking = random.randint(1, 2)
        for i in range(num_checking):
            subtype = random.choice(account_types['checking'])
            days_ago = random.randint(0, 180)
            created_at = (now - timedelta(days=days_ago)).isoformat()
            
            # Realistic checking balance: $500-$10,000
            balance = round(random.uniform(500, 10000), 2)
            
            account = {
                'account_id': f'acc_{uuid.uuid4()}',
                'user_id': user_id,
                'type': 'checking',
                'subtype': subtype,
                'balance_available': balance,
                'balance_current': balance,
                'balance_limit': None,
                'iso_currency_code': 'USD',
                'holder_category': 'personal',
                'created_at': created_at
            }
            user_accounts.append(account)
        
        # 0-1 savings account (60% probability)
        if random.random() < 0.6:
            subtype = random.choice(account_types['savings'])
            days_ago = random.randint(0, 180)
            created_at = (now - timedelta(days=days_ago)).isoformat()
            
            # Realistic savings balance: $1,000-$50,000
            balance = round(random.uniform(1000, 50000), 2)
            
            account = {
                'account_id': f'acc_{uuid.uuid4()}',
                'user_id': user_id,
                'type': 'savings',
                'subtype': subtype,
                'balance_available': balance,
                'balance_current': balance,
                'balance_limit': None,
                'iso_currency_code': 'USD',
                'holder_category': 'personal',
                'created_at': created_at
            }
            user_accounts.append(account)
        
        # 0-2 credit cards (80% probability, varied limits $1k-$50k)
        if random.random() < 0.8:
            num_credit_cards = random.randint(1, 2)
            for i in range(num_credit_cards):
                subtype = random.choice(account_types['credit card'])
                days_ago = random.randint(0, 180)
                created_at = (now - timedelta(days=days_ago)).isoformat()
                
                # Credit limit: $1k-$50k
                balance_limit = round(random.uniform(1000, 50000), 2)
                
                # Current balance: 0-80% of limit (varied utilization)
                utilization = random.uniform(0, 0.8)
                balance_current = round(balance_limit * utilization, 2)
                balance_available = round(balance_limit - balance_current, 2)
                
                account = {
                    'account_id': f'acc_{uuid.uuid4()}',
                    'user_id': user_id,
                    'type': 'credit card',
                    'subtype': subtype,
                    'balance_available': balance_available,
                    'balance_current': balance_current,
                    'balance_limit': balance_limit,
                    'iso_currency_code': 'USD',
                    'holder_category': 'personal',
                    'created_at': created_at
                }
                user_accounts.append(account)
        
        # 0-1 investment account (30% probability, higher for high-income users)
        investment_probability = 0.5 if is_high_income else 0.3
        if random.random() < investment_probability:
            # Choose investment type: brokerage (60%), 401k (30%), ira (10%)
            investment_type_roll = random.random()
            if investment_type_roll < 0.6:
                account_type = 'brokerage'
                subtype = random.choice(account_types['brokerage'])
                # Brokerage balance: $5k-$200k
                balance = round(random.uniform(5000, 200000), 2)
            elif investment_type_roll < 0.9:
                account_type = '401k'
                subtype = random.choice(account_types['401k'])
                # 401k balance: $10k-$500k
                balance = round(random.uniform(10000, 500000), 2)
            else:
                account_type = 'ira'
                subtype = random.choice(account_types['ira'])
                # IRA balance: $5k-$300k
                balance = round(random.uniform(5000, 300000), 2)
            
            days_ago = random.randint(0, 180)
            created_at = (now - timedelta(days=days_ago)).isoformat()
            
            account = {
                'account_id': f'acc_{uuid.uuid4()}',
                'user_id': user_id,
                'type': account_type,
                'subtype': subtype,
                'balance_available': balance,
                'balance_current': balance,
                'balance_limit': None,
                'iso_currency_code': 'USD',
                'holder_category': 'personal',
                'created_at': created_at
            }
            user_accounts.append(account)
        
        accounts.extend(user_accounts)
    
    return accounts


def generate_transactions(users, accounts):
    """
    Generate synthetic transaction data for users and accounts.
    
    Args:
        users: List of user dictionaries
        accounts: List of account dictionaries
    
    Returns:
        List of transaction dictionaries
    """
    transactions = []
    now = datetime.now()
    start_date = now - timedelta(days=180)
    
    # Define merchant categories with sample merchants
    merchant_categories = {
        'groceries': ['Whole Foods', 'Trader Joe\'s', 'Safeway', 'Kroger'],
        'subscriptions': ['Netflix', 'Spotify', 'Adobe', 'GitHub', 'Peloton', 'Apple', 'Amazon Prime'],
        'restaurants': ['Chipotle', 'Starbucks', 'McDonald\'s', 'Local Restaurant'],
        'gas': ['Shell', 'Chevron', 'BP'],
        'utilities': ['PG&E', 'AT&T', 'Comcast'],
        'shopping': ['Amazon', 'Target', 'Walmart', 'Best Buy'],
        'payroll': []  # Will be generated dynamically with employer names
    }
    
    # Create account lookup by user_id
    accounts_by_user = {}
    credit_cards_by_user = {}
    checking_accounts_by_user = {}
    savings_accounts_by_user = {}
    
    for account in accounts:
        user_id = account['user_id']
        if user_id not in accounts_by_user:
            accounts_by_user[user_id] = []
            credit_cards_by_user[user_id] = []
            checking_accounts_by_user[user_id] = []
            savings_accounts_by_user[user_id] = []
        
        accounts_by_user[user_id].append(account)
        
        if account['type'] == 'credit card':
            credit_cards_by_user[user_id].append(account)
        elif account['type'] == 'checking':
            checking_accounts_by_user[user_id].append(account)
        elif account['type'] == 'savings':
            savings_accounts_by_user[user_id].append(account)
    
    # Assign persona patterns to users
    # We'll create variety in transaction patterns
    for user in users:
        if user['user_type'] != 'customer':
            continue  # Skip operators
        
        user_id = user['user_id']
        user_accounts = accounts_by_user.get(user_id, [])
        
        if not user_accounts:
            continue
        
        # Assign persona pattern (randomly distributed)
        persona_pattern = random.choice([
            'high_credit_usage',
            'recurring_subscriptions',
            'regular_savings',
            'irregular_income',
            'regular_biweekly_income',
            'normal'
        ])
        
        # Generate 150-300 transactions per user
        num_transactions = random.randint(150, 300)
        
        # Track recurring merchants for subscription pattern
        recurring_merchants = {}
        
        # Track payroll dates for income patterns
        payroll_dates = []
        
        # Generate transactions
        for i in range(num_transactions):
            # Random date within 180-day window
            days_offset = random.randint(0, 180)
            transaction_date = start_date + timedelta(days=days_offset)
            
            # Select account based on persona pattern
            if persona_pattern == 'high_credit_usage' and credit_cards_by_user.get(user_id):
                # Prefer credit cards
                account = random.choice(credit_cards_by_user[user_id]) if random.random() < 0.7 else random.choice(user_accounts)
            elif persona_pattern == 'regular_savings' and savings_accounts_by_user.get(user_id):
                # Mix of checking and savings
                account = random.choice(savings_accounts_by_user[user_id]) if random.random() < 0.3 else random.choice(checking_accounts_by_user[user_id])
            else:
                # Default: prefer checking accounts
                if checking_accounts_by_user.get(user_id):
                    account = random.choice(checking_accounts_by_user[user_id])
                else:
                    account = random.choice(user_accounts)
            
            # Determine transaction type (expense or income)
            is_income = False
            
            # Handle payroll deposits
            if persona_pattern == 'regular_biweekly_income':
                # Generate biweekly payroll (every 14 days)
                if not payroll_dates:
                    # First payroll date
                    first_payroll = start_date + timedelta(days=random.randint(0, 13))
                    payroll_dates.append(first_payroll)
                
                # Check if we should add a payroll transaction
                if random.random() < 0.1:  # ~10% chance per transaction
                    is_income = True
                    employer_name = fake.company()
                    merchant_name = f"PAYROLL DEPOSIT - {employer_name}"
                    category_primary = 'income'
                    category_detailed = 'payroll'
                    amount = round(random.uniform(2000, 6000), 2)
                    payment_channel = 'ACH'
            elif persona_pattern == 'irregular_income':
                # Irregular payroll deposits
                if random.random() < 0.05:  # ~5% chance per transaction
                    is_income = True
                    employer_name = fake.company()
                    merchant_name = f"PAYROLL DEPOSIT - {employer_name}"
                    category_primary = 'income'
                    category_detailed = 'payroll'
                    amount = round(random.uniform(1500, 8000), 2)  # More variable
                    payment_channel = 'ACH'
            elif persona_pattern == 'regular_savings':
                # Regular savings deposits
                if random.random() < 0.03 and account['type'] == 'savings':  # ~3% chance, only for savings accounts
                    is_income = True
                    merchant_name = "TRANSFER FROM CHECKING"
                    category_primary = 'transfer'
                    category_detailed = 'savings_deposit'
                    amount = round(random.uniform(200, 500), 2)
                    payment_channel = 'ACH'
            
            # Handle recurring subscriptions
            if persona_pattern == 'recurring_subscriptions' and not is_income:
                # 30% chance of subscription transaction
                if random.random() < 0.3:
                    merchant_name = random.choice(merchant_categories['subscriptions'])
                    category_primary = 'subscriptions'
                    category_detailed = 'recurring_subscription'
                    
                    # Track recurring merchants
                    if merchant_name not in recurring_merchants:
                        recurring_merchants[merchant_name] = []
                    recurring_merchants[merchant_name].append(transaction_date)
                    
                    amount = round(random.uniform(5, 50), 2)
                    payment_channel = random.choice(['online', 'ACH'])
            
            # Generate regular expense transactions
            if not is_income:
                # Select category
                category_weights = {
                    'groceries': 0.25,
                    'restaurants': 0.20,
                    'gas': 0.10,
                    'utilities': 0.08,
                    'shopping': 0.15,
                    'subscriptions': 0.12,
                    'other': 0.10
                }
                
                category_roll = random.random()
                cumulative = 0
                selected_category = 'other'
                
                for cat, weight in category_weights.items():
                    cumulative += weight
                    if category_roll <= cumulative:
                        selected_category = cat
                        break
                
                if selected_category == 'groceries':
                    merchant_name = random.choice(merchant_categories['groceries'])
                    category_primary = 'groceries'
                    category_detailed = 'grocery_store'
                    amount = round(random.uniform(30, 200), 2)
                elif selected_category == 'restaurants':
                    merchant_name = random.choice(merchant_categories['restaurants'])
                    category_primary = 'restaurants'
                    category_detailed = 'restaurant'
                    amount = round(random.uniform(10, 80), 2)
                elif selected_category == 'gas':
                    merchant_name = random.choice(merchant_categories['gas'])
                    category_primary = 'gas'
                    category_detailed = 'gas_station'
                    amount = round(random.uniform(30, 80), 2)
                elif selected_category == 'utilities':
                    merchant_name = random.choice(merchant_categories['utilities'])
                    category_primary = 'utilities'
                    category_detailed = 'utility_bill'
                    amount = round(random.uniform(50, 300), 2)
                elif selected_category == 'shopping':
                    merchant_name = random.choice(merchant_categories['shopping'])
                    category_primary = 'shopping'
                    category_detailed = 'retail'
                    amount = round(random.uniform(20, 500), 2)
                elif selected_category == 'subscriptions':
                    merchant_name = random.choice(merchant_categories['subscriptions'])
                    category_primary = 'subscriptions'
                    category_detailed = 'recurring_subscription'
                    amount = round(random.uniform(5, 50), 2)
                else:
                    merchant_name = fake.company()
                    category_primary = 'other'
                    category_detailed = 'general'
                    amount = round(random.uniform(10, 200), 2)
                
                # Make amount negative for expenses
                amount = -abs(amount)
                payment_channel = random.choice(['online', 'in store', 'ACH'])
            
            # Generate transaction
            transaction = {
                'transaction_id': f'txn_{uuid.uuid4()}',
                'account_id': account['account_id'],
                'user_id': user_id,
                'date': transaction_date.date().isoformat(),
                'amount': amount,
                'merchant_name': merchant_name,
                'merchant_entity_id': f'merchant_{uuid.uuid4()}',
                'payment_channel': payment_channel,
                'category_primary': category_primary,
                'category_detailed': category_detailed,
                'pending': random.random() < 0.05,  # 5% pending
                'created_at': transaction_date.isoformat()
            }
            transactions.append(transaction)
    
    return transactions


def generate_liabilities(users, accounts):
    """
    Generate synthetic liability data for credit card accounts.
    
    Args:
        users: List of user dictionaries
        accounts: List of account dictionaries
    
    Returns:
        List of liability dictionaries
    """
    liabilities = []
    now = datetime.now()
    
    # Filter credit card accounts
    credit_card_accounts = [acc for acc in accounts if acc['type'] == 'credit card']
    
    # Create user lookup for utilization patterns
    user_utilization_patterns = {}
    for user in users:
        if user['user_type'] != 'customer':
            continue
        # Assign utilization pattern: 20% high, 30% medium, 50% low
        roll = random.random()
        if roll < 0.2:
            user_utilization_patterns[user['user_id']] = 'high'  # >50%
        elif roll < 0.5:
            user_utilization_patterns[user['user_id']] = 'medium'  # 30-50%
        else:
            user_utilization_patterns[user['user_id']] = 'low'  # <30%
    
    for account in credit_card_accounts:
        user_id = account['user_id']
        utilization_pattern = user_utilization_patterns.get(user_id, 'low')
        
        # Get current balance and limit
        balance_current = account['balance_current']
        balance_limit = account['balance_limit']
        
        # Adjust balance based on utilization pattern if needed
        if utilization_pattern == 'high':
            # Ensure >50% utilization
            if balance_current / balance_limit < 0.5:
                balance_current = round(balance_limit * random.uniform(0.5, 0.95), 2)
        elif utilization_pattern == 'medium':
            # Ensure 30-50% utilization
            if balance_current / balance_limit < 0.3 or balance_current / balance_limit > 0.5:
                balance_current = round(balance_limit * random.uniform(0.3, 0.5), 2)
        else:  # low
            # Ensure <30% utilization
            if balance_current / balance_limit >= 0.3:
                balance_current = round(balance_limit * random.uniform(0.05, 0.3), 2)
        
        # Generate liability record
        days_ago = random.randint(0, 180)
        created_at = (now - timedelta(days=days_ago)).isoformat()
        
        # APR ranges
        apr_purchase = round(random.uniform(15, 25), 2)
        apr_balance_transfer = round(random.uniform(0, 21), 2)
        apr_cash_advance = round(random.uniform(25, 30), 2)
        
        # Minimum payment: 2-3% of balance
        minimum_payment_amount = round(balance_current * random.uniform(0.02, 0.03), 2)
        
        # Last payment: varied (some minimum-only, some full balance)
        if random.random() < 0.4:  # 40% pay minimum only
            last_payment_amount = minimum_payment_amount
        else:
            # Pay more than minimum, up to full balance
            last_payment_amount = round(random.uniform(minimum_payment_amount, balance_current), 2)
        
        # Is overdue: True for 10% of accounts
        is_overdue = random.random() < 0.1
        
        # Next payment due date: random future date (within next 30 days)
        days_until_due = random.randint(1, 30)
        next_payment_due_date = (now + timedelta(days=days_until_due)).date().isoformat()
        
        # Last statement balance: close to current balance (±5%)
        variance = balance_current * 0.05
        last_statement_balance = round(balance_current + random.uniform(-variance, variance), 2)
        
        liability = {
            'liability_id': f'liab_{uuid.uuid4()}',
            'account_id': account['account_id'],
            'user_id': user_id,
            'liability_type': 'credit_card',
            'apr_purchase': apr_purchase,
            'apr_balance_transfer': apr_balance_transfer,
            'apr_cash_advance': apr_cash_advance,
            'minimum_payment_amount': minimum_payment_amount,
            'last_payment_amount': last_payment_amount,
            'is_overdue': is_overdue,
            'next_payment_due_date': next_payment_due_date,
            'last_statement_balance': last_statement_balance,
            'created_at': created_at
        }
        liabilities.append(liability)
    
    return liabilities


def main():
    """
    Main function that orchestrates data generation.
    """
    print("Generating synthetic data...")
    
    # Generate 75 users
    print("Generating users...")
    users = generate_users(75)
    
    # Generate accounts for all users
    print("Generating accounts...")
    accounts = generate_accounts(users)
    
    # Generate transactions for all users/accounts
    print("Generating transactions...")
    transactions = generate_transactions(users, accounts)
    
    # Generate liabilities for credit card accounts
    print("Generating liabilities...")
    liabilities = generate_liabilities(users, accounts)
    
    # Print summary statistics
    print("\n=== Summary Statistics ===")
    customers = [u for u in users if u['user_type'] == 'customer']
    operators = [u for u in users if u['user_type'] == 'operator']
    users_with_consent = [u for u in users if u['consent_status']]
    
    print(f"Total users: {len(users)}")
    print(f"  - Customers: {len(customers)}")
    print(f"  - Operators: {len(operators)}")
    print(f"  - Users with consent: {len(users_with_consent)} ({len(users_with_consent)/len(users)*100:.1f}%)")
    
    # Account breakdown
    account_types = {}
    for account in accounts:
        acc_type = account['type']
        account_types[acc_type] = account_types.get(acc_type, 0) + 1
    
    print(f"\nTotal accounts: {len(accounts)}")
    for acc_type, count in sorted(account_types.items()):
        print(f"  - {acc_type}: {count}")
    
    print(f"\nTotal transactions: {len(transactions)}")
    print(f"Total liabilities: {len(liabilities)}")
    
    # Write data to JSON files
    print("\nWriting data to JSON files...")
    
    # Get the script directory and construct data path
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    output_files = {
        data_dir / 'synthetic_users.json': users,
        data_dir / 'synthetic_accounts.json': accounts,
        data_dir / 'synthetic_transactions.json': transactions,
        data_dir / 'synthetic_liabilities.json': liabilities
    }
    
    for filepath, data in output_files.items():
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  - {filepath}: {len(data)} records")
    
    print("\nData generation complete!")


if __name__ == "__main__":
    main()

