---
title: Code Review — Best Practices Guide
topic: 25-software-engineering
difficulty: intermediate
time: 30m
paths:
  - backend-junior
---

# Code Review — Best Practices Guide

Code review is the most effective quality practice in software engineering. A good review catches bugs, improves design, shares knowledge, and builds team consistency.

## What to Look For

### Correctness
- Does the code do what it's supposed to?
- Are edge cases handled? (null, empty, overflow, race conditions)
- Are error paths handled properly?
- Are there off-by-one errors, race conditions, deadlocks?

### Design
- Does it fit the existing architecture?
- Is it over-engineered for the problem?
- Are abstractions appropriate?
- Is the API intuitive and hard to misuse?

### Maintainability
- Is the code readable? (clear names, reasonable function length)
- Are there tests? Are they meaningful?
- Is there unnecessary duplication?
- Would a new team member understand this?

### Performance
- Are there obvious inefficiencies? (N+1 queries, large allocations in loops)
- Is caching appropriate?
- Are database queries indexed?
- Could this cause a production incident?

## Review Process

```
Author submits PR
  → Reviewer checks within SLA (4h for critical, 24h for normal)
    → Comments, suggestions, requests
      → Author addresses feedback
        → Final approval → Merge
```

## What to Automate (Not Comment)

- Formatting: formatters (Prettier, rustfmt, gofmt, black)
- Linting: ESLint, pylint, clippy
- Type checking: TypeScript, mypy, pyright
- Security scanning: Snyk, Dependabot
- Tests: CI pipeline must pass

The reviewer's job is what automation cannot catch: design, correctness, trade-offs.

## Commenting Effectively

```
❌ "Please fix this"                      → not actionable
✅ "This could throw NPE if user is null  → better (specific + why)
    when account is deleted"
✅ "Consider extracting this validation   → better (suggestion + rationale)
    so it can be reused in OrderService"

✅ "This is well-named and tested"        → praise good work
✅ "Great catch on the edge case!"        → reinforce good practices
```

## PR Size Guidelines

| Size | Lines Changed | Review Time | Notes |
|------|-------------|-------------|-------|
| Small | < 100 | 10-15 min | Ideal; single concern |
| Medium | 100-300 | 20-40 min | Reasonable; stay focused |
| Large | 300-800 | 60+ min | Warn reviewer; split if possible |
| X-Large | 800+ | Too large | Split into multiple PRs |

Small, frequent PRs get better reviews. A 50-line PR gets thorough review; a 2000-line PR gets a glance.

## Code Review Checklist

### Pre-Submit (Author)
- [ ] Code compiles and tests pass
- [ ] Self-review done before submitting
- [ ] PR description explains WHAT and WHY
- [ ] Tests included for new functionality
- [ ] Documentation updated if API changed
- [ ] Follows team coding conventions

### During Review (Reviewer)
- [ ] Understand the problem first (read description + issue)
- [ ] Start with high-level design, then details
- [ ] Question: "How could this break?"
- [ ] Question: "Will this be easy to change?"
- [ ] Question: "Is there a simpler approach?"

## Common Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| Nitpicking style | Use formatters; focus on substance |
| Reviewing for hours | Set timer; do focused passes |
| Approving without understanding | Ask questions; run the code |
| Blocking on preferences | Differentiate "must fix" from "suggestion" |
| Rubber-stamping | Find at least one thing to discuss |
| Bikeshedding | Don't spend 30 min on naming |

## Review Types

| Type | Focus | Duration |
|------|-------|----------|
| **Formal Inspection** | All aspects; recorded defects | 60-90 min meeting |
| **Lightweight Review** | Design + correctness | 20-40 min async |
| **Over-the-shoulder** | Quick guidance | 5-15 min sync |
| **Post-commit** | Learning after merge | 15 min async |

Most teams do lightweight async review (GitHub PRs). Save formal inspections for critical security/auth changes.

## Building a Review Culture

- **Review as if you're mentoring** — teach, don't just correct
- **Welcome feedback** — code is owned by the team, not individuals
- **Review quickly** — speed matters; stale PRs demoralize
- **Rotate reviewers** — spread knowledge across the team
- **Celebrate good reviews** — praise thorough feedback publicly

> "Leave the code better than you found it." — Boy Scout Rule

## Visualization

- [PR Pipeline Animation](pr-flow-viz.html) — step through the code review lifecycle from submit to merge
- [PR Size Analyzer](pr-size-viz.html) — drag to see estimated review time and split recommendations

**Related**: [Testing Guide](/19-testing/README.md) · [Software Architecture](/17-software-architecture/README.md) · [Git Internals](/25-software-engineering/01-git-internals.md)
