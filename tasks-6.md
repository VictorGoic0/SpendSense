# SpendSense Tasks - Part 6: Recommendation Endpoints & Approval Workflow

## PR #22: Get Recommendations Endpoint

### Get Recommendations Endpoint
- [x] 1. In recommendations router, create GET `/{user_id}` endpoint
- [x] 2. Accept user_id as path parameter
- [x] 3. Accept optional status query parameter (filter by status)
- [x] 4. Accept optional window_days query parameter (default: return all)
- [x] 5. Get database session

### Query Recommendations
- [x] 6. Query Recommendation records for user_id
- [x] 7. If status parameter provided, filter by status
- [x] 8. If window_days provided, filter by window_days
- [x] 9. Order by generated_at descending (newest first)
- [x] 10. Limit to 50 recommendations (pagination could be added later)

### Response Formatting
- [x] 11. Convert recommendation models to schema objects
- [x] 12. For each recommendation, include:
    - recommendation_id
    - title
    - content
    - rationale
    - status
    - persona_type
    - generated_at
    - approved_by (if applicable)
    - approved_at (if applicable)
- [x] 13. Return JSON response with recommendations list and total count

### Access Control
- [x] 14. If status query param not provided:
    - For customer users: only return approved recommendations
    - For operator users: return all statuses
- [x] 15. Add comment indicating future authentication will enforce this

### Error Handling
- [x] 16. Handle user not found → 404
- [x] 17. Handle database errors → 500
- [x] 18. Add logging

### Testing Get Recommendations
- [x] 19. Test via API with user who has recommendations
- [x] 20. Test status filter (pending_approval, approved)
- [x] 21. Test window filter (30, 180)
- [x] 22. Verify only approved recs returned by default
- [x] 23. Verify correct order (newest first)

---

## PR #23: Approve Recommendation Endpoint

### Approve Endpoint
- [x] 1. In recommendations router, create POST `/{recommendation_id}/approve` endpoint
- [x] 2. Accept recommendation_id as path parameter
- [x] 3. Accept ApproveRequest schema in body:
   - operator_id: str
   - notes: str (optional)
- [x] 4. Get database session

### Validation
- [x] 5. Query Recommendation by recommendation_id
- [x] 6. If not found → 404 error
- [x] 7. If already approved → 400 error with message
- [x] 8. If status is 'rejected' → 400 error (can't approve rejected rec)

### Update Recommendation
- [x] 9. Update recommendation:
   - Set status='approved'
   - Set approved_by=operator_id
   - Set approved_at=current timestamp
- [x] 10. Commit transaction

### Log Operator Action
- [x] 11. Create OperatorAction record:
   - operator_id
   - action_type='approve'
   - recommendation_id
   - user_id (from recommendation)
   - reason=notes (if provided)
   - timestamp=now
- [x] 12. Commit transaction

### Response
- [x] 13. Query updated recommendation
- [x] 14. Return recommendation with updated status
- [x] 15. Return 200 status code

### Error Handling
- [x] 16. Handle not found → 404
- [x] 17. Handle invalid state transitions → 400
- [x] 18. Handle database errors → 500
- [x] 19. Add logging for all approve actions

### Testing Approve
- [x] 20. Generate recommendations for test user
- [x] 21. Get pending recommendation ID
- [x] 22. Call approve endpoint with operator_id
- [x] 23. Verify status changed to 'approved'
- [x] 24. Verify approved_by and approved_at set
- [x] 25. Verify operator_actions table has record
- [x] 26. Verify user can now see recommendation via GET endpoint

---

## PR #24: Override & Reject Endpoints

### Override Endpoint
- [x] 1. Create POST `/{recommendation_id}/override` endpoint
- [x] 2. Accept recommendation_id as path parameter
- [x] 3. Accept OverrideRequest schema in body:
   - operator_id: str
   - new_title: str (optional)
   - new_content: str (optional)
   - reason: str (required)
- [x] 4. Get database session

### Override Validation
- [x] 5. Query Recommendation by ID
- [x] 6. If not found → 404
- [x] 7. Validate at least one of new_title or new_content provided → 400 if neither

### Store Original Content
- [x] 8. Create original_content dict with:
   - original_title
   - original_content
   - overridden_at timestamp
- [x] 9. Convert to JSON string
- [x] 10. Store in recommendation.original_content field

### Update Recommendation
- [x] 11. Update recommendation:
   - Set status='overridden'
   - Update title if new_title provided
   - Update content if new_content provided
   - Append disclosure to new content if modified
   - Set override_reason=reason
   - Validate new content tone if modified
- [x] 12. If tone validation fails → 400 error
- [x] 13. Commit transaction

### Log Override Action
- [x] 14. Create OperatorAction record with action_type='override'
- [x] 15. Include reason in operator action
- [x] 16. Commit transaction

### Override Response
- [x] 17. Return updated recommendation with:
   - New content
   - original_content field
   - override_reason
- [x] 18. Return 200 status code

### Reject Endpoint
- [x] 19. Create POST `/{recommendation_id}/reject` endpoint
- [x] 20. Accept recommendation_id and RejectRequest schema:
   - operator_id: str
   - reason: str (required)

### Reject Implementation
- [x] 21. Query Recommendation by ID
- [x] 22. If not found → 404
- [x] 23. If already approved and visible to user → 400 (shouldn't reject approved recs)
- [x] 24. Update status='rejected'
- [x] 25. Set metadata with rejection reason
- [x] 26. Commit transaction

### Log Reject Action
- [x] 27. Create OperatorAction record with action_type='reject'
- [x] 28. Include reason
- [x] 29. Commit transaction
- [x] 30. Return updated recommendation

### Error Handling
- [x] 31. Handle all validation errors with appropriate messages
- [x] 32. Add logging for override and reject actions
- [x] 33. Test both endpoints via API

### Testing Override & Reject
- [x] 34. Test override with new title and content
- [x] 35. Verify original content preserved
- [x] 36. Verify tone validation on new content
- [x] 37. Test reject with pending recommendation
- [x] 38. Verify can't reject approved recommendation
- [x] 39. Verify operator actions logged

---

## PR #25: Bulk Approve Endpoint

### Bulk Approve Endpoint
- [x] 1. Create POST `/bulk-approve` endpoint
- [x] 2. Accept BulkApproveRequest schema:
   - operator_id: str
   - recommendation_ids: list[str]
- [x] 3. Get database session

### Bulk Processing
- [x] 4. Initialize counters: approved=0, failed=0, errors=[]
- [x] 5. Loop through recommendation_ids:
   - Query recommendation by ID
   - Skip if not found (log as failed)
   - Skip if not in pending_approval status (log as failed)
   - Update status='approved'
   - Set approved_by and approved_at
   - Create OperatorAction record
   - Increment approved counter
   - Catch and log any errors per recommendation

### Batch Commit
- [x] 6. After loop, commit all changes in single transaction
- [x] 7. If commit fails, rollback and return error
- [x] 8. If partial success, commit what succeeded

### Response
- [x] 9. Return BulkApproveResponse with:
   - approved: count
   - failed: count
   - errors: list of error messages
- [x] 10. Return 200 if any succeeded, 400 if all failed

### Error Handling
- [x] 11. Handle individual recommendation errors gracefully
- [x] 12. Don't fail entire batch if one fails
- [x] 13. Provide detailed error messages per failed ID
- [x] 14. Add comprehensive logging

### Testing Bulk Approve
- [x] 15. Generate 10 recommendations for test user
- [x] 16. Get list of pending recommendation IDs
- [x] 17. Call bulk approve with all IDs
- [x] 18. Verify all changed to approved
- [x] 19. Test with mix of valid and invalid IDs
- [x] 20. Verify partial success handled correctly
- [x] 21. Verify error messages informative

---

## PR #26: Frontend - Approval Queue Page

### Approval Queue Data Fetching
- [x] 1. Update `frontend/src/pages/OperatorApprovalQueue.jsx`
- [x] 2. Import useState, useEffect
- [x] 3. Import API functions: getApprovalQueue, approveRecommendation, bulkApprove, etc.
- [x] 4. Create state variables:
   - recommendations (array)
   - selectedIds (Set)
   - loading (boolean)
   - error (string)
   - filter (status filter)

### Fetch Pending Recommendations
- [x] 5. Create useEffect to fetch on mount
- [x] 6. Call getApprovalQueue(status='pending_approval')
- [x] 7. Update recommendations state
- [x] 8. Handle loading and error states

### Recommendation Card Component
- [x] 9. Create `frontend/src/components/RecommendationCard.jsx`
- [x] 10. Accept props: recommendation, onApprove, onReject, onOverride, onSelect
- [x] 11. Use Shadcn Card component
- [x] 12. Display:
    - Checkbox for selection (left side)
    - Recommendation title (large text)
    - User name and persona badge
    - Content preview (first 150 chars)
    - Rationale preview
    - Generated date
    - Action buttons: Approve, Reject, Override
- [x] 13. Style with Tailwind

### Bulk Selection
- [x] 14. Add "Select All" checkbox in page header
- [x] 15. Bind to state that selects/deselects all visible recommendations
- [x] 16. Update selectedIds state when individual checkboxes clicked
- [x] 17. Show count of selected items in header

### Bulk Approve Button
- [x] 18. Add "Bulk Approve" button in header (primary button)
- [x] 19. Disable if selectedIds.length === 0
- [x] 20. On click:
    - Call bulkApprove API with selectedIds array
    - Show loading spinner
    - On success: refetch recommendations, clear selection, show success toast
    - On error: show error message
- [x] 21. Use Shadcn Button component

### Individual Approve
- [x] 22. Handle individual approve button click:
    - Call approveRecommendation API with rec ID and operator ID
    - On success: remove from list or update status, show success toast
    - On error: show error toast
- [x] 23. Add loading state per recommendation

### Override Dialog
- [x] 24. Create override dialog using Shadcn Dialog component
- [x] 25. Include form fields:
    - New title (optional text input)
    - New content (optional textarea)
    - Reason (required textarea)
- [x] 26. On submit:
    - Call override API endpoint
    - Close dialog
    - Refetch recommendations
    - Show success toast
- [x] 27. Add validation: require reason field

### Reject Dialog
- [x] 28. Create reject dialog similar to override
- [x] 29. Include single field: Reason (required textarea)
- [x] 30. On submit:
    - Call reject API endpoint
    - Remove from queue
    - Show success toast

### Page Layout
- [x] 31. Add page header with title "Approval Queue"
- [x] 32. Add toolbar with:
    - Select All checkbox
    - Selected count display
    - Bulk Approve button
- [x] 33. Add filter dropdown for status (future: allow viewing rejected, etc.)
- [x] 34. Add recommendation cards in grid/list layout
- [x] 35. Add empty state if no pending recommendations

### Loading & Error States
- [x] 36. Show skeleton cards while loading
- [x] 37. Show error alert if fetch fails
- [x] 38. Add retry button in error state
- [x] 39. Show success/error toasts for actions

### Auto-refresh
- [x] 40. Add auto-refresh every 30 seconds (or add manual refresh button)
- [x] 41. Implement using setInterval in useEffect
- [x] 42. Clear interval on unmount

### Testing Approval Queue
- [x] 43. Generate recommendations for multiple users
- [x] 44. Navigate to approval queue
- [x] 45. Verify all pending recommendations shown
- [x] 46. Test individual approve (verify removed from queue)
- [x] 47. Test bulk approve with 5+ selected
- [x] 48. Test override with new content
- [x] 49. Test reject with reason
- [x] 50. Verify all actions reflected in database
- [x] 51. Verify operator actions logged

### Server Concurrency Optimization
- [x] 52. Implement uvicorn workers for concurrent request handling
- [x] 53. Update documentation (README.md, techContext.md) with workers command
- [x] 54. Document workers approach in FRAMEWORK_CONCURRENCY_COMPARISON.md
- [x] 55. Note: Using `--workers 4` prevents blocking operations (like recommendation generation) from blocking other requests
- [x] 56. Enable SQLite WAL mode for concurrent reads during writes
- [x] 57. Document WAL mode decision and limitations in DECISIONS.md and LIMITATIONS.md
- [x] 58. Verify fixes: 4 workers + WAL mode resolves hanging issue when generating recommendations

### Markdown Rendering for Recommendations
- [x] 59. Install react-markdown package for rendering Markdown in recommendation content
- [x] 60. Update RecommendationCard component to use ReactMarkdown for content and rationale previews
- [x] 61. Update OperatorUserDetail page to use ReactMarkdown for recommendation content display
- [x] 62. Add type checking to ensure ReactMarkdown always receives string values (handle undefined/null content)
- [x] 63. Update truncateText helper to validate input is a string before processing
- [x] 64. Verify Markdown syntax (bold, italic, etc.) renders correctly in both approval queue and user detail pages

### Expandable Content for Recommendations
- [x] 65. Add expandable content functionality to RecommendationCard component
- [x] 66. Add state to track expanded/collapsed state for content and rationale separately
- [x] 67. Show truncated preview by default (existing behavior)
- [x] 68. Add "Show more" link/button below truncated content
- [x] 69. On click, expand to show full content inline with ReactMarkdown rendering
- [x] 70. Replace "Show more" with "Show less" when expanded
- [x] 71. Add expandable content functionality to OperatorUserDetail recommendation cards
- [x] 72. Ensure both content and rationale can be expanded independently in RecommendationCard
- [x] 73. Style expand/collapse buttons with appropriate hover states
- [x] 74. Test expand/collapse functionality on both approval queue and user detail pages

---

## PR #27: Frontend - User Dashboard & Consent

### User Dashboard Setup
- [ ] 1. Update `frontend/src/pages/UserDashboard.jsx`
- [ ] 2. Accept userId as prop or get from URL params
- [ ] 3. Import useState, useEffect
- [ ] 4. Import API functions: getUser, getConsent, getRecommendations, updateConsent

### Data Fetching
- [ ] 5. Create state variables:
   - user (object)
   - consent (object with status and history)
   - recommendations (array)
   - loading (boolean)
   - error (string)
- [ ] 6. Create useEffect to fetch all data on mount
- [ ] 7. Fetch user info, consent status, and recommendations in parallel
- [ ] 8. Update state with responses

### Consent Toggle Component
- [ ] 9. Create `frontend/src/components/ConsentToggle.jsx`
- [ ] 10. Accept props: consentStatus, onToggle, loading
- [ ] 11. Use Shadcn Switch component
- [ ] 12. Display current status with icon/badge
- [ ] 13. Display last updated timestamp
- [ ] 14. On toggle:
    - Show confirmation dialog
    - If confirming grant: explain what happens
    - If confirming revoke: explain data processing stops
- [ ] 15. Call onToggle callback with action (grant/revoke)

### Consent Grant Flow
- [ ] 16. When user grants consent:
    - Call updateConsent API with action='grant'
    - Update local state
    - Fetch recommendations immediately
    - Show success message
- [ ] 17. Add loading state during API call

### Consent Revoke Flow
- [ ] 18. When user revokes consent:
    - Show warning dialog about consequences
    - Call updateConsent API with action='revoke'
    - Clear recommendations from view
    - Show informational message
- [ ] 19. Add confirmation step (require explicit click)

### No Consent State
- [ ] 20. When consent_status=false:
    - Show large call-to-action card
    - Explain benefits of granting consent
    - Show toggle to enable
    - Hide recommendations section
- [ ] 21. Use friendly, encouraging tone

### Recommendations Display
- [ ] 22. When consent_status=true and recommendations exist:
    - Display heading "Your Personalized Recommendations"
    - Show persona badge (optional, or hide from user)
    - Use RecommendationCard component (read-only version)
    - Display 3-5 recommendations
- [ ] 23. Add expand/collapse for full content

### Recommendation Card (User View)
- [ ] 24. Create user-facing version of RecommendationCard
- [ ] 25. Display:
    - Title (large, bold)
    - Content (full text, markdown formatted)
    - Rationale section (highlighted)
    - Links in metadata (if any)
- [ ] 26. No action buttons (read-only)
- [ ] 27. Style with Shadcn Card

### Empty State
- [ ] 28. When consent=true but no recommendations yet:
    - Show message "Recommendations coming soon"
    - Explain recommendations are being prepared
    - Add illustration or icon

### Page Layout
- [ ] 29. Add page header with user name
- [ ] 30. Add ConsentToggle in header area
- [ ] 31. Add recommendations section below
- [ ] 32. Use responsive layout (stack on mobile)

### Testing User Dashboard
- [ ] 33. Test with user who has consent=false
    - Verify CTA shown
    - Verify no recommendations visible
- [ ] 34. Test granting consent via toggle
    - Verify confirmation dialog
    - Verify API called
    - Verify recommendations fetched
- [ ] 35. Test with user who has consent=true
    - Verify recommendations displayed
    - Verify content readable
    - Verify rationales visible
- [ ] 36. Test revoking consent
    - Verify warning shown
    - Verify recommendations hidden after revoke
- [ ] 37. Test responsive layout on mobile
