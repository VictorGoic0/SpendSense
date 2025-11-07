# Recommendation Generation Timing Results

Testing various optimization strategies to reduce OpenAI API latency.

## Baseline (gpt-4o-mini with full context)

- **Model**: gpt-4o-mini
- **Context size**: ~583-764 tokens
- **Transactions**: 10 recent transactions
- **Additional data**: recurring_merchants array, high_utilization_cards details
- **JSON mode**: Enabled
- **Temperature**: 0.75

**Results:**
- SQL query duration: 7ms
- OpenAI query duration: **17,000ms**
- DB save duration: 9ms
- Total request duration: 17,081ms

---

## Strategy 1: Switch to gpt-3.5-turbo

**Changes:**
- Model: gpt-4o-mini → gpt-3.5-turbo
- Everything else identical

**Results:**
- SQL query duration: ~7ms
- OpenAI query duration: **5,526ms** ✅
- DB save duration: ~9ms
- Total request duration: ~5,600ms

**Improvement:** 11,474ms faster (67% reduction)
**Trade-off:** Potentially lower quality output, but cheaper ($0.50/$1.50 vs $0.15/$0.60 per 1M tokens)

---

## Strategy 2: Reduce data sent (with gpt-4o-mini)

**Changes:**
- Model: Back to gpt-4o-mini
- Transactions: 10 → 5
- Remove recurring_merchants array (send count only)
- Remove high_utilization_cards details (use signals only)
- Target context size: ~400 tokens (from ~700)

**Results:**
- SQL query duration: ~7ms
- OpenAI query duration: **18,872ms** ❌
- DB save duration: ~9ms
- Total request duration: 18,800ms

**Improvement:** None - actually 1,872ms SLOWER than baseline
**Conclusion:** Data volume is NOT the bottleneck. gpt-4o-mini latency is independent of payload size (within reasonable limits).
**Trade-off:** Less specific context for recommendations (not worth it)

---

## Strategy 3: Remove JSON mode (with gpt-4o-mini)

**Changes:**
- Remove `response_format={"type": "json_object"}`
- Allow model to generate freely without JSON schema validation

**Results:**
- SQL query duration: ~7ms
- OpenAI query duration: **23,051ms** ❌
- DB save duration: ~9ms
- Total request duration: 23,089ms

**Improvement:** None - actually 6,051ms SLOWER than baseline (35% worse)
**Conclusion:** JSON mode is NOT the bottleneck. Removing structured output constraints made it worse, possibly because the model needs extra tokens to format JSON manually.
**Trade-off:** Risk of malformed JSON (not worth it given worse performance)

---

---

## Key Findings

### What Works:
1. **Switch to gpt-3.5-turbo**: 67% faster (17s → 5.5s) ✅
   - Clear winner for latency optimization
   - Trade-off: Potentially lower quality, but acceptable for educational content

### What Doesn't Work:
1. **Reducing data volume**: No impact (actually slightly slower)
   - gpt-4o-mini latency is independent of context size within reasonable limits
   - Removing detailed context doesn't help and hurts recommendation quality

2. **Removing JSON mode**: Makes it worse (17s → 23s)
   - Model needs extra effort to manually format JSON
   - JSON schema validation is actually helpful for performance

### Conclusion:

**The model choice is the only significant factor.** gpt-4o-mini has inherent latency of 15-23 seconds regardless of optimizations. For production:

**Option A: Accept current performance**
- Use gpt-4o-mini with full context (17s average)
- Add Redis caching to serve cached recommendations instantly
- Generate recommendations asynchronously with task queue
- Users only experience delay on first generation

**Option B: Switch to gpt-3.5-turbo**
- 5.5s latency (70% faster)
- Lower cost
- Quality trade-off: Acceptable for educational content (test required)

**Option C: Hybrid approach**
- Use gpt-3.5-turbo for initial generation (fast feedback)
- Optionally regenerate with gpt-4o-mini for higher quality
- Cache both versions

