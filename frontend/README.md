# PAEOS-FX Frontend

React + TypeScript + Vite application shell. Contains foundation scaffolding
only (tenant-aware API client, i18n, error boundary, platform-status view) — no
domain screens. Those arrive in their respective phases.

## Setup

```bash
npm install
npm run dev        # http://localhost:5173 (proxies /api to the backend)
```

## Scripts

- `npm run dev` — dev server with API proxy
- `npm run build` — type-check + production build
- `npm run typecheck` — TypeScript only
- `npm run preview` — preview the production build

Set `VITE_API_BASE` to point at a non-default backend (defaults to
`http://localhost:8000` via the dev proxy).
