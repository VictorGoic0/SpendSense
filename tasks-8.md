## PR #34: AWS Deployment & Production Testing

### Initial Deployment
- [ ] 1. Configure AWS credentials: `aws configure`
- [ ] 2. Build SAM application: `sam build`
- [ ] 3. Deploy with guided mode: `sam deploy --guided`
- [ ] 4. Provide parameter values:
   - Stack name: spendsense-dev
   - AWS Region: us-east-1
   - OpenAI API Key: [your key]
   - Confirm changeset
- [ ] 5. Wait for deployment to complete

### Post-Deployment Verification
- [ ] 6. Get API Gateway URL from outputs
- [ ] 7. Test health endpoint: `curl {api-url}/`
- [ ] 8. Test GET /users endpoint
- [ ] 9. Verify CORS headers present
- [ ] 10. Check CloudWatch logs for errors

### Data Ingestion in Production
- [ ] 11. Update local scripts to use production API URL
- [ ] 12. Run data ingestion: `python scripts/test_ingest.py`
- [ ] 13. Verify data in database (Lambda will use /tmp SQLite)
- [ ] 14. Note: Data will reset on cold starts (expected for MVP)

### Compute Features in Production
- [ ] 15. Call feature computation endpoint for all users
- [ ] 16. May need to batch if Lambda timeout issues
- [ ] 17. Verify user_features table populated

### Assign Personas in Production
- [ ] 18. Call persona assignment for all users
- [ ] 19. Verify personas table populated
- [ ] 20. Check persona distribution

### Generate Recommendations in Production
- [ ] 21. Generate recommendations for test users
- [ ] 22. Verify recommendations created
- [ ] 23. Test approval workflow via API

### Frontend Connection to Production
- [ ] 24. Update frontend .env with production API URL
- [ ] 25. Rebuild frontend: `npm run build`
- [ ] 26. Test all frontend features against production API
- [ ] 27. Verify CORS working correctly

### Monitoring Setup
- [ ] 28. Configure CloudWatch alarms:
    - Lambda errors
    - API Gateway 5xx errors
    - High latency
- [ ] 29. Set up SNS topic for alerts
- [ ] 30. Test alerts by triggering errors

### Cost Monitoring
- [ ] 31. Enable cost allocation tags
- [ ] 32. Set up AWS Budget alert for $10 threshold
- [ ] 33. Monitor daily costs in billing dashboard
- [ ] 34. Review OpenAI API usage and costs

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