## PR #42: Hybrid Recommendation Engine (Education + Products)

**Goal**: Update recommendation engine to generate combined recommendations (2-3 educational + 1-2 product offers).

### Update Pydantic Schemas
- [x] 1. Update `backend/app/schemas.py`
- [x] 2. Create `ProductOfferBase` schema:
  - [x] 3. product_name: str
  - [x] 4. product_type: str
  - [x] 5. category: str
  - [x] 6. short_description: str
  - [x] 7. benefits: list[str]
  - [x] 8. typical_apy_or_fee: Optional[str]
  - [x] 9. partner_link: Optional[str]
  - [x] 10. disclosure: str
  - [x] 11. partner_name: str
- [x] 12. Create `ProductOfferResponse` schema (extends ProductOfferBase):
  - [x] 13. product_id: str
  - [x] 14. persona_targets: list[str]
  - [x] 15. active: bool
  - [x] 16. Add Config class with from_attributes=True
- [x] 17. Update `RecommendationResponse` schema:
  - [x] 18. Add content_type: str field ('education' or 'partner_offer')
  - [x] 19. Make content field optional (only for education)
  - [x] 20. Add optional product fields:
    - [x] 21. product_id: Optional[str]
    - [x] 22. product_name: Optional[str]
    - [x] 23. short_description: Optional[str]
    - [x] 24. benefits: Optional[list[str]]
    - [x] 25. partner_link: Optional[str]
    - [x] 26. disclosure: Optional[str]
  - [x] 27. Keep existing common fields (rationale, status, persona_type, etc.)

### Enhanced Recommendation Engine
- [x] 28. Update `backend/app/services/recommendation_engine.py`
- [x] 29. Import product_matcher functions
- [x] 30. Import guardrails eligibility functions
- [x] 31. Create `generate_combined_recommendations(db, user_id: str, persona_type: str, window_days: int) -> list[dict]` function:
- [x] 32. **Step 1: Generate educational recommendations**
  - [x] 33. Call existing OpenAI generation logic
  - [x] 34. Target: 2-3 educational recommendations
  - [x] 35. Set content_type = 'education' on each
- [x] 36. **Step 2: Generate product recommendations**
  - [x] 37. Get user features for window_days
  - [x] 38. Call `match_products()` from product_matcher
  - [x] 39. Get top 3 matched products with scores
  - [x] 40. Apply eligibility filtering
  - [x] 41. Take top 1-2 eligible products
  - [x] 42. Set content_type = 'partner_offer' on each
  - [x] 43. Format product data for recommendation structure
- [x] 44. **Step 3: Combine and format**
  - [x] 45. Merge educational and product recommendations into single list
  - [x] 46. Target total: 3-5 recommendations (2-3 education + 1-2 products)
  - [x] 47. Add metadata fields (recommendation_id, user_id, generated_at, etc.)
  - [x] 48. Return combined list
- [x] 49. Add logging for recommendation mix (X education, Y products)

### Store Product Recommendations in Database
- [x] 50. Update recommendation storage logic
- [x] 51. For partner_offer recommendations:
  - [x] 52. Store product_id in new field (add to recommendations table)
  - [x] 53. Store content_type field
  - [x] 54. Store product data as JSON in content field (or separate fields)
- [x] 55. Add database migration if new fields needed:
  - [x] 56. ALTER TABLE recommendations ADD COLUMN content_type TEXT DEFAULT 'education'
  - [x] 57. ALTER TABLE recommendations ADD COLUMN product_id TEXT
  - [x] 58. Add foreign key relationship to product_offers if desired
- [x] 59. Update recommendation query logic to handle both types

### Update Recommendation Generation Endpoint
- [x] 60. Update `backend/app/routers/recommendations.py`
- [x] 61. Modify `POST /recommendations/generate/{user_id}` endpoint:
  - [x] 62. Replace old generation logic with `generate_combined_recommendations()`
  - [x] 63. Store both education and product recommendations
  - [x] 64. Return combined list in response
  - [x] 65. Add content_type to response JSON
- [x] 66. Update `GET /recommendations/{user_id}` endpoint:
  - [x] 67. Include content_type in response
  - [x] 68. Include product data for partner_offer recommendations
  - [x] 69. Format benefits and persona_targets as arrays (parse JSON)

### Testing Hybrid Engine
- [x] 70. Create `scripts/test_hybrid_recommendations.py`
- [x] 71. Test with high_utilization user:
  - [x] 72. Generate combined recommendations
  - [x] 73. Verify 2-3 educational recs present
  - [x] 74. Verify 1-2 product recs present
  - [x] 75. Verify balance transfer card included in products
  - [x] 76. Verify all products pass eligibility checks
  - [x] 77. Print full recommendation list
- [x] 78. Test with savings_builder user:
  - [x] 79. Generate recommendations
  - [x] 80. Verify HYSA products included
  - [x] 81. If user has existing HYSA, verify it's excluded
- [x] 82. Test with variable_income user:
  - [x] 83. Verify budgeting app products included
- [x] 84. Test with subscription_heavy user:
  - [x] 85. Verify subscription manager products included
- [x] 86. Test with wealth_builder user:
  - [x] 87. Verify investment products included
- [x] 88. Test edge case: no eligible products
  - [x] 89. Verify only educational recommendations returned
  - [x] 90. Verify no errors thrown`
- [x] 91. Verify recommendation storage in database
- [x] 92. Verify content_type field set correctly
- [x] 93. Query recommendations via API endpoint
- [x] 94. Verify response includes all product data

### Product Catalog Data Normalization
- [x] 95. Regenerate product catalog with ~150 products (instead of ~25)
- [x] 96. Modify `scripts/generate_product_catalog.py`:
  - [x] 97. Revert prompt changes (remove explicit eligibility rules from LLM prompt)
  - [x] 98. Implement batch generation (5 batches of ~30 products each)
  - [x] 99. Add `generate_product_catalog_batch()` function for individual LLM calls
- [x] 100. Apply deterministic eligibility rules post-LLM generation:
  - [x] 101. Set `requires_no_existing_savings = TRUE` only for HYSA products
  - [x] 102. Set `requires_no_existing_investment = TRUE` only for investment/robo_advisor products
  - [x] 103. Set `min_income`, `max_credit_utilization`, `min_credit_score` deterministically based on category
  - [x] 104. Use random values within specified ranges for numeric eligibility fields
- [x] 105. Add "loan" as valid product_type:
  - [x] 106. Update `backend/app/models.py` ProductOffer model (add "loan" to CheckConstraint)
  - [x] 107. Update `backend/app/schemas.py` ProductBase schema (add "loan" to Literal)
  - [x] 108. Update `scripts/generate_product_catalog.py` type_mapping (map personal_loan, debt_consolidation, credit_builder to "loan")
- [x] 109. Make recommendations.content nullable:
  - [x] 110. Update `backend/app/models.py` Recommendation model (content = Column(Text, nullable=True))
  - [x] 111. Update `backend/app/schemas.py` RecommendationBase schema (content: Optional[str])
- [x] 112. Consolidate database migrations:
  - [x] 113. Add `apply_migrations()` function to `backend/app/database.py`
  - [x] 114. Automatically apply `product_id` column migration on startup
  - [x] 115. Document that content nullable and loan product_type migrations already applied
  - [x] 116. Remove temporary migration scripts (migrate_add_product_id.py, migrate_add_loan_product_type.py, migrate_make_content_nullable.py)
- [x] 117. Remove refresh_product_catalog.py script (one-time use complete)
- [x] 118. Verify product catalog generation produces ~150 products with correct eligibility flags
- [x] 119. Verify all products have sensible eligibility criteria (no subscription apps requiring no savings)

---

## PR #43: Frontend - Product Recommendation Display

**Goal**: Create separate card components for product recommendations to avoid layout issues. Different cards for Approval Queue, User Dashboard, and Operator Dashboard.

### Create ProductRecommendationCard for Approval Queue
- [x] 1. Create `frontend/src/components/ProductRecommendationCard.jsx` (for approval queue)
- [x] 2. Base it on RecommendationCard structure
- [x] 3. Display product_name instead of title in header
- [x] 4. Display product_name in "Content:" section (instead of markdown content)
- [x] 5. Display rationale in "Rationale:" section (same as education)
- [x] 6. Keep all approval workflow buttons (Approve, Reject, Override)
- [x] 7. Keep checkbox for selection
- [x] 8. Keep status badges and user info
- [x] 9. Add "Partner Offer" badge to distinguish from education

### Create ProductRecommendationCard for User Dashboard
- [x] 10. Create `frontend/src/components/UserProductRecommendationCard.jsx`
- [x] 11. Design as taller card for side-by-side display
- [x] 12. Display "Partner Offer" badge at top
- [x] 13. Display product_name as main title
- [x] 14. Display partner_name as subtitle
- [x] 15. Display short_description
- [x] 16. Display benefits as bulleted list with checkmarks (✓)
- [x] 17. Display typical_apy_or_fee prominently (if present)
- [x] 18. Add "Learn More" button:
    - [x] 19. Link to partner_link
    - [x] 20. Open in new tab (target="_blank", rel="noopener noreferrer")
    - [x] 21. Add external link icon
- [x] 22. Display disclosure text at bottom (small, muted, italic)
- [x] 23. Display rationale in blue box (same style as education)
- [x] 24. Use light blue/purple background to distinguish from education
- [x] 25. Make card taller to accommodate all product info

### Update UserDashboard
- [x] 26. Open `frontend/src/pages/UserDashboard.jsx`
- [x] 27. Separate educational and product recommendations
- [x] 28. Display educational recommendations in existing grid layout
- [x] 29. Create separate section for product recommendations
- [x] 30. Display product cards side-by-side in grid (2 columns on desktop)
- [x] 31. Use UserProductRecommendationCard for products
- [x] 32. Use UserRecommendationCard for education (no changes)
- [x] 33. Add section headers: "Educational Recommendations" and "Product Recommendations"

### Update OperatorUserDetail
- [x] 34. Open `frontend/src/pages/OperatorUserDetail.jsx`
- [x] 35. Keep same card width and layout structure
- [x] 36. Detect content_type for each recommendation
- [x] 37. For partner_offer recommendations:
  - [x] 38. Display product_name instead of title
  - [x] 39. Display short_description instead of content
  - [x] 40. Handle "Show more" for products:
    - [x] 41. Show short_description initially
    - [x] 42. On expand, show full product details (benefits, APY, partner info)
    - [x] 43. May need to show structured data (benefits list) instead of just text
- [x] 44. Add "Partner Offer" badge for product recommendations
- [x] 45. Keep rationale display the same for both types

### Update Approval Queue
- [x] 46. Open `frontend/src/pages/OperatorApprovalQueue.jsx`
- [x] 47. Detect content_type for each recommendation
- [x] 48. Conditionally render ProductRecommendationCard for partner_offer
- [x] 49. Conditionally render RecommendationCard for education
- [x] 50. Ensure approval workflow works for both types

### API Integration
- [x] 51. Update `frontend/src/lib/api.js` if needed
- [x] 52. Ensure recommendation fetch includes all product fields
- [x] 53. Parse benefits and persona_targets as arrays
- [x] 54. Handle missing optional fields gracefully

### Testing Frontend Display
- [x] 55. Start backend server
- [x] 56. Start frontend dev server
- [x] 57. Generate recommendations for test user (with products)
- [x] 58. Navigate to User Dashboard
- [x] 59. Verify product cards display correctly:
  - [x] 60. "Partner Offer" badge visible
  - [x] 61. Product name and description shown
  - [x] 62. Benefits list formatted nicely with checkmarks
  - [x] 63. "Learn More" button present and links correctly
  - [x] 64. Disclosure text visible at bottom
  - [x] 65. Cards displayed side-by-side in separate section
  - [x] 66. Taller cards accommodate all product info
- [x] 67. Verify educational cards still display correctly (no regression)
- [x] 68. Click "Learn More" button, verify new tab opens
- [x] 69. Test on mobile viewport (responsive)
- [x] 70. Navigate to Operator User Detail
- [x] 71. Verify product recommendations shown with product_name
- [x] 72. Verify "Show more" works for product structured data
- [x] 73. Navigate to Approval Queue
- [x] 74. Verify product recommendations show product_name in Content section
- [x] 75. Test approval workflow for product recommendation

---

## PR #44: Product Management API (Optional)

**Goal**: Add operator-facing API endpoints to manage product catalog (CRUD operations).

### Products Router
- [x] 1. Create `backend/app/routers/products.py`
- [x] 2. Create APIRouter with prefix="/products"
- [x] 3. Import ProductOffer model and schemas
- [x] 4. Import database dependency

### List Products Endpoint
- [x] 5. Create `GET /` endpoint:
  - [x] 6. Accept query parameters: active_only (bool), category (str), persona_type (str)
  - [x] 7. Query product_offers table with filters
  - [x] 8. Parse JSON fields (persona_targets, benefits)
  - [x] 9. Return list of ProductOfferResponse
  - [x] 10. Add pagination (skip, limit)
- [x] 11. Add OpenAPI documentation and examples

### Get Single Product Endpoint
- [x] 12. Create `GET /{product_id}` endpoint:
  - [x] 13. Query product by product_id
  - [x] 14. Return 404 if not found
  - [x] 15. Parse JSON fields
  - [x] 16. Return ProductOfferResponse

### Create Product Endpoint
- [x] 17. Create `POST /` endpoint:
  - [x] 18. Accept ProductOfferBase in request body
  - [x] 19. Generate product_id (prod_XXX format)
  - [x] 20. Convert persona_targets to JSON string
  - [x] 21. Convert benefits to JSON string
  - [x] 22. Create ProductOffer model instance
  - [x] 23. Save to database
  - [x] 24. Return 201 with created product

### Update Product Endpoint
- [x] 25. Create `PUT /{product_id}` endpoint:
  - [x] 26. Accept ProductOfferBase in request body
  - [x] 27. Query existing product by product_id
  - [x] 28. Return 404 if not found
  - [x] 29. Update fields from request body
  - [x] 30. Update updated_at timestamp
  - [x] 31. Commit changes
  - [x] 32. Return updated ProductOfferResponse

### Deactivate Product Endpoint
- [x] 33. Create `DELETE /{product_id}` endpoint:
  - [x] 34. Query product by product_id
  - [x] 35. Return 404 if not found
  - [x] 36. Set active = False (soft delete)
  - [x] 37. Update updated_at timestamp
  - [x] 38. Commit changes
  - [x] 39. Return 204 No Content

### Router Registration
- [x] 40. Update `backend/app/main.py`
- [x] 41. Import products router
- [x] 42. Include router with tag="products"

### Testing Product API
- [x] 43. Start backend server
- [x] 44. Open Swagger UI at /docs
- [x] 45. Test GET /products (list all)
- [x] 46. Verify all products returned
- [x] 47. Test GET /products?category=balance_transfer
- [x] 48. Verify filtered results
- [x] 49. Test GET /products/{product_id}
- [x] 50. Verify single product returned
- [x] 51. Test POST /products with new product data
- [x] 52. Verify product created
- [x] 53. Test PUT /products/{product_id} with updated data
- [x] 54. Verify product updated
- [x] 55. Test DELETE /products/{product_id}
- [x] 56. Verify product deactivated (active=False)
- [x] 57. Test error cases (invalid product_id, missing fields)