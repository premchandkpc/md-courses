# Style Guide

This guide ensures consistency across all content files. Every contributor must follow these rules.

## File Metadata

Every `.md` file **must** start with YAML frontmatter:

```yaml
---
title: Topic Title
difficulty: beginner|intermediate|advanced|staff
time: 15m|30m|45m|60m|90m
prerequisites:
  - domain/file-name
related:
  - domain/file-name
paths:
  - backend-junior
  - system-design
---
```

## Headings

- Use `#` for the title only (once per file)
- Use `##` for top-level sections
- Use `###` for subsections
- Never exceed `###` — split the file instead
- No emoji in headings

## Naming Conventions

- File names: `kebab-case.md` (lowercase, hyphens)
- Directory names: `number-name` (e.g., `08-databases`)
- No spaces or underscores in file paths

## Code Blocks

- Always specify language after opening backticks
- Code must be tested and runnable
- Show before/after patterns with ❌/✅ comments

## Content Rules

- No TODO, FIXME, or placeholder text in content files
- Every file must link to at least one prerequisite (or declare `prerequisites: []`)
- Include a read-time estimate in frontmatter
- Include 2-3 real-world scenarios per topic
- Use production numbers, not estimates

## Cross-References

- Link to related topics in both frontmatter (`related:`) and inline in text
- Use relative paths: `[MVCC](/08-databases/07-mvcc-visualization-engine.md)`

## Prohibited

- Emoji in headings
- Stale dates without a `reviewed` field
- Files over 2,000 lines — split into sub-topics
- Mixed HTML and markdown content in same file
