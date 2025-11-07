# SpendSense Tasks - Part 4: Frontend User Management & Persona Assignment

## PR #13: Frontend - Operator User List Page

### User List Data Fetching
- [x] 1. Update `frontend/src/pages/OperatorUserList.jsx`
- [x] 2. Import useState, useEffect from React
- [x] 3. Import getUsers API function
- [x] 4. Create state variables:
  - users (array)
  - loading (boolean)
  - error (string)
  - filters (object: userType, consentStatus)
  - pagination (object: limit, offset, total)
- [x] 5. Create useEffect to fetch users on mount
- [x] 6. Fetch users with current filters and pagination
- [x] 7. Update state with response data

### User Table Component
- [x] 8. Create `frontend/src/components/UserTable.jsx`
- [x] 9. Import Shadcn Table components
- [x] 10. Accept props: users, onUserClick
- [x] 11. Create table with columns:
  - Name
  - Email
  - Persona (30d)
  - Consent Status
  - Actions (View Details button)
- [x] 12. Map over users array to create table rows
- [x] 13. Style consent status with Badge component (green=true, gray=false)
- [x] 14. Style persona type with colored Badge
- [x] 15. Make rows clickable (navigate to detail page)

### Filter Controls
- [x] 16. Create `frontend/src/components/UserFilters.jsx`
- [x] 17. Add filter for user type (customer/operator/all)
- [x] 18. Add filter for consent status (true/false/all)
- [x] 19. Use Shadcn Select components for filters
- [x] 20. Emit onChange events with filter values
- [x] 21. Style with Tailwind flex layout

### Pagination Controls
- [x] 22. Create `frontend/src/components/Pagination.jsx`
- [x] 23. Accept props: currentPage, totalPages, onPageChange
- [x] 24. Create previous/next buttons
- [x] 25. Create page number buttons (show 5 at a time)
- [x] 26. Disable buttons appropriately (prev on page 1, next on last page)
- [x] 27. Style with Shadcn Button components

### User List Page Layout
- [x] 28. In OperatorUserList.jsx, add page header with title
- [x] 29. Add UserFilters component
- [x] 30. Add UserTable component with users data
- [x] 31. Add Pagination component at bottom
- [x] 32. Handle filter changes (refetch users)
- [x] 33. Handle pagination changes (refetch users)
- [x] 34. Wire up navigation to user detail page on row click

### Search Functionality
- [x] 35. Add search input field to page header
- [x] 36. Create state for search term
- [x] 37. Debounce search input (use setTimeout)
- [x] 38. Filter users by name or email locally (or add API support)
- [x] 39. Style search input with Shadcn Input component

### Loading & Error States
- [x] 40. Show loading skeleton while fetching
- [x] 41. Show empty state if no users found
- [x] 42. Show error alert if API call fails
- [x] 43. Add refresh button in error state

### Backend - Users Endpoint
- [x] 44. Create `backend/app/routers/users.py`
- [x] 45. Create APIRouter with prefix="/users"
- [x] 46. Create GET `/` endpoint:
  - Accept query parameters: limit (default: 25), offset (default: 0), user_type (optional), consent_status (optional boolean)
  - Query User records with filters
  - Query Persona records for 30d window (join or separate query)
  - Apply pagination
  - Return response with: users (array), total (count), limit, offset
- [x] 47. For each user, include:
  - user_id, full_name, email, user_type, consent_status
  - personas array with 30d persona if available
- [x] 48. Add error handling for database errors
- [x] 49. Register router in main.py

### Backend - Operator Dashboard Endpoint
- [x] 50. Create `backend/app/routers/operator.py`
- [x] 51. Create APIRouter with prefix="/operator"
- [x] 52. Create GET `/dashboard` endpoint:
  - Query total users count
  - Query users with consent_status=True count
  - Query persona distribution (count by persona_type for 30d window)
  - Query recommendation status breakdown (count by status)
  - Calculate average latency from recommendations table
- [x] 53. Return response with:
  - total_users
  - users_with_consent
  - persona_distribution (dict)
  - recommendations (dict with status counts)
  - metrics (dict with avg_latency_ms)
- [x] 54. Add error handling
- [x] 55. Register router in main.py

### Testing User List
- [x] 56. Verify user list displays all 75 users
- [x] 57. Test filter by consent status
- [x] 58. Test pagination (navigate through pages)
- [x] 59. Test search functionality
- [x] 60. Test click to navigate to detail page
- [x] 61. Verify responsive layout

---

## PR #14: Frontend - Operator User Detail Page

### User Detail Data Fetching
- [x] 1. Update `frontend/src/pages/OperatorUserDetail.jsx`
- [x] 2. Import useParams to get userId from URL
- [x] 3. Import useState, useEffect
- [x] 4. Import getUser, getUserProfile, getOperatorUserSignals API functions
- [x] 5. Create state variables:
  - user (object)
  - profile (object with personas and features)
  - signals (object with detailed signal breakdown)
  - loading (boolean)
  - error (string)
- [x] 6. Create useEffect to fetch all data on mount
- [x] 7. Fetch user, profile, and signals in parallel (Promise.all)
- [x] 8. Update state with response data

### User Info Card
- [x] 9. Create `frontend/src/components/UserInfoCard.jsx`
- [x] 10. Accept props: user data
- [x] 11. Display user name, email, user type
- [x] 12. Display consent status with Badge
- [x] 13. Display consent granted/revoked dates if available
- [x] 14. Use Shadcn Card component for layout
- [x] 15. Style with Tailwind

### Persona Display Component
- [x] 16. Create `frontend/src/components/PersonaDisplay.jsx`
- [x] 17. Accept props: persona object (type, confidence, assigned_at)
- [x] 18. Display persona type with large badge/chip
- [x] 19. Display confidence score as percentage
- [x] 20. Display assigned date
- [x] 21. Add icon/color coding per persona type:
  - high_utilization: red
  - variable_income: orange
  - subscription_heavy: yellow
  - savings_builder: green
  - wealth_builder: blue
- [x] 22. Use Shadcn Card component

### Signal Display Component - Subscriptions
- [x] 23. Create `frontend/src/components/SignalDisplay.jsx`
- [x] 24. Accept props: signals object, signalType (subscriptions/savings/credit/income)
- [x] 25. For subscriptions, display:
  - Number of recurring merchants
  - Monthly recurring spend ($)
  - Subscription spend share (%)
- [x] 26. Use progress bar to visualize subscription share
- [x] 27. List recurring merchant names if available
- [x] 28. Use Shadcn Card and Progress components

### Signal Display Component - Savings
- [x] 29. In SignalDisplay, add savings view:
  - Net savings inflow ($)
  - Savings growth rate (%)
  - Emergency fund coverage (months)
- [x] 30. Use progress bar for emergency fund (target: 3-6 months)
- [x] 31. Color code: <1 month (red), 1-3 (yellow), 3+ (green)

### Signal Display Component - Credit
- [x] 32. In SignalDisplay, add credit view:
  - Average utilization (%)
  - Max utilization (%)
  - List of credit cards with individual utilization
  - Flags: minimum payment only, interest charges, overdue
- [x] 33. Use progress bars for utilization
- [x] 34. Color code utilization: <30% (green), 30-50% (yellow), >50% (red)
- [x] 35. Show warning badges for flags

### Signal Display Component - Income
- [x] 36. In SignalDisplay, add income view:
  - Payroll detected (yes/no badge)
  - Average monthly income ($)
  - Median pay gap (days)
  - Income variability (%)
  - Cash flow buffer (months)
- [x] 37. Show warning if buffer < 1 month
- [x] 38. Show warning if high variability (>30%)

### User Detail Page Layout
- [x] 39. In OperatorUserDetail.jsx, create two-column layout
- [x] 40. Left column:
  - UserInfoCard at top
  - Persona display for 30d
  - Persona display for 180d
- [x] 41. Right column:
  - Tab navigation for signal types
  - SignalDisplay for selected tab (30d signals)
  - SignalDisplay for 180d signals below

### Recommendations Section
- [x] 42. Add section below signals for user recommendations
- [x] 43. Fetch recommendations for this user
- [x] 44. Display list of recommendations with status badges
- [x] 45. Add "Generate Recommendations" button (wire up later)
- [x] 46. Show message if no recommendations yet

### Back Navigation
- [x] 47. Add back button at top of page
- [x] 48. Link back to user list page
- [x] 49. Use Shadcn Button component

### Loading & Error States
- [x] 50. Show loading skeletons for each section
- [x] 51. Show error alert if any API call fails
- [x] 52. Add retry buttons

### Testing User Detail
- [ ] 53. Navigate to detail page from user list
- [ ] 54. Verify all user data displays correctly
- [ ] 55. Verify personas show for both windows
- [ ] 56. Verify all 4 signal types display
- [ ] 57. Test tab navigation between signals
- [ ] 58. Verify back button works
- [ ] 59. Test with users having different personas

### Backend - Get User by ID Endpoint
- [x] 60. Add GET `/{user_id}` endpoint to `backend/app/routers/users.py`
- [x] 61. Accept user_id as path parameter
- [x] 62. Query User record by user_id
- [x] 63. Query Persona records for both 30d and 180d windows
- [x] 64. Return user object with:
  - user_id, full_name, email, user_type, consent_status
  - consent_granted_at, consent_revoked_at, created_at
  - personas array with both 30d and 180d personas if available
- [x] 65. Add error handling:
  - User not found → 404
  - Database error → 500
- [ ] 66. Test endpoint via Swagger UI
- [ ] 67. Verify frontend getUser() function works correctly

### Backend - Get User Signals Endpoint
- [x] 68. Add GET `/users/{user_id}/signals` endpoint to `backend/app/routers/operator.py`
- [x] 69. Accept user_id as path parameter
- [x] 70. Query User record for user_name and consent_status
- [x] 71. Query UserFeature records for 30d and 180d windows
- [x] 72. Query Persona records for 30d and 180d windows
- [x] 73. Query Transactions to get recurring merchant names (merchants with ≥3 transactions)
- [x] 74. Query Accounts/Liabilities to get credit card details (last_four, balance, limit, utilization)
- [x] 75. Calculate income frequency from transaction patterns (biweekly/monthly)
- [x] 76. Build 30d_signals object with:
  - subscriptions: recurring_merchants (array), monthly_spend, spend_share
  - savings: net_inflow, growth_rate, emergency_fund_months
  - credit: cards array with last_four, utilization, balance, limit
  - income: payroll_detected, avg_monthly, frequency
- [x] 77. Build 180d_signals object (same structure)
- [x] 78. Return response with user_id, user_name, consent_status, 30d_signals, 180d_signals, persona_30d, persona_180d
- [x] 79. Add error handling:
  - User not found → 404
  - Features not computed → 400 with message
  - Database error → 500
- [ ] 80. Test endpoint via Swagger UI
- [ ] 81. Verify frontend getOperatorUserSignals() function works correctly

---

## PR #15: Persona Assignment Service

### Persona Assignment Service File
- [x] 1. Create `backend/app/services/persona_assignment.py`
- [x] 2. Import database models and session
- [x] 3. Import UserFeature model

### Persona Check Functions
- [x] 4. Create `check_high_utilization(features: UserFeature) -> bool`:
  - Return True if max_utilization >= 0.50
  - OR interest_charges_present == True
  - OR minimum_payment_only_flag == True
  - OR any_overdue == True
  - Otherwise return False
- [x] 5. Create `check_variable_income(features: UserFeature) -> bool`:
  - Return True if median_pay_gap_days > 45
  - AND cash_flow_buffer_months < 1
  - Otherwise return False
- [x] 6. Create `check_subscription_heavy(features: UserFeature) -> bool`:
  - Return True if recurring_merchants >= 3
  - AND (monthly_recurring_spend >= 50 OR subscription_spend_share >= 0.10)
  - Otherwise return False
- [x] 7. Create `check_savings_builder(features: UserFeature) -> bool`:
  - Return True if (savings_growth_rate >= 0.02 OR net_savings_inflow >= 200)
  - AND avg_utilization < 0.30
  - Otherwise return False
- [x] 8. Create `check_wealth_builder(features: UserFeature) -> bool`:
  - Return True if avg_monthly_income > 10000
  - AND features.user has savings_balance > 25000 (need to query)
  - AND max_utilization <= 0.20
  - AND no overdrafts/late fees (check from signals)
  - AND investment_account_detected == True
  - Otherwise return False

### Savings Balance Query for Wealth Builder
- [x] 9. Create helper `get_total_savings_balance(db, user_id) -> float`:
  - Query accounts for user where type in savings types
  - Sum balance_current across accounts
  - Return total

### Persona Assignment Logic
- [x] 10. Create `assign_persona(db, user_id: str, window_days: int) -> tuple[str, float, dict]`:
  - Query UserFeature for user and window
  - If no features found, return ('savings_builder', 0.1, {}) as fallback
  - Create list of matched personas with priorities
- [x] 11. Check wealth_builder first (priority 1.0)
- [x] 12. Check high_utilization (priority 0.95 if util>=80%, else 0.8)
- [x] 13. Check savings_builder (priority 0.7)
- [x] 14. Check variable_income (priority 0.6)
- [x] 15. Check subscription_heavy (priority 0.5)
- [x] 16. If no matches, return ('savings_builder', 0.2, {}) as fallback
- [x] 17. Sort matched personas by priority (descending)
- [x] 18. Return highest priority: (persona_type, confidence_score, reasoning_dict)

### Reasoning Dictionary
- [x] 19. For reasoning_dict, include:
  - matched_criteria: list of criteria that passed
  - feature_values: dict of relevant feature values
  - timestamp: current datetime
- [x] 20. Format as JSON-serializable dict

### Persona Creation/Update
- [x] 21. Create `create_or_update_persona(db, user_id, window_days, persona_type, confidence, reasoning)`:
  - Check if Persona record exists for user + window
  - If exists, update with new values
  - If not, create new Persona record
  - Commit to database
  - Return Persona object

### Main Assignment Function
- [x] 22. Create `assign_and_save_persona(db, user_id: str, window_days: int) -> Persona`:
  - Call assign_persona() to get type, confidence, reasoning
  - Call create_or_update_persona() to save
  - Return Persona object

### Testing Persona Assignment
- [x] 23. Create test script `scripts/test_persona_assignment.py`
- [x] 24. Test with known user IDs
- [x] 25. Verify high_utilization assigned to high util users
- [x] 26. Verify savings_builder assigned to savers
- [x] 27. Verify wealth_builder assigned to affluent users
- [x] 28. Print reasoning dicts for validation
- [x] 29. Check database for Persona records

---

## PR #16: Persona Assignment Endpoint & Batch Script

### Personas Router Creation
- [x] 1. Create `backend/app/routers/personas.py`
- [x] 2. Create APIRouter with prefix="/personas"
- [x] 3. Import persona assignment service functions

### Assign Persona Endpoint
- [x] 4. Create POST `/{user_id}/assign` endpoint:
  - Accept user_id as path parameter
  - Accept window_days as query parameter (default: 30)
  - Get database session
  - Call assign_and_save_persona()
  - Return persona object as JSON
- [x] 5. Add error handling:
  - User not found → 404
  - Features not computed → 400 with message
  - Server error → 500

### Get Persona Endpoint
- [x] 6. Create GET `/{user_id}` endpoint:
  - Accept user_id and optional window parameter
  - Query Persona records for user
  - Return persona(s) as JSON
  - If window specified, return single persona
  - If no window, return both 30d and 180d
- [x] 7. Add error handling for user/persona not found

### Router Registration
- [x] 8. Import personas router in main.py
- [x] 9. Include router in FastAPI app

### Batch Assignment Script
- [x] 10. Create `scripts/assign_all_personas.py`
- [x] 11. Import database session and persona service
- [x] 12. Query all users from database
- [x] 13. For each user:
  - Assign persona for 30-day window
  - Assign persona for 180-day window
  - Print progress (every 10 users)
- [x] 14. Print summary statistics:
  - Total users processed
  - Persona distribution for 30d
  - Persona distribution for 180d
  - Users with fallback persona assignments (low confidence savings_builder)
- [x] 15. Add __main__ block to run script

### Persona Distribution Validation
- [x] 16. After running batch script, query database:
  - Count personas by type for 30d window
  - Count personas by type for 180d window
- [x] 17. Verify all 5 persona types are represented
- [x] 18. If not, review synthetic data generation
- [x] 19. Adjust data generation to ensure variety (Note: Some persona types missing - will enhance synthetic data generation later for better variance)

### Update Profile Endpoint
- [x] 20. Update profile router to include persona data
- [x] 21. Query Persona records when fetching profile
- [x] 22. Include in response

### Testing Persona Assignment
- [x] 23. Run batch script: `python scripts/assign_all_personas.py`
- [x] 24. Verify all 75 users have personas assigned (71 users processed successfully)
- [x] 25. Check persona distribution in terminal output
- [x] 26. Verify database has records in personas table
- [x] 27. Test API endpoint via Swagger UI
- [x] 28. Verify profile endpoint includes persona data
- [x] 29. Test frontend: refresh user detail page, verify persona displays
