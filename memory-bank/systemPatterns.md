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
- **Subscriptions**: recurring merchant detection, spend share
- **Savings**: net inflow, growth rate, emergency fund coverage
- **Credit**: utilization %, minimum-payment detection, interest charges
- **Income**: payroll ACH detection, frequency, cash-flow buffer

### 3. Persona Assignment Engine (`personas/`)
- Rules-based logic (deterministic, fast)
- Prioritization when multiple personas match
- Stores assignment with confidence scores

### 4. Recommendation Engine (`recommend/`)
- 5 separate OpenAI endpoints (one per persona)
- Generates 3-5 educational items per user
- Plain-language rationales citing specific data
- Partner offer suggestions (eligibility-filtered)

### 5. Guardrails Module (`guardrails/`)
- Consent enforcement (no recs without opt-in)
- Eligibility filters (income, credit, existing accounts)
- Tone validation (no shaming language)
- Mandatory disclosures

### 6. Operator Interface (`ui/operator/`)
- User list with persona distribution
- Approval queue (pending recommendations)
- Override workflow (edit live recommendations)
- Metrics dashboard

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
- **Rules-based, not ML**: Deterministic logic for fast, explainable assignments
- **Prioritization**: When multiple personas match, highest priority wins
- **Confidence Scores**: Stored for transparency (though rules-based, not probabilistic)

### AI Integration Pattern
- **Separate Endpoints Per Persona**: 5 distinct system prompts for better context management
- **Context Payload**: Structured JSON with user features, accounts, recent transactions
- **Post-Generation Validation**: Tone check before saving to database
- **Status Workflow**: `pending_approval` → `approved` → user-visible

### Guardrails Pattern
- **Pre-Generation**: Consent check (block if no consent)
- **Post-Generation**: Tone validation (regenerate if shaming language detected)
- **Eligibility**: Filter partner offers based on user income/credit profile
- **Mandatory Disclosures**: Append to every recommendation

### Approval Workflow Pattern
- **Default Status**: All recommendations start as `pending_approval`
- **Bulk Operations**: Operators can approve multiple at once
- **Override Support**: Store original content, allow edits with reason logging
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

### Backend → Database
- SQLAlchemy ORM for all database operations
- Connection pooling for concurrent requests
- Migrations handled via SQLAlchemy

### Backend → OpenAI
- OpenAI Python SDK
- GPT-4o-mini model (cost-effective)
- JSON response format for structured output
- Error handling and retry logic

### Backend → AWS
- S3 for Parquet exports
- Lambda for serverless deployment
- SAM for Infrastructure as Code
- Pre-signed URLs for secure downloads

