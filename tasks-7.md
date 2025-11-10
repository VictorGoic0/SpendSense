# SpendSense Tasks - Part 7: Evaluation, Deployment & Testing

## PR #28: Evaluation Script - Metrics Computation

### Evaluation Script Setup
- [x] 1. Create `scripts/evaluate.py`
- [x] 2. Import required libraries: pandas, numpy, datetime, json
- [x] 3. Import database session and models
- [x] 4. Import boto3 for S3 operations

### Coverage Metrics
- [x] 5. Create `compute_coverage_metrics(db) -> dict` function:
- [x] 6. Query total users with consent_status=True
- [x] 7. Query count of users with persona assigned (30d window)
- [x] 8. Query count of users with ≥3 detected behaviors:
   - recurring_merchants >= 3 OR
   - net_savings_inflow > 0 OR
   - avg_utilization > 0
- [x] 9. Calculate coverage_percentage = (users_with_persona / total_users) * 100
- [x] 10. Return dict with coverage metrics

### Explainability Metrics
- [x] 11. Create `compute_explainability_metrics(db) -> dict` function:
- [x] 12. Query total count of recommendations
- [x] 13. Query count of recommendations with rationale not null and not empty
- [x] 14. Calculate explainability_percentage = (with_rationale / total) * 100
- [x] 15. Return dict with explainability metrics

### Latency Metrics
- [x] 16. Create `compute_latency_metrics(db) -> dict` function:
- [x] 17. Query all recommendations with generation_time_ms not null
- [x] 18. Extract generation_time_ms values into list
- [x] 19. Calculate average latency
- [x] 20. Calculate p95 latency using numpy.percentile()
- [x] 21. Return dict with latency metrics

### Auditability Metrics
- [x] 22. Create `compute_auditability_metrics(db) -> dict` function:
- [x] 23. Query total recommendations count
- [x] 24. All recommendations have decision traces (persona + features)
- [x] 25. Set auditability_percentage = 100.0
- [x] 26. Return dict with auditability metrics

### Persona Distribution
- [x] 27. Create `get_persona_distribution(db, window_days: int) -> dict` function:
- [x] 28. Query personas table grouped by persona_type
- [x] 29. Count records per persona type
- [x] 30. Return dict with counts per persona

### Recommendation Status Breakdown
- [x] 31. Create `get_recommendation_status_breakdown(db) -> dict` function:
- [x] 32. Query recommendations table grouped by status
- [x] 33. Count records per status
- [x] 34. Return dict with counts per status

### Main Evaluation Function
- [x] 35. Create `run_evaluation() -> tuple[str, dict]` function:
- [x] 36. Generate run_id with timestamp format: eval_YYYYMMDD_HHMMSS
- [x] 37. Call all metric computation functions
- [x] 38. Combine results into single metrics dict
- [x] 39. Calculate persona distribution
- [x] 40. Calculate recommendation status breakdown
- [x] 41. Print metrics to console (formatted)
- [x] 42. Return (run_id, metrics_dict)

### Save to Database
- [x] 43. Create `save_evaluation_metrics(db, run_id: str, metrics: dict)` function:
- [x] 44. Create EvaluationMetric model instance
- [x] 45. Populate all fields from metrics dict
- [x] 46. Add details field with JSON of extra info
- [x] 47. Commit to database
- [x] 48. Return metric record

### Testing Evaluation Script
- [x] 49. Add __main__ block to script
- [x] 50. Run evaluation: `python scripts/evaluate.py`
- [x] 51. Verify metrics printed to console
- [x] 52. Verify record created in evaluation_metrics table
- [x] 53. Check that all percentages = 100% (or close)
- [x] 54. Verify persona distribution shows all 5 types

### Performance Testing - OpenAI Latency Investigation
- [x] 55. Investigate 20-second average recommendation generation latency
- [x] 56. Implement detailed timing logs in recommendations.py:
   - SQL query duration tracking
   - OpenAI query duration tracking
   - Tone validation duration tracking
   - DB save duration tracking
   - Total request duration tracking
- [x] 57. Create `_write_timing_log()` function to output logs to JSON file
- [x] 58. Generate timing logs to `docs/recommendation_timing_logs.json`
- [x] 59. Identify bottleneck: OpenAI API call (~17,000ms out of ~17,081ms total)
- [x] 60. Test optimization strategy #1: Switch to gpt-3.5-turbo
- [x] 61. Record results: 67% faster (17s → 5.5s), most effective optimization
- [x] 62. Revert to gpt-4o-mini for quality
- [x] 63. Test optimization strategy #2: Reduce data sent to OpenAI
   - Reduce transactions from 10 → 5
   - Remove high_utilization_cards details
   - Remove recurring_merchants array
- [x] 64. Record results: No improvement (18.8s), context size not a factor
- [x] 65. Revert data reduction changes
- [x] 66. Test optimization strategy #3: Remove JSON mode from OpenAI call
- [x] 67. Record results: 35% slower (23s), JSON mode is beneficial
- [x] 68. Revert all optimization changes to original state
- [x] 69. Create `docs/x/` directory
- [x] 70. Create `docs/recommendation-latency-testing/recommendation_timing_results.md` with test results `recommendation_timing_results.md` and `recommendation_timing_logs.json`
- [x] 71. Create `docs/OPENAI_LATENCY_TESTING.md` with full methodology and findings
- [x] 72. Key finding documented: Model choice (gpt-4o-mini vs gpt-3.5-turbo) is the only significant performance factor
- [x] 73. Comment out timing log infrastructure in recommendations.py for future use
- [x] 74. Decision: Keep gpt-4o-mini for quality over speed in MVP
- [x] 75. Update memory bank with performance testing findings

---

## PR #29: Parquet Export & S3 Integration

### S3 Setup
- [x] 1. Create S3 bucket via AWS console or CLI
- [x] 2. Name: `spendsense-analytics-goico`
- [x] 3. Set bucket to private (block public access) - Already configured by default
- [x] 4. Create IAM policy for bucket access (using existing credentials)
- [x] 5. Add policy to user/role credentials (using existing credentials)
- [x] 6. Test bucket access with boto3

### Dependencies
- [x] 7. Add `boto3==1.29.7` to requirements.txt
- [x] 8. Add `pyarrow==14.0.1` to requirements.txt
- [x] 9. Install: `pip install boto3 pyarrow`
- [x] 10. Add AWS credentials to .env file:
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    - AWS_DEFAULT_REGION
    - S3_BUCKET_NAME

### Export User Features Function
- [x] 11. In evaluate.py, create `export_user_features_to_parquet(db, window_days: int, run_id: str) -> str`:
- [x] 12. Query all user_features for specified window_days
- [x] 13. Convert to pandas DataFrame using pd.read_sql()
- [x] 14. Define output path: `/tmp/user_features_{window_days}d_{run_id}.parquet`
- [x] 15. Export to parquet: `df.to_parquet(output_path)`
- [x] 16. Return local file path

### Upload to S3 Function
- [x] 17. Create `upload_to_s3(local_path: str, s3_key: str, bucket_name: str) -> str`:
- [x] 18. Create boto3 S3 client
- [x] 19. Upload file: `s3.upload_file(local_path, bucket_name, s3_key)`
- [x] 20. Generate pre-signed URL:
    - Expiry: 604800 seconds (7 days)
    - Method: get_object
- [x] 21. Return pre-signed URL
- [x] 22. Add error handling for S3 operations

### Export Evaluation Results
- [x] 23. Create `export_evaluation_results_to_parquet(db, run_id: str) -> str`:
- [x] 24. Query evaluation_metrics table for run_id
- [x] 25. Convert to pandas DataFrame
- [x] 26. Export to parquet: `/tmp/evaluation_{run_id}.parquet`
- [x] 27. Return local file path

### Integrate Exports into Evaluation
- [x] 28. Update run_evaluation() function:
- [x] 29. After saving metrics to DB, export user features (30d)
- [x] 30. Export user features (180d)
- [x] 31. Export evaluation results
- [x] 32. Upload all 3 files to S3
- [x] 33. Store S3 URLs in dict
- [x] 34. Return (run_id, metrics_dict, s3_urls_dict)

### Generate Evaluation Report JSON
- [x] 35. Create `generate_evaluation_report(run_id: str, metrics: dict, s3_urls: dict) -> None`:
- [x] 36. Combine all data into report dict:
    - run_id
    - timestamp
    - metrics
    - persona_distribution
    - recommendation_status
    - parquet_exports (S3 keys)
    - download_urls (pre-signed URLs)
- [x] 37. Write to file: `evaluation_report_{run_id}.json`
- [x] 38. Save in root directory
- [x] 39. Print success message with file location

### Testing Parquet Export
- [x] 40. Run evaluation script with S3 integration
- [x] 41. Verify 3 parquet files created in /tmp
- [x] 42. Verify files uploaded to S3 (check console)
- [x] 43. Verify pre-signed URLs work (try downloading)
- [x] 44. Verify JSON report created with all data
- [x] 45. Open parquet files in pandas to verify data

---

## PR #30: Evaluation API Endpoint

### Evaluation Router
- [ ] 1. Create `backend/app/routers/evaluation.py`
- [ ] 2. Create APIRouter with prefix="/evaluate"
- [ ] 3. Import evaluation functions from scripts (refactor to service if needed)

### Evaluate Endpoint
- [ ] 4. Create POST `/` endpoint:
- [ ] 5. Accept optional run_id in request body
- [ ] 6. If no run_id provided, generate one
- [ ] 7. Get database session
- [ ] 8. Call evaluation functions:
   - compute_coverage_metrics()
   - compute_explainability_metrics()
   - compute_latency_metrics()
   - compute_auditability_metrics()
- [ ] 9. Save metrics to database
- [ ] 10. Export to parquet and upload to S3
- [ ] 11. Return response with:
    - run_id
    - metrics
    - parquet_exports (S3 keys)
    - download_urls (pre-signed URLs)

### Get Latest Evaluation Endpoint
- [ ] 12. Create GET `/latest` endpoint:
- [ ] 13. Query evaluation_metrics table
- [ ] 14. Order by timestamp descending
- [ ] 15. Limit to 1 (most recent)
- [ ] 16. Return evaluation metrics

### Get Evaluation History Endpoint
- [ ] 17. Create GET `/history` endpoint:
- [ ] 18. Accept optional limit parameter (default: 10)
- [ ] 19. Query evaluation_metrics table
- [ ] 20. Order by timestamp descending
- [ ] 21. Return list of evaluation runs

### Exports List Endpoint
- [ ] 22. Create GET `/exports/latest` endpoint:
- [ ] 23. List files in S3 bucket (features/ and eval/ prefixes)
- [ ] 24. Get last 10 files sorted by date
- [ ] 25. For each file:
    - Get file name and size
    - Generate pre-signed URL
- [ ] 26. Return list of exports with download URLs

### Router Registration
- [ ] 27. Import evaluation router in main.py
- [ ] 28. Include router in FastAPI app

### Testing Evaluation API
- [ ] 29. Test POST /evaluate via Swagger UI
- [ ] 30. Verify metrics returned
- [ ] 31. Verify S3 URLs work
- [ ] 32. Test GET /latest endpoint
- [ ] 33. Test GET /exports/latest endpoint
- [ ] 34. Verify all endpoints return correct data

---

## PR #31: Frontend - Metrics Display in Operator Dashboard

### Update Dashboard to Call Evaluation
- [ ] 1. In OperatorDashboard.jsx, add "Run Evaluation" button
- [ ] 2. Import evaluate API function
- [ ] 3. Add state for evaluation results
- [ ] 4. On button click:
   - Call POST /evaluate endpoint
   - Show loading spinner
   - Update state with results
   - Show success toast

### Metrics Display Component
- [ ] 5. Create `frontend/src/components/MetricsDisplay.jsx`
- [ ] 6. Accept props: metrics object
- [ ] 7. Display coverage percentage with progress bar
- [ ] 8. Display explainability percentage with progress bar
- [ ] 9. Display average latency with badge
- [ ] 10. Display auditability percentage with progress bar
- [ ] 11. Color code: >95% green, 80-95% yellow, <80% red
- [ ] 12. Use Shadcn Progress and Badge components

### Download Links Section
- [ ] 13. Add section to dashboard for parquet downloads
- [ ] 14. Display list of available exports
- [ ] 15. Show file name, size, created date
- [ ] 16. Add download button per file (links to pre-signed URL)
- [ ] 17. Use Shadcn Button component

### Evaluation History
- [ ] 18. Add section showing last 5 evaluation runs
- [ ] 19. Display run_id, timestamp, and key metrics
- [ ] 20. Add "View Details" button per run
- [ ] 21. Format timestamps in readable format

### Real-time Updates
- [ ] 22. Add auto-refresh for metrics (every 60 seconds)
- [ ] 23. Show last updated timestamp
- [ ] 24. Add manual refresh button

### Testing Metrics Display
- [ ] 25. Navigate to operator dashboard
- [ ] 26. Click "Run Evaluation" button
- [ ] 27. Verify metrics displayed correctly
- [ ] 28. Verify progress bars accurate
- [ ] 29. Test download links for parquet files
- [ ] 30. Verify evaluation history shows recent runs

---

## PR #32: AWS SAM Template & Lambda Configuration

### SAM Template Creation
- [ ] 1. Create `template.yaml` in root directory
- [ ] 2. Set AWSTemplateFormatVersion: '2010-09-09'
- [ ] 3. Set Transform: AWS::Serverless-2016-10-31
- [ ] 4. Define Globals section:
   - Function timeout: 30
   - Function memory: 512MB
   - Runtime: python3.11

### Lambda Function Resource
- [ ] 5. Define SpendSenseAPI resource (AWS::Serverless::Function)
- [ ] 6. Set FunctionName: spendsense-api
- [ ] 7. Set Handler: app.main.handler
- [ ] 8. Set CodeUri: backend/
- [ ] 9. Define Events:
   - ApiEvent (Type: Api)
   - Path: /{proxy+}
   - Method: ANY
- [ ] 10. Define Environment Variables:
    - OPENAI_API_KEY (parameter reference)
    - DATABASE_URL (sqlite in /tmp for now)
    - S3_BUCKET_NAME (reference to bucket)
    - AWS_REGION

### S3 Bucket Resource
- [ ] 11. Define S3Bucket resource (AWS::S3::Bucket)
- [ ] 12. Set BucketName with stack name suffix
- [ ] 13. Set versioning enabled
- [ ] 14. Set encryption enabled
- [ ] 15. Reference bucket name in Lambda env vars

### IAM Role for Lambda
- [ ] 16. Define Lambda execution role
- [ ] 17. Add S3 permissions: GetObject, PutObject, ListBucket
- [ ] 18. Add CloudWatch Logs permissions
- [ ] 19. Attach role to Lambda function

### Parameters Section
- [ ] 20. Define OpenAIKey parameter (Type: String, NoEcho: true)
- [ ] 21. Define Environment parameter (Type: String, Default: dev)

### Outputs Section
- [ ] 22. Define ApiUrl output with API Gateway endpoint URL
- [ ] 23. Define S3BucketName output with bucket name
- [ ] 24. Define LambdaFunctionArn output

### Testing SAM Template
- [ ] 25. Validate template: `sam validate`
- [ ] 26. Check for syntax errors
- [ ] 27. Review IAM permissions
- [ ] 28. Ensure all references correct

---

## PR #33: Mangum Adapter & Lambda Deployment Prep

### Mangum Installation
- [ ] 1. Add `mangum==0.17.0` to requirements.txt
- [ ] 2. Install: `pip install mangum`

### Update FastAPI for Lambda
- [ ] 3. In backend/app/main.py, import Mangum
- [ ] 4. Create handler for Lambda:
   ```python
   from mangum import Mangum
   handler = Mangum(app)
   ```
- [ ] 5. Test locally to ensure no breaking changes

### Dependencies Layer (Optional)
- [ ] 6. Create requirements layer for faster deploys
- [ ] 7. Package dependencies separately
- [ ] 8. Update SAM template to reference layer

### Database Consideration
- [ ] 9. SQLite works in /tmp but resets per Lambda cold start
- [ ] 10. For MVP, accept this limitation
- [ ] 11. Add note in docs about migrating to RDS for production
- [ ] 12. Ensure synthetic data ingestion works on each cold start (or pre-load)

### Environment Variables
- [ ] 13. Create `.env.production` file with production values
- [ ] 14. Document all required env vars in README
- [ ] 15. Add instructions for setting params in SAM deploy

### Build Script
- [ ] 16. Create `scripts/build_lambda.sh` for packaging
- [ ] 17. Install dependencies in target directory
- [ ] 18. Copy application code
- [ ] 19. Create deployment package

### Testing Lambda Locally
- [ ] 20. Install SAM CLI if not installed
- [ ] 21. Build: `sam build`
- [ ] 22. Test locally: `sam local start-api`
- [ ] 23. Hit endpoints at http://localhost:3000
- [ ] 24. Verify all routes work
- [ ] 25. Check logs for errors