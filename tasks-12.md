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