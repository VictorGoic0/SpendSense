# SpendSense Tasks - Part 7: Evaluation, Deployment & Testing

## PR #28: Evaluation Script - Metrics Computation

### Evaluation Script Setup
1. Create `scripts/evaluate.py`
2. Import required libraries: pandas, numpy, datetime, json
3. Import database session and models
4. Import boto3 for S3 operations

### Coverage Metrics
5. Create `compute_coverage_metrics(db) -> dict` function:
6. Query total users with consent_status=True
7. Query count of users with persona assigned (30d window)
8. Query count of users with ≥3 detected behaviors:
   - recurring_merchants >= 3 OR
   - net_savings_inflow > 0 OR
   - avg_utilization > 0
9. Calculate coverage_percentage = (users_with_persona / total_users) * 100
10. Return dict with coverage metrics

### Explainability Metrics
11. Create `compute_explainability_metrics(db) -> dict` function:
12. Query total count of recommendations
13. Query count of recommendations with rationale not null and not empty
14. Calculate explainability_percentage = (with_rationale / total) * 100
15. Return dict with explainability metrics

### Latency Metrics
16. Create `compute_latency_metrics(db) -> dict` function:
17. Query all recommendations with generation_time_ms not null
18. Extract generation_time_ms values into list
19. Calculate average latency
20. Calculate p95 latency using numpy.percentile()
21. Return dict with latency metrics

### Auditability Metrics
22. Create `compute_auditability_metrics(db) -> dict` function:
23. Query total recommendations count
24. All recommendations have decision traces (persona + features)
25. Set auditability_percentage = 100.0
26. Return dict with auditability metrics

### Persona Distribution
27. Create `get_persona_distribution(db, window_days: int) -> dict` function:
28. Query personas table grouped by persona_type
29. Count records per persona type
30. Return dict with counts per persona

### Recommendation Status Breakdown
31. Create `get_recommendation_status_breakdown(db) -> dict` function:
32. Query recommendations table grouped by status
33. Count records per status
34. Return dict with counts per status

### Main Evaluation Function
35. Create `run_evaluation() -> tuple[str, dict]` function:
36. Generate run_id with timestamp format: eval_YYYYMMDD_HHMMSS
37. Call all metric computation functions
38. Combine results into single metrics dict
39. Calculate persona distribution
40. Calculate recommendation status breakdown
41. Print metrics to console (formatted)
42. Return (run_id, metrics_dict)

### Save to Database
43. Create `save_evaluation_metrics(db, run_id: str, metrics: dict)` function:
44. Create EvaluationMetric model instance
45. Populate all fields from metrics dict
46. Add details field with JSON of extra info
47. Commit to database
48. Return metric record

### Testing Evaluation Script
49. Add __main__ block to script
50. Run evaluation: `python scripts/evaluate.py`
51. Verify metrics printed to console
52. Verify record created in evaluation_metrics table
53. Check that all percentages = 100% (or close)
54. Verify persona distribution shows all 5 types

---

## PR #29: Parquet Export & S3 Integration

### S3 Setup
1. Create S3 bucket via AWS console or CLI
2. Name: `spendsense-analytics-{random-suffix}`
3. Set bucket to private (block public access)
4. Create IAM policy for bucket access
5. Add policy to user/role credentials
6. Test bucket access with boto3

### Dependencies
7. Add `boto3==1.29.7` to requirements.txt
8. Add `pyarrow==14.0.1` to requirements.txt
9. Install: `pip install boto3 pyarrow`
10. Add AWS credentials to .env file:
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    - AWS_DEFAULT_REGION
    - S3_BUCKET_NAME

### Export User Features Function
11. In evaluate.py, create `export_user_features_to_parquet(db, window_days: int, run_id: str) -> str`:
12. Query all user_features for specified window_days
13. Convert to pandas DataFrame using pd.read_sql()
14. Define output path: `/tmp/user_features_{window_days}d_{run_id}.parquet`
15. Export to parquet: `df.to_parquet(output_path)`
16. Return local file path

### Upload to S3 Function
17. Create `upload_to_s3(local_path: str, s3_key: str, bucket_name: str) -> str`:
18. Create boto3 S3 client
19. Upload file: `s3.upload_file(local_path, bucket_name, s3_key)`
20. Generate pre-signed URL:
    - Expiry: 604800 seconds (7 days)
    - Method: get_object
21. Return pre-signed URL
22. Add error handling for S3 operations

### Export Evaluation Results
23. Create `export_evaluation_results_to_parquet(db, run_id: str) -> str`:
24. Query evaluation_metrics table for run_id
25. Convert to pandas DataFrame
26. Export to parquet: `/tmp/evaluation_{run_id}.parquet`
27. Return local file path

### Integrate Exports into Evaluation
28. Update run_evaluation() function:
29. After saving metrics to DB, export user features (30d)
30. Export user features (180d)
31. Export evaluation results
32. Upload all 3 files to S3
33. Store S3 URLs in dict
34. Return (run_id, metrics_dict, s3_urls_dict)

### Generate Evaluation Report JSON
35. Create `generate_evaluation_report(run_id: str, metrics: dict, s3_urls: dict) -> None`:
36. Combine all data into report dict:
    - run_id
    - timestamp
    - metrics
    - persona_distribution
    - recommendation_status
    - parquet_exports (S3 keys)
    - download_urls (pre-signed URLs)
37. Write to file: `evaluation_report_{run_id}.json`
38. Save in root directory
39. Print success message with file location

### Testing Parquet Export
40. Run evaluation script with S3 integration
41. Verify 3 parquet files created in /tmp
42. Verify files uploaded to S3 (check console)
43. Verify pre-signed URLs work (try downloading)
44. Verify JSON report created with all data
45. Open parquet files in pandas to verify data

---

## PR #30: Evaluation API Endpoint

### Evaluation Router
1. Create `backend/app/routers/evaluation.py`
2. Create APIRouter with prefix="/evaluate"
3. Import evaluation functions from scripts (refactor to service if needed)

### Evaluate Endpoint
4. Create POST `/` endpoint:
5. Accept optional run_id in request body
6. If no run_id provided, generate one
7. Get database session
8. Call evaluation functions:
   - compute_coverage_metrics()
   - compute_explainability_metrics()
   - compute_latency_metrics()
   - compute_auditability_metrics()
9. Save metrics to database
10. Export to parquet and upload to S3
11. Return response with:
    - run_id
    - metrics
    - parquet_exports (S3 keys)
    - download_urls (pre-signed URLs)

### Get Latest Evaluation Endpoint
12. Create GET `/latest` endpoint:
13. Query evaluation_metrics table
14. Order by timestamp descending
15. Limit to 1 (most recent)
16. Return evaluation metrics

### Get Evaluation History Endpoint
17. Create GET `/history` endpoint:
18. Accept optional limit parameter (default: 10)
19. Query evaluation_metrics table
20. Order by timestamp descending
21. Return list of evaluation runs

### Exports List Endpoint
22. Create GET `/exports/latest` endpoint:
23. List files in S3 bucket (features/ and eval/ prefixes)
24. Get last 10 files sorted by date
25. For each file:
    - Get file name and size
    - Generate pre-signed URL
26. Return list of exports with download URLs

### Router Registration
27. Import evaluation router in main.py
28. Include router in FastAPI app

### Testing Evaluation API
29. Test POST /evaluate via Swagger UI
30. Verify metrics returned
31. Verify S3 URLs work
32. Test GET /latest endpoint
33. Test GET /exports/latest endpoint
34. Verify all endpoints return correct data

---

## PR #31: Frontend - Metrics Display in Operator Dashboard

### Update Dashboard to Call Evaluation
1. In OperatorDashboard.jsx, add "Run Evaluation" button
2. Import evaluate API function
3. Add state for evaluation results
4. On button click:
   - Call POST /evaluate endpoint
   - Show loading spinner
   - Update state with results
   - Show success toast

### Metrics Display Component
5. Create `frontend/src/components/MetricsDisplay.jsx`
6. Accept props: metrics object
7. Display coverage percentage with progress bar
8. Display explainability percentage with progress bar
9. Display average latency with badge
10. Display auditability percentage with progress bar
11. Color code: >95% green, 80-95% yellow, <80% red
12. Use Shadcn Progress and Badge components

### Download Links Section
13. Add section to dashboard for parquet downloads
14. Display list of available exports
15. Show file name, size, created date
16. Add download button per file (links to pre-signed URL)
17. Use Shadcn Button component

### Evaluation History
18. Add section showing last 5 evaluation runs
19. Display run_id, timestamp, and key metrics
20. Add "View Details" button per run
21. Format timestamps in readable format

### Real-time Updates
22. Add auto-refresh for metrics (every 60 seconds)
23. Show last updated timestamp
24. Add manual refresh button

### Testing Metrics Display
25. Navigate to operator dashboard
26. Click "Run Evaluation" button
27. Verify metrics displayed correctly
28. Verify progress bars accurate
29. Test download links for parquet files
30. Verify evaluation history shows recent runs

---

## PR #32: AWS SAM Template & Lambda Configuration

### SAM Template Creation
1. Create `template.yaml` in root directory
2. Set AWSTemplateFormatVersion: '2010-09-09'
3. Set Transform: AWS::Serverless-2016-10-31
4. Define Globals section:
   - Function timeout: 30
   - Function memory: 512MB
   - Runtime: python3.11

### Lambda Function Resource
5. Define SpendSenseAPI resource (AWS::Serverless::Function)
6. Set FunctionName: spendsense-api
7. Set Handler: app.main.handler
8. Set CodeUri: backend/
9. Define Events:
   - ApiEvent (Type: Api)
   - Path: /{proxy+}
   - Method: ANY
10. Define Environment Variables:
    - OPENAI_API_KEY (parameter reference)
    - DATABASE_URL (sqlite in /tmp for now)
    - S3_BUCKET_NAME (reference to bucket)
    - AWS_REGION

### S3 Bucket Resource
11. Define S3Bucket resource (AWS::S3::Bucket)
12. Set BucketName with stack name suffix
13. Set versioning enabled
14. Set encryption enabled
15. Reference bucket name in Lambda env vars

### IAM Role for Lambda
16. Define Lambda execution role
17. Add S3 permissions: GetObject, PutObject, ListBucket
18. Add CloudWatch Logs permissions
19. Attach role to Lambda function

### Parameters Section
20. Define OpenAIKey parameter (Type: String, NoEcho: true)
21. Define Environment parameter (Type: String, Default: dev)

### Outputs Section
22. Define ApiUrl output with API Gateway endpoint URL
23. Define S3BucketName output with bucket name
24. Define LambdaFunctionArn output

### Testing SAM Template
25. Validate template: `sam validate`
26. Check for syntax errors
27. Review IAM permissions
28. Ensure all references correct

---

## PR #33: Mangum Adapter & Lambda Deployment Prep

### Mangum Installation
1. Add `mangum==0.17.0` to requirements.txt
2. Install: `pip install mangum`

### Update FastAPI for Lambda
3. In backend/app/main.py, import Mangum
4. Create handler for Lambda:
   ```python
   from mangum import Mangum
   handler = Mangum(app)
   ```
5. Test locally to ensure no breaking changes

### Dependencies Layer (Optional)
6. Create requirements layer for faster deploys
7. Package dependencies separately
8. Update SAM template to reference layer

### Database Consideration
9. SQLite works in /tmp but resets per Lambda cold start
10. For MVP, accept this limitation
11. Add note in docs about migrating to RDS for production
12. Ensure synthetic data ingestion works on each cold start (or pre-load)

### Environment Variables
13. Create `.env.production` file with production values
14. Document all required env vars in README
15. Add instructions for setting params in SAM deploy

### Build Script
16. Create `scripts/build_lambda.sh` for packaging
17. Install dependencies in target directory
18. Copy application code
19. Create deployment package

### Testing Lambda Locally
20. Install SAM CLI if not installed
21. Build: `sam build`
22. Test locally: `sam local start-api`
23. Hit endpoints at http://localhost:3000
24. Verify all routes work
25. Check logs for errors

---

## PR #34: AWS Deployment & Production Testing

### Initial Deployment
1. Configure AWS credentials: `aws configure`
2. Build SAM application: `sam build`
3. Deploy with guided mode: `sam deploy --guided`
4. Provide parameter values:
   - Stack name: spendsense-dev
   - AWS Region: us-east-1
   - OpenAI API Key: [your key]
   - Confirm changeset
5. Wait for deployment to complete

### Post-Deployment Verification
6. Get API Gateway URL from outputs
7. Test health endpoint: `curl {api-url}/`
8. Test GET /users endpoint
9. Verify CORS headers present
10. Check CloudWatch logs for errors

### Data Ingestion in Production
11. Update local scripts to use production API URL
12. Run data ingestion: `python scripts/test_ingest.py`
13. Verify data in database (Lambda will use /tmp SQLite)
14. Note: Data will reset on cold starts (expected for MVP)

### Compute Features in Production
15. Call feature computation endpoint for all users
16. May need to batch if Lambda timeout issues
17. Verify user_features table populated

### Assign Personas in Production
18. Call persona assignment for all users
19. Verify personas table populated
20. Check persona distribution

### Generate Recommendations in Production
21. Generate recommendations for test users
22. Verify recommendations created
23. Test approval workflow via API

### Frontend Connection to Production
24. Update frontend .env with production API URL
25. Rebuild frontend: `npm run build`
26. Test all frontend features against production API
27. Verify CORS working correctly

### Monitoring Setup
28. Configure CloudWatch alarms:
    - Lambda errors
    - API Gateway 5xx errors
    - High latency
29. Set up SNS topic for alerts
30. Test alerts by triggering errors

### Cost Monitoring
31. Enable cost allocation tags
32. Set up AWS Budget alert for $10 threshold
33. Monitor daily costs in billing dashboard
34. Review OpenAI API usage and costs

---

## PR #35: Unit Tests

### Test Setup
1. Install pytest: `pip install pytest httpx`
2. Create `backend/tests/conftest.py`
3. Define test database fixture (in-memory SQLite)
4. Define test client fixture (FastAPI TestClient)
5. Define sample data fixtures (users, accounts, transactions)

### Test Persona Assignment Logic
6. Create `backend/tests/test_personas.py`
7. Test `check_high_utilization()`:
   - Test with utilization >= 50% → True
   - Test with interest charges → True
   - Test with low utilization → False
8. Test `check_variable_income()`:
   - Test with pay gap > 45 days and buffer < 1 month → True
   - Test with regular income → False
9. Test `check_savings_builder()`:
   - Test with growth >= 2% → True
   - Test with net inflow >= $200 → True
   - Test with high credit utilization → False
10. Test `check_wealth_builder()`:
    - Test with all criteria met → True
    - Test with missing investment account → False

### Test Feature Detection
11. Create `backend/tests/test_feature_detection.py`
12. Test subscription detection:
    - Create mock transactions with recurring pattern
    - Verify recurring_merchants count correct
    - Verify subscription_spend_share calculated correctly
13. Test credit utilization calculation:
    - Create mock accounts with known utilization
    - Verify avg_utilization and max_utilization correct
    - Verify flags set correctly
14. Test emergency fund calculation:
    - Create mock savings and expense data
    - Verify emergency_fund_months calculated correctly

### Test Guardrails
15. Create `backend/tests/test_guardrails.py`
16. Test tone validation:
    - Test with shaming phrases → False
    - Test with empowering language → True
    - Test with neutral content → check for empowering keywords
17. Test consent enforcement:
    - Test with consented user → True
    - Test with non-consented user → False

### Test API Endpoints
18. Create `backend/tests/test_api.py`
19. Test POST /ingest:
    - Send valid data → 201 response
    - Verify database populated
    - Test with invalid data → 422 response
20. Test GET /users:
    - Verify returns user list
    - Test pagination
    - Test filters

### Run Tests
21. Run all tests: `pytest backend/tests/ -v`
22. Verify all 10+ tests pass
23. Check test coverage: `pytest --cov=backend/app`
24. Aim for >70% coverage on core logic

### CI/CD Integration (Optional)
25. Create `.github/workflows/test.yml`
26. Define GitHub Actions workflow:
    - Checkout code
    - Setup Python
    - Install dependencies
    - Run tests
    - Report coverage
27. Configure to run on PR and push to main

---

## PR #36: Documentation & Final Polish

### README Update
1. Update README.md with comprehensive setup instructions
2. Add sections:
   - Project overview
   - Prerequisites (Python 3.11+, Node 18+, AWS account, OpenAI API key)
   - Local setup (backend + frontend)
   - Data generation and ingestion
   - Feature computation and persona assignment
   - Running the application
   - AWS deployment
   - Testing
3. Add screenshots of UI
4. Add architecture diagram (create simple diagram)

### API Documentation
5. Verify Swagger UI accessible at /docs
6. Add description fields to all endpoints
7. Add example request/response bodies
8. Document error responses

### Decision Log
9. Update docs/DECISIONS.md with key decisions:
   - Why FastAPI: async support, auto-docs, Python ecosystem
   - Why SQLite for MVP: zero setup, sufficient for demo
   - Why 5 personas: covers major financial archetypes
   - Why GPT-4o-mini: cost-effective, sufficient quality
   - Why Shadcn/ui: LLM-friendly, modern, accessible
   - Why UI on Day 1: enables early integration testing
   - Why AWS Lambda: serverless, cost-effective for MVP
10. Document trade-offs and alternatives considered

### Limitations Document
11. Update docs/LIMITATIONS.md:
    - Synthetic data limitations
    - Educational content only (not financial advice)
    - Persona simplification (real users may not fit neatly)
    - AI output variability
    - SQLite scalability (recommend RDS for production)
    - No authentication in MVP
    - Lambda cold starts and /tmp database resets
12. Add recommendations for production deployment

### Code Comments
13. Add docstrings to all service functions
14. Add type hints throughout codebase
15. Add inline comments for complex logic
16. Document edge cases and assumptions

### Cleanup
17. Remove unused imports
18. Remove commented-out code
19. Format code with black: `black backend/`
20. Lint code with flake8: `flake8 backend/`
21. Fix any linting errors

### Final Testing Checklist
22. Test complete end-to-end flow:
    - Generate synthetic data ✓
    - Ingest data ✓
    - Compute features ✓
    - Assign personas ✓
    - Generate recommendations ✓
    - Approve recommendations ✓
    - User views recommendations ✓
    - Run evaluation ✓
    - Export to S3 ✓
23. Test all error cases
24. Test on different screen sizes (responsive)
25. Test with different browsers

### Demo Preparation
26. Create demo script (step-by-step)
27. Prepare test users with interesting data
28. Create demo video (5-10 minutes):
    - Show data ingestion
    - Show operator dashboard
    - Show user detail with signals
    - Show recommendation generation
    - Show approval workflow
    - Show user view with recommendations
    - Show evaluation metrics
29. Upload demo video to YouTube or similar

### Submission Preparation
30. Create root `.gitignore` combining all patterns
31. Verify no secrets in repository
32. Create final git commit
33. Push to GitHub repository
34. Create GitHub repository README badges (if applicable)
35. Write submission email/form with:
    - GitHub repo link
    - Demo video link
    - Brief technical writeup (1-2 pages)
    - Highlights of AI integration
    - Performance metrics
    - Known limitations
36. Submit project

---

## Project Complete! 🎉

You now have a fully functional SpendSense MVP with:
- ✅ Synthetic data generation (75 users)
- ✅ Feature detection (4 signal types)
- ✅ Persona assignment (5 personas)
- ✅ AI-powered recommendations (OpenAI GPT-4o-mini)
- ✅ Approval workflow with guardrails
- ✅ Full-stack web application (React + FastAPI)
- ✅ Evaluation system with S3 exports
- ✅ AWS Lambda deployment
- ✅ 10+ unit tests
- ✅ Comprehensive documentation

Total development time: ~20 hours over 2-4 days
