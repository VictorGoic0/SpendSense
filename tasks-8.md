## PR #34: Production Deployment (Netlify + Railway)

### Frontend Deployment to Netlify
- [x] 1. Deploy frontend to Netlify (completed in previous session)
- [x] 2. Configure environment variables in Netlify
- [x] 3. Verify frontend live and accessible
- [x] 4. Note: Backend URL will be updated after Railway deployment

### Backend Cleanup - Remove AWS Lambda Code
- [x] 5. Remove Mangum from `backend/requirements.txt`
- [x] 6. Update `backend/app/main.py`:
   - Remove Mangum import and handler
   - Keep FastAPI app as-is
   - Add standard Uvicorn startup for local development
- [x] 7. Delete AWS-specific files:
   - `template.yaml`
   - `samconfig.toml`
   - `.aws-sam/` directory (if exists)
- [x] 8. Restore full requirements:
   - Rename `requirements-dev.txt` back to `requirements.txt`
   - Keep pandas, numpy, faker (no Lambda size limits on Railway)

### Railway Setup & Deployment
- [x] 9. Install Railway CLI: `npm install -g @railway/cli`
- [x] 10. Login to Railway: `railway login`
- [x] 11. Initialize Railway project: `railway init`
- [x] 12. Link to Railway project (or create new one via CLI)
- [x] 13. Create Railway configuration file (optional but recommended)
- [x] 14. Set environment variables in Railway dashboard:
   - `OPENAI_API_KEY` - your OpenAI API key
   - `DATABASE_URL` - sqlite:///data/spendsense.db (Railway has persistent disk)
   - `S3_BUCKET_NAME` - spendsense-analytics-goico
   - `AWS_ACCESS_KEY_ID` - for S3 access
   - `AWS_SECRET_ACCESS_KEY` - for S3 access
   - `AWS_DEFAULT_REGION` - us-east-2
- [ ] 15. Configure Railway service settings:
   - Root directory: `/backend`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Or use Procfile (Railway auto-detects)
- [ ] 16. Deploy to Railway: `railway up`
- [ ] 17. Wait for deployment to complete (~30-60 seconds)
- [ ] 18. Get Railway URL from dashboard or CLI: `railway domain`

### Postgres Database Setup
- [ ] 19. Add Postgres service to Railway project (via dashboard or CLI)
- [ ] 20. Install PostgreSQL adapter: Add `psycopg2-binary` to `backend/requirements.txt`
- [ ] 21. Update `backend/app/database.py` to support both SQLite (local) and Postgres (production):
   - Check `DATABASE_URL` environment variable
   - Use SQLite if `sqlite://` in URL (local development)
   - Use Postgres if `postgresql://` in URL (production)
   - Update connection string handling
- [ ] 22. Update `backend/app/main.py` to use correct database URL from environment
- [ ] 23. Test database connection locally with Postgres (optional, using Docker)
- [ ] 24. Update Railway environment variable `DATABASE_URL` to use Postgres connection string from Railway
- [ ] 25. Verify database tables are created on first deploy
- [ ] 26. Test database persistence across Railway deployments

### Deployment Script & Migrations
- [ ] 27. Investigate current migration setup:
   - Review `backend/app/database.py` - `init_db()` runs on every startup
   - Review `backend/app/main.py` - `@app.on_event("startup")` calls `init_db()`
   - Note: Currently uses `Base.metadata.create_all()` + manual SQLite migrations
   - This won't work well for Postgres or production deployments
- [ ] 28. Add Alembic for database migrations:
   - Install Alembic: `pip install alembic`
   - Add to `backend/requirements.txt`
   - Initialize Alembic: `alembic init alembic` (from backend directory)
   - Configure `alembic.ini` to use `DATABASE_URL` from environment
   - Update `alembic/env.py` to import Base and models
   - Set `target_metadata = Base.metadata` in env.py
- [ ] 29. Create initial Alembic migration:
   - Generate initial migration: `alembic revision --autogenerate -m "Initial schema"`
   - Review generated migration file
   - Test migration: `alembic upgrade head` (creates all tables)
   - Verify tables match current SQLAlchemy models
- [ ] 30. Update `backend/app/main.py` for production:
   - Modify `init_db()` or startup event to check environment
   - For production (Railway): Skip automatic `init_db()` - rely on Alembic
   - For local dev: Optionally keep `init_db()` or use Alembic there too
   - Consider: Remove `@app.on_event("startup")` init_db() call entirely
   - Or: Make it conditional based on `ENVIRONMENT` variable
- [ ] 31. Create `backend/scripts/deploy.sh` (or `deploy.py`):
   - Script should run migrations explicitly (not on startup)
   - Script should optionally run seeds (when uncommented)
   - Script should then start the server (uvicorn command)
   - Structure:
     - Always run: `alembic upgrade head` (migrations)
     - Conditionally run: Seed data (when uncommented in script)
     - Always run: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] 32. Update `backend/Procfile` to use deployment script:
   - Change from: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Change to: `web: bash scripts/deploy.sh` (or `python scripts/deploy.py`)
   - Ensure script is executable: `chmod +x backend/scripts/deploy.sh`
- [ ] 33. Migrate existing manual migrations to Alembic:
   - Review `apply_migrations()` in `database.py`
   - Convert SQLite-specific migrations to Alembic migrations if needed
   - Test that existing databases can be migrated
   - Document migration strategy for Postgres
- [ ] 34. Test deployment script locally:
   - Run script manually
   - Verify Alembic migrations run (not automatic init_db)
   - Verify server starts
   - Test with seeds uncommented
   - Test with seeds commented
   - Verify no duplicate table creation errors
- [ ] 35. Document seed data process:
   - Add comment in deployment script explaining how to enable seeds
   - Note: Seeds should only run on initial setup or when explicitly needed
   - Document when to uncomment seed section
- [ ] 36. Verify deployment script runs on Railway deploy:
   - Check Railway logs for Alembic migration output
   - Verify `alembic upgrade head` runs successfully
   - Verify tables are created/updated via migrations (not create_all)
   - Verify server starts successfully
   - Confirm no automatic init_db() conflicts

### Evaluation Service Investigation
- [ ] 37. Investigate why evaluation router was disabled for Railway:
   - Check `backend/app/main.py` for disabled evaluation import
   - Review error logs from previous Railway deployments
   - Identify specific dependency or resource issue
- [ ] 38. Check evaluation service dependencies:
   - Review `backend/app/services/evaluation_service.py`
   - Identify pandas/numpy usage and requirements
   - Check if dependencies are in `requirements.txt`
- [ ] 39. Test evaluation service locally:
   - Ensure all dependencies installed
   - Run evaluation endpoint manually
   - Check for any import errors or missing dependencies
- [ ] 40. Resolve evaluation service issues:
   - Fix any missing dependencies
   - Resolve any import errors
   - Test evaluation endpoint works locally
- [ ] 41. Re-enable evaluation router in production:
   - Uncomment evaluation router in `backend/app/main.py`
   - Deploy to Railway
   - Verify evaluation endpoint accessible
   - Test evaluation functionality end-to-end

### Post-Deployment Verification
- [ ] 42. Test health endpoint: `curl {railway-url}/`
- [ ] 43. Verify response: `{"message": "SpendSense API is running"}`
- [ ] 44. Test GET /users endpoint: `curl {railway-url}/users`
- [ ] 45. Check Railway logs for any errors: `railway logs`
- [ ] 46. Verify CORS headers present (test from frontend domain)
- [ ] 47. Test API documentation: Visit `{railway-url}/docs`

### Data Ingestion in Production
- [ ] 48. Update local scripts with Railway API URL
- [ ] 49. Run data ingestion: `python backend/scripts/test_ingest.py`
- [ ] 50. Verify data persists in Postgres database
- [ ] 51. Note: Data will persist between deploys (Postgres is persistent)

### Compute Features in Production
- [ ] 52. Call feature computation endpoint for all users
- [ ] 53. Verify user_features table populated in Postgres
- [ ] 54. Check Railway metrics (CPU/RAM usage)

### Assign Personas in Production
- [ ] 55. Call persona assignment for all users
- [ ] 56. Verify personas table populated in Postgres
- [ ] 57. Check persona distribution

### Generate Recommendations in Production
- [ ] 58. Generate recommendations for test users
- [ ] 59. Verify recommendations created in Postgres
- [ ] 60. Test approval workflow via API

### Frontend Connection to Production Backend
- [ ] 61. Update Netlify environment variable `VITE_API_URL` to Railway URL
- [ ] 62. Trigger Netlify redeploy (or auto-deploys on env change)
- [ ] 63. Test all frontend features against Railway API
- [ ] 64. Verify CORS working correctly
- [ ] 65. Test complete user flow:
   - Operator dashboard loads
   - User list displays
   - User details show signals
   - Recommendations generate
   - Approval workflow works
   - User view shows recommendations

### Monitoring Setup
- [ ] 66. Configure Railway metrics tracking (built-in)
- [ ] 67. Set up Railway webhook notifications (optional)
- [ ] 68. Monitor deployment logs for errors
- [ ] 69. Set up uptime monitoring (UptimeRobot or similar - optional)

### Cost Monitoring
- [ ] 70. Check Railway usage dashboard
- [ ] 71. Monitor free tier credit ($5/month)
- [ ] 72. Review OpenAI API usage and costs
- [ ] 73. Set up Railway budget alert if needed

---

## PR #35: Unit Tests

### Test Setup
- [ ] 1. Install pytest: `pip install pytest httpx`
- [ ] 2. Create `backend/tests/conftest.py`
- [ ] 3. Define test database fixture (in-memory SQLite)
- [ ] 4. Define test client fixture (FastAPI TestClient)
- [ ] 5. Define sample data fixtures (users, accounts, transactions)

### Test Persona Assignment Logic
- [ ] 6. Create `backend/tests/test_personas.py`
- [ ] 7. Test `check_high_utilization()`:
   - Test with utilization >= 50% → True
   - Test with interest charges → True
   - Test with low utilization → False
- [ ] 8. Test `check_variable_income()`:
   - Test with pay gap > 45 days and buffer < 1 month → True
   - Test with regular income → False
- [ ] 9. Test `check_savings_builder()`:
   - Test with growth >= 2% → True
   - Test with net inflow >= $200 → True
   - Test with high credit utilization → False
- [ ] 10. Test `check_wealth_builder()`:
    - Test with all criteria met → True
    - Test with missing investment account → False

### Test Feature Detection
- [ ] 11. Create `backend/tests/test_feature_detection.py`
- [ ] 12. Test subscription detection:
    - Create mock transactions with recurring pattern
    - Verify recurring_merchants count correct
    - Verify subscription_spend_share calculated correctly
- [ ] 13. Test credit utilization calculation:
    - Create mock accounts with known utilization
    - Verify avg_utilization and max_utilization correct
    - Verify flags set correctly
- [ ] 14. Test emergency fund calculation:
    - Create mock savings and expense data
    - Verify emergency_fund_months calculated correctly

### Test Guardrails
- [ ] 15. Create `backend/tests/test_guardrails.py`
- [ ] 16. Test tone validation:
    - Test with shaming phrases → False
    - Test with empowering language → True
    - Test with neutral content → check for empowering keywords
- [ ] 17. Test consent enforcement:
    - Test with consented user → True
    - Test with non-consented user → False

### Test API Endpoints
- [ ] 18. Create `backend/tests/test_api.py`
- [ ] 19. Test POST /ingest:
    - Send valid data → 201 response
    - Verify database populated
    - Test with invalid data → 422 response
- [ ] 20. Test GET /users:
    - Verify returns user list
    - Test pagination
    - Test filters

### Run Tests
- [ ] 21. Run all tests: `pytest backend/tests/ -v`
- [ ] 22. Verify all 10+ tests pass
- [ ] 23. Check test coverage: `pytest --cov=backend/app`
- [ ] 24. Aim for >70% coverage on core logic

### CI/CD Integration (Optional)
- [ ] 25. Create `.github/workflows/test.yml`
- [ ] 26. Define GitHub Actions workflow:
    - Checkout code
    - Setup Python
    - Install dependencies
    - Run tests
    - Report coverage
- [ ] 27. Configure to run on PR and push to main

---

## PR #36: Documentation & Final Polish

### README Update
- [ ] 1. Update README.md with comprehensive setup instructions
- [ ] 2. Add sections:
   - Project overview
   - Prerequisites (Python 3.11+, Node 18+, AWS account, OpenAI API key)
   - Local setup (backend + frontend)
   - Data generation and ingestion
   - Feature computation and persona assignment
   - Running the application
   - AWS deployment
   - Testing
- [ ] 3. Add screenshots of UI
- [ ] 4. Add architecture diagram (create simple diagram)

### API Documentation
- [ ] 5. Verify Swagger UI accessible at /docs
- [ ] 6. Add description fields to all endpoints
- [ ] 7. Add example request/response bodies
- [ ] 8. Document error responses

### Decision Log
- [ ] 9. Update docs/DECISIONS.md with key decisions:
   - Why FastAPI: async support, auto-docs, Python ecosystem
   - Why SQLite for MVP: zero setup, sufficient for demo
   - Why 5 personas: covers major financial archetypes
   - Why GPT-4o-mini: cost-effective, sufficient quality
   - Why Shadcn/ui: LLM-friendly, modern, accessible
   - Why UI on Day 1: enables early integration testing
   - Why AWS Lambda: serverless, cost-effective for MVP
- [ ] 10. Document trade-offs and alternatives considered

### Limitations Document
- [ ] 11. Update docs/LIMITATIONS.md:
    - Synthetic data limitations
    - Educational content only (not financial advice)
    - Persona simplification (real users may not fit neatly)
    - AI output variability
    - SQLite scalability (recommend RDS for production)
    - No authentication in MVP
    - Lambda cold starts and /tmp database resets
- [ ] 12. Add recommendations for production deployment

### Code Comments
- [ ] 13. Add docstrings to all service functions
- [ ] 14. Add type hints throughout codebase
- [ ] 15. Add inline comments for complex logic
- [ ] 16. Document edge cases and assumptions

### Cleanup
- [ ] 17. Remove unused imports
- [ ] 18. Remove commented-out code
- [ ] 19. Format code with black: `black backend/`
- [ ] 20. Lint code with flake8: `flake8 backend/`
- [ ] 21. Fix any linting errors

### Final Testing Checklist
- [ ] 22. Test complete end-to-end flow:
    - Generate synthetic data ✓
    - Ingest data ✓
    - Compute features ✓
    - Assign personas ✓
    - Generate recommendations ✓
    - Approve recommendations ✓
    - User views recommendations ✓
    - Run evaluation ✓
    - Export to S3 ✓
- [ ] 23. Test all error cases
- [ ] 24. Test on different screen sizes (responsive)
- [ ] 25. Test with different browsers

### Demo Preparation
- [ ] 26. Create demo script (step-by-step)
- [ ] 27. Prepare test users with interesting data
- [ ] 28. Create demo video (5-10 minutes):
    - Show data ingestion
    - Show operator dashboard
    - Show user detail with signals
    - Show recommendation generation
    - Show approval workflow
    - Show user view with recommendations
    - Show evaluation metrics
- [ ] 29. Upload demo video to YouTube or similar

### Submission Preparation
- [ ] 30. Create root `.gitignore` combining all patterns
- [ ] 31. Verify no secrets in repository
- [ ] 32. Create final git commit
- [ ] 33. Push to GitHub repository
- [ ] 34. Create GitHub repository README badges (if applicable)
- [ ] 35. Write submission email/form with:
    - GitHub repo link
    - Demo video link
    - Brief technical writeup (1-2 pages)
    - Highlights of AI integration
    - Performance metrics
    - Known limitations
- [ ] 36. Submit project