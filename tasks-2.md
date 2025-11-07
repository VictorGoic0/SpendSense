# SpendSense Tasks - Part 2: Database Models & Data Ingestion API

## PR #4: Pydantic Schemas for Data Validation

### User Schemas
- [x] 1. Create `backend/app/schemas.py`
- [x] 2. Import Pydantic BaseModel, Field, validator
- [x] 3. Create `UserBase` schema with core user fields
- [x] 4. Create `UserCreate` schema (extends UserBase) for POST requests
- [x] 5. Create `UserResponse` schema (extends UserBase) with all fields including IDs and timestamps
- [x] 6. Add Config class with `from_attributes = True` for ORM compatibility

### Account Schemas
- [x] 7. Create `AccountBase` schema with core account fields
- [x] 8. Create `AccountCreate` schema for account creation
- [x] 9. Create `AccountResponse` schema with all fields
- [x] 10. Add Config class for ORM compatibility

### Transaction Schemas
- [x] 11. Create `TransactionBase` schema with core transaction fields
- [x] 12. Create `TransactionCreate` schema for transaction creation
- [x] 13. Create `TransactionResponse` schema with all fields
- [x] 14. Add Config class for ORM compatibility

### Liability Schemas
- [x] 15. Create `LiabilityBase` schema with core liability fields
- [x] 16. Create `LiabilityCreate` schema for liability creation
- [x] 17. Create `LiabilityResponse` schema with all fields
- [x] 18. Add Config class for ORM compatibility

### Ingestion Schemas
- [x] 19. Create `IngestRequest` schema with fields:
    - users: List[UserCreate]
    - accounts: List[AccountCreate]
    - transactions: List[TransactionCreate]
    - liabilities: List[LiabilityCreate]
- [x] 20. Create `IngestResponse` schema with fields:
    - status: str
    - ingested: dict (counts per entity type)
    - duration_ms: int

### Feature Schemas
- [x] 21. Create `UserFeatureResponse` schema with all feature fields
- [x] 22. Add Config class for ORM compatibility

### Persona Schemas
- [x] 23. Create `PersonaResponse` schema with all persona fields
- [x] 24. Add Config class for ORM compatibility

### Recommendation Schemas
- [x] 25. Create `RecommendationBase` schema with core fields
- [x] 26. Create `RecommendationCreate` schema for creation
- [x] 27. Create `RecommendationResponse` schema with all fields including status
- [x] 28. Create `RecommendationApprove` schema with operator_id and notes
- [x] 29. Create `RecommendationOverride` schema with operator_id, new_title, new_content, reason
- [x] 30. Create `RecommendationReject` schema with operator_id and reason
- [x] 31. Add Config classes for ORM compatibility

---

## PR #5: Data Ingestion API Endpoint

### FastAPI App Setup
- [x] 1. Update `backend/app/main.py` to create FastAPI instance
- [x] 2. Add title, description, version to FastAPI app
- [x] 3. Add CORS middleware with allowed origins (include localhost:5173 for frontend)
- [x] 4. Configure CORS to allow credentials and all methods/headers
- [x] 5. Import database session dependency

### Ingest Router Creation
- [x] 6. Create `backend/app/routers/ingest.py`
- [x] 7. Create APIRouter instance with prefix="/ingest" and tags=["ingestion"]
- [x] 8. Import database models and schemas
- [x] 9. Import database session dependency

### Ingest Endpoint - Users
- [x] 10. Create POST endpoint `/` (full path: `/ingest`)
- [x] 11. Accept `IngestRequest` schema as request body
- [x] 12. Accept database session as dependency
- [x] 13. Start timer to track duration
- [x] 14. Process users list:
    - Loop through users in request
    - Create User model instances
    - Bulk insert using `db.bulk_save_objects()`
    - Commit transaction
    - Capture count of users inserted

### Ingest Endpoint - Accounts
- [x] 15. Process accounts list:
    - Loop through accounts in request
    - Create Account model instances
    - Bulk insert using `db.bulk_save_objects()`
    - Commit transaction
    - Capture count of accounts inserted

### Ingest Endpoint - Transactions
- [x] 16. Process transactions list (handle in batches for performance):
    - Split transactions into batches of 1000
    - For each batch:
      - Create Transaction model instances
      - Bulk insert using `db.bulk_save_objects()`
      - Commit transaction
    - Capture total count of transactions inserted

### Ingest Endpoint - Liabilities
- [x] 17. Process liabilities list:
    - Loop through liabilities in request
    - Create Liability model instances
    - Bulk insert using `db.bulk_save_objects()`
    - Commit transaction
    - Capture count of liabilities inserted

### Ingest Endpoint - Response
- [x] 18. Calculate duration in milliseconds
- [x] 19. Create response with:
    - status: "success"
    - ingested counts for each entity type
    - duration_ms
- [x] 20. Return IngestResponse
- [x] 21. Add error handling with try/except:
    - Rollback transaction on error
    - Return 500 error with error message

### Router Registration
- [x] 22. Import ingest router in `backend/app/main.py`
- [x] 23. Include router in FastAPI app: `app.include_router(ingest.router)`

### Testing Ingestion
- [x] 24. Start FastAPI server: `uvicorn app.main:app --reload`
- [x] 25. Create test script `scripts/test_ingest.py` to POST synthetic data
- [x] 26. Test with all 4 JSON files
- [x] 27. Verify successful response with correct counts
- [x] 28. Use SQLite browser to verify data in database:
    - Check users table has 75 records
    - Check accounts table populated
    - Check transactions table populated (15k+ records)
    - Check liabilities table populated
- [x] 29. Test idempotency: run ingestion twice, handle duplicate key errors gracefully
- [x] 30. Verify API accessible at `http://localhost:8000/docs` (Swagger UI)

---

## PR #6: Feature Detection Service - Subscription Signals

### Service File Creation
1. Create `backend/app/services/feature_detection.py`
2. Import required libraries: SQLAlchemy, datetime, collections
3. Import database models
4. Import database session

### Helper Functions
5. Create `get_transactions_in_window(db, user_id, window_days)` function:
   - Query transactions for user
   - Filter by date (last N days)
   - Order by date ascending
   - Return list of transactions
6. Create `get_accounts_by_type(db, user_id, account_types)` function:
   - Query accounts for user
   - Filter by account type (checking, savings, etc.)
   - Return list of accounts

### Subscription Detection - Merchant Grouping
7. Create `compute_subscription_signals(db, user_id, window_days)` function
8. Get all transactions in window for user
9. Group transactions by merchant_name using Counter/dict
10. For each merchant with ≥3 transactions:
    - Extract transaction dates
    - Sort dates chronologically
    - Calculate day gaps between consecutive transactions

### Subscription Detection - Recurring Pattern
11. Create `is_recurring_pattern(dates)` helper function:
    - Accept list of transaction dates
    - Calculate gaps between consecutive dates
    - Check if gaps are approximately 30 days (weekly: ~7, monthly: ~30, quarterly: ~90)
    - Allow ±5 day tolerance
    - Return True if pattern detected
12. Filter merchants to only those with recurring patterns

### Subscription Detection - Spend Calculation
13. Count total recurring merchants (≥3 occurrences with pattern)
14. Calculate monthly_recurring_spend:
    - Sum all amounts for recurring merchants
    - Divide by number of months in window
15. Calculate total_spend in window (sum all transaction amounts)
16. Calculate subscription_spend_share = recurring_spend / total_spend
17. Return dict with:
    - recurring_merchants (count)
    - monthly_recurring_spend (float)
    - subscription_spend_share (float, 0-1)

### Testing Subscription Detection
18. Create test function in `scripts/test_feature_detection.py`
19. Test with known users that have subscription patterns
20. Verify recurring merchants detected correctly
21. Verify spend calculations accurate
22. Log results for validation

---

## PR #7: Feature Detection Service - Savings Signals

### Savings Detection - Account Filtering
1. Add `compute_savings_signals(db, user_id, window_days)` function to feature_detection.py
2. Get savings-type accounts for user:
   - Account types: savings, money market, cash management, HSA
   - Use `get_accounts_by_type()` helper
3. If no savings accounts, return zero values for all metrics

### Savings Detection - Net Inflow Calculation
4. For each savings account:
   - Get all transactions in window
   - Separate deposits (amount > 0) and withdrawals (amount < 0)
   - Calculate net_inflow = sum(deposits) + sum(withdrawals)
5. Sum net_inflow across all savings accounts
6. Calculate monthly_net_inflow = net_inflow / (window_days / 30)

### Savings Detection - Growth Rate
7. For each savings account:
   - Get current balance from account record
   - Calculate balance at start of window:
     - Get balance_current
     - Subtract net_inflow during window
   - Calculate growth_rate = (current - start) / start (if start > 0)
8. Calculate average growth_rate across all savings accounts

### Savings Detection - Emergency Fund
9. Calculate total savings balance (sum across all savings accounts)
10. Get checking account transactions to estimate monthly expenses:
    - Filter to expense transactions (amount < 0)
    - Sum absolute values
    - Divide by number of months in window
11. Calculate emergency_fund_months = savings_balance / avg_monthly_expenses
12. Handle edge case: if expenses = 0, set emergency_fund_months = 0

### Savings Detection - Response
13. Return dict with:
    - net_savings_inflow (float)
    - savings_growth_rate (float, 0-1)
    - emergency_fund_months (float)
14. Add error handling for division by zero
15. Add logging for debugging

### Testing Savings Detection
16. Test with users who have positive savings patterns
17. Test with users who have no savings accounts
18. Verify growth rate calculations
19. Verify emergency fund calculations
20. Log results for validation
