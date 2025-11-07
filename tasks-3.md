# SpendSense Tasks - Part 3: Credit/Income Detection & Frontend Setup

## PR #8: Feature Detection Service - Credit Signals

### Credit Detection - Account & Liability Queries
- [x] 1. Add `compute_credit_signals(db, user_id, window_days)` function to feature_detection.py
- [x] 2. Query all credit card accounts for user
- [x] 3. Join accounts with liabilities table
- [x] 4. If no credit cards, return zero/false values for all metrics

### Credit Utilization Calculation
- [x] 5. For each credit card account:
   - Get balance_current and balance_limit from account
   - Calculate utilization = balance_current / balance_limit
   - Store utilization per card
- [x] 6. Calculate avg_utilization across all cards
- [x] 7. Calculate max_utilization (highest single card)
- [x] 8. Set flags:
   - utilization_30_flag = any card >= 0.30
   - utilization_50_flag = any card >= 0.50
   - utilization_80_flag = any card >= 0.80

### Minimum Payment Detection
- [x] 9. For each credit card liability:
   - Get minimum_payment_amount from liability
   - Get last_payment_amount from liability
   - Check if last_payment <= minimum_payment (with $5 tolerance)
   - Set flag if true
- [x] 10. Set minimum_payment_only_flag = True if any card matches pattern

### Interest & Overdue Detection
- [x] 11. Query transactions for interest charges:
    - Filter category_detailed='interest charge' or similar
    - Check if any exist in window
    - Set interest_charges_present flag
- [x] 12. Check liabilities for overdue status:
    - Query is_overdue field
    - Set any_overdue = True if any card overdue

### Credit Detection - Response
- [x] 13. Return dict with:
    - avg_utilization (float, 0-1)
    - max_utilization (float, 0-1)
    - utilization_30_flag (bool)
    - utilization_50_flag (bool)
    - utilization_80_flag (bool)
    - minimum_payment_only_flag (bool)
    - interest_charges_present (bool)
    - any_overdue (bool)
- [x] 14. Add error handling for division by zero (limit = 0)
- [x] 15. Add logging for debugging

### Testing Credit Detection
- [x] 16. Test with users having high utilization (>50%)
- [x] 17. Test with users having low utilization (<30%)
- [x] 18. Test with users making minimum payments only
- [x] 19. Test with users having overdue accounts
- [x] 20. Verify all flags set correctly
- [x] 21. Log results for validation

---

## PR #9: Feature Detection Service - Income Signals

### Income Detection - Payroll Identification
- [x] 1. Add `compute_income_signals(db, user_id, window_days)` function to feature_detection.py
- [x] 2. Get all transactions for user in window
- [x] 3. Filter for potential payroll deposits:
   - payment_channel = 'ACH'
   - amount > 0 (positive/deposit)
   - category_primary in ['income', 'payroll', 'salary']
   - OR merchant_name contains 'PAYROLL' or 'SALARY'
- [x] 4. Sort payroll transactions by date ascending

### Income Pattern Analysis
- [x] 5. Set payroll_detected = True if ≥2 payroll transactions found
- [x] 6. If no payroll detected, return default values
- [x] 7. Calculate gaps between consecutive payroll deposits:
   - Get list of dates
   - Calculate day differences between consecutive dates
   - Store list of gaps
- [x] 8. Calculate median_pay_gap_days from gaps list

### Income Variability Calculation
- [x] 9. Extract payroll amounts from transactions
- [x] 10. Calculate mean of payroll amounts
- [x] 11. Calculate standard deviation of payroll amounts
- [x] 12. Calculate income_variability = std_dev / mean (coefficient of variation)
- [x] 13. Handle edge case: if mean = 0 or only 1 payment, set variability = 0

### Cash Flow Buffer Calculation
- [x] 14. Get checking account(s) for user
- [x] 15. Calculate current checking balance (sum of balance_current)
- [x] 16. Estimate monthly expenses:
    - Get expense transactions (amount < 0) from checking
    - Sum absolute values
    - Divide by number of months in window
- [x] 17. Calculate cash_flow_buffer_months = checking_balance / avg_monthly_expenses
- [x] 18. Handle edge case: if expenses = 0, set buffer = 0

### Average Monthly Income
- [x] 19. Calculate avg_monthly_income:
    - Sum all payroll amounts in window
    - Divide by number of months in window
- [x] 20. Round to 2 decimal places

### Income Detection - Response
- [x] 21. Return dict with:
    - payroll_detected (bool)
    - median_pay_gap_days (int)
    - income_variability (float)
    - cash_flow_buffer_months (float)
    - avg_monthly_income (float)
- [x] 22. Add error handling for edge cases
- [x] 23. Add logging for debugging

### Investment Account Detection
- [x] 24. Add `detect_investment_accounts(db, user_id)` function
- [x] 25. Query accounts for user with types:
    - brokerage, 401k, ira, roth_ira, investment, pension
- [x] 26. Return True if any investment accounts exist, False otherwise

### Testing Income Detection
- [x] 27. Test with users having regular biweekly payroll
- [x] 28. Test with users having irregular income (freelancers)
- [x] 29. Test with users having high income variability
- [x] 30. Test with users having low cash flow buffer
- [x] 31. Verify median pay gap calculations
- [x] 32. Verify income variability calculations
- [x] 33. Log results for validation

---

## PR #10: Feature Computation Endpoint & Batch Script

### Feature Computation Function
- [x] 1. Create `compute_all_features(db, user_id, window_days)` function in feature_detection.py
- [x] 2. Call all 4 signal detection functions:
   - compute_subscription_signals()
   - compute_savings_signals()
   - compute_credit_signals()
   - compute_income_signals()
- [x] 3. Call detect_investment_accounts()
- [x] 4. Combine all results into single dict
- [x] 5. Create or update UserFeature record in database
- [x] 6. Return computed features

### Features Router Creation
- [x] 7. Create `backend/app/routers/features.py`
- [x] 8. Create APIRouter with prefix="/features"
- [x] 9. Create POST `/compute/{user_id}` endpoint:
   - Accept user_id as path parameter
   - Accept window_days as query parameter (default: 30)
   - Call compute_all_features()
   - Return computed features as JSON
- [x] 10. Add error handling for user not found

### Profile Endpoint
- [x] 11. Create `backend/app/routers/profile.py`
- [x] 12. Create APIRouter with prefix="/profile"
- [x] 13. Create GET `/{user_id}` endpoint:
    - Accept user_id as path parameter
    - Accept optional window query param
    - Query UserFeature records for user (30d and 180d)
    - Query Persona records for user
    - Return combined profile with features and personas
- [x] 14. Add error handling for user not found

### Router Registration
- [x] 15. Import features and profile routers in main.py
- [x] 16. Include both routers in FastAPI app

### Batch Computation Script
- [x] 17. Create `scripts/compute_all_features.py`
- [x] 18. Import database session and models
- [x] 19. Query all users from database
- [x] 20. For each user:
    - Compute features for 30-day window
    - Compute features for 180-day window
    - Print progress (every 10 users)
- [x] 21. Print summary statistics:
    - Total users processed
    - Average computation time per user
    - Total duration
- [x] 22. Add __main__ block to run script

### Testing Feature Computation
- [x] 23. Run batch script: `python scripts/compute_all_features.py`
- [x] 24. Verify user_features table populated for all users
- [x] 25. Verify both 30d and 180d records exist per user
- [x] 26. Spot-check feature values for accuracy
- [x] 27. Test API endpoint via Swagger UI or curl
- [x] 28. Verify profile endpoint returns combined data

---

## PR #11: Frontend - Project Setup & Basic Routing

### Frontend Configuration
1. Navigate to frontend/ directory
2. Update `vite.config.js` to set port 5173
3. Update `vite.config.js` to add proxy for API calls (http://localhost:8000)
4. Create `.env` file with `VITE_API_BASE_URL=http://localhost:8000`

### API Client Setup
5. Create `frontend/src/lib/api.js`
6. Import axios
7. Create axios instance with baseURL from env variable
8. Set default headers (Content-Type: application/json)
9. Add request interceptor for logging (optional)
10. Add response interceptor for error handling
11. Export axios instance as `api`

### API Service Functions
12. Create `frontend/src/lib/apiService.js`
13. Import api client
14. Create async function `getUsers(params)` - GET /users
15. Create async function `getUser(userId)` - GET /users/{userId}
16. Create async function `getUserProfile(userId, window)` - GET /profile/{userId}
17. Create async function `getRecommendations(userId, status)` - GET /recommendations/{userId}
18. Create async function `getOperatorDashboard()` - GET /operator/dashboard
19. Create async function `getOperatorUserSignals(userId)` - GET /operator/users/{userId}/signals
20. Create async function `getApprovalQueue(status)` - GET /operator/review
21. Create async function `approveRecommendation(recId, operatorId, notes)` - POST /recommendations/{recId}/approve
22. Create async function `bulkApprove(operatorId, recIds)` - POST /recommendations/bulk-approve
23. Create async function `updateConsent(userId, action)` - POST /consent
24. Create async function `getConsent(userId)` - GET /consent/{userId}
25. Export all functions

### Routing Setup
26. Update `frontend/src/App.jsx`
27. Import BrowserRouter, Routes, Route from react-router-dom
28. Create route structure:
    - / → redirect to /operator/dashboard
    - /operator/dashboard → OperatorDashboard
    - /operator/users → OperatorUserList
    - /operator/users/:userId → OperatorUserDetail
    - /operator/approval-queue → OperatorApprovalQueue
    - /user/:userId/dashboard → UserDashboard
29. Wrap routes in BrowserRouter

### Layout Component
30. Create `frontend/src/components/Layout.jsx`
31. Create basic navigation header with links:
    - Operator Dashboard
    - User List
    - Approval Queue
32. Add main content area that renders children
33. Style with Tailwind classes
34. Export Layout component

### Page Placeholders
35. Create `frontend/src/pages/OperatorDashboard.jsx` with placeholder div
36. Create `frontend/src/pages/OperatorUserList.jsx` with placeholder div
37. Create `frontend/src/pages/OperatorUserDetail.jsx` with placeholder div
38. Create `frontend/src/pages/OperatorApprovalQueue.jsx` with placeholder div
39. Create `frontend/src/pages/UserDashboard.jsx` with placeholder div
40. Each page should render page title and "Coming soon" message

### Testing Navigation
41. Start backend: `uvicorn app.main:app --reload`
42. Start frontend: `npm run dev`
43. Verify frontend accessible at http://localhost:5173
44. Test navigation between placeholder pages
45. Verify no console errors
46. Verify CORS working (check network tab)

---

## PR #12: Frontend - Operator Dashboard (Metrics & Charts)

### Dashboard Data Fetching
1. Update `frontend/src/pages/OperatorDashboard.jsx`
2. Import useState, useEffect from React
3. Import api service functions
4. Create state variables:
   - dashboardData (object)
   - loading (boolean)
   - error (string)
5. Create useEffect to fetch dashboard data on mount
6. Call getOperatorDashboard() API function
7. Update state with response data
8. Handle loading and error states

### Metrics Cards Component
9. Create `frontend/src/components/MetricsCard.jsx`
10. Accept props: title, value, subtitle, icon (optional)
11. Use Shadcn Card component
12. Display title in card header
13. Display large value in card content
14. Display subtitle below value
15. Style with Tailwind for visual hierarchy
16. Export component

### Dashboard Layout
17. In OperatorDashboard.jsx, create grid layout for metrics
18. Use Tailwind grid classes (grid-cols-1 md:grid-cols-2 lg:grid-cols-4)
19. Create MetricsCard for total users
20. Create MetricsCard for users with consent
21. Create MetricsCard for pending approvals
22. Create MetricsCard for avg latency

### Persona Distribution Chart
23. Install recharts if not already installed
24. Import BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip from recharts
25. Transform persona_distribution data for recharts:
    - Convert object to array of {name, value} objects
26. Create bar chart showing persona distribution
27. Style with Shadcn Card wrapper
28. Add chart title "Persona Distribution"
29. Use responsive container for chart

### Recommendation Status Chart
30. Create second chart for recommendation status breakdown
31. Use similar bar chart structure
32. Show counts for pending, approved, overridden, rejected
33. Use different color scheme for status types
34. Add chart title "Recommendation Status"

### Loading & Error States
35. Create loading skeleton using Shadcn Skeleton component
36. Show skeleton cards while data fetching
37. Create error alert using Shadcn Alert component
38. Display error message if API call fails
39. Add retry button on error

### Testing Dashboard
40. Run frontend and backend
41. Verify metrics display correctly
42. Verify charts render with data
43. Test loading state (add artificial delay)
44. Test error state (stop backend)
45. Verify responsive layout on different screen sizes
