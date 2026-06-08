---
title: Google Search Ranking System - L5 Deep Dive
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# Google Search Ranking System - L5 Deep Dive

> **[🎨 View Interactive Diagram](search-architecture.html)** | [← Back to Index](systems-index.html)

*"How do you return 10 most relevant pages from a trillion-page corpus in 200ms?"*

---

## 🔍 Context

**Google Search Scale:**
- 1 trillion pages indexed
- 99,000 search queries per second
- 1B+ daily active users
- Sub-200ms latency requirement
- 15+ signals affecting ranking

**Core Challenge:** Relevance at planetary scale, subject to adversarial actors (SEO spam).

---

## 📋 Requirements

### Functional
1. Return 10 most relevant pages for any query
2. Support query refinement & suggestions
3. Handle queries in 100+ languages
4. Detect & suppress spam/low-quality content
5. Fresh results (updated within hours)

### Non-Functional
- QPS: 100K globally
- Latency: p50 <100ms, p99 <200ms
- Availability: 99.99%
- Freshness: web crawl every 2-7 days
- Consistency: eventual (acceptable lag)

---

## 📊 Estimation

### Traffic

```
Daily searches: 8.5B (Google's public data)
QPS = 8.5B / 86400 = 98,380 QPS
Peak QPS (2x): ~200K QPS
Per datacenter: 200K / 10 = 20K QPS

Per query, average:
- 10 results displayed
- Ranking 100 candidates
- Total rankings: 8.5B * 100 = 850B rankings/day
```

### Storage

**Index:**
```
Pages indexed: 1 trillion (1T)
Average page size: 50KB
Full index size: 50 PB (!!)
But compressed: 5 PB (10:1 compression)

Distributed across 1000 datacenters:
- 5 PB / 1000 = 5 TB per datacenter
- Replicated 3x: 15 TB total per datacenter

This fits on modern sharded infrastructure:
- 100 shards per datacenter
- Each shard: 150 GB (fits in RAM with compression)
```

**Metadata & Signals:**
```
Signals per page: 200 features
Storage: 1T pages * 200 * 4 bytes = 800 GB
Replicated: 2.4 TB per datacenter

PageRank scores: 1T pages * 4 bytes = 4 GB
Replicated: 12 GB per datacenter

Freshness signals: 1T pages * 20 bytes = 20 GB
Replicated: 60 GB per datacenter
```

### Compute

**Query Processing:**
```
For each query:
1. Parse & understand (NLP): 5ms
2. Retrieve candidates (inverted index): 20ms
3. Rank candidates (ML model): 100ms
4. Aggregate results: 10ms
5. Serialize response: 5ms

Total: ~140ms (fits p99 <200ms)

Parallelization:
- Parse: 1 machine
- Retrieve: 10 shards in parallel
- Rank: batch inference on GPUs
- Aggregate: 1 machine

Bottleneck: Ranking (largest latency component)
```

---

## 🏗️ Architecture

```
User Query
    │
    ▼
┌─────────────────────────┐
│ Query Understanding      │
│ (NLP, Entity detection)  │
└──────────┬───────────────┘
           │
           ▼
┌─────────────────────────┐
│ Candidate Retrieval      │
│ (Inverted Index)        │
│ 10 shards in parallel   │
└──────────┬───────────────┘
           │
           ▼
┌─────────────────────────┐
│ Feature Enrichment       │
│ (Quality, freshness)    │
└──────────┬───────────────┘
           │
           ▼
┌─────────────────────────┐
│ Ranking (LambdaMART)    │
│ ML model scoring        │
└──────────┬───────────────┘
           │
           ▼
┌─────────────────────────┐
│ Diversity & Safety      │
│ Remove spam, duplicates │
└──────────┬───────────────┘
           │
           ▼
┌─────────────────────────┐
│ Response Construction   │
│ Snippets + metadata     │
└──────────┬───────────────┘
           │
           ▼
       Results
```

### Component 1: Query Understanding

```
Input: "machine learning"
├─ Tokenization: ["machine", "learning"]
├─ Entity detection: TECH_FIELD("machine learning")
├─ Intent: LEARNING (educational intent)
├─ Query expansion: 
│  ├─ "ML"
│  ├─ "artificial intelligence"
│  └─ "neural networks"
└─ Geographic context: User location

BERT-based model:
- Input: Query text
- Output: [intent_vector, entity_vector, ...] (768D)
- Latency: <5ms
- Model size: 300MB
```

### Component 2: Candidate Retrieval (Inverted Index)

```
Inverted Index:
word1 → [docID_1, docID_2, ...]
word2 → [docID_3, docID_1, ...]

For query "machine learning":
├─ Lookup word "machine" → 500M docs
├─ Lookup word "learning" → 300M docs
├─ Intersect → 50M docs containing both
└─ Return top 1000 by PageRank

Optimization: Early termination
├─ Don't iterate all 50M
├─ Fetch top 1000 by PageRank
├─ Latency: <20ms

Sharding:
├─ 1000 index shards (by docID)
├─ Each shard indexed separately
├─ Query: broadcast to all shards in parallel
├─ Merge results
```

**Index Storage (per shard):**
```
Shard shards 1000 docs:
- Inverted lists: 100 MB
- Position info: 50 MB
- PageRank scores: 10 MB
- Fresh signals: 5 MB

Total per shard: 165 MB
Fits in L3 cache (smart scheduling)
```

### Component 3: Ranking Model (LambdaMART)

**Model:**
```
LambdaMART (Learning-to-Rank):
- GBDT (Gradient Boosted Decision Trees)
- Trained on millions of human judgments
- Input: 200 features per document
- Output: Relevance score [0-100]

Input Features:
├─ Query features (50)
│  ├─ Query length
│  ├─ Query intent
│  └─ Query entity type
│
├─ Document features (100)
│  ├─ Title relevance (BM25)
│  ├─ Body relevance (BM25)
│  ├─ URL structure
│  ├─ Domain reputation
│  ├─ Page quality score
│  ├─ Freshness
│  └─ AMP/Mobile-friendly
│
├─ Query-document features (50)
│  ├─ Title-query overlap
│  ├─ Body-query overlap
│  ├─ Entity matching
│  └─ Semantic similarity

Output: Relevance score
```

**Training:**
```
Data: Human-labeled search results
- Millions of queries
- Multiple documents per query
- Labels: Relevant, Somewhat relevant, Not relevant

Loss: LambdaMART loss
- Optimizes ranking order
- Each pair: if doc_i ranked higher than doc_j
             but doc_j is more relevant
             → increase loss

Training time: 24 hours on 1000 GPUs
Model size: 200 MB
```

**Inference:**
```
Per query:
- Input: 1000 candidates * 200 features
- Run through GBDT: 100ms
- Output: 1000 scores

Optimization:
- Batch 100 queries together
- Parallelized score computation
- GPU acceleration via XGBoost

Throughput: 1000 queries/sec per GPU
GPUs needed for 100K QPS: 100 GPUs (with redundancy: 500)
```

### Component 4: Spam & Quality Filtering

```
Apply filters to remove:
├─ Machine-generated spam
├─ Link spam (artificially inflated PageRank)
├─ Thin content (insufficient content)
├─ Adult content (user preference)
├─ Malware sites (security)
└─ Duplicate content (near-duplicates)

Spam detection:
├─ Domain reputation score (ML model)
├─ Link graph analysis (abnormal links)
├─ Content analysis (generated text detection)
├─ User signals (bounce rate, time-on-site)

Cost: ML inference <5ms per document
```

---

## 🤖 ML System

### Online Learning

```
Problem: Search results quickly become stale
Solution: Real-time signals update relevance

Pipeline:
Click logs → Kafka → Stream processor → Feature store

Updates:
- CTR (click-through rate): changes within hours
- Bounce rate: changes within hours
- Fresh content detection: real-time

Implementation:
- Keep CTR features in Redis (fast lookup)
- Updated hourly from logs
- Ranking model uses fresh CTR in scoring
- More clicks = higher relevance score
```

### Semantic Search (BERT Integration)

```
Problem: Keyword matching misses semantic intent
Example: "best programming book" vs "top coding resource"

Solution: Semantic embeddings
├─ Query embedding: BERT("best programming book") → 768D vector
├─ Document embedding: BERT(doc title + snippet) → 768D vector
├─ Similarity: Cosine(query_embed, doc_embed)

Implementation:
├─ Index: Precomputed document embeddings
├─ Query time: BERT inference on query (5ms)
├─ Retrieval: ANN search (FAISS) for similar docs
├─ Ranking: Use similarity as feature in LambdaMART

Result:
- Captures semantic intent
- Improves relevance
- Handles synonyms automatically
```

### Typo Tolerance

```
Problem: "Serach" (typo of "Search") should still work

Solution: Edit distance + fuzzy matching
├─ For misspelled query: generate corrections
├─ "serach" → ["search", "serach", ...]
├─ Rank corrections by similarity
├─ Blend results from corrected query

Implementation:
- BK-tree index for edit distance
- Fast typo detection (<1ms)
- Fallback: show "Did you mean: search?"
```

---

## ⚡ Production

### Freshness

**Problem:** New pages take weeks to appear in search

**Solution: Rapid indexing**
```
Crawling schedule:
├─ Popular pages: crawled every 24 hours
├─ Medium pages: crawled every 7 days
├─ Rare pages: crawled every month

Pipeline:
Crawl → Parse → Extract features → Index update

Total latency: Hours to days

Real-time signals (within hours):
├─ Social media mentions
├─ Breaking news detection
├─ Top query acceleration (crawl trending topics faster)
```

### Spam Combat

```
Adversarial problem: SEO spam evolves constantly

Detection:
├─ Link spam: abnormal inbound link patterns
├─ Content spam: generated text detection (NLP)
├─ Cloaking: serving different content to Googlebot
├─ Private: DNS hijacking, compromised sites

Mitigation:
├─ Manual review of flagged domains
├─ Automated penalties for spam signals
├─ User report feedback
├─ Collaboration with site owners

Arms race:
├─ Spammers evolve tactics
├─ Google updates spam detector
├─ Cycle repeats (weeks to months)
```

### Monitoring

```
Alerts:
├─ p99 latency > 200ms
├─ Ranking quality drop (A/B test shows lower CTR)
├─ Index freshness lag > 24 hours
├─ Spam increase (user complaints)

Quality metrics:
├─ CTR (click-through rate) per result
├─ Zero-click searches (good answer shown in snippet)
├─ Time-to-first-click (how quickly user finds answer)
├─ Dwell time (how long user stays on site)
```

---

## 🔧 Optimizations

### Optimization 1: Early Termination

```
Bottleneck: Ranking 1000 candidates

Optimization: Don't rank all 1000
├─ Sort candidates by simple signal (PageRank)
├─ Rank top 100 only
├─ Latency: 100ms → 50ms
├─ Quality loss: <1% (already good candidates)

Trade-off:
- Faster response
- Might miss relevant doc ranked outside top 100
- Acceptable (top-100 already very relevant)
```

### Optimization 2: Two-Level Ranking

```
Level 1: Fast ranker (CPU)
├─ Simple features (BM25, PageRank)
├─ Returns: top 200
├─ Latency: 30ms

Level 2: Slow ranker (GPU/GBDT)
├─ Complex features (semantic, freshness, quality)
├─ Ranks only top 200
├─ Latency: 50ms

Result: 80ms total (vs 100ms)
Quality: Comparable (second-pass ranks best candidates)
```

### Optimization 3: Caching

```
Popular queries (60% of traffic):
├─ "weather"
├─ "time"
├─ "news"
├─ etc.

Cache strategy:
├─ For popular queries: fully cache results
├─ TTL: 1 hour
├─ Cache hit rate: 60% of requests
├─ Saved latency: 200ms (direct response)

Cost: 1000 Redis nodes to store top 1M queries
Benefit: 60% of requests serve in <10ms (from cache)
```

---

## 🔴 Failure Modes

### Failure 1: Index Shard Down

```
Symptom: Query returns only 9 results instead of 10

Cause:
- One of 1000 index shards becomes unavailable
- ~1/1000 queries affected (those needing results from that shard)

Detection:
- Query latency doesn't spike (fast enough without one shard)
- Result count drops (one result missing)
- Alert: <95% of expected results returned

Mitigation:
- Replicate each shard 3x across datacenters
- Failover to replica automatically
- Query can complete without waiting for failed shard
  └─ Degrade result count, but serve fast
```

### Failure 2: Ranking Model Degrades

```
Symptom: CTR drops 10% after model update

Root cause:
- New ranking model makes worse decisions
- Training-serving skew
- Bug in feature engineering

Detection:
- A/B test: 1% of users get new model
- Monitor CTR, dwell time, bounce rate
- Alert if CTR < baseline - 2%

Fix:
- Rollback: revert to previous model (5 min)
- Investigate: identify feature bug
- Retrain: fix + train new model (6 hours)
- Canary: deploy to 10% → 50% → 100%
```

---

## 📈 Scaling

### 10x Traffic

```
Current: 100K QPS
Scaled: 1M QPS

Bottleneck: Ranking (GBDT inference)

Solution 1: Model distillation
├─ Train small student on large teacher
├─ Student: 10x faster
├─ Quality: 95% of original
├─ Inference: 10ms → 1ms per document

Solution 2: More GPUs
├─ Current: 500 GPUs
├─ Need: 5000 GPUs for 1M QPS
├─ Cost: $50M+ capex

Solution 3: Approximate ranking
├─ Use fast heuristic for initial rank
├─ Only rank top 100 precisely
├─ Efficiency: 10x better

Use: Distillation + approximate ranking
Result: Handle 1M QPS with 1000 GPUs (vs 5000)
```

---

## 💭 Interview Questions

1. How would you handle a query in a language with limited training data?
2. What if PageRank computation becomes latency bottleneck?
3. How do you prevent adversarial queries from breaking the system?
4. How would you support searching 10x more pages with same latency?
5. What's the impact of a 1-second index delay on user experience?

---

*Last Updated: 2026-05-28*
