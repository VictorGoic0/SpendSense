# SpendSense

**Personalized Financial Education Platform**

SpendSense transforms synthetic bank transaction data into actionable financial education through behavioral pattern detection, persona-based recommendations, and AI-generated content. The platform analyzes user spending patterns, assigns educational personas, and generates personalized financial recommendations with strict consent management and operator oversight workflows.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Project Setup](#project-setup)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Environment Configuration](#environment-configuration)
- [Tech Stack](#tech-stack)
  - [Backend](#backend)
  - [Frontend](#frontend)
  - [AI & Infrastructure](#ai--infrastructure)
- [API Routes](#api-routes)
  - [Root](#root)
  - [Ingestion](#ingestion)
  - [Features](#features)
  - [Profile](#profile)
  - [Users](#users)
  - [Operator](#operator)
  - [Personas](#personas)
  - [Recommendations](#recommendations)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Deployment](#deployment)

---

## Overview

SpendSense is a comprehensive financial education platform that:

- **Detects Financial Patterns**: Analyzes transaction data to identify behavioral patterns (subscriptions, credit utilization, savings habits, income variability)
- **Assigns Educational Personas**: Categorizes users into one of five personas (High Utilization, Variable Income, Subscription Heavy, Savings Builder, Wealth Builder) based on their financial behavior
- **Generates AI Recommendations**: Creates personalized financial education content using OpenAI GPT-4o-mini, tailored to each user's persona and financial situation
- **Manages Consent**: Implements strict consent management with audit trails
- **Operator Oversight**: Provides approval workflows for operators to review, approve, reject, or override AI-generated recommendations before they reach users

The platform is designed with explainability, responsible AI practices, and user privacy at its core.

---

## Key Features

- ✅ **Behavioral Feature Detection**: Computes 20+ financial signals from transaction data
- ✅ **Persona Assignment**: Automatic assignment to educational personas based on behavioral patterns
- ✅ **AI-Powered Recommendations**: GPT-4o-mini generates personalized financial education content
- ✅ **Consent Management**: Full consent tracking with grant/revoke capabilities and audit logs
- ✅ **Operator Workflows**: Approval, rejection, override, and bulk approval capabilities
- ✅ **Dual Window Analysis**: Supports both 30-day and 180-day analysis windows
- ✅ **Operator Dashboard**: Comprehensive metrics and user insights
- ✅ **Responsive UI**: Modern React frontend with Shadcn/ui components

---

## Project Setup

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: Latest stable version (check `frontend/package.json` for compatibility)
- **SQLite**: Included with Python (no separate installation needed)
- **OpenAI API Key**: Required for recommendation generation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Copy example environment file (if available)
# Create a .env file with:
# OPENAI_API_KEY=your_api_key_here
```

5. Initialize the database (runs automatically on startup):
```bash
# The database is initialized automatically when the server starts
```

6. Start the FastAPI server:

**Development (with auto-reload):**
```bash
uvicorn app.main:app --reload
```

**Production/Concurrent requests (with workers):**
```bash
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs` (Swagger UI)
- Alternative Docs: `http://localhost:8000/redoc`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173` (Vite default port)

### Environment Configuration

**Backend** (`.env` file in `backend/`):
```
OPENAI_API_KEY=your_openai_api_key_here
```

**Frontend**: No environment variables required for basic setup. API base URL is configured in `src/lib/api.js`.

---

## Tech Stack

### Backend

- **Framework**: FastAPI 0.104.1
- **Language**: Python 3.11+
- **Database**: SQLite (via SQLAlchemy 2.0.23)
- **ORM**: SQLAlchemy 2.0.23
- **Validation**: Pydantic 2.5.0
- **Server**: Uvicorn 0.24.0 (with standard extras)
- **AI Integration**: OpenAI SDK 2.7.1
- **Utilities**:
  - `python-dotenv` 1.0.0 (environment variable management)
  - `faker` 20.1.0 (synthetic data generation)
  - `requests` 2.31.0 (HTTP client for testing)

### Frontend

- **Framework**: React 18.3.1
- **Build Tool**: Vite 7.1.7
- **Routing**: React Router DOM 7.9.5
- **UI Components**: 
  - Shadcn/ui (Radix UI primitives)
  - `@radix-ui/react-dialog` 1.1.15
  - `@radix-ui/react-slot` 1.2.4
  - `@radix-ui/react-switch` 1.2.6
- **Styling**: 
  - Tailwind CSS 3.4.17
  - `tailwindcss-animate` 1.0.7
  - `tailwind-merge` 3.3.1
  - `class-variance-authority` 0.7.1
  - `clsx` 2.1.1
- **HTTP Client**: Axios 1.13.2
- **Charts**: Recharts 3.3.0
- **Icons**: Lucide React 0.552.0
- **Development Tools**:
  - ESLint 9.36.0
  - PostCSS 8.4.47
  - Autoprefixer 10.4.20

### AI & Infrastructure

- **AI Model**: OpenAI GPT-4o-mini
- **Deployment Target**: AWS Lambda, API Gateway, S3
- **Database**: SQLite (development), ready for PostgreSQL migration

---

## API Routes

All API routes are prefixed with their router prefix. The base URL is `http://localhost:8000` in development.

### Root

#### `GET /`
- **Description**: Root endpoint, returns API status
- **Response**: `{"message": "SpendSense API"}`

---

### Ingestion

#### `POST /ingest/`
- **Description**: Bulk ingest users, accounts, transactions, liabilities, and products
- **Request Body**: `IngestRequest` (users, accounts, transactions, liabilities, products arrays)
- **Response**: `IngestResponse` (status, ingested counts, duration_ms)
- **Tags**: `ingestion`
- **Processing Order**: Users → Accounts → Transactions → Liabilities → Products
- **Note**: Transactions are processed in batches of 1000 for performance

---

### Features

#### `POST /features/compute/{user_id}`
- **Description**: Compute all behavioral features for a user
- **Path Parameters**: 
  - `user_id` (string): User ID
- **Query Parameters**:
  - `window_days` (int, optional): Time window in days (default: 30, max: 365)
- **Response**: Dictionary with user_id, window_days, and features object
- **Tags**: `features`

---

### Profile

#### `GET /profile/{user_id}`
- **Description**: Get user profile with features and personas
- **Path Parameters**:
  - `user_id` (string): User ID
- **Query Parameters**:
  - `window` (int, optional): Window filter (30 or 180). If not provided, returns both.
- **Response**: Dictionary with user info, features (30d and/or 180d), and personas
- **Tags**: `profile`

---

### Users

#### `GET /users/`
- **Description**: Get list of users with pagination and filtering
- **Query Parameters**:
  - `limit` (int, optional): Number of users to return (default: 25, max: 100)
  - `offset` (int, optional): Number of users to skip (default: 0)
  - `user_type` (string, optional): Filter by user type (customer or operator)
  - `consent_status` (bool, optional): Filter by consent status
- **Response**: Dictionary with users list, total count, limit, and offset
- **Tags**: `users`

#### `GET /users/{user_id}`
- **Description**: Get a single user by ID with personas for both 30d and 180d windows
- **Path Parameters**:
  - `user_id` (string): User ID
- **Response**: Dictionary with user data and personas list
- **Tags**: `users`

---

### Operator

#### `GET /operator/dashboard`
- **Description**: Get operator dashboard metrics and statistics
- **Response**: Dictionary with:
  - `total_users`: Total number of users
  - `users_with_consent`: Number of users with consent_status=True
  - `persona_distribution`: Count of users per persona type (30d window)
  - `recommendations`: Count of recommendations per status
  - `metrics`: Performance metrics (avg_latency_ms)
- **Tags**: `operator`

#### `GET /operator/users/{user_id}/signals`
- **Description**: Get detailed signals for a user for operator view
- **Path Parameters**:
  - `user_id` (string): User ID
- **Response**: Dictionary with user info, 30d_signals, 180d_signals, and personas
- **Tags**: `operator`

---

### Personas

#### `POST /personas/{user_id}/assign`
- **Description**: Assign persona to a user based on computed features
- **Path Parameters**:
  - `user_id` (string): User ID
- **Query Parameters**:
  - `window_days` (int, optional): Time window in days (default: 30, max: 365)
- **Response**: `PersonaResponse` with assigned persona details
- **Tags**: `personas`

#### `GET /personas/{user_id}`
- **Description**: Get persona(s) for a user
- **Path Parameters**:
  - `user_id` (string): User ID
- **Query Parameters**:
  - `window` (int, optional): Window filter (30 or 180). If not provided, returns both.
- **Response**: List of `PersonaResponse` objects
- **Tags**: `personas`

---

### Recommendations

#### `POST /recommendations/generate/{user_id}`
- **Description**: Generate AI-powered financial recommendations for a user
- **Path Parameters**:
  - `user_id` (string): User ID
- **Query Parameters**:
  - `window_days` (int, optional): Time window in days (default: 30, max: 365)
  - `force_regenerate` (bool, optional): Force regeneration even if recommendations exist (default: false)
- **Response**: Dictionary with user_id, persona, recommendations list, and generation_time_ms
- **Tags**: `recommendations`

#### `GET /recommendations/{user_id}`
- **Description**: Get recommendations for a user
- **Path Parameters**:
  - `user_id` (string): User ID
- **Query Parameters**:
  - `status` (string, optional): Filter by status (pending_approval, approved, overridden, rejected)
  - `window_days` (int, optional): Filter by window_days (default: return all)
- **Response**: Dictionary with recommendations list and total count
- **Tags**: `recommendations`

#### `POST /recommendations/{recommendation_id}/approve`
- **Description**: Approve a recommendation
- **Path Parameters**:
  - `recommendation_id` (string): Recommendation ID
- **Request Body**: `RecommendationApprove` (operator_id, notes optional)
- **Response**: Updated recommendation object
- **Tags**: `recommendations`

#### `POST /recommendations/{recommendation_id}/override`
- **Description**: Override a recommendation with new content
- **Path Parameters**:
  - `recommendation_id` (string): Recommendation ID
- **Request Body**: `RecommendationOverride` (operator_id, new_title optional, new_content optional, reason required)
- **Response**: Updated recommendation with original_content and override_reason
- **Tags**: `recommendations`

#### `POST /recommendations/{recommendation_id}/reject`
- **Description**: Reject a recommendation
- **Path Parameters**:
  - `recommendation_id` (string): Recommendation ID
- **Request Body**: `RecommendationReject` (operator_id, reason required)
- **Response**: Updated recommendation object
- **Tags**: `recommendations`

#### `POST /recommendations/bulk-approve`
- **Description**: Bulk approve multiple recommendations
- **Request Body**: `BulkApproveRequest` (operator_id, recommendation_ids array)
- **Response**: `BulkApproveResponse` (approved count, failed count, errors list)
- **Tags**: `recommendations`

---

## Project Structure

```
SpendSense/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI app initialization
│   │   ├── database.py     # Database connection and initialization
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── routers/         # API route handlers
│   │   │   ├── ingest.py
│   │   │   ├── features.py
│   │   │   ├── profile.py
│   │   │   ├── users.py
│   │   │   ├── operator.py
│   │   │   ├── personas.py
│   │   │   └── recommendations.py
│   │   ├── services/        # Business logic services
│   │   │   ├── feature_detection.py
│   │   │   ├── persona_assignment.py
│   │   │   ├── recommendation_engine.py
│   │   │   └── guardrails.py
│   │   ├── prompts/         # Persona-specific prompt templates
│   │   └── utils/            # Utility functions
│   ├── requirements.txt      # Python dependencies
│   ├── venv/                 # Virtual environment (gitignored)
│   └── spendsense.db        # SQLite database (gitignored)
│
├── frontend/                # React frontend application
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── ui/          # Shadcn/ui components
│   │   │   ├── Layout.jsx
│   │   │   ├── UserTable.jsx
│   │   │   └── ...
│   │   ├── pages/           # Page components
│   │   │   ├── OperatorDashboard.jsx
│   │   │   ├── OperatorUserList.jsx
│   │   │   ├── OperatorUserDetail.jsx
│   │   │   ├── OperatorApprovalQueue.jsx
│   │   │   └── UserDashboard.jsx
│   │   ├── lib/             # Utilities and API client
│   │   │   ├── api.js
│   │   │   ├── apiService.js
│   │   │   └── utils.js
│   │   ├── constants/       # Constants and enums
│   │   └── main.jsx         # React entry point
│   ├── package.json
│   └── vite.config.js
│
├── scripts/                 # Utility scripts
│   ├── generate_synthetic_data.py
│   ├── generate_product_catalog.py
│   ├── compute_all_features.py
│   ├── assign_all_personas.py
│   ├── test_*.py            # Test scripts for various endpoints
│   └── verify_ingest.py
│
├── data/                    # Synthetic data files
│   ├── synthetic_users.json
│   ├── synthetic_accounts.json
│   ├── synthetic_transactions.json
│   ├── synthetic_liabilities.json
│   └── product_catalog.json  # Generated product catalog
│
├── docs/                    # Documentation
│   ├── DECISIONS.md
│   └── LIMITATIONS.md
│
├── memory-bank/             # Project documentation and context
│   ├── projectbrief.md
│   ├── productContext.md
│   ├── systemPatterns.md
│   ├── techContext.md
│   ├── activeContext.md
│   └── progress.md
│
├── PRD.md                   # Product Requirements Document
├── README.md                # This file
└── architecture.mermaid     # System architecture diagram
```

---

## Development Workflow

### Backend Development

1. **Activate virtual environment**:
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

2. **Run server**:

**Development (with auto-reload):**
```bash
uvicorn app.main:app --reload
```

**Production/Concurrent requests (with workers):**
```bash
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

**Note**: Using `--workers 4` runs 4 separate processes, allowing concurrent request handling even with blocking operations (like recommendation generation). This prevents one long-running request from blocking others.

3. **Access API documentation**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend Development

1. **Start development server**:
```bash
cd frontend
npm run dev
```

2. **Build for production**:
```bash
npm run build
```

3. **Preview production build**:
```bash
npm run preview
```

### Data Ingestion Workflow

**First-Time Setup** (complete workflow):

1. **Start the backend server** (creates database tables automatically):
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload
```
The database tables are automatically created on server startup via `init_db()` in `backend/app/main.py`. This uses SQLAlchemy's `Base.metadata.create_all()` to create all tables from the model definitions.

2. **Generate synthetic user data** (creates JSON files):
```bash
# From project root
python scripts/generate_synthetic_data.py
```
This generates:
- `data/synthetic_users.json` (75 users: 71 customers, 4 operators)
- `data/synthetic_accounts.json` (2-4 accounts per user)
- `data/synthetic_transactions.json` (150-300 transactions per user)
- `data/synthetic_liabilities.json` (credit card liabilities)

3. **Ingest user data via API** (loads JSON into database):
```bash
# Make sure backend server is running first
python scripts/test_ingest.py
```
This POSTs the JSON data to `/ingest/` endpoint, which bulk inserts users, accounts, transactions, and liabilities into the database.

4. **Compute features for users**:
```bash
python scripts/compute_all_features.py
```
Computes behavioral features (subscriptions, savings, credit utilization, income patterns) for all users.

5. **Assign personas**:
```bash
python scripts/assign_all_personas.py
```
Assigns personas (high_utilization, variable_income, subscription_heavy, savings_builder, wealth_builder) to all users based on their features.

6. **Generate and ingest product catalog** (optional, for product recommendations):
```bash
# Step 6a: Generate product catalog JSON (requires OPENAI_API_KEY in .env)
python scripts/generate_product_catalog.py
```
This uses OpenAI GPT-4o to generate 20-25 realistic financial products matched to the 5 personas. The catalog is saved to `data/product_catalog.json`.

**Expected runtime**: ~30-60 seconds  
**Expected API cost**: ~$0.10-0.20

```bash
# Step 6b: Ingest products via API
# Make sure backend server is running first
python scripts/test_ingest_products.py
```
This POSTs the product catalog JSON to the `/ingest/` endpoint, which bulk inserts products into the database. Products are ingested the same way as all other data (users, accounts, transactions, liabilities) for consistency.

---

## Testing

### Backend Testing

Test scripts are available in the `scripts/` directory:

- `test_ingest.py` - Test data ingestion
- `test_feature_detection.py` - Test feature computation
- `test_persona_assignment.py` - Test persona assignment
- `test_get_recommendations.py` - Test recommendation retrieval
- `test_approve_recommendation.py` - Test recommendation approval
- `test_bulk_approve.py` - Test bulk approval
- `test_override_reject.py` - Test override and reject endpoints

Run any test script:
```bash
python scripts/test_<script_name>.py [arguments]
```

### API Testing

Use the Swagger UI at `http://localhost:8000/docs` for interactive API testing, or use the provided test scripts.

---

## Deployment

### AWS Lambda Deployment

The platform is designed for serverless deployment on AWS:

- **Backend**: FastAPI application packaged for Lambda
- **API Gateway**: REST API endpoint configuration
- **S3**: Static frontend hosting
- **Database**: SQLite for MVP (can be migrated to RDS/PostgreSQL)

### Environment Variables

Ensure the following environment variables are set in your deployment:

- `OPENAI_API_KEY`: Required for recommendation generation

### Database Migration

For production, consider migrating from SQLite to PostgreSQL or another production-grade database. The SQLAlchemy models are database-agnostic and can be easily adapted.

---

## Additional Resources

- **API Documentation**: Available at `/docs` when the server is running
- **Product Requirements**: See `PRD.md`
- **Architecture Diagram**: See `architecture.mermaid`
- **Project Context**: See `memory-bank/` directory for detailed project documentation

---

**Note**: This README is maintained as a reference document and is updated periodically as the project evolves. For the most current API documentation, refer to the Swagger UI at `/docs` when the server is running.
