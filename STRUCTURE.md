# Project Structure

Knowledge Universe — Engineering education platform.

```
md-courses/
├── README.md              # Overview & quick start
├── STRUCTURE.md           # This file — directory guide
├── ARCHIVE.md             # Legacy docs status
├── TECH_DEBT.md           # Known tech debt
├── package.json           # Node.js project metadata
├── MERMAID_TEMPLATES.md   # Diagram templates (reference)
│
├── data/                  # Content + web server
│   ├── server.js          # Express-like HTTP server (no deps)
│   ├── read.html          # Single-page viewer app
│   ├── read.css           # Viewer styles (extracted)
│   ├── API.md             # API documentation
│   │
│   ├── 00-foundations/    # Core CS fundamentals
│   ├── 01-ai-ml/          # AI/ML engineering
│   │   ├── fundamentals/
│   │   ├── deep-learning/
│   │   ├── llm-engineering/
│   │   ├── agentic-ai/
│   │   ├── ai-production/
│   │   └── mlops/
│   │
│   ├── 02-data-engineering/
│   │   ├── storage-formats/
│   │   ├── processing/
│   │   ├── streaming/
│   │   ├── orchestration/
│   │   ├── warehouse-lakehouse/
│   │   └── data-quality-governance/
│   │
│   ├── 03-backend/        # Backend engineering (Go, Java, Python, TS)
│   ├── 04-frontend/       # Frontend (React focus)
│   ├── 05-cloud/          # Cloud (AWS, etc.)
│   ├── 06-devops/         # DevOps (Docker, CI/CD)
│   ├── 07-kubernetes/     # Kubernetes
│   ├── 08-databases/      # Database design & internals
│   ├── 09-distributed-systems/
│   ├── 10-messaging/      # Event systems (Kafka, RabbitMQ, SNS/SQS)
│   ├── 11-networking/     # TCP/IP, HTTP, TLS, DNS, LB
│   ├── 12-operating-systems/
│   ├── 13-security/
│   ├── 14-sre-observability/
│   ├── 15-system-design/  # High-level system design
│   ├── 16-microservices/
│   ├── 17-software-architecture/
│   ├── 18-performance-engineering/
│   ├── 19-testing/
│   ├── 20-interviews/     # Interview prep
│   ├── 21-roadmaps/       # Learning roadmaps
│   ├── 22-production-stories/
│   ├── 23-projects/       # Hands-on projects
│   ├── 24-low-level-design/
│   ├── 25-software-engineering/
│   ├── arch/              # Architecture reference
│   └── cheat-sheets/      # Quick reference sheets
│
├── .claude/               # Claude Code settings
└── .code-review-graph/    # Knowledge graph (auto-generated)
```

---

## Key Files

### Server

| File | Purpose |
|------|---------|
| `data/server.js` | Serves content & API (Node.js, no dependencies) |
| `data/API.md` | Complete API documentation |

### Viewer

| File | Purpose |
|------|---------|
| `data/read.html` | Single-page React-like app |
| `data/read.css` | Extracted styles (external) |

### Documentation

| File | Purpose |
|------|---------|
| `README.md` | Overview & setup |
| `STRUCTURE.md` | This file — explains layout |
| `ARCHIVE.md` | Legacy docs status |
| `TECH_DEBT.md` | Known issues |

---

## Numbering Convention

Domain folders are numbered for ordering:
- `00-` Foundations
- `01-` AI/ML
- `02-` Data Engineering
- ...
- `25-` Software Engineering

Helps organize ~25 major engineering domains.

---

## Content Format

All files are **Markdown** (`.md`) unless noted:
- Headers with anchors for navigation
- Code blocks with syntax highlighting
- Mermaid diagrams (graphs, flowcharts, UML)
- LAYER tags for difficulty levels (L1-L5)

---

## Getting Started

1. **Start server:**
   ```bash
   npm start
   # or: node data/server.js
   ```

2. **Open browser:**
   ```
   http://localhost:3000
   ```

3. **Browse content:**
   - Sidebar tree navigation
   - Search (sidebar input)
   - Full-text search (⌘K or ⌘F)

4. **API reference:**
   - See `data/API.md`

---

## Architecture

### Frontend (data/read.html)
- Single-page app (no framework)
- ~2000 lines (HTML + CSS + JS)
- Features: tree nav, TOC, search, themes, zoom, layers

### Backend (data/server.js)
- Tiny HTTP server (~300 lines)
- Zero dependencies (Node.js built-ins only)
- Routes: `/api/tree`, `/api/file`, `/api/search`, `/api/stats`

### Data (data/ folders)
- Markdown files (~350 total)
- Nested by domain & subdomain
- Mermaid diagrams embedded

---

## Commands

```bash
# Install (if using npm)
npm install

# Start server (port 3000)
npm start

# Custom port
node data/server.js 8080

# View API docs
cat data/API.md
```

---

## Maintenance

- **Update content:** Edit `.md` files in `data/` folders
- **Rebuild graph:** The knowledge graph (`.code-review-graph/`) auto-updates
- **Review legacy:** Check `ARCHIVE.md` for outdated docs
- **Track debt:** See `TECH_DEBT.md`
