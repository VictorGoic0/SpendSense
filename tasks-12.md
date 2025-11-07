# SpendSense Tasks - Part 12: Article Catalog & Vector-Based Matching

**Context**: Add educational article recommendations by matching generated recommendations to a curated article catalog using vector similarity search. This feature uses Pinecone vector database with OpenAI embeddings to find the most relevant article for each educational recommendation in real-time.

**Prerequisites**: 
- Product catalog feature implemented (PR #38-45)
- Pinecone account and API key configured
- OpenAI embeddings API access

---

## PR #46: Article Catalog Schema & LLM-Based Generation

**Goal**: Create articles database table and generate 50 realistic educational articles using GPT-4o (10 per persona).

**Current State**: No article catalog exists
**Target State**: Database table created, 50 LLM-generated articles ready for seeding

### Database Migration
- [ ] 1. Create database migration for articles table
- [ ] 2. Add article_id (TEXT PRIMARY KEY)
- [ ] 3. Add title (TEXT NOT NULL)
- [ ] 4. Add source (TEXT NOT NULL) - 'NerdWallet', 'Investopedia', 'CFPB', etc.
- [ ] 5. Add url (TEXT NOT NULL) - Placeholder URLs for MVP
- [ ] 6. Add summary (TEXT NOT NULL) - 2-3 sentences for display
- [ ] 7. Add full_text (TEXT NOT NULL) - Full article content for embedding
- [ ] 8. Add categories (TEXT) - JSON array: ["credit", "debt", "budgeting"]
- [ ] 9. Add persona_targets (TEXT) - JSON array: ["high_utilization", "savings_builder"]
- [ ] 10. Add reading_time_minutes (INTEGER)
- [ ] 11. Add published_date (DATE)
- [ ] 12. Add active (BOOLEAN DEFAULT TRUE)
- [ ] 13. Add timestamps (created_at, updated_at)
- [ ] 14. Create index on persona_targets
- [ ] 15. Create index on active status
- [ ] 16. Create index on categories

### Update Recommendations Table
- [ ] 17. Add database migration to recommendations table
- [ ] 18. ALTER TABLE recommendations ADD COLUMN article_id TEXT
- [ ] 19. Add foreign key relationship to articles table (optional for MVP)
- [ ] 20. Create index on article_id for faster lookups

### Update Database Models
- [ ] 21. Create Article model in `backend/app/models.py`
- [ ] 22. Define all fields matching table schema
- [ ] 23. Add relationship to Recommendation model (if FK added)
- [ ] 24. Add __repr__ method for debugging
- [ ] 25. Test model creation and queries
- [ ] 26. Update Recommendation model to include article_id field
- [ ] 27. Add article relationship accessor if needed

### Article Generation Script
- [ ] 28. Create `scripts/generate_article_catalog.py`
- [ ] 29. Import OpenAI client
- [ ] 30. Define article generation prompt:
  - [ ] 31. Generate 50 articles total (10 per persona)
  - [ ] 32. Personas: high_utilization, variable_income, subscription_heavy, savings_builder, wealth_builder
  - [ ] 33. Realistic titles (e.g., "How to Pay Down Credit Card Debt Fast")
  - [ ] 34. Realistic sources (NerdWallet, Investopedia, CFPB, The Balance, Forbes)
  - [ ] 35. 2-3 sentence summaries
  - [ ] 36. 300-500 word "full text" (simulated article content for embedding)
  - [ ] 37. Realistic reading times (5-10 minutes)
  - [ ] 38. Appropriate categories per article
  - [ ] 39. Persona targets (can be multiple)
  - [ ] 40. Placeholder URLs (e.g., https://example.com/articles/article-slug)
- [ ] 41. Create `generate_article_catalog()` function:
  - [ ] 42. Call OpenAI GPT-4o with structured prompt
  - [ ] 43. Use response_format={"type": "json_object"}
  - [ ] 44. Temperature 0.7 for balance of creativity and consistency
  - [ ] 45. Parse JSON response
  - [ ] 46. Validate response structure
  - [ ] 47. Return list of articles
- [ ] 48. Create `validate_article(article, index)` function:
  - [ ] 49. Check required fields present (title, source, url, summary, full_text, persona_targets)
  - [ ] 50. Validate persona_targets is list of valid personas
  - [ ] 51. Validate categories is list (if present)
  - [ ] 52. Warn if full_text < 100 words (too short for good embedding)
  - [ ] 53. Return boolean validation result
- [ ] 54. Create `enhance_articles(articles)` function:
  - [ ] 55. Add article_id (art_{index:03d} format)
  - [ ] 56. Set active=True for all
  - [ ] 57. Set created_at and updated_at timestamps
  - [ ] 58. Set default reading_time if not provided (word_count / 200)
  - [ ] 59. Generate realistic published_date (last 1-2 years)
  - [ ] 60. Return enhanced articles list
- [ ] 61. Create `save_to_json(articles, filename)` function:
  - [ ] 62. Save to `data/article_catalog.json`
  - [ ] 63. Pretty-print with indent=2
  - [ ] 64. Print confirmation message
- [ ] 65. Add main execution block:
  - [ ] 66. Print banner with script title
  - [ ] 67. Call generate_article_catalog()
  - [ ] 68. Print count of generated articles
  - [ ] 69. Validate all articles
  - [ ] 70. Enhance with metadata
  - [ ] 71. Print final count after validation
  - [ ] 72. Warn if < 50 articles (target: 50)
  - [ ] 73. Save to JSON
  - [ ] 74. Print distribution by persona
  - [ ] 75. Print distribution by category
  - [ ] 76. Print sample article for review

### Testing Article Generation
- [ ] 77. Set OPENAI_API_KEY in environment
- [ ] 78. Run: `python scripts/generate_article_catalog.py`
- [ ] 79. Verify 50 articles generated
- [ ] 80. Review `data/article_catalog.json` for quality
- [ ] 81. Check article titles are realistic and relevant
- [ ] 82. Verify full_text is substantial (300-500 words)
- [ ] 83. Verify persona distribution (10 per persona)
- [ ] 84. Check URLs are placeholder format
- [ ] 85. Verify summaries are 2-3 sentences
- [ ] 86. If quality is poor, adjust prompt and regenerate

### Documentation
- [ ] 87. Add article generation instructions to README.md
- [ ] 88. Document expected runtime (~60-90 seconds)
- [ ] 89. Document expected OpenAI API cost (~$0.30-0.50)
- [ ] 90. Add note: "Articles are LLM-generated placeholders. Replace with real articles when ready."
- [ ] 91. Document how to replace with real articles later (manual curation process)

---

## PR #47: Article Seeding & Vector Database Population

**Goal**: Seed articles into database and generate embeddings for vector search.

### Article Seeding Script
- [ ] 1. Create `scripts/seed_article_catalog.py`
- [ ] 2. Import database session and Article model
- [ ] 3. Import json module for reading catalog file
- [ ] 4. Create `load_article_catalog(filepath: str) -> list[dict]` function:
  - [ ] 5. Open and read `data/article_catalog.json`
  - [ ] 6. Parse JSON and return list of article dicts
  - [ ] 7. Add error handling for missing/invalid file
- [ ] 8. Create `clear_existing_articles(db) -> int` function:
  - [ ] 9. Query all Article records
  - [ ] 10. Delete all records (fresh start for MVP)
  - [ ] 11. Commit transaction
  - [ ] 12. Return count of deleted articles
  - [ ] 13. Print confirmation message
- [ ] 14. Create `seed_articles(db, articles: list[dict]) -> int` function:
  - [ ] 15. Iterate through articles list
  - [ ] 16. For each article:
    - [ ] 17. Convert persona_targets to JSON string if list
    - [ ] 18. Convert categories to JSON string if list
    - [ ] 19. Create Article model instance
    - [ ] 20. Set all fields from article dict
    - [ ] 21. Add to session
  - [ ] 22. Commit all articles in single transaction
  - [ ] 23. Return count of articles inserted
  - [ ] 24. Add error handling with rollback
- [ ] 25. Create `print_distribution(db)` function:
  - [ ] 26. Query articles grouped by persona_targets
  - [ ] 27. Parse JSON and count articles per persona
  - [ ] 28. Print formatted table showing distribution
  - [ ] 29. Query articles grouped by categories
  - [ ] 30. Print category distribution
  - [ ] 31. Print total active articles

### Embedding Generation Service
- [ ] 32. Update `backend/app/services/embedding_service.py` (or create if not exists)
- [ ] 33. Import OpenAI client
- [ ] 34. Create `generate_article_embedding(article: Article) -> list[float]` function:
  - [ ] 35. Combine title + summary + full_text into single text
  - [ ] 36. Call OpenAI embeddings API with text-embedding-3-small
  - [ ] 37. Extract embedding vector (1536 dimensions)
  - [ ] 38. Return embedding as list of floats
  - [ ] 39. Add error handling for API failures
  - [ ] 40. Add retry logic (3 retries with exponential backoff)
- [ ] 41. Create `batch_embed_articles(articles: list[Article]) -> list[tuple[str, list[float]]]` function:
  - [ ] 42. Process articles in batches of 100 (API limit)
  - [ ] 43. For each batch, combine texts
  - [ ] 44. Call OpenAI embeddings API with batch
  - [ ] 45. Extract embeddings for each article
  - [ ] 46. Return list of (article_id, embedding) tuples
  - [ ] 47. Add progress logging (processed X of Y articles)

### Pinecone Index Setup
- [ ] 48. Create Pinecone index for articles (if not exists):
  - [ ] 49. Index name: `spendsense-articles`
  - [ ] 50. Dimension: 1536 (text-embedding-3-small)
  - [ ] 51. Metric: cosine
  - [ ] 52. Cloud: AWS, Region: us-east-1
- [ ] 53. Create `get_articles_index()` function in embedding_service:
  - [ ] 54. Initialize Pinecone client
  - [ ] 55. Return index object for spendsense-articles
  - [ ] 56. Add error handling for missing API key
  - [ ] 57. Add error handling for index not found

### Vector Database Population Script
- [ ] 58. Create `scripts/populate_article_vectors.py`
- [ ] 59. Import database session, Article model, embedding_service
- [ ] 60. Add command-line arguments:
  - [ ] 61. `--batch-size` (default: 50, number of articles per batch)
  - [ ] 62. `--dry-run` (test mode, don't write to Pinecone)
- [ ] 63. Query all active articles from database
- [ ] 64. Generate embeddings for all articles:
  - [ ] 65. Call `batch_embed_articles()` with all articles
  - [ ] 66. Track total token usage
  - [ ] 67. Calculate estimated cost ($0.00002/1k tokens)
- [ ] 68. Prepare Pinecone vectors:
  - [ ] 69. For each article + embedding:
    - [ ] 70. Create vector dict with id=article_id
    - [ ] 71. Set values=embedding (1536 floats)
    - [ ] 72. Set metadata: title, source, summary, persona_targets, categories, url, reading_time
- [ ] 73. Upload to Pinecone:
  - [ ] 74. Get articles index
  - [ ] 75. Upsert vectors in batches of 100
  - [ ] 76. Add progress bar with tqdm
  - [ ] 77. Track successful uploads and failures
  - [ ] 78. Log failed uploads to `failed_article_embeddings.json`
- [ ] 79. Print summary statistics:
  - [ ] 80. Total articles embedded
  - [ ] 81. Total vectors in Pinecone index
  - [ ] 82. Total token usage
  - [ ] 83. Total cost
  - [ ] 84. Duration
- [ ] 85. Query index stats and print:
  - [ ] 86. Total vectors in index
  - [ ] 87. Index dimension
  - [ ] 88. Index fullness (% of free tier used)

### Testing Vector Population
- [ ] 89. Run seeding script: `python scripts/seed_article_catalog.py`
- [ ] 90. Verify all 50 articles inserted into database
- [ ] 91. Check distribution statistics printed correctly
- [ ] 92. Run vector population script: `python scripts/populate_article_vectors.py`
- [ ] 93. Verify all 50 articles embedded successfully
- [ ] 94. Check Pinecone dashboard shows 50 vectors in spendsense-articles index
- [ ] 95. Query sample vector from Pinecone to verify metadata
- [ ] 96. Verify metadata fields are correct (title, source, persona_targets, etc.)
- [ ] 97. Test dry-run mode works: `python scripts/populate_article_vectors.py --dry-run`

---

## PR #48: Article Matching Service (Vector Similarity Search)

**Goal**: Implement real-time article matching using vector similarity search for generated recommendations.

### Article Matching Service Setup
- [ ] 1. Create `backend/app/services/article_matcher.py`
- [ ] 2. Import embedding_service functions
- [ ] 3. Import Article model
- [ ] 4. Import Pinecone client
- [ ] 5. Add logging setup

### Vector Search Function
- [ ] 6. Create `search_similar_articles(recommendation_text: str, persona_type: str, top_k: int = 3) -> list[dict]` function:
  - [ ] 7. Accept recommendation text (title + content combined)
  - [ ] 8. Accept persona_type for filtering
  - [ ] 9. Accept top_k (default: 3, number of results to return)
  - [ ] 10. Generate embedding for recommendation text:
    - [ ] 11. Call OpenAI embeddings API with text-embedding-3-small
    - [ ] 12. Extract embedding vector (1536 dimensions)
    - [ ] 13. Add error handling for API failures
  - [ ] 14. Query Pinecone articles index:
    - [ ] 15. Use index.query() with recommendation embedding
    - [ ] 16. Set top_k parameter
    - [ ] 17. Include metadata in results
    - [ ] 18. Filter by active=True in metadata
    - [ ] 19. Optionally filter by persona_targets (if strict matching desired)
  - [ ] 20. Extract results from Pinecone response:
    - [ ] 21. For each match:
      - [ ] 22. Extract similarity score (0-1 range, cosine similarity)
      - [ ] 23. Extract metadata (article_id, title, source, url, etc.)
      - [ ] 24. Query database for full Article record using article_id
      - [ ] 25. Combine DB article with similarity score
  - [ ] 26. Return list of dicts with article + similarity score
  - [ ] 27. Add logging for search queries (rec text length, persona, top score)

### Article Selection Logic
- [ ] 28. Create `select_best_article(recommendation_text: str, persona_type: str, threshold: float = 0.75) -> Optional[dict]` function:
  - [ ] 29. Accept recommendation text
  - [ ] 30. Accept persona_type for context
  - [ ] 31. Accept similarity threshold (default: 0.75)
  - [ ] 32. Call `search_similar_articles()` to get top 3
  - [ ] 33. Extract top result (highest similarity score)
  - [ ] 34. Check if top score >= threshold:
    - [ ] 35. If yes: Return article dict with score
    - [ ] 36. If no: Return None (no suitable article found)
  - [ ] 37. Add logging for selection decision:
    - [ ] 38. Log when article is selected (article_id, score)
    - [ ] 39. Log when no article meets threshold (top score, threshold)

### Batch Matching Helper
- [ ] 40. Create `match_articles_for_recommendations(recommendations: list[dict], persona_type: str) -> list[dict]` function:
  - [ ] 41. Accept list of recommendation dicts (title, content)
  - [ ] 42. Accept persona_type for filtering
  - [ ] 43. For each recommendation:
    - [ ] 44. Combine title + content into single text
    - [ ] 45. Call `select_best_article()` with text and persona
    - [ ] 46. Add article_id to recommendation dict if match found
    - [ ] 47. Add similarity_score to recommendation dict for debugging
    - [ ] 48. Add matched_article object (for immediate use, not stored)
  - [ ] 49. Return updated recommendations list
  - [ ] 50. Add summary logging (X of Y recs matched to articles)

### Helper Functions
- [ ] 51. Create `get_article_by_id(db, article_id: str) -> Optional[Article]` function:
  - [ ] 52. Query Article table by article_id
  - [ ] 53. Return Article model object
  - [ ] 54. Return None if not found
  - [ ] 55. Add error handling

### Testing Article Matching
- [ ] 56. Create `scripts/test_article_matching.py`
- [ ] 57. Test vector search with sample recommendation text:
  - [ ] 58. High utilization rec: "Understanding credit utilization and debt paydown strategies"
  - [ ] 59. Call `search_similar_articles()` with text
  - [ ] 60. Verify top 3 results returned
  - [ ] 61. Verify similarity scores in reasonable range (0.5-0.95)
  - [ ] 62. Print results for manual review
- [ ] 63. Test article selection with different thresholds:
  - [ ] 64. Test with threshold 0.75 (should match most recs)
  - [ ] 65. Test with threshold 0.90 (should match fewer recs)
  - [ ] 66. Test with threshold 0.50 (should match almost all recs)
  - [ ] 67. Verify None returned when no article meets threshold
- [ ] 68. Test batch matching:
  - [ ] 69. Create 3-5 sample recommendations
  - [ ] 70. Call `match_articles_for_recommendations()`
  - [ ] 71. Verify article_ids attached where appropriate
  - [ ] 72. Verify similarity_scores logged correctly
  - [ ] 73. Print summary statistics
- [ ] 74. Test with all 5 persona types:
  - [ ] 75. High utilization → credit/debt articles
  - [ ] 76. Variable income → budgeting/irregular income articles
  - [ ] 77. Subscription heavy → subscription/spending articles
  - [ ] 78. Savings builder → savings/emergency fund articles
  - [ ] 79. Wealth builder → investing/retirement articles
- [ ] 80. Verify matching quality (articles are topically relevant)

---

## PR #49: Hybrid Recommendation Engine with Article Matching

**Goal**: Integrate article matching into existing recommendation generation flow.

### Update Pydantic Schemas
- [ ] 1. Update `backend/app/schemas.py`
- [ ] 2. Create `ArticleBase` schema:
  - [ ] 3. article_id: str
  - [ ] 4. title: str
  - [ ] 5. source: str
  - [ ] 6. url: str
  - [ ] 7. summary: str
  - [ ] 8. reading_time_minutes: Optional[int]
- [ ] 9. Create `ArticleResponse` schema (extends ArticleBase):
  - [ ] 10. categories: list[str]
  - [ ] 11. persona_targets: list[str]
  - [ ] 12. published_date: Optional[date]
  - [ ] 13. active: bool
  - [ ] 14. Add Config class with from_attributes=True
- [ ] 15. Update `RecommendationResponse` schema:
  - [ ] 16. Add article_id: Optional[str]
  - [ ] 17. Add article: Optional[ArticleResponse] (nested article data)
  - [ ] 18. Keep all existing fields (content_type, product fields, etc.)

### Enhanced Recommendation Engine
- [ ] 19. Update `backend/app/services/recommendation_engine.py`
- [ ] 20. Import article_matcher functions
- [ ] 21. Update `generate_combined_recommendations()` function:
  - [ ] 22. After generating educational recommendations (existing logic)
  - [ ] 23. Before generating product recommendations
  - [ ] 24. **Step 1.5: Match articles to educational recs**
    - [ ] 25. Extract educational recommendations from list
    - [ ] 26. Call `match_articles_for_recommendations()` with educational recs
    - [ ] 27. Update educational recs with article_id where matched
    - [ ] 28. Log matching statistics (X of Y recs got articles)
  - [ ] 29. Continue with existing product recommendation logic
  - [ ] 30. Return combined list with article_ids populated

### Recommendation Storage Updates
- [ ] 31. Update recommendation storage in `backend/app/routers/recommendations.py`
- [ ] 32. In `POST /recommendations/generate/{user_id}` endpoint:
  - [ ] 33. After calling `generate_combined_recommendations()`
  - [ ] 34. For each recommendation:
    - [ ] 35. Check if article_id is present
    - [ ] 36. If present, store in article_id column
    - [ ] 37. Store article_similarity_score in metadata_json (for debugging)
  - [ ] 38. Continue with existing storage logic

### Recommendation Retrieval Updates
- [ ] 39. Update `GET /recommendations/{user_id}` endpoint:
  - [ ] 40. Query recommendations with article_id JOIN articles
  - [ ] 41. For recommendations with article_id:
    - [ ] 42. Include full article data in response
    - [ ] 43. Parse article metadata (categories, persona_targets from JSON)
  - [ ] 44. Return enriched recommendations with article objects

### Error Handling & Fallback
- [ ] 45. Add error handling in recommendation engine:
  - [ ] 46. If article matching fails (Pinecone error):
    - [ ] 47. Log error with stack trace
    - [ ] 48. Continue with recommendations (article_id = NULL)
    - [ ] 49. Don't block recommendation generation
  - [ ] 50. If embedding generation fails:
    - [ ] 51. Log error
    - [ ] 52. Skip article matching for that rec
    - [ ] 53. Continue with next recommendation
- [ ] 54. Add fallback for missing articles:
  - [ ] 55. If article_id in DB but article record deleted:
    - [ ] 56. Return recommendation without article data
    - [ ] 57. Log warning

### Performance Optimization
- [ ] 58. Add timing instrumentation:
  - [ ] 59. Measure article matching latency (should be ~100-300ms for 2-3 recs)
  - [ ] 60. Log latency breakdown: embedding (X ms), vector search (Y ms), DB query (Z ms)
  - [ ] 61. Add to existing recommendation generation timing logs
- [ ] 62. Optimize embedding calls:
  - [ ] 63. Batch embed multiple recs if possible (OpenAI supports batching)
  - [ ] 64. Cache embeddings in memory if same rec text generated multiple times (unlikely but possible)

### Testing Hybrid Engine with Articles
- [ ] 65. Create `scripts/test_hybrid_recommendations_with_articles.py`
- [ ] 66. Test recommendation generation for high_utilization user:
  - [ ] 67. Generate recommendations via API
  - [ ] 68. Verify 2-3 educational recs with article_ids attached
  - [ ] 69. Verify 1-2 product recs (no article_ids, as expected)
  - [ ] 70. Check article similarity scores (should be >0.75)
  - [ ] 71. Verify total latency acceptable (<6s including article matching)
- [ ] 72. Test with all 5 persona types:
  - [ ] 73. Verify articles matched are topically relevant to persona
  - [ ] 74. Check match rate (target: 60-80% of educational recs get articles)
- [ ] 75. Test edge case: No articles meet threshold:
  - [ ] 76. Generate rec for niche topic
  - [ ] 77. Verify article_id is NULL
  - [ ] 78. Verify recommendation still generated successfully
- [ ] 79. Test performance:
  - [ ] 80. Measure latency with article matching
  - [ ] 81. Target: <500ms added for 2-3 recs
  - [ ] 82. Verify acceptable for MVP (<6s total)
- [ ] 83. Query recommendations via GET endpoint:
  - [ ] 84. Verify article objects included in response
  - [ ] 85. Check article fields complete (title, source, url, summary, reading_time)

---

## PR #50: Frontend - Article Display Integration

**Goal**: Update frontend to display linked articles for educational recommendations.

### Update RecommendationCard Component
- [ ] 1. Open `frontend/src/components/RecommendationCard.jsx`
- [ ] 2. Update to handle article data
- [ ] 3. For education type recommendations:
  - [ ] 4. Check if recommendation.article exists
  - [ ] 5. If article present:
    - [ ] 6. Display article section below content
    - [ ] 7. Show article title
    - [ ] 8. Show source (e.g., "from NerdWallet")
    - [ ] 9. Show reading time (e.g., "8 min read")
    - [ ] 10. Show article summary (2-3 sentences, muted text)
    - [ ] 11. Add "Read Full Article" button:
      - [ ] 12. Link to article.url
      - [ ] 13. Open in new tab (target="_blank", rel="noopener noreferrer")
      - [ ] 14. Style with secondary/outline variant
      - [ ] 15. Add external link icon (↗)
  - [ ] 16. If no article:
    - [ ] 17. No article section displayed (existing behavior)
- [ ] 18. For partner_offer type recommendations:
  - [ ] 19. No article section (products don't get articles)

### Styling Updates
- [ ] 20. Add CSS classes for article section:
  - [ ] 21. `.article-section` with subtle border-top separator
  - [ ] 22. `.article-title` with appropriate font size and weight
  - [ ] 23. `.article-meta` for source and reading time (small, muted)
  - [ ] 24. `.article-summary` for 2-3 sentence description
  - [ ] 25. `.article-cta` button styling (outline, secondary color)
- [ ] 26. Ensure responsive design (mobile-friendly)
- [ ] 27. Add hover states for "Read Full Article" button
- [ ] 28. Test dark mode compatibility (if applicable)

### Example Article Card UI
```
┌─────────────────────────────────────────────┐
│ 📚 Educational Recommendation               │
│                                             │
│ Understanding Credit Utilization            │
│                                             │
│ Your credit utilization of 68% is          │
│ impacting your credit score. Here's how... │
│ [content continues]                         │
│                                             │
│ Why: With average utilization at 68%...    │
│                                             │
│ ─────────────────────────────────────────  │
│                                             │
│ 📖 Related Article                          │
│                                             │
│ How to Lower Your Credit Utilization       │
│ from NerdWallet • 8 min read              │
│                                             │
│ Learn proven strategies to reduce your     │
│ credit card utilization and improve your   │
│ credit score with these actionable tips.   │
│                                             │
│ [Read Full Article ↗]                      │
└─────────────────────────────────────────────┘
```

### Update UserRecommendationCard Component
- [ ] 29. Open `frontend/src/components/UserRecommendationCard.jsx`
- [ ] 30. Add same article display logic as RecommendationCard
- [ ] 31. Ensure consistent styling between components
- [ ] 32. Test with and without articles

### Update OperatorUserDetail Page
- [ ] 33. Open `frontend/src/pages/OperatorUserDetail.jsx`
- [ ] 34. Update recommendations table to show article info:
  - [ ] 35. Add "Article" column to table
  - [ ] 36. For recommendations with article:
    - [ ] 37. Display article title (truncated if long)
    - [ ] 38. Add "View Article" link (opens in new tab)
    - [ ] 39. Show article icon or badge
  - [ ] 40. For recommendations without article:
    - [ ] 41. Display "—" or "None" in Article column
- [ ] 42. In recommendation detail view:
  - [ ] 43. Show full article information if present
  - [ ] 44. Display article title, source, summary, reading time
  - [ ] 45. Add clickable link to article URL

### API Integration
- [ ] 46. Update `frontend/src/lib/apiService.js` if needed
- [ ] 47. Ensure getRecommendations() returns article objects
- [ ] 48. Parse article metadata (categories, persona_targets) if needed
- [ ] 49. Handle missing article gracefully (undefined/null checks)

### Testing Frontend Display
- [ ] 50. Start backend server
- [ ] 51. Start frontend dev server
- [ ] 52. Generate recommendations for test user
- [ ] 53. Navigate to User Dashboard
- [ ] 54. Verify article sections display for educational recs:
  - [ ] 55. Article title visible
  - [ ] 56. Source and reading time shown
  - [ ] 57. Summary text displayed (2-3 sentences)
  - [ ] 58. "Read Full Article" button present
  - [ ] 59. Button links to correct URL
  - [ ] 60. Link opens in new tab
- [ ] 61. Verify no article section for recs without articles
- [ ] 62. Verify no article section for product recommendations
- [ ] 63. Test responsive layout (mobile view)
- [ ] 64. Test hover states and interactions
- [ ] 65. Navigate to Operator User Detail
- [ ] 66. Verify article column shows article titles
- [ ] 67. Test "View Article" links work
- [ ] 68. Verify recommendations without articles show "—"

---

## PR #51: Unit Tests & Documentation

**Goal**: Add comprehensive unit tests for article matching and update documentation.

### Unit Tests - Article Matching
- [ ] 1. Create `backend/tests/test_article_matcher.py`
- [ ] 2. Create test fixtures:
  - [ ] 3. Sample articles (one per persona type)
  - [ ] 4. Sample recommendation texts (matching each persona)
  - [ ] 5. Mock Pinecone responses
- [ ] 6. Test `search_similar_articles()`:
  - [ ] 7. High utilization rec → credit/debt articles returned
  - [ ] 8. Variable income rec → budgeting articles returned
  - [ ] 9. Verify similarity scores in valid range (0-1)
  - [ ] 10. Verify top_k parameter works (returns correct number)
  - [ ] 11. Test with no matches found (empty result)
- [ ] 12. Test `select_best_article()`:
  - [ ] 13. Similarity > threshold → article returned
  - [ ] 14. Similarity < threshold → None returned
  - [ ] 15. Test different threshold values (0.5, 0.75, 0.9)
  - [ ] 16. Verify None returned when no articles exist
- [ ] 17. Test `match_articles_for_recommendations()`:
  - [ ] 18. Batch of 3 recs → verify article_ids attached appropriately
  - [ ] 19. Mixed results (some match, some don't) → verify correct assignments
  - [ ] 20. Verify similarity_scores logged for debugging

### Integration Tests
- [ ] 21. Create `backend/tests/test_article_recommendations_integration.py`
- [ ] 22. Test full flow for high_utilization user:
  - [ ] 23. Generate recommendations via API
  - [ ] 24. Verify educational recs have article_ids
  - [ ] 25. Verify article objects included in response
  - [ ] 26. Check article data is complete (title, source, url, summary)
  - [ ] 27. Verify product recs don't have article_ids
- [ ] 28. Test with all 5 persona types:
  - [ ] 29. Verify articles matched are topically relevant
  - [ ] 30. Check article persona_targets overlap with user persona
- [ ] 31. Test edge case: No articles meet threshold:
  - [ ] 32. Generate rec with obscure topic
  - [ ] 33. Verify article_id is NULL
  - [ ] 34. Verify recommendation generated successfully anyway
- [ ] 35. Test GET /recommendations/{user_id}:
  - [ ] 36. Verify article objects included in response
  - [ ] 37. Check nested article data correct
  - [ ] 38. Test with recommendations that have and don't have articles

### Performance Tests
- [ ] 39. Create `backend/tests/test_article_matching_performance.py`
- [ ] 40. Test embedding generation latency:
  - [ ] 41. Generate 10 recommendation embeddings
  - [ ] 42. Measure average time per embedding
  - [ ] 43. Target: <50ms per embedding
- [ ] 44. Test vector search latency:
  - [ ] 45. Perform 10 vector searches
  - [ ] 46. Measure average time per search
  - [ ] 47. Target: <100ms per search
- [ ] 48. Test end-to-end article matching:
  - [ ] 49. Match articles for 3 recommendations
  - [ ] 50. Measure total time
  - [ ] 51. Target: <300ms for 3 recs
- [ ] 52. Test recommendation generation with articles:
  - [ ] 53. Generate full set of recommendations (education + products + articles)
  - [ ] 54. Measure total latency
  - [ ] 55. Target: <6s total (acceptable for MVP)

### Run All Tests
- [ ] 56. Run test suite: `pytest backend/tests/ -v`
- [ ] 57. Verify all tests pass (target: 15+ new tests)
- [ ] 58. Check test coverage: `pytest --cov=backend/app/services`
- [ ] 59. Aim for >75% coverage on article_matcher service

### Documentation Updates
- [ ] 60. Update `README.md`:
  - [ ] 61. Add "Article Recommendations" section
  - [ ] 62. Document article catalog generation: `python scripts/generate_article_catalog.py`
  - [ ] 63. Document article seeding: `python scripts/seed_article_catalog.py`
  - [ ] 64. Document vector population: `python scripts/populate_article_vectors.py`
  - [ ] 65. Explain article matching logic (vector similarity, 0.75 threshold)
  - [ ] 66. Add note: "Articles are LLM-generated placeholders. Replace with real articles for production."
- [ ] 67. Update `docs/DECISIONS.md`:
  - [ ] 68. Add entry: "Article Recommendations via Vector Similarity Search"
  - [ ] 69. Rationale: Real-time matching, fast (<300ms), scales well
  - [ ] 70. Trade-offs: LLM-generated articles for MVP, placeholder URLs
  - [ ] 71. Future: Replace with real curated articles from reputable sources
  - [ ] 72. Implementation: Pinecone + OpenAI embeddings, 0.75 threshold
- [ ] 73. Update `docs/LIMITATIONS.md`:
  - [ ] 74. Add entry: "Article Recommendations"
  - [ ] 75. Limitation: Articles are LLM-generated placeholders, not real content
  - [ ] 76. Impact: Links don't lead to actual articles (placeholder URLs)
  - [ ] 77. Recommendation: Curate 30-50 real articles from NerdWallet, Investopedia, CFPB
  - [ ] 78. Process: Update article URLs + full_text, regenerate embeddings
- [ ] 79. Create `docs/ARTICLE_CATALOG.md`:
  - [ ] 80. Document article catalog structure
  - [ ] 81. Document vector similarity matching algorithm
  - [ ] 82. Document similarity threshold (0.75)
  - [ ] 83. Explain when articles are matched (educational recs only)
  - [ ] 84. Provide examples of good matches (persona + topic alignment)
  - [ ] 85. Document how to replace with real articles:
    - [ ] 86. Curate real articles manually
    - [ ] 87. Update article records in database (url, full_text)
    - [ ] 88. Regenerate embeddings: `python scripts/populate_article_vectors.py`
    - [ ] 89. Test matching quality with real articles

### Update PRD
- [ ] 90. Append article recommendations feature to PRD.md
- [ ] 91. Include overview, goals, database schema
- [ ] 92. Include vector matching flow diagram
- [ ] 93. Include frontend mockups
- [ ] 94. Include future enhancements (real articles, ML ranking)

---

## Summary

**Total Tasks**: 275+ subtasks across 6 PRs
**Expected Timeline**: 2.5-3.5 hours
**Expected Cost**: ~$0.30-0.50 for article generation (one-time)

**Key Features Delivered**:
- ✅ Article catalog with 50 LLM-generated articles (10 per persona)
- ✅ Articles seeded into database with full metadata
- ✅ Vector embeddings generated and stored in Pinecone
- ✅ Real-time article matching using vector similarity search (<300ms)
- ✅ Hybrid recommendations: 2-3 educational (with articles) + 1-2 products
- ✅ Frontend display of linked articles with "Read Full Article" button
- ✅ 15+ unit tests covering matching and performance
- ✅ Comprehensive documentation and migration guide

**Success Criteria**:
- Article catalog generated and seeded ✓
- Vector database populated with embeddings ✓
- 60-80% of educational recs get article matches (similarity >0.75) ✓
- Article matching adds <300ms to rec generation ✓
- UI displays articles with title, source, summary, reading time, link ✓
- Comprehensive test coverage (75%+) ✓
- Clear documentation for replacing with real articles ✓

**Future Enhancements**:
- Replace LLM-generated articles with real curated content (1-2 hours)
- Add ML-based ranking (combine vector similarity + user engagement data)
- Click tracking for article links (analytics)
- Article recommendation A/B testing
- User feedback on article relevance
- Expand article catalog to 100+ articles
- Multi-article recommendations (show top 3, not just 1)
- Article summary generation (if full text not available)

---

**Note on Real Articles**: Articles are currently LLM-generated placeholders with fake URLs for MVP speed. To replace with real articles:
1. Manually curate 30-50 real articles from reputable sources (NerdWallet, Investopedia, CFPB, The Balance, Forbes)
2. Update article records in database with real URLs and full text
3. Regenerate embeddings using `populate_article_vectors.py`
4. Test matching quality improves with real content
5. Estimated time: 1-2 hours for curation

---

**End of Tasks - Part 12**

