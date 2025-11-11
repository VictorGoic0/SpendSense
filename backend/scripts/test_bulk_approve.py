#!/usr/bin/env python3
"""
Test script for POST bulk approve recommendations endpoint.

Tests the POST /recommendations/bulk-approve endpoint.

Usage:
    Make sure the virtual environment is activated:
        cd backend
        source venv/bin/activate
    
    Then run from project root:
        python backend/scripts/test_bulk_approve.py [user_id] [operator_id]
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
    print("  python backend/scripts/test_bulk_approve.py")
    sys.exit(1)

# Base URL for the API
API_BASE_URL = "http://localhost:8000"


def get_pending_recommendations(user_id: str, limit: int = 10):
    """Get pending recommendations for a user"""
    url = f"{API_BASE_URL}/recommendations/{user_id}"
    params = {"status": "pending_approval"}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        result = response.json()
        
        recommendations = result.get('recommendations', [])
        return recommendations[:limit]
    except Exception as e:
        print(f"Error getting pending recommendations: {e}")
        return []


def test_bulk_approve(recommendation_ids: list, operator_id: str):
    """Test POST bulk approve recommendations endpoint"""
    url = f"{API_BASE_URL}/recommendations/bulk-approve"
    
    payload = {
        "operator_id": operator_id,
        "recommendation_ids": recommendation_ids
    }
    
    print(f"\n{'=' * 60}")
    print(f"Testing POST /recommendations/bulk-approve")
    print(f"Operator ID: {operator_id}")
    print(f"Recommendation IDs ({len(recommendation_ids)}):")
    for rec_id in recommendation_ids:
        print(f"  - {rec_id}")
    print(f"{'=' * 60}")
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Request successful!")
            print(f"Status Code: {response.status_code}")
            print(f"\nBulk Approve Results:")
            print(f"  - Approved: {result.get('approved', 0)}")
            print(f"  - Failed: {result.get('failed', 0)}")
            
            if result.get('errors'):
                print(f"\n  Errors ({len(result.get('errors', []))}):")
                for error in result.get('errors', []):
                    print(f"    - {error}")
            return True
        else:
            print(f"\n❌ Request failed!")
            print(f"Status Code: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Detail: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"Response: {response.text}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error: Could not connect to {API_BASE_URL}")
        print("Make sure the FastAPI server is running:")
        print("  cd backend && uvicorn app.main:app --reload")
        return False
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def verify_recommendations_status(recommendation_ids: list, user_id: str, expected_status: str):
    """Verify recommendations have expected status"""
    print(f"\n📋 Verifying {len(recommendation_ids)} recommendations have status '{expected_status}'")
    
    url = f"{API_BASE_URL}/recommendations/{user_id}"
    params = {"status": expected_status}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        result = response.json()
        
        approved_recs = result.get('recommendations', [])
        approved_ids = {rec.get('recommendation_id') for rec in approved_recs}
        
        verified = 0
        for rec_id in recommendation_ids:
            if rec_id in approved_ids:
                verified += 1
        
        print(f"  ✅ Verified {verified}/{len(recommendation_ids)} recommendations have status '{expected_status}'")
        return verified == len(recommendation_ids)
    except Exception as e:
        print(f"  ⚠️  Could not verify: {e}")
        return False


def main():
    """Main test function"""
    # Get user_id and operator_id from command line or use defaults
    if len(sys.argv) > 2:
        user_id = sys.argv[1]
        operator_id = sys.argv[2]
    elif len(sys.argv) > 1:
        user_id = sys.argv[1]
        operator_id = "operator_001"
        print("⚠️  No operator_id provided. Using default 'operator_001'")
    else:
        user_id = "user_001"
        operator_id = "operator_001"
        print("⚠️  No arguments provided. Using defaults:")
        print(f"   user_id: {user_id}")
        print(f"   operator_id: {operator_id}")
        print("   Usage: python backend/scripts/test_bulk_approve.py <user_id> <operator_id>")
    
    print("=" * 60)
    print("Testing POST Bulk Approve Recommendations Endpoint")
    print("=" * 60)
    
    # Get pending recommendations
    print(f"\n📋 Step 1: Getting pending recommendations for user {user_id}")
    pending_recs = get_pending_recommendations(user_id, limit=10)
    
    if not pending_recs:
        print(f"❌ No pending recommendations found for user {user_id}")
        print("   Please generate recommendations first:")
        print(f"   POST /recommendations/generate/{user_id}")
        return
    
    print(f"✅ Found {len(pending_recs)} pending recommendations")
    recommendation_ids = [rec.get('recommendation_id') for rec in pending_recs]
    
    # Test 1: Bulk approve all pending recommendations
    print("\n📋 Test 1: Bulk approve all pending recommendations")
    success = test_bulk_approve(recommendation_ids, operator_id)
    
    if success:
        # Test 2: Verify all changed to approved
        print("\n📋 Test 2: Verify all changed to approved")
        verify_recommendations_status(recommendation_ids, user_id, "approved")
        
        # Test 3: Test with mix of valid and invalid IDs
        print("\n📋 Test 3: Test with mix of valid and invalid IDs")
        mixed_ids = recommendation_ids[:2] + ["invalid_rec_12345", "invalid_rec_67890"]
        test_bulk_approve(mixed_ids, operator_id)
        
        # Test 4: Test with already approved recommendations (should fail)
        print("\n📋 Test 4: Test with already approved recommendations (should fail)")
        if recommendation_ids:
            test_bulk_approve(recommendation_ids[:2], operator_id)
    
    # Test 5: Test with all invalid IDs (should return 400)
    print("\n📋 Test 5: Test with all invalid IDs (should return 400)")
    test_bulk_approve(["invalid_rec_1", "invalid_rec_2", "invalid_rec_3"], operator_id)
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

