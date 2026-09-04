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
├── context/AuthContext  useAuth(): user, login, logout, can(role)
├── lib/                 axios instance (+ bearer token), query client, auth storage, formatters
├── types/api.ts         response types mirrored from the contract
├── components/
│   ├── ui/              Button, Card, Badge, Table, Field, StatCard, States, …
│   ├── layout/          AppShell, Sidebar, Topbar (user menu)
│   ├── RequireAuth.tsx  route guard (+ optional role)
│   ├── Toast.tsx        toast provider + useToast()
│   └── ErrorBoundary.tsx
└── pages/               one file per route (LoginPage, UsersPage, …)
```

Auth: `AuthContext` hydrates from `/auth/me` on load; the axios interceptor
attaches the bearer token and redirects to `/login` on `401`. `can("reviewer")`
etc. gate role-specific actions. `RequireAuth` guards the routes.

Data fetching goes through TanStack Query; components never call axios directly.
Design tokens live as CSS variables in `src/index.css` and are surfaced to
Tailwind in `tailwind.config.js` (`brand`, `ink`, `line`, `ok/warn/danger`, …).
