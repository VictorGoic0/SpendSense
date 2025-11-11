#!/usr/bin/env python3
"""
Batch script to compute features for all users.

Computes features for both 30-day and 180-day windows for all users in the database.
"""

import sys
from pathlib import Path
import time
from datetime import datetime

# Add backend to path (where app/ module lives)
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import SQLALCHEMY_DATABASE_URL
from app.models import User
from app.services.feature_detection import compute_all_features


def main():
    """Main function to compute features for all users"""
    # Create database session
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("Batch Feature Computation")
        print("=" * 60)
        print()
        
        # Query all users from database
        users = db.query(User).filter(User.user_type == 'customer').all()
        
        if not users:
            print("No users found in database. Please run data ingestion first.")
            return
        
        print(f"Found {len(users)} users to process")
        print(f"Computing features for 30-day and 180-day windows...")
        print()
        
        start_time = time.time()
        total_computation_times = []
        
        # For each user
        for idx, user in enumerate(users, 1):
            user_start_time = time.time()
            
            try:
                # Compute features for 30-day window
                compute_all_features(db, user.user_id, 30)
                
                # Compute features for 180-day window
                compute_all_features(db, user.user_id, 180)
                
                user_duration = time.time() - user_start_time
                total_computation_times.append(user_duration)
                
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
        
        if total_computation_times:
            avg_time = sum(total_computation_times) / len(total_computation_times)
            print(f"Average computation time per user: {avg_time:.3f} seconds")
            print(f"Total feature records created/updated: {len(users) * 2} (30d + 180d per user)")
        
        print()
        print("✅ Feature computation complete!")
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

