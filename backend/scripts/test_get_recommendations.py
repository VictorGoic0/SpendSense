#!/usr/bin/env python3
"""
Test script for GET recommendations endpoint.

Tests the GET /recommendations/{user_id} endpoint with various filters.

Usage:
    Make sure the virtual environment is activated:
        cd backend
        source venv/bin/activate
    
    Then run from project root:
        python backend/scripts/test_get_recommendations.py [user_id]
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
    print("  python backend/scripts/test_get_recommendations.py")
    sys.exit(1)

# Base URL for the API
API_BASE_URL = "http://localhost:8000"


def test_get_recommendations(user_id: str, status: str = None, window_days: int = None):
    """Test GET recommendations endpoint"""
    url = f"{API_BASE_URL}/recommendations/{user_id}"
    params = {}
    
    if status:
        params["status"] = status
    if window_days:
        params["window_days"] = window_days
    
    print(f"\n{'=' * 60}")
    print(f"Testing GET /recommendations/{user_id}")
    if params:
        print(f"Query params: {params}")
    print(f"{'=' * 60}")
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        result = response.json()
        
        print(f"\n✅ Request successful!")
        print(f"Status Code: {response.status_code}")
        print(f"Total recommendations: {result.get('total', 0)}")
        print(f"Returned recommendations: {len(result.get('recommendations', []))}")
        
        if result.get('recommendations'):
            print(f"\nFirst recommendation:")
            rec = result['recommendations'][0]
            print(f"  - ID: {rec.get('recommendation_id')}")
            print(f"  - Title: {rec.get('title', '')[:50]}...")
            print(f"  - Status: {rec.get('status')}")
            print(f"  - Persona: {rec.get('persona_type')}")
            print(f"  - Generated at: {rec.get('generated_at')}")
        else:
            print("\n⚠️  No recommendations found")
        
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


def main():
    """Main test function"""
    # Get user_id from command line or use default
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        # Try to get a user_id from the database or use a test ID
        print("⚠️  No user_id provided. Using test user_id 'user_001'")
        print("   Usage: python backend/scripts/test_get_recommendations.py <user_id>")
        user_id = "user_001"
    
    print("=" * 60)
    print("Testing GET Recommendations Endpoint")
    print("=" * 60)
    
    # Test 1: Get all recommendations (default - should only show approved for customers)
    print("\n📋 Test 1: Get recommendations (default)")
    test_get_recommendations(user_id)
    
    # Test 2: Get pending_approval recommendations
    print("\n📋 Test 2: Get pending_approval recommendations")
    test_get_recommendations(user_id, status="pending_approval")
    
    # Test 3: Get approved recommendations
    print("\n📋 Test 3: Get approved recommendations")
    test_get_recommendations(user_id, status="approved")
    
    # Test 4: Get recommendations with window_days filter
    print("\n📋 Test 4: Get recommendations with window_days=30")
    test_get_recommendations(user_id, window_days=30)
    
    # Test 5: Get recommendations with both filters
    print("\n📋 Test 5: Get approved recommendations with window_days=30")
    test_get_recommendations(user_id, status="approved", window_days=30)
    
    # Test 6: Test with non-existent user
    print("\n📋 Test 6: Test with non-existent user")
    test_get_recommendations("non_existent_user_12345")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

