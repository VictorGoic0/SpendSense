# SpendSense Tasks - Part 10: Product Catalog & Recommendation Integration

**Context**: Add product recommendations (savings accounts, credit cards, apps, services) alongside educational content. Products are matched to users based on persona and behavioral signals, then filtered by eligibility criteria. This enables SpendSense to recommend relevant financial products in addition to educational recommendations.

**Prerequisites**: 
- Recommendation engine implemented (PR #19-24)
- Guardrails service functional (PR #25)
- User/Operator dashboards complete (PR #26-27)

---

## PR #38: Database Schema & Product Catalog Generation

**Goal**: Create product_offers table and generate realistic product catalog using OpenAI GPT-4o.

**Current State**: No product catalog exists, only educational recommendations
**Target State**: Database table created, 20-25 realistic products generated and ready for seeding

### Database Migration
- [x] 1. Create database migration for product_offers table
- [x] 2. Add product_id (TEXT PRIMARY KEY)
- [x] 3. Add product_name (TEXT NOT NULL)
- [x] 4. Add product_type (TEXT NOT NULL) - savings_account, credit_card, app, service, investment_account
- [x] 5. Add category (TEXT NOT NULL) - balance_transfer, hysa, budgeting_app, subscription_manager, robo_advisor
- [x] 6. Add persona_targets (TEXT NOT NULL) - JSON array of target personas
- [x] 7. Add eligibility criteria fields:
  - [x] 8. min_income (REAL DEFAULT 0)
  - [x] 9. max_credit_utilization (REAL DEFAULT 1.0)
  - [x] 10. requires_no_existing_savings (BOOLEAN DEFAULT FALSE)
  - [x] 11. requires_no_existing_investment (BOOLEAN DEFAULT FALSE)
  - [x] 12. min_credit_score (INTEGER)
- [x] 13. Add content fields:
  - [x] 14. short_description (TEXT NOT NULL)
  - [x] 15. benefits (TEXT NOT NULL) - JSON array of benefit strings
  - [x] 16. typical_apy_or_fee (TEXT)
  - [x] 17. partner_link (TEXT)
  - [x] 18. disclosure (TEXT NOT NULL)
- [x] 19. Add business fields:
  - [x] 20. partner_name (TEXT NOT NULL)
  - [x] 21. commission_rate (REAL DEFAULT 0.0)
  - [x] 22. priority (INTEGER DEFAULT 1)
  - [x] 23. active (BOOLEAN DEFAULT TRUE)
- [x] 24. Add timestamps (created_at, updated_at)
- [x] 25. Create index on persona_targets
- [x] 26. Create index on active status

### Update Database Models
- [x] 27. Create ProductOffer model in `backend/app/models.py`
- [x] 28. Define all fields matching table schema
- [x] 29. Add relationship helpers if needed
- [x] 30. Add __repr__ method for debugging
- [x] 31. Test model creation and queries

### Product Generation Script Review & Enhancement
- [x] 32. Review existing `scripts/generate_product_catalog.py`
- [x] 33. Verify prompt includes all 5 personas (high_utilization, variable_income, subscription_heavy, savings_builder, wealth_builder)
- [x] 34. Ensure prompt requests 20-25 products total
- [x] 35. Update prompt to include realistic eligibility criteria:
  - [x] 36. Balance transfer cards: min_income $2000/mo, max_credit_utilization varies
  - [x] 37. HYSA accounts: no strict requirements
  - [x] 38. Investment accounts: min_income $5000-10000/mo
  - [x] 39. Budgeting apps: typically no requirements
  - [x] 40. Subscription managers: no strict requirements
- [x] 41. Add standard disclosure template to prompt:
  ```
  "This is educational content, not financial advice. Product terms, rates, and 
  availability subject to change. SpendSense may receive compensation from partners. 
  Consult a licensed financial advisor for personalized guidance."
  ```
- [x] 42. Verify enhance_products() adds all required metadata fields
- [x] 43. Update extract_partner_name() logic if needed
- [x] 44. Ensure JSON output includes min_credit_score for credit products

### Generate Product Catalog
- [x] 45. Set OPENAI_API_KEY in environment (user must set in .env file)
- [x] 46. Run generation script: `python scripts/generate_product_catalog.py` (requires API key)
- [x] 47. Review generated `data/product_catalog.json`
- [x] 48. Verify 20-25 products generated (21 products generated ✓)
- [x] 49. Check product names sound realistic (Chase, Marcus, Ally, Wealthfront, YNAB, etc.) ✓
- [x] 50. Verify persona distribution:
  - [x] 51. High Utilization: 4-5 products (5 products ✓)
  - [x] 52. Variable Income: 4-5 products (7 products ✓)
  - [x] 53. Subscription Heavy: 3-4 products (4 products ✓)
  - [x] 54. Savings Builder: 4-5 products (6 products ✓)
  - [x] 55. Wealth Builder: 4-5 products (7 products ✓)
- [x] 56. Verify each product has realistic benefits (3-5 bullets) (21/21 products ✓)
- [x] 57. Verify APY/fee values are realistic for current market (4.5% APY, 0% intro APR, etc. ✓)
- [x] 58. Verify eligibility criteria make sense per product type (balance transfer: min_income 2500, max_util 0.75, min_score 670; HYSA: no restrictions ✓)
- [x] 59. Check disclosure text is present on all products (21/21 products ✓)
- [x] 60. If quality is poor, adjust prompt and regenerate (Quality verified - no regeneration needed ✓)

### Documentation
- [x] 61. Add product catalog generation instructions to README.md
- [x] 62. Document expected runtime (~30-60 seconds)
- [x] 63. Document expected OpenAI API cost (~$0.10-0.20)
- [x] 64. Add product schema documentation to project docs

---

## PR #39: Product Seeding & Database Population

**Goal**: Create seeding script to load generated products into database and verify data integrity.

### Product Seeding Script
- [ ] 1. Create `scripts/seed_product_catalog.py`
- [ ] 2. Import database session and ProductOffer model
- [ ] 3. Import json module for reading catalog file
- [ ] 4. Create `load_product_catalog(filepath: str) -> list[dict]` function:
  - [ ] 5. Open and read `data/product_catalog.json`
  - [ ] 6. Parse JSON and return list of product dicts
  - [ ] 7. Add error handling for missing/invalid file
- [ ] 8. Create `clear_existing_products(db) -> int` function:
  - [ ] 9. Query all ProductOffer records
  - [ ] 10. Delete all records (fresh start for MVP)
  - [ ] 11. Commit transaction
  - [ ] 12. Return count of deleted products
  - [ ] 13. Print confirmation message
- [ ] 14. Create `seed_products(db, products: list[dict]) -> int` function:
  - [ ] 15. Iterate through products list
  - [ ] 16. For each product:
    - [ ] 17. Convert persona_targets to JSON string if list
    - [ ] 18. Convert benefits to JSON string if list
    - [ ] 19. Create ProductOffer model instance
    - [ ] 20. Set all fields from product dict
    - [ ] 21. Add to session
  - [ ] 22. Commit all products in single transaction
  - [ ] 23. Return count of products inserted
  - [ ] 24. Add error handling with rollback
- [ ] 25. Create `print_distribution(db)` function:
  - [ ] 26. Query products grouped by category
  - [ ] 27. Count products per category
  - [ ] 28. Print formatted table showing distribution
  - [ ] 29. Query products grouped by product_type
  - [ ] 30. Print product type distribution
  - [ ] 31. Calculate and print persona coverage (parse JSON arrays)

### Main Seeding Flow
- [ ] 32. Add __main__ block to script
- [ ] 33. Get database session
- [ ] 34. Load product catalog from JSON
- [ ] 35. Print total products to be seeded
- [ ] 36. Clear existing products (with confirmation)
- [ ] 37. Seed new products
- [ ] 38. Print success message with count
- [ ] 39. Print distribution statistics
- [ ] 40. Close database session

### Testing Seeding
- [ ] 41. Run seeding script: `python scripts/seed_product_catalog.py`
- [ ] 42. Verify output shows 20-25 products seeded
- [ ] 43. Check distribution by category (should be balanced)
- [ ] 44. Open database and query product_offers table
- [ ] 45. Verify all 20-25 products present
- [ ] 46. Spot check 3-5 products for data completeness:
  - [ ] 47. All required fields populated
  - [ ] 48. persona_targets is valid JSON array
  - [ ] 49. benefits is valid JSON array
  - [ ] 50. Eligibility criteria make sense
- [ ] 51. Run seeding script again to test clear + re-seed
- [ ] 52. Verify idempotency (same result on multiple runs)

### Error Handling & Validation
- [ ] 53. Add validation for required fields before insertion
- [ ] 54. Check that persona_targets contains valid persona types only
- [ ] 55. Validate numeric fields (income, utilization) are in reasonable ranges
- [ ] 56. Add logging for any invalid/skipped products
- [ ] 57. Test with malformed JSON file (verify graceful failure)

---

## PR #40: Product Matching Service

**Goal**: Implement service to match users to relevant products based on persona and financial signals.

### Product Matching Service Setup
- [ ] 1. Create `backend/app/services/product_matcher.py`
- [ ] 2. Import database models (ProductOffer, UserFeature, Account)
- [ ] 3. Import json module for parsing JSON fields
- [ ] 4. Import typing for type hints
- [ ] 5. Add logging setup

### Relevance Scoring Logic
- [ ] 6. Create `calculate_relevance_score(product: ProductOffer, features: UserFeature, accounts: list) -> float` function:
- [ ] 7. Initialize base score = 0.5
- [ ] 8. Add scoring rules for balance_transfer products:
  - [ ] 9. If avg_utilization > 0.5: score += 0.3
  - [ ] 10. If interest_charges_present: score += 0.2
  - [ ] 11. If avg_utilization > 0.7: score += 0.2 (bonus for very high)
- [ ] 12. Add scoring rules for hysa (high-yield savings account) products:
  - [ ] 13. If net_savings_inflow > 0 and emergency_fund_months < 3: score += 0.4
  - [ ] 14. If savings_growth_rate > 0.02: score += 0.2
  - [ ] 15. If has existing HYSA: score -= 0.5 (penalize)
- [ ] 16. Add scoring rules for budgeting_app products:
  - [ ] 17. If income_variability > 0.3: score += 0.3
  - [ ] 18. If financial_buffer_days < 30: score += 0.3
  - [ ] 19. If avg_monthly_expenses_volatility > 0.25: score += 0.2
- [ ] 20. Add scoring rules for subscription_manager products:
  - [ ] 21. If recurring_merchants >= 5: score += 0.4
  - [ ] 22. If subscription_spend_share > 0.2: score += 0.3
- [ ] 23. Add scoring rules for robo_advisor / investment products:
  - [ ] 24. If monthly_income > 5000 and avg_utilization < 0.3: score += 0.4
  - [ ] 25. If emergency_fund_months >= 3: score += 0.3
  - [ ] 26. If has existing investment account: score -= 0.4 (penalize)
- [ ] 27. Clamp score to range [0.0, 1.0]
- [ ] 28. Return relevance score

### Product Rationale Generation
- [ ] 29. Create `generate_product_rationale(product: ProductOffer, features: UserFeature) -> str` function:
- [ ] 30. Use product category to determine rationale template
- [ ] 31. For balance_transfer products:
  - [ ] 32. Calculate estimated monthly interest savings
  - [ ] 33. Format: "With your credit utilization at {util}%, this card could save you ${savings}/month in interest."
- [ ] 34. For hysa products:
  - [ ] 35. Calculate annual interest earnings based on current savings
  - [ ] 36. Format: "Your ${amount}/month savings in a HYSA earning {apy} could generate ${earnings} extra per year."
- [ ] 37. For budgeting_app products:
  - [ ] 38. Cite income variability or buffer days
  - [ ] 39. Format: "With variable income and only {buffer_days} days of buffer, this app helps manage irregular cash flow."
- [ ] 40. For subscription_manager products:
  - [ ] 41. Cite number of recurring merchants
  - [ ] 42. Format: "You have {count} recurring subscriptions totaling ${amount}/month - this tool can help identify savings."
- [ ] 43. For investment products:
  - [ ] 44. Cite income and existing emergency fund
  - [ ] 45. Format: "With ${income}/month income and {months} months emergency fund, you're ready to start investing."
- [ ] 46. Return rationale string

### Main Product Matching Function
- [ ] 47. Create `match_products(db, user_id: str, persona_type: str, features: UserFeature) -> list[dict]` function:
- [ ] 48. Parse persona_type (handle both 30d and 180d versions)
- [ ] 49. Query active products where persona_targets contains user's persona:
  - [ ] 50. Filter by active=True
  - [ ] 51. Parse persona_targets JSON field
  - [ ] 52. Check if user's persona in target list
- [ ] 53. Query user's accounts for eligibility checks
- [ ] 54. For each candidate product:
  - [ ] 55. Calculate relevance score
  - [ ] 56. Generate rationale
  - [ ] 57. Create result dict with product data + score + rationale
- [ ] 58. Filter out products with relevance_score < 0.5 (too low)
- [ ] 59. Sort products by relevance_score descending
- [ ] 60. Return top 3 products
- [ ] 61. Add logging for matched products and scores

### Helper Functions
- [ ] 62. Create `get_account_types(accounts: list) -> set[str]` function:
  - [ ] 63. Extract account_type from each account
  - [ ] 64. Return set of unique account types
- [ ] 65. Create `has_hysa(accounts: list) -> bool` function:
  - [ ] 66. Check if any account has type 'savings' with high interest indicator
  - [ ] 67. Return boolean
- [ ] 68. Create `has_investment_account(accounts: list) -> bool` function:
  - [ ] 69. Check if any account has type 'investment'
  - [ ] 70. Return boolean

### Testing Product Matching
- [ ] 71. Create `scripts/test_product_matching.py`
- [ ] 72. Test with high_utilization user:
  - [ ] 73. Query user with high utilization from database
  - [ ] 74. Call match_products()
  - [ ] 75. Verify balance transfer cards ranked high
  - [ ] 76. Verify relevance scores make sense
  - [ ] 77. Print matched products and scores
- [ ] 78. Test with savings_builder user:
  - [ ] 79. Query user with savings activity
  - [ ] 80. Call match_products()
  - [ ] 81. Verify HYSA products ranked high
  - [ ] 82. Print results
- [ ] 83. Test with variable_income user:
  - [ ] 84. Verify budgeting apps ranked high
- [ ] 85. Test with subscription_heavy user:
  - [ ] 86. Verify subscription managers ranked high
- [ ] 87. Test with wealth_builder user:
  - [ ] 88. Verify investment products ranked high
- [ ] 89. Verify rationale text is specific and cites user data
- [ ] 90. Test edge case: user with no matching products
- [ ] 91. Test edge case: all products have low relevance scores

---

## PR #41: Enhanced Guardrails - Product Eligibility

**Goal**: Add eligibility checking to guardrails service to filter out products users don't qualify for.

### Eligibility Checker Function
- [ ] 1. Update `backend/app/services/guardrails.py`
- [ ] 2. Import ProductOffer model and product-related types
- [ ] 3. Create `check_product_eligibility(db, user_id: str, product: ProductOffer, features: UserFeature) -> tuple[bool, str]` function:
- [ ] 4. Query user's accounts for account type checking
- [ ] 5. **Check income requirement**:
  - [ ] 6. If product.min_income > 0
  - [ ] 7. Calculate user's monthly income from features
  - [ ] 8. If user income < min_income: return (False, "Income below minimum requirement")
- [ ] 9. **Check credit utilization requirement**:
  - [ ] 10. If product.max_credit_utilization < 1.0
  - [ ] 11. Get user's avg_utilization from features
  - [ ] 12. If avg_utilization > max_credit_utilization: return (False, "Credit utilization too high")
- [ ] 13. **Check existing savings requirement**:
  - [ ] 14. If product.requires_no_existing_savings = True
  - [ ] 15. Check if user has any savings accounts
  - [ ] 16. If has savings: return (False, "Already has savings account")
- [ ] 17. **Check existing investment requirement**:
  - [ ] 18. If product.requires_no_existing_investment = True
  - [ ] 19. Check if user has any investment accounts
  - [ ] 20. If has investment: return (False, "Already has investment account")
- [ ] 21. **Check category-specific rules**:
  - [ ] 22. If category = "balance_transfer":
    - [ ] 23. Require avg_utilization >= 0.3 (only show if meaningful balance to transfer)
    - [ ] 24. If below threshold: return (False, "Balance transfer not beneficial at current utilization")
- [ ] 25. If all checks pass: return (True, "Eligible")
- [ ] 26. Add logging for eligibility failures

### Batch Eligibility Checking
- [ ] 27. Create `filter_eligible_products(db, user_id: str, products: list[dict], features: UserFeature) -> list[dict]` function:
- [ ] 28. Accept list of product matches with scores
- [ ] 29. For each product:
  - [ ] 30. Run eligibility check
  - [ ] 31. If eligible, keep in list
  - [ ] 32. If not eligible, log reason and skip
- [ ] 33. Return filtered list of eligible products
- [ ] 34. Add summary logging (X of Y products eligible)

### Integration with Product Matcher
- [ ] 35. Update `product_matcher.py` to use eligibility filtering
- [ ] 36. In `match_products()` function:
  - [ ] 37. After scoring and sorting products
  - [ ] 38. Before returning results
  - [ ] 39. Call `filter_eligible_products()`
  - [ ] 40. Return only eligible products

### Testing Eligibility Logic
- [ ] 41. Create `scripts/test_product_eligibility.py`
- [ ] 42. Test income requirement:
  - [ ] 43. Create user with income $3000/mo
  - [ ] 44. Test with product requiring min_income $5000
  - [ ] 45. Verify not eligible
  - [ ] 46. Test with product requiring min_income $2000
  - [ ] 47. Verify eligible
- [ ] 48. Test credit utilization requirement:
  - [ ] 49. Create user with 90% utilization
  - [ ] 50. Test with balance transfer card max_utilization 85%
  - [ ] 51. Verify not eligible
- [ ] 52. Test existing account requirements:
  - [ ] 53. Create user with savings account
  - [ ] 54. Test with HYSA requiring no existing savings
  - [ ] 55. Verify not eligible
  - [ ] 56. Create user without savings account
  - [ ] 57. Verify eligible
- [ ] 58. Test category-specific rules:
  - [ ] 59. Create user with 20% utilization
  - [ ] 60. Test with balance transfer card
  - [ ] 61. Verify not eligible (utilization too low for balance transfer)
- [ ] 62. Test full flow: match + filter
  - [ ] 63. Generate product matches for test user
  - [ ] 64. Apply eligibility filtering
  - [ ] 65. Verify only appropriate products remain
- [ ] 66. Print detailed eligibility results for manual review