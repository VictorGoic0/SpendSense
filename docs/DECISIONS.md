# Decision Log

This document tracks key architectural and technical decisions made during the development of SpendSense.

## Technology Choices

### FastAPI
**Decision**: Use FastAPI for the backend API framework
**Rationale**: 
- Python-based, ideal for data processing pipelines (pandas, feature engineering)
- Built-in async support for concurrent requests
- Auto-generated API documentation
- Easy integration with SQLAlchemy

### SQLite for MVP
**Decision**: Use SQLite for MVP, with migration path to PostgreSQL
**Rationale**:
- Zero setup required
- Sufficient for 75 users in MVP
- Easy migration path to PostgreSQL for production
- File-based, easy to backup/restore

### SQLite WAL Mode for Concurrency
**Decision**: Enable WAL (Write-Ahead Logging) mode for SQLite to support concurrent reads during writes
**Rationale**:
- Multiple uvicorn workers need concurrent database access
- Default SQLite mode blocks all reads during write transactions
- WAL mode allows multiple readers while a writer is active
- Prevents user list queries from hanging during recommendation generation
- Essential for multi-worker FastAPI deployment
**Implementation**:
- Enabled via SQLAlchemy event listener in `backend/app/database.py`
- Runs `PRAGMA journal_mode=WAL` on every database connection
- Creates `spendsense.db-wal` and `spendsense.db-shm` files (normal, managed by SQLite)
- Location: `backend/app/database.py` lines 23-28
**Trade-offs**:
- Backup complexity: Must backup both main file and WAL file, or checkpoint before backup
- Network file systems: WAL mode doesn't work on network-mounted drives (NFS, SMB)
- WAL file growth: Can grow if checkpoints don't run (SQLite auto-checkpoints periodically)
- Recovery: If WAL file is corrupted, recent transactions might be lost
**Mitigation**:
- For production backups, run `PRAGMA wal_checkpoint(TRUNCATE)` before backup
- WAL mode is SQLite-specific and won't be needed when migrating to PostgreSQL

### React 18 + Vite
**Decision**: Use React 18 with Vite as build tool
**Rationale**:
- Modern React features
- Fast development experience with Vite
- Good compatibility with Shadcn/ui components

### Shadcn/ui Component Library
**Decision**: Use Shadcn/ui for UI components
**Rationale**:
- LLM-friendly component structure
- Modern, accessible components
- TailwindCSS-based, easy to customize
- Copy-paste components (not a dependency)

### OpenAI GPT-4o-mini
**Decision**: Use GPT-4o-mini for recommendation generation
**Rationale**:
- Cost-effective for MVP (~$0.15/$0.60 per 1M tokens)
- Sufficient quality for educational content
- Lower latency than GPT-4
- Can upgrade specific personas to GPT-4o if needed

### Separate Endpoints Per Persona
**Decision**: Create 5 separate OpenAI endpoints (one per persona)
**Rationale**:
- Dedicated system prompts optimized per persona
- Better context management (only relevant signals passed)
- Easier to tune tone and focus per persona
- Cost tracking per persona
- A/B testing individual personas

### Rules-Based Persona Assignment
**Decision**: Use deterministic rules-based logic instead of ML
**Rationale**:
- Fast and deterministic
- Fully explainable (no black box)
- Easy to debug and adjust
- No training data required

### UI on Day 1
**Decision**: Build React UI as MVP requirement on Day 1
**Rationale**:
- Essential for integration testing
- Ensures end-to-end flow works early
- Operator approval workflow requires UI
- User consent management requires UI

## Data Architecture Decisions

### Metadata Exclusion from Database
**Decision**: Exclude `token_usage` and `estimated_cost_usd` from recommendation metadata stored in database
**Rationale**:
- Token usage and cost data are operational metrics, not business data
- Reduces database storage requirements
- Keeps database schema focused on user-facing data
- Cost tracking can be done via logging/monitoring systems
**Implementation**:
- These fields are included in metadata during OpenAI API response processing
- Stripped from metadata before saving to `metadata_json` field in database
- Still available in logs and API responses for monitoring/review
- Location: `backend/app/routers/recommendations.py` lines 226-229

### Validation Warnings Storage
**Decision**: Store tone validation warnings in `metadata_json["validation_warnings"]` array
**Rationale**:
- Allows operator to see validation issues without blocking persistence
- Enables audit trail of content quality checks
- Supports operator decision-making with full context
- Empty array indicates valid content (no warnings)
**Implementation**:
- Warnings stored as array of objects with `severity`, `type`, and `message` fields
- Two severity levels: `critical` (forbidden phrases) and `notable` (lacks empowering language)
- All recommendations persisted regardless of warnings for operator review
- Location: `backend/app/services/guardrails.py` and `backend/app/routers/recommendations.py`

## Guardrails Service Architecture

### Non-Blocking Tone Validation
**Decision**: Tone validation does not block recommendation persistence - all recommendations saved regardless of warnings
**Rationale**:
- Human oversight (operator) is final arbiter of content quality
- Automated validation may have false positives/negatives
- Allows operator to review edge cases and make informed decisions
- Maintains audit trail of all generated content
**Implementation**:
- `validate_tone()` returns structured warnings, not boolean pass/fail
- Recommendations saved with `status='pending_approval'` even with warnings
- Operator UI displays warnings with color coding (RED for critical, YELLOW for notable)
- Operator can approve/override/reject based on warnings
- Location: `backend/app/services/guardrails.py` and `backend/app/routers/recommendations.py`

### Tone Validation Severity Levels
**Decision**: Two-tier severity system for tone validation warnings
**Rationale**:
- Distinguishes between critical issues (forbidden phrases) and notable issues (lacks empowering language)
- Enables operator UI to prioritize attention (RED vs YELLOW)
- Allows nuanced content review workflow
**Implementation**:
- **Critical warnings**: Forbidden shaming phrases (e.g., "you're overspending", "bad habit")
  - Severity: `critical`
  - Type: `forbidden_phrase`
  - Display: RED in operator UI
- **Notable warnings**: Missing empowering language keywords
  - Severity: `notable`
  - Type: `lacks_empowering_language`
  - Display: YELLOW in operator UI
- Location: `backend/app/services/guardrails.py` lines 86-127

### Override Endpoint Tone Validation
**Decision**: Override endpoint validates tone on new content and rejects if critical warnings present
**Rationale**:
- Prevents operators from accidentally introducing shaming language
- Maintains content quality standards even for manual edits
- Allows notable warnings (lacks empowering language) but blocks critical ones
**Implementation**:
- When operator overrides recommendation with new content, tone validation runs
- If critical warnings (forbidden phrases) found → 400 error, override rejected
- Notable warnings (lacks empowering language) allowed but logged
- Original content preserved in `original_content` JSON field
- Location: `backend/app/routers/recommendations.py` override endpoint

## Recommendation Workflow Decisions

### Default Status: Pending Approval
**Decision**: All AI-generated recommendations start with `status='pending_approval'`
**Rationale**:
- Ensures human review before user visibility
- Maintains quality control and compliance
- Allows operator to catch edge cases and AI errors
- Supports audit trail of all content decisions
**Implementation**:
- Recommendations created with `status='pending_approval'` regardless of validation warnings
- Only moved to `approved` after explicit operator action
- Can be `overridden` (edited) or `rejected` by operator
- Location: `backend/app/routers/recommendations.py` generate endpoint

### Mandatory Disclosure Appending
**Decision**: Append mandatory disclosure to all recommendation content before saving
**Rationale**:
- Regulatory compliance requirement
- Ensures users understand content is educational, not financial advice
- Consistent application across all recommendations
**Implementation**:
- Disclosure appended via `guardrails.append_disclosure()` function
- Applied during recommendation generation and override operations
- Disclosure text: "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."
- Location: `backend/app/services/guardrails.py` and `backend/app/routers/recommendations.py`

### Caching Strategy for Recommendations
**Decision**: Return existing recommendations if found (unless `force_regenerate=True`)
**Rationale**:
- Reduces OpenAI API costs
- Improves response latency
- Allows regeneration when needed (e.g., after new transactions)
**Implementation**:
- Check for existing recommendations with same `user_id`, `window_days`, and `status='pending_approval'`
- Return 200 status code for cached results
- Return 201 status code for newly generated recommendations
- `force_regenerate` query parameter allows bypassing cache
- Location: `backend/app/routers/recommendations.py` generate endpoint

## Database Schema Decisions

### JSON Field for Metadata
**Decision**: Store recommendation metadata as JSON string in `metadata_json` field
**Rationale**:
- Flexible schema for varying metadata structures
- Supports validation warnings, partner offer data, and future extensions
- Avoids complex relational schema for semi-structured data
**Implementation**:
- `metadata_json` column type: `Text` (stores JSON string)
- Serialized via `json.dumps()` before saving
- Deserialized when reading from database
- Excludes operational metrics (token_usage, cost) before serialization
- Location: `backend/app/models.py` Recommendation model

### Original Content Storage for Overrides
**Decision**: Store original content in JSON format when recommendation is overridden
**Rationale**:
- Maintains audit trail of content changes
- Allows rollback if needed
- Supports compliance and transparency requirements
**Implementation**:
- `original_content` field stores JSON with `original_title`, `original_content`, `overridden_at`
- Only populated when override operation occurs
- Preserved even if recommendation is later approved or rejected
- Location: `backend/app/routers/recommendations.py` override endpoint

## API Design Decisions

### Access Control Removal (MVP)
**Decision**: Removed premature access control logic from GET recommendations endpoint
**Rationale**:
- Authentication not implemented in MVP
- Cannot determine requester identity without auth
- Will be implemented when authentication is added
**Implementation**:
- Endpoint returns all recommendations when no status filter provided
- Status filter allows filtering by recommendation status
- Future: Will enforce customer vs operator access when JWT auth added
- Location: `backend/app/routers/recommendations.py` GET endpoint

### Operator Action Audit Trail
**Decision**: Log all operator actions (approve, reject, override) in `operator_actions` table
**Rationale**:
- Compliance and audit requirements
- Enables analysis of operator decision patterns
- Supports debugging and quality improvement
**Implementation**:
- `OperatorAction` model stores: operator_id, action_type, recommendation_id, user_id, reason, timestamp
- Created for every approve, reject, and override operation
- Reason field optional for approve, required for reject/override
- Location: `backend/app/routers/recommendations.py` approval endpoints

## Frontend Architecture Decisions

### Centralized Enum System
**Decision**: All enum values defined in `frontend/src/constants/enums.js`
**Rationale**:
- Single source of truth for enum values
- Prevents hardcoded strings throughout codebase
- Easier maintenance and refactoring
- Type safety through constants
**Implementation**:
- Enums: `UserType`, `ConsentStatus`, `ConsentAction`
- Helper functions for display formatting
- Used consistently across all components
- Location: `frontend/src/constants/enums.js`

### Path Alias Configuration
**Decision**: Use `@src` alias for frontend imports instead of relative paths
**Rationale**:
- Cleaner import statements
- Easier refactoring (move files without breaking imports)
- Better IDE support and autocomplete
- Consistent with modern React practices
**Implementation**:
- Configured in `vite.config.js` and `jsconfig.json`
- All components updated to use `@src` consistently
- Location: `frontend/vite.config.js` and `frontend/jsconfig.json`

## Persona Assignment Decisions

### Savings Builder as Default Fallback Persona
**Decision**: Use `savings_builder` as the default fallback persona when no persona criteria match
**Rationale**:
- Ensures recommendation generation can always proceed (all 5 personas have prompt files)
- `savings_builder` is the most general positive persona, suitable for users who don't fit specific categories
- Low confidence scores (0.1-0.2) clearly indicate fallback assignments
- Avoids need for special handling or missing prompt files
- Maintains system consistency - all users get valid personas
**Implementation**:
- When no features are computed: Assign `savings_builder` with confidence 0.1
- When features exist but no persona matches: Assign `savings_builder` with confidence 0.2
- Confidence scores signal to operators that these are fallback assignments
- Removed `general_wellness` persona type entirely (no prompt file, no explicit criteria)
- Location: `backend/app/services/persona_assignment.py` lines 264-271 and 380-387

## Performance Optimization Decisions

### Vector Database Integration for Sub-1s Latency
**Decision**: Integrate Pinecone Serverless vector database with OpenAI embeddings to achieve sub-1 second recommendation retrieval
**Context**: Based on comprehensive latency testing documented in `docs/OPENAI_LATENCY_TESTING.md`
**Problem Statement**:
- Current OpenAI API latency: ~17 seconds average per recommendation generation
- Testing revealed model choice (gpt-4o-mini) is the primary bottleneck, not context size or JSON mode
- Alternative (gpt-3.5-turbo) is 67% faster but lower quality
- Need to maintain gpt-4o-mini quality while achieving <1s response times
**Rationale**:
- **Vector DB for semantic search**: Pre-compute embeddings for user contexts and recommendations, retrieve similar recommendations in <50ms instead of generating fresh via OpenAI
- **Quality preservation**: Keep gpt-4o-mini for edge cases and unique user contexts (similarity score < 0.85)
- **Hybrid architecture**: Use vector DB for high-similarity matches, fall back to OpenAI for edge cases
- **Cost reduction**: 80-90% reduction in OpenAI API costs (fewer fresh generations)
- **Showcase AI engineering**: Demonstrates production-grade LLM application architecture with embeddings, semantic search, and hybrid retrieval
**Architecture**:
- **Pinecone Serverless**: Vector database for storing and querying recommendation embeddings (1M vectors free tier)
- **OpenAI text-embedding-3-small**: Generate embeddings for user contexts and recommendations ($0.00002/1k tokens)
- **Similarity threshold**: 0.85 cutoff for vector DB matches vs OpenAI fallback
- **Redis caching layer**: Multi-tier caching strategy (user context, recommendations, DB queries)
- **AWS ElastiCache Serverless**: Redis instance for production deployment
**Expected Performance**:
- Vector DB hits: <1 second total latency (50ms vector search + 100ms DB/API overhead)
- OpenAI fallback (edge cases): 2-5 seconds with gpt-4o-mini
- Overall improvement: 94% latency reduction for cached/similar contexts
**Prerequisites**:
- Scale synthetic data to 500-1,000 users (current: 75 users insufficient for vector DB value)
- Generate recommendations for all users (need 1,500-5,000 recommendations for meaningful similarity matching)
- Implement Redis caching layer first (quick win, simpler than vector DB)
- Migrate to PostgreSQL (AWS RDS) for production-grade database
**Implementation Plan**:
- Phase 1: Redis caching layer (PR #31)
- Phase 2: PostgreSQL migration (PR #32)
- Phase 3: Scale synthetic data to 500-1,000 users (PR #33)
- Phase 4: Vector DB integration with Pinecone (PR #34-37)
**Testing Results** (See `docs/OPENAI_LATENCY_TESTING.md`):
- ❌ Context size reduction: No improvement (18.8s vs 17s baseline)
- ❌ JSON mode removal: 35% slower (23s vs 17s baseline)
- ✅ Model change (gpt-3.5-turbo): 67% faster (5.5s) but lower quality
- ✅ Vector DB approach: Maintains quality while achieving <1s for similar contexts
**Location**: To be implemented in `backend/app/services/vector_recommendation_engine.py`

### Redis Caching Strategy
**Decision**: Implement multi-tier Redis caching for all database queries and API responses
**Rationale**:
- Quick win: Instant response for repeated queries (user profiles, recommendations, features)
- Complements vector DB: Cache vector DB results for subsequent requests
- Production-ready: AWS ElastiCache Serverless (free tier available)
- Reduces database load and improves overall system performance
**Implementation**:
- Cache keys: `user_context:{user_id}:{window_days}`, `recommendations:{user_id}:{window_days}`, `features:{user_id}:{window_days}`
- TTLs: User context (1h), recommendations (24h), features (1h)
- Cache invalidation: On new transactions, feature updates, or force_regenerate=True
**Location**: To be implemented in `backend/app/services/redis_cache.py`

### PostgreSQL Migration for Production
**Decision**: Migrate from SQLite to PostgreSQL (AWS RDS) for production deployment
**Rationale**:
- Better concurrency than SQLite (no WAL mode limitations)
- Production-grade durability and backup capabilities
- AWS RDS integration for managed service benefits
- All SQLAlchemy models are PostgreSQL-compatible (no schema changes needed)
**Implementation**:
- Keep SQLite for local development
- Use environment variable for DATABASE_URL switching
- Re-ingest synthetic data or use pg_dump for migration
**Location**: `backend/app/database.py` (connection string update)

