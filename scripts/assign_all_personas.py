#!/usr/bin/env python3
"""
Batch script to assign personas for all users.

Assigns personas for both 30-day and 180-day windows for all users in the database.
"""

import sys
from pathlib import Path
import time
from datetime import datetime
from collections import Counter

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Get the correct database path (backend/spendsense.db)
backend_dir = Path(__file__).parent.parent / "backend"
database_path = backend_dir / "spendsense.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{database_path.absolute()}"

from app.models import User, Persona
from app.services.persona_assignment import assign_and_save_persona


def main():
    """Main function to assign personas for all users"""
    # Create database session
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("Batch Persona Assignment")
        print("=" * 60)
        print()
        
        # Query all users from database
        users = db.query(User).filter(User.user_type == 'customer').all()
        
        if not users:
            print("No users found in database. Please run data ingestion first.")
            return
        
        print(f"Found {len(users)} users to process")
        print(f"Assigning personas for 30-day and 180-day windows...")
        print()
        
        start_time = time.time()
        persona_30d_counter = Counter()
        persona_180d_counter = Counter()
        users_with_no_persona_30d = 0
        users_with_no_persona_180d = 0
        
        # For each user
        for idx, user in enumerate(users, 1):
            try:
                # Assign persona for 30-day window
                persona_30d = assign_and_save_persona(db, user.user_id, 30)
                if persona_30d.persona_type == 'general_wellness':
                    users_with_no_persona_30d += 1
                else:
                    persona_30d_counter[persona_30d.persona_type] += 1
                
                # Assign persona for 180-day window
                persona_180d = assign_and_save_persona(db, user.user_id, 180)
                if persona_180d.persona_type == 'general_wellness':
                    users_with_no_persona_180d += 1
                else:
                    persona_180d_counter[persona_180d.persona_type] += 1
                
                # Print progress (every 10 users)
                if idx % 10 == 0:
                    print(f"Processed {idx}/{len(users)} users...")
            
            except Exception as e:
                print(f"Error processing user {user.user_id}: {e}")
                continue
        
        total_duration = time.time() - start_time
        
        # Print summary statistics
        print()
        print("=" * 60)
        print("Summary Statistics")
        print("=" * 60)
        print(f"Total users processed: {len(users)}")
        print(f"Total duration: {total_duration:.2f} seconds")
        print()
        
        # Persona distribution for 30d window
        print("30-Day Window Persona Distribution:")
        print("-" * 60)
        for persona_type, count in sorted(persona_30d_counter.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(users)) * 100
            print(f"  {persona_type:25s}: {count:3d} ({percentage:5.1f}%)")
        if users_with_no_persona_30d > 0:
            percentage = (users_with_no_persona_30d / len(users)) * 100
            print(f"  {'general_wellness':25s}: {users_with_no_persona_30d:3d} ({percentage:5.1f}%)")
        print()
        
        # Persona distribution for 180d window
        print("180-Day Window Persona Distribution:")
        print("-" * 60)
        for persona_type, count in sorted(persona_180d_counter.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(users)) * 100
            print(f"  {persona_type:25s}: {count:3d} ({percentage:5.1f}%)")
        if users_with_no_persona_180d > 0:
            percentage = (users_with_no_persona_180d / len(users)) * 100
            print(f"  {'general_wellness':25s}: {users_with_no_persona_180d:3d} ({percentage:5.1f}%)")
        print()
        
        # Verify all 5 persona types are represented
        all_persona_types_30d = set(persona_30d_counter.keys())
        all_persona_types_180d = set(persona_180d_counter.keys())
        expected_types = {'high_utilization', 'variable_income', 'subscription_heavy', 'savings_builder', 'wealth_builder'}
        
        missing_30d = expected_types - all_persona_types_30d
        missing_180d = expected_types - all_persona_types_180d
        
        if missing_30d:
            print(f"⚠️  Warning: Missing persona types in 30d window: {', '.join(missing_30d)}")
        if missing_180d:
            print(f"⚠️  Warning: Missing persona types in 180d window: {', '.join(missing_180d)}")
        
        if not missing_30d and not missing_180d:
            print("✅ All 5 persona types are represented!")
        
        print()
        print("✅ Persona assignment complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

