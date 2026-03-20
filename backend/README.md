# SpendSense — Backend

FastAPI service, SQLite database (default), scripts for synthetic data and batch jobs. **Work from this directory** for Python setup and running the API.

## Prerequisites

- **Python** 3.11+
- **SQLite** — bundled with Python; DB file is created under this folder by default
- **OpenAI API key** — required for recommendation generation and optional catalog scripts

## Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # Linux, macOS, WSL
# Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## Environment variables

Create **`backend/.env`** (gitignored). The same template lives in **`example-env.md`** in this folder; copy from there when you want a file you can edit without opening the README.

### Example `.env` (also in `example-env.md`)

```env
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
# OPENAI_REASONING_MODEL=gpt-4o-mini   # optional; default is gpt-4o-mini in code

# Database Configuration
DATABASE_URL=sqlite:///./spendsense.db

# AWS Configuration (for S3 exports)
# If using AWS CLI credentials (aws configure), these are optional
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_DEFAULT_REGION=us-east-2
S3_BUCKET_NAME=spendsense-analytics-goico
```

Optional for hosted / multi-environment setups:

```env
ENVIRONMENT=dev   # dev | staging | prod
```

- **`DATABASE_URL`**: Relative SQLite paths (e.g. `sqlite:///./spendsense.db`) are resolved to **`backend/`** in code, so Uvicorn and CLI scripts behave the same whether you run from `backend/` or the repo root. For PostgreSQL, use your provider’s connection string.
- **SQLite absolute paths** (SQLAlchemy): `sqlite:///tmp/foo.db` is **not** `/tmp/foo.db` — it is a **relative** path `tmp/foo.db` from the process cwd, and fails if that folder does not exist (`unable to open database file`). For a Unix absolute path use **four** slashes: `sqlite:////tmp/foo.db`.
- **`OPENAI_API_KEY`**: Required for `/recommendations/generate/...` and any scripts that call OpenAI.
- **`OPENAI_REASONING_MODEL`** *(optional)*: Overrides the chat model for educational recommendations (default in code: **`gpt-4o-mini`**).

### Recommendation generation (OpenAI)

Configured in **`app/services/recommendation_engine.py`** (`generate_recommendations_via_openai`).

| Setting | Current choice | Notes |
|--------|----------------|--------|
| **Model** | **`gpt-4o-mini`** (default) | Cheaper than reasoning-tier minis (e.g. GPT-5-mini); override with `OPENAI_REASONING_MODEL` if you experiment. |
| **Temperature** | **`0`** | Minimum supported for this model — most deterministic. Runs at **0.75–1.0** produced noticeably worse, less on-prompt educational copy than **temperature 0** in practice. |
| **Logged cost estimate** | **$0.15 / 1M** input, **$0.60 / 1M** output | Matches 4o-mini–era pricing; update constants in code if you point `OPENAI_REASONING_MODEL` at another SKU. |

JSON **`response_format`** is unchanged (structured recommendations for parsing and guardrails).

## Run the API

With venv activated and cwd = `backend`:

**Development (auto-reload, single worker):**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Concurrent load locally (multiple workers, no reload):**

```bash
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

Workers help when long-running work (e.g. OpenAI calls) would otherwise block other requests; SQLite WAL mode is enabled in code for read concurrency.

Each worker runs app startup independently, so several processes can hit `create_all()` at once on an empty DB. That used to surface as `table ... already exists` on SQLite; `init_db()` now catches that race and retries so all workers start cleanly.

- API: **http://localhost:8000**
- Swagger: **http://localhost:8000/docs**
- ReDoc: **http://localhost:8000/redoc**

Tables are initialized on startup (`init_db` / migrations in `app/database.py`).

## Tech stack

- **FastAPI** — HTTP API
- **SQLAlchemy** — ORM
- **Pydantic** — validation
- **Uvicorn** — ASGI server
- **OpenAI SDK** — recommendations
- **python-dotenv**, **Faker**, **requests** — config, synthetic data, script HTTP calls
- **pandas**, **numpy**, **pyarrow**, **boto3** — evaluation and S3 parquet exports

## API routes (reference)

Base URL in development: `http://localhost:8000`. **Authoritative list**: Swagger UI at `/docs` (includes routers added after this doc, e.g. consent, products, evaluation).

### Root

#### `GET /`

- Returns API status, e.g. `{"message": "SpendSense API"}`.

### Ingestion

#### `POST /ingest/`

- Bulk ingest users, accounts, transactions, liabilities, and products.
- Body: `IngestRequest` with arrays for each entity type.
- Response: `IngestResponse` (counts, `duration_ms`).
- Order: users → accounts → transactions → liabilities → products; transactions batched in 1000s.

### Features

#### `POST /features/compute/{user_id}`

- Compute behavioral features for a user.
- Query: `window_days` (default 30, max 365).
- Response: `user_id`, `window_days`, `features`.

### Profile

#### `GET /profile/{user_id}`

- Profile with features and personas.
- Query: `window` optional (`30` or `180`); omit for both.

### Users

#### `GET /users/`

- Paginated users; query: `limit`, `offset`, `user_type`, `consent_status`.

#### `GET /users/{user_id}`

- Single user with personas (30d and 180d).

### Operator

#### `GET /operator/dashboard`

- Dashboard metrics: totals, consent, persona distribution, recommendation counts, latency metrics.

#### `GET /operator/users/{user_id}/signals`

- Operator view: user, `30d_signals`, `180d_signals`, personas.

### Personas

#### `POST /personas/{user_id}/assign`

- Assign persona from features; query: `window_days`.

#### `GET /personas/{user_id}`

- List personas; query: optional `window` (30 or 180).

### Recommendations

#### `POST /recommendations/generate/{user_id}`

- Generate (or return cached) recommendations; query: `window_days`, `force_regenerate`.

#### `GET /recommendations/{user_id}`

- List recommendations; query: `status`, `window_days`.

#### `POST /recommendations/{recommendation_id}/approve`

- Body: `RecommendationApprove` (operator_id, optional notes).

#### `POST /recommendations/{recommendation_id}/override`

- Body: `RecommendationOverride` (operator_id, reason; optional new title/content).

#### `POST /recommendations/{recommendation_id}/reject`

- Body: `RecommendationReject` (operator_id, reason).

#### `POST /recommendations/bulk-approve`

- Body: `BulkApproveRequest` (operator_id, `recommendation_ids`).

---

Additional endpoints (consent, product CRUD, evaluation runs and exports) are documented in **`/docs`**.

## Project layout (this folder)

```
backend/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── routers/
│   ├── services/
│   ├── prompts/
│   └── utils/
├── scripts/           # Run from repo root: python backend/scripts/<name>.py (venv active)
├── data/              # Synthetic JSON + product_catalog.json (generated / ingested)
├── requirements.txt
├── spendsense.db      # Local SQLite (gitignored)
└── example-env.md     # Copy-paste template for .env
```

## `backend/data/` (seeding inputs)

| File | Role |
|------|------|
| `synthetic_users.json` | Produced by `generate_synthetic_data.py`; ingested via API |
| `synthetic_accounts.json` | Same |
| `synthetic_transactions.json` | Same |
| `synthetic_liabilities.json` | Same |
| `product_catalog.json` | Product rows for `/ingest/` (often checked in or produced by a separate generator) |

## Data workflow (local) — **recommended order**

Use **venv active**. Commands below use the **repository root**; cwd does not affect which DB file is used (see `DATABASE_URL` above).

**Important:** run **`compute_all_features.py` before `assign_all_personas.py`**. Personas are computed from `UserFeature` rows; if you assign first, you only get low-confidence fallbacks or stale behavior until features exist.

| Step | What to run | API? | Notes |
|------|-------------|------|--------|
| 0 | Start Uvicorn | — | Creates tables on startup |
| 1 | `generate_synthetic_data.py` | No | Skip if `backend/data/synthetic_*.json` already look good |
| 2 | `run_ingest.py` | **Yes** | Loads all synthetic JSON → `POST /ingest/` |
| *(opt)* | `verify_ingest.py` | No | Row counts (direct DB) |
| 3 | `run_ingest_products.py` | **Yes** | Optional; needs `backend/data/product_catalog.json` |
| 4 | `compute_all_features.py` | No | 30d + 180d features for every user |
| 5 | `assign_all_personas.py` | No | Personas from features |

After **step 5** you can generate recommendations (needs `OPENAI_API_KEY`), use operator flows, etc. **Step 3** is only for product-offer / hybrid flows.

**`fix_general_wellness_personas.py`** — one-off migration helper: updates rows where `persona_type` is the legacy value `general_wellness`. If your DB never used that label, it will make **no changes**; safe to ignore.

## Scripts reference (all of `backend/scripts/`)

Everything below: `python backend/scripts/<file>.py` from repo root with `backend` venv active.

### Pipeline / batch (not `test_*.py` API harnesses)

| Script | Purpose |
|--------|---------|
| `generate_synthetic_data.py` | Build synthetic JSON seed files in `backend/data/`. |
| `run_ingest.py` | HTTP: load synthetic JSON → `POST /ingest/` (data load, not a test). |
| `verify_ingest.py` | Quick row counts + sample row (direct SQL). |
| `run_ingest_products.py` | HTTP: load `product_catalog.json` → `POST /ingest/`. |
| `compute_all_features.py` | Batch: compute features for all users (both windows). |
| `assign_all_personas.py` | Batch: assign personas for all users (both windows). |
| `evaluate.py` | Offline evaluation metrics, DB persistence, optional Parquet/S3 export (see also **`POST /evaluate/`** in Swagger). |

### Service / engine smoke scripts (direct DB; typical dependency order)

Run these when debugging logic — **not** required for a minimal happy path if you only use the API + batch steps above.

| Script | Rough prerequisite |
|--------|--------------------|
| `test_feature_detection.py` | Ingested transactions/accounts |
| `test_persona_assignment.py` | Features computed |
| `test_context_builder.py` | Features + personas |
| `test_openai_generation.py` | Context + **`OPENAI_API_KEY`** |
| `test_guardrails.py` | Users/features in DB |
| `test_product_matching.py` | Products ingested + features/personas |
| `test_product_eligibility.py` | Products + features/personas |
| `test_hybrid_recommendations.py` | Full user state + products for combined recs |
| `test_product_offer_model.py` | Sanity check `ProductOffer` create/query/delete (direct DB) |

### HTTP API smoke scripts (running server)

| Script | Exercises |
|--------|-----------|
| `test_get_recommendations.py` | `GET /recommendations/{user_id}` |
| `test_approve_recommendation.py` | Approve endpoint |
| `test_bulk_approve.py` | Bulk approve |
| `test_override_reject.py` | Override + reject |

### One-off maintenance

| Script | Purpose |
|--------|---------|
| `fix_general_wellness_personas.py` | Rewrites legacy `general_wellness` persona rows to `savings_builder` |

## Testing

- **Interactive API**: **http://localhost:8000/docs**
- **pytest**: if you add/use `tests/` under backend, run from `backend` per your layout; `scripts/test_*.py` files are **manual CLI harnesses**, not pytest. **`run_ingest.py`** and **`run_ingest_products.py`** are named separately — they load data via the API, not “tests” of behavior.

## Deployment (Railway — backend)

- Connect the repo; set env vars in the dashboard: `OPENAI_API_KEY`, `DATABASE_URL`, `S3_BUCKET_NAME`, `ENVIRONMENT`, AWS fields if used.
- Production-style serve: `uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000` (or platform default).
- PostgreSQL: point `DATABASE_URL` at the provider string; models are intended to work without SQLite-specific code paths for normal CRUD.

## More context

Product overview and monorepo map: [`../README.md`](../README.md).
