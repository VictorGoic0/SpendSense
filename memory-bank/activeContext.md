# Active Context: SpendSense

## Current Work Focus
**Status**: PR #2 Complete - Synthetic Data Generation Script Finished

## Recent Changes
- ✅ PR #2 Complete: All 38 tasks finished
- ✅ Synthetic data generation script implemented (`scripts/generate_synthetic_data.py`)
- ✅ Faker dependency added and installed (faker==20.1.0)
- ✅ User generation function: 71 customers + 4 operators, 30% consent rate
- ✅ Account generation function: 2-4 accounts per user (checking, savings, credit cards, investments)
- ✅ Transaction generation function: 150-300 transactions per user over 180-day window
- ✅ Liability generation function: Credit card liabilities with varied utilization patterns
- ✅ Main execution function: Orchestrates all generation and exports to JSON
- ✅ JSON seed files generated:
  - `data/synthetic_users.json`: 75 records (21KB)
  - `data/synthetic_accounts.json`: 272 records (104KB)
  - `data/synthetic_transactions.json`: 15,590 records (7.9MB)
  - `data/synthetic_liabilities.json`: 92 records (50KB)
- ✅ Persona patterns implemented in transaction generation:
  - High credit card usage
  - Recurring subscriptions
  - Regular savings deposits
  - Irregular income patterns
  - Regular biweekly payroll
- ✅ Data generation assumptions documented in script header

## Next Steps
1. **PR #3: Database Schema & SQLAlchemy Models** - Implement 10 database tables
   - Database configuration (SQLite setup)
   - User model
   - Account model
   - Transaction model
   - Liability model
   - UserFeature model
   - Persona model
   - Recommendation model
   - EvaluationMetric model
   - ConsentLog model
   - OperatorAction model
   - Database initialization on startup

## Active Decisions and Considerations

### Immediate Priorities
- **Database schema implementation** - Next task (PR #3)
- **Data ingestion endpoint** - Will need database models first
- **Feature detection pipeline** - Depends on database schema
- **UI components** - Can start after data ingestion endpoint is ready

### Technical Decisions Made
- **Node version** - Node.js 20 LTS (documented in techContext.md and .cursor/rules/)
- **Python version** - Python 3.9.6 currently (should upgrade to 3.11+)
- **Package management** - Consolidated root .gitignore (Python + Node patterns)
- **Shadcn/ui** - Using `shadcn` (not deprecated `shadcn-ui`)
- **Synthetic data format** - JSON files that can seed both SQLite and production databases
- **Random seed** - Set to 42 for reproducibility
- **Data generation patterns** - Persona patterns distributed across users for realistic behavioral signals

### Integration Points
- Frontend ↔ Backend: CORS configuration needed, API client setup in `frontend/src/lib/api.js`
- Backend ↔ Database: SQLAlchemy setup complete, models to be implemented (PR #3)
- Backend ↔ OpenAI: API key management via environment variables
- Backend ↔ AWS: S3 bucket setup pending
- Data Generation ↔ Database: JSON seed files ready for ingestion endpoint

## Current Blockers
None - Ready to proceed with PR #3 (Database Schema)

## Active Questions
1. Should we upgrade Python venv to 3.11+ before proceeding with database models?
2. Are AWS credentials configured for S3 exports?
3. Should we create the data ingestion endpoint before or after database models?

## Workflow Notes
- PR #1 complete (all 41 tasks checked off)
- PR #2 complete (all 38 tasks checked off)
- Following tasks-1.md structure (PR #3 next)
- Synthetic data generation produces JSON files that can be reused as seeds
- Data includes realistic persona patterns for testing feature detection
- All AI recommendations require operator approval before user visibility
- Consent is mandatory - no recommendations without opt-in

