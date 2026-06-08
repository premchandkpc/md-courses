# Project Structure

Knowledge Universe — Engineering education platform.

```
md-courses/
├── content/                         # All content (was data/ domains)
│   ├── 00-foundations/ … 25-*/     # 26 numbered domain folders
│   ├── arch/                        # Architecture reference (9 files)
│   ├── cheat-sheets/                # Quick reference (13 files)
│   ├── components/                  # Shared components (8 files)
│   ├── html-visualizations/         # 220 standalone D3.js viz files
│   └── API.md                       # HTTP API reference
│
├── packages/                        # Monorepo (npm workspaces)
│   ├── api-server/                  # Node.js HTTP server
│   │   └── server.js                # Zero deps, ~380 lines
│   ├── legacy-viewer/               # Vanilla JS SPA
│   │   ├── read.html                # ~2000 lines (inline HTML+CSS+JS)
│   │   └── read.css                 # Viewer styles
│   ├── python-server/               # Python alt server
│   │   └── server.py                # Stdlib only
│   └── react-frontend/              # Modern React app
│       ├── src/
│       │   ├── App.tsx / main.tsx
│       │   ├── components/ / stores/ / machines/
│       │   ├── engine/ / lib/ / types/
│       └── vite.config.ts / package.json
│
├── scripts/                         # Python utility scripts
├── docs/
│   └── archive/                     # Stale phase/initiative docs
│
├── AGENTS.md / AI-REVIEW.md
├── ARCHIVE.md / STRUCTURE.md
├── README.md / LICENSE / Makefile
├── package.json                     # Root workspace config
├── CONTRIBUTING.md / CODE_OF_CONDUCT.md / SECURITY.md
└── .gitignore / .github/
```

## Numbering Convention

Domain folders are numbered `00-` through `25-` for ordering:
- `00` Foundations → `25` Software Engineering

## Content Format

- **Markdown** (`.md`) with code blocks, Mermaid diagrams
- **HTML** (`.html`) with D3.js interactive visualizations (88 in content/ + 220 in html-visualizations/)
- LAYER tags for difficulty levels (L1-L5) in some domains

## Key Files

| File | Purpose |
|------|---------|
| `packages/api-server/server.js` | Serves content & API (Node.js, no deps) |
| `content/API.md` | Complete API documentation |
| `packages/legacy-viewer/read.html` | Single-page viewer app |
| `AGENTS.md` | AI agent instructions |
| `AI-REVIEW.md` | Content inventory & quality review |

## Commands

```bash
npm start                  # Start server (port 3000)
make frontend              # Start Vite dev server (port 5173)
make viz                   # Both together
make frontend-build        # Production build (tsc -b && vite build)
make frontend-typecheck    # TypeScript type check
node packages/api-server/server.js 8080   # Custom port
```

## Architecture

### Server (packages/api-server/server.js)
- Tiny HTTP server (~380 lines)
- Zero dependencies (Node.js built-ins only)
- Routes: `/api/tree`, `/api/file`, `/api/search`, `/api/stats`

### Legacy Viewer (packages/legacy-viewer/read.html)
- Single-page app (no framework)
- ~2000 lines (HTML + CSS + JS inline)
- Features: tree nav, TOC, search, themes, zoom, layers

### React Frontend (packages/react-frontend/)
- React 19 + Vite + TypeScript + Tailwind v4
- XState for state machines, Zustand for stores
- Pixi.js, ECharts, xyflow for visualizations

### Content (content/ folders)
- 535 files across 30 domain directories
- 88 interactive HTML visualizations with D3.js in content/
- 220 standalone viz files in content/html-visualizations/
- Mermaid diagrams embedded in Markdown
