# Contributing

Thanks for your interest! This is a comprehensive engineering knowledge base. We welcome contributions, corrections, and improvements.

## How to Contribute

### Report Issues

1. Found an error or have a suggestion? Open an issue
2. Include the file path and specific problem
3. For code examples: specify the language and context

### Submit Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Make your changes following the content guidelines (below)
4. Commit with a clear message
5. Push and open a pull request

## Content Guidelines

### Structure

- **Location:** Content lives in `data/` organized by numbered domains (00-25)
- **Format:** Markdown (`.md`) with inline code blocks and diagrams
- **Naming:** `[topic-slug].md` (lowercase, hyphens, descriptive)

### Quality Standards

- **Code examples:** Must be tested and runnable (include language marker)
- **Real metrics:** Use production numbers, not estimates
- **Scenarios:** Include 2-3 real-world production scenarios
- **Diagrams:** ASCII, Mermaid, or D3.js (interactive where valuable)
- **Explanations:** Focus on the "why," not just the "what"
- **Accessibility:** Make content understandable to learners at all levels (beginner→advanced)

### File Template

```markdown
# Topic Title

**Level:** Beginner/Intermediate/Advanced | **Time:** X mins

## Overview
[1-2 paragraph summary + why it matters]

## Core Concepts
[3-5 detailed sections with examples]

## Real Production Example
[Before/after metrics, code sample, business impact]

## Best Practices Checklist
[Actionable items for learners]

## See Also
[Cross-references to related topics]
```

### Code Example Format
```markdown
# Good example with language marker
\`\`\`python
def process_data(items):
    """Real, tested code."""
    return [x * 2 for x in items]
\`\`\`

# Show before/after patterns
# ❌ Bad: explain why this is wrong
# ✅ Good: show the correct approach
```

## Phase 7: Active Development

We're currently in **Phase 7** — a major expansion adding:
- **Frontend:** 25 new files (Core Web Vitals, testing, state management, security)
- **Database:** Topics 08-11 (connection pooling, DR, multi-region, replication)
- **Cloud:** Azure + GCP coverage (61 new files)
- **Interactive:** Quizzes, videos, benchmarks

**To contribute to Phase 7:** Check `MASTER_ROADMAP_PHASE_7_8.md` for the roadmap or open an issue to ask about current priorities.

## Review Process

1. **Automated checks:** CI/CD validates syntax and formatting
2. **Manual review:** Domain expert reviews for accuracy + quality
3. **Feedback:** Constructive comments on PRs (discuss, don't dismiss)
4. **Merge:** After approval, your contribution ships

## Questions?

- Check `STRUCTURE.md` for project layout
- See `AI-REVIEW.md` for content inventory
- Read `AGENTS.md` for AI-assisted workflows
- Open an issue if stuck
