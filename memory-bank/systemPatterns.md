# System Patterns: SpendSense

## Architecture Overview

### Data Flow
```
Synthetic Data (JSON) 
    ↓
POST /ingest → FastAPI
    ↓
SQLite Database (10+ tables)
    ↓
Feature Detection Pipeline (background job)
    ↓
Persona Assignment (rules-based)
    ↓
AI Recommendation Generation (OpenAI)
    ↓
Guardrails Check (consent, eligibility, tone)
    ↓
Approval Queue (operator review)
    ↓
User Dashboard (React UI)
```

## System Components

### 1. Data Ingestion Module (`ingest/`)
- Validates synthetic Plaid-style JSON
- Populates 4 core tables: users, accounts, transactions, liabilities
- Idempotent ingestion (can re-run safely)

### 2. Feature Engineering Pipeline (`features/`)
- Computes 30-day and 180-day behavioral signals
- **Subscriptions**: recurring merchant detection, spend share (✅ Complete)
- **Savings**: net inflow, growth rate, emergency fund coverage (✅ Complete)
- **Credit**: utilization %, minimum-payment detection, interest charges, overdue status (✅ Complete)
- **Income**: payroll ACH detection, frequency, cash-flow buffer (✅ Complete)
- **Computation**: Combined feature computation function, API endpoints, batch processing (✅ Complete)

### 3. Persona Assignment Engine (`personas/`)
- ✅ Rules-based logic (deterministic, fast) - **PR #15 Complete**
- ✅ Prioritization when multiple personas match - **PR #15 Complete**
- ✅ Stores assignment with confidence scores - **PR #15 Complete**
- ✅ API endpoints for assignment and retrieval - **PR #16 Complete**
- ✅ Batch assignment script for all users - **PR #16 Complete**
- **Service File**: `backend/app/services/persona_assignment.py`
- **Router File**: `backend/app/routers/personas.py`
- **Check Functions**: high_utilization, variable_income, subscription_heavy, savings_builder, wealth_builder
- **Priority Order**: wealth_builder (1.0) → high_utilization (0.95/0.8) → savings_builder (0.7) → variable_income (0.6) → subscription_heavy (0.5)
- **Reasoning**: JSON-serialized dict with matched_criteria, feature_values, timestamp, priority
- **API Endpoints**: POST /personas/{user_id}/assign, GET /personas/{user_id}
- **Batch Script**: `scripts/assign_all_personas.py`
- **Test Script**: `scripts/test_persona_assignment.py`
- **Personas Assigned**: 142 records (71 users × 2 windows)
- **Note**: Synthetic data variance enhancement needed - wealth_builder and variable_income personas not well represented in current test data

### 4. Recommendation Engine (`recommend/`)
- ✅ Context building service complete (PR #18)
  - `build_user_context()`: Queries user data, features, accounts, transactions
  - Returns structured context dict with all behavioral signals and relevant data
  - Token-efficient design (top 5 accounts, last 10 transactions, top 10 recurring merchants)
  - Context validation function ensures data quality
  - Service file: `backend/app/services/recommendation_engine.py`
  - Test script: `scripts/test_context_builder.py` - All tests passing
- ✅ OpenAI integration complete (PR #19)
  - `generate_recommendations_via_openai()`: Generates recommendations via OpenAI API
  - Uses gpt-4o-mini model with temperature 0.75
  - Exponential backoff retry logic for rate limits
  - Comprehensive error handling
  - Token usage tracking (in metadata for review, NOT saved to DB)
  - Generates 3-5 educational recommendations per user
  - Plain-language rationales citing specific data
  - All recommendations validated for empowering tone
  - Test script: `scripts/test_openai_generation.py` - All quality checks passing

### 5. Guardrails Module (`guardrails/`)
- Consent enforcement (no recs without opt-in)
- Eligibility filters (income, credit, existing accounts)
- Tone validation (no shaming language)
- Mandatory disclosures

### 6. Operator Interface (`ui/operator/`)
- ✅ Metrics dashboard (PR #12 Complete)
  - Total users, users with consent, pending approvals, avg latency metrics
  - Persona distribution bar chart
  - Recommendation status breakdown chart
  - Loading and error states
- ✅ User list page (PR #13 Complete)
  - User table with pagination, filters, search
  - Filter by user type and consent status
  - Search by name or email
  - Loading skeletons and error handling
  - Backend GET /users endpoint with pagination and filters
- ✅ User detail page (PR #14 Complete)
  - Two-column layout with user info, personas (30d/180d), and signal displays
  - Tab navigation for signal types (subscriptions, savings, credit, income)
  - Signal visualization with progress bars and color coding
  - Recommendations section with status badges
  - Back navigation and loading/error states
  - Backend GET /users/{user_id} and GET /operator/users/{user_id}/signals endpoints
- Approval queue (pending recommendations) (PR #16+)
- Override workflow (edit live recommendations) (PR #16+)

### 7. User Interface (`ui/user/`)
- Consent management toggle
- Personalized recommendation feed
- Educational content display
- Rationale transparency

### 8. Evaluation Harness (`eval/`)
- Metrics computation script
- SQLite table for dashboard display
- Parquet export to S3 for deep analysis

## Database Schema (10 Tables)

1. **users** - User accounts with consent tracking
2. **accounts** - Bank accounts (checking, savings, credit, investment)
3. **transactions** - Individual transactions with merchant/category data
4. **liabilities** - Credit cards and loans with APR/payment info
5. **user_features** - Computed behavioral signals (30d and 180d windows)
6. **personas** - Persona assignments with confidence scores
7. **recommendations** - AI-generated content with approval status
8. **evaluation_metrics** - System performance metrics
9. **consent_log** - Audit trail of consent changes
10. **operator_actions** - Log of approve/reject/override actions

## Design Patterns

### Persona Assignment Pattern
- **Rules-based, not ML**: Deterministic logic for fast, explainable assignments ✅ Implemented
- **Prioritization**: When multiple personas match, highest priority wins ✅ Implemented
- **Confidence Scores**: Stored for transparency (though rules-based, not probabilistic) ✅ Implemented
- **Implementation**: `backend/app/services/persona_assignment.py`
- **Check Functions**: Each persona has dedicated check function with specific criteria
- **Helper Functions**: get_total_savings_balance(), has_overdraft_or_late_fees() for wealth_builder checks
- **Reasoning Storage**: JSON-serialized reasoning dict stored in Persona.reasoning field

### AI Integration Pattern
- **OpenAI SDK**: Version 2.7.1 installed and configured (upgraded from 1.3.5 for compatibility)
- **Prompt System**: 5 self-contained persona-specific prompts following "just right" calibration guide
  - Each prompt is lean (~50-60 lines), self-contained, principle-based
  - Structure: Role & Context, Core Principles, LANGUAGE STYLE (empowering language requirements), Response Framework (5 steps), Guidelines (with topic lists), Output Format
  - Prompts located in `backend/app/prompts/` directory
  - Prompt loader utility (`backend/app/utils/prompt_loader.py`) with in-memory caching
- **Prompt Design**: 
  - Self-contained (no base template) for clarity
  - Reduced prescription, increased principles
  - Topic lists in guidelines for persona-specific depth
  - Simplified output format (JSON structure without lengthy examples)
  - **LANGUAGE STYLE section added** (PR #19): Explicit requirements for empowering phrases ("You can...", "Let's explore...", "Many people find...", "Consider...")
  - Temperature: 0.75 (increased from 0.7 for more natural variation)
- **Context Building** (PR #18 Complete): ✅
  - `build_user_context()` function in `backend/app/services/recommendation_engine.py`
  - Queries user data, features, accounts, transactions, persona-specific details
  - Returns structured JSON context with:
    - Base info: user_id, window_days, persona_type
    - All behavioral signals (subscription, savings, credit, income)
    - Top 5 accounts (masked names), last 10 transactions
    - High utilization cards, recurring merchants, savings info (when applicable)
  - Token-efficient design (target <2000 tokens, actual: 583-764 tokens)
  - Context validation function ensures data quality
  - Test script validates context structure and token counts
- **OpenAI API Integration** (PR #19 Complete): ✅
  - `generate_recommendations_via_openai()` function in `backend/app/services/recommendation_engine.py`
  - Calls OpenAI chat completions API (gpt-4o-mini, temperature 0.75, JSON response format)
  - Exponential backoff retry logic for rate limits (3 retries, 1s/2s/4s delays)
  - Comprehensive error handling (rate limits, invalid API key, model not found, JSON parsing)
  - Response parsing with validation (required fields: title, content, rationale)
  - Token usage tracking (extracted, logged, cost calculated)
  - Token info included in metadata for review/testing (STRIPPED before DB save)
  - Test script validates quality, tone, and empowering language
- **Post-Generation Validation**: Tone check before saving to database (to be implemented in PR #20)
- **Status Workflow**: `pending_approval` → `approved` → user-visible

### Guardrails Pattern
- **Pre-Generation**: Consent check (block if no consent) - recommendations not generated without consent
- **Post-Generation**: Tone validation (warnings stored, but recommendations still persisted)
  - `validate_tone()` returns structured dict: `{"is_valid": bool, "validation_warnings": [...]}`
  - **Critical warnings** (forbidden phrases): severity="critical", type="forbidden_phrase" → RED in operator UI
  - **Notable warnings** (lacks empowering language): severity="notable", type="lacks_empowering_language" → YELLOW in operator UI
  - Validation warnings stored in `metadata_json["validation_warnings"]` (empty array if valid)
  - **All recommendations persisted** regardless of warnings - operator reviews and decides
- **Eligibility**: Filter partner offers based on user income/credit profile
- **Mandatory Disclosures**: Append to every recommendation content

### Approval Workflow Pattern
- **Default Status**: All recommendations start as `pending_approval`
- **Approve Endpoint**: POST `/recommendations/{recommendation_id}/approve` (PR #23 Complete)
  - Validates recommendation exists and is in valid state (not already approved, not rejected)
  - Updates recommendation status to 'approved', sets approved_by and approved_at
  - Creates OperatorAction record for audit trail
  - Returns updated recommendation
- **Bulk Operations**: Operators can approve multiple at once (to be implemented in PR #25)
- **Override Support**: Store original content, allow edits with reason logging (to be implemented in PR #24)
- **Reject Support**: Reject recommendations with reason logging (to be implemented in PR #24)
- **Audit Trail**: All actions logged in `operator_actions` table

## Key Technical Decisions

### Why FastAPI?
- Python for data pipelines (pandas, feature engineering)
- Async support for concurrent requests
- Auto-generated API documentation
- Easy integration with SQLAlchemy

### Why SQLite for MVP?
- Zero setup required
- Good enough for 75 users
- Easy migration path to PostgreSQL
- File-based, easy to backup/restore

### Why 5 Separate OpenAI Endpoints?
- Dedicated system prompts optimized per persona
- Better context management (only relevant signals passed)
- Easier to tune tone and focus per persona
- Cost tracking per persona
- A/B testing individual personas

### Why Rules-Based Personas?
- Deterministic and fast
- Fully explainable (no black box)
- Easy to debug and adjust
- No training data required

### Why UI on Day 1?
- Essential for integration testing
- Ensures end-to-end flow works early
- Operator approval workflow requires UI
- User consent management requires UI

## Component Relationships

### Frontend → Backend
- React UI makes API calls via Axios
- CORS enabled for local development
- API base URL configurable (local vs AWS)
- Path alias `@src` configured for cleaner imports
- Fast Refresh compatible (component-only exports)
- **Backend Endpoints Available**:
  - GET /users - User list with pagination and filters
  - GET /users/{user_id} - Single user with personas for both windows
  - GET /operator/dashboard - Dashboard metrics and statistics
  - GET /operator/users/{user_id}/signals - Detailed signals for operator view (30d and 180d)
  - GET /profile/{user_id} - User profile with features and personas
  - POST /features/compute/{user_id} - Compute features for user
  - POST /personas/{user_id}/assign - Assign persona for user (with optional window_days parameter)
  - GET /personas/{user_id} - Get personas for user (with optional window filter)
  - POST /ingest - Bulk data ingestion
  - POST /recommendations/generate/{user_id} - Generate recommendations for user
  - GET /recommendations/{user_id} - Get recommendations for user (with optional status and window_days filters)
  - POST /recommendations/{recommendation_id}/approve - Approve a recommendation (PR #23 Complete)

### Frontend Constants & Enums Pattern
- **Centralized Enums**: All enum values defined in `frontend/src/constants/enums.js`
- **Never Hardcode**: Always use enum values instead of string literals
- **Available Enums**:
  - `UserType`: CUSTOMER, OPERATOR, ALL (for filters)
  - `ConsentStatus`: GRANTED (true), REVOKED (false), ALL (for filters)
  - `ConsentAction`: GRANT, REVOKE
- **Helper Functions**: `getConsentStatusDisplay()`, `getUserTypeDisplay()` for UI text
- **Documentation**: See `frontend/src/constants/README.md` for usage examples

### Backend → Database
- SQLAlchemy ORM for all database operations
- Connection pooling for concurrent requests
- Migrations handled via SQLAlchemy

### Backend → OpenAI
- OpenAI Python SDK (v2.7.1) installed and configured (upgraded from 1.3.5)
- API key management via environment variables (`.env.local`)
- GPT-4o-mini model (cost-effective) - in use
- JSON response format for structured output
- Temperature: 0.75 (optimized for natural, empowering language)
- Error handling and retry logic: Exponential backoff for rate limits (3 retries, 1s/2s/4s)
- Prompt templates: 5 persona-specific prompts in `backend/app/prompts/` directory
  - All prompts include LANGUAGE STYLE section with empowering language requirements
- Prompt loader: `backend/app/utils/prompt_loader.py` with caching for performance
- Context builder: `backend/app/services/recommendation_engine.py` with `build_user_context()` function (PR #18 complete)
  - Queries user data, features, accounts, transactions
  - Returns structured JSON context for OpenAI API calls
  - Token-efficient design validated (583-764 tokens per context)
- OpenAI integration: `generate_recommendations_via_openai()` function (PR #19 complete)
  - Generates 3-5 recommendations per user
  - Token usage tracked (in metadata for review, NOT saved to DB)
  - All recommendations validated for empowering tone
  - Test script validates quality and language

### Backend → AWS
- S3 for Parquet exports
- Lambda for serverless deployment
- SAM for Infrastructure as Code
- Pre-signed URLs for secure downloads

