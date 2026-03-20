# SpendSense — Frontend

React (Vite) SPA for the operator dashboard, user views, and recommendation workflows. Run everything in this folder; the app expects a running API (see [`../backend/README.md`](../backend/README.md)).

## Prerequisites

- **Node.js**: 20 LTS recommended (matches project conventions; check compatibility with `package.json` if you use another version)
- **Backend**: FastAPI on `http://localhost:8000` unless you override the API base URL (below)

## Setup

```bash
cd frontend
npm install
npm run dev
```

The dev server defaults to **http://localhost:5173** (Vite).

## Routes

Defined in `src/App.jsx`. Base URL in dev: **`http://localhost:5173`**.

| Path | Page | Who it’s for |
|------|------|----------------|
| `/` | Redirect | → `/operator/dashboard` |
| `/operator/dashboard` | `OperatorDashboard` | Operator — metrics, charts |
| `/operator/users` | `OperatorUserList` | Operator — browse users, copy **`user_id`** |
| `/operator/users/:userId` | `OperatorUserDetail` | Operator — signals, generate recs, per-user tools |
| `/operator/approval-queue` | `OperatorApprovalQueue` | Operator — pending / overridden / rejected recs |
| **`/user/:userId/dashboard`** | **`UserDashboard`** | **Customer view** (simulated end user) |

### Customer / user dashboard (`/user/:userId/dashboard`)

There is **no** link in the top nav to this route — open it **manually** in the browser.

1. Start backend + `npm run dev`.
2. Get a **customer** `user_id` (not an operator): **Operator → User List**, or `GET /users/` with `user_type=customer` in Swagger.
3. Visit:

   **`http://localhost:5173/user/<user_id>/dashboard`**

   Example (replace with a real id from your DB):

   `http://localhost:5173/user/usr_48fcb736-260e-4bc4-bbf7-1d267b24f9d6/dashboard`

**Behavior (matches `UserDashboard.jsx`):**

- Loads user, consent, and **approved** recommendations only (`getRecommendations(userId, 'approved')`).
- If **consent is off**, recommendations are hidden until the user grants consent on this page.
- Educational and product recs use separate card components; both appear when present and approved.

## Environment variables

Optional `.env` or `.env.local` in this directory:

| Variable | Purpose |
|----------|---------|
| `VITE_API_BASE_URL` | Base URL for the API. If unset, the client uses `http://localhost:8000`. |

Configured in `src/lib/api.js` via `import.meta.env.VITE_API_BASE_URL`.

**WSL / remote API**: If the browser runs on Windows and the API is only bound inside WSL, you may need a URL reachable from the host (for example the Windows host IP from WSL’s perspective, or `0.0.0.0` on the backend plus the correct host port).

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Dev server with HMR |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | ESLint |

## Tech stack

- **React** 18 — UI
- **Vite** — build and dev server
- **React Router** — routing
- **Shadcn/ui** (Radix primitives) — components
- **Tailwind CSS** — styling
- **Axios** — HTTP client
- **Recharts** — charts
- **Lucide React** — icons

Path alias: `@src` → `src/` (see `vite.config.js` and `jsconfig.json`).

## Project layout (this folder)

```
frontend/
├── src/
│   ├── components/     # UI + feature components (incl. components/ui)
│   ├── pages/          # Route-level pages
│   ├── lib/            # api.js, apiService.js, utils
│   ├── constants/
│   └── main.jsx
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## Deployment (Netlify)

Repo root `netlify.toml` uses base directory `frontend`, build `npm run build`, publish `dist/`. Client-side routing uses a SPA redirect (`/*` → `/index.html`).

## More context

Product overview, repo layout, and pointers to docs: [`../README.md`](../README.md).
