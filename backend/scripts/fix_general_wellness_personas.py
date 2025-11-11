#!/usr/bin/env python3
"""
Temporary script to fix data quality issue: Update all 'general_wellness' personas to 'savings_builder'.

This script:
1. Finds all Persona records with persona_type = 'general_wellness'
2. Updates them to 'savings_builder' with appropriate confidence scores
3. Also checks for users with features but no personas (shouldn't happen, but handles edge case)
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add backend to path (where app/ module lives)
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker

# Get the correct database path (backend/spendsense.db)
database_path = backend_dir / "spendsense.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{database_path.absolute()}"

from app.models import User, Persona, UserFeature


def main():
    """Main function to fix general_wellness personas"""
    # Create database session
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("Fix General Wellness Personas")
        print("=" * 60)
        print()
        
        # Step 1: Find all personas with 'general_wellness'
        # Note: SQLite might allow old data even with new constraint
        # We'll query directly using raw SQL to catch any that exist
        general_wellness_personas = db.query(Persona).filter(
            Persona.persona_type == 'general_wellness'
        ).all()
        
        print(f"Found {len(general_wellness_personas)} persona(s) with 'general_wellness' type")
        print()
        
        if general_wellness_personas:
            print("Updating personas to 'savings_builder':")
            print("-" * 60)
            
            updated_count = 0
            for persona in general_wellness_personas:
                # Determine confidence based on whether features exist
                features = db.query(UserFeature).filter(
                    and_(
                        UserFeature.user_id == persona.user_id,
                        UserFeature.window_days == persona.window_days
                    )
                ).first()
                
                if features:
                    # Features exist but no match - use 0.2 confidence
                    new_confidence = 0.2
                    reason = 'No persona criteria matched - fallback assignment'
                else:
                    # No features - use 0.1 confidence
                    new_confidence = 0.1
                    reason = 'No features computed for this user/window - fallback assignment'
                
                # Update reasoning JSON
                try:
                    # Try to parse existing reasoning
                    existing_reasoning = json.loads(persona.reasoning) if persona.reasoning else {}
                except:
                    existing_reasoning = {}
                
                # Update reasoning with fallback info
                updated_reasoning = {
                    'matched_criteria': [],
                    'feature_values': {},
                    'timestamp': datetime.now().isoformat(),
                    'reason': reason,
                    'original_persona_type': 'general_wellness',
                    'migrated_at': datetime.now().isoformat()
                }
                # Preserve any existing fields
                updated_reasoning.update(existing_reasoning)
                updated_reasoning['reason'] = reason
                updated_reasoning['original_persona_type'] = 'general_wellness'
                updated_reasoning['migrated_at'] = datetime.now().isoformat()
                
                # Update persona
                persona.persona_type = 'savings_builder'
                persona.confidence_score = new_confidence
                persona.reasoning = json.dumps(updated_reasoning)
                persona.assigned_at = datetime.now()
                
                print(f"  User {persona.user_id}, window {persona.window_days}d:")
                print(f"    {persona.persona_id}: 'general_wellness' → 'savings_builder' (confidence: {new_confidence})")
                updated_count += 1
            
            # Commit all updates
            db.commit()
            print()
            print(f"✅ Updated {updated_count} persona(s)")
        else:
            print("✅ No 'general_wellness' personas found in database")
        
        print()
        
        # Step 2: Check for users with features but no personas (edge case)
        print("Checking for users with features but no personas:")
        print("-" * 60)
        
        # Get all users with features
        users_with_features = db.query(UserFeature.user_id, UserFeature.window_days).distinct().all()
        
        missing_personas = []
        for user_id, window_days in users_with_features:
            persona = db.query(Persona).filter(
                and_(
                    Persona.user_id == user_id,
                    Persona.window_days == window_days
                )
            ).first()
            
            if not persona:
                missing_personas.append((user_id, window_days))
        
        if missing_personas:
            print(f"⚠️  Found {len(missing_personas)} user/window combinations with features but no persona:")
            for user_id, window_days in missing_personas:
                print(f"  User {user_id}, window {window_days}d")
            print()
            print("These should be assigned personas. Run assign_all_personas.py to fix.")
        else:
            print("✅ All users with features have personas assigned")
        
        print()
        print("=" * 60)
        print("Fix complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

