# Project Structure

Knowledge Universe — Engineering education platform.

```
md-courses/
├── AGENTS.md              # AI agent instructions
├── AI-REVIEW.md           # Comprehensive content inventory
├── ARCHIVE.md             # Archive index (stale docs moved)
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── ENHANCEMENTS_REPAIRS_ROADMAP.md  # Active enhancement roadmap
├── LICENSE                # MIT
├── Makefile               # Build/run commands
├── README.md              # Overview & quick start
├── SECURITY.md
├── STRUCTURE.md           # This file
├── package.json           # Node.js project metadata
├── server.py              # Python server (alternative)
│
├── data/                  # Content + web server
│   ├── server.js          # Node.js HTTP server (zero deps)
│   ├── read.html          # Legacy SPA viewer (~2000 lines)
│   ├── read.css           # Viewer styles
│   ├── API.md             # API documentation
│   ├── 00-foundations/    # CS fundamentals
│   ├── 01-ai-ml/          # AI/ML engineering (7 subdirs)
│   ├── 02-data-engineering/
│   ├── 03-backend/        # Backend (44 files, largest lines)
│   ├── 04-frontend/       # Frontend (76 files, expanded)
│   ├── 05-cloud/          # Cloud (19 files)
│   ├── 06-devops/         # DevOps (11 files)
│   ├── 07-kubernetes/     # Kubernetes (13 files)
│   ├── 08-databases/      # Database systems (72 files, merged)
│   ├── 09-distributed-systems/
│   ├── 10-messaging/
│   ├── 11-networking/
│   ├── 12-operating-systems/
│   ├── 13-security/
│   ├── 14-sre-observability/
│   ├── 15-system-design/  # System design (86 files, largest count)
│   ├── 16-microservices/
│   ├── 17-software-architecture/
│   ├── 18-performance-engineering/
│   ├── 19-testing/
│   ├── 20-interviews/
│   ├── 21-roadmaps/
│   ├── 22-production-stories/
│   ├── 23-projects/
│   ├── 24-low-level-design/
│   ├── 25-software-engineering/
│   ├── arch/              # Architecture reference (9 files)
│   ├── cheat-sheets/      # Quick reference (13 files)
│   └── components/        # Shared components (7 files)
│
├── frontend/              # Modern React app
│   ├── src/
│   │   ├── App.tsx        # Main app component
│   │   ├── main.tsx       # Entry point
│   │   ├── components/    # React components
│   │   ├── stores/        # Zustand stores
│   │   ├── machines/      # XState state machines
│   │   ├── engine/        # Core engine
│   │   ├── hooks/         # React hooks
│   │   ├── lib/           # Utilities
│   │   └── types/         # TypeScript types
│   ├── vite.config.ts     # Vite config (proxies /api → :3000)
│   └── package.json       # React 19, TS, Tailwind v4, XState, Zustand
│
├── scripts/               # Python utility scripts
│   ├── analyze-code-syntax.py
│   ├── batch-convert-backend.py
│   ├── batch7-embedder.py
│   ├── convert-diagrams.py
│   ├── enhance_files.py
│   ├── process_batch7.py
│   ├── scan-all-domains.py
│   ├── strip_placeholders.py
│   └── validate_syntax.py
│
├── docs/
│   └── archive/           # Stale phase/initiative docs (32 files)
│
├── .claude/               # Claude Code settings
├── .code-review-graph/    # Knowledge graph (auto-generated)
└── .gitignore
```

## Numbering Convention

Domain folders are numbered `00-` through `25-` for ordering:
- `00` Foundations → `25` Software Engineering

## Content Format

- **Markdown** (`.md`) with code blocks, Mermaid diagrams
- **HTML** (`.html`) with D3.js interactive visualizations (77 total)
- LAYER tags for difficulty levels (L1-L5) in some domains

## Key Files

| File | Purpose |
|------|---------|
| `data/server.js` | Serves content & API (Node.js, no dependencies) |
| `data/API.md` | Complete API documentation |
| `data/read.html` | Single-page viewer app |
| `data/read.css` | Viewer styles |
| `AGENTS.md` | AI agent instructions |
| `AI-REVIEW.md` | Content inventory & quality review |

## Commands

```bash
npm start                  # Start server (port 3000)
make frontend              # Start Vite dev server (port 5173)
make viz                   # Both together
make frontend-build        # Production build (tsc -b && vite build)
make frontend-typecheck    # TypeScript type check
node data/server.js 8080   # Custom port
```

## Architecture

### Server (data/server.js)
- Tiny HTTP server (~380 lines)
- Zero dependencies (Node.js built-ins only)
- Routes: `/api/tree`, `/api/file`, `/api/search`, `/api/stats`

### Legacy Viewer (data/read.html)
- Single-page app (no framework)
- ~2000 lines (HTML + CSS + JS inline)
- Features: tree nav, TOC, search, themes, zoom, layers

### React Frontend (frontend/)
- React 19 + Vite + TypeScript + Tailwind v4
- XState for state machines, Zustand for stores
- Pixi.js, ECharts, xyflow for visualizations

### Content (data/ folders)
- 474 files, ~365K lines across 28 directories
- 77 interactive HTML visualizations with D3.js
- Mermaid diagrams embedded in Markdown
