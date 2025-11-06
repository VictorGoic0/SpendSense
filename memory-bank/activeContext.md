# Active Context: SpendSense

## Current Work Focus
**Status**: PR #1 Complete - Ready to begin PR #2 (Synthetic Data Generation)

## Recent Changes
- ✅ PR #1 Complete: All 41 tasks finished
- ✅ Backend structure initialized (FastAPI app, database setup, routers, services, utils)
- ✅ Frontend structure initialized (React 18, Vite, Shadcn/ui, TailwindCSS configured)
- ✅ Documentation created (README, DECISIONS.md, LIMITATIONS.md)
- ✅ Git repository initialized with consolidated .gitignore
- ✅ Node.js 20 LTS specified and documented
- ✅ Package management rules created in `.cursor/rules/`
- ✅ Environment variable template created (example-env.md)

## Next Steps
1. **PR #2: Synthetic Data Generation** - Create script to generate 75 synthetic users
   - Add faker dependency
   - Implement user generation function
   - Implement account generation function
   - Implement transaction generation function
   - Implement liability generation function
   - Create main execution function
   - Test and validate generated data

## Active Decisions and Considerations

### Immediate Priorities
- **Synthetic data generation** - Next task (PR #2)
- **UI is MVP requirement** - Frontend structure ready, components to be built
- **Feature detection critical** - Will depend on synthetic data being generated first
- **Persona assignment** - Rules-based, deterministic logic (Day 2)

### Technical Decisions Made
- **Node version** - Node.js 20 LTS (documented in techContext.md and .cursor/rules/)
- **Python version** - Python 3.11+ (using 3.9.6 currently, should upgrade)
- **Package management** - Consolidated root .gitignore (Python + Node patterns)
- **Shadcn/ui** - Using `shadcn` (not deprecated `shadcn-ui`)

### Integration Points
- Frontend ↔ Backend: CORS configuration needed, API client setup in `frontend/src/lib/api.js`
- Backend ↔ Database: SQLAlchemy setup complete, models to be implemented
- Backend ↔ OpenAI: API key management via environment variables
- Backend ↔ AWS: S3 bucket setup pending

## Current Blockers
None - Ready to proceed with PR #2

## Active Questions
1. Should we upgrade Python venv to 3.11+ before proceeding?
2. Are AWS credentials configured for S3 exports?

## Workflow Notes
- PR #1 complete (all 41 tasks checked off)
- Following tasks-1.md structure (PR #2 next)
- UI structure ready, components to be built after data ingestion
- All AI recommendations require operator approval before user visibility
- Consent is mandatory - no recommendations without opt-in

