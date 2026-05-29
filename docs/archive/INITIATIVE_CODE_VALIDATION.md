# Initiative Tracking: Code Validation & Syntax Sweep

**Initiative:** 60K+ code examples validation (7 languages, 30 domains)  
**Owner:** [QA engineer]  
**Phase:** 7.1-7.3 (Weeks 2-24)  
**Status:** Planned  
**Last Updated:** 2026-05-29

---

## Overview

Validate 60,000+ code examples across 437 markdown files using language-specific syntax checkers. Target 93% pass rate (56K+ examples). Fix high-risk domains (SQL 85%, Bash 90%). Integrate validation into CI/CD to prevent future regressions.

**Effort:** 120 hours (Phase 1-2: tooling + high-risk fixes)  
**Timeline:** 3 weeks foundation + 8 weeks maintenance  
**Team:** 1 QA engineer + 1-2 developer contractors (for fixes)  
**Success Metric:** 93% pass rate achieved; validate_syntax.py running in CI/CD; all regressions <1% per month

---

## Deliverables Checklist

### Phase 1: Tooling & Setup (Weeks 2-3)

- [ ] **validate_syntax.py** deployed (850 lines, production-ready) — Est: 12 hrs
- [ ] **Language validators** configured:
  - [ ] Python (ast.parse) — Est: 2 hrs
  - [ ] JavaScript (node --check) — Est: 2 hrs
  - [ ] TypeScript (tsc --noEmit) — Est: 3 hrs
  - [ ] SQL (sqlglot for multi-dialect) — Est: 4 hrs
  - [ ] Bash (shellcheck + sh -n) — Est: 4 hrs
  - [ ] Go (go build) — Est: 2 hrs
  - [ ] Java (javac) — Est: 3 hrs
- [ ] **CI/CD integration** (GitHub Actions) — Est: 8 hrs
- [ ] **Baseline report** (current state: find all failures) — Est: 6 hrs
- [ ] **validation_config.yaml** created — Est: 4 hrs

**Phase 1 Total:** 50 hours / 2 weeks

---

### Phase 2: High-Risk Domain Fixes (Weeks 4-8)

**SQL (Target: 85% → 95% pass)**
- [ ] Identify multi-dialect failures (PostgreSQL vs MySQL vs Oracle) — Est: 8 hrs
- [ ] Add dialect markers to examples (e.g., `<!-- SQL: PostgreSQL -->`) — Est: 6 hrs
- [ ] Fix schema-dependent examples (qualify tables, use test schemas) — Est: 10 hrs
- [ ] Test with sqlglot validator — Est: 4 hrs
- **SQL Subtotal:** 28 hours

**Bash (Target: 90% → 96% pass)**
- [ ] Identify environment-dependent failures (hardcoded paths, globbing) — Est: 8 hrs
- [ ] Fix PATH/shell assumptions — Est: 8 hrs
- [ ] Test with shellcheck — Est: 4 hrs
- [ ] Add setup instructions (prerequisites) — Est: 4 hrs
- **Bash Subtotal:** 24 hours

**Java (Target: 95% → 98% pass)**
- [ ] Verify version compatibility (Java 8 vs 17 syntax) — Est: 6 hrs
- [ ] Fix version-specific failures — Est: 4 hrs
- **Java Subtotal:** 10 hours

**Other languages (Python, JS, TS, Go)**
- [ ] Batch validation + minor fixes — Est: 12 hrs
- **Other Subtotal:** 12 hours

**Phase 2 Total:** 74 hours / 4 weeks

---

### Phase 3: CI/CD Integration & Monitoring (Weeks 9-11)

- [ ] **GitHub Actions workflow** configured — Est: 8 hrs
  - Pre-commit hook: validate changed files
  - CI trigger: full suite validation on PR
  - Report generation: JSON + markdown output
- [ ] **Regression monitoring** dashboard — Est: 6 hrs
- [ ] **Automated failure alerts** (Slack) — Est: 4 hrs
- [ ] **Monthly baseline report** automation — Est: 4 hrs

**Phase 3 Total:** 22 hours / 3 weeks

---

### Phase 4: Ongoing Maintenance (Weeks 12+)

- [ ] **Weekly review** of new failures — Est: 2 hrs/week
- [ ] **Monthly fixes** (address regression creep) — Est: 4 hrs/month
- [ ] **Quarterly dependency updates** (language versions) — Est: 3 hrs/quarter
- [ ] **Contractor support** for bulk fixes (as needed) — Est: 40 hrs/quarter (reserve)

**Phase 4 (Ongoing):** ~30 min/week baseline; scale with new content

---

## Language-Specific Metrics

### Current State (Pre-Validation)

| Language | Count | Validator | Est Pass | High Risk? | Priority |
|----------|-------|-----------|----------|-----------|----------|
| Python | 8,500 | ast.parse | 98% | NO | 5 |
| SQL | 7,200 | sqlglot | 85% | **YES** | 1 |
| JavaScript | 6,800 | node --check | 99% | NO | 3 |
| Bash | 6,200 | shellcheck | 90% | **YES** | 1 |
| Java | 5,100 | javac | 95% | MEDIUM | 2 |
| Go | 4,600 | go build | 92% | MEDIUM | 2 |
| TypeScript | 3,800 | tsc --noEmit | 97% | NO | 4 |
| Other | 12,000 | Mixed | 88% | MEDIUM | 3 |
| **TOTAL** | **60,000** | — | **93%** | — | — |

---

## Weekly Progress

### Week 1 (Phase 7.0: Kickoff)
- [ ] Agent 5 deliverables reviewed
- [ ] QA engineer assigned
- [ ] Tool compatibility verified (Python 3.9+, tools available)
- **Status:** Planned

### Week 2-3 (Phase 7.1a: Tooling)
- [ ] validate_syntax.py deployed
- [ ] All 7 language validators configured
- [ ] Baseline report generated (identify current failures)
- [ ] CI/CD integration started
- **Deliverables:** Tool + baseline + config
- **Status:** [Pending start]

### Week 4-8 (Phase 7.1b: High-Risk Fixes)
- [ ] SQL failures analyzed + fixed (target: 85% → 95%)
- [ ] Bash failures analyzed + fixed (target: 90% → 96%)
- [ ] Java version issues resolved
- [ ] Regression risk: ~2% of examples need edits
- **Deliverables:** Fixed files + updated baseline
- **Status:** [Pending start]

### Week 9-11 (Phase 7.2a: CI/CD)
- [ ] GitHub Actions workflow live
- [ ] Pre-commit validation active
- [ ] Dashboard + alerts configured
- [ ] First monthly report generated
- **Status:** [Pending start]

### Week 12+ (Phase 7.3: Monitoring)
- [ ] Weekly failure triage (30 min/week)
- [ ] Monthly bulk fixes (4 hrs/month)
- [ ] Quarterly language updates
- **Ongoing status:** [Pending start]

---

## Quality Gates

- [ ] 93% overall pass rate achieved (56K+ of 60K examples)
- [ ] SQL pass rate ≥ 85% (may require schema notes for remaining 15%)
- [ ] Bash pass rate ≥ 90% (document environment assumptions for remaining 10%)
- [ ] All other languages ≥ 95% pass rate
- [ ] Zero regression increases month-over-month
- [ ] All newly-added examples validated before merge (CI/CD gated)

---

## High-Risk Domains (Priority Order)

### 🔴 CRITICAL: SQL

**Issue:** Multi-dialect syntax differences (PostgreSQL ≠ MySQL ≠ Oracle ≠ DynamoDB)

**Examples:**
- PostgreSQL: `RETURNING` clause not in MySQL
- MySQL: `AUTO_INCREMENT` vs PostgreSQL `SERIAL`
- Oracle: `ROWNUM` syntax unique
- NoSQL: JSON operators vary

**Fix approach:**
- Use sqlglot to normalize dialects
- Add dialect tags to code blocks
- Test on actual databases (if possible)

**Timeline:** Weeks 4-7 (high priority, longest fix time)

---

### 🔴 CRITICAL: Bash

**Issue:** Environment-dependent (PATH, shell compatibility, globbing)

**Examples:**
- Hardcoded `/usr/bin/psql` fails if not in PATH
- `set -euo pipefail` not POSIX
- Glob patterns depend on shell (bash vs sh vs zsh)
- Variable expansion differs

**Fix approach:**
- Use shellcheck for linting
- Add setup instructions (prerequisites)
- Mark shell-specific code (bash, zsh, POSIX)
- Avoid non-portable features

**Timeline:** Weeks 4-6 (medium priority, moderate fix time)

---

### 🟡 MEDIUM: Java

**Issue:** Version-specific syntax (Java 8 vs 17+)

**Examples:**
- Java 8: No switch expressions
- Java 16+: Records (new syntax)
- Java 17+: sealed classes

**Fix approach:**
- Add version markers
- Test with JDK 17 (latest stable)
- Fallback to Java 8 syntax for compatibility

**Timeline:** Weeks 6-8 (lower priority, easier fixes)

---

### 🟡 MEDIUM: Go

**Issue:** Package structure, import paths, versioning

**Examples:**
- `go get` commands depend on version
- Import paths change with module system
- Error handling syntax evolved

**Fix approach:**
- Use `go mod` for examples
- Test with Go 1.21+
- Include `go.mod` for complex examples

**Timeline:** Weeks 6-8 (medium priority)

---

## Validator Implementation Details

```
validate_syntax.py
├── BaseSyntaxValidator (abstract)
│   ├── PythonValidator
│   │   └── uses: ast.parse()
│   ├── JavaScriptValidator
│   │   └── uses: node --check
│   ├── TypeScriptValidator
│   │   └── uses: tsc --noEmit
│   ├── SQLValidator
│   │   └── uses: sqlglot
│   ├── BashValidator
│   │   └── uses: shellcheck + sh -n
│   ├── GoValidator
│   │   └── uses: go build
│   └── JavaValidator
│       └── uses: javac
├── CodeBlockExtractor
│   └── regex patterns per language
├── ValidationEngine
│   └── orchestrates validators
└── Reporters
    ├── JSONReport (detailed)
    └── ConsoleReport (summary)
```

---

## Dependencies

- **Depends on:** Agent 5 deliverables (validate_syntax.py + config)
- **Depends on:** Completed Phase 7.1 content (frontend, database files)
- **Enables:** Clean CI/CD gate for all future content
- **Critical path:** NO (runs parallel to feature work; gating happens in CI)

---

## Resources

- **Agent 5 Validation Script:** `/validate_syntax.py` (850 lines, production-ready)
- **Config:** `/validation_config.yaml` (customizable per domain)
- **Analysis:** `/SYNTAX_VALIDATION_ANALYSIS.md` (detailed breakdown)
- **CI/CD template:** [To create Week 2]

---

## Notes

- **Parallel work:** Tooling (Week 2-3) must complete before fixes (Week 4-8).
- **Contractor-friendly:** SQL/Bash fixes are repetitive; good for junior devs.
- **Quick wins:** Python, JS, TS need minimal fixes; focus on SQL/Bash.
- **Automation:** Can auto-classify examples by language; use regex + file type hints.
- **Future:** Consider web dashboard for viewing/filtering failures (Phase 8).

---

**Owner Sign-off:** [Awaiting assignment]  
**Start date:** [Phase 7.1, Week 2]  
**Foundation completion:** Week 11 (10 weeks)  
**Ongoing maintenance:** 30 min/week indefinite
