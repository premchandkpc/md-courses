# Engineering Knowledge Universe — AGENTS.md

## Two Servers

| Server | Command | Port | Dependencies |
|--------|---------|------|-------------|
| Node.js (primary) | `node packages/api-server/server.js` | 3000 | Zero (Node built-ins only) |
| Python (alt) | `python3 packages/python-server/server.py` | 3000 | Zero (stdlib only) |

Preferred: `make serve` or `npm start` (both run `node packages/api-server/server.js`).

## Two Frontends

| Frontend | Location | Tech | Start Command |
|----------|----------|------|---------------|
| Legacy SPA | `packages/legacy-viewer/read.html` | Vanilla JS, ~2000 lines | Served by Node.js on :3000 |
| Modern React | `packages/react-frontend/` | React 19, Vite, TS, Tailwind v4, XState, Zustand | `make frontend` (Vite :5173, proxies /api → :3000) |

React frontend proxies `/api` → `localhost:3000` (see `packages/react-frontend/vite.config.ts`).
Run both together: `make viz` (starts Node on :3000 + Vite on :5173).

## Content Layout

- All content lives in `content/` as Markdown (`.md`) + HTML (`.html`) files.
- 736 files (417 MD + 311 HTML + 8 other), ~380K lines across 25 numbered domain folders + `arch/`, `cheat-sheets/`, `components/`, `paths/`, `html-visualizations/`.
- Served via JSON API at `/api/tree`, `/api/file?path=...`, `/api/search?q=...`, `/api/stats`.

## Largest Domains

| Domain | Files | Lines |
|--------|------:|------:|
| 15-system-design | 86 | 44,591 |
| 04-frontend | 76 | 28,980 |
| 08-databases | 72 | 37,893 |
| 03-backend | 44 | 56,986 |

## Key Commands

```bash
make serve              # Node.js server on :3000
make frontend           # Vite dev server on :5173
make frontend-build     # Production build (tsc -b && vite build)
make frontend-typecheck # tsc --noEmit
make viz                # Node :3000 + Vite :5173 concurrently
make clean              # rm -rf packages/react-frontend/node_modules packages/react-frontend/dist
npm run lint -w packages/react-frontend  # ESLint (React frontend only)
python3 packages/python-server/server.py       # Python server on :3000
```

No tests, no CI, no lint for the main project.

## Scripts

All batch conversion utilities are in `scripts/` (Python):
`analyze-code-syntax.py`, `batch-convert-backend.py`, `batch7-embedder.py`, `convert-diagrams.py`, `enhance_files.py`, `process_batch7.py`, `scan-all-domains.py`, `strip_placeholders.py`, `validate_syntax.py`.

## Node Requirement

`packages/api-server/server.js` requires Node >=14 (per `package.json` `engines`).

## Known Gotchas

- `packages/legacy-viewer/read.html` is a **vanilla JS SPA** — no React, no bundler. Edit the file directly.
- The React frontend (`packages/react-frontend/`) is a separate app with its own `package.json`, TypeScript config, and ESLint.
- `content/08-databases/` has 72 files (merged legacy `data/databases/` dir).
- 04-frontend has 76 files — React/JS content was expanded significantly.
- Stale phase/docs moved to `docs/archive/`. Utility scripts in `scripts/`.
- AUX files (`.DS_Store`) accumulate easily — clean with `find . -name '.DS_Store' -delete`.
