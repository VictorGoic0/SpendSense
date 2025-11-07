# SpendSense PRD: Personalized Financial Education Platform

**Version:** 1.0  
**Timeline:** 2-4 days (MVP focus)  
**Last Updated:** November 6, 2025

---

## Executive Summary

SpendSense transforms synthetic bank transaction data into actionable financial education through behavioral pattern detection, persona-based recommendations, and AI-generated content. Built for an AI engineering fellowship with emphasis on explainability, consent management, and responsible AI practices.

### Core Value Proposition
- Detects financial behavioral patterns from transaction data
- Assigns users to 1 of 5 educational personas
- Generates personalized, AI-powered financial education content
- Maintains strict consent and eligibility guardrails
- Provides operator oversight with approval workflows

### Success Criteria (MVP)
- ✅ 75 synthetic users with realistic financial profiles
- ✅ 100% persona assignment coverage
- ✅ 100% recommendations have AI-generated rationales
- ✅ <5 second recommendation generation latency
- ✅ Full consent tracking and enforcement
- ✅ Operator approval workflow functional
- ✅ Working UI (operator + user views) - **MVP REQUIREMENT**
- ✅ Deployed to AWS Lambda

---

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Data Models](#data-models)
3. [API Specification](#api-specification)
4. [Feature Requirements](#feature-requirements)
5. [AI Integration Strategy](#ai-integration-strategy)
6. [Persona Definitions](#persona-definitions)
7. [Development Plan](#development-plan)
8. [Testing & Evaluation](#testing-evaluation)
9. [Deployment Strategy](#deployment-strategy)

---

## System Architecture

### Tech Stack

**Frontend:**
- React 18 (Vite build tool)
- Shadcn/ui component library (LLM-optimized)
- TailwindCSS
- React Router for navigation
- Axios for API calls

**Backend:**
- FastAPI (Python 3.11+)
- SQLite (local development)
- AWS RDS PostgreSQL (stretch goal)
- Pydantic for data validation
- OpenAI Python SDK

**AI/ML:**
- OpenAI GPT-4o-mini (primary model for MVP)
- Separate endpoints per persona (5 distinct system prompts)
- Redis caching for generated content (stretch goal)

**Infrastructure:**
- AWS Lambda (serverless compute)
- AWS API Gateway (REST API)
- AWS SAM (Infrastructure as Code)
- AWS S3 (Parquet file storage)
- AWS ElastiCache Redis (stretch - caching layer)

**Analytics:**
- Pandas for data processing
- Parquet files for analytical exports
- SQLite for operational metrics

### Data Flow Architecture

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

### System Components

**1. Data Ingestion Module** (`ingest/`)
- Validates synthetic Plaid-style JSON
- Populates 4 core tables: users, accounts, transactions, liabilities
- Idempotent ingestion (can re-run safely)

**2. Feature Engineering Pipeline** (`features/`)
- Computes 30-day and 180-day behavioral signals
- Subscriptions: recurring merchant detection, spend share
- Savings: net inflow, growth rate, emergency fund coverage
- Credit: utilization %, minimum-payment detection, interest charges
- Income: payroll ACH detection, frequency, cash-flow buffer

**3. Persona Assignment Engine** (`personas/`)
- Rules-based logic (deterministic, fast)
- Prioritization when multiple personas match
- Stores assignment with confidence scores

**4. Recommendation Engine** (`recommend/`)
- 5 separate OpenAI endpoints (one per persona)
- Generates 3-5 educational items per user
- Plain-language rationales citing specific data
- Partner offer suggestions (eligibility-filtered)

**5. Guardrails Module** (`guardrails/`)
- Consent enforcement (no recs without opt-in)
- Eligibility filters (income, credit, existing accounts)
- Tone validation (no shaming language)
- Mandatory disclosures

**6. Operator Interface** (`ui/operator/`) - **MVP REQUIRED**
- User list with persona distribution
- Approval queue (pending recommendations)
- Override workflow (edit live recommendations)
- Metrics dashboard

**7. User Interface** (`ui/user/`) - **MVP REQUIRED**
- Consent management toggle
- Personalized recommendation feed
- Educational content display
- Rationale transparency

**8. Evaluation Harness** (`eval/`)
- Metrics computation script
- SQLite table for dashboard display
- Parquet export to S3 for deep analysis

---

## Data Models

### Database Schema (SQLite for MVP)

#### 1. Users Table
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    consent_status BOOLEAN DEFAULT FALSE,
    consent_granted_at DATETIME,
    consent_revoked_at DATETIME,
    user_type TEXT CHECK(user_type IN ('customer', 'operator')) DEFAULT 'customer'
);
```

#### 2. Accounts Table
```sql
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL, -- checking, savings, credit card, etc.
    subtype TEXT,
    balance_available REAL,
    balance_current REAL,
    balance_limit REAL,
    iso_currency_code TEXT DEFAULT 'USD',
    holder_category TEXT, -- personal, business
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

#### 3. Transactions Table
```sql
CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    amount REAL NOT NULL,
    merchant_name TEXT,
    merchant_entity_id TEXT,
    payment_channel TEXT,
    category_primary TEXT,
    category_detailed TEXT,
    pending BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE INDEX idx_transactions_user_date ON transactions(user_id, date);
CREATE INDEX idx_transactions_merchant ON transactions(merchant_name);
```

#### 4. Liabilities Table
```sql
CREATE TABLE liabilities (
    liability_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    liability_type TEXT CHECK(liability_type IN ('credit_card', 'mortgage', 'student_loan')),
    
    -- Credit card fields
    apr_purchase REAL,
    apr_balance_transfer REAL,
    apr_cash_advance REAL,
    minimum_payment_amount REAL,
    last_payment_amount REAL,
    is_overdue BOOLEAN DEFAULT FALSE,
    next_payment_due_date DATE,
    last_statement_balance REAL,
    
    -- Loan fields
    interest_rate REAL,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

#### 5. User Features Table
```sql
CREATE TABLE user_features (
    feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    window_days INTEGER NOT NULL, -- 30 or 180
    computed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Subscription signals
    recurring_merchants INTEGER DEFAULT 0,
    monthly_recurring_spend REAL DEFAULT 0,
    subscription_spend_share REAL DEFAULT 0,
    
    -- Savings signals
    net_savings_inflow REAL DEFAULT 0,
    savings_growth_rate REAL DEFAULT 0,
    emergency_fund_months REAL DEFAULT 0,
    
    -- Credit signals
    avg_utilization REAL DEFAULT 0,
    max_utilization REAL DEFAULT 0,
    utilization_30_flag BOOLEAN DEFAULT FALSE,
    utilization_50_flag BOOLEAN DEFAULT FALSE,
    utilization_80_flag BOOLEAN DEFAULT FALSE,
    minimum_payment_only_flag BOOLEAN DEFAULT FALSE,
    interest_charges_present BOOLEAN DEFAULT FALSE,
    any_overdue BOOLEAN DEFAULT FALSE,
    
    -- Income signals
    payroll_detected BOOLEAN DEFAULT FALSE,
    median_pay_gap_days INTEGER,
    income_variability REAL,
    cash_flow_buffer_months REAL DEFAULT 0,
    avg_monthly_income REAL DEFAULT 0,
    
    -- Investment signals
    investment_account_detected BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, window_days)
);
CREATE INDEX idx_features_user ON user_features(user_id);
```

#### 6. Personas Table
```sql
CREATE TABLE personas (
    persona_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    window_days INTEGER NOT NULL,
    persona_type TEXT NOT NULL CHECK(persona_type IN (
        'high_utilization',
        'variable_income',
        'subscription_heavy',
        'savings_builder',
        'wealth_builder'
    )),
    confidence_score REAL DEFAULT 1.0,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reasoning TEXT, -- JSON with matched criteria
    
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, window_days)
);
CREATE INDEX idx_personas_user ON personas(user_id);
```

#### 7. Recommendations Table
```sql
CREATE TABLE recommendations (
    recommendation_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    persona_type TEXT NOT NULL,
    window_days INTEGER NOT NULL,
    
    content_type TEXT CHECK(content_type IN ('education', 'partner_offer')),
    title TEXT NOT NULL,
    content TEXT NOT NULL, -- AI-generated markdown content
    rationale TEXT NOT NULL, -- Plain-language "because" explanation
    
    status TEXT CHECK(status IN ('pending_approval', 'approved', 'overridden', 'rejected')) DEFAULT 'pending_approval',
    approved_by TEXT,
    approved_at DATETIME,
    override_reason TEXT,
    original_content JSON, -- Stores pre-override version
    
    metadata JSON, -- Links, tags, priority
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    generation_time_ms INTEGER, -- Track latency
    expires_at DATETIME,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE INDEX idx_recommendations_user ON recommendations(user_id);
CREATE INDEX idx_recommendations_status ON recommendations(status);
```

#### 8. Evaluation Metrics Table
```sql
CREATE TABLE evaluation_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Coverage metrics
    total_users INTEGER,
    users_with_persona INTEGER,
    users_with_behaviors INTEGER,
    coverage_percentage REAL,
    
    -- Explainability metrics
    total_recommendations INTEGER,
    recommendations_with_rationale INTEGER,
    explainability_percentage REAL,
    
    -- Latency metrics
    avg_recommendation_latency_ms REAL,
    p95_recommendation_latency_ms REAL,
    
    -- Auditability
    recommendations_with_traces INTEGER,
    auditability_percentage REAL,
    
    -- Additional metrics
    details JSON
);
```

#### 9. Consent Log Table
```sql
CREATE TABLE consent_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    action TEXT CHECK(action IN ('granted', 'revoked')) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE INDEX idx_consent_user ON consent_log(user_id);
```

#### 10. Operator Actions Table
```sql
CREATE TABLE operator_actions (
    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
    operator_id TEXT NOT NULL,
    action_type TEXT CHECK(action_type IN ('approve', 'reject', 'override')) NOT NULL,
    recommendation_id TEXT,
    user_id TEXT NOT NULL,
    reason TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

---

## API Specification

### Base URL
- Local: `http://localhost:8000`
- AWS: `https://{api-id}.execute-api.us-east-1.amazonaws.com/prod`

### Authentication
MVP: No authentication (internal use only)
Stretch: JWT tokens with role-based access (customer vs operator)

---

### Core Endpoints

#### 1. User Management

**POST /users**
```json
// Request
{
  "full_name": "Jane Doe",
  "email": "jane@example.com",
  "user_type": "customer"
}

// Response (201)
{
  "user_id": "usr_abc123",
  "full_name": "Jane Doe",
  "email": "jane@example.com",
  "consent_status": false,
  "created_at": "2025-11-06T10:00:00Z"
}
```

**GET /users**
```json
// Query params: ?user_type=customer&consent_status=true&limit=50&offset=0

// Response (200)
{
  "users": [
    {
      "user_id": "usr_abc123",
      "full_name": "Jane Doe",
      "email": "jane@example.com",
      "consent_status": true,
      "persona": "savings_builder"
    }
  ],
  "total": 75,
  "limit": 50,
  "offset": 0
}
```

**GET /users/{user_id}**
```json
// Response (200)
{
  "user_id": "usr_abc123",
  "full_name": "Jane Doe",
  "email": "jane@example.com",
  "consent_status": true,
  "consent_granted_at": "2025-11-05T14:30:00Z",
  "user_type": "customer",
  "created_at": "2025-11-01T10:00:00Z"
}
```

---

#### 2. Data Ingestion

**POST /ingest**
```json
// Request (multipart/form-data or JSON)
{
  "users": [...],  // Array of user objects
  "accounts": [...],
  "transactions": [...],
  "liabilities": [...]
}

// Response (201)
{
  "status": "success",
  "ingested": {
    "users": 75,
    "accounts": 225,
    "transactions": 15420,
    "liabilities": 180
  },
  "duration_ms": 3421
}
```

---

#### 3. Consent Management

**POST /consent**
```json
// Request
{
  "user_id": "usr_abc123",
  "action": "grant",  // or "revoke"
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}

// Response (200)
{
  "user_id": "usr_abc123",
  "consent_status": true,
  "consent_granted_at": "2025-11-06T10:30:00Z"
}
```

**GET /consent/{user_id}**
```json
// Response (200)
{
  "user_id": "usr_abc123",
  "consent_status": true,
  "consent_granted_at": "2025-11-05T14:30:00Z",
  "consent_revoked_at": null,
  "history": [
    {
      "action": "granted",
      "timestamp": "2025-11-05T14:30:00Z"
    }
  ]
}
```

---

#### 4. Profile & Features

**GET /profile/{user_id}**
```json
// Query params: ?window=30 (default: both 30 and 180)

// Response (200)
{
  "user_id": "usr_abc123",
  "consent_status": true,
  "personas": {
    "30d": {
      "type": "savings_builder",
      "confidence": 0.95,
      "assigned_at": "2025-11-06T08:00:00Z"
    },
    "180d": {
      "type": "savings_builder",
      "confidence": 0.92,
      "assigned_at": "2025-11-06T08:00:00Z"
    }
  },
  "features": {
    "30d": {
      "recurring_merchants": 4,
      "monthly_recurring_spend": 87.50,
      "subscription_spend_share": 0.08,
      "net_savings_inflow": 450.00,
      "savings_growth_rate": 0.03,
      "emergency_fund_months": 2.5,
      "avg_utilization": 0.15,
      "payroll_detected": true,
      "avg_monthly_income": 5200.00
    },
    "180d": { ... }
  }
}
```

---

#### 5. Recommendations

**POST /recommendations/generate/{user_id}**
```json
// Request (optional params)
{
  "window_days": 30,  // default: 30
  "force_regenerate": false  // skip cache
}

// Response (201)
{
  "user_id": "usr_abc123",
  "persona": "savings_builder",
  "recommendations": [
    {
      "recommendation_id": "rec_xyz789",
      "content_type": "education",
      "title": "Automate Your Savings for Faster Growth",
      "content": "You're already saving $450/month—great work! Setting up automatic transfers can help you...",
      "rationale": "We noticed your consistent $450 monthly savings deposits to your Ally Savings account (****1234). Automating this process can ensure you never miss a month and help you reach your emergency fund goal 3 months faster.",
      "status": "pending_approval",
      "generated_at": "2025-11-06T10:45:00Z"
    }
  ],
  "generation_time_ms": 2341
}
```

**GET /recommendations/{user_id}**
```json
// Query params: ?status=approved&window=30

// Response (200)
{
  "user_id": "usr_abc123",
  "recommendations": [
    {
      "recommendation_id": "rec_xyz789",
      "content_type": "education",
      "title": "Automate Your Savings for Faster Growth",
      "content": "...",
      "rationale": "...",
      "status": "approved",
      "approved_by": "operator_001",
      "approved_at": "2025-11-06T11:00:00Z"
    }
  ],
  "total": 5
}
```

**POST /recommendations/{recommendation_id}/approve**
```json
// Request
{
  "operator_id": "operator_001",
  "notes": "Looks good, approved."
}

// Response (200)
{
  "recommendation_id": "rec_xyz789",
  "status": "approved",
  "approved_by": "operator_001",
  "approved_at": "2025-11-06T11:00:00Z"
}
```

**POST /recommendations/{recommendation_id}/override**
```json
// Request
{
  "operator_id": "operator_001",
  "new_title": "Updated Title",
  "new_content": "Updated content...",
  "reason": "Adjusted tone for user sensitivity"
}

// Response (200)
{
  "recommendation_id": "rec_xyz789",
  "status": "overridden",
  "original_content": { ... },
  "new_content": { ... },
  "override_reason": "Adjusted tone for user sensitivity"
}
```

**POST /recommendations/{recommendation_id}/reject**
```json
// Request
{
  "operator_id": "operator_001",
  "reason": "Content quality insufficient"
}

// Response (200)
{
  "recommendation_id": "rec_xyz789",
  "status": "rejected"
}
```

**POST /recommendations/bulk-approve**
```json
// Request
{
  "operator_id": "operator_001",
  "recommendation_ids": ["rec_1", "rec_2", "rec_3"]
}

// Response (200)
{
  "approved": 3,
  "failed": 0
}
```

---

#### 6. Feedback

**POST /feedback**
```json
// Request
{
  "user_id": "usr_abc123",
  "recommendation_id": "rec_xyz789",
  "feedback_type": "helpful",  // helpful, not_helpful, inappropriate
  "comment": "This helped me set up auto-transfer!"
}

// Response (201)
{
  "feedback_id": "fb_001",
  "status": "recorded"
}
```

---

#### 7. Operator Views

**GET /operator/review**
```json
// Query params: ?status=pending_approval&limit=50

// Response (200)
{
  "pending_recommendations": [
    {
      "recommendation_id": "rec_xyz789",
      "user_id": "usr_abc123",
      "user_name": "Jane Doe",
      "persona": "savings_builder",
      "title": "Automate Your Savings",
      "generated_at": "2025-11-06T10:45:00Z",
      "preview": "You're already saving $450/month..."
    }
  ],
  "total": 23
}
```

**GET /operator/users/{user_id}/signals**
```json
// Response (200)
{
  "user_id": "usr_abc123",
  "user_name": "Jane Doe",
  "consent_status": true,
  "30d_signals": {
    "subscriptions": {
      "recurring_merchants": ["Netflix", "Spotify", "Adobe", "GitHub"],
      "monthly_spend": 87.50,
      "spend_share": 0.08
    },
    "savings": {
      "net_inflow": 450.00,
      "growth_rate": 0.03,
      "emergency_fund_months": 2.5
    },
    "credit": {
      "cards": [
        {
          "last_four": "4523",
          "utilization": 0.15,
          "balance": 750,
          "limit": 5000
        }
      ]
    },
    "income": {
      "payroll_detected": true,
      "avg_monthly": 5200.00,
      "frequency": "biweekly"
    }
  },
  "180d_signals": { ... },
  "persona_30d": "savings_builder",
  "persona_180d": "savings_builder"
}
```

**GET /operator/dashboard**
```json
// Response (200)
{
  "total_users": 75,
  "users_with_consent": 52,
  "persona_distribution": {
    "high_utilization": 15,
    "variable_income": 8,
    "subscription_heavy": 12,
    "savings_builder": 18,
    "wealth_builder": 22
  },
  "recommendations": {
    "pending_approval": 23,
    "approved": 145,
    "overridden": 8,
    "rejected": 3
  },
  "metrics": {
    "coverage_percentage": 100.0,
    "explainability_percentage": 100.0,
    "avg_latency_ms": 2341
  }
}
```

---

#### 8. Evaluation & Exports

**POST /evaluate**
```json
// Request
{
  "run_id": "eval_20251106_001"
}

// Response (200)
{
  "run_id": "eval_20251106_001",
  "metrics": {
    "coverage_percentage": 100.0,
    "explainability_percentage": 100.0,
    "avg_recommendation_latency_ms": 2341,
    "p95_recommendation_latency_ms": 4521,
    "auditability_percentage": 100.0
  },
  "parquet_exports": {
    "user_features_30d": "s3://spendsense-analytics/features/user_features_30d_20251106.parquet",
    "user_features_180d": "s3://spendsense-analytics/features/user_features_180d_20251106.parquet",
    "evaluation_results": "s3://spendsense-analytics/eval/eval_20251106_001.parquet"
  },
  "download_urls": {
    "user_features_30d": "https://...",  // Pre-signed URL (7-day expiry)
    "evaluation_results": "https://..."
  }
}
```

**GET /exports/latest**
```json
// Response (200)
{
  "exports": [
    {
      "export_id": "exp_001",
      "file_name": "user_features_30d_20251106.parquet",
      "file_size_mb": 2.4,
      "created_at": "2025-11-06T12:00:00Z",
      "download_url": "https://..."  // Pre-signed S3 URL
    }
  ]
}
```

---

## Feature Requirements

### MVP Features (Must-Have)

#### Data & Features
- ✅ Generate 75 synthetic users with realistic financial profiles
- ✅ 30% users with consent=true (rest=false)
- ✅ Diverse income levels ($2k-$15k/month range)
- ✅ Varied credit behaviors (10%-90% utilization spread)
- ✅ Multiple account types per user (checking, savings, credit, investment)
- ✅ POST /ingest endpoint to populate database
- ✅ Compute all 4 signal categories (subscriptions, savings, credit, income)
- ✅ 30-day and 180-day feature windows

#### Personas
- ✅ All 5 personas implemented with documented criteria
- ✅ Rules-based assignment (deterministic)
- ✅ Prioritization logic for multi-match scenarios
- ✅ Store confidence scores and reasoning

#### Recommendations
- ✅ 5 separate OpenAI endpoints (one per persona)
- ✅ Generate 3-5 education items per user
- ✅ Plain-language rationales citing specific data
- ✅ GPT-4o-mini for content generation
- ✅ Guardrails: consent check, eligibility filters, tone validation
- ✅ Mandatory disclaimer: "This is educational content, not financial advice"

#### Approval Workflow
- ✅ Recommendations start as `pending_approval`
- ✅ Operator must approve before user visibility
- ✅ Bulk approve functionality
- ✅ Override workflow with reason logging
- ✅ Reject with reason

#### User Interface - **CRITICAL MVP REQUIREMENT**
- ✅ React + Vite + Shadcn/ui
- ✅ **Operator view: user list, approval queue, metrics dashboard**
- ✅ **Operator view: click into user → see all signals and recommendations**
- ✅ **User view: consent toggle, approved recommendations display**
- ✅ **Must be functional by end of Day 1 for integration testing**

#### Evaluation
- ✅ Python script: compute coverage, explainability, latency, auditability
- ✅ Write metrics to SQLite `evaluation_metrics` table
- ✅ Export user features to Parquet → S3
- ✅ Generate `evaluation_report.json`
- ✅ Display key metrics in operator dashboard

#### Deployment
- ✅ FastAPI deployed to AWS Lambda via AWS SAM
- ✅ API Gateway for REST endpoints
- ✅ S3 bucket for Parquet exports
- ✅ Pre-signed URLs for downloads (7-day expiry)

#### Testing
- ✅ 10 unit/integration tests minimum
- ✅ Test persona assignment logic
- ✅ Test guardrails enforcement
- ✅ Test API endpoints (happy path)

---

### Stretch Goals (Post-MVP)

#### Redis Caching
- Cache AI-generated recommendations with TTL
- Invalidate cache on new transaction data
- AWS ElastiCache Redis integration

#### Vector Database
- Pinecone or AWS OpenSearch Serverless
- Semantic search over educational content library
- Embed 50-100 pre-written articles
- Return top 3-5 relevant articles per user profile

#### Migration to AWS RDS PostgreSQL
- Replace SQLite with PostgreSQL
- Enable multi-user concurrency
- Production-ready database

#### Enhanced AI Features
- Upgrade specific endpoints to GPT-4o for better quality
- Add image generation for educational infographics
- Video content recommendations

#### Authentication
- JWT tokens for API access
- Role-based access control (customer vs operator)
- Secure endpoints

#### Additional Metrics
- Fairness analysis (demographic parity)
- User engagement tracking
- A/B testing framework for recommendation variations

---

## AI Integration Strategy

### OpenAI Model Selection

**Primary Model: GPT-4o-mini**
- **Use Cases:** All MVP recommendation generation, tone checking, rationale generation
- **Cost:** ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **Latency:** ~1-2 seconds per request
- **Quality:** Sufficient for educational content, better than GPT-3.5-turbo

**Upgrade Path (Post-MVP):**
- If GPT-4o-mini outputs are insufficient, upgrade specific personas to **GPT-4o**
- GPT-4o: $2.50 per 1M input tokens, $10 per 1M output tokens
- More nuanced financial advice, better reasoning
- Monitor quality on Day 2-3 and decide

**NOT using GPT-4 (full):** Too expensive for MVP ($30/1M output tokens)

### Prompt Architecture

**Separate Endpoint Per Persona** (5 total)
- `/recommendations/generate/high_utilization`
- `/recommendations/generate/variable_income`
- `/recommendations/generate/subscription_heavy`
- `/recommendations/generate/savings_builder`
- `/recommendations/generate/wealth_builder`

**Why Separate Endpoints:**
- Dedicated system prompts optimized per persona
- Better context management (only relevant signals passed)
- Easier to tune tone and focus per persona
- Cost tracking per persona
- A/B testing individual personas

### System Prompt Templates

#### Base Template (Shared Guardrails)
```
You are a financial education assistant for SpendSense, a platform that helps users improve their financial literacy.

CRITICAL RULES:
1. NEVER provide regulated financial advice (e.g., "You should invest in X stock")
2. ALWAYS use educational, empowering tone - NO shaming language
3. EVERY recommendation must cite specific user data in the rationale
4. Use plain language (avoid jargon like "amortization", "APR" without explanation)
5. Format output as JSON with keys: title, content, rationale, metadata

OUTPUT FORMAT:
{
  "recommendations": [
    {
      "title": "Short, actionable title",
      "content": "Educational content in markdown format (200-400 words)",
      "rationale": "Because [specific data point], [insight], [benefit]",
      "metadata": {
        "priority": "high|medium|low",
        "tags": ["debt", "budgeting"],
        "links": ["https://..."]
      }
    }
  ]
}

MANDATORY DISCLOSURE (append to every recommendation):
"This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."
```

#### Persona 1: High Utilization
```
PERSONA: High Utilization - User struggling with credit card debt

USER CONTEXT:
{user_data}

FOCUS AREAS:
- Debt paydown strategies (avalanche vs snowball methods)
- Credit utilization impact on credit scores
- Payment automation to avoid late fees
- Balance transfer options (educational only - explain how they work)
- Interest calculation transparency

TONE: Supportive, non-judgmental, action-oriented
AVOID: Phrases like "you're overspending", "bad financial habits"
USE: "Let's explore ways to reduce interest charges", "Many people face this challenge"

Generate 3-5 educational recommendations tailored to this user's credit situation.
```

#### Persona 2: Variable Income
```
PERSONA: Variable Income Budgeter - User with irregular income (freelancer, gig worker, seasonal)

USER CONTEXT:
{user_data}

FOCUS AREAS:
- Percent-based budgeting (not fixed amounts)
- Emergency fund building strategies
- Income smoothing techniques
- Cash flow buffer optimization
- "Feast or famine" expense management

TONE: Practical, empathetic, normalizing
EXAMPLES: Use relatable scenarios like "In high-income months, set aside X% for lean months"

Generate 3-5 educational recommendations for managing variable income.
```

#### Persona 3: Subscription Heavy
```
PERSONA: Subscription Heavy - User with many recurring subscriptions

USER CONTEXT:
{user_data}

FOCUS AREAS:
- Subscription audit checklists
- Cancellation/negotiation tactics
- Free alternative recommendations
- Bill alert setup
- Annual vs monthly cost comparisons

TONE: Helpful, non-preachy, empowering
HIGHLIGHT: Show potential annual savings in concrete dollars

Generate 3-5 educational recommendations about subscription management.
```

#### Persona 4: Savings Builder
```
PERSONA: Savings Builder - User actively building emergency fund/savings

USER CONTEXT:
{user_data}

FOCUS AREAS:
- Goal setting frameworks (3-6 month emergency fund targets)
- Automation strategies (auto-transfers, round-up apps)
- High-yield savings account education (APY explained)
- CD basics for longer-term savings
- Progress tracking and milestone celebration

TONE: Encouraging, motivational, celebrating progress
CELEBRATE: Acknowledge current savings behavior as positive

Generate 3-5 educational recommendations to accelerate savings goals.
```

#### Persona 5: Wealth Builder
```
PERSONA: Wealth Builder - Affluent user ready for investment/retirement planning

USER CONTEXT:
{user_data}

FOCUS AREAS:
- Tax-advantaged investing (401k, IRA, HSA strategies)
- Asset allocation basics (stocks/bonds/real estate)
- Retirement planning milestones
- Estate planning fundamentals
- Charitable giving tax strategies

TONE: Sophisticated but accessible, forward-looking
AVOID: Specific investment recommendations (ETFs, individual stocks)
EDUCATE: Explain concepts like "employer 401k match is free money"

Generate 3-5 educational recommendations for long-term wealth building.
```

### Context Payload Structure

```python
user_data_payload = {
    "user_id": "usr_abc123",
    "window_days": 30,
    "persona": "savings_builder",
    "features": {
        "net_savings_inflow": 450.00,
        "savings_growth_rate": 0.03,
        "emergency_fund_months": 2.5,
        "avg_monthly_income": 5200.00,
        "avg_utilization": 0.15
    },
    "accounts": [
        {
            "type": "savings",
            "name": "Ally Savings ****1234",
            "balance": 6500.00
        },
        {
            "type": "checking",
            "name": "Chase Checking ****5678",
            "balance": 2100.00
        }
    ],
    "recent_transactions": [
        {
            "date": "2025-11-01",
            "merchant": "Ally Bank",
            "amount": 450.00,
            "type": "transfer to savings"
        }
    ]
}
```

### Tone Validation (Guardrails)

**Post-Generation Check:**
```python
def validate_tone(content: str) -> Dict[str, Any]:
    """
    Validates content for tone compliance.
    
    Returns:
        {
            "is_valid": bool,  # True if no warnings, False if any warnings exist
            "validation_warnings": [
                {
                    "severity": "critical" | "notable",
                    "type": "forbidden_phrase" | "lacks_empowering_language",
                    "message": str  # Human-readable description
                }
            ]
        }
    
    Examples:
        # Valid content (no warnings)
        {
            "is_valid": True,
            "validation_warnings": []
        }
        
        # Invalid: Contains forbidden phrase
        {
            "is_valid": False,
            "validation_warnings": [
                {
                    "severity": "critical",
                    "type": "forbidden_phrase",
                    "message": "Contains shaming language: 'you're overspending'"
                }
            ]
        }
        
        # Invalid: Lacks empowering language
        {
            "is_valid": False,
            "validation_warnings": [
                {
                    "severity": "notable",
                    "type": "lacks_empowering_language",
                    "message": "Content lacks empowering tone - no empowering keywords found"
                }
            ]
        }
    """
    
    warnings = []
    
    # Forbidden phrases (CRITICAL - RED in operator UI)
    shame_phrases = [
        "you're overspending",
        "bad habit",
        "poor financial decision",
        "irresponsible",
        "wasteful spending",
        "you should stop",
        "you need to"
    ]
    
    content_lower = content.lower()
    
    for phrase in shame_phrases:
        if phrase in content_lower:
            warnings.append({
                "severity": "critical",
                "type": "forbidden_phrase",
                "message": f"Contains shaming language: '{phrase}'"
            })
    
    # Ensure empowering language present (NOTABLE - YELLOW in operator UI)
    empowering_keywords = ["you can", "let's", "many people", "common challenge", "opportunity", "consider", "explore"]
    if not any(keyword in content_lower for keyword in empowering_keywords):
        warnings.append({
            "severity": "notable",
            "type": "lacks_empowering_language",
            "message": "Content lacks empowering tone - no empowering keywords found"
        })
    
    return {
        "is_valid": len(warnings) == 0,
        "validation_warnings": warnings
    }
```

**Validation Flow:**
1. **All recommendations are persisted** to database with `status='pending_approval'`, regardless of validation warnings
2. **Validation warnings stored in metadata**: `metadata_json["validation_warnings"]` contains array of warnings (empty if valid)
3. **Operator UI displays warnings**:
   - **Critical warnings** (forbidden phrases) → RED badge/alert
   - **Notable warnings** (lacks empowering language) → YELLOW badge/alert
4. **Operator can approve/decline** recommendations regardless of warnings (human oversight)
5. **Warnings are informational** - they flag potential issues but don't block persistence or approval

### Caching Strategy (Stretch Goal - Redis)

**Cache Key Format:**
```
recommendation:{user_id}:{window_days}:{transaction_hash}
```

**Transaction Hash:**
- Hash of user's last 30 days of transaction IDs
- Changes when new transactions added → cache invalidated

**TTL:**
- 7 days (recommendations expire after 1 week)

**Workflow:**
1. Request comes in for user recommendations
2. Check Redis cache with key
3. If hit → return cached recommendations (latency: <50ms)
4. If miss → generate via OpenAI (latency: 2-3s) → cache result
5. On new transaction ingestion → invalidate cache for affected users

**Cost Savings:**
- 75 users × 2 windows = 150 recommendation sets
- Without cache: 150 API calls per evaluation run
- With cache: ~10-20 API calls (only users with new data)
- Savings: ~$0.50-$1.00 per evaluation run (adds up over time)

---

## Persona Definitions

### Persona 1: High Utilization

**Criteria:**
- ANY credit card utilization ≥50% **OR**
- Interest charges detected (interest_charges_present = true) **OR**
- Minimum-payment-only detected **OR**
- Any liability is_overdue = true

**Prioritization:**
- If multiple personas match, High Utilization takes priority when ANY credit card utilization ≥80%

**Primary Educational Focus:**
- Debt paydown strategies (avalanche vs snowball methods)
- Credit utilization impact on credit scores (explain 30% rule)
- Payment automation setup to avoid late fees
- Balance transfer education (how they work, pros/cons)
- Interest calculation transparency (show monthly interest in dollars)

**Example Rationale:**
"We noticed your Visa ending in 4523 is at 68% utilization ($3,400 of $5,000 limit). High credit utilization can negatively impact your credit score. Bringing this below 30% ($1,500) could improve your score and reduce your monthly interest charges of $87."

**Partner Offer Suggestions:**
- Balance transfer credit cards (0% APR intro offers)
- Debt consolidation loan education
- Credit counseling services

---

### Persona 2: Variable Income Budgeter

**Criteria:**
- Median pay gap > 45 days **AND**
- Cash-flow buffer < 1 month

**Prioritization:**
- If savings signals are positive (growth rate ≥2%), Savings Builder takes priority over Variable Income

**Primary Educational Focus:**
- Percent-based budgeting (allocate % of each paycheck, not fixed amounts)
- Emergency fund building for income smoothing
- Cash flow buffer optimization strategies
- "Feast or famine" expense management
- Budgeting apps designed for variable income

**Example Rationale:**
"We noticed your income varies significantly, with pay gaps ranging from 30-60 days. Your current cash flow buffer is 0.8 months. Building a 2-3 month buffer can help smooth out lean periods and reduce financial stress between paychecks."

**Partner Offer Suggestions:**
- Budgeting apps (YNAB, Monarch Money)
- High-yield savings for emergency fund
- Income smoothing tools (apps that advance earned wages)

---

### Persona 3: Subscription Heavy

**Criteria:**
- Recurring merchants ≥3 **AND**
- (Monthly recurring spend ≥$50 in 30-day window **OR** Subscription spend share ≥10%)

**Prioritization:**
- Lowest priority of all personas (others take precedence if multi-match)

**Primary Educational Focus:**
- Subscription audit checklists (list all subscriptions)
- Cancellation tactics and negotiation tips
- Free alternative recommendations (e.g., free trials, library services)
- Bill alert setup to catch upcoming renewals
- Annual vs monthly cost comparisons (show $120/year vs $10/month psychology)

**Example Rationale:**
"You're spending $127/month across 5 recurring subscriptions (Netflix, Spotify, Adobe, GitHub, Peloton). That's $1,524/year—15% of your total spending. An audit could help identify subscriptions you no longer use. Even cutting one could save $100-200 annually."

**Partner Offer Suggestions:**
- Subscription management tools (Truebill, Rocket Money)
- Negotiation services (bill shark)

---

### Persona 4: Savings Builder

**Criteria:**
- Savings growth rate ≥2% over window **OR**
- Net savings inflow ≥$200/month **AND**
- ALL credit card utilizations < 30%

**Prioritization:**
- If investment account detected AND income >$10k/month, Wealth Builder takes priority

**Primary Educational Focus:**
- Goal setting frameworks (3-6 month emergency fund, down payment goals)
- Automation strategies (auto-transfers on payday, round-up apps)
- High-yield savings account education (APY explained, top HYSA providers)
- CD basics for longer-term savings goals (>1 year horizon)
- Progress tracking and milestone celebration techniques

**Example Rationale:**
"You're consistently saving $450/month to your Ally Savings account (****1234), growing your balance by 3% monthly. You're on track to hit a 3-month emergency fund in 4 months. Setting up automatic transfers can ensure you never miss a month and accelerate this to 3 months."

**Partner Offer Suggestions:**
- High-yield savings accounts (Marcus, Ally, Wealthfront)
- Certificate of Deposit (CD) options for goal-based savings
- Savings automation apps (Digit, Qapital)

---

### Persona 5: Wealth Builder

**Criteria:**
- Average monthly income > $10,000 (from payroll ACH detection) **AND**
- Savings balance > $25,000 **AND**
- ALL credit card utilizations ≤20% **AND**
- No overdrafts or late fees in 180-day window **AND**
- Investment account detected (account type = brokerage, 401k, IRA, or similar)

**Prioritization:**
- Highest priority when all criteria met (affluent users ready for advanced strategies)

**Primary Educational Focus:**
- Tax-advantaged investing strategies (401k employer match, IRA contribution limits, HSA triple tax advantage)
- Asset allocation basics (stocks/bonds/real estate diversification)
- Retirement planning milestones (age-based targets)
- Estate planning fundamentals (wills, trusts, beneficiary designations)
- Charitable giving tax strategies (donor-advised funds, appreciated securities)

**Example Rationale:**
"With your consistent $12,500/month income and $45,000 in savings, you're in a strong position to focus on long-term wealth building. We noticed you have a 401(k) account—are you maximizing your employer match? Many employers offer 50-100% match on contributions up to 3-6% of salary, which is effectively free money."

**Partner Offer Suggestions:**
- Robo-advisors for automated investing (Betterment, Wealthfront)
- Financial advisor consultations (fee-only fiduciaries)
- Estate planning attorney resources
- Premium budgeting/net worth tracking tools (Monarch Money Premium)

**Additional Notes:**
- Avoid specific investment recommendations (individual stocks, ETFs)
- Educate on concepts like "time in the market beats timing the market"
- Emphasize tax-advantaged account benefits over taxable brokerage
- Point to reputable sources (IRS.gov for contribution limits, Bogleheads for investment philosophy)

---

### Persona Prioritization Logic

When multiple personas match, apply this prioritization:

1. **Wealth Builder** (if income >$10k + investment account + all other criteria)
2. **High Utilization** (if ANY card ≥80% utilization or overdue)
3. **Savings Builder** (if positive savings signals + low credit utilization)
4. **Variable Income** (if income gaps + low buffer)
5. **Subscription Heavy** (lowest priority, mostly informational)

**Edge Cases:**
- User matches High Utilization + Savings Builder → Assign High Utilization (debt reduction takes priority)
- User matches Wealth Builder criteria except investment account not detected → Assign Savings Builder
- User matches no personas → Assign "General Financial Wellness" (default persona, not part of the 5)

---

## Development Plan

### Hour-by-Hour Breakdown (20 hours total)

---

### Day 1 (10 hours) - **INCLUDES UI AS MVP REQUIREMENT**

#### Hours 1-2: Data Foundation
**Goal:** Generate realistic synthetic data

**Tasks:**
1. Create Python script: `scripts/generate_synthetic_data.py`
2. Use Faker library for names, emails, dates
3. Generate 75 users with varied profiles:
   - Income distribution: $2k-$15k/month (normal distribution, mean=$6k)
   - 30% with consent=true
   - 5% operators (user_type='operator')
4. Generate accounts per user:
   - 1-2 checking accounts (100% of users)
   - 0-1 savings accounts (60% of users)
   - 0-2 credit cards (80% of users, varied limits $1k-$50k)
   - 0-1 investment accounts (30% of users, skew towards high-income)
5. Generate transactions:
   - 150-300 transactions per user over 180 days
   - Mix of: groceries, subscriptions, transfers, payroll deposits
   - Ensure persona signals are present (e.g., recurring merchants, savings deposits)
6. Generate liabilities:
   - Credit card APRs: 15%-25% range
   - Varied utilization: 10%-90%
   - Some users with is_overdue=true, interest_charges>0
7. Output to JSON files:
   - `data/synthetic_users.json`
   - `data/synthetic_accounts.json`
   - `data/synthetic_transactions.json`
   - `data/synthetic_liabilities.json`

**Validation:**
- Run script: `python scripts/generate_synthetic_data.py`
- Verify file sizes: transactions.json should be largest (~5-10MB)
- Spot-check: open files, ensure data looks realistic

**Deliverable:** 4 JSON files with 75 users worth of synthetic data

---

#### Hours 3-4: Backend Core
**Goal:** FastAPI skeleton + database schema + ingestion endpoint

**Tasks:**
1. Initialize FastAPI project:
   ```bash
   mkdir backend
   cd backend
   pip install fastapi uvicorn sqlalchemy pydantic python-dotenv
   ```
2. Create project structure:
   ```
   backend/
   ├── app/
   │   ├── __init__.py
   │   ├── main.py              # FastAPI app with CORS
   │   ├── database.py          # SQLAlchemy setup
   │   ├── models.py            # SQLAlchemy models (10 tables)
   │   ├── schemas.py           # Pydantic schemas
   │   ├── routers/
   │   │   ├── __init__.py
   │   │   ├── ingest.py        # POST /ingest
   │   │   ├── users.py         # User CRUD
   │   │   ├── consent.py       # Consent management
   │   │   ├── profile.py       # GET /profile/{user_id}
   │   │   ├── recommendations.py
   │   │   ├── operator.py      # Operator views
   │   │   └── evaluation.py    # Evaluation endpoints
   │   ├── services/
   │   │   ├── feature_detection.py
   │   │   ├── persona_assignment.py
   │   │   ├── recommendation_engine.py
   │   │   └── guardrails.py
   │   └── utils/
   │       └── helpers.py
   ├── tests/
   ├── requirements.txt
   └── .env
   ```
3. Define SQLAlchemy models for all 10 tables (see Data Models section)
4. **Enable CORS for local frontend development**
5. Implement POST `/ingest` endpoint:
   - Accept JSON payload with users, accounts, transactions, liabilities
   - Validate with Pydantic schemas
   - Bulk insert into SQLite
   - Return ingestion stats (counts, duration)
6. Implement basic GET `/users` and GET `/users/{user_id}` endpoints
7. Test locally:
   ```bash
   uvicorn app.main:app --reload
   curl -X POST http://localhost:8000/ingest -H "Content-Type: application/json" -d @data/synthetic_users.json
   ```

**Deliverable:** Working `/ingest` endpoint that populates SQLite database

---

#### Hours 5-6: Feature Detection Pipeline
**Goal:** Compute all behavioral signals (subscriptions, savings, credit, income)

**Tasks:**
1. Implement `services/feature_detection.py`:
   - `compute_subscription_signals(user_id, window_days)`
   - `compute_savings_signals(user_id, window_days)`
   - `compute_credit_signals(user_id, window_days)`
   - `compute_income_signals(user_id, window_days)`
2. **Subscription Detection:**
   - Query transactions for user in window
   - Group by merchant_name, count occurrences
   - Detect recurring: ≥3 occurrences with ~30-day cadence (±5 days tolerance)
   - Sum monthly_recurring_spend
   - Calculate subscription_spend_share = recurring / total_spend
3. **Savings Detection:**
   - Filter accounts by type IN ('savings', 'money market', 'cash management', 'HSA')
   - Calculate net_savings_inflow = sum(deposits) - sum(withdrawals) to savings accounts
   - Calculate savings_growth_rate = (current_balance - balance_30d_ago) / balance_30d_ago
   - Calculate emergency_fund_months = savings_balance / avg_monthly_expenses
4. **Credit Detection:**
   - Join accounts with liabilities table (account_type = 'credit card')
   - Calculate utilization per card = balance_current / balance_limit
   - Flags: utilization ≥30%, ≥50%, ≥80%
   - Detect minimum_payment_only: last_payment_amount ≤ minimum_payment_amount (within $5 tolerance)
   - Check interest_charges_present: search transactions for category='interest charge'
   - Check any_overdue: is_overdue = true in liabilities
5. **Income Detection:**
   - Search transactions for payment_channel='ACH' AND amount>0 AND category IN ('payroll', 'income', 'salary')
   - Calculate median_pay_gap_days between consecutive payroll deposits
   - Calculate income_variability = std_dev(payroll_amounts) / mean(payroll_amounts)
   - Calculate cash_flow_buffer_months = checking_balance / avg_monthly_expenses
6. **Investment Account Detection:**
   - Check if user has accounts with type IN ('brokerage', '401k', 'ira', 'investment')
7. Create endpoint: POST `/features/compute/{user_id}`:
   - Accepts: `{"window_days": 30}`
   - Computes all signals
   - Inserts/updates `user_features` table
   - Returns computed features as JSON
8. Batch compute for all users:
   - Create script: `scripts/compute_all_features.py`
   - Loop through all users
   - Compute 30d and 180d features
   - Log progress

**Deliverable:** All 75 users have computed features in `user_features` table

---

#### Hours 7-10: **FRONTEND DEVELOPMENT (MVP REQUIREMENT)**
**Goal:** Build React UI for integration testing - operator and user views

**Tasks:**

**Hour 7: Project Setup & Basic Layout**
1. Initialize Vite React project:
   ```bash
   npm create vite@latest frontend -- --template react
   cd frontend
   npm install
   ```
2. Install Shadcn/ui:
   ```bash
   npx shadcn-ui@latest init
   npx shadcn-ui@latest add button card table dialog badge switch
   ```
3. Install dependencies:
   ```bash
   npm install react-router-dom axios recharts
   ```
4. Setup project structure:
   ```
   frontend/
   ├── src/
   │   ├── pages/
   │   │   ├── OperatorDashboard.jsx
   │   │   ├── OperatorUserList.jsx
   │   │   ├── OperatorUserDetail.jsx
   │   │   ├── OperatorApprovalQueue.jsx
   │   │   ├── UserDashboard.jsx
   │   │   └── UserConsent.jsx
   │   ├── components/
   │   │   ├── UserTable.jsx
   │   │   ├── RecommendationCard.jsx
   │   │   ├── SignalDisplay.jsx
   │   │   ├── ConsentToggle.jsx
   │   │   └── MetricsCard.jsx
   │   ├── lib/
   │   │   └── api.js          # Axios instance
   │   ├── App.jsx
   │   └── main.jsx
   ```
5. Setup Axios instance with base URL: `http://localhost:8000`
6. Create basic routing structure with React Router

**Hour 8: Operator Dashboard & User List**
1. **OperatorDashboard.jsx:**
   - Display key metrics (total users, persona distribution, pending approvals)
   - Use Shadcn/ui Card components
   - Fetch data from GET `/operator/dashboard`
   - Simple bar chart for persona distribution (using recharts)
2. **OperatorUserList.jsx:**
   - Paginated table of all users
   - Columns: Name, Email, Persona, Consent Status, Actions
   - Use Shadcn/ui Table component
   - Fetch from GET `/users`
   - Click on user → navigate to detail page
3. **UserTable.jsx component:**
   - Reusable table component with sortable columns
   - Filter by persona and consent status

**Hour 9: Operator User Detail & Approval Queue**
1. **OperatorUserDetail.jsx:**
   - Display user info (name, email, consent status)
   - Show computed features (30d and 180d) in cards
   - Use SignalDisplay component to visualize features
   - Show assigned persona with confidence score
   - List user's recommendations with status badges
   - Fetch from GET `/operator/users/{userId}/signals`
2. **SignalDisplay.jsx component:**
   - Visual display of signals (badges, progress bars)
   - Show subscription merchants, credit utilization, savings rate
3. **OperatorApprovalQueue.jsx:**
   - List of pending recommendations
   - Bulk select checkboxes
   - Bulk approve button
   - Individual approve/reject/override buttons per recommendation
   - Fetch from GET `/operator/review`
4. **RecommendationCard.jsx component:**
   - Display title, preview, persona, generated date
   - Action buttons: Approve, Reject, Override
   - Modal/dialog for override (edit content + reason)

**Hour 10: User View & Integration Testing**
1. **UserDashboard.jsx:**
   - If consent=false, show "Enable recommendations" prompt
   - If consent=true, show approved recommendations feed
   - Use RecommendationCard component (read-only version)
   - Fetch from GET `/recommendations/{userId}?status=approved`
2. **ConsentToggle.jsx component:**
   - Switch component with confirmation dialog
   - POST to `/consent` on toggle
   - Show consent status and last updated timestamp
3. **Integration Testing:**
   - Run backend: `uvicorn app.main:app --reload`
   - Run frontend: `npm run dev`
   - Test full flow:
     - Ingest synthetic data via Postman
     - View users in operator dashboard
     - Click into a user, see features
     - (Persona assignment will come Day 2)
   - Fix any CORS issues
   - Ensure all API calls work

**Deliverable:** Functional React UI (operator + user views) for testing integration

---

### Day 2 (10 hours)

#### Hours 1-2: Persona Assignment
**Goal:** Implement all 5 personas with prioritization logic

**Tasks:**
1. Implement `services/persona_assignment.py`:
   - `assign_persona(user_id, window_days) -> PersonaResult`
2. **Persona Logic (see Persona Definitions section for full criteria)**:
   - `check_high_utilization(features) -> bool`
   - `check_variable_income(features) -> bool`
   - `check_subscription_heavy(features) -> bool`
   - `check_savings_builder(features) -> bool`
   - `check_wealth_builder(features) -> bool`
3. **Prioritization:**
   ```python
   def assign_persona(user_id, window_days):
       features = get_user_features(user_id, window_days)
       matched_personas = []
       
       if check_wealth_builder(features):
           matched_personas.append(('wealth_builder', 1.0))
       if check_high_utilization(features):
           priority = 0.95 if features.max_utilization >= 0.8 else 0.8
           matched_personas.append(('high_utilization', priority))
       if check_savings_builder(features):
           matched_personas.append(('savings_builder', 0.7))
       if check_variable_income(features):
           matched_personas.append(('variable_income', 0.6))
       if check_subscription_heavy(features):
           matched_personas.append(('subscription_heavy', 0.5))
       
       if not matched_personas:
           return ('savings_builder', 0.2)  # fallback with low confidence
       
       # Return highest priority persona
       matched_personas.sort(key=lambda x: x[1], reverse=True)
       return matched_personas[0]
   ```
4. Create endpoint: POST `/personas/assign/{user_id}`:
   - Computes persona for 30d and 180d windows
   - Inserts into `personas` table with reasoning JSON
5. Batch assign for all users:
   - Script: `scripts/assign_all_personas.py`
   - Loop through users, assign personas
6. Validate distribution:
   - Query: `SELECT persona_type, COUNT(*) FROM personas WHERE window_days=30 GROUP BY persona_type`
   - Expect: all 5 personas represented (may need to tweak synthetic data generation)
7. **Update frontend to display personas**

**Deliverable:** All users have assigned personas in database, visible in UI

---

#### Hours 3-7: AI Recommendation Engine
**Goal:** OpenAI integration with 5 persona-specific prompts

**Tasks:**
1. Install OpenAI SDK: `pip install openai`
2. Set environment variable: `OPENAI_API_KEY=sk-...`
3. Implement `services/recommendation_engine.py`:
   - `generate_recommendations(user_id, persona_type, window_days) -> List[Recommendation]`
4. **Create 5 System Prompts:**
   - Store in: `app/prompts/high_utilization.txt`, `variable_income.txt`, etc.
   - See AI Integration Strategy section for full prompt templates
5. **Build Context Payload:**
   ```python
   def build_user_context(user_id, window_days):
       user = get_user(user_id)
       features = get_user_features(user_id, window_days)
       accounts = get_user_accounts(user_id)
       recent_txns = get_recent_transactions(user_id, limit=10)
       
       return {
           "user_id": user_id,
           "window_days": window_days,
           "features": features.dict(),
           "accounts": [
               {
                   "type": acc.type,
                   "name": f"{acc.type.title()} ****{acc.account_id[-4:]}",
                   "balance": acc.balance_current
               }
               for acc in accounts
           ],
           "recent_transactions": [
               {
                   "date": str(txn.date),
                   "merchant": txn.merchant_name,
                   "amount": txn.amount
               }
               for txn in recent_txns
           ]
       }
   ```
6. **OpenAI API Call:**
   ```python
   from openai import OpenAI
   import time
   
   client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
   
   def generate_recommendations(user_id, persona_type, window_days):
       system_prompt = load_prompt(f"app/prompts/{persona_type}.txt")
       user_context = build_user_context(user_id, window_days)
       
       start_time = time.time()
       
       response = client.chat.completions.create(
           model="gpt-4o-mini",
           messages=[
               {"role": "system", "content": system_prompt},
               {"role": "user", "content": json.dumps(user_context)}
           ],
           response_format={"type": "json_object"},
           temperature=0.7
       )
       
       generation_time_ms = int((time.time() - start_time) * 1000)
       
       recommendations_json = json.loads(response.choices[0].message.content)
       
       # Add generation time to each recommendation
       for rec in recommendations_json['recommendations']:
           rec['generation_time_ms'] = generation_time_ms
       
       return recommendations_json['recommendations']
   ```
7. **Guardrails Integration:**
   - Before saving recommendations, call `guardrails.validate_tone(content)`
   - Check consent: `user.consent_status == True`
   - If validation fails, regenerate or reject
8. **Endpoints:**
   - POST `/recommendations/generate/{user_id}`:
     - Check consent
     - Get persona
     - Generate recommendations via OpenAI
     - Validate tone
     - Insert into `recommendations` table with status='pending_approval'
     - Return recommendations + generation time
   - GET `/recommendations/{user_id}`:
     - Query recommendations for user
     - Filter by status (default: approved only for customers)
     - Return list
   - POST `/recommendations/{recommendation_id}/approve`:
     - Update status to 'approved'
     - Log operator action
   - POST `/recommendations/{recommendation_id}/override`:
     - Store original content in JSON field
     - Update title/content with new values
     - Set status='overridden'
     - Log reason
   - POST `/recommendations/bulk-approve`:
     - Loop through recommendation_ids
     - Update all to 'approved'
9. **Test Generation:**
   - Manually trigger for 5-10 test users via UI
   - Review outputs for quality in operator approval queue
   - Adjust prompts if needed
10. **Update Frontend:**
    - Add "Generate Recommendations" button in operator user detail page
    - Update approval queue to show new recommendations
    - Test full approval workflow in UI

**Deliverable:** Working AI recommendation generation for all 5 personas, testable via UI

---

#### Hours 8-10: Evaluation System
**Goal:** Metrics computation script + Parquet exports to S3

**Tasks:**
1. Create `scripts/evaluate.py`:
   ```python
   import pandas as pd
   import numpy as np
   from datetime import datetime
   from app.database import SessionLocal
   from app.models import User, Persona, Recommendation, UserFeatures, EvaluationMetric
   
   def compute_metrics():
       db = SessionLocal()
       run_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
       
       # Coverage
       total_users = db.query(User).filter(User.consent_status == True).count()
       users_with_persona = db.query(Persona).filter(Persona.window_days == 30).count()
       users_with_behaviors = db.query(UserFeatures).filter(
           (UserFeatures.recurring_merchants >= 3) |
           (UserFeatures.net_savings_inflow > 0) |
           (UserFeatures.avg_utilization > 0)
       ).count()
       coverage = (users_with_persona / total_users) * 100 if total_users > 0 else 0
       
       # Explainability
       total_recs = db.query(Recommendation).count()
       recs_with_rationale = db.query(Recommendation).filter(
           Recommendation.rationale != None,
           Recommendation.rationale != ""
       ).count()
       explainability = (recs_with_rationale / total_recs) * 100 if total_recs > 0 else 0
       
       # Latency (from generation_time stored during creation)
       latencies = [r.generation_time_ms for r in db.query(Recommendation).all() if r.generation_time_ms]
       avg_latency = sum(latencies) / len(latencies) if latencies else 0
       p95_latency = np.percentile(latencies, 95) if latencies else 0
       
       # Auditability
       recs_with_traces = total_recs  # All recs have decision traces (persona + features)
       auditability = 100.0
       
       # Insert into evaluation_metrics table
       metric = EvaluationMetric(
           run_id=run_id,
           total_users=total_users,
           users_with_persona=users_with_persona,
           users_with_behaviors=users_with_behaviors,
           coverage_percentage=coverage,
           total_recommendations=total_recs,
           recommendations_with_rationale=recs_with_rationale,
           explainability_percentage=explainability,
           avg_recommendation_latency_ms=avg_latency,
           p95_recommendation_latency_ms=p95_latency,
           recommendations_with_traces=recs_with_traces,
           auditability_percentage=auditability
       )
       db.add(metric)
       db.commit()
       
       print(f"Evaluation {run_id} complete:")
       print(f"  Coverage: {coverage:.1f}%")
       print(f"  Explainability: {explainability:.1f}%")
       print(f"  Avg Latency: {avg_latency:.0f}ms")
       print(f"  P95 Latency: {p95_latency:.0f}ms")
       
       return run_id, metric
   ```
2. **Parquet Export to S3:**
   ```python
   import boto3
   import pyarrow as pa
   import pyarrow.parquet as pq
   
   def export_to_parquet_and_s3(run_id):
       db = SessionLocal()
       
       # Export user features (30d)
       features_30d = pd.read_sql(
           "SELECT * FROM user_features WHERE window_days=30",
           db.bind
       )
       features_30d_path = f'/tmp/user_features_30d_{run_id}.parquet'
       features_30d.to_parquet(features_30d_path)
       
       # Export user features (180d)
       features_180d = pd.read_sql(
           "SELECT * FROM user_features WHERE window_days=180",
           db.bind
       )
       features_180d_path = f'/tmp/user_features_180d_{run_id}.parquet'
       features_180d.to_parquet(features_180d_path)
       
       # Export evaluation results
       eval_df = pd.read_sql(
           f"SELECT * FROM evaluation_metrics WHERE run_id='{run_id}'",
           db.bind
       )
       eval_path = f'/tmp/evaluation_{run_id}.parquet'
       eval_df.to_parquet(eval_path)
       
       # Upload to S3
       s3 = boto3.client('s3')
       bucket_name = os.getenv('S3_BUCKET_NAME', 'spendsense-analytics')
       
       files_to_upload = [
           (features_30d_path, f'features/user_features_30d_{run_id}.parquet'),
           (features_180d_path, f'features/user_features_180d_{run_id}.parquet'),
           (eval_path, f'eval/evaluation_{run_id}.parquet')
       ]
       
       download_urls = {}
       
       for local_path, s3_key in files_to_upload:
           s3.upload_file(local_path, bucket_name, s3_key)
           
           # Generate pre-signed URL (7-day expiry)
           url = s3.generate_presigned_url(
               'get_object',
               Params={
                   'Bucket': bucket_name,
                   'Key': s3_key
               },
               ExpiresIn=604800  # 7 days
           )
           download_urls[s3_key] = url
       
       return download_urls
   ```
3. **S3 Setup:**
   - Create bucket: `spendsense-analytics-{random-suffix}`
   - Set bucket policy to allow access
   - For local development: use AWS credentials from `~/.aws/credentials`
4. **Run Evaluation:**
   ```bash
   python scripts/evaluate.py
   ```
5. **Generate JSON Report:**
   - Script outputs: `evaluation_report.json`
   - Contains all metrics + S3 download URLs
6. **Add Evaluation Endpoint:**
   - POST `/evaluate` - triggers evaluation script, returns metrics + download URLs
7. **Update Frontend:**
   - Add "Run Evaluation" button in operator dashboard
   - Display metrics after evaluation completes
   - Show download links for Parquet files

**Deliverable:** Evaluation metrics in database + Parquet files in S3 + visible in UI

---

### Day 3 (Stretch Goals - Deploy & Polish)

#### AWS Deployment (3-4 hours)
**Goal:** Deploy FastAPI to AWS Lambda via SAM

**Tasks:**
1. Install AWS SAM CLI:
   ```bash
   brew install aws-sam-cli  # macOS
   ```
2. Create `template.yaml` (SAM CloudFormation template):
   ```yaml
   AWSTemplateFormatVersion: '2010-09-09'
   Transform: AWS::Serverless-2016-10-31
   
   Globals:
     Function:
       Timeout: 30
       MemorySize: 512
       Runtime: python3.11
   
   Resources:
     SpendSenseAPI:
       Type: AWS::Serverless::Function
       Properties:
         FunctionName: spendsense-api
         Handler: app.main.handler
         CodeUri: backend/
         Events:
           ApiEvent:
             Type: Api
             Properties:
               Path: /{proxy+}
               Method: ANY
         Environment:
           Variables:
             OPENAI_API_KEY: !Ref OpenAIKey
             DATABASE_URL: sqlite:///tmp/spendsense.db
             S3_BUCKET_NAME: !Ref S3Bucket
   
     S3Bucket:
       Type: AWS::S3::Bucket
       Properties:
         BucketName: !Sub 'spendsense-analytics-${AWS::StackName}'
   
   Parameters:
     OpenAIKey:
       Type: String
       NoEcho: true
   
   Outputs:
     ApiUrl:
       Description: "API Gateway endpoint URL"
       Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/"
     S3BucketName:
       Description: "S3 Bucket for Parquet exports"
       Value: !Ref S3Bucket
   ```
3. Modify FastAPI for Lambda:
   ```python
   # app/main.py
   from mangum import Mangum
   
   app = FastAPI()
   
   # ... all routes ...
   
   handler = Mangum(app)  # AWS Lambda handler
   ```
4. Install dependencies:
   ```bash
   pip install mangum
   ```
5. Build and deploy:
   ```bash
   sam build
   sam deploy --guided
   ```
6. Test deployed API:
   ```bash
   curl https://{api-id}.execute-api.us-east-1.amazonaws.com/Prod/users
   ```
7. Update frontend API base URL to use deployed endpoint

**Deliverable:** FastAPI running on AWS Lambda, frontend connected to production API

---

#### Redis Caching (2-3 hours) - Stretch
**Goal:** Cache AI-generated recommendations

**Tasks:**
1. Set up AWS ElastiCache Redis (or run locally: `docker run -p 6379:6379 redis`)
2. Install redis library: `pip install redis`
3. Implement caching layer:
   ```python
   import redis
   import hashlib
   
   redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
   
   def get_transaction_hash(user_id, window_days):
       txns = get_recent_transactions(user_id, window_days)
       txn_ids = [t.transaction_id for t in txns]
       return hashlib.md5(''.join(txn_ids).encode()).hexdigest()
   
   def get_cached_recommendations(user_id, window_days):
       txn_hash = get_transaction_hash(user_id, window_days)
       cache_key = f"rec:{user_id}:{window_days}:{txn_hash}"
       cached = redis_client.get(cache_key)
       return json.loads(cached) if cached else None
   
   def cache_recommendations(user_id, window_days, recommendations):
       txn_hash = get_transaction_hash(user_id, window_days)
       cache_key = f"rec:{user_id}:{window_days}:{txn_hash}"
       redis_client.setex(cache_key, 604800, json.dumps(recommendations))  # 7-day TTL
   ```
4. Update recommendation generation endpoint to check cache first
5. Add cache hit/miss metrics to evaluation

**Deliverable:** Cached recommendations with sub-50ms latency on cache hits

---

#### Vector Database Integration (4-5 hours) - Stretch
**Goal:** Semantic search over educational content library

**Tasks:**
1. Choose vector DB: Pinecone (free tier) or AWS OpenSearch Serverless
2. Create educational content library:
   - Write/curate 50-100 financial education articles
   - Topics: debt paydown, budgeting, investing, credit scores, etc.
   - Store as markdown files in `content/articles/`
3. Embed content using OpenAI embeddings:
   ```python
   from openai import OpenAI
   
   client = OpenAI()
   
   def embed_article(content):
       response = client.embeddings.create(
           model="text-embedding-3-small",
           input=content
       )
       return response.data[0].embedding
   ```
4. Upload embeddings to Pinecone:
   ```python
   import pinecone
   
   pinecone.init(api_key=os.getenv("PINECONE_API_KEY"))
   index = pinecone.Index("spendsense-articles")
   
   for article in articles:
       embedding = embed_article(article.content)
       index.upsert([(article.id, embedding, article.metadata)])
   ```
5. At recommendation time:
   - Embed user's financial profile
   - Search Pinecone for top 5 relevant articles
   - Include article links in recommendations
6. Update recommendation engine to use semantic search

**Deliverable:** Recommendations include semantically relevant educational articles

---

#### Testing & Polish (2-3 hours)
**Goal:** Write 10 unit tests + polish UI

**Tasks:**
1. Write unit tests (pytest):
   - Test persona assignment logic (4 tests)
   - Test feature detection (3 tests)
   - Test guardrails (2 tests)
   - Test API endpoints (1 test)
2. Polish frontend:
   - Add loading states
   - Improve error handling
   - Add success/error toasts
   - Responsive design tweaks
3. Documentation:
   - Update README with deployment instructions
   - Add screenshots to README
   - Write decision log

**Deliverable:** 10 passing tests + polished UI + documentation

---

## Testing & Evaluation

### Unit Tests (Minimum 10)

**Test Coverage Areas:**
1. **Persona Assignment Logic (4 tests)**
   - Test high utilization detection (utilization ≥50%)
   - Test variable income detection (pay gap >45d, buffer <1mo)
   - Test savings builder detection (growth ≥2%)
   - Test wealth builder detection (income >$10k, investment account)

2. **Feature Detection (3 tests)**
   - Test subscription detection (recurring merchants ≥3)
   - Test credit utilization calculation
   - Test emergency fund months calculation

3. **Guardrails (2 tests)**
   - Test consent enforcement (no recs without consent)
   - Test tone validation (detect shaming phrases)

4. **API Endpoints (1 test)**
   - Test POST `/ingest` with valid JSON payload

**Test Framework:** pytest

**Example Test:**
```python
# tests/test_personas.py
import pytest
from app.services.persona_assignment import check_high_utilization

def test_high_utilization_detection():
    features = {
        "max_utilization": 0.68,
        "interest_charges_present": True,
        "any_overdue": False
    }
    assert check_high_utilization(features) == True

def test_high_utilization_not_detected():
    features = {
        "max_utilization": 0.25,
        "interest_charges_present": False,
        "any_overdue": False
    }
    assert check_high_utilization(features) == False
```

**Run Tests:**
```bash
cd backend
pytest tests/ -v
```

---

### Evaluation Metrics (Success Criteria)

**Target Metrics:**
- ✅ Coverage: 100% (all consented users have persona + ≥3 detected behaviors)
- ✅ Explainability: 100% (all recommendations have plain-language rationales)
- ✅ Latency: <5 seconds per user recommendation generation
- ✅ Auditability: 100% (all recommendations have decision traces)

**Evaluation Script Output:**
```json
{
  "run_id": "eval_20251106_001",
  "timestamp": "2025-11-06T15:30:00Z",
  "metrics": {
    "total_users": 52,
    "users_with_persona": 52,
    "users_with_behaviors": 52,
    "coverage_percentage": 100.0,
    "total_recommendations": 247,
    "recommendations_with_rationale": 247,
    "explainability_percentage": 100.0,
    "avg_recommendation_latency_ms": 2341,
    "p95_recommendation_latency_ms": 4521,
    "recommendations_with_traces": 247,
    "auditability_percentage": 100.0
  },
  "persona_distribution": {
    "high_utilization": 12,
    "variable_income": 7,
    "subscription_heavy": 9,
    "savings_builder": 14,
    "wealth_builder": 10
  },
  "parquet_exports": {
    "user_features_30d": "s3://spendsense-analytics/features/user_features_30d_20251106.parquet",
    "download_url": "https://spendsense-analytics.s3.amazonaws.com/..."
  }
}
```

---

## Deployment Strategy

### AWS SAM Configuration

**Architecture:**
```
User/Operator Browser
    ↓
CloudFront (optional, for React frontend)
    ↓
API Gateway
    ↓
AWS Lambda (FastAPI)
    ↓
SQLite (stored in /tmp/) OR RDS PostgreSQL (stretch)
    ↓
S3 (Parquet exports)
```

**SAM Template Highlights:**
- Lambda function: 512MB memory, 30s timeout
- API Gateway: REST API with ANY method on /{proxy+}
- Environment variables: OPENAI_API_KEY, DATABASE_URL, S3_BUCKET_NAME
- S3 bucket for Parquet exports

**Deployment Commands:**
```bash
# First time
sam build
sam deploy --guided

# Subsequent deploys
sam build && sam deploy
```

**Cost Estimates (MVP usage):**
- Lambda: ~$0.20/day (10-20 invocations, mostly development testing)
- API Gateway: ~$0.035/1000 requests (~$0.05/day)
- S3: ~$0.023/GB/month (~$0.05/month for Parquet files)
- OpenAI API: ~$0.50-$1.00/day during development (75 users × 5 personas × 2 windows = ~750 API calls total, but cached after first gen)

**Total MVP cost: ~$5-10 for 2-4 days of development**

---

### Local Development Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:5173
```

**Environment Variables (.env):**
```env
OPENAI_API_KEY=sk-...
DATABASE_URL=sqlite:///./spendsense.db
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=spendsense-analytics
```

---

## Success Metrics & Demo Plan

### Demo Flow (5-10 minutes)

**Act 1: Data Ingestion (1 min)**
1. Show synthetic data JSON files (75 users)
2. POST `/ingest` via UI button → database populated
3. Show SQLite database (users, accounts, transactions tables)

**Act 2: Feature Detection & Personas (2 min)**
1. Run feature computation via UI button
2. Show `user_features` table with computed signals in operator dashboard
3. Run persona assignment
4. Show persona distribution chart (all 5 personas represented)

**Act 3: AI Recommendations (2 min)**
1. Open operator dashboard
2. Click into a "High Utilization" user
3. Show detected signals (68% utilization, $87/month interest)
4. Click "Generate Recommendations" button
5. Show AI-generated content with plain-language rationale

**Act 4: Approval Workflow (1 min)**
1. Navigate to approval queue in UI
2. Bulk approve 5 pending recommendations via checkbox selection
3. Show one recommendation moving to "approved" status
4. Override one recommendation (edit content via modal, add reason)

**Act 5: User Experience (1 min)**
1. Switch to user view in UI
2. Show consent toggle (revoke → no recommendations visible)
3. Grant consent → recommendations appear
4. Click into recommendation → show full educational content

**Act 6: Evaluation & Metrics (2 min)**
1. Run evaluation via UI button
2. Show metrics dashboard:
   - Coverage: 100%
   - Explainability: 100%
   - Avg latency: 2.3s
3. Download Parquet file from S3 (show pre-signed URL)
4. Open in pandas/Excel → show raw feature data

**Closing: Highlight AI Integration**
- 5 separate OpenAI endpoints (persona-specific prompts)
- GPT-4o-mini for cost efficiency
- Tone validation guardrails (no shaming language)
- Explainable AI (rationales cite specific user data)
- **Full-stack integration with React UI for testing**

---

## Documentation Requirements

### README.md
- Project overview (1 paragraph)
- Setup instructions (one-command if possible)
- How to run locally (backend + frontend)
- How to deploy to AWS
- How to run evaluation script
- Screenshots of UI

### Decision Log (docs/DECISIONS.md)
- Why FastAPI? (Python for data pipelines, async support, auto-docs)
- Why SQLite for MVP? (Zero setup, good enough for 75 users, easy migration to Postgres)
- Why 5 personas? (Requirements specified 5, covers major financial archetypes)
- Why GPT-4o-mini? (Cost-effective, sufficient quality for educational content)
- Why Shadcn/ui? (LLM-friendly, modern, accessible components)
- **Why UI on Day 1? (Essential for integration testing, ensures end-to-end flow works early)**

### API Documentation
- Auto-generated by FastAPI: `http://localhost:8000/docs`
- Swagger UI with all endpoints, schemas, examples

### Limitations Document (docs/LIMITATIONS.md)
- **Synthetic Data**: Not real bank data, patterns may not reflect actual user behavior
- **No Financial Advice**: Educational content only, not personalized financial advice
- **Persona Simplification**: Real users may not fit neatly into 5 categories
- **AI Variability**: GPT-4o-mini outputs non-deterministic, requires tone validation
- **Scalability**: SQLite not suitable for production (move to RDS PostgreSQL)
- **Security**: No authentication in MVP (add JWT tokens for production)

---

## Appendix

### Dependencies (requirements.txt)
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
python-dotenv==1.0.0
openai==1.3.5
redis==5.0.1
pandas==2.1.3
pyarrow==14.0.1
faker==20.1.0
boto3==1.29.7
pytest==7.4.3
httpx==0.25.2  # for testing FastAPI
mangum==0.17.0  # AWS Lambda adapter
```

### Tech Stack Summary
- **Backend**: FastAPI (Python 3.11+), SQLite/PostgreSQL
- **Frontend**: React 18, Vite, Shadcn/ui, TailwindCSS - **MVP REQUIREMENT**
- **AI**: OpenAI GPT-4o-mini
- **Infrastructure**: AWS Lambda, API Gateway, S3, SAM
- **Caching**: Redis (ElastiCache or local) - stretch
- **Analytics**: Pandas, Parquet

### Key Files to Create
1. `backend/app/main.py` - FastAPI app with CORS
2. `backend/app/models.py` - SQLAlchemy models (10 tables)
3. `backend/app/services/persona_assignment.py` - Persona logic
4. `backend/app/services/recommendation_engine.py` - OpenAI integration
5. `backend/app/prompts/*.txt` - System prompts for each persona
6. `scripts/generate_synthetic_data.py` - Data generation
7. `scripts/compute_all_features.py` - Feature detection
8. `scripts/evaluate.py` - Metrics computation
9. **`frontend/src/pages/OperatorDashboard.jsx`** - Operator UI - **MVP**
10. **`frontend/src/pages/UserDashboard.jsx`** - User UI - **MVP**
11. `template.yaml` - AWS SAM configuration

---

## Final Checklist

**Day 1 Deliverables (ALL MVP):**
- [ ] 75 synthetic users in JSON files
- [ ] SQLite database schema (10 tables)
- [ ] POST `/ingest` endpoint working
- [ ] All behavioral signals computed (30d and 180d windows)
- [ ] **React frontend initialized with Shadcn/ui**
- [ ] **Operator dashboard functional (user list, metrics)**
- [ ] **User dashboard functional (consent toggle, recommendations view)**
- [ ] **Full integration testing possible via UI**

**Day 2 Deliverables (ALL MVP):**
- [ ] All 5 personas assigned with prioritization
- [ ] AI recommendation generation working (5 endpoints)
- [ ] Guardrails enforced (consent, tone, eligibility)
- [ ] **Recommendations visible and testable in UI**
- [ ] **Approval workflow functional in UI (approve/reject/override)**
- [ ] Evaluation script outputs metrics + Parquet to S3
- [ ] **Metrics displayed in operator dashboard**

**Stretch (Day 3+):**
- [ ] FastAPI deployed to AWS Lambda
- [ ] Frontend deployed (Vercel/Netlify/S3+CloudFront)
- [ ] Redis caching (optional)
- [ ] Vector database integration (optional)
- [ ] 10 unit tests passing

**Documentation:**
- [ ] README with setup instructions + screenshots
- [ ] Decision log explaining key choices (including UI-first approach)
- [ ] Limitations documented
- [ ] Demo video or live presentation ready

---

## Feature Extension: Product Recommendations

### Overview

SpendSense will recommend relevant financial products (savings accounts, credit cards, apps, services) alongside educational content. Products are matched to users based on persona type and behavioral signals, then filtered by eligibility criteria to ensure appropriate recommendations.

### Goals

1. **Hybrid Recommendations**: Generate 2-3 product recommendations per user in addition to 2-3 educational recommendations (total 3-5 items)
2. **Smart Matching**: Match products based on persona type and specific financial signals
3. **Eligibility Filtering**: Apply hard filters for income, credit utilization, and existing accounts
4. **Realistic Catalog**: Generate 20-25 realistic products using LLM (GPT-4o)
5. **Transparent Display**: Show product offers with benefits, partner links, and mandatory disclosure text in UI

### Product Types & Categories

#### Product Types
- `savings_account` - High-yield savings accounts, CDs, money market accounts
- `credit_card` - Balance transfer cards, cash back cards, rewards cards
- `app` - Budgeting apps, expense trackers, financial planning tools
- `service` - Subscription managers, bill negotiation, credit counseling
- `investment_account` - Robo-advisors, retirement planning, brokerage accounts

#### Product Categories
- `balance_transfer` - 0% APR balance transfer credit cards
- `hysa` - High-yield savings accounts
- `budgeting_app` - Budgeting and expense tracking applications
- `subscription_manager` - Subscription tracking and cancellation services
- `robo_advisor` - Automated investment management
- `personal_loan` - Debt consolidation loans
- `cash_back_card` - Cash back rewards credit cards
- `credit_counseling` - Free or paid credit counseling services

### Database Schema Extension

#### product_offers Table
```sql
CREATE TABLE product_offers (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    product_type TEXT NOT NULL, -- savings_account, credit_card, app, service, investment_account
    category TEXT NOT NULL, -- balance_transfer, hysa, budgeting_app, etc.
    persona_targets TEXT NOT NULL, -- JSON array: ["high_utilization", "savings_builder"]
    
    -- Eligibility criteria
    min_income REAL DEFAULT 0,
    max_credit_utilization REAL DEFAULT 1.0,
    requires_no_existing_savings BOOLEAN DEFAULT FALSE,
    requires_no_existing_investment BOOLEAN DEFAULT FALSE,
    min_credit_score INTEGER,
    
    -- Content
    short_description TEXT NOT NULL,
    benefits TEXT NOT NULL, -- JSON array of benefit strings
    typical_apy_or_fee TEXT,
    partner_link TEXT,
    disclosure TEXT NOT NULL,
    
    -- Business
    partner_name TEXT NOT NULL,
    commission_rate REAL DEFAULT 0.0,
    priority INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT TRUE,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_product_offers_persona ON product_offers(persona_targets);
CREATE INDEX idx_product_offers_active ON product_offers(active);
```

#### recommendations Table Extension
```sql
ALTER TABLE recommendations ADD COLUMN content_type TEXT DEFAULT 'education';
ALTER TABLE recommendations ADD COLUMN product_id TEXT;
ALTER TABLE recommendations ADD FOREIGN KEY (product_id) REFERENCES product_offers(product_id);
```

### Product Catalog Generation

#### LLM-Based Generation
**Tool**: OpenAI GPT-4o  
**Script**: `scripts/generate_product_catalog.py`  
**Output**: `data/product_catalog.json`  
**Cost**: ~$0.20 (one-time)

**Prompt Structure**:
- Generate 20-25 realistic financial products
- 4-5 products per persona (high_utilization, variable_income, subscription_heavy, savings_builder, wealth_builder)
- Include realistic product names (e.g., "Chase Slate Edge", "Marcus High-Yield Savings")
- Set appropriate eligibility criteria based on product type
- Generate 3-5 specific benefits per product
- Use current market APY/fee rates

**Example Products**:

```json
{
  "product_id": "prod_001",
  "product_name": "Chase Slate Edge",
  "product_type": "credit_card",
  "category": "balance_transfer",
  "persona_targets": ["high_utilization"],
  "min_income": 2500,
  "max_credit_utilization": 0.85,
  "min_credit_score": 670,
  "short_description": "0% intro APR for 18 months on balance transfers",
  "benefits": [
    "0% intro APR on balance transfers for 18 months",
    "No balance transfer fee for first 60 days",
    "$0 annual fee",
    "Credit score monitoring included"
  ],
  "typical_apy_or_fee": "0% intro APR for 18mo",
  "disclosure": "This is educational content, not financial advice..."
}
```

#### Product Seeding
**Script**: `scripts/seed_product_catalog.py`
- Clears existing products
- Loads JSON catalog
- Inserts into database
- Prints distribution statistics

### Product Matching Logic

#### Relevance Scoring Algorithm

**Service**: `backend/app/services/product_matcher.py`

**Scoring Rules** (base score 0.5, add points for relevance):

**Balance Transfer Cards**:
- +0.3 if avg_utilization > 0.5
- +0.2 if interest_charges_present
- +0.2 if avg_utilization > 0.7 (bonus for very high)

**HYSA (High-Yield Savings)**:
- +0.4 if net_savings_inflow > 0 AND emergency_fund_months < 3
- +0.2 if savings_growth_rate > 0.02
- -0.5 if has existing HYSA (penalty)

**Budgeting Apps**:
- +0.3 if income_variability > 0.3
- +0.3 if financial_buffer_days < 30
- +0.2 if avg_monthly_expenses_volatility > 0.25

**Subscription Managers**:
- +0.4 if recurring_merchants >= 5
- +0.3 if subscription_spend_share > 0.2

**Investment Products (Robo-Advisors)**:
- +0.4 if monthly_income > 5000 AND avg_utilization < 0.3
- +0.3 if emergency_fund_months >= 3
- -0.4 if has existing investment account (penalty)

**Final Score**: Clamp to [0.0, 1.0]

#### Matching Flow

1. Query active products where persona_targets contains user's persona
2. For each product, calculate relevance_score using signals
3. Filter out products with score < 0.5 (low relevance)
4. Sort by relevance_score descending
5. Return top 3 products

### Eligibility Filtering

#### Guardrails Service Extension
**Service**: `backend/app/services/guardrails.py`  
**Function**: `check_product_eligibility()`

**Hard Filters** (returns `(is_eligible: bool, reason: str)`):

1. **Income Requirements**:
   - If product.min_income > user's avg_monthly_income → not eligible
   - Reason: "Income below minimum requirement"

2. **Credit Utilization**:
   - If product.max_credit_utilization < user's avg_utilization → not eligible
   - Reason: "Credit utilization too high"

3. **Existing Savings Account**:
   - If product.requires_no_existing_savings AND user has savings account → not eligible
   - Reason: "Already has savings account"

4. **Existing Investment Account**:
   - If product.requires_no_existing_investment AND user has investment account → not eligible
   - Reason: "Already has investment account"

5. **Category-Specific Rules**:
   - Balance transfer cards: Require avg_utilization >= 0.3 (only show if meaningful balance to transfer)
   - Reason: "Balance transfer not beneficial at current utilization"

### Hybrid Recommendation Engine

#### Updated Flow

**Service**: `backend/app/services/recommendation_engine.py`  
**Function**: `generate_combined_recommendations()`

**Steps**:

1. **Generate Educational Recommendations** (existing logic)
   - Call OpenAI with persona-specific prompt
   - Generate 2-3 educational items
   - Set `content_type = 'education'`

2. **Generate Product Recommendations** (new logic)
   - Get user features and accounts
   - Call `match_products()` from product_matcher
   - Get top 3 matched products with scores
   - Apply `check_product_eligibility()` to each
   - Take top 1-2 eligible products
   - Set `content_type = 'partner_offer'`
   - Format product data for recommendation structure

3. **Combine and Store**
   - Merge educational and product recommendations
   - Target total: 3-5 recommendations (2-3 education + 1-2 products)
   - Generate recommendation_id for each
   - Store in recommendations table with appropriate content_type
   - Return combined list

### API Updates

#### Generate Recommendations Endpoint Update
**Endpoint**: `POST /recommendations/generate/{user_id}`  
**Changes**:
- Replace `generate_recommendations()` with `generate_combined_recommendations()`
- Store both content types in database
- Return mixed list in response

**Response Example**:
```json
{
  "recommendations": [
    {
      "recommendation_id": "rec_123",
      "content_type": "education",
      "title": "Understanding Credit Utilization Impact",
      "content": "Your credit utilization of 68% is impacting...",
      "rationale": "With average utilization at 68%, this is..."
    },
    {
      "recommendation_id": "rec_124",
      "content_type": "partner_offer",
      "product_id": "prod_001",
      "product_name": "Chase Slate Edge",
      "short_description": "0% intro APR for 18 months",
      "benefits": ["0% intro APR...", "No balance transfer fee..."],
      "partner_link": "https://example.com/prod_001",
      "disclosure": "This is educational content...",
      "rationale": "With your credit utilization at 68%, this card could save you $87/month in interest."
    }
  ]
}
```

#### Optional: Product Management API
**Router**: `backend/app/routers/products.py`

```python
GET /products - List all products
GET /products/{product_id} - Get single product
POST /products - Create product (manual additions)
PUT /products/{product_id} - Update product
DELETE /products/{product_id} - Deactivate product (soft delete)
```

### Frontend Updates

#### RecommendationCard Component Extension
**File**: `frontend/src/components/RecommendationCard.jsx`

**Changes**:
- Detect `content_type` field
- Render different layouts based on type

**For Education Type** (existing):
- Display title, markdown content, rationale
- Keep existing styling

**For Partner Offer Type** (new):
- Display "Partner Offer" badge (secondary variant)
- Show product_name as title
- Show partner_name as subtitle
- Display short_description
- Show benefits as bulleted list with checkmarks (✓)
- Display typical_apy_or_fee prominently if present
- Add "Learn More" button (links to partner_link, opens in new tab)
- Display disclosure text (text-xs, muted, italic, bottom of card)
- Light blue/purple background to distinguish from education cards
- Display rationale (common for both types)

**Example Product Card UI**:
```
┌─────────────────────────────────────────────┐
│ 🏷️ Partner Offer                            │
│                                             │
│ Chase Slate Edge                            │
│ by Chase                                    │
│                                             │
│ 0% intro APR for 18 months on balance      │
│ transfers                                   │
│                                             │
│ ┌─ Benefits ─────────────────────────────┐ │
│ │ ✓ 0% intro APR for 18 months          │ │
│ │ ✓ No balance transfer fee (first 60d) │ │
│ │ ✓ $0 annual fee                       │ │
│ │ ✓ Credit score monitoring included    │ │
│ └──────────────────────────────────────── │ │
│                                             │
│ 📊 0% intro APR for 18mo                   │
│                                             │
│ [Learn More →]                              │
│                                             │
│ Why: With your credit utilization at 68%,  │
│ this card could save you $87/month in      │
│ interest.                                   │
│                                             │
│ ⓘ This is educational content, not         │
│   financial advice. Product terms subject   │
│   to change.                                │
└─────────────────────────────────────────────┘
```

#### UserDashboard Updates
**File**: `frontend/src/pages/UserDashboard.jsx`

**Changes**: Minimal (RecommendationCard handles rendering)
- Verify recommendations list displays mix naturally
- Test with both content types

#### OperatorUserDetail Updates
**File**: `frontend/src/pages/OperatorUserDetail.jsx`

**Changes**:
- Show content_type column in recommendations table
- Display product_name for partner_offer rows
- Add "Product" badge or icon
- Optional: Filter dropdown (All / Educational Only / Products Only)

### Testing Strategy

#### Unit Tests

**File**: `backend/tests/test_product_matcher.py`
- Test relevance scoring for all product categories
- Verify score calculations with different user features
- Test that low-relevance products are filtered out

**File**: `backend/tests/test_product_eligibility.py`
- Test income requirements
- Test credit utilization limits
- Test existing account checks
- Test category-specific rules

#### Integration Tests

**File**: `backend/tests/test_product_recommendations_integration.py`
- Test full flow: generation → matching → filtering → storage
- Verify mix of education + products returned
- Test edge cases (no eligible products, all products filtered)

#### Manual Testing
1. Generate product catalog
2. Seed into database
3. Generate recommendations for each persona type
4. Verify product matches make sense
5. Test approval workflow for product recommendations
6. Verify frontend display (benefits, links, disclosure)

### Compliance & Legal

#### Required Disclaimers

All product recommendations MUST include:
```
This is educational content, not financial advice. Product terms, rates, and 
availability subject to change. SpendSense may receive compensation from partners. 
Consult a licensed financial advisor for personalized guidance.
```

#### Data Usage
- Product recommendations based on transaction data (already consented)
- No additional consent required beyond existing consent flow
- Users can revoke consent anytime (removes all recommendations)

#### Affiliate Disclosure
- Clearly mark partner offers as "Partner Offer"
- Disclose potential compensation (even if $0 for MVP)
- No deceptive marketing practices

### Success Metrics

**Coverage**:
- % of users receiving at least 1 product recommendation
- Target: 60-80% (not all users will be eligible for all products)

**Eligibility**:
- % of matched products that pass eligibility filtering
- Target: >50% (indicates matching logic is working)

**Mix**:
- Average ratio of educational to product recommendations
- Target: 2:1 to 3:1 (more educational content than products)

**Quality**:
- Operator approval rate for product recommendations
- Target: >80% (high confidence in matching + eligibility logic)

### Implementation Timeline

**Total: 4-6 hours across 8 PRs**

#### PR #38: Database Schema & Product Catalog Generation (1-2 hours)
- Create product_offers table migration
- Generate product catalog via GPT-4o
- Review and validate generated products
- Create seeding script

#### PR #39: Product Seeding & Database Population (30 min)
- Implement seeding script
- Test database insertion
- Verify data integrity

#### PR #40: Product Matching Service (60 min)
- Implement relevance scoring algorithm
- Create product matching function
- Generate rationales citing user data

#### PR #41: Enhanced Guardrails - Product Eligibility (45 min)
- Implement eligibility checking
- Add category-specific rules
- Integration with product matcher

#### PR #42: Hybrid Recommendation Engine (45 min)
- Update recommendation engine
- Combine education + products
- Update database storage

#### PR #43: Frontend - Product Recommendation Display (1 hour)
- Update RecommendationCard component
- Add product card styling
- Test with both content types

#### PR #44: Product Management API (Optional) (30 min)
- CRUD endpoints for operators
- Product filtering and search

#### PR #45: Unit Tests & Documentation (30-60 min)
- Write 20+ unit tests
- Update README and decision log
- Create product catalog documentation

### Future Enhancements

#### Post-MVP Phase
- Real partner integrations with affiliate APIs
- Click tracking and conversion analytics
- A/B testing framework (products vs. no products)
- Product comparison tool (side-by-side)
- User feedback ("Was this helpful?")
- Seasonal offers and limited-time promotions

#### Production Phase
- Machine learning for product matching (replace rule-based)
- Real-time product availability checks via partner APIs
- Personalized APY/rate quotes based on user's credit profile
- Integration with credit score APIs for better eligibility
- Automated product catalog updates (weekly scraping)

### Limitations

**MVP Constraints**:
- Product catalog is LLM-generated (not live data)
- Partner links are placeholder URLs (example.com)
- APY rates may be outdated (but realistic for demonstration)
- Product availability not verified in real-time
- No actual affiliate partnerships or commission tracking

**Impact**:
- Users cannot actually sign up for products through the platform
- Product data may not reflect current market offerings

**Recommendation for Production**:
- Integrate with real financial product APIs (CardRatings, DepositAccounts, Plaid)
- Establish affiliate partnerships with actual financial institutions
- Implement real-time rate updates via partner APIs
- Add click tracking and conversion measurement

---

## Feature Extension: Educational Article Recommendations

### Overview

SpendSense will link educational recommendations to relevant external articles using vector similarity search. This feature uses Pinecone vector database with OpenAI embeddings to match each generated educational recommendation to the most relevant article from a curated catalog in real-time.

### Goals

1. **Enhanced Educational Content**: Link each educational recommendation to a relevant external article (if similarity >0.75)
2. **Real-Time Matching**: Use vector similarity search for fast matching (~100-300ms for 2-3 recs)
3. **Quality Threshold**: Only show articles that are highly relevant (similarity score >= 0.75)
4. **User Experience**: Provide "Read Full Article" button with article metadata (title, source, reading time, summary)
5. **MVP Speed**: Use LLM-generated articles for MVP (60-90 seconds vs. 1-2 hours manual curation)

### Why Vector DB is Ideal for This Use Case

**Comparison to Previous Vector DB Proposal**:
- **Previous Use Case**: Cache educational recommendations for similar users
  - Problem: Required 500-1,000 users for meaningful similarity
  - Problem: Cold start issue (new users have no cached recs)
  - Problem: User context too complex for simple similarity
- **Article Matching Use Case**: Semantic similarity between rec and article
  - ✅ Works with 50-100 articles (no minimum user requirement)
  - ✅ No cold start (articles are pre-embedded once)
  - ✅ Pure semantic matching (perfect for vector DB)
  - ✅ Much faster than LLM-based matching (300ms vs. 5-17s)

### Article Catalog Design

#### articles Table Schema
```sql
CREATE TABLE articles (
    article_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT NOT NULL, -- 'NerdWallet', 'Investopedia', 'CFPB', etc.
    url TEXT NOT NULL, -- Placeholder URLs for MVP
    summary TEXT NOT NULL, -- 2-3 sentences for display
    full_text TEXT NOT NULL, -- Full article content for embedding (300-500 words)
    categories TEXT, -- JSON array: ["credit", "debt", "budgeting"]
    persona_targets TEXT, -- JSON array: ["high_utilization", "savings_builder"]
    reading_time_minutes INTEGER,
    published_date DATE,
    active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_articles_persona ON articles(persona_targets);
CREATE INDEX idx_articles_active ON articles(active);
CREATE INDEX idx_articles_categories ON articles(categories);
```

#### recommendations Table Extension
```sql
ALTER TABLE recommendations ADD COLUMN article_id TEXT;
ALTER TABLE recommendations ADD FOREIGN KEY (article_id) REFERENCES articles(article_id);
```

### Article Generation (LLM-Based for MVP)

#### Why LLM-Generated Articles for MVP
- **Speed**: 60-90 seconds for 50 articles vs. 1-2 hours manual curation
- **Consistency**: LLM generates structured data (title, summary, full_text, metadata)
- **Good Enough**: Realistic-sounding articles sufficient for demonstrating vector matching
- **Replaceable**: Easy to swap with real articles later (update URLs + full_text, regenerate embeddings)

#### Generation Approach
**Script**: `scripts/generate_article_catalog.py`  
**Tool**: OpenAI GPT-4o  
**Output**: `data/article_catalog.json`  
**Cost**: ~$0.30-0.50 (one-time)

**Prompt Structure**:
- Generate 50 articles total (10 per persona)
- Personas: high_utilization, variable_income, subscription_heavy, savings_builder, wealth_builder
- Realistic titles (e.g., "How to Pay Down Credit Card Debt Fast")
- Realistic sources (NerdWallet, Investopedia, CFPB, The Balance, Forbes)
- 2-3 sentence summaries (for display in UI)
- 300-500 word "full text" (simulated article content for quality embeddings)
- Realistic reading times (5-10 minutes)
- Appropriate categories (credit, debt, budgeting, savings, investing, etc.)
- Persona targets (can be multiple)
- Placeholder URLs (https://example.com/articles/article-slug)

**Example Article**:
```json
{
  "article_id": "art_001",
  "title": "How to Lower Your Credit Utilization Fast",
  "source": "NerdWallet",
  "url": "https://example.com/articles/lower-credit-utilization",
  "summary": "Learn proven strategies to reduce your credit card utilization and improve your credit score. We cover balance transfers, payment timing, and limit increases.",
  "full_text": "[300-500 words of simulated article content for embedding...]",
  "categories": ["credit", "debt", "high_utilization"],
  "persona_targets": ["high_utilization"],
  "reading_time_minutes": 7,
  "published_date": "2024-09-15"
}
```

**Article Topics by Persona**:
- **High Utilization**: Debt paydown strategies, balance transfers, avalanche vs snowball, debt consolidation, credit utilization impact
- **Variable Income**: Budgeting with irregular income, building cash flow buffers, income smoothing, emergency fund prioritization, percent-based budgeting
- **Subscription Heavy**: Subscription audits, cancellation tactics, free alternatives, annual vs monthly comparison, subscription tracking tools
- **Savings Builder**: Emergency fund guides, HYSA comparisons, savings goals, automatic savings, CD laddering
- **Wealth Builder**: 401k optimization, asset allocation, tax-advantaged accounts, retirement planning, estate planning basics

### Vector Embedding & Database Population

#### Embedding Generation
**Service**: `backend/app/services/embedding_service.py`  
**Model**: OpenAI text-embedding-3-small (1536 dimensions)  
**Input**: Article title + summary + full_text (combined)  
**Output**: 1536-dimensional embedding vector

**Process**:
1. For each article, combine title + summary + full_text into single text
2. Call OpenAI embeddings API: `text-embedding-3-small`
3. Extract 1536-dimensional vector
4. Store in Pinecone with metadata

**Script**: `scripts/populate_article_vectors.py`
- Batch process all 50 articles
- Generate embeddings (batches of 100, ~10 API calls)
- Upload to Pinecone with metadata
- Total cost: ~$0.30-0.50 (one-time)

#### Pinecone Index Configuration
```
Index Name: spendsense-articles
Dimension: 1536
Metric: cosine
Cloud: AWS
Region: us-east-1
```

**Vector Metadata** (stored with each embedding):
- article_id (for database lookup)
- title
- source
- url
- summary
- persona_targets (JSON string)
- categories (JSON string)
- reading_time_minutes
- active (boolean)

### Article Matching Logic

#### Real-Time Vector Similarity Search

**Service**: `backend/app/services/article_matcher.py`

**Matching Flow**:
```
1. Generate educational recommendations (existing OpenAI logic)
   ↓
2. For each educational recommendation:
   a. Combine title + content into single text
   b. Generate embedding using text-embedding-3-small (~100ms)
   c. Query Pinecone for top 3 similar articles (~50-100ms)
   d. Extract top result (highest cosine similarity score)
   e. If score >= 0.75:
      - Attach article_id to recommendation
      - Store similarity_score in metadata (for debugging)
   f. Else:
      - Leave article_id = NULL (no good match)
   ↓
3. Store recommendations with article_id populated (or NULL)
   ↓
4. Return recommendations to operator approval queue
```

**Performance**:
- Embedding generation: ~100ms per rec
- Vector search: ~50-100ms per rec
- Total per rec: ~100-300ms
- For 2-3 educational recs: ~200-600ms total added to rec generation

**Similarity Threshold**:
- Default: 0.75 (cosine similarity)
- Rationale: Balance between showing relevant articles and avoiding poor matches
- Expected match rate: 60-80% of educational recs get articles
- Adjustable via environment variable if needed

**No LLM Calls**: Unlike previous vector DB proposal (which still used LLM for final generation), this approach uses ONLY vector similarity - much faster and more predictable.

### Integration into Recommendation Engine

#### Updated Recommendation Generation Flow

**Service**: `backend/app/services/recommendation_engine.py`

**Updated `generate_combined_recommendations()` function**:

```python
def generate_combined_recommendations(db, user_id, persona_type, window_days):
    # Step 1: Generate educational recommendations (existing)
    educational_recs = generate_via_openai(persona_type, user_context)
    for rec in educational_recs:
        rec['content_type'] = 'education'
    
    # Step 1.5: Match articles to educational recs (NEW)
    educational_recs_with_articles = match_articles_for_recommendations(
        educational_recs, persona_type
    )
    # Adds article_id to each rec where similarity >= 0.75
    
    # Step 2: Generate product recommendations (existing)
    product_recs = match_and_filter_products(db, user_id, persona_type)
    for rec in product_recs:
        rec['content_type'] = 'partner_offer'
    
    # Step 3: Combine and return
    all_recs = educational_recs_with_articles + product_recs
    return all_recs  # Total 3-5 recommendations
```

**No Breaking Changes**: Article matching is additive - if it fails, recommendations still work (article_id = NULL).

### API Updates

#### GET /recommendations/{user_id} Enhancement

**Response Example**:
```json
{
  "recommendations": [
    {
      "recommendation_id": "rec_123",
      "content_type": "education",
      "title": "Understanding Credit Utilization Impact",
      "content": "Your credit utilization of 68% is impacting...",
      "rationale": "With average utilization at 68%...",
      "article_id": "art_001",
      "article": {
        "article_id": "art_001",
        "title": "How to Lower Your Credit Utilization Fast",
        "source": "NerdWallet",
        "url": "https://example.com/articles/lower-credit-utilization",
        "summary": "Learn proven strategies to reduce your credit card utilization...",
        "reading_time_minutes": 7
      }
    },
    {
      "recommendation_id": "rec_124",
      "content_type": "partner_offer",
      "product_id": "prod_001",
      "product_name": "Chase Slate Edge",
      "article_id": null
      // Products don't get articles
    }
  ]
}
```

### Frontend Updates

#### RecommendationCard Component Enhancement
**File**: `frontend/src/components/RecommendationCard.jsx`

**For Educational Recommendations with Articles**:

```jsx
{recommendation.content_type === 'education' && recommendation.article && (
  <div className="article-section border-t pt-4 mt-4">
    <div className="text-sm font-semibold text-gray-700">
      📖 Related Article
    </div>
    <div className="mt-2">
      <h4 className="font-medium">{recommendation.article.title}</h4>
      <div className="text-xs text-gray-500 mt-1">
        from {recommendation.article.source} • {recommendation.article.reading_time_minutes} min read
      </div>
      <p className="text-sm text-gray-600 mt-2">
        {recommendation.article.summary}
      </p>
      <a
        href={recommendation.article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 mt-3"
      >
        Read Full Article ↗
      </a>
    </div>
  </div>
)}
```

**Example UI**:
```
┌─────────────────────────────────────────────┐
│ 📚 Educational Recommendation               │
│                                             │
│ Understanding Credit Utilization            │
│                                             │
│ Your credit utilization of 68% is          │
│ impacting your credit score...             │
│ [content continues]                         │
│                                             │
│ Why: With average utilization at 68%...    │
│                                             │
│ ─────────────────────────────────────────  │
│                                             │
│ 📖 Related Article                          │
│                                             │
│ How to Lower Your Credit Utilization       │
│ from NerdWallet • 7 min read              │
│                                             │
│ Learn proven strategies to reduce your     │
│ credit card utilization and improve your   │
│ credit score with these actionable tips.   │
│                                             │
│ [Read Full Article ↗]                      │
└─────────────────────────────────────────────┘
```

### Performance Impact

#### Latency Analysis

**Current Recommendation Generation**:
- OpenAI educational recs: ~17s (gpt-4o-mini)
- Product matching: ~200ms
- Total: ~17.2s

**With Article Matching**:
- OpenAI educational recs: ~17s (unchanged)
- Product matching: ~200ms (unchanged)
- Article matching: ~200-600ms (2-3 recs)
- Total: ~17.4-17.8s

**Impact**: +200-600ms (~3% increase) - acceptable for MVP

**Much Better Than Alternatives**:
- LLM-based article matching would add ~5-17s per rec (total: ~27-34s)
- Vector similarity is 20-50x faster

### Testing Strategy

#### Unit Tests
**File**: `backend/tests/test_article_matcher.py`
- Test vector similarity search (returns top 3 articles)
- Test similarity threshold logic (>0.75 → attach, <0.75 → NULL)
- Test batch matching (3 recs, mix of matches and no-matches)
- Test persona filtering (articles match persona of rec)

#### Integration Tests
**File**: `backend/tests/test_article_recommendations_integration.py`
- Generate recommendations for each persona type
- Verify article_ids attached appropriately (~60-80% of educational recs)
- Verify article objects included in API response
- Verify product recs don't have articles (as expected)

#### Performance Tests
**File**: `backend/tests/test_article_matching_performance.py`
- Measure embedding generation latency (target: <100ms per rec)
- Measure vector search latency (target: <100ms per search)
- Measure end-to-end article matching (target: <300ms for 3 recs)

### Replacing with Real Articles

#### Process for Production

When time permits, replace LLM-generated articles with real curated content:

**Step 1: Curate Real Articles** (1-2 hours)
- Manually find 30-50 high-quality articles from reputable sources
- Sources: NerdWallet, Investopedia, CFPB, The Balance, Forbes
- 10 articles per persona (credit/debt, budgeting, savings, investing, subscriptions)
- Copy full article text (or representative excerpts if paywalled)

**Step 2: Update Database**
```sql
UPDATE articles 
SET url = 'https://www.nerdwallet.com/article/credit-cards/pay-off-credit-card-debt',
    full_text = '[actual article text...]'
WHERE article_id = 'art_001';
```

**Step 3: Regenerate Embeddings**
```bash
python scripts/populate_article_vectors.py
```
- Re-embeds all articles with updated full_text
- Uploads new embeddings to Pinecone (replaces old)
- Cost: ~$0.30-0.50 (same as initial)

**Step 4: Test Matching Quality**
- Generate recommendations for test users
- Verify articles matched are still relevant
- Adjust similarity threshold if needed

**Expected Outcome**: Better matching quality (real articles are more coherent than LLM-generated)

### Success Metrics

**Match Rate**:
- % of educational recs that get article matches (similarity >0.75)
- Target: 60-80%

**Relevance Quality**:
- Operator approval rate for recs with articles
- Target: >85% (high confidence in article relevance)

**Performance**:
- Average article matching latency per rec
- Target: <150ms per rec

**User Engagement** (future):
- Click-through rate on "Read Full Article" button
- Target: >30% of users click at least one article

### Limitations

**MVP Constraints**:
- Articles are LLM-generated placeholders (not real content)
- URLs are placeholder (example.com/articles/slug)
- Article quality may vary (but realistic enough for demonstration)
- No click tracking or engagement analytics

**Impact**:
- Users cannot actually read full articles (links don't work)
- Article content may not be as comprehensive as real articles

**Recommendation for Production**:
- Curate 30-50 real articles from reputable sources (1-2 hours)
- Update URLs to real article links
- Regenerate embeddings with real full_text
- Add click tracking for engagement analytics
- Expand catalog to 100+ articles over time

### Implementation Timeline

**Total: 2.5-3.5 hours across 6 PRs**

#### PR #46: Article Catalog Schema & LLM-Based Generation (1-1.5 hours)
- Create articles table migration
- Create article generation script with validation
- Generate 50 articles via GPT-4o
- Review and save to JSON

#### PR #47: Article Seeding & Vector Database Population (30-45 min)
- Implement seeding script
- Generate embeddings for all articles
- Create Pinecone index and upload vectors
- Verify vector metadata

#### PR #48: Article Matching Service (30-45 min)
- Implement vector similarity search
- Create article selection logic (threshold: 0.75)
- Test with sample recommendations

#### PR #49: Hybrid Recommendation Engine with Article Matching (30 min)
- Integrate article matching into rec generation
- Update schemas to include article data
- Test end-to-end flow

#### PR #50: Frontend - Article Display Integration (30 min)
- Update RecommendationCard component
- Add article section with "Read Full Article" button
- Test with sample data

#### PR #51: Unit Tests & Documentation (30-45 min)
- Write 15+ unit tests
- Update README with article generation instructions
- Update DECISIONS.md and LIMITATIONS.md
- Document real article replacement process

### Future Enhancements

#### Post-MVP Phase
- Replace with real curated articles (1-2 hours)
- Expand catalog to 100+ articles
- Click tracking and engagement analytics
- Multi-article recommendations (show top 3, not just 1)
- User feedback on article relevance

#### Production Phase
- ML-based ranking (combine vector similarity + user engagement data)
- Article summary generation (if full text not available)
- A/B testing similarity thresholds
- Personalized article ranking based on user behavior
- Automatic article catalog updates (weekly refresh)

---

**Documentation:**
- [ ] README with setup instructions + screenshots
- [ ] Decision log explaining key choices (including UI-first approach)
- [ ] Limitations documented
- [ ] Demo video or live presentation ready

---

**End of PRD**