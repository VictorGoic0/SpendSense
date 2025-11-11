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
- Populates 5 core tables: users, accounts, transactions, liabilities, products
- Idempotent ingestion (can re-run safely)
- Processing order: Users → Accounts → Transactions → Liabilities → Products
- Transactions processed in batches of 1000 for performance

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
- **Fallback Behavior**: When no persona matches, assign `savings_builder` with low confidence (0.1 if no features, 0.2 if features exist but no match)
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
- 🔄 **Hybrid Vector DB + OpenAI architecture planned (PR #34-37)**
  - **Problem**: 17s OpenAI latency with gpt-4o-mini (documented in `docs/OPENAI_LATENCY_TESTING.md`)
  - **Solution**: Pinecone Serverless + OpenAI embeddings + hybrid retrieval
  - **Architecture**:
    - Vector DB for semantic search (retrieve similar recommendations in <50ms)
    - OpenAI fallback for edge cases (similarity score < 0.85)
    - Redis caching layer for instant repeated queries
  - **Expected Performance**: <1s for vector DB hits, 2-5s for OpenAI fallback
  - **Prerequisites**: Scale data to 500-1,000 users (75 users insufficient for meaningful similarity matching)
  - **Services**:
    - `embedding_service.py`: Generate embeddings with text-embedding-3-small
    - `vector_search_service.py`: Query Pinecone for similar recommendations
    - `recommendation_engine.py` (updated): Hybrid logic (vector DB → OpenAI fallback)

### 5. Guardrails Module (`guardrails/`)
- Consent enforcement (no recs without opt-in)
- Eligibility filters (income, credit, existing accounts)
- Product eligibility checking (PR #41 Complete):
  - `check_product_eligibility()`: Checks income, utilization, existing accounts, category-specific rules
  - `filter_eligible_products()`: Batch filters product matches by eligibility
  - Integrated into product matching flow
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
- ✅ Approval queue (PR #26 Complete)
  - GET /operator/review endpoint: Fetches all non-approved recommendations, ordered by generated_at ascending
  - Frontend OperatorApprovalQueue page with bulk selection, individual actions, override/reject dialogs
  - RecommendationCard component with user info, persona badges, content previews, action buttons
  - Auto-refresh every 30 seconds, status filtering, loading/error states
- ✅ Override workflow (PR #24, #26 Complete)
  - Backend override endpoint with original content preservation
  - Frontend override dialog with form validation and tone checking

### 7. User Interface (`ui/user/`)
- ✅ User Dashboard (PR #27 Complete)
  - ConsentToggle component: Switch with confirmation dialogs for grant/revoke
  - UserRecommendationCard component: Read-only recommendation display with markdown rendering
  - UserDashboard page: Parallel data fetching, consent management, recommendations display
  - Empty states: No consent CTA, "coming soon" for pending recommendations
  - Responsive layout with loading/error states
- ✅ Consent Management (PR #27 Complete)
  - Backend endpoints: POST `/consent`, GET `/consent/{user_id}`
  - ConsentLog audit trail for all consent changes
  - Frontend integration with grant/revoke flows
- Personalized recommendation feed
- Educational content display
- Rationale transparency

### 8. Product Catalog (`products/`)
- ✅ Product catalog generation (PR #38 Complete, PR #42 Normalized)
  - `ProductOffer` model: Stores financial products (savings accounts, credit cards, apps, services, investment accounts, loans)
  - Product generation script: `scripts/generate_product_catalog.py`
    - Uses OpenAI GPT-4o with batch generation (5 batches of ~30 products) to generate ~150 products
    - Loads `.env` from backend folder automatically
    - Applies deterministic eligibility rules post-LLM generation:
      - `requires_no_existing_savings = TRUE` only for HYSA products
      - `requires_no_existing_investment = TRUE` only for investment/robo_advisor products
      - `min_income`, `max_credit_utilization`, `min_credit_score` set deterministically based on category
    - Validates and enhances products with metadata
    - Generates `data/product_catalog.json` with complete product data
  - Generated catalog: ~150 products covering all 5 personas
    - Categories: balance_transfer, hysa, budgeting_app, subscription_manager, robo_advisor, investment_account, retirement_plan, debt_consolidation, personal_loan, credit_builder
    - Product types: savings_account, credit_card, app, service, investment_account, loan
    - All products include disclosures, benefits, eligibility criteria, partner information
    - Eligibility flags set correctly (no subscription apps requiring no savings)
  - Schema documentation: `docs/PRODUCT_SCHEMA.md` with complete field descriptions and JSON format
- ✅ Product ingestion via API (PR #39 Complete)
  - Products ingested through `/ingest/` endpoint (same as users, accounts, transactions, liabilities)
  - `ProductCreate` and `ProductResponse` schemas added to `backend/app/schemas.py`
  - Ingestion endpoint converts `persona_targets` and `benefits` lists to JSON strings
  - Test script: `scripts/test_ingest_products.py` for API-based ingestion
  - All product data follows consistent API ingestion pattern
- ✅ Product matching service (PR #40 Complete)
  - Service file: `backend/app/services/product_matcher.py`
  - Helper functions: `get_account_types()`, `has_hysa()`, `has_investment_account()`
  - Relevance scoring: `calculate_relevance_score()` with category-specific rules
    - Balance transfer: High utilization + interest charges
    - HYSA: Savings activity + low emergency fund (penalizes existing HYSA)
    - Budgeting apps: Income variability + low buffer
    - Subscription managers: High recurring merchants + spend share
    - Investment products: High income + low utilization + good emergency fund (penalizes existing investment)
  - Rationale generation: `generate_product_rationale()` with personalized explanations citing user data
  - Main matching: `match_products()` - Filters by persona, scores products, generates rationales, applies eligibility filtering, returns top 3 eligible products
  - Test script: `scripts/test_product_matching.py` with comprehensive coverage for all personas
- ✅ Eligibility filtering (PR #41 Complete)
  - Service file: `backend/app/services/guardrails.py`
  - `check_product_eligibility()`: Checks income, utilization, existing accounts, category-specific rules
  - `filter_eligible_products()`: Batch filters product matches by eligibility
  - Integrated into product matching flow (products filtered after scoring)
  - Test script: `scripts/test_product_eligibility.py` with comprehensive coverage
- ✅ Product management API (PR #44 Complete)
  - Router file: `backend/app/routers/products.py`
  - GET `/products/` - List products with filtering (active_only, category, persona_type) and pagination (skip, limit)
  - GET `/products/{product_id}` - Get single product by ID (404 if not found)
  - POST `/products/` - Create new product (generates prod_XXX product_id, converts lists to JSON, returns 201)
  - PUT `/products/{product_id}` - Update existing product (updates all fields, updates updated_at, returns 404 if not found)
  - DELETE `/products/{product_id}` - Deactivate product (soft delete: sets active=False, returns 204 No Content)
  - JSON field parsing: Helper function `_parse_json_fields()` parses persona_targets and benefits from JSON strings
  - Error handling: 404 for not found, 500 for server errors, comprehensive logging
  - Router registered in `backend/app/main.py` with tag="products"
  - OpenAPI documentation: All endpoints documented with FastAPI auto-generated docs

### 9. Evaluation Harness (`eval/`)
- ✅ Metrics computation script (PR #28 Complete)
  - `scripts/evaluate.py`: Comprehensive evaluation script
  - Coverage metrics: Percentage of users with personas assigned
  - Explainability metrics: Percentage of recommendations with rationale
  - Latency metrics: Average and p95 recommendation generation time
  - Auditability metrics: Percentage of recommendations with decision traces (100%)
  - Persona distribution: Groups personas by type for 30d and 180d windows
  - Recommendation status breakdown: Groups recommendations by status
  - Main function: `run_evaluation()` generates unique run_id, computes all metrics, prints formatted output
  - Database persistence: `save_evaluation_metrics()` saves metrics to evaluation_metrics table
  - Dependencies: pandas==2.1.4, numpy==1.26.2
  - Output: Formatted console output with all metrics, distributions, and breakdowns
- ✅ Parquet export to S3 (PR #29 Complete)
  - `export_user_features_to_parquet()`: Exports user features for 30d/180d windows to Parquet format
  - `export_evaluation_results_to_parquet()`: Exports evaluation metrics to Parquet format
  - `upload_to_s3()`: Uploads files to S3 and generates 7-day pre-signed URLs
  - S3 bucket: `spendsense-analytics-goico` (us-east-2 region)
  - File organization: `features/` prefix for user features, `eval/` prefix for evaluation results
  - Error handling: Clear error messages for missing AWS credentials or S3 failures
  - `generate_evaluation_report()`: Creates JSON report with metrics and S3 download URLs
  - Dependencies: boto3==1.29.7, pyarrow==14.0.1
  - Integration: Exports run automatically after metrics computation
  - Output: 3 Parquet files (30d features, 180d features, evaluation results) + JSON report with pre-signed URLs

## Database Schema (11 Tables)

1. **users** - User accounts with consent tracking
2. **accounts** - Bank accounts (checking, savings, credit, investment)
3. **transactions** - Individual transactions with merchant/category data
4. **liabilities** - Credit cards and loans with APR/payment info
5. **user_features** - Computed behavioral signals (30d and 180d windows)
6. **personas** - Persona assignments with confidence scores
7. **recommendations** - AI-generated content with approval status ✅ PR #42 Updated
    - Core fields: recommendation_id (PK), user_id (FK), persona_type, window_days, content_type ('education' or 'partner_offer')
    - Content fields: title, content (nullable - only for education), rationale, product_id (nullable - only for partner_offer)
    - Status fields: status, approved_by, approved_at, override_reason, original_content
    - Metadata: metadata_json (includes product_data for partner_offer recommendations)
    - Timestamps: generated_at, generation_time_ms, expires_at
    - Indexes: user_id, status, window_days
8. **evaluation_metrics** - System performance metrics
9. **consent_log** - Audit trail of consent changes
10. **operator_actions** - Log of approve/reject/override actions
11. **product_offers** - Financial product catalog (savings accounts, credit cards, apps, services, investment accounts, loans) ✅ PR #38 Complete, PR #42 Normalized
    - Core fields: product_id (PK), product_name, product_type (includes "loan"), category, persona_targets (JSON array)
    - Eligibility criteria: min_income, max_credit_utilization, requires_no_existing_savings/investment, min_credit_score
      - Eligibility flags set deterministically: requires_no_existing_savings only for HYSA, requires_no_existing_investment only for investment products
    - Content fields: short_description, benefits (JSON array), typical_apy_or_fee, partner_link, disclosure
    - Business fields: partner_name, commission_rate, priority, active
    - Timestamps: created_at, updated_at (auto-set/updated)
    - Indexes: persona_targets, active status
    - See `docs/PRODUCT_SCHEMA.md` for complete schema documentation

## Design Patterns

### Persona Assignment Pattern
- **Rules-based, not ML**: Deterministic logic for fast, explainable assignments ✅ Implemented
- **Prioritization**: When multiple personas match, highest priority wins ✅ Implemented
- **Confidence Scores**: Stored for transparency (though rules-based, not probabilistic) ✅ Implemented
- **Implementation**: `backend/app/services/persona_assignment.py`
- **Check Functions**: Each persona has dedicated check function with specific criteria
- **Helper Functions**: get_total_savings_balance(), has_overdraft_or_late_fees() for wealth_builder checks
- **Reasoning Storage**: JSON-serialized reasoning dict stored in Persona.reasoning field

### Hybrid Recommendation Retrieval Pattern (Planned)
- **Vector DB first, OpenAI fallback**: Optimize for speed without sacrificing quality
- **Similarity threshold**: 0.85 cutoff for vector DB vs OpenAI (configurable)
- **Embedding strategy**: User context embeddings + recommendation embeddings
- **Metadata filtering**: Query by persona_type for relevant results only
- **Background jobs**: Embed new recommendations immediately after OpenAI generation
- **Monitoring**: Track vector DB hit rate, similarity scores, latency breakdown
- **Implementation**: To be added in PR #34-37
- **Services**:
  - `embedding_service.py`: OpenAI text-embedding-3-small integration
  - `vector_search_service.py`: Pinecone query logic
  - `recommendation_engine.py` (updated): Hybrid retrieval logic

### AI Integration Pattern
- **OpenAI SDK**: Version 2.7.1 installed and configured (upgraded from 1.3.5 for compatibility)
- **Model Selection**: Using gpt-4o-mini (prioritizing quality over speed)
  - Average latency: ~17 seconds per recommendation generation
  - Performance Testing (documented in `docs/performance_testing/`):
    - gpt-3.5-turbo: 67% faster (5.5s) but lower quality
    - Context size: Not a significant factor in latency
    - JSON mode: Beneficial for performance, should NOT be removed
  - Future optimization options: Redis caching, async task queue, or model switch
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
- **Product Eligibility** (PR #41 Complete):
  - `check_product_eligibility()`: Checks income, credit utilization, existing accounts, category-specific rules
  - `filter_eligible_products()`: Batch filters product matches by eligibility
  - Integrated into product matching flow (products filtered after scoring, before returning)
  - Returns tuple of (is_eligible: bool, reason: str) with comprehensive logging
- **Eligibility**: Filter partner offers based on user income/credit profile
- **Mandatory Disclosures**: Append to every recommendation content

### Consent Management Pattern
- **Consent Endpoints**: POST `/consent`, GET `/consent/{user_id}` (PR #27 Complete)
  - POST `/consent`: Updates user consent_status, updates consent_granted_at or consent_revoked_at timestamps
  - Creates ConsentLog entry for audit trail (action: "granted" or "revoked")
  - Returns ConsentResponse with updated status
  - GET `/consent/{user_id}`: Returns consent status, timestamps, and full history from ConsentLog
- **Consent Schemas**: ConsentRequest (user_id, action), ConsentHistoryItem (action, timestamp), ConsentResponse (user_id, consent_status, timestamps, history)
- **Frontend Integration**: ConsentToggle component with Switch, confirmation dialogs, status display
- **User Dashboard**: Consent management integrated with automatic recommendation fetch on grant, recommendations cleared on revoke
- **Audit Trail**: All consent changes logged in consent_log table with timestamps

### Approval Workflow Pattern
- **Default Status**: All recommendations start as `pending_approval`
- **Approve Endpoint**: POST `/recommendations/{recommendation_id}/approve` (PR #23 Complete)
  - Validates recommendation exists and is in valid state (not already approved, not rejected)
  - Updates recommendation status to 'approved', sets approved_by and approved_at
  - Creates OperatorAction record for audit trail
  - Returns updated recommendation
- **Override Endpoint**: POST `/recommendations/{recommendation_id}/override` (PR #24 Complete)
  - Validates recommendation exists and at least one of new_title or new_content provided
  - Stores original content in JSON format (original_title, original_content, overridden_at)
  - Updates recommendation with new content, validates tone, appends disclosure
  - Rejects new content with critical tone warnings (forbidden phrases)
  - Creates OperatorAction record with action_type='override'
  - Returns updated recommendation with original_content and override_reason
- **Reject Endpoint**: POST `/recommendations/{recommendation_id}/reject` (PR #24 Complete)
  - Validates recommendation exists and is not already approved
  - Updates recommendation status to 'rejected'
  - Stores rejection reason in metadata_json (rejection_reason, rejected_by, rejected_at)
  - Creates OperatorAction record with action_type='reject'
  - Returns updated recommendation with rejection metadata
- **Bulk Operations**: POST `/recommendations/bulk-approve` endpoint (PR #25 Complete)
  - Accepts array of recommendation IDs
  - Processes each individually with error handling
  - Batch commit in single transaction
  - Returns summary with approved/failed counts and error messages
- **Approval Queue Endpoint**: GET `/operator/review` (PR #26 Complete)
  - Fetches all recommendations where status != 'approved'
  - Optional status filter (pending_approval, overridden, rejected)
  - Orders by generated_at ascending (oldest first, queue order)
  - Includes user information via JOIN
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
  - POST /ingest - Bulk data ingestion (users, accounts, transactions, liabilities, products)
  - POST /recommendations/generate/{user_id} - Generate recommendations for user
  - GET /recommendations/{user_id} - Get recommendations for user (with optional status and window_days filters)
  - POST /recommendations/{recommendation_id}/approve - Approve a recommendation (PR #23 Complete)
  - POST /recommendations/{recommendation_id}/override - Override a recommendation with new content (PR #24 Complete)
  - POST /recommendations/{recommendation_id}/reject - Reject a recommendation (PR #24 Complete)
  - POST /recommendations/bulk-approve - Bulk approve multiple recommendations (PR #25 Complete)
  - GET /operator/review - Get approval queue (all non-approved recommendations) (PR #26 Complete)
  - POST /consent - Update user consent status (grant/revoke) (PR #27 Complete)
  - GET /consent/{user_id} - Get user consent status and history (PR #27 Complete)
  - GET /products - List products with filtering and pagination (PR #44 Complete)
  - GET /products/{product_id} - Get single product by ID (PR #44 Complete)
  - POST /products - Create new product (PR #44 Complete)
  - PUT /products/{product_id} - Update existing product (PR #44 Complete)
  - DELETE /products/{product_id} - Deactivate product (soft delete) (PR #44 Complete)
  - POST /evaluate/ - Run evaluation, compute metrics, export to S3 (PR #30 Complete)
  - GET /evaluate/latest - Get most recent evaluation metrics (PR #30 Complete)
  - GET /evaluate/history - Get evaluation history with optional limit (PR #30 Complete)
  - GET /evaluate/exports/latest - List latest S3 exports with pre-signed URLs (PR #30 Complete)

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
- S3 for Parquet exports (PR #29 Complete)
  - Bucket: `spendsense-analytics-goico` in us-east-2 region
  - Organized folder structure: `features/` and `eval/` prefixes
  - Pre-signed URLs with 7-day expiry (604800 seconds)
  - Error handling for missing credentials and S3 failures
- Evaluation API endpoints (PR #30 Complete)
  - Router: `backend/app/routers/evaluation.py`
  - Imports evaluation functions from `scripts/evaluate.py`
  - Adapts evaluation script to work with FastAPI dependency injection
  - All endpoints tested and verified via Swagger UI
- Railway for backend deployment
  - FastAPI application runs as standard web service
  - Auto-seeding: Database seeded from JSON files on startup if empty
  - Environment variables configured via Railway dashboard
  - Automatic HTTPS and domain provisioning

