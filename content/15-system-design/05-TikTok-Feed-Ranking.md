---
title: TikTok Feed Ranking - L5 Deep Dive
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# TikTok Feed Ranking - L5 Deep Dive

> **[🎨 View Interactive Diagram](tiktok-architecture.html)** | [← Back to Index](systems-index.html)

*"Infinite personalized feed with exploration/exploitation at 2B MAU scale."*

---

## 🎵 Context

**TikTok Scale:**
- 2 billion monthly active users
- 100+ million creators
- 1M+ new videos per day
- Sub-500ms feed generation latency
- Focus: engagement time (watch duration)

**Core Challenge:** Exploration/exploitation balance + long-term value optimization

---

## 📊 Estimation

```
Daily active users: 1 billion
Scrolls per user per day: 20
Videos per scroll: 10 new recommendations
Total daily recs: 1B * 20 * 10 = 200B recommendations/day

QPS: 200B / 86400 = 2.3M QPS (MASSIVE!)

But with parallelization + caching, peak ~100K QPS per algorithm
```

---

## 🏗️ Architecture

```
User Opens Feed
    │
    ▼
┌─────────────────────────────┐
│ Context Collection          │
│ (user, time, device)        │
└──────────┬──────────────────┘
           │
    ┌──────┴──────────────────┐
    │                         │
    ▼                         ▼
┌─────────────┐       ┌──────────────┐
│ Fast Pool   │       │ Exploration  │
│ (personali- │       │ Pool         │
│  zed rec)   │       │ (new videos) │
│             │       │              │
│ 80% slots   │       │ 20% slots    │
└──────┬──────┘       └──────┬───────┘
       │                     │
       └─────────────┬───────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │ Ranking (contextual     │
        │ bandit + long-term RL)  │
        │                         │
        │ Score each video        │
        └────────┬────────────────┘
                 │
                 ▼
        ┌─────────────────────────┐
        │ Diversity Filter        │
        │ (avoid repetition)      │
        └────────┬────────────────┘
                 │
                 ▼
            Feed returned
```

---

## 🤖 ML: Contextual Bandits

```
Key Idea: For each (user, video) pair:
├─ Estimate: P(user engages with video | context)
├─ Context: time, location, device, etc.
├─ Action: show or not show this video
├─ Reward: watch duration

Thompson Sampling per context:
├─ Sample theta ~ Beta(alpha_context, beta_context)
├─ Score = theta (high uncertainty → explore)
├─ Show top-k scored videos
└─ Update based on engagement feedback
```

---

## 📈 Long-Term Value Optimization

```
Problem: Immediate engagement ≠ long-term satisfaction

Solution: RL to maximize lifetime value
├─ State: user, video, context
├─ Action: show video or not
├─ Reward: watch duration + future engagement
│  = immediate_watch_time + lambda * predicted_future_sessions
└─ Learn policy: which videos maximize long-term engagement

Trade-off:
├─ Short-term: show viral videos (high immediate watch-time)
├─ Long-term: show diverse content (keep user interested long-term)
├─ Optimization: blend 0.7 * short-term + 0.3 * long-term
```

---

## ⚡ Production

**Key Metrics:**
- Watch time per session
- Session frequency (how often user returns)
- Diversity (topic coverage)
- Creator diversity (creator growth)

**A/B Testing:**
- New ranking model: test on 1% users
- Measure: session length, retention
- Rollout: if watch-time >= baseline

---

*Last Updated: 2026-05-28*
