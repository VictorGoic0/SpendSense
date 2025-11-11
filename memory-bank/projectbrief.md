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
- ✅ Deployed to Railway (moved from AWS Lambda for ease of deployment)

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
- ✅ Synthetic data generation (75 users) - **COMPLETE**
- ✅ Feature detection pipeline (subscriptions, savings, credit, income) - **COMPLETE**
- ✅ 5 persona assignment with prioritization - **COMPLETE**
- ✅ AI recommendation generation (5 persona-specific endpoints) - **COMPLETE**
- ✅ Guardrails (consent, tone, eligibility) - **COMPLETE**
- ✅ Operator approval workflow - **COMPLETE**
- ✅ React UI (operator + user views) - **COMPLETE**
- ✅ Evaluation metrics - **COMPLETE**
- ✅ Parquet exports to S3 (PR #29) - **COMPLETE**
- ✅ Railway deployment - **COMPLETE**
  - Backend deployed to Railway for ease of deployment
  - Auto-seeding on startup
  - Environment variables configured via Railway dashboard

**In Scope (Performance Optimization):**
- ⏳ Redis caching layer (PR #31)
- ⏳ PostgreSQL migration (PR #32)
- ⏳ Scale synthetic data to 500-1,000 users (Future PR)
- ⏳ Vector database integration with Pinecone (PR #34-37)
- **Goal**: Achieve sub-1s recommendation latency (from 17s baseline)
- **Architecture**: Hybrid vector DB + OpenAI fallback

**Out of Scope (Future):**
- Authentication/JWT
- Real bank data integration (Plaid API)
- Mobile app
- Real-time transaction streaming

