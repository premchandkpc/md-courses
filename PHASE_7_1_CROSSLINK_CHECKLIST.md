# Phase 7.1 Cross-Linking Checklist

**Status:** Implementation Guide for Monday Kickoff  
**Date:** 2026-05-30  
**Goal:** Systematic linking between Phase 7.1 files

---

## What Cross-Linking Accomplishes

1. **User navigation:** "I learned about Redux, now show me Zustand alternative"
2. **Reinforcement:** Concepts appear in multiple contexts (state management → error boundaries → forms)
3. **Learning paths:** Guided progression (fundamentals → patterns → advanced)
4. **SEO/discovery:** More internal links = better search indexing

---

## Phase 7.1 Files (17 total)

### Frontend (10 files)

1. **Core Web Vitals** (data/04-frontend/react/09-performance/02-core-web-vitals-metrics.md)
2. **Vitest + RTL** (data/04-frontend/react/15-testing/03-unit-testing-vitest-rtl.md)
3. **Redux/Zustand** (data/04-frontend/react/05-state-management/02-redux-zustand-patterns.md)
4. **WCAG Accessibility** (data/04-frontend/react/16-accessibility/02-wcag-patterns-and-compliance.md)
5. **XSS/CSRF/CSP** (data/04-frontend/react/17-security/02-xss-csrf-csp-deep-dive.md)
6. **Compound Components** (data/04-frontend/react/06-component-architecture/02-compound-components-pattern.md)
7. **React Fiber** (data/04-frontend/react/02-react-internals/02-fiber-reconciliation-engine.md)
8. **Advanced Forms** (data/04-frontend/react/08-forms/02-advanced-form-patterns.md)
9. **Error Boundaries** (data/04-frontend/react/35-error-handling/01-error-boundaries-and-patterns.md)

### Database (4 files)

10. **Connection Pooling** (data/08-databases/08-connection-pooling.md)
11. **Disaster Recovery** (data/08-databases/09-disaster-recovery.md)
12. **Replication** (data/08-databases/10-database-replication.md)
13. **Sharding** (data/08-databases/11-database-sharding.md)

---

## Cross-Link Map

### Core Web Vitals → Links to:
- ✅ Performance optimization (existing file)
- ❌ Advanced Forms (forms performance impact)
- ❌ Error Boundaries (error state performance)
- ❌ Server Components (if shipping from server)

**Action:** Add to "See Also" section:
```markdown
- Advanced Form Patterns: Form responsiveness impacts INP
- Error Boundaries: Error UI rendering impacts CLS
```

### Vitest + RTL → Links to:
- ✅ React testing strategy (existing file)
- ❌ Redux/Zustand (testing state changes)
- ❌ Forms (testing form submission)
- ❌ Compound Components (testing component composition)

**Action:** Add examples:
```markdown
// Test Redux store changes
test('Redux action updates state', () => {
  // Use Redux testing patterns from "Redux/Zustand Patterns"
});

// Test form submission
test('Form submits with validation', () => {
  // Reference "Advanced Form Patterns" for form testing approach
});
```

### Redux/Zustand → Links to:
- ✅ State management intro (existing file)
- ❌ Compound Components (using Context for state)
- ❌ Error Boundaries (error state management)
- ❌ Forms (form state management comparison)
- ❌ Vitest (testing Redux/Zustand)

**Action:** Add comparison section:
```markdown
## Comparison: State Management vs Other Patterns

| Pattern | When to Use | Link |
|---------|-------------|------|
| Redux | Large apps, complex state | This file |
| Compound Components + Context | Component-level composition | Compound Components Pattern |
| Form State (React Hook Form) | Form-specific state | Advanced Form Patterns |
```

### WCAG Accessibility → Links to:
- ✅ Basic a11y (existing file)
- ❌ Compound Components (accessible component APIs)
- ❌ Forms (form a11y: labels, error messages)
- ❌ Error Boundaries (accessible error UI)

**Action:** Add:
```markdown
## Accessibility in Real Components

See these files for a11y patterns in context:
- **Compound Components:** Accessible API design (role, aria-selected)
- **Advanced Forms:** Accessible form inputs + error messages
- **Error Boundaries:** Accessible error UI for users
```

### XSS/CSRF/CSP → Links to:
- ✅ React security (existing file)
- ❌ Advanced Forms (CSRF tokens in forms)
- ❌ Error Boundaries (XSS in error messages)
- ❌ React Fiber (where XSS can happen in render)

**Action:** Add:
```markdown
## XSS in Real Applications

- **Advanced Forms:** CSRF token handling in form submission
- **React Fiber:** Understanding render-phase XSS risks
- **Error Boundaries:** Sanitizing error messages before display
```

### Compound Components → Links to:
- ✅ Component architecture intro (existing file)
- ❌ WCAG (accessible compound components)
- ❌ Redux/Zustand (state in compound components)
- ❌ Fiber (understanding re-renders)

**Action:** Add:
```markdown
## Compound Components with State Management

- Use with **Redux/Zustand** for global state in subcomponents
- Access context via custom hooks (see "React Fiber" for hook mechanics)
- Ensure **WCAG accessibility** at every subcomponent level
```

### React Fiber → Links to:
- ❌ Redux/Zustand (how state updates trigger fiber work)
- ❌ Compound Components (context subscription behavior)
- ❌ Error Boundaries (error boundary in fiber tree)
- ❌ Vitest (testing fiber behavior)

**Action:** Add:
```markdown
## Fiber in Real Applications

- **Redux/Zustand:** State changes enqueue fiber work (scheduler)
- **Compound Components:** Context changes affect fiber tree
- **Error Boundaries:** Error boundary fiber catches child errors
- **Testing:** Vitest tests run without fiber (jsdom, not browser)
```

### Advanced Forms → Links to:
- ✅ Form testing (existing file)
- ❌ Redux/Zustand (form state options)
- ❌ WCAG (form accessibility)
- ❌ XSS/CSRF (CSRF tokens in forms)
- ❌ Error Boundaries (form submission errors)

**Action:** Add:
```markdown
## Forms in Real Applications

| Aspect | Link |
|--------|------|
| Form state management | Redux/Zustand Patterns |
| Form accessibility | WCAG Patterns |
| CSRF protection | XSS/CSRF/CSP |
| Error handling | Error Boundaries |
| Testing forms | Vitest + RTL |
```

### Error Boundaries → Links to:
- ❌ XSS/CSRF/CSP (XSS in error messages)
- ❌ Advanced Forms (form submission errors)
- ❌ React Fiber (where errors happen in render)
- ❌ WCAG (accessible error UI)

**Action:** Add:
```markdown
## Error Boundaries with Other Patterns

- **XSS/CSRF/CSP:** Sanitize error messages before display
- **WCAG:** Make error UI keyboard-navigable + screen-reader friendly
- **React Fiber:** Errors thrown during render caught by boundaries
- **Forms:** Handle async form submission errors (retry patterns)
```

### Connection Pooling → Links to:
- ❌ Replication (pooling replicates across servers)
- ❌ Sharding (pool size considerations with shards)
- ❌ Disaster Recovery (pool reconnection after failover)

**Action:** Add:
```markdown
## Pooling in Scaled Systems

- **Replication:** Pool connections to primary + replicas separately
- **Sharding:** Each shard needs its own connection pool
- **Disaster Recovery:** Pool must detect broken connections + auto-reconnect
```

### Disaster Recovery → Links to:
- ❌ Replication (replication is core DR strategy)
- ❌ Sharding (backup considerations with shards)
- ❌ Connection Pooling (pool behavior during failover)

**Action:** Add:
```markdown
## DR Across Database Patterns

- **Replication:** Primary mechanism (synchronous for zero-loss)
- **Sharding:** Each shard needs independent backup strategy
- **Connection Pooling:** Must auto-detect primary failure + reconnect
```

### Replication → Links to:
- ❌ Disaster Recovery (replication strategy choice)
- ❌ Sharding (multi-shard replication topology)
- ❌ Connection Pooling (read replicas scaling)

**Action:** Add:
```markdown
## Replication in Practice

- **DR choice:** Decide sync vs async for RTO/RPO (see Disaster Recovery)
- **Sharding:** Each shard replica topology must be consistent
- **Scaling reads:** Distribute queries to replicas via pooled connections
```

### Sharding → Links to:
- ❌ Replication (replication topology with shards)
- ❌ Disaster Recovery (backup strategy per shard)
- ❌ Connection Pooling (pool size calculation with shards)

**Action:** Add:
```markdown
## Sharding at Scale

- **Replication:** Each shard has its own replica set
- **Disaster Recovery:** Shard-level backups (not monolithic)
- **Pooling:** Connection budget = shard_count × pool_size_per_shard
```

---

## Implementation Tasks

### Phase 1: Add "See Also" Sections (4 hours)

Each file needs a "See Also" section linking to related Phase 7.1 files.

Template:
```markdown
## See Also

- [Redux/Zustand Patterns](../../05-state-management/02-redux-zustand-patterns.md) — State management comparison
- [Error Boundaries](../../35-error-handling/01-error-boundaries-and-patterns.md) — Error recovery patterns
- [Advanced Form Patterns](../../08-forms/02-advanced-form-patterns.md) — Form state + submission
```

**Effort:** 30 min per file × 13 files = 6.5 hours

### Phase 2: Add Contextual Links (6 hours)

Within file body, add cross-references where concepts relate.

Example (in Redux/Zustand):
```markdown
### Selector Optimization

Without memoization, every store update triggers re-render (see **React Fiber** for details on render phases).

For form state, consider React Hook Form instead (see **Advanced Form Patterns**).
```

**Effort:** 30 min per file × 17 files = 8.5 hours

### Phase 3: Verify Links (2 hours)

Run link checker to ensure all links resolve.

```bash
python3 << 'EOF'
import re, os
from pathlib import Path

for md_file in Path('data').rglob('*.md'):
    content = md_file.read_text()
    for link in re.findall(r'\]\(([^\)]+)\)', content):
        if link.startswith('#'):
            continue  # Skip anchors
        path = md_file.parent / link
        if not path.exists():
            print(f"BROKEN: {md_file} → {link}")
EOF
```

**Effort:** 1 hour

---

## Success Metrics

- [ ] All 17 files have "See Also" section
- [ ] All cross-references are bidirectional (if A → B, then B → A)
- [ ] All links resolve (no 404s)
- [ ] Average 4+ cross-links per file
- [ ] No circular dependencies (A → B → C → A)

---

## Files to Update (Ranked by Priority)

**HIGH PRIORITY (Core to learning path):**
1. Redux/Zustand → Forms, Compound Components, Error Boundaries
2. Advanced Forms → Redux, Error Boundaries, WCAG
3. React Fiber → Redux, Compound Components, Vitest
4. Error Boundaries → Forms, XSS/CSRF, WCAG
5. Compound Components → WCAG, Redux, Fiber

**MEDIUM PRIORITY (Topic-specific):**
6. WCAG → Forms, Compound Components, Error Boundaries
7. XSS/CSRF/CSP → Forms, Error Boundaries, Fiber
8. Core Web Vitals → Forms, Fiber, Error Boundaries
9. Vitest → Forms, Redux, Compound Components

**LOW PRIORITY (Infrastructure):**
10. Connection Pooling → Replication, Sharding, DR
11. Disaster Recovery → Replication, Sharding, Pooling
12. Replication → DR, Sharding, Pooling
13. Sharding → DR, Replication, Pooling

---

## Execution Plan (Before Monday)

**Friday Afternoon (4 hours):**
1. Add "See Also" sections to all 17 files (2 hours)
2. Add 2-3 contextual links per file (2 hours)

**Monday Morning (1 hour):**
1. Verify all links resolve (30 min)
2. Add to PR checklist (30 min)

**Total effort:** 5 hours

---

## Checklist

- [ ] Redux/Zustand updated with cross-links
- [ ] Forms updated with cross-links
- [ ] Error Boundaries updated with cross-links
- [ ] Compound Components updated with cross-links
- [ ] React Fiber updated with cross-links
- [ ] WCAG updated with cross-links
- [ ] XSS/CSRF/CSP updated with cross-links
- [ ] Core Web Vitals updated with cross-links
- [ ] Vitest updated with cross-links
- [ ] Connection Pooling updated with cross-links
- [ ] Disaster Recovery updated with cross-links
- [ ] Replication updated with cross-links
- [ ] Sharding updated with cross-links
- [ ] All links verified (no broken references)
- [ ] Cross-link checklist added to CONTRIBUTING.md

---

## See Also

- TECHNICAL_DEBT_STRATEGY.md (cross-linking is debt payoff item)
- VALIDATION_GUIDE.md (validation includes link checking)
- SESSION_SUMMARY_2026_05_30.md (phase 7.1 results)
