# TEMPLATE: Frontend File Structure

**Use this template for Frontend Phase 1-2 files**

---

## Front Matter

```markdown
# [Topic Name]: [Specific Technology/Pattern]

**Level:** [Beginner/Intermediate/Advanced] | **Time:** [X] mins | **Interview:** [⭐ none / 🔥 Critical / ⭐⭐ Important]

---
```

## Sections (Required)

### 1. Overview (2-3 paragraphs)

- **What:** 1 sentence definition
- **Why it matters:** 2-3 bullet points (business impact, common mistakes, interview relevance)
- **Real scenario:** 1 production scenario

### 2. Core Concepts (Detailed Explanation)

Divide into 3-5 subsections, each with:
- **Explanation** (1 paragraph)
- **Code example** (good + bad)
- **Real-world context** (when/why this applies)

### 3. Implementation (Code Examples)

Minimum 3 examples:
1. ❌ **Bad:** Anti-pattern, common mistakes
2. ✅ **Good:** Basic correct usage
3. ✅ **Better:** Optimized/production version

**Languages to cover:**
- JavaScript/TypeScript (primary)
- React (if applicable)
- Next.js (if applicable)
- HTML/CSS (if applicable)

### 4. Common Pitfalls & Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| [Problem name] | What users experience | Code fix |
| [Problem 2] | Symptom | Fix |

### 5. Real Production Example

**Scenario:** 1 real-world case study

```
Before: [metrics/problem]
After: [improvements]
Code change: [diff or example]
Result: [impact - latency, throughput, user experience]
```

### 6. Monitoring / Testing

- How to verify the feature works
- Metrics to monitor
- Test cases

### 7. Performance Considerations (if applicable)

- Bundle size impact
- Runtime performance
- Memory usage

### 8. Browser Compatibility / Version Support

- Minimum versions
- Fallbacks for older browsers

### 9. Best Practices Checklist

- [ ] Item 1
- [ ] Item 2
- [ ] Item 3

### 10. See Also

- Cross-references to related files
- Prerequisites
- Follow-up topics

---

## Format Guidelines

- **Code blocks:** Always show language (`javascript`, `jsx`, `typescript`, `html`, `css`)
- **Comments:** Explain WHY, not WHAT
- **Real metrics:** Never estimate. Use real numbers from production.
- **Examples:** Minimum 15-20 examples per file (mix good/bad)
- **Diagrams:** ASCII, Mermaid, or D3.js for complex concepts
- **Scenarios:** Minimum 2-3 real production scenarios
- **Length:** 800-1,200 lines (~5,000-7,000 words)

---

## Quality Checklist

- [ ] All code examples tested (runnable)
- [ ] All metrics from production (not estimates)
- [ ] All recommendations explained (not dogma)
- [ ] Cross-links to related files
- [ ] Interview questions covered
- [ ] Performance implications stated
- [ ] Browser support documented
- [ ] Real failure modes explained
- [ ] Monitoring/debugging guidance included

---

## Examples

See completed files:
- `09-performance/02-core-web-vitals-metrics.md` (completed)
- `15-testing/03-unit-testing-vitest-rtl.md` (TBD)
- `05-state-management/02-redux-zustand-patterns.md` (TBD)
