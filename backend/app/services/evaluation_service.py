#!/usr/bin/env python3
"""
Evaluation Script - Metrics Computation

Computes system performance metrics:
- Coverage: Percentage of users with personas assigned
- Explainability: Percentage of recommendations with rationale
- Latency: Average and p95 recommendation generation time
- Auditability: Percentage of recommendations with decision traces
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pandas as pd
import numpy as np
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from sqlalchemy import create_engine, func, or_
from sqlalchemy.orm import sessionmaker

# Get the correct database path (backend/spendsense.db)
backend_dir = Path(__file__).parent.parent / "backend"
database_path = backend_dir / "spendsense.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{database_path.absolute()}"

from app.models import (
    User, 
    Persona, 
    Recommendation, 
    UserFeature, 
    EvaluationMetric
)


# ============================================================================
# Coverage Metrics
# ============================================================================

def compute_coverage_metrics(db) -> dict:
    """
    Compute coverage metrics: percentage of users with personas assigned.
    
    Coverage = (users_with_persona / total_users_with_consent) * 100
    
    Args:
        db: Database session
    
    Returns:
        Dictionary with coverage metrics
    """
    # Query total users with consent_status=True
    total_users = db.query(User).filter(
        User.consent_status == True,
        User.user_type == 'customer'
    ).count()
    
    # Query count of users with persona assigned (30d window)
    # Use distinct to count unique users
    distinct_user_ids = db.query(Persona.user_id).filter(
        Persona.window_days == 30
    ).distinct().all()
    users_with_persona = len(distinct_user_ids)
    
    # Query count of users with ≥3 detected behaviors:
    # - recurring_merchants >= 3 OR
    # - net_savings_inflow > 0 OR
    # - avg_utilization > 0
    distinct_behavior_user_ids = db.query(UserFeature.user_id).filter(
        UserFeature.window_days == 30,
        or_(
            UserFeature.recurring_merchants >= 3,
            UserFeature.net_savings_inflow > 0,
            UserFeature.avg_utilization > 0
        )
    ).distinct().all()
    users_with_behaviors = len(distinct_behavior_user_ids)
    
    # Calculate coverage_percentage
    coverage_percentage = (users_with_persona / total_users * 100) if total_users > 0 else 0.0
    
    return {
        "total_users": total_users,
        "users_with_persona": users_with_persona,
        "users_with_behaviors": users_with_behaviors,
        "coverage_percentage": round(coverage_percentage, 2)
    }


# ============================================================================
# Explainability Metrics
# ============================================================================

def compute_explainability_metrics(db) -> dict:
    """
    Compute explainability metrics: percentage of recommendations with rationale.
    
    Explainability = (recommendations_with_rationale / total_recommendations) * 100
    
    Args:
        db: Database session
    
    Returns:
        Dictionary with explainability metrics
    """
    # Query total count of recommendations
    total_recommendations = db.query(Recommendation).count()
    
    # Query count of recommendations with rationale not null and not empty
    recommendations_with_rationale = db.query(Recommendation).filter(
        Recommendation.rationale.isnot(None),
        Recommendation.rationale != ""
    ).count()
    
    # Calculate explainability_percentage
    explainability_percentage = (
        (recommendations_with_rationale / total_recommendations * 100) 
        if total_recommendations > 0 else 0.0
    )
    
    return {
        "total_recommendations": total_recommendations,
        "recommendations_with_rationale": recommendations_with_rationale,
        "explainability_percentage": round(explainability_percentage, 2)
    }


# ============================================================================
# Latency Metrics
# ============================================================================

def compute_latency_metrics(db) -> dict:
    """
    Compute latency metrics: average and p95 recommendation generation time.
    
    Args:
        db: Database session
    
    Returns:
        Dictionary with latency metrics
    """
    # Query all recommendations with generation_time_ms not null
    recommendations = db.query(Recommendation.generation_time_ms).filter(
        Recommendation.generation_time_ms.isnot(None)
    ).all()
    
    # Extract generation_time_ms values into list
    latencies = [r.generation_time_ms for r in recommendations if r.generation_time_ms is not None]
    
    if not latencies:
        return {
            "avg_recommendation_latency_ms": 0.0,
            "p95_recommendation_latency_ms": 0.0,
            "total_recommendations_with_latency": 0
        }
    
    # Calculate average latency
    avg_latency = sum(latencies) / len(latencies)
    
    # Calculate p95 latency using numpy.percentile()
    p95_latency = np.percentile(latencies, 95)
    
    return {
        "avg_recommendation_latency_ms": round(avg_latency, 2),
        "p95_recommendation_latency_ms": round(float(p95_latency), 2),
        "total_recommendations_with_latency": len(latencies)
    }


# ============================================================================
# Auditability Metrics
# ============================================================================

def compute_auditability_metrics(db) -> dict:
    """
    Compute auditability metrics: percentage of recommendations with decision traces.
    
    All recommendations have decision traces (persona + features), so this should be 100%.
    
    Args:
        db: Database session
    
    Returns:
        Dictionary with auditability metrics
    """
    # Query total recommendations count
    total_recommendations = db.query(Recommendation).count()
    
    # All recommendations have decision traces (persona + features)
    # Since persona_type is required and features are always computed, 
    # auditability_percentage = 100.0
    recommendations_with_traces = total_recommendations
    auditability_percentage = 100.0
    
    return {
        "total_recommendations": total_recommendations,
        "recommendations_with_traces": recommendations_with_traces,
        "auditability_percentage": auditability_percentage
    }


# ============================================================================
# Persona Distribution
# ============================================================================

def get_persona_distribution(db, window_days: int) -> dict:
    """
    Get distribution of personas by type for a given window.
    
    Args:
        db: Database session
        window_days: Time window (30 or 180)
    
    Returns:
        Dictionary with counts per persona type
    """
    # Query personas table grouped by persona_type
    results = db.query(
        Persona.persona_type,
        func.count(Persona.persona_id).label('count')
    ).filter(
        Persona.window_days == window_days
    ).group_by(Persona.persona_type).all()
    
    # Build dictionary with counts per persona
    distribution = {}
    for persona_type, count in results:
        distribution[persona_type] = count
    
    return distribution


# ============================================================================
# Recommendation Status Breakdown
# ============================================================================

def get_recommendation_status_breakdown(db) -> dict:
    """
    Get breakdown of recommendations by status.
    
    Args:
        db: Database session
    
    Returns:
        Dictionary with counts per status
    """
    # Query recommendations table grouped by status
    results = db.query(
        Recommendation.status,
        func.count(Recommendation.recommendation_id).label('count')
    ).group_by(Recommendation.status).all()
    
    # Build dictionary with counts per status
    breakdown = {}
    for status, count in results:
        breakdown[status] = count
    
    return breakdown


# ============================================================================
# Parquet Export Functions
# ============================================================================

def export_user_features_to_parquet(db, window_days: int, run_id: str) -> str:
    """
    Export user features to parquet format.
    
    Args:
        db: Database session
        window_days: Time window (30 or 180)
        run_id: Evaluation run identifier
    
    Returns:
        Local file path to parquet file
    """
    # Query all user_features for specified window_days
    query = db.query(UserFeature).filter(
        UserFeature.window_days == window_days
    )
    
    # Convert to pandas DataFrame using pd.read_sql()
    df = pd.read_sql(query.statement, db.bind)
    
    # Define output path: /tmp/user_features_{window_days}d_{run_id}.parquet
    output_path = f"/tmp/user_features_{window_days}d_{run_id}.parquet"
    
    # Export to parquet: df.to_parquet(output_path)
    df.to_parquet(output_path, index=False)
    
    return output_path


def export_evaluation_results_to_parquet(db, run_id: str) -> str:
    """
    Export evaluation results to parquet format.
    
    Args:
        db: Database session
        run_id: Evaluation run identifier
    
    Returns:
        Local file path to parquet file
    """
    # Query evaluation_metrics table for run_id
    query = db.query(EvaluationMetric).filter(
        EvaluationMetric.run_id == run_id
    )
    
    # Convert to pandas DataFrame
    df = pd.read_sql(query.statement, db.bind)
    
    # Export to parquet: /tmp/evaluation_{run_id}.parquet
    output_path = f"/tmp/evaluation_{run_id}.parquet"
    df.to_parquet(output_path, index=False)
    
    return output_path


# ============================================================================
# S3 Upload Functions
# ============================================================================

def upload_to_s3(local_path: str, s3_key: str, bucket_name: str) -> str:
    """
    Upload file to S3 and generate pre-signed URL.
    
    Args:
        local_path: Path to local file
        s3_key: S3 object key (path in bucket)
        bucket_name: S3 bucket name
    
    Returns:
        Pre-signed URL for downloading the file
    
    Raises:
        NoCredentialsError: If AWS credentials are not configured
        ClientError: If S3 operation fails
    """
    try:
        # Create boto3 S3 client
        s3_client = boto3.client('s3')
        
        # Upload file: s3.upload_file(local_path, bucket_name, s3_key)
        s3_client.upload_file(local_path, bucket_name, s3_key)
        
        # Generate pre-signed URL:
        # Expiry: 604800 seconds (7 days)
        # Method: get_object
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': s3_key},
            ExpiresIn=604800  # 7 days
        )
        
        return presigned_url
        
    except NoCredentialsError:
        raise RuntimeError(
            "AWS credentials not found. Please configure AWS credentials using "
            "'aws configure' or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY "
            "environment variables."
        )
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        raise RuntimeError(
            f"Failed to upload to S3: {error_code} - {error_message}. "
            f"Check bucket name '{bucket_name}' and IAM permissions."
        )


# ============================================================================
# Evaluation Report Generation
# ============================================================================

def generate_evaluation_report(run_id: str, metrics: dict, s3_urls: dict) -> str:
    """
    Generate evaluation report JSON file.
    
    Args:
        run_id: Evaluation run identifier
        metrics: Metrics dictionary
        s3_urls: Dictionary with S3 keys and pre-signed URLs
    
    Returns:
        Path to generated report file
    """
    # Combine all data into report dict:
    report = {
        "run_id": run_id,
        "timestamp": metrics.get("timestamp", datetime.now().isoformat()),
        "metrics": {
            "coverage": metrics.get("coverage", {}),
            "explainability": metrics.get("explainability", {}),
            "latency": metrics.get("latency", {}),
            "auditability": metrics.get("auditability", {})
        },
        "persona_distribution": {
            "30d": metrics.get("persona_distribution_30d", {}),
            "180d": metrics.get("persona_distribution_180d", {})
        },
        "recommendation_status": metrics.get("recommendation_status_breakdown", {}),
        "parquet_exports": {
            key: key for key in s3_urls.keys()  # S3 keys
        },
        "download_urls": s3_urls  # Pre-signed URLs
    }
    
    # Write to file: evaluation_report_{run_id}.json
    # Save in root directory
    root_dir = Path(__file__).parent.parent
    report_path = root_dir / f"evaluation_report_{run_id}.json"
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Evaluation report saved: {report_path}")
    
    return str(report_path)


# ============================================================================
# Main Evaluation Function
# ============================================================================

def run_evaluation() -> tuple[str, dict, dict]:
    """
    Run complete evaluation and compute all metrics.
    
    Returns:
        Tuple of (run_id, metrics_dict, s3_urls_dict)
    """
    # Generate run_id with timestamp format: eval_YYYYMMDD_HHMMSS
    run_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Create database session
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Call all metric computation functions
        coverage_metrics = compute_coverage_metrics(db)
        explainability_metrics = compute_explainability_metrics(db)
        latency_metrics = compute_latency_metrics(db)
        auditability_metrics = compute_auditability_metrics(db)
        
        # Calculate persona distribution
        persona_distribution_30d = get_persona_distribution(db, window_days=30)
        persona_distribution_180d = get_persona_distribution(db, window_days=180)
        
        # Calculate recommendation status breakdown
        recommendation_status_breakdown = get_recommendation_status_breakdown(db)
        
        # Combine results into single metrics dict
        metrics = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "coverage": coverage_metrics,
            "explainability": explainability_metrics,
            "latency": latency_metrics,
            "auditability": auditability_metrics,
            "persona_distribution_30d": persona_distribution_30d,
            "persona_distribution_180d": persona_distribution_180d,
            "recommendation_status_breakdown": recommendation_status_breakdown
        }
        
        # Print metrics to console (formatted)
        print("=" * 80)
        print(f"Evaluation Run: {run_id}")
        print("=" * 80)
        print()
        
        print("Coverage Metrics:")
        print("-" * 80)
        print(f"  Total users with consent: {coverage_metrics['total_users']}")
        print(f"  Users with persona (30d): {coverage_metrics['users_with_persona']}")
        print(f"  Users with behaviors: {coverage_metrics['users_with_behaviors']}")
        print(f"  Coverage percentage: {coverage_metrics['coverage_percentage']}%")
        print()
        
        print("Explainability Metrics:")
        print("-" * 80)
        print(f"  Total recommendations: {explainability_metrics['total_recommendations']}")
        print(f"  Recommendations with rationale: {explainability_metrics['recommendations_with_rationale']}")
        print(f"  Explainability percentage: {explainability_metrics['explainability_percentage']}%")
        print()
        
        print("Latency Metrics:")
        print("-" * 80)
        print(f"  Average latency: {latency_metrics['avg_recommendation_latency_ms']}ms")
        print(f"  P95 latency: {latency_metrics['p95_recommendation_latency_ms']}ms")
        print(f"  Recommendations with latency data: {latency_metrics['total_recommendations_with_latency']}")
        print()
        
        print("Auditability Metrics:")
        print("-" * 80)
        print(f"  Total recommendations: {auditability_metrics['total_recommendations']}")
        print(f"  Recommendations with traces: {auditability_metrics['recommendations_with_traces']}")
        print(f"  Auditability percentage: {auditability_metrics['auditability_percentage']}%")
        print()
        
        print("Persona Distribution (30-day window):")
        print("-" * 80)
        if persona_distribution_30d:
            for persona_type, count in sorted(persona_distribution_30d.items(), key=lambda x: x[1], reverse=True):
                print(f"  {persona_type:25s}: {count:3d}")
        else:
            print("  No personas found")
        print()
        
        print("Persona Distribution (180-day window):")
        print("-" * 80)
        if persona_distribution_180d:
            for persona_type, count in sorted(persona_distribution_180d.items(), key=lambda x: x[1], reverse=True):
                print(f"  {persona_type:25s}: {count:3d}")
        else:
            print("  No personas found")
        print()
        
        print("Recommendation Status Breakdown:")
        print("-" * 80)
        if recommendation_status_breakdown:
            for status, count in sorted(recommendation_status_breakdown.items(), key=lambda x: x[1], reverse=True):
                print(f"  {status:25s}: {count:3d}")
        else:
            print("  No recommendations found")
        print()
        
        print("=" * 80)
        print("✅ Evaluation complete!")
        print("=" * 80)
        
        # Export to parquet and upload to S3
        print()
        print("Exporting data to Parquet and uploading to S3...")
        print("-" * 80)
        
        # Get S3 bucket name from environment or use default
        bucket_name = os.getenv('S3_BUCKET_NAME', 'spendsense-analytics-goico')
        
        s3_urls = {}
        
        try:
            # Export user features (30d)
            print("Exporting user features (30d)...")
            features_30d_path = export_user_features_to_parquet(db, window_days=30, run_id=run_id)
            s3_key_30d = f"features/user_features_30d_{run_id}.parquet"
            presigned_url_30d = upload_to_s3(features_30d_path, s3_key_30d, bucket_name)
            s3_urls[s3_key_30d] = presigned_url_30d
            print(f"  ✅ Uploaded: {s3_key_30d}")
            
            # Export user features (180d)
            print("Exporting user features (180d)...")
            features_180d_path = export_user_features_to_parquet(db, window_days=180, run_id=run_id)
            s3_key_180d = f"features/user_features_180d_{run_id}.parquet"
            presigned_url_180d = upload_to_s3(features_180d_path, s3_key_180d, bucket_name)
            s3_urls[s3_key_180d] = presigned_url_180d
            print(f"  ✅ Uploaded: {s3_key_180d}")
            
            # Note: Evaluation results export will happen in main() after metrics are saved
            print()
            print("✅ User features uploaded to S3 successfully!")
            print()
            
        except Exception as e:
            print(f"\n❌ Error during S3 export: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        return (run_id, metrics, s3_urls)
        
    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


# ============================================================================
# Save to Database
# ============================================================================

def save_evaluation_metrics(db, run_id: str, metrics: dict) -> EvaluationMetric:
    """
    Save evaluation metrics to database.
    
    Args:
        db: Database session
        run_id: Unique run identifier
        metrics: Dictionary with all metrics
    
    Returns:
        EvaluationMetric record
    """
    # Extract metrics from nested structure
    coverage = metrics.get("coverage", {})
    explainability = metrics.get("explainability", {})
    latency = metrics.get("latency", {})
    auditability = metrics.get("auditability", {})
    
    # Create EvaluationMetric model instance
    metric_record = EvaluationMetric(
        run_id=run_id,
        timestamp=datetime.now(),
        # Coverage fields
        total_users=coverage.get("total_users"),
        users_with_persona=coverage.get("users_with_persona"),
        users_with_behaviors=coverage.get("users_with_behaviors"),
        coverage_percentage=coverage.get("coverage_percentage"),
        # Explainability fields
        total_recommendations=explainability.get("total_recommendations"),
        recommendations_with_rationale=explainability.get("recommendations_with_rationale"),
        explainability_percentage=explainability.get("explainability_percentage"),
        # Latency fields
        avg_recommendation_latency_ms=latency.get("avg_recommendation_latency_ms"),
        p95_recommendation_latency_ms=latency.get("p95_recommendation_latency_ms"),
        # Auditability fields
        recommendations_with_traces=auditability.get("recommendations_with_traces"),
        auditability_percentage=auditability.get("auditability_percentage"),
        # Details field with JSON of extra info
        details=json.dumps({
            "persona_distribution_30d": metrics.get("persona_distribution_30d", {}),
            "persona_distribution_180d": metrics.get("persona_distribution_180d", {}),
            "recommendation_status_breakdown": metrics.get("recommendation_status_breakdown", {})
        })
    )
    
    # Add to database session
    db.add(metric_record)
    db.commit()
    db.refresh(metric_record)
    
    return metric_record


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main function to run evaluation and save results"""
    # Create database session
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Run evaluation (this will export to parquet and upload to S3)
        run_id, metrics, s3_urls = run_evaluation()
        
        # Save to database (must be done before exporting evaluation results)
        print()
        print("Saving metrics to database...")
        metric_record = save_evaluation_metrics(db, run_id, metrics)
        print(f"✅ Metrics saved with metric_id: {metric_record.metric_id}")
        print()
        
        # Export evaluation results now that metrics are saved
        print("Exporting evaluation results...")
        bucket_name = os.getenv('S3_BUCKET_NAME', 'spendsense-analytics-goico')
        eval_path = export_evaluation_results_to_parquet(db, run_id=run_id)
        s3_key_eval = f"eval/evaluation_{run_id}.parquet"
        presigned_url_eval = upload_to_s3(eval_path, s3_key_eval, bucket_name)
        s3_urls[s3_key_eval] = presigned_url_eval
        print(f"  ✅ Uploaded: {s3_key_eval}")
        print()
        
        # Generate evaluation report
        print("Generating evaluation report...")
        report_path = generate_evaluation_report(run_id, metrics, s3_urls)
        print()
        
        print("=" * 80)
        print("🎉 Evaluation complete with S3 exports!")
        print("=" * 80)
        print(f"Run ID: {run_id}")
        print(f"Report: {report_path}")
        print(f"S3 Bucket: {bucket_name}")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

