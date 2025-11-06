# Limitations

This document outlines known limitations and constraints of the SpendSense MVP.

## Data Limitations

### Synthetic Data
- **Not Real Bank Data**: All transaction data is synthetically generated
- **Pattern Assumptions**: Generated patterns may not reflect actual user behavior
- **Limited Diversity**: 75 users may not capture full range of financial behaviors

## Technical Limitations

### Database
- **SQLite for MVP**: Not suitable for production scale or concurrent users
- **No Connection Pooling**: SQLite has limited concurrency support
- **Migration Required**: Must migrate to PostgreSQL for production

### AI/ML Limitations
- **Non-Deterministic Outputs**: GPT-4o-mini outputs vary between runs
- **Tone Validation**: Requires post-generation checks (may need regeneration)
- **Cost Scaling**: API costs scale linearly with user count
- **Latency**: ~2-3 seconds per recommendation generation

### Persona System
- **Simplification**: Real users may not fit neatly into 5 categories
- **Rules-Based**: May miss nuanced patterns that ML could detect
- **Prioritization**: Edge cases in multi-persona matches may need refinement

### Security
- **No Authentication**: MVP has no authentication (internal use only)
- **No Authorization**: No role-based access control in MVP
- **API Keys**: OpenAI API key stored in environment variables (not encrypted at rest)

### Scalability
- **Single Lambda Function**: All endpoints in one function (may need splitting)
- **No Caching**: No Redis caching in MVP (all recommendations regenerated)
- **No CDN**: Frontend served directly (no CDN optimization)

## Content Limitations

### Financial Advice
- **Educational Only**: Content is educational, not personalized financial advice
- **No Regulatory Compliance**: Not a registered financial advisor
- **Generic Recommendations**: May not account for individual circumstances

### Partner Offers
- **No Real Integrations**: Partner offers are educational suggestions only
- **No Affiliate Links**: No actual partner integrations in MVP

## Future Improvements

- Migrate to PostgreSQL for production
- Add Redis caching for recommendations
- Implement JWT authentication
- Add vector database for semantic content search
- Upgrade specific personas to GPT-4o for better quality
- Add real-time transaction processing
- Implement A/B testing framework

