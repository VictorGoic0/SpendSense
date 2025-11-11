#!/usr/bin/env python3
"""
Quick verification script to check ingested data counts.
"""

import sys
from pathlib import Path

# Add backend to path (where app/ module lives)
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from app.database import SQLALCHEMY_DATABASE_URL

def check_data():
    """Check record counts in database"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as conn:
        # Get counts for each table
        tables = ['users', 'accounts', 'transactions', 'liabilities']
        
        print("=" * 60)
        print("Database Record Counts")
        print("=" * 60)
        print()
        
        for table in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {table:15} {count:>6} records")
        
        print()
        print("=" * 60)
        
        # Sample data check
        print("\nSample User:")
        result = conn.execute(text("SELECT user_id, full_name, email, user_type FROM users LIMIT 1"))
        row = result.fetchone()
        if row:
            print(f"  ID: {row[0]}")
            print(f"  Name: {row[1]}")
            print(f"  Email: {row[2]}")
            print(f"  Type: {row[3]}")
        
        print("\nSample Transaction:")
        result = conn.execute(text("SELECT transaction_id, amount, merchant_name, date FROM transactions LIMIT 1"))
        row = result.fetchone()
        if row:
            print(f"  ID: {row[0]}")
            print(f"  Amount: ${row[1]:.2f}")
            print(f"  Merchant: {row[2]}")
            print(f"  Date: {row[3]}")

if __name__ == "__main__":
    try:
        check_data()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

