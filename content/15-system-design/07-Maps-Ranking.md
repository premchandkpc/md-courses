---
title: Google Maps Ranking - L5 Deep Dive
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# Google Maps Ranking - L5 Deep Dive

> **[🎨 View Interactive Diagram](maps-architecture.html)** | [← Back to Index](systems-index.html)

*"Rank 200M places by relevance + distance + popularity."*

---

## 🗺️ Context

**Maps Scale:**
- 200M+ places indexed
- 100K+ QPS
- <200ms latency requirement
- Geographically distributed
- Real-time popularity signals

---

## 🏗️ Architecture

```
User Search: "coffee near me"
    │
    ▼
┌─────────────────────────┐
│ Query Understanding     │
│ (extract: type, prefs)  │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ Geographic Retrieval    │
│ (find nearby places)    │
│ Using geo-index         │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ Ranking                 │
│ ├─ Relevance (match)    │
│ ├─ Distance (proximity) │
│ ├─ Popularity (ratings) │
│ └─ Recency (freshness)  │
└──────────┬──────────────┘
           │
           ▼
    Top Places + Map
```

---

## 🔧 Key Components

### Geospatial Indexing

```
Index by Hilbert Curve:
├─ Space-filling curve (2D → 1D)
├─ Nearby places → nearby curve values
├─ Range query: find places in bounding box
├─ Latency: <10ms for geographic retrieval
```

### Ranking Signals

```
Score = 
  w1 * relevance_score +
  w2 * distance_score +
  w3 * popularity_score +
  w4 * freshness_score

where:
  relevance: query-place text match (BM25)
  distance: 1 / (1 + distance_km)
  popularity: ratings * review_count
  freshness: hours_since_update
```

### Real-Time Signals

```
Updated every minute:
├─ Popularity (from user visits)
├─ Crowdedness (estimated wait time)
├─ Reviews (new ratings)
├─ Hours (if open/closed)

Rerank in real-time based on these signals
```

---

## 🌍 Geographic Distribution

```
Problem: User in Singapore shouldn't wait for index in US

Solution: Geo-partitioned indexes
├─ Split world into regions
├─ Each region has full index
├─ Route requests to nearest region
├─ Replicate across 3 datacenters per region
└─ Latency: <50ms from nearest region

Regional spikes (rush hour):
├─ More queries in peak areas
├─ Load balancing spreads across datacenters
├─ Fallback: serve cached results
```

---

## 💡 Special Challenges

### Region Boundaries
```
User at border (on boundary of two regions):
├─ Query to region 1: finds nearby places in region 1
├─ Query to region 2: finds nearby places in region 2
├─ Merge results
└─ Return top-K across regions
```

### Personalization
```
Same search, different users = different results:
├─ User A (frequent vegetarian)
   → Rank vegetarian restaurants higher
├─ User B (budget-conscious)
   → Rank cheap places higher
├─ Personalization via: preferences + history
```

---

*Last Updated: 2026-05-28*
