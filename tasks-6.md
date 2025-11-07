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
- [ ] 1. In recommendations router, create POST `/{recommendation_id}/approve` endpoint
- [ ] 2. Accept recommendation_id as path parameter
- [ ] 3. Accept ApproveRequest schema in body:
   - operator_id: str
   - notes: str (optional)
- [ ] 4. Get database session

### Validation
- [ ] 5. Query Recommendation by recommendation_id
- [ ] 6. If not found → 404 error
- [ ] 7. If already approved → 400 error with message
- [ ] 8. If status is 'rejected' → 400 error (can't approve rejected rec)

### Update Recommendation
- [ ] 9. Update recommendation:
   - Set status='approved'
   - Set approved_by=operator_id
   - Set approved_at=current timestamp
- [ ] 10. Commit transaction

### Log Operator Action
- [ ] 11. Create OperatorAction record:
   - operator_id
   - action_type='approve'
   - recommendation_id
   - user_id (from recommendation)
   - reason=notes (if provided)
   - timestamp=now
- [ ] 12. Commit transaction

### Response
- [ ] 13. Query updated recommendation
- [ ] 14. Return recommendation with updated status
- [ ] 15. Return 200 status code

### Error Handling
- [ ] 16. Handle not found → 404
- [ ] 17. Handle invalid state transitions → 400
- [ ] 18. Handle database errors → 500
- [ ] 19. Add logging for all approve actions

### Testing Approve
- [ ] 20. Generate recommendations for test user
- [ ] 21. Get pending recommendation ID
- [ ] 22. Call approve endpoint with operator_id
- [ ] 23. Verify status changed to 'approved'
- [ ] 24. Verify approved_by and approved_at set
- [ ] 25. Verify operator_actions table has record
- [ ] 26. Verify user can now see recommendation via GET endpoint

---

## PR #24: Override & Reject Endpoints

### Override Endpoint
- [ ] 1. Create POST `/{recommendation_id}/override` endpoint
- [ ] 2. Accept recommendation_id as path parameter
- [ ] 3. Accept OverrideRequest schema in body:
   - operator_id: str
   - new_title: str (optional)
   - new_content: str (optional)
   - reason: str (required)
- [ ] 4. Get database session

### Override Validation
- [ ] 5. Query Recommendation by ID
- [ ] 6. If not found → 404
- [ ] 7. Validate at least one of new_title or new_content provided → 400 if neither

### Store Original Content
- [ ] 8. Create original_content dict with:
   - original_title
   - original_content
   - overridden_at timestamp
- [ ] 9. Convert to JSON string
- [ ] 10. Store in recommendation.original_content field

### Update Recommendation
- [ ] 11. Update recommendation:
   - Set status='overridden'
   - Update title if new_title provided
   - Update content if new_content provided
   - Append disclosure to new content if modified
   - Set override_reason=reason
   - Validate new content tone if modified
- [ ] 12. If tone validation fails → 400 error
- [ ] 13. Commit transaction

### Log Override Action
- [ ] 14. Create OperatorAction record with action_type='override'
- [ ] 15. Include reason in operator action
- [ ] 16. Commit transaction

### Override Response
- [ ] 17. Return updated recommendation with:
   - New content
   - original_content field
   - override_reason
- [ ] 18. Return 200 status code

### Reject Endpoint
- [ ] 19. Create POST `/{recommendation_id}/reject` endpoint
- [ ] 20. Accept recommendation_id and RejectRequest schema:
   - operator_id: str
   - reason: str (required)

### Reject Implementation
- [ ] 21. Query Recommendation by ID
- [ ] 22. If not found → 404
- [ ] 23. If already approved and visible to user → 400 (shouldn't reject approved recs)
- [ ] 24. Update status='rejected'
- [ ] 25. Set metadata with rejection reason
- [ ] 26. Commit transaction

### Log Reject Action
- [ ] 27. Create OperatorAction record with action_type='reject'
- [ ] 28. Include reason
- [ ] 29. Commit transaction
- [ ] 30. Return updated recommendation

### Error Handling
- [ ] 31. Handle all validation errors with appropriate messages
- [ ] 32. Add logging for override and reject actions
- [ ] 33. Test both endpoints via API

### Testing Override & Reject
- [ ] 34. Test override with new title and content
- [ ] 35. Verify original content preserved
- [ ] 36. Verify tone validation on new content
- [ ] 37. Test reject with pending recommendation
- [ ] 38. Verify can't reject approved recommendation
- [ ] 39. Verify operator actions logged

---

## PR #25: Bulk Approve Endpoint

### Bulk Approve Endpoint
- [ ] 1. Create POST `/bulk-approve` endpoint
- [ ] 2. Accept BulkApproveRequest schema:
   - operator_id: str
   - recommendation_ids: list[str]
- [ ] 3. Get database session

### Bulk Processing
- [ ] 4. Initialize counters: approved=0, failed=0, errors=[]
- [ ] 5. Loop through recommendation_ids:
   - Query recommendation by ID
   - Skip if not found (log as failed)
   - Skip if not in pending_approval status (log as failed)
   - Update status='approved'
   - Set approved_by and approved_at
   - Create OperatorAction record
   - Increment approved counter
   - Catch and log any errors per recommendation

### Batch Commit
- [ ] 6. After loop, commit all changes in single transaction
- [ ] 7. If commit fails, rollback and return error
- [ ] 8. If partial success, commit what succeeded

### Response
- [ ] 9. Return BulkApproveResponse with:
   - approved: count
   - failed: count
   - errors: list of error messages
- [ ] 10. Return 200 if any succeeded, 400 if all failed

### Error Handling
- [ ] 11. Handle individual recommendation errors gracefully
- [ ] 12. Don't fail entire batch if one fails
- [ ] 13. Provide detailed error messages per failed ID
- [ ] 14. Add comprehensive logging

### Testing Bulk Approve
- [ ] 15. Generate 10 recommendations for test user
- [ ] 16. Get list of pending recommendation IDs
- [ ] 17. Call bulk approve with all IDs
- [ ] 18. Verify all changed to approved
- [ ] 19. Test with mix of valid and invalid IDs
- [ ] 20. Verify partial success handled correctly
- [ ] 21. Verify error messages informative

---

## PR #26: Frontend - Approval Queue Page

### Approval Queue Data Fetching
- [ ] 1. Update `frontend/src/pages/OperatorApprovalQueue.jsx`
- [ ] 2. Import useState, useEffect
- [ ] 3. Import API functions: getApprovalQueue, approveRecommendation, bulkApprove, etc.
- [ ] 4. Create state variables:
   - recommendations (array)
   - selectedIds (Set)
   - loading (boolean)
   - error (string)
   - filter (status filter)

### Fetch Pending Recommendations
- [ ] 5. Create useEffect to fetch on mount
- [ ] 6. Call getApprovalQueue(status='pending_approval')
- [ ] 7. Update recommendations state
- [ ] 8. Handle loading and error states

### Recommendation Card Component
- [ ] 9. Create `frontend/src/components/RecommendationCard.jsx`
- [ ] 10. Accept props: recommendation, onApprove, onReject, onOverride, onSelect
- [ ] 11. Use Shadcn Card component
- [ ] 12. Display:
    - Checkbox for selection (left side)
    - Recommendation title (large text)
    - User name and persona badge
    - Content preview (first 150 chars)
    - Rationale preview
    - Generated date
    - Action buttons: Approve, Reject, Override
- [ ] 13. Style with Tailwind

### Bulk Selection
- [ ] 14. Add "Select All" checkbox in page header
- [ ] 15. Bind to state that selects/deselects all visible recommendations
- [ ] 16. Update selectedIds state when individual checkboxes clicked
- [ ] 17. Show count of selected items in header

### Bulk Approve Button
- [ ] 18. Add "Bulk Approve" button in header (primary button)
- [ ] 19. Disable if selectedIds.length === 0
- [ ] 20. On click:
    - Call bulkApprove API with selectedIds array
    - Show loading spinner
    - On success: refetch recommendations, clear selection, show success toast
    - On error: show error message
- [ ] 21. Use Shadcn Button component

### Individual Approve
- [ ] 22. Handle individual approve button click:
    - Call approveRecommendation API with rec ID and operator ID
    - On success: remove from list or update status, show success toast
    - On error: show error toast
- [ ] 23. Add loading state per recommendation

### Override Dialog
- [ ] 24. Create override dialog using Shadcn Dialog component
- [ ] 25. Include form fields:
    - New title (optional text input)
    - New content (optional textarea)
    - Reason (required textarea)
- [ ] 26. On submit:
    - Call override API endpoint
    - Close dialog
    - Refetch recommendations
    - Show success toast
- [ ] 27. Add validation: require reason field

### Reject Dialog
- [ ] 28. Create reject dialog similar to override
- [ ] 29. Include single field: Reason (required textarea)
- [ ] 30. On submit:
    - Call reject API endpoint
    - Remove from queue
    - Show success toast

### Page Layout
- [ ] 31. Add page header with title "Approval Queue"
- [ ] 32. Add toolbar with:
    - Select All checkbox
    - Selected count display
    - Bulk Approve button
- [ ] 33. Add filter dropdown for status (future: allow viewing rejected, etc.)
- [ ] 34. Add recommendation cards in grid/list layout
- [ ] 35. Add empty state if no pending recommendations

### Loading & Error States
- [ ] 36. Show skeleton cards while loading
- [ ] 37. Show error alert if fetch fails
- [ ] 38. Add retry button in error state
- [ ] 39. Show success/error toasts for actions

### Auto-refresh
- [ ] 40. Add auto-refresh every 30 seconds (or add manual refresh button)
- [ ] 41. Implement using setInterval in useEffect
- [ ] 42. Clear interval on unmount

### Testing Approval Queue
- [ ] 43. Generate recommendations for multiple users
- [ ] 44. Navigate to approval queue
- [ ] 45. Verify all pending recommendations shown
- [ ] 46. Test individual approve (verify removed from queue)
- [ ] 47. Test bulk approve with 5+ selected
- [ ] 48. Test override with new content
- [ ] 49. Test reject with reason
- [ ] 50. Verify all actions reflected in database
- [ ] 51. Verify operator actions logged

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
