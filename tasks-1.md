# SpendSense Tasks - Part 1: Project Setup & Data Foundation

## PR #1: Project Initialization & Workspace Setup

### Backend Setup
- [x] 1. Create root project directory `spendsense/`
- [x] 2. Create `backend/` directory
- [x] 3. Initialize Python virtual environment in backend/
- [x] 4. Create `backend/requirements.txt` with initial dependencies:
   - fastapi==0.104.1
   - uvicorn[standard]==0.24.0
   - sqlalchemy==2.0.23
   - pydantic==2.5.0
   - python-dotenv==1.0.0
- [x] 5. Create `backend/.env.example` file with placeholder environment variables
- [x] 6. Create `backend/.gitignore` for Python projects
- [x] 7. Install dependencies: `pip install -r requirements.txt`

### Backend Project Structure
- [x] 8. Create `backend/app/` directory
- [x] 9. Create `backend/app/__init__.py`
- [x] 10. Create `backend/app/main.py` (empty FastAPI app skeleton)
- [x] 11. Create `backend/app/database.py` (SQLAlchemy setup placeholder)
- [x] 12. Create `backend/app/models.py` (empty models file)
- [x] 13. Create `backend/app/schemas.py` (empty schemas file)
- [x] 14. Create `backend/app/routers/` directory with `__init__.py`
- [x] 15. Create `backend/app/services/` directory with `__init__.py`
- [x] 16. Create `backend/app/utils/` directory with `__init__.py`
- [x] 17. Create `backend/tests/` directory with `__init__.py`

### Frontend Setup
- [x] 18. Create `frontend/` directory at root level
- [x] 19. Run `npm create vite@latest frontend -- --template react`
- [x] 20. Navigate to frontend and run `npm install`
- [x] 21. Initialize Shadcn/ui: `npx shadcn@latest init` (Note: `shadcn-ui` is deprecated, use `shadcn` instead)
- [x] 22. Install React Router: `npm install react-router-dom`
- [x] 23. Install Axios: `npm install axios`
- [x] 24. Install Recharts: `npm install recharts`
- [x] 25. Add Shadcn components: `npx shadcn@latest add button card table dialog badge switch` (Note: `shadcn-ui` is deprecated, use `shadcn` instead)

### Frontend Project Structure
- [x] 26. Create `frontend/src/pages/` directory
- [x] 27. Create `frontend/src/components/` directory
- [x] 28. Create `frontend/src/lib/` directory
- [x] 29. Create `frontend/src/lib/api.js` (Axios instance with base URL)
- [x] 30. Update `frontend/.gitignore` to exclude node_modules and build files

### Data Directory
- [x] 31. Create `data/` directory at root level
- [x] 32. Create `data/.gitkeep` to track empty directory

### Scripts Directory
- [x] 33. Create `scripts/` directory at root level
- [x] 34. Create `scripts/__init__.py`

### Documentation
- [x] 35. Create root `README.md` with project title and basic description
- [x] 36. Create `docs/` directory
- [x] 37. Create `docs/DECISIONS.md` placeholder
- [x] 38. Create `docs/LIMITATIONS.md` placeholder

### Git Repository
- [x] 39. Initialize git repository: `git init`
- [x] 40. Create root `.gitignore` combining Python and Node patterns
- [x] 41. Create initial commit with project structure

---

## PR #2: Synthetic Data Generation Script

### Dependencies
- [x] 1. Add `faker==20.1.0` to `backend/requirements.txt`
- [x] 2. Install faker: `pip install faker`

### Script Creation
- [x] 3. Create `scripts/generate_synthetic_data.py`
- [x] 4. Import required libraries (Faker, json, random, datetime, uuid)
- [x] 5. Set random seed for reproducibility: `random.seed(42)`

### User Generation Function
- [x] 6. Create function `generate_users(count=75)` that returns list of user dicts
- [x] 7. Generate 71 customers (95%) and 4 operators (5%)
- [x] 8. For each user, generate:
   - user_id (format: usr_{uuid})
   - full_name (Faker)
   - email (Faker, ensure unique)
   - created_at (random date in last 6 months)
   - consent_status (30% True, 70% False)
   - consent_granted_at (if consent_status=True, random recent date)
   - user_type ('customer' or 'operator')
- [x] 9. Return list of user dictionaries

### Account Generation Function
- [x] 10. Create function `generate_accounts(users)` that returns list of account dicts
- [x] 11. For each user, generate 2-4 accounts with varied types:
   - 1-2 checking accounts (100% of users)
   - 0-1 savings account (60% probability)
   - 0-2 credit cards (80% probability, varied limits $1k-$50k)
   - 0-1 investment account (30% probability, higher for high-income users)
- [x] 12. For each account generate:
   - account_id (format: acc_{uuid})
   - user_id (reference to user)
   - type (checking, savings, credit card, brokerage, 401k, ira)
   - subtype (specific account subtype)
   - balance_available (realistic based on account type)
   - balance_current (realistic based on account type)
   - balance_limit (for credit cards, $1k-$50k range)
   - iso_currency_code ('USD')
   - holder_category ('personal')
   - created_at
- [x] 13. Return list of account dictionaries

### Transaction Generation Function
- [x] 14. Create function `generate_transactions(users, accounts)` that returns list of transaction dicts
- [x] 15. Define merchant categories with sample merchants:
   - Groceries: Whole Foods, Trader Joe's, Safeway, Kroger
   - Subscriptions: Netflix, Spotify, Adobe, GitHub, Peloton, Apple, Amazon Prime
   - Restaurants: Chipotle, Starbucks, McDonald's, Local Restaurant
   - Gas: Shell, Chevron, BP
   - Utilities: PG&E, AT&T, Comcast
   - Shopping: Amazon, Target, Walmart, Best Buy
   - Payroll: "PAYROLL DEPOSIT - Employer Name"
- [x] 16. For each user, generate 150-300 transactions over 180-day window
- [x] 17. Ensure transaction patterns align with intended personas:
   - Some users: high credit card transactions with high balances
   - Some users: recurring subscription merchants (3+ occurrences, ~30 day intervals)
   - Some users: regular savings deposits ($200-$500/month)
   - Some users: irregular payroll deposits (variable income)
   - Some users: regular biweekly payroll deposits ($2k-$6k range)
- [x] 18. For each transaction generate:
   - transaction_id (format: txn_{uuid})
   - account_id (reference to account)
   - user_id (reference to user)
   - date (date within 180-day window)
   - amount (realistic for category, negative for expenses, positive for income)
   - merchant_name (from category lists)
   - merchant_entity_id (format: merchant_{uuid})
   - payment_channel ('online', 'in store', 'ACH')
   - category_primary (groceries, subscriptions, income, etc.)
   - category_detailed (more specific category)
   - pending (False for most, True for 5%)
   - created_at
- [x] 19. Return list of transaction dictionaries

### Liability Generation Function
- [x] 20. Create function `generate_liabilities(users, accounts)` that returns list of liability dicts
- [x] 21. For each credit card account, generate liability record:
   - liability_id (format: liab_{uuid})
   - account_id (reference to credit card account)
   - user_id (reference to user)
   - liability_type ('credit_card')
   - apr_purchase (15%-25% range)
   - apr_balance_transfer (0%-21% range)
   - apr_cash_advance (25%-30% range)
   - minimum_payment_amount (2-3% of balance)
   - last_payment_amount (varied: some minimum-only, some full balance)
   - is_overdue (True for 10% of accounts)
   - next_payment_due_date (random future date)
   - last_statement_balance (close to current balance)
   - created_at
- [x] 22. Ensure variety in credit behaviors:
   - 20% of users: high utilization (>50%)
   - 30% of users: medium utilization (30-50%)
   - 50% of users: low utilization (<30%)
- [x] 23. Return list of liability dictionaries

### Main Execution Function
- [x] 24. Create `main()` function that orchestrates data generation
- [x] 25. Generate 75 users
- [x] 26. Generate accounts for all users
- [x] 27. Generate transactions for all users/accounts
- [x] 28. Generate liabilities for credit card accounts
- [x] 29. Print summary statistics:
   - Total users (breakdown by type)
   - Total accounts (breakdown by type)
   - Total transactions
   - Total liabilities
   - Users with consent=True
- [x] 30. Write data to JSON files:
   - `data/synthetic_users.json`
   - `data/synthetic_accounts.json`
   - `data/synthetic_transactions.json`
   - `data/synthetic_liabilities.json`
- [x] 31. Use pretty print (indent=2) for readability

### Testing & Validation
- [x] 32. Add `if __name__ == "__main__":` block to call main()
- [x] 33. Run script: `python scripts/generate_synthetic_data.py`
- [x] 34. Verify all 4 JSON files created in data/ directory
- [x] 35. Verify file sizes (transactions.json should be largest, ~5-10MB)
- [x] 36. Spot-check JSON files for data quality:
   - Valid dates
   - Realistic amounts
   - Proper ID formats
   - Correct consent distribution (30% True)
- [x] 37. Verify persona signal distribution in data:
   - Multiple users with 3+ recurring merchants
   - Multiple users with positive savings deposits
   - Multiple users with high credit utilization
   - Multiple users with irregular income patterns
- [x] 38. Document any data generation assumptions in comments

---

## PR #3: Database Schema & SQLAlchemy Models

### Database Configuration
1. Create `backend/app/database.py` with SQLAlchemy setup
2. Define `SQLALCHEMY_DATABASE_URL = "sqlite:///./spendsense.db"`
3. Create SQLAlchemy engine with `create_engine()`
4. Create `SessionLocal` with `sessionmaker()`
5. Create `Base = declarative_base()`
6. Create `get_db()` dependency function for FastAPI
7. Create `init_db()` function to create all tables

### Users Model
8. Create `User` model in `backend/app/models.py`
9. Add fields:
   - user_id: String, primary key
   - full_name: String, not nullable
   - email: String, unique, not nullable
   - created_at: DateTime, default=now
   - consent_status: Boolean, default=False
   - consent_granted_at: DateTime, nullable
   - consent_revoked_at: DateTime, nullable
   - user_type: String, check constraint (customer/operator), default='customer'
10. Add __repr__ method for debugging

### Accounts Model
11. Create `Account` model in `backend/app/models.py`
12. Add fields:
    - account_id: String, primary key
    - user_id: String, foreign key to users.user_id
    - type: String, not nullable
    - subtype: String, nullable
    - balance_available: Float, nullable
    - balance_current: Float, nullable
    - balance_limit: Float, nullable
    - iso_currency_code: String, default='USD'
    - holder_category: String, nullable
    - created_at: DateTime, default=now
13. Add relationship to User model
14. Add __repr__ method

### Transactions Model
15. Create `Transaction` model in `backend/app/models.py`
16. Add fields:
    - transaction_id: String, primary key
    - account_id: String, foreign key to accounts.account_id
    - user_id: String, foreign key to users.user_id
    - date: Date, not nullable
    - amount: Float, not nullable
    - merchant_name: String, nullable
    - merchant_entity_id: String, nullable
    - payment_channel: String, nullable
    - category_primary: String, nullable
    - category_detailed: String, nullable
    - pending: Boolean, default=False
    - created_at: DateTime, default=now
17. Add indexes:
    - Index on (user_id, date)
    - Index on merchant_name
18. Add relationships to User and Account
19. Add __repr__ method

### Liabilities Model
20. Create `Liability` model in `backend/app/models.py`
21. Add fields:
    - liability_id: String, primary key
    - account_id: String, foreign key to accounts.account_id
    - user_id: String, foreign key to users.user_id
    - liability_type: String, check constraint
    - apr_purchase: Float, nullable
    - apr_balance_transfer: Float, nullable
    - apr_cash_advance: Float, nullable
    - minimum_payment_amount: Float, nullable
    - last_payment_amount: Float, nullable
    - is_overdue: Boolean, default=False
    - next_payment_due_date: Date, nullable
    - last_statement_balance: Float, nullable
    - interest_rate: Float, nullable
    - created_at: DateTime, default=now
22. Add relationships to User and Account
23. Add __repr__ method

### User Features Model
24. Create `UserFeature` model in `backend/app/models.py`
25. Add fields:
    - feature_id: Integer, primary key, autoincrement
    - user_id: String, foreign key to users.user_id
    - window_days: Integer, not nullable (30 or 180)
    - computed_at: DateTime, default=now
    - recurring_merchants: Integer, default=0
    - monthly_recurring_spend: Float, default=0
    - subscription_spend_share: Float, default=0
    - net_savings_inflow: Float, default=0
    - savings_growth_rate: Float, default=0
    - emergency_fund_months: Float, default=0
    - avg_utilization: Float, default=0
    - max_utilization: Float, default=0
    - utilization_30_flag: Boolean, default=False
    - utilization_50_flag: Boolean, default=False
    - utilization_80_flag: Boolean, default=False
    - minimum_payment_only_flag: Boolean, default=False
    - interest_charges_present: Boolean, default=False
    - any_overdue: Boolean, default=False
    - payroll_detected: Boolean, default=False
    - median_pay_gap_days: Integer, nullable
    - income_variability: Float, nullable
    - cash_flow_buffer_months: Float, default=0
    - avg_monthly_income: Float, default=0
    - investment_account_detected: Boolean, default=False
26. Add unique constraint on (user_id, window_days)
27. Add index on user_id
28. Add relationship to User
29. Add __repr__ method

### Personas Model
30. Create `Persona` model in `backend/app/models.py`
31. Add fields:
    - persona_id: Integer, primary key, autoincrement
    - user_id: String, foreign key to users.user_id
    - window_days: Integer, not nullable
    - persona_type: String, check constraint (5 persona types)
    - confidence_score: Float, default=1.0
    - assigned_at: DateTime, default=now
    - reasoning: Text (JSON), nullable
32. Add unique constraint on (user_id, window_days)
33. Add index on user_id
34. Add relationship to User
35. Add __repr__ method

### Recommendations Model
36. Create `Recommendation` model in `backend/app/models.py`
37. Add fields:
    - recommendation_id: String, primary key
    - user_id: String, foreign key to users.user_id
    - persona_type: String, not nullable
    - window_days: Integer, not nullable
    - content_type: String, check constraint (education/partner_offer)
    - title: String, not nullable
    - content: Text, not nullable
    - rationale: Text, not nullable
    - status: String, check constraint (pending_approval/approved/overridden/rejected), default='pending_approval'
    - approved_by: String, nullable
    - approved_at: DateTime, nullable
    - override_reason: Text, nullable
    - original_content: Text (JSON), nullable
    - metadata: Text (JSON), nullable
    - generated_at: DateTime, default=now
    - generation_time_ms: Integer, nullable
    - expires_at: DateTime, nullable
38. Add indexes:
    - Index on user_id
    - Index on status
39. Add relationship to User
40. Add __repr__ method

### Evaluation Metrics Model
41. Create `EvaluationMetric` model in `backend/app/models.py`
42. Add fields:
    - metric_id: Integer, primary key, autoincrement
    - run_id: String, not nullable
    - timestamp: DateTime, default=now
    - total_users: Integer, nullable
    - users_with_persona: Integer, nullable
    - users_with_behaviors: Integer, nullable
    - coverage_percentage: Float, nullable
    - total_recommendations: Integer, nullable
    - recommendations_with_rationale: Integer, nullable
    - explainability_percentage: Float, nullable
    - avg_recommendation_latency_ms: Float, nullable
    - p95_recommendation_latency_ms: Float, nullable
    - recommendations_with_traces: Integer, nullable
    - auditability_percentage: Float, nullable
    - details: Text (JSON), nullable
43. Add __repr__ method

### Consent Log Model
44. Create `ConsentLog` model in `backend/app/models.py`
45. Add fields:
    - log_id: Integer, primary key, autoincrement
    - user_id: String, foreign key to users.user_id
    - action: String, check constraint (granted/revoked)
    - timestamp: DateTime, default=now
    - ip_address: String, nullable
    - user_agent: String, nullable
46. Add index on user_id
47. Add relationship to User
48. Add __repr__ method

### Operator Actions Model
49. Create `OperatorAction` model in `backend/app/models.py`
50. Add fields:
    - action_id: Integer, primary key, autoincrement
    - operator_id: String, not nullable
    - action_type: String, check constraint (approve/reject/override)
    - recommendation_id: String, foreign key to recommendations.recommendation_id, nullable
    - user_id: String, foreign key to users.user_id
    - reason: Text, nullable
    - timestamp: DateTime, default=now
51. Add relationships to User and Recommendation
52. Add __repr__ method

### Database Initialization
53. Update `backend/app/main.py` to import Base and models
54. Add database initialization on startup (create all tables)
55. Test database creation: run `uvicorn app.main:app --reload`
56. Verify `spendsense.db` file created in backend/ directory
57. Use SQLite browser to inspect tables and schema
58. Verify all 10 tables created with correct columns and constraints

---