# Active Context: SpendSense

## Current Work Focus
**Status**: Project initialization - Memory bank setup

## Recent Changes
- Memory bank structure created
- Core documentation files established
- Project structure defined based on PRD
- Node.js 20 LTS specified and documented
- Package management rules created in `.cursor/rules/`

## Next Steps
1. **Review existing codebase** - Check what's already implemented in `backend/` and `frontend/`
2. **Assess current state** - Determine what components are complete vs. what needs to be built
3. **Prioritize MVP features** - Focus on Day 1 deliverables:
   - Synthetic data generation
   - Backend core (FastAPI + database schema)
   - Feature detection pipeline
   - React UI (operator + user views)
4. **Begin implementation** - Start with data foundation and backend core

## Active Decisions and Considerations

### Immediate Priorities
- **UI is MVP requirement** - Must be functional by end of Day 1 for integration testing
- **Synthetic data first** - Need 75 users with realistic profiles before anything else
- **Feature detection critical** - All downstream features depend on computed signals
- **Persona assignment** - Rules-based, deterministic logic (Day 2)

### Technical Decisions Pending
- **Package versions** - Verify all dependencies are latest stable builds (rule created)
- **Database location** - SQLite file path for local development
- **API base URL** - Configuration for local vs. AWS deployment

### Technical Decisions Made
- **Node version** - Node.js 20 LTS (documented in techContext.md and .cursor/rules/)

### Integration Points
- Frontend ↔ Backend: CORS configuration, API client setup
- Backend ↔ Database: SQLAlchemy models, connection pooling
- Backend ↔ OpenAI: API key management, error handling
- Backend ↔ AWS: S3 bucket setup, credentials configuration

## Current Blockers
None identified yet - project in initialization phase.

## Active Questions
1. What's the current state of `backend/` and `frontend/` directories?
2. Are there any existing implementations we should review?
3. Are AWS credentials already configured?

## Workflow Notes
- Follow PRD development plan (Day 1, Day 2, Day 3 structure)
- UI must be built on Day 1 (Hours 7-10) for integration testing
- All AI recommendations require operator approval before user visibility
- Consent is mandatory - no recommendations without opt-in

