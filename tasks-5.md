# SpendSense Tasks - Part 5: AI Recommendation Engine

## PR #17: OpenAI Integration Setup & Prompt Templates

### OpenAI Dependencies
- [x] 1. Add `openai==1.3.5` to backend/requirements.txt
- [x] 2. Install OpenAI SDK: `pip install openai`
- [x] 3. Add `OPENAI_API_KEY=sk-...` to .env file
- [x] 4. Add .env to .gitignore if not already there

### Prompts Directory
- [x] 5. Create `backend/app/prompts/` directory
- [x] 6. Create `backend/app/prompts/__init__.py`

### Base Prompt Template
- [x] 7. Create `backend/app/prompts/base_template.txt`
- [x] 8. Write shared rules that apply to all personas:
   - NEVER provide regulated financial advice
   - ALWAYS use educational, empowering tone
   - NO shaming language
   - EVERY recommendation must cite specific user data
   - Use plain language
   - Format output as JSON
- [x] 9. Define JSON output structure with keys:
   - title (string)
   - content (string, markdown format)
   - rationale (string, "because..." format)
   - metadata (object with priority, tags, links)
- [x] 10. Add mandatory disclosure text to append to all recommendations

### High Utilization Prompt
- [x] 11. Create `backend/app/prompts/high_utilization.txt`
- [x] 12. Include base template rules
- [x] 13. Add persona description: "User struggling with credit card debt"
- [x] 14. Define focus areas:
    - Debt paydown strategies (avalanche vs snowball)
    - Credit utilization impact on scores
    - Payment automation
    - Balance transfer education
    - Interest calculation transparency
- [x] 15. Define tone: Supportive, non-judgmental, action-oriented
- [x] 16. Add avoid/use examples for language
- [x] 17. Add instruction to generate 3-5 recommendations

### Variable Income Prompt
- [x] 18. Create `backend/app/prompts/variable_income.txt`
- [x] 19. Include base template rules
- [x] 20. Add persona description: "User with irregular income"
- [x] 21. Define focus areas:
    - Percent-based budgeting
    - Emergency fund building
    - Income smoothing techniques
    - Cash flow buffer optimization
    - "Feast or famine" expense management
- [x] 22. Define tone: Practical, empathetic, normalizing
- [x] 23. Add examples of relatable scenarios
- [x] 24. Add instruction to generate 3-5 recommendations

### Subscription Heavy Prompt
- [x] 25. Create `backend/app/prompts/subscription_heavy.txt`
- [x] 26. Include base template rules
- [x] 27. Add persona description: "User with many subscriptions"
- [x] 28. Define focus areas:
    - Subscription audit checklists
    - Cancellation/negotiation tactics
    - Free alternative recommendations
    - Bill alert setup
    - Annual vs monthly cost comparisons
- [x] 29. Define tone: Helpful, non-preachy, empowering
- [x] 30. Add instruction to highlight potential annual savings
- [x] 31. Add instruction to generate 3-5 recommendations

### Savings Builder Prompt
- [x] 32. Create `backend/app/prompts/savings_builder.txt`
- [x] 33. Include base template rules
- [x] 34. Add persona description: "User actively building savings/emergency fund"
- [x] 35. Define focus areas:
    - Goal setting frameworks (3-6 month targets)
    - Automation strategies
    - High-yield savings account education
    - CD basics
    - Progress tracking and milestone celebration
- [x] 36. Define tone: Encouraging, motivational, celebrating progress
- [x] 37. Add instruction to acknowledge current savings behavior positively
- [x] 38. Add instruction to generate 3-5 recommendations

### Wealth Builder Prompt
- [x] 39. Create `backend/app/prompts/wealth_builder.txt`
- [x] 40. Include base template rules
- [x] 41. Add persona description: "Affluent user ready for investment/retirement planning"
- [x] 42. Define focus areas:
    - Tax-advantaged investing (401k, IRA, HSA)
    - Asset allocation basics
    - Retirement planning milestones
    - Estate planning fundamentals
    - Charitable giving tax strategies
- [x] 43. Define tone: Sophisticated but accessible, forward-looking
- [x] 44. Add instruction to AVOID specific investment recommendations
- [x] 45. Add instruction to EDUCATE on concepts like employer match
- [x] 46. Add instruction to generate 3-5 recommendations

### Prompt Loader Utility
- [x] 47. Create `backend/app/utils/prompt_loader.py`
- [x] 48. Create function `load_prompt(persona_type: str) -> str`:
    - Construct file path to prompt file
    - Read file contents
    - Return as string
- [x] 49. Add error handling for file not found
- [x] 50. Cache loaded prompts in memory (dict) for performance

---

## PR #18: Recommendation Engine Service - Context Building

### Recommendation Service File
- [x] 1. Create `backend/app/services/recommendation_engine.py`
- [x] 2. Import OpenAI client
- [x] 3. Import database models
- [x] 4. Import prompt loader utility
- [x] 5. Create OpenAI client instance with API key from env

### User Context Builder - Basic Info
- [x] 6. Create `build_user_context(db, user_id: str, window_days: int) -> dict`:
- [x] 7. Query User record
- [x] 8. Query UserFeature record for window
- [x] 9. Query Persona record for window
- [x] 10. Create base context dict with:
    - user_id
    - window_days
    - persona_type

### User Context Builder - Features
- [x] 11. Add features to context dict:
    - subscription signals (merchants, spend)
    - savings signals (inflow, growth, emergency fund)
    - credit signals (utilization, flags)
    - income signals (payroll, variability, buffer)
- [x] 12. Convert feature object to dict
- [x] 13. Round float values to 2 decimal places for readability

### User Context Builder - Accounts
- [x] 14. Query Account records for user
- [x] 15. For each account, create account info dict:
    - type (checking, savings, credit card, etc.)
    - name (masked: "Checking ****1234")
    - balance (current balance)
- [x] 16. Add accounts list to context
- [x] 17. Limit to top 5 accounts by balance for token efficiency

### User Context Builder - Recent Transactions
- [x] 18. Query Transaction records for user in last 30 days
- [x] 19. Sort by date descending
- [x] 20. Limit to 10 most recent transactions
- [x] 21. For each transaction, create transaction dict:
    - date (formatted as string)
    - merchant (merchant_name)
    - amount (rounded to 2 decimals)
    - type (deposit/expense based on amount sign)
- [x] 22. Add transactions list to context

### User Context Builder - Specific Data Points
- [x] 23. For credit cards with high utilization, add detailed info:
    - Last 4 digits
    - Current balance
    - Credit limit
    - Utilization percentage
    - Monthly interest charges (if available)
- [x] 24. For recurring merchants, add list of merchant names
- [x] 25. For savings accounts, add growth trend info
- [x] 26. Return complete context dict

### Context Validation
- [x] 27. Create `validate_context(context: dict) -> bool`:
    - Check required fields present
    - Check data types correct
    - Return True if valid, False otherwise
- [x] 28. Add logging for invalid context

### Testing Context Building
- [x] 29. Create test script `scripts/test_context_builder.py`
- [x] 30. Test with multiple user IDs
- [x] 31. Print context dict for review
- [x] 32. Verify all required fields present
- [x] 33. Verify data looks realistic
- [x] 34. Check token count of context (should be <2000 tokens)

---

## PR #19: Recommendation Engine Service - OpenAI Integration

### OpenAI Call Function
- [x] 1. In recommendation_engine.py, create `generate_recommendations_via_openai(persona_type: str, user_context: dict) -> list`:
- [x] 2. Load system prompt for persona type using prompt_loader
- [x] 3. Convert user_context dict to JSON string
- [x] 4. Record start time for latency tracking

### OpenAI API Call
- [x] 5. Call OpenAI chat completions API:
   - model: "gpt-4o-mini"
   - messages: system prompt + user context
   - response_format: {"type": "json_object"}
   - temperature: 0.7
- [x] 6. Wrap in try/except for error handling
- [x] 7. Record end time and calculate latency in milliseconds

### Response Parsing
- [x] 8. Extract message content from response
- [x] 9. Parse JSON string to dict
- [x] 10. Extract recommendations array from response
- [x] 11. For each recommendation:
    - Validate required fields (title, content, rationale)
    - Add generation_time_ms
    - Add persona_type
- [x] 12. Return list of recommendation dicts

### Error Handling
- [x] 13. Handle OpenAI API errors:
    - Rate limit errors → wait and retry (exponential backoff)
    - Invalid API key → log error and raise exception
    - Model not found → log error and raise exception
    - JSON parsing errors → log and return empty list
- [x] 14. Add comprehensive logging for debugging

### Token Usage Tracking
- [x] 15. Extract token usage from OpenAI response
- [x] 16. Log tokens used (prompt + completion)
- [x] 17. Calculate estimated cost
- [x] 18. Return token usage separately (NOT saved to DB, only for logging/review in test output file)

### Testing OpenAI Integration
- [x] 19. Create test script `scripts/test_openai_generation.py`
- [x] 20. Test with each persona type (5 tests)
- [x] 21. Verify JSON response structure
- [x] 22. Verify 3-5 recommendations returned per call
- [x] 23. Verify rationales cite specific data
- [x] 24. Check content quality and tone
- [x] 25. Measure latency (should be <5 seconds)
- [x] 26. Print generated recommendations for review

---

## PR #20: Guardrails Service - Tone & Consent Validation

### Guardrails Service File
- [ ] 1. Create `backend/app/services/guardrails.py`
- [ ] 2. Import database models

### Tone Validation - Forbidden Phrases
- [ ] 3. Create `validate_tone(content: str) -> Dict[str, Any]`:
   - Returns structured dict with `is_valid` (bool) and `validation_warnings` (array)
   - Format: `{"is_valid": bool, "validation_warnings": [{"severity": "critical"|"notable", "type": str, "message": str}]}`
- [ ] 4. Define list of forbidden shaming phrases:
   - "you're overspending"
   - "bad habit"
   - "poor financial decision"
   - "irresponsible"
   - "wasteful spending"
   - "you should stop"
   - "you need to"
- [ ] 5. Convert content to lowercase for checking
- [ ] 6. Loop through forbidden phrases
- [ ] 7. If any phrase found, add to warnings array:
   - severity: "critical"
   - type: "forbidden_phrase"
   - message: f"Contains shaming language: '{phrase}'"

### Tone Validation - Empowering Language
- [ ] 8. Define list of empowering keywords that should be present:
   - "you can"
   - "let's"
   - "many people"
   - "common challenge"
   - "opportunity"
   - "consider"
   - "explore"
- [ ] 9. Check if at least one empowering keyword present
- [ ] 10. If none found, add to warnings array:
   - severity: "notable"
   - type: "lacks_empowering_language"
   - message: "Content lacks empowering tone - no empowering keywords found"
- [ ] 11. Return result dict:
   - If warnings exist: `{"is_valid": False, "validation_warnings": [...]}`
   - If all checks pass: `{"is_valid": True, "validation_warnings": []}`

### Consent Validation
- [ ] 12. Create `check_consent(db, user_id: str) -> bool`:
- [ ] 13. Query User record
- [ ] 14. Check consent_status field
- [ ] 15. Return True if consent_status == True, False otherwise
- [ ] 16. Add logging for consent checks

### Eligibility Validation - Income Requirements
- [ ] 17. Create `check_income_eligibility(db, user_id: str, min_income: float) -> bool`:
- [ ] 18. Query UserFeature for user (30d window)
- [ ] 19. Check if avg_monthly_income >= min_income
- [ ] 20. Return True if eligible, False otherwise

### Eligibility Validation - Credit Requirements
- [ ] 21. Create `check_credit_eligibility(db, user_id: str, max_utilization: float) -> bool`:
- [ ] 22. Query UserFeature for user
- [ ] 23. Check if max_utilization <= max_utilization threshold
- [ ] 24. Return True if eligible, False otherwise

### Eligibility Validation - Account Existence
- [ ] 25. Create `check_account_exists(db, user_id: str, account_type: str) -> bool`:
- [ ] 26. Query Account records for user
- [ ] 27. Filter by account_type
- [ ] 28. Return True if at least one account found, False otherwise

### Partner Offer Filtering
- [ ] 29. Create `filter_partner_offers(db, user_id: str, offers: list) -> list`:
- [ ] 30. For each offer:
    - Check eligibility requirements (income, credit, existing accounts)
    - Remove offer if user not eligible
- [ ] 31. Return filtered list of offers

### Mandatory Disclosure
- [ ] 32. Create constant `MANDATORY_DISCLOSURE = "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."`
- [ ] 33. Create `append_disclosure(content: str) -> str`:
    - Add disclosure to end of content
    - Return updated content

### Testing Guardrails
- [ ] 34. Create test script `scripts/test_guardrails.py`
- [ ] 35. Test tone validation with good and bad examples
- [ ] 36. Test consent checking with consented/non-consented users
- [ ] 37. Test eligibility checks with various user scenarios
- [ ] 38. Verify all functions work as expected

---

## PR #21: Recommendation Generation Endpoint

### Recommendations Router
- [ ] 1. Create `backend/app/routers/recommendations.py`
- [ ] 2. Create APIRouter with prefix="/recommendations"
- [ ] 3. Import recommendation engine and guardrails services
- [ ] 4. Import database models and schemas

### Generate Recommendations Endpoint - Validation
- [ ] 5. Create POST `/generate/{user_id}` endpoint:
- [ ] 6. Accept user_id as path parameter
- [ ] 7. Accept optional window_days query parameter (default: 30)
- [ ] 8. Accept optional force_regenerate query parameter (default: False)
- [ ] 9. Get database session
- [ ] 10. Check if user exists → 404 if not
- [ ] 11. Check consent using guardrails.check_consent() → 403 if not consented

### Generate Recommendations Endpoint - Check Existing
- [ ] 12. Query existing recommendations for user + window
- [ ] 13. If recommendations exist and not force_regenerate:
    - Return existing recommendations
    - Skip generation (saves API costs)

### Generate Recommendations Endpoint - Get Context
- [ ] 14. Get user persona for window
- [ ] 15. If no persona assigned → 400 error with message to assign persona first
- [ ] 16. Build user context using build_user_context()
- [ ] 17. Validate context

### Generate Recommendations Endpoint - Call OpenAI
- [ ] 18. Call generate_recommendations_via_openai() with persona and context
- [ ] 19. Measure total generation time
- [ ] 20. If OpenAI call fails → 500 error with message

### Generate Recommendations Endpoint - Validate Tone
- [ ] 21. For each generated recommendation:
    - Extract content field
    - Call guardrails.validate_tone() → returns `{"is_valid": bool, "validation_warnings": [...]}`
    - Store validation_warnings in recommendation metadata:
      - Initialize metadata dict if not present
      - Set `metadata["validation_warnings"] = tone_result["validation_warnings"]`
      - Empty array if valid, populated array if warnings exist
    - Log warnings if any (for monitoring)
    - **IMPORTANT**: Do NOT skip recommendations with warnings - persist all for operator review

### Generate Recommendations Endpoint - Save to Database
- [ ] 23. For each recommendation (including those with warnings):
    - Generate recommendation_id (rec_{uuid})
    - Create Recommendation model instance
    - Set fields: user_id, persona_type, window_days, content_type, title, content, rationale
    - Set status='pending_approval' (all recommendations start pending, regardless of warnings)
    - Set generation_time_ms
    - Set generated_at timestamp
    - Append mandatory disclosure to content
    - Set metadata_json: Serialize metadata dict (includes validation_warnings) to JSON string
- [ ] 24. Bulk insert recommendations
- [ ] 25. Commit transaction

### Generate Recommendations Endpoint - Response
- [ ] 26. Query newly created recommendations
- [ ] 27. Convert to schema objects
- [ ] 28. Return JSON response with:
    - user_id
    - persona
    - recommendations list
    - generation_time_ms (total)
- [ ] 29. Return 201 status code

### Error Handling
- [ ] 30. Wrap entire endpoint in try/except
- [ ] 31. Rollback database transaction on error
- [ ] 32. Return appropriate error responses:
    - 403: No consent
    - 404: User not found
    - 400: No persona assigned or invalid request
    - 500: Server error (OpenAI failure, database error)
- [ ] 33. Add detailed error messages and logging

### Testing Recommendation Generation
- [ ] 34. Test via Swagger UI at http://localhost:8000/docs
- [ ] 35. Test with consented user → should succeed
- [ ] 36. Test with non-consented user → should return 403
- [ ] 37. Test with user without persona → should return 400
- [ ] 38. Verify recommendations saved in database (including those with warnings)
- [ ] 39. Verify status='pending_approval' for all recommendations
- [ ] 40. Verify content includes disclosure
- [ ] 41. Verify rationales cite specific data
- [ ] 42. Check generation_time_ms < 5000
- [ ] 43. Verify validation_warnings stored in metadata_json:
    - Empty array for valid recommendations
    - Populated array with severity/type/message for invalid recommendations
- [ ] 44. Verify recommendations with warnings are still persisted (not skipped)
