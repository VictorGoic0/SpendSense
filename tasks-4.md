# SpendSense Tasks - Part 4: Frontend User Management & Persona Assignment

## PR #13: Frontend - Operator User List Page

### User List Data Fetching
- [ ] 1. Update `frontend/src/pages/OperatorUserList.jsx`
- [ ] 2. Import useState, useEffect from React
- [ ] 3. Import getUsers API function
- [ ] 4. Create state variables:
  - users (array)
  - loading (boolean)
  - error (string)
  - filters (object: userType, consentStatus)
  - pagination (object: limit, offset, total)
- [ ] 5. Create useEffect to fetch users on mount
- [ ] 6. Fetch users with current filters and pagination
- [ ] 7. Update state with response data

### User Table Component
- [ ] 8. Create `frontend/src/components/UserTable.jsx`
- [ ] 9. Import Shadcn Table components
- [ ] 10. Accept props: users, onUserClick
- [ ] 11. Create table with columns:
  - Name
  - Email
  - Persona (30d)
  - Consent Status
  - Actions (View Details button)
- [ ] 12. Map over users array to create table rows
- [ ] 13. Style consent status with Badge component (green=true, gray=false)
- [ ] 14. Style persona type with colored Badge
- [ ] 15. Make rows clickable (navigate to detail page)

### Filter Controls
- [ ] 16. Create `frontend/src/components/UserFilters.jsx`
- [ ] 17. Add filter for user type (customer/operator/all)
- [ ] 18. Add filter for consent status (true/false/all)
- [ ] 19. Use Shadcn Select components for filters
- [ ] 20. Emit onChange events with filter values
- [ ] 21. Style with Tailwind flex layout

### Pagination Controls
- [ ] 22. Create `frontend/src/components/Pagination.jsx`
- [ ] 23. Accept props: currentPage, totalPages, onPageChange
- [ ] 24. Create previous/next buttons
- [ ] 25. Create page number buttons (show 5 at a time)
- [ ] 26. Disable buttons appropriately (prev on page 1, next on last page)
- [ ] 27. Style with Shadcn Button components

### User List Page Layout
- [ ] 28. In OperatorUserList.jsx, add page header with title
- [ ] 29. Add UserFilters component
- [ ] 30. Add UserTable component with users data
- [ ] 31. Add Pagination component at bottom
- [ ] 32. Handle filter changes (refetch users)
- [ ] 33. Handle pagination changes (refetch users)
- [ ] 34. Wire up navigation to user detail page on row click

### Search Functionality
- [ ] 35. Add search input field to page header
- [ ] 36. Create state for search term
- [ ] 37. Debounce search input (use setTimeout)
- [ ] 38. Filter users by name or email locally (or add API support)
- [ ] 39. Style search input with Shadcn Input component

### Loading & Error States
- [ ] 40. Show loading skeleton while fetching
- [ ] 41. Show empty state if no users found
- [ ] 42. Show error alert if API call fails
- [ ] 43. Add refresh button in error state

### Testing User List
- [ ] 44. Verify user list displays all 75 users
- [ ] 45. Test filter by consent status
- [ ] 46. Test pagination (navigate through pages)
- [ ] 47. Test search functionality
- [ ] 48. Test click to navigate to detail page
- [ ] 49. Verify responsive layout

---

## PR #14: Frontend - Operator User Detail Page

### User Detail Data Fetching
- [ ] 1. Update `frontend/src/pages/OperatorUserDetail.jsx`
- [ ] 2. Import useParams to get userId from URL
- [ ] 3. Import useState, useEffect
- [ ] 4. Import getUser, getUserProfile, getOperatorUserSignals API functions
- [ ] 5. Create state variables:
  - user (object)
  - profile (object with personas and features)
  - signals (object with detailed signal breakdown)
  - loading (boolean)
  - error (string)
- [ ] 6. Create useEffect to fetch all data on mount
- [ ] 7. Fetch user, profile, and signals in parallel (Promise.all)
- [ ] 8. Update state with response data

### User Info Card
- [ ] 9. Create `frontend/src/components/UserInfoCard.jsx`
- [ ] 10. Accept props: user data
- [ ] 11. Display user name, email, user type
- [ ] 12. Display consent status with Badge
- [ ] 13. Display consent granted/revoked dates if available
- [ ] 14. Use Shadcn Card component for layout
- [ ] 15. Style with Tailwind

### Persona Display Component
- [ ] 16. Create `frontend/src/components/PersonaDisplay.jsx`
- [ ] 17. Accept props: persona object (type, confidence, assigned_at)
- [ ] 18. Display persona type with large badge/chip
- [ ] 19. Display confidence score as percentage
- [ ] 20. Display assigned date
- [ ] 21. Add icon/color coding per persona type:
  - high_utilization: red
  - variable_income: orange
  - subscription_heavy: yellow
  - savings_builder: green
  - wealth_builder: blue
- [ ] 22. Use Shadcn Card component

### Signal Display Component - Subscriptions
- [ ] 23. Create `frontend/src/components/SignalDisplay.jsx`
- [ ] 24. Accept props: signals object, signalType (subscriptions/savings/credit/income)
- [ ] 25. For subscriptions, display:
  - Number of recurring merchants
  - Monthly recurring spend ($)
  - Subscription spend share (%)
- [ ] 26. Use progress bar to visualize subscription share
- [ ] 27. List recurring merchant names if available
- [ ] 28. Use Shadcn Card and Progress components

### Signal Display Component - Savings
- [ ] 29. In SignalDisplay, add savings view:
  - Net savings inflow ($)
  - Savings growth rate (%)
  - Emergency fund coverage (months)
- [ ] 30. Use progress bar for emergency fund (target: 3-6 months)
- [ ] 31. Color code: <1 month (red), 1-3 (yellow), 3+ (green)

### Signal Display Component - Credit
- [ ] 32. In SignalDisplay, add credit view:
  - Average utilization (%)
  - Max utilization (%)
  - List of credit cards with individual utilization
  - Flags: minimum payment only, interest charges, overdue
- [ ] 33. Use progress bars for utilization
- [ ] 34. Color code utilization: <30% (green), 30-50% (yellow), >50% (red)
- [ ] 35. Show warning badges for flags

### Signal Display Component - Income
- [ ] 36. In SignalDisplay, add income view:
  - Payroll detected (yes/no badge)
  - Average monthly income ($)
  - Median pay gap (days)
  - Income variability (%)
  - Cash flow buffer (months)
- [ ] 37. Show warning if buffer < 1 month
- [ ] 38. Show warning if high variability (>30%)

### User Detail Page Layout
- [ ] 39. In OperatorUserDetail.jsx, create two-column layout
- [ ] 40. Left column:
  - UserInfoCard at top
  - Persona display for 30d
  - Persona display for 180d
- [ ] 41. Right column:
  - Tab navigation for signal types
  - SignalDisplay for selected tab (30d signals)
  - SignalDisplay for 180d signals below

### Recommendations Section
- [ ] 42. Add section below signals for user recommendations
- [ ] 43. Fetch recommendations for this user
- [ ] 44. Display list of recommendations with status badges
- [ ] 45. Add "Generate Recommendations" button (wire up later)
- [ ] 46. Show message if no recommendations yet

### Back Navigation
- [ ] 47. Add back button at top of page
- [ ] 48. Link back to user list page
- [ ] 49. Use Shadcn Button component

### Loading & Error States
- [ ] 50. Show loading skeletons for each section
- [ ] 51. Show error alert if any API call fails
- [ ] 52. Add retry buttons

### Testing User Detail
- [ ] 53. Navigate to detail page from user list
- [ ] 54. Verify all user data displays correctly
- [ ] 55. Verify personas show for both windows
- [ ] 56. Verify all 4 signal types display
- [ ] 57. Test tab navigation between signals
- [ ] 58. Verify back button works
- [ ] 59. Test with users having different personas

---

## PR #15: Persona Assignment Service

### Persona Assignment Service File
- [ ] 1. Create `backend/app/services/persona_assignment.py`
- [ ] 2. Import database models and session
- [ ] 3. Import UserFeature model

### Persona Check Functions
- [ ] 4. Create `check_high_utilization(features: UserFeature) -> bool`:
  - Return True if max_utilization >= 0.50
  - OR interest_charges_present == True
  - OR minimum_payment_only_flag == True
  - OR any_overdue == True
  - Otherwise return False
- [ ] 5. Create `check_variable_income(features: UserFeature) -> bool`:
  - Return True if median_pay_gap_days > 45
  - AND cash_flow_buffer_months < 1
  - Otherwise return False
- [ ] 6. Create `check_subscription_heavy(features: UserFeature) -> bool`:
  - Return True if recurring_merchants >= 3
  - AND (monthly_recurring_spend >= 50 OR subscription_spend_share >= 0.10)
  - Otherwise return False
- [ ] 7. Create `check_savings_builder(features: UserFeature) -> bool`:
  - Return True if (savings_growth_rate >= 0.02 OR net_savings_inflow >= 200)
  - AND avg_utilization < 0.30
  - Otherwise return False
- [ ] 8. Create `check_wealth_builder(features: UserFeature) -> bool`:
  - Return True if avg_monthly_income > 10000
  - AND features.user has savings_balance > 25000 (need to query)
  - AND max_utilization <= 0.20
  - AND no overdrafts/late fees (check from signals)
  - AND investment_account_detected == True
  - Otherwise return False

### Savings Balance Query for Wealth Builder
- [ ] 9. Create helper `get_total_savings_balance(db, user_id) -> float`:
  - Query accounts for user where type in savings types
  - Sum balance_current across accounts
  - Return total

### Persona Assignment Logic
- [ ] 10. Create `assign_persona(db, user_id: str, window_days: int) -> tuple[str, float, dict]`:
  - Query UserFeature for user and window
  - If no features found, return ('general_wellness', 0.0, {})
  - Create list of matched personas with priorities
- [ ] 11. Check wealth_builder first (priority 1.0)
- [ ] 12. Check high_utilization (priority 0.95 if util>=80%, else 0.8)
- [ ] 13. Check savings_builder (priority 0.7)
- [ ] 14. Check variable_income (priority 0.6)
- [ ] 15. Check subscription_heavy (priority 0.5)
- [ ] 16. If no matches, return ('general_wellness', 0.0, {})
- [ ] 17. Sort matched personas by priority (descending)
- [ ] 18. Return highest priority: (persona_type, confidence_score, reasoning_dict)

### Reasoning Dictionary
- [ ] 19. For reasoning_dict, include:
  - matched_criteria: list of criteria that passed
  - feature_values: dict of relevant feature values
  - timestamp: current datetime
- [ ] 20. Format as JSON-serializable dict

### Persona Creation/Update
- [ ] 21. Create `create_or_update_persona(db, user_id, window_days, persona_type, confidence, reasoning)`:
  - Check if Persona record exists for user + window
  - If exists, update with new values
  - If not, create new Persona record
  - Commit to database
  - Return Persona object

### Main Assignment Function
- [ ] 22. Create `assign_and_save_persona(db, user_id: str, window_days: int) -> Persona`:
  - Call assign_persona() to get type, confidence, reasoning
  - Call create_or_update_persona() to save
  - Return Persona object

### Testing Persona Assignment
- [ ] 23. Create test script `scripts/test_persona_assignment.py`
- [ ] 24. Test with known user IDs
- [ ] 25. Verify high_utilization assigned to high util users
- [ ] 26. Verify savings_builder assigned to savers
- [ ] 27. Verify wealth_builder assigned to affluent users
- [ ] 28. Print reasoning dicts for validation
- [ ] 29. Check database for Persona records

---

## PR #16: Persona Assignment Endpoint & Batch Script

### Personas Router Creation
- [ ] 1. Create `backend/app/routers/personas.py`
- [ ] 2. Create APIRouter with prefix="/personas"
- [ ] 3. Import persona assignment service functions

### Assign Persona Endpoint
- [ ] 4. Create POST `/{user_id}/assign` endpoint:
  - Accept user_id as path parameter
  - Accept window_days as query parameter (default: 30)
  - Get database session
  - Call assign_and_save_persona()
  - Return persona object as JSON
- [ ] 5. Add error handling:
  - User not found → 404
  - Features not computed → 400 with message
  - Server error → 500

### Get Persona Endpoint
- [ ] 6. Create GET `/{user_id}` endpoint:
  - Accept user_id and optional window parameter
  - Query Persona records for user
  - Return persona(s) as JSON
  - If window specified, return single persona
  - If no window, return both 30d and 180d
- [ ] 7. Add error handling for user/persona not found

### Router Registration
- [ ] 8. Import personas router in main.py
- [ ] 9. Include router in FastAPI app

### Batch Assignment Script
- [ ] 10. Create `scripts/assign_all_personas.py`
- [ ] 11. Import database session and persona service
- [ ] 12. Query all users from database
- [ ] 13. For each user:
  - Assign persona for 30-day window
  - Assign persona for 180-day window
  - Print progress (every 10 users)
- [ ] 14. Print summary statistics:
  - Total users processed
  - Persona distribution for 30d
  - Persona distribution for 180d
  - Users with no persona (general_wellness)
- [ ] 15. Add __main__ block to run script

### Persona Distribution Validation
- [ ] 16. After running batch script, query database:
  - Count personas by type for 30d window
  - Count personas by type for 180d window
- [ ] 17. Verify all 5 persona types are represented
- [ ] 18. If not, review synthetic data generation
- [ ] 19. Adjust data generation to ensure variety

### Update Profile Endpoint
- [ ] 20. Update profile router to include persona data
- [ ] 21. Query Persona records when fetching profile
- [ ] 22. Include in response

### Testing Persona Assignment
- [ ] 23. Run batch script: `python scripts/assign_all_personas.py`
- [ ] 24. Verify all 75 users have personas assigned
- [ ] 25. Check persona distribution in terminal output
- [ ] 26. Verify database has records in personas table
- [ ] 27. Test API endpoint via Swagger UI
- [ ] 28. Verify profile endpoint includes persona data
- [ ] 29. Test frontend: refresh user detail page, verify persona displays
