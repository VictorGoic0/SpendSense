#!/usr/bin/env python3
"""
Test script for product ingestion via API endpoint.

Loads product catalog JSON file and POSTs it to the /ingest endpoint.

Usage:
    Make sure the virtual environment is activated and backend server is running:
        cd backend
        source venv/bin/activate
        uvicorn app.main:app --reload
    
    Then run from project root:
        python backend/scripts/test_ingest_products.py
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
    print("  python backend/scripts/test_ingest_products.py")
    print("\nOr install requests in your current Python environment:")
    print("  pip install requests==2.31.0")
    sys.exit(1)

# Base URL for the API
API_BASE_URL = "http://localhost:8000"

# Path to product catalog JSON file (scripts are now in backend/scripts/, data is in backend/data/)
DATA_DIR = Path(__file__).parent.parent / "data"
PRODUCTS_FILE = DATA_DIR / "product_catalog.json"


def load_products(file_path: Path) -> list:
    """Load product data from JSON file"""
    if not file_path.exists():
        print(f"❌ Error: Product catalog file not found: {file_path}")
        print(f"\nPlease generate the product catalog first:")
        print(f"  python backend/scripts/generate_product_catalog.py")
        sys.exit(1)
    
    try:
        with open(file_path, 'r') as f:
            products = json.load(f)
        
        if not isinstance(products, list):
            print(f"❌ Error: Expected JSON array, got {type(products).__name__}")
            sys.exit(1)
        
        print(f"✓ Loaded {len(products)} products from {file_path}")
        return products
    
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in product catalog: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading product catalog: {e}")
        sys.exit(1)


def ingest_products(products: list):
    """POST products to /ingest endpoint"""
    print("\n" + "=" * 60)
    print("Ingesting Products via API")
    print("=" * 60)
    
    # Prepare request payload
    payload = {
        "products": products
    }
    
    try:
        print(f"\n📤 POSTing {len(products)} products to {API_BASE_URL}/ingest/...")
        response = requests.post(
            f"{API_BASE_URL}/ingest/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        response.raise_for_status()
        result = response.json()
        
        print("\n✅ Ingestion successful!")
        print(f"   Status: {result['status']}")
        print(f"   Products ingested: {result['ingested'].get('products', 0)}")
        print(f"   Duration: {result['duration_ms']}ms")
        
        return result
    
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error: Could not connect to API at {API_BASE_URL}")
        print("   Make sure the backend server is running:")
        print("   cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
        sys.exit(1)
    
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"   Detail: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"   Response: {e.response.text}")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


def main():
    """Main function"""
    print("=" * 60)
    print("SpendSense Product Ingestion Test")
    print("=" * 60)
    
    # Load products
    products = load_products(PRODUCTS_FILE)
    
    # Ingest products
    result = ingest_products(products)
    
    print("\n" + "=" * 60)
    print("✅ Product ingestion complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

