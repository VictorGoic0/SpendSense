#!/usr/bin/env python3
"""
Test script for OpenAI recommendation generation

Tests the generate_recommendations_via_openai function with each persona type.
Verifies response structure, content quality, and saves output to JSON file for review.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend to path (where app/ module lives)
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Get the correct database path (backend/spendsense.db)
database_path = backend_dir / "spendsense.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{database_path.absolute()}"

from app.services.recommendation_engine import (
    build_user_context,
    validate_context,
    generate_recommendations_via_openai
)
from app.models import User, Persona


def verify_rationale_cites_data(rationale: str, user_context: dict) -> bool:
    """
    Check if rationale cites specific data from user context.
    
    Args:
        rationale: The rationale string to check
        user_context: The user context dictionary
    
    Returns:
        True if rationale appears to cite specific data
    """
    rationale_lower = rationale.lower()
    
    # Check for common data citation patterns
    citation_indicators = [
        "because",
        "based on",
        "your",
        "you have",
        "you're",
        "utilization",
        "balance",
        "income",
        "spending",
        "account",
        "transaction",
        "merchant",
        "savings",
        "credit",
    ]
    
    # Check if rationale contains at least 2 citation indicators
    matches = sum(1 for indicator in citation_indicators if indicator in rationale_lower)
    return matches >= 2


def check_content_quality(recommendation: dict) -> tuple[bool, list[str]]:
    """
    Check content quality and tone.
    
    Args:
        recommendation: Recommendation dictionary
    
    Returns:
        Tuple of (is_valid, issues_list)
    """
    issues = []
    content = recommendation.get("content", "").lower()
    title = recommendation.get("title", "").lower()
    
    # Check for shaming language (forbidden phrases)
    forbidden_phrases = [
        "you're overspending",
        "bad habit",
        "poor financial decision",
        "irresponsible",
        "wasteful spending",
        "you should stop",
        "you need to",
    ]
    
    for phrase in forbidden_phrases:
        if phrase in content or phrase in title:
            issues.append(f"Contains shaming language: '{phrase}'")
    
    # Check for empowering language (should be present)
    empowering_keywords = [
        "you can",
        "let's",
        "many people",
        "common challenge",
        "opportunity",
        "consider",
        "explore",
    ]
    
    has_empowering = any(keyword in content for keyword in empowering_keywords)
    if not has_empowering:
        issues.append("Lacks empowering tone")
    
    # Check content length (should be substantial)
    if len(recommendation.get("content", "")) < 100:
        issues.append("Content too short (<100 characters)")
    
    # Check title length (should be reasonable)
    if len(recommendation.get("title", "")) < 10:
        issues.append("Title too short (<10 characters)")
    
    is_valid = len(issues) == 0
    return (is_valid, issues)


def test_persona_generation(db, persona_type: str, window_days: int = 30):
    """Test recommendation generation for a specific persona type"""
    print(f"\n{'='*80}")
    print(f"Testing OpenAI Generation - {persona_type}")
    print(f"{'='*80}\n")
    
    # Find a user with this persona type
    persona = db.query(Persona).filter(
        Persona.persona_type == persona_type,
        Persona.window_days == window_days
    ).first()
    
    if not persona:
        print(f"⚠️  No user found with persona '{persona_type}' for {window_days}d window")
        return None
    
    user_id = persona.user_id
    print(f"User ID: {user_id[:30]}...")
    print(f"Persona: {persona_type}")
    print(f"Window: {window_days} days\n")
    
    try:
        # Build user context
        print("Building user context...")
        user_context = build_user_context(db, user_id, window_days)
        
        if not validate_context(user_context):
            print("❌ Context validation failed")
            return None
        
        print("✅ Context built and validated\n")
        
        # Generate recommendations
        print("Calling OpenAI API...")
        start_time = datetime.now()
        
        recommendations = generate_recommendations_via_openai(persona_type, user_context)
        
        end_time = datetime.now()
        total_latency = (end_time - start_time).total_seconds() * 1000  # Convert to ms
        
        print(f"✅ OpenAI API call completed\n")
        
        # Verify JSON response structure
        print("Verifying response structure...")
        if not isinstance(recommendations, list):
            print(f"❌ Recommendations is not a list, got {type(recommendations)}")
            return None
        
        print(f"✅ Response is a list with {len(recommendations)} items")
        
        # Verify 3-5 recommendations returned per call
        if len(recommendations) < 3:
            print(f"⚠️  Warning: Only {len(recommendations)} recommendations returned (expected 3-5)")
        elif len(recommendations) > 5:
            print(f"⚠️  Warning: {len(recommendations)} recommendations returned (expected 3-5)")
        else:
            print(f"✅ Correct number of recommendations: {len(recommendations)}")
        
        # Verify each recommendation has required fields
        required_fields = ["title", "content", "rationale", "generation_time_ms", "persona_type"]
        all_valid = True
        
        for idx, rec in enumerate(recommendations):
            missing = [field for field in required_fields if field not in rec]
            if missing:
                print(f"❌ Recommendation {idx} missing fields: {missing}")
                all_valid = False
        
        if all_valid:
            print("✅ All recommendations have required fields")
        
        # Verify rationales cite specific data
        print("\nVerifying rationales cite specific data...")
        rationale_issues = []
        for idx, rec in enumerate(recommendations):
            rationale = rec.get("rationale", "")
            if not verify_rationale_cites_data(rationale, user_context):
                rationale_issues.append(f"Recommendation {idx}: rationale doesn't cite specific data")
        
        if rationale_issues:
            print(f"⚠️  {len(rationale_issues)} rationales may not cite specific data:")
            for issue in rationale_issues:
                print(f"   - {issue}")
        else:
            print("✅ All rationales cite specific data")
        
        # Check content quality and tone
        print("\nChecking content quality and tone...")
        quality_issues = []
        for idx, rec in enumerate(recommendations):
            is_valid, issues = check_content_quality(rec)
            if not is_valid:
                quality_issues.append((idx, issues))
        
        if quality_issues:
            print(f"⚠️  {len(quality_issues)} recommendations have quality issues:")
            for idx, issues in quality_issues:
                print(f"   Recommendation {idx}:")
                for issue in issues:
                    print(f"     - {issue}")
        else:
            print("✅ All recommendations pass quality checks")
        
        # Measure latency
        print(f"\nLatency: {total_latency:.0f}ms")
        if total_latency < 5000:
            print("✅ Latency under 5 seconds")
        else:
            print(f"⚠️  Warning: Latency exceeds 5 seconds ({total_latency/1000:.1f}s)")
        
        # Extract token usage from metadata (for logging/review, NOT saved to DB)
        token_usage = None
        estimated_cost = None
        if recommendations and "metadata" in recommendations[0]:
            metadata = recommendations[0].get("metadata", {})
            token_usage = metadata.get("token_usage")
            estimated_cost = metadata.get("estimated_cost_usd")
            
            # Log token usage and cost for review
            if token_usage:
                print(f"\nToken Usage:")
                print(f"  Prompt tokens: {token_usage.get('prompt_tokens', 0)}")
                print(f"  Completion tokens: {token_usage.get('completion_tokens', 0)}")
                print(f"  Total tokens: {token_usage.get('total_tokens', 0)}")
            if estimated_cost:
                print(f"  Estimated cost: ${estimated_cost:.6f}")
        
        # Print generated recommendations for review
        print(f"\n{'='*80}")
        print("Generated Recommendations:")
        print(f"{'='*80}\n")
        
        for idx, rec in enumerate(recommendations, 1):
            print(f"Recommendation {idx}:")
            print(f"  Title: {rec['title']}")
            print(f"  Rationale: {rec['rationale']}")
            print(f"  Content Preview: {rec['content'][:200]}...")
            print()
        
        # Prepare output data
        output_data = {
            "test_timestamp": datetime.now().isoformat(),
            "persona_type": persona_type,
            "user_id": user_id,
            "window_days": window_days,
            "total_latency_ms": round(total_latency, 2),
            "token_usage": token_usage,
            "estimated_cost_usd": estimated_cost,
            "recommendations_count": len(recommendations),
            "recommendations": [
                {
                    "title": rec["title"],
                    "content": rec["content"],
                    "rationale": rec["rationale"],
                    "generation_time_ms": rec.get("generation_time_ms"),
                    "metadata": rec.get("metadata", {})
                }
                for rec in recommendations
            ],
            "user_context_summary": {
                "persona_type": user_context.get("persona_type"),
                "subscription_signals": user_context.get("subscription_signals"),
                "savings_signals": user_context.get("savings_signals"),
                "credit_signals": user_context.get("credit_signals"),
                "income_signals": user_context.get("income_signals"),
                "accounts_count": len(user_context.get("accounts", [])),
                "transactions_count": len(user_context.get("recent_transactions", [])),
            }
        }
        
        return output_data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main test function"""
    # Create database session
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("OpenAI Recommendation Generation Test")
        print("=" * 80)
        
        # Test with each persona type (5 tests)
        persona_types = [
            "high_utilization",
            "variable_income",
            "subscription_heavy",
            "savings_builder",
            "wealth_builder"
        ]
        
        all_results = []
        
        for persona_type in persona_types:
            result = test_persona_generation(db, persona_type, window_days=30)
            if result:
                all_results.append(result)
        
        # Save output to JSON file
        output_file = Path(__file__).parent.parent / "openai_test_output.json"
        
        output_data = {
            "test_run_timestamp": datetime.now().isoformat(),
            "total_tests": len(all_results),
            "persona_types_tested": persona_types,
            "results": all_results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 80)
        print("Test Summary")
        print("=" * 80)
        print(f"✅ Successful tests: {len(all_results)}/{len(persona_types)}")
        print(f"📄 Output saved to: {output_file}")
        print("\nNote: Review the output file and delete when done.")
        
        if len(all_results) == len(persona_types):
            print("\n✅ All tests passed!")
        else:
            print(f"\n⚠️  {len(persona_types) - len(all_results)} test(s) failed or skipped")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

