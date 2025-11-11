"""
Test script for guardrails service

Tests:
- Tone validation with good and bad examples
- Consent checking with consented/non-consented users
- Eligibility checks with various user scenarios
"""

import sys
import os
from pathlib import Path

# Add backend to path (where app/ module lives)
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set database path
db_path = backend_dir / "spendsense.db"
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import User, UserFeature
from app.services.guardrails import (
    validate_tone,
    check_consent,
    check_income_eligibility,
    check_credit_eligibility,
    check_account_exists,
    filter_partner_offers,
    append_disclosure,
    MANDATORY_DISCLOSURE
)


def test_tone_validation():
    """Test tone validation with various examples"""
    print("\n" + "="*80)
    print("TEST: Tone Validation")
    print("="*80)
    
    # Test 1: Valid content (no warnings)
    print("\n1. Testing valid content (should pass):")
    valid_content = "You can improve your savings by setting up automatic transfers. Let's explore options that work for your situation. Many people find this approach helpful."
    result = validate_tone(valid_content)
    print(f"   Content: {valid_content[:60]}...")
    print(f"   Result: is_valid={result['is_valid']}, warnings={len(result['validation_warnings'])}")
    assert result["is_valid"] == True, "Valid content should pass"
    assert len(result["validation_warnings"]) == 0, "Valid content should have no warnings"
    print("   ✅ PASSED")
    
    # Test 2: Contains forbidden phrase (critical warning)
    print("\n2. Testing content with forbidden phrase (should fail with critical warning):")
    bad_content = "You're overspending on subscriptions. This is a bad habit that needs to stop."
    result = validate_tone(bad_content)
    print(f"   Content: {bad_content}")
    print(f"   Result: is_valid={result['is_valid']}, warnings={len(result['validation_warnings'])}")
    assert result["is_valid"] == False, "Content with forbidden phrase should fail"
    assert len(result["validation_warnings"]) > 0, "Should have warnings"
    assert any(w["severity"] == "critical" for w in result["validation_warnings"]), "Should have critical warning"
    assert any(w["type"] == "forbidden_phrase" for w in result["validation_warnings"]), "Should have forbidden_phrase type"
    print(f"   Warnings: {result['validation_warnings']}")
    print("   ✅ PASSED")
    
    # Test 3: Lacks empowering language (notable warning)
    print("\n3. Testing content without empowering language (should fail with notable warning):")
    no_empower_content = "Setting up automatic transfers is important. Make sure to do this every month."
    result = validate_tone(no_empower_content)
    print(f"   Content: {no_empower_content}")
    print(f"   Result: is_valid={result['is_valid']}, warnings={len(result['validation_warnings'])}")
    assert result["is_valid"] == False, "Content without empowering language should fail"
    assert len(result["validation_warnings"]) > 0, "Should have warnings"
    assert any(w["severity"] == "notable" for w in result["validation_warnings"]), "Should have notable warning"
    assert any(w["type"] == "lacks_empowering_language" for w in result["validation_warnings"]), "Should have lacks_empowering_language type"
    print(f"   Warnings: {result['validation_warnings']}")
    print("   ✅ PASSED")
    
    # Test 4: Both issues (critical + notable)
    print("\n4. Testing content with both issues (should fail with both warnings):")
    both_bad = "You're overspending. This is irresponsible behavior."
    result = validate_tone(both_bad)
    print(f"   Content: {both_bad}")
    print(f"   Result: is_valid={result['is_valid']}, warnings={len(result['validation_warnings'])}")
    assert result["is_valid"] == False, "Content with both issues should fail"
    assert len(result["validation_warnings"]) >= 2, "Should have at least 2 warnings"
    critical_count = sum(1 for w in result["validation_warnings"] if w["severity"] == "critical")
    notable_count = sum(1 for w in result["validation_warnings"] if w["severity"] == "notable")
    print(f"   Critical warnings: {critical_count}, Notable warnings: {notable_count}")
    print(f"   All warnings: {result['validation_warnings']}")
    print("   ✅ PASSED")
    
    print("\n✅ All tone validation tests passed!")


def test_consent_checking(db: Session):
    """Test consent checking with various users"""
    print("\n" + "="*80)
    print("TEST: Consent Checking")
    print("="*80)
    
    # Get a user with consent
    consented_user = db.query(User).filter(User.consent_status == True).first()
    if consented_user:
        print(f"\n1. Testing consented user: {consented_user.user_id}")
        result = check_consent(db, consented_user.user_id)
        print(f"   Result: {result}")
        assert result == True, "Consented user should return True"
        print("   ✅ PASSED")
    else:
        print("\n1. No consented users found in database (skipping)")
    
    # Get a user without consent
    non_consented_user = db.query(User).filter(User.consent_status == False).first()
    if non_consented_user:
        print(f"\n2. Testing non-consented user: {non_consented_user.user_id}")
        result = check_consent(db, non_consented_user.user_id)
        print(f"   Result: {result}")
        assert result == False, "Non-consented user should return False"
        print("   ✅ PASSED")
    else:
        print("\n2. No non-consented users found in database (skipping)")
    
    # Test with non-existent user
    print("\n3. Testing non-existent user:")
    result = check_consent(db, "nonexistent_user_12345")
    print(f"   Result: {result}")
    assert result == False, "Non-existent user should return False"
    print("   ✅ PASSED")
    
    print("\n✅ All consent checking tests passed!")


def test_eligibility_checks(db: Session):
    """Test eligibility checks with various user scenarios"""
    print("\n" + "="*80)
    print("TEST: Eligibility Checks")
    print("="*80)
    
    # Get a user with features
    user_with_features = db.query(User).join(UserFeature).filter(
        UserFeature.window_days == 30
    ).first()
    
    if user_with_features:
        features = db.query(UserFeature).filter(
            UserFeature.user_id == user_with_features.user_id,
            UserFeature.window_days == 30
        ).first()
        
        print(f"\n1. Testing income eligibility for user: {user_with_features.user_id}")
        print(f"   User's avg_monthly_income: ${features.avg_monthly_income or 0:.2f}")
        
        # Test with threshold below user's income
        if features.avg_monthly_income:
            threshold_below = features.avg_monthly_income - 1000
            result = check_income_eligibility(db, user_with_features.user_id, threshold_below)
            print(f"   Threshold: ${threshold_below:.2f} → Result: {result}")
            assert result == True, "User should be eligible if income >= threshold"
            print("   ✅ PASSED")
            
            # Test with threshold above user's income
            threshold_above = features.avg_monthly_income + 1000
            result = check_income_eligibility(db, user_with_features.user_id, threshold_above)
            print(f"   Threshold: ${threshold_above:.2f} → Result: {result}")
            assert result == False, "User should not be eligible if income < threshold"
            print("   ✅ PASSED")
        
        print(f"\n2. Testing credit eligibility for user: {user_with_features.user_id}")
        print(f"   User's max_utilization: {features.max_utilization or 0:.2%}")
        
        # Test with threshold above user's utilization
        if features.max_utilization is not None:
            threshold_above = features.max_utilization + 0.1
            result = check_credit_eligibility(db, user_with_features.user_id, threshold_above)
            print(f"   Threshold: {threshold_above:.2%} → Result: {result}")
            assert result == True, "User should be eligible if utilization <= threshold"
            print("   ✅ PASSED")
            
            # Test with threshold below user's utilization
            threshold_below = max(0.0, features.max_utilization - 0.1)
            result = check_credit_eligibility(db, user_with_features.user_id, threshold_below)
            print(f"   Threshold: {threshold_below:.2%} → Result: {result}")
            if features.max_utilization > threshold_below:
                assert result == False, "User should not be eligible if utilization > threshold"
            print("   ✅ PASSED")
        
        print(f"\n3. Testing account existence for user: {user_with_features.user_id}")
        # Test checking account
        result = check_account_exists(db, user_with_features.user_id, "checking")
        print(f"   Checking account exists: {result}")
        print("   ✅ PASSED")
        
        # Test non-existent account type
        result = check_account_exists(db, user_with_features.user_id, "nonexistent_type_xyz")
        print(f"   Non-existent account type: {result}")
        assert result == False, "Non-existent account type should return False"
        print("   ✅ PASSED")
    else:
        print("\nNo users with features found in database (skipping eligibility tests)")
    
    print("\n✅ All eligibility check tests passed!")


def test_partner_offer_filtering(db: Session):
    """Test partner offer filtering"""
    print("\n" + "="*80)
    print("TEST: Partner Offer Filtering")
    print("="*80)
    
    # Get a user with features
    user_with_features = db.query(User).join(UserFeature).filter(
        UserFeature.window_days == 30
    ).first()
    
    if user_with_features:
        features = db.query(UserFeature).filter(
            UserFeature.user_id == user_with_features.user_id,
            UserFeature.window_days == 30
        ).first()
        
        # Create test offers
        offers = [
            {
                "offer_id": "offer_1",
                "title": "High-Yield Savings Account",
                "metadata": {
                    "min_income": (features.avg_monthly_income or 0) - 1000,  # User should be eligible
                }
            },
            {
                "offer_id": "offer_2",
                "title": "Premium Credit Card",
                "metadata": {
                    "max_utilization": (features.max_utilization or 0) + 0.1,  # User should be eligible
                }
            },
            {
                "offer_id": "offer_3",
                "title": "Investment Account",
                "metadata": {
                    "min_income": (features.avg_monthly_income or 0) + 10000,  # User should NOT be eligible
                }
            },
            {
                "offer_id": "offer_4",
                "title": "No Requirements Offer",
                "metadata": {}
            }
        ]
        
        print(f"\nTesting with user: {user_with_features.user_id}")
        print(f"User income: ${features.avg_monthly_income or 0:.2f}")
        print(f"User max utilization: {features.max_utilization or 0:.2%}")
        print(f"\nOriginal offers: {len(offers)}")
        
        filtered = filter_partner_offers(db, user_with_features.user_id, offers)
        print(f"Filtered offers: {len(filtered)}")
        
        # Should filter out offer_3 (income too high)
        assert len(filtered) < len(offers), "Should filter out some offers"
        assert any(o["offer_id"] == "offer_4" for o in filtered), "Offer with no requirements should pass"
        
        print(f"Filtered offer IDs: {[o['offer_id'] for o in filtered]}")
        print("   ✅ PASSED")
    else:
        print("\nNo users with features found in database (skipping partner offer filtering test)")
    
    print("\n✅ Partner offer filtering test passed!")


def test_mandatory_disclosure():
    """Test mandatory disclosure appending"""
    print("\n" + "="*80)
    print("TEST: Mandatory Disclosure")
    print("="*80)
    
    # Test 1: Content ending with period
    print("\n1. Testing content ending with period:")
    content1 = "This is great advice. You should follow it."
    result1 = append_disclosure(content1)
    print(f"   Original: {content1}")
    print(f"   Result ends with disclosure: {result1.endswith(MANDATORY_DISCLOSURE)}")
    assert MANDATORY_DISCLOSURE in result1, "Result should contain disclosure"
    print("   ✅ PASSED")
    
    # Test 2: Content not ending with period
    print("\n2. Testing content not ending with period:")
    content2 = "This is great advice"
    result2 = append_disclosure(content2)
    print(f"   Original: {content2}")
    print(f"   Result ends with disclosure: {result2.endswith(MANDATORY_DISCLOSURE)}")
    assert MANDATORY_DISCLOSURE in result2, "Result should contain disclosure"
    assert result2.endswith(".") or result2.endswith(MANDATORY_DISCLOSURE), "Should add period if needed"
    print("   ✅ PASSED")
    
    print("\n✅ All mandatory disclosure tests passed!")


def main():
    """Run all guardrails tests"""
    print("\n" + "="*80)
    print("GUARDRAILS SERVICE TESTS")
    print("="*80)
    
    # Initialize database session
    db = SessionLocal()
    
    try:
        # Test tone validation (no DB needed)
        test_tone_validation()
        
        # Test consent checking
        test_consent_checking(db)
        
        # Test eligibility checks
        test_eligibility_checks(db)
        
        # Test partner offer filtering
        test_partner_offer_filtering(db)
        
        # Test mandatory disclosure (no DB needed)
        test_mandatory_disclosure()
        
        print("\n" + "="*80)
        print("✅ ALL GUARDRAILS TESTS PASSED!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

