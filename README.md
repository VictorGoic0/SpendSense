# SpendSense

**Personalized Financial Education Platform**

SpendSense turns synthetic bank-like transaction data into financial education: behavioral signals, persona assignment, AI-generated recommendations (with operator review), consent, and optional product-style offers. The repo is a **monorepo**: Python API in `backend/`, React UI in `frontend/`.

## Documentation map

| Doc | Purpose |
|-----|---------|
| **[backend/README.md](backend/README.md)** | Python venv, **`DATABASE_URL` / `.env`**, Uvicorn, API overview, scripts, ingestion workflow, Railway |
| **[frontend/README.md](frontend/README.md)** | Node, `npm install`, dev server, **`VITE_API_BASE_URL`**, build, Netlify |

Setup on a new machine (including **WSL**): open the README in the folder you are working in—no need to hunt here for ports or env vars.

## Table of contents

- [Overview](#overview)
- [Key features](#key-features)
- [Quick start](#quick-start)
- [Tech stack (summary)](#tech-stack-summary)
- [Project structure](#project-structure)
- [Additional resources](#additional-resources)

---

## Overview

- **Pattern detection** — Subscriptions, savings, credit, income signals from transactions.
- **Personas** — e.g. high utilization, variable income, subscription-heavy, savings/wealth builders.
- **Recommendations** — OpenAI-backed generation; operator approve / reject / override; consent-gated for end users.
- **Governance** — Audit-friendly flows and guardrails; evaluation and parquet export paths exist on the backend.

---

## Key features

- Behavioral feature computation (20+ signals) and 30d / 180d windows  
- Persona assignment from features  
- AI recommendations with operator queue and bulk actions  
- Consent tracking and history  
- Operator dashboard and user-facing dashboard  
- Product catalog ingestion and hybrid educational + product recommendations (see OpenAPI for full surface)

---

## Quick start

1. **API**: Follow [backend/README.md](backend/README.md) (venv, `.env`, `uvicorn`). Default API: `http://localhost:8000`, docs at `/docs`.
2. **UI**: Follow [frontend/README.md](frontend/README.md). Default app: `http://localhost:5173`.

CORS is configured for local Vite ports; if you change origin or API URL, adjust backend CORS and/or `VITE_API_BASE_URL`.

---

## Tech stack (summary)

| Area | Stack |
|------|--------|
| Backend | FastAPI, SQLAlchemy, Pydantic, SQLite (default), Uvicorn, OpenAI SDK (educational recs: **gpt-4o-mini**, **temperature 0** — see `backend/README.md`) |
| Frontend | React 18, Vite, React Router, Shadcn/ui, Tailwind, Axios, Recharts |
| Ops / data | Optional AWS S3 for exports; Railway (backend) and Netlify (frontend) documented in per-folder READMEs |

Version details and commands: **backend** and **frontend** READMEs above.

---

## Project structure

```
SpendSense/
├── backend/           # FastAPI app — see backend/README.md
├── frontend/          # Vite + React — see frontend/README.md
├── backend/scripts/   # CLI helpers (run as python backend/scripts/... from repo root)
├── backend/data/      # Synthetic JSON, product catalog (generated / ingested)
├── docs/              # ADRs, limitations, performance notes
├── memory-bank/       # Project context for contributors
├── PRD.md
├── architecture.mermaid
├── netlify.toml       # Frontend deploy (base: frontend)
└── README.md          # This file
```

---

## Additional resources

- **OpenAPI**: `/docs` on a running server (always current).  
- **Product**: [PRD.md](PRD.md)  
- **Architecture**: [architecture.mermaid](architecture.mermaid)  
- **Decisions / limits**: [docs/](docs/)  
- **Contributor context**: [memory-bank/](memory-bank/)
