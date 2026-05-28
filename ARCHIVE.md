# Documentation Archive & Status

This document tracks the status of legacy implementation docs in the root directory.

## Outdated / Likely Stale

These docs likely need review or archival. They track implementation phases or enhancement projects that may be:
- Completed ✅
- Abandoned 🚫
- Superseded by newer approaches 🔄

| Document | Purpose | Status | Action |
|----------|---------|--------|--------|
| `PHASE_2_STATUS.md` | Phase 2 conversion tracking | ❓ Unclear | Review & archive or update |
| `ENHANCEMENT_FRAMEWORK.md` | Enhancement methodology | ❓ Unclear | Review or delete |
| `ENHANCEMENT_STATUS.md` | Enhancement progress tracker | ❓ Unclear | Review or delete |
| `BACKEND_CONVERSION_QUEUE.md` | Backend conversion queue | ❓ Unclear | Review or delete |
| `CONVERSION_REPORT_BACKEND.md` | Conversion report | ❓ Unclear | Review or delete |
| `DIAGRAM_ENHANCEMENT_IMPLEMENTATION.md` | Diagram enhancement plan | ❓ Unclear | Review or delete |
| `TIER2_BATCH_STRATEGY.md` | Tier 2 batch processing | ❓ Unclear | Review or delete |
| `SCAN_ALL_DOMAINS.md` | Domain scanning utility | ❓ Unclear | Review or delete |
| `ASCII_TO_MERMAID_CONVERSION.md` | ASCII → Mermaid converter | ❓ Unclear | Review or delete |
| `MERMAID_TEMPLATES.md` | Mermaid diagram templates | ✅ Reference | Keep (useful reference) |
| `TECH_DEBT.md` | Technical debt tracking | ❓ Unclear | Review — likely outdated |

---

## Current Documentation

| Document | Status | Purpose |
|----------|--------|---------|
| `README.md` | ✅ Current | Project overview & setup |
| `package.json` | ✅ Current | Node.js project metadata |
| `data/API.md` | ✅ Current | Server API documentation |

---

## Recommendation

**Immediate action:**
1. Review the 11 status/phase docs
2. If completed → delete
3. If abandoned → move to `docs/archive/` folder with explanatory note
4. If relevant → extract useful info into README.md or dedicated guide

**Why clean up?**
- Reduces confusion about project state
- Prevents developers following outdated instructions
- Improves repo clarity

---

## How to Archive

```bash
# Create archive folder
mkdir -p docs/archive

# Move outdated docs
mv PHASE_2_STATUS.md docs/archive/
mv ENHANCEMENT_FRAMEWORK.md docs/archive/
# ... etc

# Create index in docs/archive/README.md explaining why archived
```

---

## Quick Links

- **Active docs:** `README.md`, `data/API.md`, `package.json`
- **Reference:** `MERMAID_TEMPLATES.md`
- **To review:** All others in table above
