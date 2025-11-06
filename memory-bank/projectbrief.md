# Project Brief: SpendSense

## Overview
SpendSense is a personalized financial education platform that transforms synthetic bank transaction data into actionable financial education through behavioral pattern detection, persona-based recommendations, and AI-generated content.

## Core Value Proposition
- Detects financial behavioral patterns from transaction data
- Assigns users to 1 of 5 educational personas
- Generates personalized, AI-powered financial education content
- Maintains strict consent and eligibility guardrails
- Provides operator oversight with approval workflows

## Project Context
Built for an AI engineering fellowship with emphasis on:
- Explainability (all recommendations have plain-language rationales)
- Consent management (strict opt-in requirements)
- Responsible AI practices (tone validation, no shaming language)
- Operator oversight (approval workflows before user visibility)

## Success Criteria (MVP)
- ✅ 75 synthetic users with realistic financial profiles
- ✅ 100% persona assignment coverage
- ✅ 100% recommendations have AI-generated rationales
- ✅ <5 second recommendation generation latency
- ✅ Full consent tracking and enforcement
- ✅ Operator approval workflow functional
- ✅ Working UI (operator + user views) - **MVP REQUIREMENT**
- ✅ Deployed to AWS Lambda

## Timeline
2-4 days (MVP focus)

## Key Constraints
- MVP must include functional React UI for integration testing
- Must use GPT-4o-mini for cost efficiency (not GPT-4)
- SQLite for MVP (can migrate to PostgreSQL later)
- No authentication in MVP (internal use only)
- Educational content only (not financial advice)

## Scope Boundaries
**In Scope (MVP):**
- Synthetic data generation (75 users)
- Feature detection pipeline (subscriptions, savings, credit, income)
- 5 persona assignment with prioritization
- AI recommendation generation (5 persona-specific endpoints)
- Guardrails (consent, tone, eligibility)
- Operator approval workflow
- React UI (operator + user views)
- Evaluation metrics and Parquet exports to S3
- AWS Lambda deployment

**Out of Scope (Stretch Goals):**
- Redis caching
- Vector database integration
- AWS RDS PostgreSQL migration
- Authentication/JWT
- Real bank data integration
- Mobile app

