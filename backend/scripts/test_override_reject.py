#!/usr/bin/env python3
"""
Test script for POST override and reject recommendation endpoints.

Tests the POST /recommendations/{recommendation_id}/override and
POST /recommendations/{recommendation_id}/reject endpoints.

Usage:
    Make sure the virtual environment is activated:
        cd backend
        source venv/bin/activate
    
    Then run from project root:
        python backend/scripts/test_override_reject.py [recommendation_id] [operator_id]
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
    print("  python backend/scripts/test_override_reject.py")
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


def test_override_recommendation(recommendation_id: str, operator_id: str, new_title: str = None, new_content: str = None, reason: str = "Test override"):
    """Test POST override recommendation endpoint"""
    url = f"{API_BASE_URL}/recommendations/{recommendation_id}/override"
    
    payload = {
        "operator_id": operator_id,
        "reason": reason
    }
    if new_title:
        payload["new_title"] = new_title
    if new_content:
        payload["new_content"] = new_content
    
    print(f"\n{'=' * 60}")
    print(f"Testing POST /recommendations/{recommendation_id}/override")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"{'=' * 60}")
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Request successful!")
            print(f"Status Code: {response.status_code}")
            print(f"\nOverridden Recommendation:")
            print(f"  - ID: {result.get('recommendation_id')}")
            print(f"  - Title: {result.get('title', '')[:50]}...")
            print(f"  - Status: {result.get('status')}")
            print(f"  - Override reason: {result.get('override_reason', '')[:50]}...")
            if result.get('original_content'):
                try:
                    original = json.loads(result.get('original_content'))
                    print(f"  - Original title: {original.get('original_title', '')[:50]}...")
                except:
                    print(f"  - Original content preserved: Yes")
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


def test_reject_recommendation(recommendation_id: str, operator_id: str, reason: str = "Test rejection"):
    """Test POST reject recommendation endpoint"""
    url = f"{API_BASE_URL}/recommendations/{recommendation_id}/reject"
    
    payload = {
        "operator_id": operator_id,
        "reason": reason
    }
    
    print(f"\n{'=' * 60}")
    print(f"Testing POST /recommendations/{recommendation_id}/reject")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"{'=' * 60}")
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Request successful!")
            print(f"Status Code: {response.status_code}")
            print(f"\nRejected Recommendation:")
            print(f"  - ID: {result.get('recommendation_id')}")
            print(f"  - Title: {result.get('title', '')[:50]}...")
            print(f"  - Status: {result.get('status')}")
            if result.get('metadata_json'):
                try:
                    metadata = json.loads(result.get('metadata_json'))
                    print(f"  - Rejection reason: {metadata.get('rejection_reason', '')[:50]}...")
                    print(f"  - Rejected by: {metadata.get('rejected_by')}")
                except:
                    print(f"  - Rejection metadata: Present")
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
        print("   Usage: python backend/scripts/test_override_reject.py <recommendation_id> <operator_id>")
        
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
    print("Testing POST Override & Reject Recommendation Endpoints")
    print("=" * 60)
    
    # Test 1: Override with new title and content
    print("\n📋 Test 1: Override with new title and content")
    test_override_recommendation(
        recommendation_id,
        operator_id,
        new_title="Updated Title: Better Financial Planning",
        new_content="You can improve your financial situation by exploring budgeting strategies. Many people find that tracking expenses helps them understand their spending patterns. Consider setting up automatic savings transfers to build your emergency fund.",
        reason="Content needed more empowering tone"
    )
    
    # Test 2: Override with only new title
    print("\n📋 Test 2: Override with only new title")
    # Get another pending recommendation
    test_user_id = "user_001"
    pending_rec = get_pending_recommendation(test_user_id)
    if pending_rec:
        test_override_recommendation(
            pending_rec.get('recommendation_id'),
            operator_id,
            new_title="Improved Title",
            reason="Title needed improvement"
        )
    
    # Test 3: Override with only new content
    print("\n📋 Test 3: Override with only new content")
    pending_rec = get_pending_recommendation(test_user_id)
    if pending_rec:
        test_override_recommendation(
            pending_rec.get('recommendation_id'),
            operator_id,
            new_content="Let's explore ways to optimize your financial health. Many people find success by reviewing their spending habits regularly. You can start by identifying areas where you might want to adjust your budget.",
            reason="Content needed better tone"
        )
    
    # Test 4: Test override validation (neither title nor content)
    print("\n📋 Test 4: Test override validation (should fail - neither title nor content)")
    pending_rec = get_pending_recommendation(test_user_id)
    if pending_rec:
        test_override_recommendation(
            pending_rec.get('recommendation_id'),
            operator_id,
            reason="Test validation"
        )
    
    # Test 5: Test override with forbidden phrase (should fail tone validation)
    print("\n📋 Test 5: Test override with forbidden phrase (should fail tone validation)")
    pending_rec = get_pending_recommendation(test_user_id)
    if pending_rec:
        test_override_recommendation(
            pending_rec.get('recommendation_id'),
            operator_id,
            new_content="You're overspending and need to stop this bad habit immediately.",
            reason="Test tone validation"
        )
    
    # Test 6: Reject pending recommendation
    print("\n📋 Test 6: Reject pending recommendation")
    pending_rec = get_pending_recommendation(test_user_id)
    if pending_rec:
        test_reject_recommendation(
            pending_rec.get('recommendation_id'),
            operator_id,
            reason="Content not appropriate for user"
        )
    
    # Test 7: Test reject validation (should fail - can't reject approved)
    print("\n📋 Test 7: Test reject validation (should fail - can't reject approved)")
    # First approve a recommendation
    pending_rec = get_pending_recommendation(test_user_id)
    if pending_rec:
        approve_url = f"{API_BASE_URL}/recommendations/{pending_rec.get('recommendation_id')}/approve"
        approve_payload = {"operator_id": operator_id, "notes": "Test approval"}
        try:
            approve_response = requests.post(approve_url, json=approve_payload)
            if approve_response.status_code == 200:
                print(f"✅ Approved recommendation {pending_rec.get('recommendation_id')} for test")
                # Now try to reject it
                test_reject_recommendation(
                    pending_rec.get('recommendation_id'),
                    operator_id,
                    reason="Should fail - already approved"
                )
        except Exception as e:
            print(f"⚠️  Could not approve recommendation for test: {e}")
    
    # Test 8: Test with non-existent recommendation
    print("\n📋 Test 8: Test with non-existent recommendation")
    test_override_recommendation("non_existent_rec_12345", operator_id, new_title="Test", reason="Test")
    test_reject_recommendation("non_existent_rec_12345", operator_id, reason="Test")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

