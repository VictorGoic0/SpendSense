# SpendSense Tasks - Part 9: Vector DB Integration & Performance Optimization

**Context**: Based on comprehensive OpenAI latency testing (documented in `docs/OPENAI_LATENCY_TESTING.md`), we identified that gpt-4o-mini model latency (~17s) is the primary bottleneck. Vector database integration with embeddings will achieve <1s response times while maintaining quality.

**Prerequisites**: 
- Redis caching layer implemented (PR #31)
- PostgreSQL migration complete (PR #32)
- Synthetic data scaled to 500-1,000 users (PR #33)

---

## PR #33: Scale Synthetic Data Generation (Prerequisite for Vector DB)

**Goal**: Generate 500-1,000 synthetic users with complete financial profiles and recommendations to provide sufficient data volume for vector database similarity matching.

**Current State**: 75 users with ~225-375 recommendations (insufficient for meaningful vector DB value)
**Target State**: 500-1,000 users with ~2,000-5,000 recommendations

### Data Generation Scaling
- [ ] 1. Update `scripts/generate_synthetic_data.py` to accept command-line argument for user count
- [ ] 2. Add `--num-users` parameter (default: 75, max: 1000)
- [ ] 3. Scale account generation proportionally (3-4 accounts per user)
- [ ] 4. Scale transaction generation to maintain realistic patterns (150-250 transactions per user)
- [ ] 5. Scale liability generation for credit card users (~30% have credit cards)
- [ ] 6. Maintain persona distribution ratios (high_utilization: 40%, subscription_heavy: 30%, savings_builder: 15%, variable_income: 10%, wealth_builder: 5%)
- [ ] 7. Add random seed parameter for reproducibility
- [ ] 8. Update JSON file naming to include user count (e.g., `synthetic_users_500.json`)

### Performance Optimization
- [ ] 9. Implement batched writing for large JSON files (write every 100 users)
- [ ] 10. Add progress bar using `tqdm` library for long-running generation
- [ ] 11. Add memory usage monitoring (warn if approaching limits)
- [ ] 12. Optimize transaction generation loop (use list comprehension where possible)
- [ ] 13. Add data quality validation checks (distributions, date ranges, amounts)

### Bulk Recommendation Generation
- [ ] 14. Create `scripts/generate_all_recommendations.py` for batch recommendation generation
- [ ] 15. Accept command-line argument for user batch size (default: 10 users at a time)
- [ ] 16. Query all users without recommendations in chunks
- [ ] 17. For each user:
  - [ ] 18. Compute features (30d and 180d) if not already computed
  - [ ] 19. Assign persona (30d and 180d) if not already assigned
  - [ ] 20. Generate recommendations (30d and 180d) via `/recommendations/generate/{user_id}`
- [ ] 21. Add progress tracking with estimated time remaining
- [ ] 22. Add retry logic for failed generations (max 3 retries per user)
- [ ] 23. Log failures to `failed_recommendations.json` for review
- [ ] 24. Add rate limiting to avoid OpenAI API rate limits (max 10 requests/minute)
- [ ] 25. Calculate total cost estimate based on token usage
- [ ] 26. Print summary statistics (total generated, failed, cost, duration)

### Data Quality & Validation
- [ ] 27. Create `scripts/validate_scaled_data.py` to verify data quality
- [ ] 28. Check user count matches target
- [ ] 29. Verify persona distribution matches expected ratios
- [ ] 30. Validate all users have features computed (30d and 180d)
- [ ] 31. Validate all users have personas assigned (30d and 180d)
- [ ] 32. Validate recommendation coverage (target: 80%+ of users with recommendations)
- [ ] 33. Check for duplicate user_ids, account_ids, transaction_ids
- [ ] 34. Verify date ranges are realistic (within last 6 months)
- [ ] 35. Validate amount distributions (no negative savings, realistic credit card balances)
- [ ] 36. Print detailed validation report

### Documentation
- [ ] 37. Update `README.md` with scaled data generation instructions
- [ ] 38. Document expected runtime for 500 and 1,000 user generation
- [ ] 39. Document expected OpenAI API costs for bulk recommendation generation
- [ ] 40. Add troubleshooting section for common issues (rate limits, memory usage)

---

## PR #34: Pinecone Setup & Embedding Infrastructure

**Goal**: Set up Pinecone Serverless vector database and implement embedding generation infrastructure using OpenAI text-embedding-3-small.

### Pinecone Setup
- [ ] 1. Create Pinecone account and get API key
- [ ] 2. Add `PINECONE_API_KEY` to `.env` file and `backend/example-env.md`
- [ ] 3. Add `pinecone-client` to `backend/requirements.txt` (latest version)
- [ ] 4. Create Pinecone serverless index:
  - [ ] 5. Index name: `spendsense-recommendations`
  - [ ] 6. Dimension: 1536 (OpenAI text-embedding-3-small output size)
  - [ ] 7. Metric: `cosine` (for similarity search)
  - [ ] 8. Cloud: AWS, Region: `us-east-1`
- [ ] 9. Verify index creation and connectivity

### Embedding Service Infrastructure
- [ ] 10. Create `backend/app/services/embedding_service.py`
- [ ] 11. Import OpenAI client and Pinecone client
- [ ] 12. Create `get_pinecone_index() -> Index` function:
  - [ ] 13. Initialize Pinecone client with API key from environment
  - [ ] 14. Return index object for `spendsense-recommendations`
  - [ ] 15. Add error handling for missing API key
  - [ ] 16. Add error handling for index not found
- [ ] 17. Create `generate_embedding(text: str) -> list[float]` function:
  - [ ] 18. Accept text string (user context or recommendation content)
  - [ ] 19. Call OpenAI embeddings API with `model="text-embedding-3-small"`
  - [ ] 20. Extract embedding vector from response
  - [ ] 21. Return list of 1536 floats
  - [ ] 22. Add error handling for API failures
  - [ ] 23. Add retry logic with exponential backoff (3 retries)
  - [ ] 24. Log token usage for monitoring

### Context Embedding Functions
- [ ] 25. Create `embed_user_context(context: dict) -> list[float]` function:
  - [ ] 26. Accept user context dict (from `build_user_context()`)
  - [ ] 27. Convert context dict to JSON string
  - [ ] 28. Simplify context for embedding (remove verbose arrays):
    - [ ] 29. Keep: persona_type, window_days, all signal values
    - [ ] 30. Summarize: account types (not full list), transaction count (not full list)
    - [ ] 31. Remove: raw transaction data, recurring merchant names (keep count only)
  - [ ] 32. Call `generate_embedding()` with simplified context JSON
  - [ ] 33. Return embedding vector
  - [ ] 34. Cache embeddings in memory (dict with context hash as key)

### Recommendation Embedding Functions
- [ ] 35. Create `embed_recommendation(rec: dict) -> list[float]` function:
  - [ ] 36. Accept recommendation dict (title, content, rationale)
  - [ ] 37. Combine title + content + rationale into single text string
  - [ ] 38. Call `generate_embedding()` with combined text
  - [ ] 39. Return embedding vector

### Testing
- [ ] 40. Create `scripts/test_embeddings.py` to validate embedding generation
- [ ] 41. Test context embedding for 5 sample users
- [ ] 42. Test recommendation embedding for 5 sample recommendations
- [ ] 43. Verify embedding dimensions (1536)
- [ ] 44. Verify embedding values are floats in range [-1, 1]
- [ ] 45. Test Pinecone connectivity and index query
- [ ] 46. Print token usage and estimated costs

---

## PR #35: Vector Database Population (Batch Embedding Job)

**Goal**: Generate embeddings for all existing recommendations and user contexts, store in Pinecone with metadata.

### Batch Embedding Script
- [ ] 1. Create `scripts/populate_vector_db.py` for batch embedding generation
- [ ] 2. Import database session, models, embedding_service
- [ ] 3. Add command-line arguments:
  - [ ] 4. `--batch-size` (default: 50, number of recommendations per batch)
  - [ ] 5. `--dry-run` (test mode, don't write to Pinecone)
- [ ] 6. Query all recommendations with `status='approved'` (only approved recs in vector DB)
- [ ] 7. Process recommendations in batches

### Recommendation Vector Storage
- [ ] 8. For each recommendation batch:
  - [ ] 9. Generate embedding for recommendation (title + content + rationale)
  - [ ] 10. Prepare Pinecone vector dict:
    - [ ] 11. `id`: `rec_{recommendation_id}` (unique identifier)
    - [ ] 12. `values`: embedding vector (1536 floats)
    - [ ] 13. `metadata`: 
      - [ ] 14. `recommendation_id` (for database lookup)
      - [ ] 15. `user_id` (for filtering)
      - [ ] 16. `persona_type` (for filtering)
      - [ ] 17. `window_days` (30 or 180)
      - [ ] 18. `title` (for display)
      - [ ] 19. `content_preview` (first 200 chars)
      - [ ] 20. `generated_at` (timestamp)
  - [ ] 21. Call `index.upsert(vectors=[vector_dict])`
  - [ ] 22. Handle batch upsert (max 100 vectors per upsert)

### User Context Vector Storage
- [ ] 23. For each user with recommendations:
  - [ ] 24. Build user context using `build_user_context()`
  - [ ] 25. Generate embedding for context
  - [ ] 26. Prepare Pinecone vector dict:
    - [ ] 27. `id`: `context_{user_id}_{window_days}` (unique identifier)
    - [ ] 28. `values`: embedding vector (1536 floats)
    - [ ] 29. `metadata`:
      - [ ] 30. `user_id` (for filtering)
      - [ ] 31. `persona_type` (for filtering)
      - [ ] 32. `window_days` (30 or 180)
      - [ ] 33. Context signals (subscription, savings, credit, income) as JSON string
  - [ ] 34. Call `index.upsert(vectors=[vector_dict])`

### Progress Tracking & Error Handling
- [ ] 35. Add progress bar with `tqdm` (total: number of recommendations + users)
- [ ] 36. Track successful upserts and failures
- [ ] 37. Log failed embeddings to `failed_embeddings.json`
- [ ] 38. Add retry logic for Pinecone API failures (3 retries)
- [ ] 39. Calculate and display estimated OpenAI API cost (embeddings are cheap: $0.00002/1k tokens)
- [ ] 40. Print summary statistics:
  - [ ] 41. Total recommendations embedded
  - [ ] 42. Total user contexts embedded
  - [ ] 43. Total vectors in Pinecone index
  - [ ] 44. Total token usage
  - [ ] 45. Total cost
  - [ ] 46. Duration

### Index Statistics
- [ ] 47. Create `get_index_stats()` function to query Pinecone index stats
- [ ] 48. Print index stats at end of script:
  - [ ] 49. Total vectors
  - [ ] 50. Dimension
  - [ ] 51. Index fullness (percentage of 1M free tier used)

### Testing & Validation
- [ ] 52. Run script with `--dry-run` first to validate logic
- [ ] 53. Test with small batch (10 recommendations) before full run
- [ ] 54. Verify vectors are stored correctly in Pinecone dashboard
- [ ] 55. Query sample vectors to verify metadata is correct
- [ ] 56. Update documentation with expected runtime and costs

---

## PR #36: Vector Search Implementation (Query Engine)

**Goal**: Implement vector similarity search to retrieve recommendations based on user context, with similarity scoring and fallback logic.

### Vector Search Service
- [ ] 1. Create `backend/app/services/vector_search_service.py`
- [ ] 2. Import embedding_service, Pinecone client, logging
- [ ] 3. Create `search_similar_recommendations(context: dict, persona_type: str, top_k: int = 5) -> list[dict]` function:
  - [ ] 4. Accept user context dict (from `build_user_context()`)
  - [ ] 5. Accept persona_type for filtering
  - [ ] 6. Accept top_k (number of results to return)
- [ ] 7. Generate embedding for user context using `embed_user_context()`
- [ ] 8. Query Pinecone index:
  - [ ] 9. Use `index.query()` with context embedding vector
  - [ ] 10. Filter by `persona_type` in metadata
  - [ ] 11. Set `top_k` parameter (default: 5)
  - [ ] 12. Include metadata in results (`include_metadata=True`)
- [ ] 13. Extract results from Pinecone response
- [ ] 14. For each match:
  - [ ] 15. Extract similarity score (0-1 range, cosine similarity)
  - [ ] 16. Extract metadata (recommendation_id, title, content_preview, etc.)
  - [ ] 17. Query database for full recommendation using `recommendation_id`
  - [ ] 18. Combine DB recommendation with similarity score
- [ ] 19. Return list of dicts with recommendation + similarity score

### Similarity Threshold Logic
- [ ] 20. Create `should_use_vector_db_result(similarity_score: float, threshold: float = 0.85) -> bool` function:
  - [ ] 21. Accept similarity score from Pinecone query
  - [ ] 22. Accept threshold (default: 0.85, configurable via environment variable)
  - [ ] 23. Return True if score >= threshold (use vector DB result)
  - [ ] 24. Return False if score < threshold (use OpenAI fallback)
- [ ] 25. Add `VECTOR_DB_SIMILARITY_THRESHOLD` to `.env` (default: 0.85)

### Database Query Helpers
- [ ] 26. Create `get_recommendation_by_id(db: Session, recommendation_id: str) -> Recommendation` function:
  - [ ] 27. Query recommendations table by recommendation_id
  - [ ] 28. Return Recommendation model object
  - [ ] 29. Handle not found case (return None)

### Logging & Monitoring
- [ ] 30. Log vector search queries:
  - [ ] 31. User context (user_id, persona_type, window_days)
  - [ ] 32. Top similarity score
  - [ ] 33. Number of results returned
  - [ ] 34. Decision: "vector_db" or "openai_fallback"
- [ ] 35. Add metrics for monitoring:
  - [ ] 36. Vector DB hit rate (% of queries using vector DB vs OpenAI)
  - [ ] 37. Average similarity score
  - [ ] 38. Latency (time spent in vector search)

### Error Handling
- [ ] 39. Handle Pinecone API failures gracefully (log error, fall back to OpenAI)
- [ ] 40. Handle embedding generation failures (log error, fall back to OpenAI)
- [ ] 41. Handle database query failures (log error, return 500)
- [ ] 42. Add retry logic for transient failures (3 retries with exponential backoff)

### Testing
- [ ] 43. Create `scripts/test_vector_search.py` to validate search functionality
- [ ] 44. Test search for 10 sample users with different personas
- [ ] 45. Verify similarity scores are in expected range (0-1)
- [ ] 46. Test threshold logic (0.85 cutoff)
- [ ] 47. Verify full recommendation data is returned correctly
- [ ] 48. Test fallback logic (simulate low similarity scores)
- [ ] 49. Print search results with similarity scores for manual review

---

## PR #37: Hybrid Recommendation Engine (Vector DB + OpenAI Fallback)

**Goal**: Integrate vector search into recommendation generation endpoint with hybrid logic (vector DB for high similarity, OpenAI for edge cases).

### Hybrid Recommendation Engine
- [ ] 1. Update `backend/app/services/recommendation_engine.py`
- [ ] 2. Import vector_search_service functions
- [ ] 3. Create `generate_recommendations_hybrid(db: Session, user_id: str, window_days: int, persona_type: str) -> tuple[list[dict], str]` function:
  - [ ] 4. Accept database session, user_id, window_days, persona_type
  - [ ] 5. Build user context using existing `build_user_context()` function
  - [ ] 6. **Step 1: Try vector DB search**
    - [ ] 7. Call `search_similar_recommendations(context, persona_type, top_k=5)`
    - [ ] 8. Check if any results returned and top score >= threshold (0.85)
  - [ ] 9. **Step 2a: If vector DB hit (score >= 0.85)**
    - [ ] 10. Extract top 3-5 recommendations from vector search results
    - [ ] 11. Return recommendations list and source="vector_db"
  - [ ] 10. **Step 2b: If vector DB miss (score < 0.85) or no results**
    - [ ] 11. Fall back to OpenAI generation
    - [ ] 12. Call existing `generate_recommendations_via_openai(persona_type, context)`
    - [ ] 13. Store new recommendations in vector DB (background job)
    - [ ] 14. Return recommendations list and source="openai_4o_mini"

### Update Recommendation Generation Endpoint
- [ ] 15. Update `backend/app/routers/recommendations.py`
- [ ] 16. Modify `POST /recommendations/generate/{user_id}` endpoint:
  - [ ] 17. Add query parameter `use_vector_db: bool = True` (enable/disable vector DB)
  - [ ] 18. Check Redis cache first (existing logic)
  - [ ] 19. If cache miss:
    - [ ] 20. Check if vector DB is enabled (`use_vector_db=True`)
    - [ ] 21. If enabled, call `generate_recommendations_hybrid()`
    - [ ] 22. If disabled or vector DB fails, fall back to OpenAI directly
  - [ ] 23. Store recommendations in database (existing logic)
  - [ ] 24. Cache recommendations in Redis (existing logic)
  - [ ] 25. Add `source` field to response JSON (vector_db, redis_cache, or openai_4o_mini)
  - [ ] 26. Add `similarity_score` field to response JSON (if vector DB used)

### Background Embedding Job
- [ ] 27. Create background job to embed new recommendations immediately after OpenAI generation
- [ ] 28. In recommendation generation endpoint, after OpenAI fallback:
  - [ ] 29. Generate embeddings for new recommendations
  - [ ] 30. Store in Pinecone with metadata (same format as batch job)
  - [ ] 31. Log success/failure
  - [ ] 32. Don't block HTTP response (run asynchronously if possible)

### Performance Metrics
- [ ] 33. Add timing instrumentation to measure latency:
  - [ ] 34. Redis cache check latency
  - [ ] 35. Vector DB search latency
  - [ ] 36. OpenAI API latency (existing)
  - [ ] 37. Total request latency
- [ ] 38. Log latency breakdown for monitoring:
  - [ ] 39. Format: `{"cache_ms": 5, "vector_db_ms": 50, "openai_ms": 0, "total_ms": 55, "source": "vector_db"}`
- [ ] 40. Add latency metrics to response JSON (optional, for testing)

### A/B Testing Support
- [ ] 41. Add environment variable `VECTOR_DB_ENABLED` (default: true)
- [ ] 42. Add environment variable `VECTOR_DB_SIMILARITY_THRESHOLD` (default: 0.85)
- [ ] 43. Allow operators to adjust threshold dynamically (future: admin UI)
- [ ] 44. Log vector DB vs OpenAI usage ratio for analysis

### Error Handling & Fallback
- [ ] 45. If vector DB query fails:
  - [ ] 46. Log error with full stack trace
  - [ ] 47. Fall back to OpenAI generation immediately
  - [ ] 48. Return recommendations with `source="openai_4o_mini_fallback"`
- [ ] 49. If embedding generation fails:
  - [ ] 50. Log error
  - [ ] 51. Continue with OpenAI generation (don't block response)
  - [ ] 52. Skip storing in vector DB (try again on next request)

### Testing
- [ ] 53. Create `scripts/test_hybrid_engine.py` to validate hybrid logic
- [ ] 54. Test with 20 users (mix of existing and new users)
- [ ] 55. Verify vector DB is used for existing users (similarity score >= 0.85)
- [ ] 56. Verify OpenAI fallback is used for edge cases
- [ ] 57. Measure latency for both paths:
  - [ ] 58. Vector DB path: target <1s
  - [ ] 59. OpenAI fallback path: target 2-5s (faster than 17s baseline)
- [ ] 60. Verify recommendations quality is maintained (no degradation)
- [ ] 61. Test with vector DB disabled (`use_vector_db=False`) to ensure OpenAI still works
- [ ] 62. Print detailed test results with latency breakdown

### Documentation
- [ ] 63. Update `docs/DECISIONS.md` with hybrid engine implementation details
- [ ] 64. Update `docs/OPENAI_LATENCY_TESTING.md` with final performance results
- [ ] 65. Create `docs/VECTOR_DB_ARCHITECTURE.md` with architecture diagram and flow
- [ ] 66. Update `README.md` with vector DB setup instructions
- [ ] 67. Document expected performance improvements (17s → <1s for vector DB hits)
- [ ] 68. Document cost savings (80-90% reduction in OpenAI API costs)
- [ ] 69. Add troubleshooting section for common issues (Pinecone connectivity, low similarity scores)