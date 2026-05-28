# Netflix Recommendations - L5 Deep Dive

> **[🎨 View Interactive Diagram](netflix-architecture.html)** | [← Back to Index](systems-index.html)

*"Cold-start + diversity + long-term satisfaction at 250M users."*

---

## 📺 Context

**Netflix Scale:**
- 250M+ subscribers
- 10K+ content titles
- 200M+ daily requests
- Batch-driven (daily recompute)
- Focus: long-term retention

---

## 🏗️ Approach: Offline Batch

```
Nightly Pipeline:
├─ Extract user watch history (past 6 months)
├─ Compute user embeddings via collaborative filtering
├─ Compute content embeddings via collaborative filtering
├─ Score all user-content pairs (ANN)
├─ Apply diversity penalties
├─ Store personalized recommendations
├─ Deploy updated lists
```

**Why Batch?**
- Can use expensive algorithms (collaborative filtering)
- Can optimize globally (diversity across portfolio)
- Less infrastructure than real-time
- Acceptable staleness (24 hours)

---

## 🤖 ML: Collaborative Filtering

```
User-User Collab:
├─ Find users similar to target user
├─ Aggregate movies they watched
├─ Score by similarity × movie popularity

Content-Content Collab:
├─ Find movies similar to user's watch history
├─ Score by similarity × current popularity

Blended:
├─ 0.6 * user-user + 0.4 * content-content
├─ Reduces filter bubble
└─ Better diversity

Result: 100-200 recommendations per user (stored)
```

---

## ❄️ Cold Start

```
New User (no watch history):
├─ Demo questions: "What genres do you like?"
├─ Return: genre-based popular content
├─ Gradually personalize as they watch

New Content (no views):
├─ Show in "New & Popular" section
├─ Bootstrap engagement
├─ Later: surface based on user preference match
```

---

## 🎯 Diversity Optimization

```
Problem: Recommendations all same genre = boredom

Solution: Diversity penalties
├─ Score = collab_score * (1 - diversity_penalty)
├─ diversity_penalty ∝ (# already shown in genre)
├─ Result: spread recommendations across genres

Example:
├─ Drama score: 0.9 × (1 - 0.5) = 0.45 (many dramas shown)
├─ Comedy score: 0.7 × (1 - 0.1) = 0.63 (fewer comedies shown)
└─ Comedy ranked higher (despite lower base score!)
```

---

*Last Updated: 2026-05-28*
