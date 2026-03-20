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
