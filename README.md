# SpendSense

Personalized financial education platform that transforms synthetic bank transaction data into actionable financial education through behavioral pattern detection, persona-based recommendations, and AI-generated content.

## Overview

SpendSense detects financial behavioral patterns from transaction data, assigns users to one of five educational personas, and generates personalized, AI-powered financial education content with strict consent management and operator oversight workflows.

## Tech Stack

- **Backend**: FastAPI (Python 3.11+), SQLite
- **Frontend**: React 18, Vite, Shadcn/ui, TailwindCSS
- **AI**: OpenAI GPT-4o-mini
- **Infrastructure**: AWS Lambda, API Gateway, S3

## Quick Start

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

- `backend/` - FastAPI application
- `frontend/` - React application
- `scripts/` - Utility scripts (data generation, evaluation)
- `data/` - Synthetic data files
- `docs/` - Documentation

