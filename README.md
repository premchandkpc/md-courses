# Engineering Knowledge Universe

Complete software, AI, data & distributed systems engineering knowledge base — **535 files**, **380K+ lines**, **30 domains**, **100+ real-world scenarios**, **77 interactive visualizations**.

**Status:** Phase 7 in progress (Frontend +25 files, Database +44 files, Cloud +61 files)

## Quick Start

```bash
npm start          # API + viewer on http://localhost:3000
make frontend      # React frontend on http://localhost:5173
make viz           # Both together
python3 server.py  # Python server (alternative)
```

## Architecture

| Layer | Tech | Description |
|-------|------|-------------|
| **Content** | Markdown + HTML | 474 files across 25 numbered domains in `data/` |
| **API Server** | Node.js (zero deps) | `data/server.js` — serves tree, file, search, stats at `/api/*` |
| **Alt Server** | Python (stdlib) | `server.py` — same API, no dependencies |
| **Legacy Viewer** | Vanilla JS SPA | `data/read.html` — ~2000 lines, no build step |
| **React Frontend** | React 19, Vite, TS, Tailwind v4, XState, Zustand | `frontend/` — proxies `/api` → `localhost:3000` |

## Domain Overview

| Domain | Files | Lines | Focus |
|--------|------:|------:|-------|
| 00-foundations | 3 | 489 | CS theory, DS&A, math |
| 01-ai-ml | 9 | 15,251 | AI/ML, deep learning, LLMs, agents, MLOps |
| 02-data-engineering | 8 | 9,402 | Batch/stream processing, Spark, Flink, lakehouse |
| 03-backend | 44 | 56,986 | Go, Java, Python, TS — internals, patterns |
| 04-frontend | 76 | 28,980 | React, Next.js, state, rendering, performance |
| 05-cloud | 19 | 15,573 | AWS deep dives (EC2, S3, Lambda, EKS, RDS, IAM) |
| 06-devops | 11 | 19,151 | CI/CD, Terraform, Docker, GitOps, DevSecOps |
| 07-kubernetes | 13 | 12,192 | Core K8s, networking, security, operators, service mesh |
| 08-databases | 72 | 37,893 | PostgreSQL, Redis, MySQL, NoSQL, indexing, tuning |
| 09-distributed-systems | 14 | 8,558 | Consensus (Raft/Paxos), CAP, replication, caching |
| 10-messaging | 15 | 11,842 | Kafka, RabbitMQ, SNS/SQS — internals, patterns |
| 11-networking | 14 | 10,680 | TCP/IP, HTTP/1.1-3, QUIC, gRPC, DNS, CDN, TLS |
| 12-operating-systems | 12 | 11,467 | Linux kernel, CPU scheduling, memory, I/O, IPC |
| 13-security | 5 | 6,414 | OWASP Top 10, auth/Z, cryptography, zero trust |
| 14-sre-observability | 4 | 5,243 | Prometheus, Grafana, OpenTelemetry, SLIs/SLOs |
| 15-system-design | 86 | 44,591 | 11 real-world systems (WhatsApp, Netflix, Twitter, Uber...) |
| 16-microservices | 12 | 10,262 | Decomposition, discovery, API gateways, sagas |
| 17-software-architecture | 2 | 1,993 | Architecture styles, DDD, CQRS, event sourcing |
| 18-performance-engineering | 4 | 5,581 | Profiling, JVM tuning, optimization patterns |
| 19-testing | 4 | 7,798 | Unit → E2E → chaos → performance testing |
| 20-interviews | 4 | 2,273 | Java, distributed systems, system design prep |
| 21-roadmaps | 4 | 2,523 | Backend, distributed systems, career roadmaps |
| 22-production-stories | 10 | 15,737 | 9 real-world incidents — outages, cascading failures |
| 23-projects | 4 | 4,757 | Build: distributed cache, queue, workflow engine |
| 24-low-level-design | 4 | 4,347 | Parking lot, elevator, chess — OOD, UML, design patterns |
| 25-software-engineering | 4 | 2,780 | Git internals, code review, technical writing |
| arch | 9 | 6,971 | Platform vision, knowledge graph, simulation engine |
| cheat-sheets | 13 | 6,253 | Quick-reference guides |
| components | 7 | 1,237 | Shared content components |

## Docs

| File | Purpose |
|------|---------|
| `STRUCTURE.md` | Directory layout & project organization |
| `AGENTS.md` | AI agent instructions for this repo |
| `data/API.md` | HTTP API reference (tree, file, search, stats) |
| `ARCHIVE.md` | Archive index (stale docs moved to `docs/archive/`) |

## Key Commands

```bash
make serve              # Node.js server on :3000
make frontend           # Vite dev server on :5173
make frontend-build     # Production build (tsc -b && vite build)
make frontend-typecheck # tsc --noEmit
make viz                # Node :3000 + Vite :5173 concurrently
make clean              # rm -rf frontend/node_modules frontend/dist
npm run lint --prefix frontend  # ESLint (React frontend only)
python3 server.py       # Python server on :3000
```

## Project Layout

```
├── data/              # Content + web server (the main thing)
│   ├── server.js      # Node.js API server (zero deps)
│   ├── read.html      # Legacy SPA viewer
│   ├── read.css       # Viewer styles
│   ├── API.md         # API docs
│   ├── 00-25/         # Numbered domain folders
│   ├── arch/          # Architecture reference
│   └── cheat-sheets/  # Quick reference
├── frontend/          # React 19 + Vite + TS app
├── scripts/           # Python utility scripts (batch enhancements)
├── docs/archive/      # Stale phase/initiative docs
├── AGENTS.md          # AI agent instructions
├── AI-REVIEW.md       # Comprehensive content inventory
├── Makefile           # Build/run commands
└── server.py          # Alternative Python server
```

## Quick Stats

| Metric | Value |
|--------|-------|
| Total content files | **535** (437 MD + 88 HTML) |
| Total lines of content | **~380K** |
| Code examples | **60K+** (93% syntax validated) |
| Interactive visualizations | 88 HTML files (D3.js) |
| Real-world scenarios | **120+** across all domains |
| Domains covered | 30 numbered (00-foundations through 25-software-engineering) |
| Languages | Python, JavaScript, TypeScript, SQL, Bash, Go, Java, Kotlin, Rust |
| Cloud platforms | AWS (extensive), Azure (Phase 7), GCP (Phase 7), multi-cloud (Phase 7) |
| Databases | PostgreSQL, MySQL, Redis, MongoDB, DynamoDB, Oracle (6 total, all documented) |
| Messaging | Kafka, RabbitMQ, gRPC, SNS/SQS, Pub/Sub |
| Orchestration | Kubernetes, Docker, ECS, EKS, GKE, AKS |
| Server deps | Zero (Node.js built-ins only) |

## Tech Stack

- **Runtime:** Node.js >=14 (server), Python 3 (alt server)
- **Frontend (legacy):** Vanilla JS, no framework, ~2000 lines
- **Frontend (modern):** React 19, TypeScript 6, Vite 8, Tailwind v4, XState 5, Zustand 5, Pixi.js 8, ECharts 6, xyflow 12
- **Content:** Markdown with Mermaid diagrams, D3.js/HTML visualizations

## Navigation

- **New learner?** Start: `21-roadmaps/`
- **System design?** Go: `15-system-design/` (86 files)
- **Database deep dives?** Check: `08-databases/` (72 files, 6 engines)
- **Production incidents?** See: `22-production-stories/`
- **API reference?** See: `data/API.md`
- **Inventory?** See: `AI-REVIEW.md`

## License

MIT
