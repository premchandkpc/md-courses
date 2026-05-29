# Engineering Knowledge Universe — AGENTS.md

## Two Servers

| Server | Command | Port | Dependencies |
|--------|---------|------|-------------|
| Node.js (primary) | `node data/server.js` | 3000 | Zero (Node built-ins only) |
| Python (alt) | `python3 server.py` | 3000 | Zero (stdlib only) |

Preferred: `make serve` or `npm start` (both run `node data/server.js`).

## Two Frontends

| Frontend | Location | Tech | Start Command |
|----------|----------|------|---------------|
| Legacy SPA | `data/read.html` | Vanilla JS, ~2000 lines | Served by Node.js on :3000 |
| Modern React | `frontend/` | React 19, Vite, TS, Tailwind v4, XState, Zustand | `make frontend` (Vite :5173, proxies /api → :3000) |

React frontend proxies `/api` → `localhost:3000` (see `frontend/vite.config.ts`).
Run both together: `make viz` (starts Node on :3000 + Vite on :5173).

## Content Layout

- All content lives in `data/` as Markdown (`.md`) + HTML (`.html`) files.
- Organized by numbered domain folders: `00-foundations/` through `25-software-engineering/`.
- Plus `arch/`, `cheat-sheets/`.
- Served via JSON API at `/api/tree`, `/api/file?path=...`, `/api/search?q=...`, `/api/stats`.

## Key Commands

```bash
make serve              # Node.js server on :3000
make frontend           # Vite dev server on :5173
make frontend-build     # Production build (tsc -b && vite build)
make frontend-typecheck # tsc --noEmit
make viz                # Node :3000 + Vite :5173 concurrently
make clean              # rm -rf frontend/node_modules frontend/dist
python3 server.py       # Python server on :3000
```

No tests, no CI, no lint for the main project. React frontend has ESLint (`npm run lint --prefix frontend`).

## Utility Scripts (root, Python)

Used for batch content enhancements and conversions (past phases):
`analyze-code-syntax.py`, `batch-convert-backend.py`, `batch7-embedder.py`, `convert-diagrams.py`, `enhance_files.py`, `process_batch7.py`, `scan-all-domains.py`, `strip_placeholders.py`, `validate_syntax.py`.

## Node Requirement

`data/server.js` requires Node >=14 (per `package.json` `engines`).
`server.py` requires Python 3.

## Known Gotchas

- `data/read.html` is a **vanilla JS SPA** — no React, no bundler. Edit the file directly.
- The React frontend (`frontend/`) is a separate app with its own `package.json` and TypeScript config.
- README stats are outdated (says 228 files / 203K lines; actual is ~535 files / 380K+ lines).
- AUX files (`.DS_Store`) accumulate easily — clean with `find . -name '.DS_Store' -delete`.
- `data/databases/` was merged into `data/08-databases/`. The source directory no longer exists.
