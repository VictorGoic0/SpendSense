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

## Project Complete! 🎉

You now have a fully functional SpendSense MVP with:

**Data & Infrastructure:**
- ✅ Synthetic data generation (75 users, 272 accounts, 15,590 transactions)
- ✅ SQLite database with WAL mode for concurrency
- ✅ SQLAlchemy models for all 10 core tables
- ✅ Data ingestion API with bulk processing

**Feature Detection & Personas:**
- ✅ Feature detection service (4 signal types: subscriptions, savings, credit, income)
- ✅ Rules-based persona assignment (5 personas: high_utilization, variable_income, subscription_heavy, savings_builder, wealth_builder)
- ✅ 30-day and 180-day behavioral signal windows

**Recommendation Engine:**
- ✅ AI-powered educational recommendations (OpenAI GPT-4o-mini)
- ✅ Persona-specific prompt templates (5 optimized prompts)
- ✅ Context building service (token-efficient user data aggregation)
- ✅ Product catalog recommendations (20-25 LLM-generated products)
- ✅ Article catalog recommendations (50 LLM-generated articles, vector similarity matching)
- ✅ Hybrid recommendations (2-3 educational + 1-2 products + linked articles)

**Guardrails & Quality:**
- ✅ Tone validation (forbidden phrases, empowering language checks)
- ✅ Consent enforcement (no recommendations without opt-in)
- ✅ Eligibility filtering (income, credit, existing accounts)
- ✅ Mandatory disclosures appended to all recommendations

**Operator Interface:**
- ✅ Metrics dashboard (users, consent, approvals, latency, charts)
- ✅ User list page (pagination, filters, search)
- ✅ User detail page (personas, signals visualization, recommendations)
- ✅ Approval queue (bulk selection, individual actions)
- ✅ Override/reject workflows with audit trails

**User Interface:**
- ✅ User dashboard (recommendations display, consent management)
- ✅ Consent toggle with confirmation dialogs
- ✅ Recommendation cards with markdown rendering
- ✅ Article display with "Read Full Article" buttons

**Evaluation & Testing:**
- ✅ Evaluation system (coverage, explainability, latency metrics)
- ✅ 15+ unit tests (article matching, performance)
- ✅ Comprehensive test scripts for all services

**Documentation:**
- ✅ Memory bank system (project brief, context, patterns, progress)
- ✅ Decision log (DECISIONS.md)
- ✅ Product requirements document (PRD.md)
- ✅ Limitations documentation
- ✅ Performance testing documentation

**Architecture:**
- ✅ FastAPI backend with async support
- ✅ React 18 + Vite frontend
- ✅ Shadcn/ui component library
- ✅ Pinecone vector database integration (article matching)
- ✅ OpenAI embeddings (text-embedding-3-small)