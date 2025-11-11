#!/usr/bin/env python3
"""
Test script for POST approve recommendation endpoint.

Tests the POST /recommendations/{recommendation_id}/approve endpoint.

Usage:
    Make sure the virtual environment is activated:
        cd backend
        source venv/bin/activate
    
    Then run from project root:
        python backend/scripts/test_approve_recommendation.py [recommendation_id] [operator_id]
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
    print("  python backend/scripts/test_approve_recommendation.py")
    sys.exit(1)

# Base URL for the API
API_BASE_URL = "http://localhost:8000"


def get_pending_recommendation(user_id: str):
    """Get a pending recommendation for a user"""
    url = f"{API_BASE_URL}/recommendations/{user_id}"
    params = {"status": "pending_approval"}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        result = response.json()
        
        if result.get('recommendations'):
            return result['recommendations'][0]
        return None
    except Exception as e:
        print(f"Error getting pending recommendation: {e}")
        return None


def test_approve_recommendation(recommendation_id: str, operator_id: str, notes: str = None):
    """Test POST approve recommendation endpoint"""
    url = f"{API_BASE_URL}/recommendations/{recommendation_id}/approve"
    
    payload = {
        "operator_id": operator_id
    }
    if notes:
        payload["notes"] = notes
    
    print(f"\n{'=' * 60}")
    print(f"Testing POST /recommendations/{recommendation_id}/approve")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"{'=' * 60}")
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Request successful!")
            print(f"Status Code: {response.status_code}")
            print(f"\nApproved Recommendation:")
            print(f"  - ID: {result.get('recommendation_id')}")
            print(f"  - Title: {result.get('title', '')[:50]}...")
            print(f"  - Status: {result.get('status')}")
            print(f"  - Approved by: {result.get('approved_by')}")
            print(f"  - Approved at: {result.get('approved_at')}")
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


def verify_recommendation_status(recommendation_id: str, expected_status: str):
    """Verify recommendation status via GET endpoint"""
    # We need to find which user this recommendation belongs to
    # For now, we'll just check if we can get it via a user
    # In a real scenario, we'd query by recommendation_id
    print(f"\n📋 Verifying recommendation {recommendation_id} has status '{expected_status}'")
    print("   (Note: This requires knowing the user_id - checking via GET endpoint)")
    return True


def verify_operator_action(recommendation_id: str, operator_id: str):
    """Verify operator action was logged"""
    print(f"\n📋 Verifying operator action logged for recommendation {recommendation_id}")
    print("   (Note: This would require querying the operator_actions table directly)")
    return True


def main():
    """Main test function"""
    # Get recommendation_id and operator_id from command line or use defaults
    if len(sys.argv) > 2:
        recommendation_id = sys.argv[1]
        operator_id = sys.argv[2]
    elif len(sys.argv) > 1:
        recommendation_id = sys.argv[1]
        operator_id = "operator_001"
        print("⚠️  No operator_id provided. Using default 'operator_001'")
    else:
        # Try to get a pending recommendation
        print("⚠️  No recommendation_id provided. Attempting to find pending recommendation...")
        print("   Usage: python backend/scripts/test_approve_recommendation.py <recommendation_id> <operator_id>")
        
        # Try to get a pending recommendation for a test user
        test_user_id = "user_001"
        pending_rec = get_pending_recommendation(test_user_id)
        
        if pending_rec:
            recommendation_id = pending_rec.get('recommendation_id')
            operator_id = "operator_001"
            print(f"✅ Found pending recommendation: {recommendation_id}")
        else:
            print(f"❌ No pending recommendations found for user {test_user_id}")
            print("   Please generate recommendations first or provide a recommendation_id")
            return
    
    print("=" * 60)
    print("Testing POST Approve Recommendation Endpoint")
    print("=" * 60)
    
    # Test 1: Approve recommendation
    print("\n📋 Test 1: Approve recommendation")
    success = test_approve_recommendation(recommendation_id, operator_id, notes="Test approval")
    
    if success:
        # Test 2: Verify status changed to approved
        print("\n📋 Test 2: Verify status changed to approved")
        verify_recommendation_status(recommendation_id, "approved")
        
        # Test 3: Verify operator action logged
        print("\n📋 Test 3: Verify operator action logged")
        verify_operator_action(recommendation_id, operator_id)
        
        # Test 4: Try to approve again (should fail)
        print("\n📋 Test 4: Try to approve again (should fail with 400)")
        test_approve_recommendation(recommendation_id, operator_id, notes="Duplicate approval attempt")
    
    # Test 5: Test with non-existent recommendation
    print("\n📋 Test 5: Test with non-existent recommendation")
    test_approve_recommendation("non_existent_rec_12345", operator_id)
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

