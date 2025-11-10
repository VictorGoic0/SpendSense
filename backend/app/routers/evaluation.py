"""
Evaluation Router

Endpoints for running system evaluation metrics and retrieving evaluation history.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import sys
from pathlib import Path

from app.database import get_db
from app.models import EvaluationMetric
from app.schemas import EvaluationRequest
from app.services.evaluation_service import (
    compute_coverage_metrics,
    compute_explainability_metrics,
    compute_latency_metrics,
    compute_auditability_metrics,
    get_persona_distribution,
    get_recommendation_status_breakdown,
    export_user_features_to_parquet,
    export_evaluation_results_to_parquet,
    upload_to_s3,
    save_evaluation_metrics,
    generate_evaluation_report
)
import boto3
from botocore.exceptions import ClientError

router = APIRouter(prefix="/evaluate", tags=["evaluation"])


def run_evaluation_with_db(db: Session) -> tuple[str, dict, dict]:
    """
    Run complete evaluation and compute all metrics using provided database session.
    
    Args:
        db: Database session from FastAPI dependency
    
    Returns:
        Tuple of (run_id, metrics_dict, s3_urls_dict)
    """
    # Generate run_id with timestamp format: eval_YYYYMMDD_HHMMSS
    run_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
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
        
        # Save metrics to database
        save_evaluation_metrics(db, run_id, metrics)
        
        # Export to parquet and upload to S3
        bucket_name = os.getenv('S3_BUCKET_NAME', 'spendsense-analytics-goico')
        s3_urls = {}
        
        try:
            # Export user features (30d)
            features_30d_path = export_user_features_to_parquet(db, window_days=30, run_id=run_id)
            s3_key_30d = f"features/user_features_30d_{run_id}.parquet"
            presigned_url_30d = upload_to_s3(features_30d_path, s3_key_30d, bucket_name)
            s3_urls[s3_key_30d] = presigned_url_30d
            
            # Export user features (180d)
            features_180d_path = export_user_features_to_parquet(db, window_days=180, run_id=run_id)
            s3_key_180d = f"features/user_features_180d_{run_id}.parquet"
            presigned_url_180d = upload_to_s3(features_180d_path, s3_key_180d, bucket_name)
            s3_urls[s3_key_180d] = presigned_url_180d
            
            # Export evaluation results
            eval_path = export_evaluation_results_to_parquet(db, run_id=run_id)
            s3_key_eval = f"eval/evaluation_{run_id}.parquet"
            presigned_url_eval = upload_to_s3(eval_path, s3_key_eval, bucket_name)
            s3_urls[s3_key_eval] = presigned_url_eval
            
        except Exception as e:
            # Log error but don't fail the evaluation
            # S3 upload failures shouldn't prevent metrics from being returned
            pass
        
        return (run_id, metrics, s3_urls)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during evaluation: {str(e)}"
        )


@router.post("/")
async def evaluate(
    request: Optional[EvaluationRequest] = Body(default=None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Run evaluation and compute all metrics.
    
    This endpoint:
    1. Generates or uses provided run_id
    2. Computes all metrics (coverage, explainability, latency, auditability)
    3. Saves metrics to database
    4. Exports data to parquet and uploads to S3
    5. Returns metrics with S3 download URLs
    
    Args:
        request: Optional EvaluationRequest with run_id
        db: Database session
    
    Returns:
        Dictionary with:
        - run_id: Evaluation run identifier
        - metrics: All computed metrics
        - parquet_exports: S3 keys for exported files
        - download_urls: Pre-signed URLs for downloading files
    
    Raises:
        500: Server error during evaluation
    """
    try:
        # Extract run_id from request if provided
        requested_run_id = request.run_id if request else None
        
        # Run evaluation
        generated_run_id, metrics, s3_urls = run_evaluation_with_db(db)
        
        # Use provided run_id if given, otherwise use generated
        final_run_id = requested_run_id if requested_run_id else generated_run_id
        
        # If run_id was provided and different, update it in metrics
        if requested_run_id and requested_run_id != generated_run_id:
            # Update the run_id in the saved metrics record
            metric_record = db.query(EvaluationMetric).filter(
                EvaluationMetric.run_id == generated_run_id
            ).first()
            if metric_record:
                metric_record.run_id = requested_run_id
                db.commit()
            metrics["run_id"] = requested_run_id
            final_run_id = requested_run_id
        
        return {
            "run_id": final_run_id,
            "metrics": metrics,
            "parquet_exports": {
                key: key for key in s3_urls.keys()  # S3 keys
            },
            "download_urls": s3_urls  # Pre-signed URLs
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )


@router.get("/latest")
async def get_latest_evaluation(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the most recent evaluation metrics.
    
    Args:
        db: Database session
    
    Returns:
        Dictionary with latest evaluation metrics
    
    Raises:
        404: No evaluation metrics found
    """
    # Query evaluation_metrics table
    # Order by timestamp descending
    # Limit to 1 (most recent)
    metric = db.query(EvaluationMetric).order_by(
        EvaluationMetric.timestamp.desc()
    ).first()
    
    if not metric:
        raise HTTPException(
            status_code=404,
            detail="No evaluation metrics found"
        )
    
    # Parse details JSON if present
    import json
    details = {}
    if metric.details:
        try:
            details = json.loads(metric.details)
        except (json.JSONDecodeError, TypeError):
            details = {}
    
    return {
        "metric_id": metric.metric_id,
        "run_id": metric.run_id,
        "timestamp": metric.timestamp.isoformat() if metric.timestamp else None,
        "coverage": {
            "total_users": metric.total_users,
            "users_with_persona": metric.users_with_persona,
            "users_with_behaviors": metric.users_with_behaviors,
            "coverage_percentage": metric.coverage_percentage
        },
        "explainability": {
            "total_recommendations": metric.total_recommendations,
            "recommendations_with_rationale": metric.recommendations_with_rationale,
            "explainability_percentage": metric.explainability_percentage
        },
        "latency": {
            "avg_recommendation_latency_ms": metric.avg_recommendation_latency_ms,
            "p95_recommendation_latency_ms": metric.p95_recommendation_latency_ms
        },
        "auditability": {
            "recommendations_with_traces": metric.recommendations_with_traces,
            "auditability_percentage": metric.auditability_percentage
        },
        "details": details
    }


@router.get("/history")
async def get_evaluation_history(
    limit: int = Query(default=10, ge=1, le=100, description="Number of evaluation runs to return"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get evaluation history (list of recent evaluation runs).
    
    Args:
        limit: Maximum number of runs to return (default: 10, max: 100)
        db: Database session
    
    Returns:
        Dictionary with:
        - total: Total count of evaluation runs
        - runs: List of evaluation runs
    """
    # Query evaluation_metrics table
    # Order by timestamp descending
    metrics = db.query(EvaluationMetric).order_by(
        EvaluationMetric.timestamp.desc()
    ).limit(limit).all()
    
    # Get total count
    total_count = db.query(EvaluationMetric).count()
    
    # Parse details JSON for each metric
    import json
    runs = []
    for metric in metrics:
        details = {}
        if metric.details:
            try:
                details = json.loads(metric.details)
            except (json.JSONDecodeError, TypeError):
                details = {}
        
        runs.append({
            "metric_id": metric.metric_id,
            "run_id": metric.run_id,
            "timestamp": metric.timestamp.isoformat() if metric.timestamp else None,
            "coverage_percentage": metric.coverage_percentage,
            "explainability_percentage": metric.explainability_percentage,
            "avg_recommendation_latency_ms": metric.avg_recommendation_latency_ms,
            "auditability_percentage": metric.auditability_percentage,
            "details": details
        })
    
    return {
        "total": total_count,
        "runs": runs
    }


@router.get("/exports/latest")
async def get_latest_exports(
    limit: int = Query(default=10, ge=1, le=50, description="Number of exports to return"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List latest S3 exports (parquet files).
    
    This endpoint:
    1. Lists files in S3 bucket (features/ and eval/ prefixes)
    2. Gets last N files sorted by date
    3. Generates pre-signed URLs for each file
    
    Args:
        limit: Maximum number of exports to return (default: 10, max: 50)
        db: Database session (not used but kept for consistency)
    
    Returns:
        Dictionary with:
        - exports: List of export objects with file name, size, date, and download URL
    
    Raises:
        500: Server error (S3 access error)
    """
    try:
        bucket_name = os.getenv('S3_BUCKET_NAME', 'spendsense-analytics-goico')
        
        # Create boto3 S3 client
        s3_client = boto3.client('s3')
        
        # List files in S3 bucket with features/ and eval/ prefixes
        exports = []
        
        # List files in features/ prefix
        try:
            features_response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix='features/'
            )
            if 'Contents' in features_response:
                for obj in features_response['Contents']:
                    exports.append({
                        "key": obj['Key'],
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "prefix": "features"
                    })
        except ClientError as e:
            # If prefix doesn't exist, continue
            pass
        
        # List files in eval/ prefix
        try:
            eval_response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix='eval/'
            )
            if 'Contents' in eval_response:
                for obj in eval_response['Contents']:
                    exports.append({
                        "key": obj['Key'],
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "prefix": "eval"
                    })
        except ClientError as e:
            # If prefix doesn't exist, continue
            pass
        
        # Sort by last_modified descending (newest first)
        exports.sort(key=lambda x: x['last_modified'], reverse=True)
        
        # Limit to requested number
        exports = exports[:limit]
        
        # Generate pre-signed URLs for each file
        for export in exports:
            try:
                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': export['key']},
                    ExpiresIn=604800  # 7 days
                )
                export['download_url'] = presigned_url
            except ClientError as e:
                export['download_url'] = None
                export['error'] = str(e)
        
        return {
            "total": len(exports),
            "exports": exports
        }
    
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        raise HTTPException(
            status_code=500,
            detail=f"S3 access error: {error_code} - {error_message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )

