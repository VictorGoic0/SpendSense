# Decision Log

This document tracks key architectural and technical decisions made during the development of SpendSense.

## Technology Choices

### FastAPI
**Decision**: Use FastAPI for the backend API framework
**Rationale**: 
- Python-based, ideal for data processing pipelines (pandas, feature engineering)
- Built-in async support for concurrent requests
- Auto-generated API documentation
- Easy integration with SQLAlchemy

### SQLite for MVP
**Decision**: Use SQLite for MVP, with migration path to PostgreSQL
**Rationale**:
- Zero setup required
- Sufficient for 75 users in MVP
- Easy migration path to PostgreSQL for production
- File-based, easy to backup/restore

### React 18 + Vite
**Decision**: Use React 18 with Vite as build tool
**Rationale**:
- Modern React features
- Fast development experience with Vite
- Good compatibility with Shadcn/ui components

### Shadcn/ui Component Library
**Decision**: Use Shadcn/ui for UI components
**Rationale**:
- LLM-friendly component structure
- Modern, accessible components
- TailwindCSS-based, easy to customize
- Copy-paste components (not a dependency)

### OpenAI GPT-4o-mini
**Decision**: Use GPT-4o-mini for recommendation generation
**Rationale**:
- Cost-effective for MVP (~$0.15/$0.60 per 1M tokens)
- Sufficient quality for educational content
- Lower latency than GPT-4
- Can upgrade specific personas to GPT-4o if needed

### Separate Endpoints Per Persona
**Decision**: Create 5 separate OpenAI endpoints (one per persona)
**Rationale**:
- Dedicated system prompts optimized per persona
- Better context management (only relevant signals passed)
- Easier to tune tone and focus per persona
- Cost tracking per persona
- A/B testing individual personas

### Rules-Based Persona Assignment
**Decision**: Use deterministic rules-based logic instead of ML
**Rationale**:
- Fast and deterministic
- Fully explainable (no black box)
- Easy to debug and adjust
- No training data required

### UI on Day 1
**Decision**: Build React UI as MVP requirement on Day 1
**Rationale**:
- Essential for integration testing
- Ensures end-to-end flow works early
- Operator approval workflow requires UI
- User consent management requires UI

