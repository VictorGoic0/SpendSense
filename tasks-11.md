## PR #42: Hybrid Recommendation Engine (Education + Products)

**Goal**: Update recommendation engine to generate combined recommendations (2-3 educational + 1-2 product offers).

### Update Pydantic Schemas
- [ ] 1. Update `backend/app/schemas.py`
- [ ] 2. Create `ProductOfferBase` schema:
  - [ ] 3. product_name: str
  - [ ] 4. product_type: str
  - [ ] 5. category: str
  - [ ] 6. short_description: str
  - [ ] 7. benefits: list[str]
  - [ ] 8. typical_apy_or_fee: Optional[str]
  - [ ] 9. partner_link: Optional[str]
  - [ ] 10. disclosure: str
  - [ ] 11. partner_name: str
- [ ] 12. Create `ProductOfferResponse` schema (extends ProductOfferBase):
  - [ ] 13. product_id: str
  - [ ] 14. persona_targets: list[str]
  - [ ] 15. active: bool
  - [ ] 16. Add Config class with from_attributes=True
- [ ] 17. Update `RecommendationResponse` schema:
  - [ ] 18. Add content_type: str field ('education' or 'partner_offer')
  - [ ] 19. Make content field optional (only for education)
  - [ ] 20. Add optional product fields:
    - [ ] 21. product_id: Optional[str]
    - [ ] 22. product_name: Optional[str]
    - [ ] 23. short_description: Optional[str]
    - [ ] 24. benefits: Optional[list[str]]
    - [ ] 25. partner_link: Optional[str]
    - [ ] 26. disclosure: Optional[str]
  - [ ] 27. Keep existing common fields (rationale, status, persona_type, etc.)

### Enhanced Recommendation Engine
- [ ] 28. Update `backend/app/services/recommendation_engine.py`
- [ ] 29. Import product_matcher functions
- [ ] 30. Import guardrails eligibility functions
- [ ] 31. Create `generate_combined_recommendations(db, user_id: str, persona_type: str, window_days: int) -> list[dict]` function:
- [ ] 32. **Step 1: Generate educational recommendations**
  - [ ] 33. Call existing OpenAI generation logic
  - [ ] 34. Target: 2-3 educational recommendations
  - [ ] 35. Set content_type = 'education' on each
- [ ] 36. **Step 2: Generate product recommendations**
  - [ ] 37. Get user features for window_days
  - [ ] 38. Call `match_products()` from product_matcher
  - [ ] 39. Get top 3 matched products with scores
  - [ ] 40. Apply eligibility filtering
  - [ ] 41. Take top 1-2 eligible products
  - [ ] 42. Set content_type = 'partner_offer' on each
  - [ ] 43. Format product data for recommendation structure
- [ ] 44. **Step 3: Combine and format**
  - [ ] 45. Merge educational and product recommendations into single list
  - [ ] 46. Target total: 3-5 recommendations (2-3 education + 1-2 products)
  - [ ] 47. Add metadata fields (recommendation_id, user_id, generated_at, etc.)
  - [ ] 48. Return combined list
- [ ] 49. Add logging for recommendation mix (X education, Y products)

### Store Product Recommendations in Database
- [ ] 50. Update recommendation storage logic
- [ ] 51. For partner_offer recommendations:
  - [ ] 52. Store product_id in new field (add to recommendations table)
  - [ ] 53. Store content_type field
  - [ ] 54. Store product data as JSON in content field (or separate fields)
- [ ] 55. Add database migration if new fields needed:
  - [ ] 56. ALTER TABLE recommendations ADD COLUMN content_type TEXT DEFAULT 'education'
  - [ ] 57. ALTER TABLE recommendations ADD COLUMN product_id TEXT
  - [ ] 58. Add foreign key relationship to product_offers if desired
- [ ] 59. Update recommendation query logic to handle both types

### Update Recommendation Generation Endpoint
- [ ] 60. Update `backend/app/routers/recommendations.py`
- [ ] 61. Modify `POST /recommendations/generate/{user_id}` endpoint:
  - [ ] 62. Replace old generation logic with `generate_combined_recommendations()`
  - [ ] 63. Store both education and product recommendations
  - [ ] 64. Return combined list in response
  - [ ] 65. Add content_type to response JSON
- [ ] 66. Update `GET /recommendations/{user_id}` endpoint:
  - [ ] 67. Include content_type in response
  - [ ] 68. Include product data for partner_offer recommendations
  - [ ] 69. Format benefits and persona_targets as arrays (parse JSON)

### Testing Hybrid Engine
- [ ] 70. Create `scripts/test_hybrid_recommendations.py`
- [ ] 71. Test with high_utilization user:
  - [ ] 72. Generate combined recommendations
  - [ ] 73. Verify 2-3 educational recs present
  - [ ] 74. Verify 1-2 product recs present
  - [ ] 75. Verify balance transfer card included in products
  - [ ] 76. Verify all products pass eligibility checks
  - [ ] 77. Print full recommendation list
- [ ] 78. Test with savings_builder user:
  - [ ] 79. Generate recommendations
  - [ ] 80. Verify HYSA products included
  - [ ] 81. If user has existing HYSA, verify it's excluded
- [ ] 82. Test with variable_income user:
  - [ ] 83. Verify budgeting app products included
- [ ] 84. Test with subscription_heavy user:
  - [ ] 85. Verify subscription manager products included
- [ ] 86. Test with wealth_builder user:
  - [ ] 87. Verify investment products included
- [ ] 88. Test edge case: no eligible products
  - [ ] 89. Verify only educational recommendations returned
  - [ ] 90. Verify no errors thrown
- [ ] 91. Verify recommendation storage in database
- [ ] 92. Verify content_type field set correctly
- [ ] 93. Query recommendations via API endpoint
- [ ] 94. Verify response includes all product data

---

## PR #43: Frontend - Product Recommendation Display

**Goal**: Update frontend to display product recommendations with benefits, partner links, and disclosure text.

### Update RecommendationCard Component
- [ ] 1. Open `frontend/src/components/RecommendationCard.jsx`
- [ ] 2. Add content_type detection logic:
  - [ ] 3. Check if recommendation.content_type === 'partner_offer'
  - [ ] 4. Render different layouts based on content_type
- [ ] 5. **For education type (existing logic)**:
  - [ ] 6. Display title
  - [ ] 7. Display markdown content
  - [ ] 8. Display rationale
  - [ ] 9. Keep existing styling
- [ ] 10. **For partner_offer type (new logic)**:
  - [ ] 11. Display "Partner Offer" badge (Badge component, variant="secondary")
  - [ ] 12. Display product_name as title
  - [ ] 13. Display partner_name as subtitle
  - [ ] 14. Display short_description
  - [ ] 15. Display benefits as bulleted list:
    - [ ] 16. Use Card with light blue/purple background
    - [ ] 17. Add checkmark icon (✓) before each benefit
    - [ ] 18. Style with medium font weight
  - [ ] 19. Display typical_apy_or_fee prominently (if present)
  - [ ] 20. Add "Learn More" button:
    - [ ] 21. Link to partner_link
    - [ ] 22. Open in new tab (target="_blank", rel="noopener noreferrer")
    - [ ] 23. Style with primary color
    - [ ] 24. Add external link icon
  - [ ] 25. Display disclosure text:
    - [ ] 26. Small font size (text-xs)
    - [ ] 27. Muted color (text-gray-500)
    - [ ] 28. Italic style
    - [ ] 29. Bottom of card
  - [ ] 30. Add light blue/purple background to entire card (distinguish from education)
  - [ ] 31. Display rationale (common for both types)

### Styling Updates
- [ ] 32. Add CSS classes for product cards:
  - [ ] 33. `.product-card` with light blue background
  - [ ] 34. `.product-benefits-list` with checkmark styling
  - [ ] 35. `.product-disclosure` for small print
  - [ ] 36. `.partner-badge` for "Partner Offer" badge
- [ ] 37. Ensure responsive design (mobile-friendly)
- [ ] 38. Test dark mode compatibility (if applicable)

### Update UserDashboard
- [ ] 39. Open `frontend/src/pages/UserDashboard.jsx`
- [ ] 40. No major changes needed (RecommendationCard handles everything)
- [ ] 41. Verify recommendations list displays mix naturally
- [ ] 42. Test with sample data containing both types

### Update OperatorUserDetail
- [ ] 43. Open `frontend/src/pages/OperatorUserDetail.jsx`
- [ ] 44. Update recommendations table to show content_type column
- [ ] 45. For partner_offer rows:
  - [ ] 46. Display product_name instead of title
  - [ ] 47. Add "Product" badge or icon
  - [ ] 48. Show partner_name in additional column
- [ ] 49. Add filter dropdown (optional):
  - [ ] 50. "All Recommendations"
  - [ ] 51. "Educational Only"
  - [ ] 52. "Products Only"
  - [ ] 53. Filter state management
  - [ ] 54. Apply filter to displayed recommendations
- [ ] 55. Verify approval workflow works for product recommendations

### API Integration
- [ ] 56. Update `frontend/src/lib/api.js` if needed
- [ ] 57. Ensure recommendation fetch includes all product fields
- [ ] 58. Parse benefits and persona_targets as arrays
- [ ] 59. Handle missing optional fields gracefully

### Testing Frontend Display
- [ ] 60. Start backend server
- [ ] 61. Start frontend dev server
- [ ] 62. Generate recommendations for test user (with products)
- [ ] 63. Navigate to User Dashboard
- [ ] 64. Verify product cards display correctly:
  - [ ] 65. "Partner Offer" badge visible
  - [ ] 66. Product name and description shown
  - [ ] 67. Benefits list formatted nicely with checkmarks
  - [ ] 68. "Learn More" button present and links correctly
  - [ ] 69. Disclosure text visible at bottom
  - [ ] 70. Light blue background distinguishes from education cards
- [ ] 71. Verify educational cards still display correctly (no regression)
- [ ] 72. Click "Learn More" button, verify new tab opens
- [ ] 73. Test on mobile viewport (responsive)
- [ ] 74. Navigate to Operator User Detail
- [ ] 75. Verify product recommendations shown in table
- [ ] 76. Verify content_type column correct
- [ ] 77. Test filter dropdown (if implemented)
- [ ] 78. Test approval workflow for product recommendation

---

## PR #44: Product Management API (Optional)

**Goal**: Add operator-facing API endpoints to manage product catalog (CRUD operations).

### Products Router
- [ ] 1. Create `backend/app/routers/products.py`
- [ ] 2. Create APIRouter with prefix="/products"
- [ ] 3. Import ProductOffer model and schemas
- [ ] 4. Import database dependency

### List Products Endpoint
- [ ] 5. Create `GET /` endpoint:
  - [ ] 6. Accept query parameters: active_only (bool), category (str), persona_type (str)
  - [ ] 7. Query product_offers table with filters
  - [ ] 8. Parse JSON fields (persona_targets, benefits)
  - [ ] 9. Return list of ProductOfferResponse
  - [ ] 10. Add pagination (skip, limit)
- [ ] 11. Add OpenAPI documentation and examples

### Get Single Product Endpoint
- [ ] 12. Create `GET /{product_id}` endpoint:
  - [ ] 13. Query product by product_id
  - [ ] 14. Return 404 if not found
  - [ ] 15. Parse JSON fields
  - [ ] 16. Return ProductOfferResponse

### Create Product Endpoint
- [ ] 17. Create `POST /` endpoint:
  - [ ] 18. Accept ProductOfferBase in request body
  - [ ] 19. Generate product_id (prod_XXX format)
  - [ ] 20. Convert persona_targets to JSON string
  - [ ] 21. Convert benefits to JSON string
  - [ ] 22. Create ProductOffer model instance
  - [ ] 23. Save to database
  - [ ] 24. Return 201 with created product

### Update Product Endpoint
- [ ] 25. Create `PUT /{product_id}` endpoint:
  - [ ] 26. Accept ProductOfferBase in request body
  - [ ] 27. Query existing product by product_id
  - [ ] 28. Return 404 if not found
  - [ ] 29. Update fields from request body
  - [ ] 30. Update updated_at timestamp
  - [ ] 31. Commit changes
  - [ ] 32. Return updated ProductOfferResponse

### Deactivate Product Endpoint
- [ ] 33. Create `DELETE /{product_id}` endpoint:
  - [ ] 34. Query product by product_id
  - [ ] 35. Return 404 if not found
  - [ ] 36. Set active = False (soft delete)
  - [ ] 37. Update updated_at timestamp
  - [ ] 38. Commit changes
  - [ ] 39. Return 204 No Content

### Router Registration
- [ ] 40. Update `backend/app/main.py`
- [ ] 41. Import products router
- [ ] 42. Include router with tag="products"

### Testing Product API
- [ ] 43. Start backend server
- [ ] 44. Open Swagger UI at /docs
- [ ] 45. Test GET /products (list all)
- [ ] 46. Verify all products returned
- [ ] 47. Test GET /products?category=balance_transfer
- [ ] 48. Verify filtered results
- [ ] 49. Test GET /products/{product_id}
- [ ] 50. Verify single product returned
- [ ] 51. Test POST /products with new product data
- [ ] 52. Verify product created
- [ ] 53. Test PUT /products/{product_id} with updated data
- [ ] 54. Verify product updated
- [ ] 55. Test DELETE /products/{product_id}
- [ ] 56. Verify product deactivated (active=False)
- [ ] 57. Test error cases (invalid product_id, missing fields)

---

## PR #45: Unit Tests & Documentation

**Goal**: Add comprehensive unit tests for product matching and eligibility, update documentation.

### Unit Tests - Product Matching
- [ ] 1. Create `backend/tests/test_product_matcher.py`
- [ ] 2. Create test fixtures:
  - [ ] 3. Sample products (balance transfer, HYSA, budgeting app, etc.)
  - [ ] 4. Sample user features for each persona type
  - [ ] 5. Sample accounts with different types
- [ ] 6. Test `calculate_relevance_score()`:
  - [ ] 7. High utilization user + balance transfer card → score >= 0.8
  - [ ] 8. Low utilization user + balance transfer card → score <= 0.5
  - [ ] 9. High savings user + HYSA → score >= 0.7
  - [ ] 10. User with existing HYSA + HYSA product → score <= 0.3
  - [ ] 11. Variable income user + budgeting app → score >= 0.7
  - [ ] 12. Stable income user + budgeting app → score <= 0.5
  - [ ] 13. Subscription heavy user + subscription manager → score >= 0.7
  - [ ] 14. Wealth builder + investment product → score >= 0.8
- [ ] 15. Test `generate_product_rationale()`:
  - [ ] 16. Verify balance transfer rationale includes utilization %
  - [ ] 17. Verify HYSA rationale includes savings amount and APY
  - [ ] 18. Verify budgeting app rationale includes buffer days or variability
  - [ ] 19. Verify subscription manager rationale includes merchant count
  - [ ] 20. Verify investment rationale includes income and emergency fund
- [ ] 21. Test `match_products()`:
  - [ ] 22. Returns 1-3 products
  - [ ] 23. Products match user's persona
  - [ ] 24. Products ordered by relevance score descending
  - [ ] 25. Low-relevance products (<0.5) filtered out

### Unit Tests - Product Eligibility
- [ ] 26. Create `backend/tests/test_product_eligibility.py`
- [ ] 27. Test income requirement:
  - [ ] 28. User income $5k, product min $10k → not eligible
  - [ ] 29. User income $10k, product min $5k → eligible
- [ ] 30. Test credit utilization requirement:
  - [ ] 31. User 90% utilization, product max 85% → not eligible
  - [ ] 32. User 70% utilization, product max 85% → eligible
- [ ] 33. Test existing savings requirement:
  - [ ] 34. User with savings account, product requires no savings → not eligible
  - [ ] 35. User without savings account, product requires no savings → eligible
- [ ] 36. Test existing investment requirement:
  - [ ] 37. User with investment account, product requires no investment → not eligible
  - [ ] 38. User without investment account → eligible
- [ ] 39. Test category-specific rules:
  - [ ] 40. User with 20% utilization, balance transfer card → not eligible (too low)
  - [ ] 41. User with 60% utilization, balance transfer card → eligible
- [ ] 42. Test `filter_eligible_products()`:
  - [ ] 43. Mix of eligible and ineligible products → only eligible returned
  - [ ] 44. All products ineligible → empty list returned
  - [ ] 45. All products eligible → all returned

### Integration Tests
- [ ] 46. Create `backend/tests/test_product_recommendations_integration.py`
- [ ] 47. Test full flow for high_utilization user:
  - [ ] 48. Generate combined recommendations
  - [ ] 49. Verify 2-3 educational recs
  - [ ] 50. Verify 1-2 product recs
  - [ ] 51. Verify balance transfer card included
  - [ ] 52. Verify eligibility passed
  - [ ] 53. Verify recommendations stored in database correctly
- [ ] 54. Test full flow for savings_builder with existing HYSA:
  - [ ] 55. Generate recommendations
  - [ ] 56. Verify HYSA product filtered out
  - [ ] 57. Verify other products still present
- [ ] 58. Test end-to-end via API:
  - [ ] 59. POST /recommendations/generate/{user_id}
  - [ ] 60. Verify response contains both content types
  - [ ] 61. Verify product data complete
  - [ ] 62. GET /recommendations/{user_id}
  - [ ] 63. Verify stored recommendations include products

### Run All Tests
- [ ] 64. Run test suite: `pytest backend/tests/ -v`
- [ ] 65. Verify all tests pass (target: 20+ new tests)
- [ ] 66. Check test coverage: `pytest --cov=backend/app/services`
- [ ] 67. Aim for >80% coverage on new services (product_matcher, eligibility)

### Documentation Updates
- [ ] 68. Update `README.md`:
  - [ ] 69. Add "Product Recommendations" section
  - [ ] 70. Document product catalog generation: `python scripts/generate_product_catalog.py`
  - [ ] 71. Document product seeding: `python scripts/seed_product_catalog.py`
  - [ ] 72. Explain product matching logic
  - [ ] 73. Explain eligibility filtering
- [ ] 74. Update `docs/DECISIONS.md`:
  - [ ] 75. Add entry: "Product Recommendations via LLM-Generated Catalog"
  - [ ] 76. Rationale: Faster than manual research, realistic data, easy to regenerate
  - [ ] 77. Trade-offs: Fake partner links, rates may be outdated, need disclaimers
  - [ ] 78. Future: Real partner integrations
- [ ] 79. Update `docs/LIMITATIONS.md`:
  - [ ] 80. Add entry: "Product Recommendations"
  - [ ] 81. Limitation: LLM-generated products, placeholder partner links
  - [ ] 82. Impact: Users cannot sign up through platform
  - [ ] 83. Recommendation: Integrate with real APIs (CardRatings, DepositAccounts, Plaid)
- [ ] 84. Create `docs/PRODUCT_CATALOG.md`:
  - [ ] 85. Document product catalog structure
  - [ ] 86. Document eligibility criteria
  - [ ] 87. Document matching algorithm
  - [ ] 88. Document category-specific scoring rules
  - [ ] 89. Add examples of products per persona
  - [ ] 90. Document future enhancements (real partners, A/B testing, click tracking)

---

## Summary

**Total Tasks**: 410+ subtasks across 8 PRs
**Expected Timeline**: 4-6 hours
**Expected Cost**: ~$0.20 for product generation (one-time)

**Key Features Delivered**:
- ✅ Product catalog with 20-25 realistic products (LLM-generated)
- ✅ Product seeding into database
- ✅ Product matching service (persona + signal based)
- ✅ Eligibility filtering (income, utilization, existing accounts)
- ✅ Hybrid recommendation engine (2-3 education + 1-2 products)
- ✅ Frontend display with benefits, partner links, disclosure
- ✅ 20+ unit tests covering product matching and eligibility
- ✅ Optional: Product management API for operators

**Success Criteria**:
- Product catalog generated and seeded ✓
- Users receive 3-5 total recommendations (mix of education + products) ✓
- Products matched based on persona and relevance ✓
- Ineligible products filtered out ✓
- UI displays product offers distinctly from education ✓
- Disclosure text present on all product offers ✓
- Comprehensive test coverage (80%+) ✓

**Post-MVP Enhancements**:
- Real partner integrations and affiliate links
- Click tracking and conversion analytics
- A/B testing framework (products vs. no products)
- Machine learning for product matching
- Product comparison tool
- Real-time product availability checks

---

**End of Tasks - Part 10**

## Project Complete! 🎉
You now have a fully functional SpendSense MVP with:
- ✅ Synthetic data generation (75 users)
- ✅ Feature detection (4 signal types)
- ✅ Persona assignment (5 personas)
- ✅ AI-powered recommendations (OpenAI GPT-4o-mini)
- ✅ Approval workflow with guardrails
- ✅ Full-stack web application (React + FastAPI)
- ✅ Evaluation system with S3 exports
- ✅ AWS Lambda deployment
- ✅ 10+ unit tests
- ✅ Comprehensive documentation
Total development time: ~20 hours over 2-4 days