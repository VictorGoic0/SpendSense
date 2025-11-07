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

