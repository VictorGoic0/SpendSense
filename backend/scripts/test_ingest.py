#!/usr/bin/env python3
"""
Test script for data ingestion endpoint.

Loads synthetic JSON data files and POSTs them to the /ingest endpoint.

Usage:
    Make sure the virtual environment is activated:
        cd backend
        source venv/bin/activate
    
    Then run from project root:
        python backend/scripts/test_ingest.py
"""

import json
import sys
from pathlib import Path

# Check if requests is available
try:
    import requests
except ImportError:
    print("=" * 60)
    print("❌ Error: 'requests' module not found")
    print("=" * 60)
    print("\nPlease activate the virtual environment first:")
    print("  cd backend")
    print("  source venv/bin/activate  # On macOS/Linux")
    print("  # or")
    print("  venv\\Scripts\\activate  # On Windows")
    print("\nThen run the script from the project root:")
    print("  python backend/scripts/test_ingest.py")
    print("\nOr install requests in your current Python environment:")
    print("  pip install requests==2.31.0")
    sys.exit(1)

# Base URL for the API
API_BASE_URL = "http://localhost:8000"

# Paths to JSON files (scripts are now in backend/scripts/, data is in backend/data/)
DATA_DIR = Path(__file__).parent.parent / "data"
USERS_FILE = DATA_DIR / "synthetic_users.json"
ACCOUNTS_FILE = DATA_DIR / "synthetic_accounts.json"
TRANSACTIONS_FILE = DATA_DIR / "synthetic_transactions.json"
LIABILITIES_FILE = DATA_DIR / "synthetic_liabilities.json"


def load_json_file(file_path: Path) -> list:
    """Load JSON data from file"""
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    with open(file_path, 'r') as f:
        return json.load(f)


def ingest_data():
    """Load all JSON files and POST to /ingest endpoint"""
    
    print("Loading synthetic data files...")
    
    # Load all JSON files
    users = load_json_file(USERS_FILE)
    accounts = load_json_file(ACCOUNTS_FILE)
    transactions = load_json_file(TRANSACTIONS_FILE)
    liabilities = load_json_file(LIABILITIES_FILE)
    
    print(f"Loaded:")
    print(f"  - Users: {len(users)}")
    print(f"  - Accounts: {len(accounts)}")
    print(f"  - Transactions: {len(transactions)}")
    print(f"  - Liabilities: {len(liabilities)}")
    
    # Prepare request payload
    payload = {
        "users": users,
        "accounts": accounts,
        "transactions": transactions,
        "liabilities": liabilities
    }
    
    print(f"\nPosting data to {API_BASE_URL}/ingest...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/ingest",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        response.raise_for_status()
        
        result = response.json()
        
        print("\n✅ Ingestion successful!")
        print(f"Status: {result['status']}")
        print(f"Duration: {result['duration_ms']}ms")
        print("\nIngested counts:")
        for entity_type, count in result['ingested'].items():
            print(f"  - {entity_type}: {count}")
        
        return True
    
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error: Could not connect to {API_BASE_URL}")
        print("Make sure the FastAPI server is running:")
        print("  cd backend && uvicorn app.main:app --reload")
        return False
    
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"Detail: {error_detail}")
            except:
                print(f"Response: {e.response.text}")
        return False
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("SpendSense Data Ingestion Test")
    print("=" * 60)
    print()
    
    success = ingest_data()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Test completed successfully!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ Test failed!")
        print("=" * 60)
        sys.exit(1)

