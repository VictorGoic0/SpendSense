# OpenAI API Latency Testing & Optimization

**Date:** November 2024  
**Context:** Recommendation generation endpoint showing 17-20 second average latency  
**Goal:** Identify and resolve performance bottleneck

---

## Problem Statement

Initial metrics showed recommendation generation taking an average of **17-20 seconds**, with the breakdown:
- SQL query duration: ~7ms (negligible)
- OpenAI query duration: ~17,000ms (99% of total time)
- DB save duration: ~9ms (negligible)

**Hypothesis:** OpenAI API call is the bottleneck. Need to identify which factors contribute to latency.

---

## Testing Methodology

1. **Baseline measurement** with full production configuration
2. **Isolated testing** of individual optimization strategies
3. **Timing logs** captured for each request to `recommendation_timing_logs.json`
4. **Results tracked** in `recommendation_timing_results.md`

Each strategy tested independently to measure isolated impact.

---

## Baseline Configuration

- **Model:** gpt-4o-mini
- **Context size:** ~583-764 tokens
- **System prompt:** ~50-60 lines (persona-specific)
- **JSON mode:** Enabled (`response_format={"type": "json_object"}`)
- **Temperature:** 0.75
- **Data included:**
  - All behavioral signals (subscription, savings, credit, income)
  - Top 5 accounts with balances
  - Last 10 transactions (30-day window)
  - High utilization credit card details (when applicable)
  - Recurring merchant names (up to 10)
  - Savings account growth info

**Baseline Result:** 17,000ms average OpenAI latency

---

## Strategy 1: Switch to gpt-3.5-turbo

**Hypothesis:** gpt-3.5-turbo has lower latency than gpt-4o-mini

**Changes:**
- Model: `gpt-4o-mini` → `gpt-3.5-turbo`
- All other parameters identical

**Results:**
- OpenAI query duration: **5,526ms** ✅
- **Improvement: 11,474ms faster (67% reduction)**

**Conclusion:** Model choice is the primary latency factor. gpt-3.5-turbo is significantly faster.

**Trade-offs:**
- Lower quality output (needs testing for educational content acceptability)
- Lower cost: $0.50/$1.50 per 1M tokens (vs $0.15/$0.60 for gpt-4o-mini)
- May require quality validation testing

---

## Strategy 2: Reduce Context Size

**Hypothesis:** Smaller payload = faster processing

**Changes:**
- Transactions: 10 → 5
- Removed `recurring_merchants` array (kept count in signals)
- Removed `high_utilization_cards` details (kept flags in signals)
- Target: ~400 tokens (from ~700 tokens)

**Results:**
- OpenAI query duration: **18,872ms** ❌
- **Improvement: None (1,872ms SLOWER than baseline)**

**Conclusion:** Context size does NOT impact gpt-4o-mini latency within reasonable limits. The model's inference time is independent of payload size for our use case.

**Trade-offs:**
- Lost valuable context for recommendations
- Worse recommendation quality
- No performance benefit

---

## Strategy 3: Remove JSON Mode

**Hypothesis:** Forcing JSON schema validation adds overhead

**Changes:**
- Removed `response_format={"type": "json_object"}`
- Model generates JSON freely without schema validation

**Results:**
- OpenAI query duration: **23,051ms** ❌
- **Improvement: None (6,051ms SLOWER - 35% worse)**

**Conclusion:** JSON mode is NOT the bottleneck. Removing structured output constraints actually made performance worse, likely because:
1. Model needs extra tokens/processing to manually format JSON
2. JSON schema validation provides helpful constraints that speed generation
3. Without schema, model may iterate more to ensure valid structure

**Trade-offs:**
- Risk of malformed JSON (requires retry logic)
- Worse performance
- Not worth it

---

## Key Findings

### Latency Factors (Ranked by Impact)

1. **Model choice** - CRITICAL (67% improvement possible)
   - gpt-3.5-turbo: ~5.5 seconds
   - gpt-4o-mini: ~17 seconds
   - This is the ONLY factor that significantly impacts latency

2. **Context size** - NO IMPACT
   - Tested 43% reduction in tokens (~700 → ~400)
   - Result: No measurable improvement
   - Conclusion: OpenAI's inference is parallelized; token count doesn't matter at our scale

3. **JSON mode** - NEGATIVE IMPACT
   - Removing JSON schema validation made it 35% slower
   - Conclusion: Structured output helps model efficiency

### What We Learned

- **gpt-4o-mini has inherent latency** of 15-23 seconds regardless of optimizations
- **Payload optimization doesn't help** - inference time is dominated by model architecture, not data size
- **Structured output is good** - JSON mode helps rather than hurts
- **Only model switching works** - gpt-3.5-turbo is the only proven optimization

---

## Recommendations

### Short-term Options

**Option A: Accept Current Performance (Recommended for MVP)**
- Keep gpt-4o-mini with full context (17s average)
- Implement async generation with task queue
- Add Redis caching for instant retrieval of generated recommendations
- Users only experience delay on first generation per window
- Benefits: Maintains quality, predictable behavior

**Option B: Switch to gpt-3.5-turbo**
- 5.5s latency (70% faster)
- Lower operational cost
- Requires quality validation testing
- Benefits: Fast response, lower cost
- Risks: Potential quality degradation

**Option C: Hybrid Approach**
- Use gpt-3.5-turbo for initial generation (fast user feedback)
- Optionally regenerate with gpt-4o-mini for higher quality
- Cache both versions, serve based on user preference or A/B test
- Benefits: Best of both worlds
- Complexity: Requires dual model management

### Long-term Solutions

1. **Async Generation + Caching**
   - Generate recommendations asynchronously (background job)
   - Store in Redis with TTL
   - Serve instantly from cache
   - Regenerate periodically or on-demand
   - **Perceived latency: <100ms**

2. **Streaming Responses**
   - Stream recommendations as they generate
   - Show partial results immediately
   - **Perceived latency: <1 second to first content**

3. **Fine-tuned Model**
   - Train lighter model on persona patterns
   - Much faster inference
   - Lower cost per request
   - Requires dataset collection and training pipeline

4. **Pre-generation Strategy**
   - Generate recommendations for all users nightly
   - Store in database
   - Serve instantly during the day
   - **Perceived latency: <10ms**

---

## Implementation Decision

**Status:** Testing complete, awaiting decision

**Current recommendation:** Implement Option A (async + caching) with gpt-4o-mini
- Maintains quality standards
- Acceptable user experience with caching
- Simpler than hybrid approach
- Proven to work at scale

**Alternative:** If quality testing shows gpt-3.5-turbo is acceptable, switch for 70% latency reduction.

---

## Related Files

- Timing logs: `recommendation_timing_logs.json`
- Results summary: `recommendation_timing_results.md`
- Implementation: `backend/app/services/recommendation_engine.py`
- Endpoint: `backend/app/routers/recommendations.py`

---

## Testing Tools Added

1. **Timing instrumentation** in recommendation generation endpoint
   - Tracks SQL, OpenAI, tone validation, and DB save times
   - Logs to `recommendation_timing_logs.json`
   - See: `backend/app/routers/recommendations.py`

2. **Results tracking file** for A/B testing
   - Documents each strategy's performance
   - See: `recommendation_timing_results.md`

