# ArthSetu Frontend

React + TypeScript + Vite + Tailwind console for the ArthSetu API.

## Run

```bash
npm install
npm run dev            # http://localhost:5173
```

The dev server proxies `/api/*` to `http://localhost:8000` (the backend), so
start the API first (`python -m uvicorn backend.app.main:app --reload` from the
repo root). Override the target with `VITE_API_TARGET`.

For a deployed build, set `VITE_API_BASE_URL` to the API origin + prefix
(e.g. `https://api.example/api/v1`).

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Vite dev server with HMR |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Serve the production build |
| `npm run typecheck` | `tsc --noEmit` |

## Layout

```
src/
├── api/endpoints.ts     typed API client (one layer, matches Docs/API_CONTRACT.md)
├── lib/                 axios instance, query client, formatters, cn()
├── types/api.ts         response types mirrored from the contract
├── components/
│   ├── ui/              Button, Card, Badge, Table, Field, StatCard, States, …
│   ├── layout/          AppShell, Sidebar, Topbar
│   ├── Toast.tsx        toast provider + useToast()
│   └── ErrorBoundary.tsx
└── pages/               one file per route
```

Data fetching goes through TanStack Query; components never call axios directly.
Design tokens live as CSS variables in `src/index.css` and are surfaced to
Tailwind in `tailwind.config.js` (`brand`, `ink`, `line`, `ok/warn/danger`, …).
