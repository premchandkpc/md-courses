---
title: YouTube Recommendations System - Google L5 Deep Dive
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# YouTube Recommendations System - Google L5 Deep Dive

> **[🎨 View Interactive Diagram](youtube-architecture.html)** | [← Back to Index](systems-index.html)

*"How do you recommend the right video to the right user at the right time, at planetary scale?"*

---

## 🎬 Context: The Opportunity

**YouTube Stats:**
- 2.5 billion users
- 500 hours of video uploaded per minute
- 1 billion hours watched per day
- 80% of watch time driven by recommendations
- Watch time on recommended videos: ~200M hours/day

**Your mission:** Design the system that handles that.

---

## 🔍 Phase 1: Requirements Clarification

### Functional Requirements

**User-facing:**
1. Generate personalized video recommendations for homepage
2. Update feed in real-time as user scrolls
3. Optimize for watch time (not clicks)
4. Balance fresh content with proven recommendations
5. Handle creator growth (new videos, channels)
6. Support different geographies, languages, devices

**System requirements:**
1. Serve billions of daily recommendations
2. Low latency (<500ms p99)
3. Handle mobile, desktop, TV
4. Support A/B testing framework
5. Graceful degradation under failure

### Non-Functional Requirements

**Scale:**
- 1B+ daily active users
- 500+ hours uploaded per minute
- 10M+ simultaneous viewers
- 100K+ videos ranking per user per day

**Latency:**
- p50: <100ms
- p99: <500ms
- p99.9: <1000ms

**Consistency:**
- Eventual consistency OK (users see slightly stale recommendations)
- No strong consistency requirement
- Freshness: updated within seconds for trending

**Freshness:**
- Trending videos: <5 min delay
- Regular videos: <1 hour delay
- User interaction signals: <100ms

**Availability:**
- 99.99% uptime
- Graceful degradation under partial outage
- Fallback to simple recommendations

---

## 📊 Phase 2: Estimation Section

### Traffic Estimation

```
Daily Active Users (DAU): 1 billion
Recommendation calls per user per day: 10 (homepage + scrolls)
Total daily recommendation requests: 10B

QPS = 10B requests / 86400 seconds = 115,740 QPS
Peak QPS (3x average): ~350,000 QPS

Recommendation generation per request: 1000-5000 candidates to rank
Total ranking operations: 10B * 2000 = 20 trillion ranking operations/day
```

### Storage Estimation

**Video Metadata:**
```
Total videos: 1 billion
Metadata per video: 5KB (title, description, thumbnail, tags)
Total: 1B * 5KB = 5 TB

But only ~10% actively watched: 500 GB hot tier
```

**User Profile & History:**
```
Users: 1 billion
Watch history per user: 1000 videos
History storage: 1B * 1000 * 16 bytes (video ID) = 16 TB
But recent 1000 is hot: ~16 TB in cache

User profile features: 100 features * 4 bytes = 400 bytes
Total: 1B * 400 = 400 GB
```

**Embeddings Storage:**
```
Video embeddings: 256 dimensions * 4 bytes float = 1 KB per video
1B videos * 1 KB = 1 TB

User embeddings: 256 dimensions * 4 bytes float = 1 KB per user
1B users * 1 KB = 1 TB

Total embeddings in vector DB: 2 TB
But hot (recently active): 100-200 GB
```

**Feature Store:**
```
Real-time features: 200 features per user/video pair
Feature storage (sample): 1% of pairs = 1B pairs
1B * 200 * 4 bytes = 800 GB

Keep in Redis for fast lookup
```

**Kafka Buffer (for streaming):**
```
User interactions: 1B users * 100 interactions/day = 100B events/day
Event size: ~100 bytes
Kafka retention: 7 days
Storage: 100B * 100 * 7 = 70 TB
But distributed: 70 TB / 10 brokers = 7 TB per broker
```

### Compute Estimation

**Retrieval (Candidate Generation):**
```
10B requests/day * 2000 candidates = 20 trillion candidate generations
If using ANN (FAISS): 1 million QPS per machine (approximate)
Machines needed: 350K QPS / 1M QPS per machine = ~1 machine cluster
But redundancy + load balancing: 5-10 machines
But distributed across datacenters: 50-100 machines globally
```

**Ranking:**
```
10B requests/day * 2000 candidates = 20 trillion rankings
Neural ranking model inference: ~1000 inferences/second per GPU
QPS: 350K * 2000 = 700M ranking ops/sec
GPUs needed: 700M / 1000 = 700K GPUs (!!)

Actually: batch in groups of 1000
Effective throughput: 1000 inferences/ms * 1000 batch = 1M ops/sec per GPU
GPUs needed: 700K GPUs / 1000 = 700 GPUs
Plus redundancy + regional distribution: 5-10K GPUs globally
```

**Re-ranking (diversity/freshness):**
```
10B requests * 100 candidates served = 1T re-ranking operations
This is CPU-based (simpler): 1M ops/sec per CPU
CPUs needed: 1T / 86400s / 1M = ~11,500 CPUs
```

### Network Bandwidth

```
Request: (user ID, context) = 100 bytes
Response: (100 video IDs + metadata) = 10 KB
Daily bandwidth: 10B * 10 KB = 100 PB/day incoming
Response: 100 PB/day outgoing (to edge)

But compressed: 50 PB/day

Per second: 50 PB / 86400s = 580 GB/sec
This assumes global distribution + CDN caching
```

---

## 🏗️ Phase 3: High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Client                             │
│          (Web, Mobile, TV, Smart Home)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   API Gateway / Load Balancer │
        │   (per geography/device)      │
        └──────────────────┬────────────┘
                           │
        ┌──────────────────┴────────────────────┐
        │                                       │
        ▼                                       ▼
   ┌─────────────┐                    ┌──────────────────┐
   │  Request    │                    │  Context Service │
   │  Router     │                    │  (user location, │
   │  (decide    │                    │   device, time)  │
   │  ranking    │                    └──────────────────┘
   │  pipeline)  │
   └──────┬──────┘
          │
    ┌─────┴──────────────────────────────┐
    │                                    │
    ▼                                    ▼
┌──────────────────────┐      ┌──────────────────────┐
│ Candidate Generation │      │ Ranking Service      │
│ Layer                │      │                      │
│ (Retrieve 1000s)     │      │ (Score + Filter)     │
│                      │      │                      │
│ - Collaboration      │      │ - Neural network     │
│ - Content-based      │      │ - Features           │
│ - Trending           │      │ - Multi-objective    │
│ - Fresh pool         │      │ - Diversity boost    │
│ - ANN (FAISS)        │      │                      │
└──────────────────────┘      └──────────────────────┘
         │                              │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────┐
         │  Re-ranking Service      │
         │  (freshness boost,       │
         │   diversity, dedup)      │
         └──────────────┬───────────┘
                        │
                        ▼
        ┌────────────────────────────┐
        │  Response Construction     │
        │  (metadata enrichment)     │
        └─────────────┬──────────────┘
                      │
                      ▼
         ┌──────────────────────┐
         │  Client / Cache      │
         │  (edge + browser)    │
         └──────────────────────┘
```

### Data Flow Layers

```
ONLINE SERVING LAYER (Real-time)
├─ API Gateway
├─ Candidate Generation (retrieval)
├─ Ranking (inference)
└─ Re-ranking (business logic)
    └─ Response Cache (Redis/Memcached)

FEATURE LAYER (Real-time + Batch)
├─ User Features (Redis)
│  └─ Watch history, embeddings, interests
├─ Video Features (Redis)
│  └─ Category, creator, freshness, quality
└─ Context Features
   └─ Time, device, location, language

ML MODEL LAYER (Offline trained, online served)
├─ Candidate Generation Models
│  └─ Collaborative filtering, content-based
├─ Ranking Models
│  └─ Watch-time prediction, CTR prediction
└─ Re-ranking Logic
   └─ Diversity, freshness boosting

OFFLINE BATCH LAYER (Training + Precomputation)
├─ Training Pipelines (daily/weekly)
│  └─ XGBoost, neural networks
├─ Embedding Generation
│  └─ Video & user embeddings
└─ Index Precomputation
   └─ FAISS indexes for ANN search
```

---

## 🎯 Phase 4: Deep Component Dives

### Component 1: Candidate Generation (Retrieval)

**Purpose:** Retrieve ~1000 potential videos from 1B+ corpus in <100ms

**Architecture:**

```
User Query (user_id, context)
    │
    ▼
┌─────────────────────────────────────────────┐
│ Feature Extraction                          │
│ - User embedding (from Redis)               │
│ - User interests (watch history)            │
│ - Context (time, device, location)          │
└────────────┬────────────────────────────────┘
             │
    ┌────────┴────────────┬──────────────────────┐
    │                     │                      │
    ▼                     ▼                      ▼
┌───────────────┐  ┌────────────┐  ┌──────────────────┐
│ Collaboration │  │ Content-   │  │ Trending /       │
│ Filtering Pool│  │ Based Pool │  │ Fresh Content    │
│               │  │            │  │ Pool             │
│ FAISS Index   │  │ FAISS Index│  │                  │
│ (user<->user) │  │(metadata + │  │ Manually curated │
│               │  │ embeddings)│  │ OR trending algo │
│ Return 300    │  │ Return 400 │  │ Return 300       │
└───────────────┘  └────────────┘  └──────────────────┘
    │                     │                      │
    └─────────────────────┴──────────────────────┘
                          │
                          ▼
            ┌──────────────────────────┐
            │ Deduplication + Filtering│
            │ - Remove seen videos     │
            │ - Remove blocked content │
            │ - Apply diversity filter │
            │                          │
            │ Output: ~1000 candidates │
            └──────────────────────────┘
```

**Storage:**
```
FAISS Indexes (on SSDs/RAM):
- User-user collab: 1B users * 256D embeddings * 4 bytes = 1 TB
  (keep top 10M active users in RAM: 40 GB)
  
- Content index: 1B videos * 256D embeddings * 4 bytes = 1 TB
  (keep top 100M videos in RAM: 100 GB)

Sharding strategy:
- User index: partition by user_id % 1000
  Each shard handles 1M users
  Distributed across 100 machines (10 shards per machine)

- Video index: partition by video_id % 1000
  Each shard handles 1M videos
  Distributed across 100 machines

- Replication: 3x across datacenters
```

**APIs:**
```
GET /candidate_generation/collab
  Input: user_id, top_k=300
  Output: [video_id, score, features]
  Latency SLA: <30ms p99

GET /candidate_generation/content_based
  Input: user_embedding, top_k=400
  Output: [video_id, score, features]
  Latency SLA: <30ms p99

GET /candidate_generation/trending
  Input: geo, language, top_k=300
  Output: [video_id, score, features]
  Latency SLA: <10ms p99 (cached)
```

**Caching:**
```
Redis cache layer:
- User embeddings (10M active): ~40 GB
- Top video embeddings (100M): ~100 GB
- Recent trending videos (per geo): ~5 GB
- Cache TTL: 1 hour for embeddings, 5 min for trending

Cache miss: regenerate from FAISS
```

**Failure Handling:**
```
If collab filtering fails → fallback to content-based
If content-based fails → fallback to trending
If all fail → return hardcoded popular videos
```

---

### Component 2: Ranking Service

**Purpose:** Score and order ~1000 candidates by watch-time potential

**Models:**

```
Input Features:
├─ User Features (100)
│  ├─ Watch history embedding (256D)
│  ├─ Average watch duration
│  ├─ Preferred categories
│  ├─ Preferred creators
│  ├─ Country, language
│  ├─ Device type
│  └─ Time of day
│
├─ Video Features (100)
│  ├─ Video embedding (256D)
│  ├─ Video age (freshness)
│  ├─ Category
│  ├─ Creator reputation
│  ├─ View count + velocity
│  ├─ Like/comment engagement
│  ├─ Predicted quality score
│  └─ Duration
│
└─ Interaction Features (50)
   ├─ User-watched-category (0/1)
   ├─ User-follows-creator (0/1)
   ├─ Video-similarity-to-watch-history
   ├─ Time-since-upload
   └─ Regional popularity

Output: Predicted watch-time (hours)
```

**Model Architecture:**

```
Two-tower neural network:

User Tower:          Video Tower:
Input (100D)         Input (100D)
    │                    │
    ▼                    ▼
Dense(512)           Dense(512)
  ReLU                 ReLU
    │                    │
    ▼                    ▼
Dense(256)           Dense(256)
  ReLU                 ReLU
    │                    │
    ▼                    ▼
Dense(128)           Dense(128)
  ReLU                 ReLU
    │                    │
    └────────┬───────────┘
             │
             ▼
        Dot Product
             │
             ▼
        Dense(1)
        Sigmoid
             │
             ▼
    Watch-time Prediction
    (0-360 minutes)
```

**Inference Optimization:**

```
Batch inference:
- Input: 1000 candidates * 200D features = 200K features
- Batch size: 1000 (all candidates for one user)
- Time per batch: 10ms
- Throughput: 100 batches/sec per GPU = 100K rankings/sec

GPU utilization:
- We need 350K QPS
- 100K rankings/sec per GPU
- 3.5 GPUs during average load
- 10+ GPUs with redundancy + peak load

Model serving: TensorFlow Serving or PyTorch Serve
- Load balancer distributes requests
- Batch accumulation (10ms window)
- Fallback: CPU inference if GPUs saturated
```

**Score Formula:**

```
score =
    watch_time_pred * (1.0) +
    freshness_boost * (0.2 if age < 24h else 0) +
    creator_quality_score * (0.1) +
    diversity_penalty +  // reduce similar videos
    cold_start_bonus * (0.5 if creator_new else 0)
```

**Caching:**

```
Redis cache for ranked results:
- Key: user_id + session_id
- Value: top 200 ranked video_ids
- TTL: 5 minutes
- Cache hit rate: ~60% (same user scrolling)
```

---

### Component 3: Re-ranking Service

**Purpose:** Apply business logic (freshness, diversity, deduplication)

```
Input: 1000 ranked videos
    │
    ▼
┌─────────────────────────────┐
│ 1. Deduplication            │
│    - Remove if user watched │
│    - Remove if user liked   │
│    - Remove last N watched  │
└──────────────┬──────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 2. Diversity Filter          │
│    - Max N videos per creator│
│    - Max N videos per        │
│      category                │
│    - Vary video duration     │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 3. Freshness Boost           │
│    - Trending videos move up │
│    - New uploads move up     │
│    - Creator livestream      │
│      highest priority        │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 4. Quality Filter            │
│    - Remove problematic      │
│      content                 │
│    - Remove demonetized      │
│    - Check regional blocks   │
└──────────────┬───────────────┘
               │
               ▼
    Output: 100 videos to user
```

**Implementation:**

```python
def rerank(candidates, user_id):
    # 1. Dedup
    watch_history = redis.get(f"watch:{user_id}")
    candidates = [v for v in candidates if v.id not in watch_history]
    
    # 2. Diversity
    creators_shown = {}
    categories_shown = {}
    result = []
    
    for video in candidates:
        if creators_shown[video.creator_id] < MAX_PER_CREATOR:
            if categories_shown[video.category] < MAX_PER_CATEGORY:
                result.append(video)
    
    # 3. Freshness boost
    result.sort(key=lambda v: (
        -is_trending(v.id),
        -freshness_score(v.upload_time),
        -v.rank_score
    ))
    
    # 4. Quality filter
    result = [v for v in result if not is_problematic(v.id)]
    
    return result[:100]
```

**Latency:** <5ms (mostly filtering, no model inference)

---

### Component 4: Feature Store

**Purpose:** Serve 1000s of features at <5ms latency

**Architecture:**

```
Real-time Features (Redis):
├─ User features (400MB per machine)
│  ├─ Watch history (last 1000 videos)
│  ├─ User embedding
│  ├─ Preferences
│  └─ Engagement metrics
│
├─ Video features (500MB per machine)
│  ├─ Embeddings
│  ├─ Metadata
│  ├─ Recent stats
│  └─ Quality scores
│
└─ Computed features (100MB)
   ├─ User-video similarity
   └─ Contextual scores

Update Pipeline:
   Kafka Streams
        │
        ▼
   Feature Computation
        │
        ▼
   Redis Publish
        │
        ▼
   Cache TTL: 1 hour
   Refresh: via streaming
```

**Sharding:**

```
Redis Cluster (24 nodes):
- User features: Partition by user_id % 1000
- Video features: Partition by video_id % 1000
- Replication: 3x
- Failover: automatic

Hot tier (30GB):
- Top 100M actively used features
- Cache hit rate: >95%

Cold tier (Disk):
- Full feature database
- Used for cold start, backfill
```

**APIs:**

```
GET /features/user/{user_id}
  Returns: 200 user features
  Latency: <2ms

GET /features/video/{video_id}
  Returns: 200 video features
  Latency: <2ms

GET /features/batch
  Input: [(user_id, video_id), ...]
  Returns: interaction features
  Latency: <5ms
```

---

### Component 5: Vector Database (Embeddings)

**System:** FAISS (Facebook AI Similarity Search)

**Why FAISS:**
- Billions of embeddings
- <10ms query latency
- GPU acceleration
- Approximate nearest neighbors (sufficient accuracy)

**Index Type:**
```
IVF (Inverted File) Index:
- Split vectors into 1000 clusters (coarse quantization)
- Search returns approximate neighbors
- Speed-accuracy tradeoff:
  - 99% recall: ~100ms
  - 90% recall: ~20ms
  - 50% recall: ~5ms
  
We use: ~90% recall (good balance)
```

**Storage:**

```
User Embeddings (256D float32):
- 1B users * 256 * 4 = 1 TB
- But only 10M active in RAM: 40 GB
- Distributed across 10 machines (4 GB per machine)
- With replication: 12 GB per machine

Video Embeddings (256D float32):
- 1B videos * 256 * 4 = 1 TB
- Keep 100M hot: 100 GB
- Distributed across 10 machines (10 GB per machine)
- With replication: 30 GB per machine
```

**Update Strategy:**

```
New embeddings computed:
- Daily batch: recompute user embeddings (daily engagement)
- Hourly batch: recompute video embeddings (new content)

Index update:
- Build new index overnight
- Gradually shift traffic to new index
- Old index serves requests for 24 hours (safety)
- Shadow index validation (compare results)
```

---

## 🤖 Phase 5: ML System Deep Dive

### 5.1 Retrieval Models

**Model 1: Collaborative Filtering**

```
Input: user_id
Output: 300 similar videos (weighted by popularity)

Implementation: User-User Collab Filtering via embedding
├─ Compute user embedding from watch history
├─ Find similar users via cosine similarity
├─ Aggregate videos watched by similar users
└─ Weight by similarity * popularity

User embedding = Average(video embeddings watched by user)
    = Sum(embed[v] for v in watch_history) / len(watch_history)

Similarity = cosine(user_embed, other_user_embed)

Candidates = Weighted union of videos from top 100 similar users

Pros:
  ✓ Captures user preferences
  ✓ Can handle cold start with aggregate embeddings
  ✓ Fast at scale

Cons:
  ✗ Can be biased toward popular content
  ✗ May miss diverse content
  ✗ Needs fresh user embeddings (daily recompute)
```

**Model 2: Content-Based Filtering**

```
Input: user_id
Output: 400 similar videos

Implementation: Video-Video similarity via embeddings
├─ Get user's watch history
├─ For each video in history:
│   └─ Find N similar videos (high cosine similarity)
├─ Aggregate and deduplicate
└─ Return top 400 by weighted score

Video Similarity = Cosine(embed[v1], embed[v2])

Score = Sum(similarity(v, watched_video) 
         * watch_time(watched_video) 
         / total_watch_time)

Pros:
  ✓ Can recommend niche content
  ✓ Doesn't need user embeddings
  ✓ Explainable (similar to what you watched)

Cons:
  ✗ Can get stuck in filter bubble
  ✗ Embedding quality critical
  ✗ Sensitive to embedding drift
```

**Embedding Training:**

```
Training Data:
- User watch sequences (user_id, [video_ids], duration_seconds)
- Billions of sequences from logs

Loss Function: Contrastive loss
- Similar videos (watched together) → close embeddings
- Dissimilar videos (not watched together) → far embeddings

sketch_loss = ||embed[v_watch] - embed[v_context]||^2 
            + sum(neg_sample, max(0, margin - ||embed[v_watch] - embed[v_neg]||^2))

Training:
- Model: 4-layer MLP + embedding layer
- Data: 1B+ sequences
- Hardware: 100+ GPUs
- Time: 24 hours
- Batch size: 64K
- Learning rate: 0.001 with decay

Every 7 days: Retrain embeddings with fresh data
```

### 5.2 Ranking Models

**Core Model: Watch-Time Prediction**

```
Input: (user features, video features, context)
Output: Predicted watch-time (0-360 minutes)

Model: Deep neural network

Architecture:
User Input(100)─┐
                ├─→ User Tower ─→ Dense(128) ─┐
                │                              │
Video Input(100)┼─→ Video Tower ─→ Dense(128) ├─→ Dot Product ─→ Dense(128) ─→ Dense(1)
                │                              │
Context(50)─────┘                              │
                                           ReLU + Dropout
                                               │
                                          Sigmoid * 360
                                               │
                                          Watch-time (mins)
```

**Loss Function:**

```
For each (user, video) pair:
- y_true = actual watch time in seconds
- y_pred = predicted watch time

Loss = MSE(y_pred, y_true) + weighted_L2_regularization

# Weight samples: longer watch-times more important
sample_weight = sqrt(y_true + 1)  # avoid zero weight

Weighted_MSE = mean(sample_weight * (y_pred - y_true)^2)
```

**Training Pipeline:**

```
Data Collection:
- 10B watch events per day
- Each event: (user_id, video_id, context, watch_time)
- Stored in Hive/BigQuery

Preprocessing (daily):
- Extract features (embeddings, metadata, engagement)
- Join with user profile table
- Join with video metadata table
- Generate interaction features

Training (daily):
- Data: 10B records * 7 days = 70B training examples
- Downsampled for speed: sample 1% = 700M records
- Split: 70% train, 15% val, 15% test

Validation:
- Compute AUC (for binary classification version)
- Compute RMSE on holdout set
- A/B test on 1% of users (shadow traffic)

Deployment:
- If RMSE improves: gradual rollout (10% → 50% → 100%)
- Monitor watch-time lift
- Rollback if watch-time drops

Model size: ~50MB (can fit in GPU memory)
Inference: 10ms per batch of 1000
```

### 5.3 Online Learning

**The Problem:**
- User preferences change (drift)
- New videos arrive constantly
- Feedback (watches) is immediate
- Daily retraining is too slow

**Solution: Incremental Learning**

```
Approach 1: Feature update (lightweight)
├─ Every watch updates user embedding
├─ Update: user_embed = 0.9 * user_embed + 0.1 * watched_video_embed
├─ Latency: <1ms (just Redis update)
└─ Effect: user quickly adapts to new content

Approach 2: Online model update (heavier)
├─ Batch of 100K recent watches
├─ Update model weights via SGD
├─ Every 1 hour (not every watch)
├─ Use streaming features from Kafka
└─ Keep model coefficients lightweight

Approach 3: Bandit algorithms (exploration)
├─ Explore new content with small probability
├─ Exploit known good content
├─ Update exploration distribution based on results
└─ Discussed below
```

### 5.4 Exploration vs Exploitation

**The Tradeoff:**
```
Exploitation: Show videos we know user will watch
- Maximizes immediate watch-time
- Leads to filter bubble (same content forever)
- Bad for business: limits discovery, creator growth

Exploration: Show videos user might not watch
- Increases diversity
- Discovers new interests
- Better for ecosystem
- Short-term watch-time may decrease
```

**Thompson Sampling (Bandit Algorithm):**

```
For each video in candidate pool:
1. Maintain (alpha, beta) = Beta distribution params
   - alpha = number of positive feedback
   - beta = number of negative feedback

2. Sample theta ~ Beta(alpha, beta)
   - theta = estimated CTR for this video

3. Score = theta (random sample from distribution)
   - High uncertainty → higher chance of exploration
   - High exploitation value → higher score

4. User watches/skips the video
   - If watch: alpha += 1
   - If skip: beta += 1
   - Update distribution

Result: Natural exploration-exploitation balance
```

**Implementation:**

```python
class ThompsonSampler:
    def __init__(self, video_id):
        self.alpha = 1  # 1 watch
        self.beta = 1   # 1 skip (initial)
    
    def sample_ctr(self):
        # Sample from Beta distribution
        return np.random.beta(self.alpha, self.beta)
    
    def update(self, did_watch):
        if did_watch:
            self.alpha += 1
        else:
            self.beta += 1

# In ranking:
def score_video(video, user, context):
    base_score = ranking_model.predict(user, video, context)
    
    # Thompson sampling score (exploration bonus)
    sampler = redis.get(f"sampler:{video.id}")
    thompson_score = sampler.sample_ctr()
    
    # Blend: exploit known good + explore new
    final_score = 0.95 * base_score + 0.05 * thompson_score
    
    return final_score
```

**Results:**
- Exploration ratio: ~5% (adjustable)
- New videos get exposure
- Users discover new interests
- Watch-time barely decreases (short-term)
- Leads to better long-term satisfaction

### 5.5 Cold Start Problem

**New User (no watch history):**
```
Solution 1: Demographics-based
├─ Age, country, language → find similar users
├─ Use collaborative filtering from similar cohorts
└─ Works OK, takes 10+ interactions to personalize

Solution 2: Context-based
├─ Recommend trending/popular videos
├─ Geographic popularity
├─ Language-matched content
└─ Fast, universal

Solution 3: Hybrid
├─ Blend demographics + context
├─ Show trending content (learn preferences)
├─ Gradually shift to personalized
└─ Best approach
```

**New Video (no engagement history):**
```
Solution 1: Creator reputation
├─ Popular creator → higher initial ranking
└─ Gives new video from trusted creator visibility

Solution 2: Content quality signals
├─ Title quality score (ML model)
├─ Thumbnail quality score
├─ Description quality
├─ Video resolution/bitrate
└─ Shows good production value

Solution 3: Freshness boost
├─ New videos get ranking boost
├─ Gradually decay as video ages
├─ Lets algorithms learn true engagement
└─ Bootstrap engagement discovery

Solution 4: Cold start pool
├─ Dedicated 5% of ranking slots for new videos
├─ Sample diverse creators/categories
├─ Learning happens on this 5%
└─ Avoids new video placement conflicts
```

**Boosting Formula:**

```
cold_start_boost = {
    0.5 if video.age < 1h AND creator.verified,
    0.3 if video.age < 24h AND creator.verified,
    0.1 if video.age < 24h,
    0.0 otherwise
}

adjusted_score = base_score + cold_start_boost
```

### 5.6 Multi-Objective Optimization

**Problem:** YouTube optimizes for multiple metrics simultaneously:
1. Watch time (revenue, user engagement)
2. Diversity (ecosystem health, creator growth)
3. Freshness (content discovery, new videos)
4. Engagement (comments, likes, shares)
5. Satisfaction (long-term retention)

**Approach: Weighted Multi-Objective**

```
score = 
    w1 * watch_time_score +
    w2 * diversity_score +
    w3 * freshness_score +
    w4 * engagement_score +
    w5 * satisfaction_score

where sum(w_i) = 1.0

Weights tuned via A/B testing:
- w1 = 0.50 (watch time: primary)
- w2 = 0.10 (diversity: important)
- w3 = 0.15 (freshness: important)
- w4 = 0.15 (engagement: important)
- w5 = 0.10 (satisfaction: important)

Tuning process:
- Change weights 10% at a time
- Run A/B test (1-2 weeks)
- Measure impact on overall satisfaction
- Adjust incrementally

Result: Balanced recommendations
- Users get good content (watch time)
- Diverse (not repetitive)
- Fresh (new uploads visible)
- Engaging (high comment videos)
- Satisfying (long-term usage)
```

---

## ⚡ Phase 6: Production Realities

### Failure Mode 1: Ranking Latency Spike

**Symptom:** Response times jump from 100ms to 500ms+

**Root Causes:**
```
1. GPU saturation
   - Load increase (viral event)
   - Model size increase (new model too big)
   - Batch accumulation timeout

2. Feature store timeout
   - Redis connection pool exhausted
   - Network latency spike
   - Feature computation slow

3. Candidate generation bottleneck
   - FAISS index not in memory
   - Database query slow
   - Network issue

4. Re-ranking filter explosion
   - Dedup filter very slow (huge watch history)
   - Diversity filter over-filtering
   - Database query for content filtering
```

**Detection:**
```
Monitoring:
- p99 latency SLI
- p99 GPU queue depth
- Redis connection pool exhaustion
- Feature store error rate

Alert triggers:
- p99 latency > 200ms (SLA is 500ms p99)
- GPU queue > 100 (indicates saturation)
- Redis timeout rate > 0.1%
```

**Mitigation (in priority order):**
```
Immediate (seconds):
1. Load shed: start returning cached results
2. Reduce batch size to unblock
3. Fallback to simpler ranking model (CPU-based)

Short-term (minutes):
4. Scale up GPU pool (if available)
5. Drain traffic to other datacenters
6. Switch to smaller ranking model

Long-term (hours):
7. Investigate root cause
8. Deploy fix
9. Canary rollout
```

**Prevention:**
```
- Batch accumulation: don't wait >10ms for batch full
- GPU reservation: keep 20% headroom
- Model optimization: quantization to reduce memory
- Caching: increase cache for repeated requests
- Load shedding: return popular videos if overloaded
```

### Failure Mode 2: Model Drift / Quality Drop

**Symptom:** Watch-time decreases 5%+ after model update

**Root Causes:**
```
1. Training-serving skew
   - Features computed differently in offline vs online
   - Feature ranges change
   - Missing features at serving time

2. Data distribution shift
   - User behavior changes (seasonality, trend)
   - New videos appear (content shift)
   - Device mix changes

3. Embedding staleness
   - User embeddings updated slowly
   - Video embeddings outdated
   - Means vs new content

4. Bug in training
   - Data leak (future info in features)
   - Wrong labels (watch time miscalculation)
   - Feature engineering mistake
```

**Detection:**
```
Offline validation:
- Track AUC, RMSE on holdout set
- Check feature distributions (KL divergence)
- Compare with previous model

Online A/B test:
- Run on 1% traffic first (shadow traffic)
- Measure watch-time, engagement, retention
- Alert if any metric < baseline - 2%

Continuous monitoring:
- Watch-time per recommendation
- Click-through rate
- Average session length
- User retention (weekly)
```

**Fix:**
```
If detected before rollout:
1. Don't deploy
2. Investigate in offline analysis
3. Fix training code
4. Retrain
5. Restart A/B test

If detected after rollout:
1. Immediate: roll back to previous model
2. Parallel: investigate root cause
3. Fix + retrain
4. Canary rollout (10% → 25% → 50% → 100%)
```

### Failure Mode 3: Embedding Staleness

**Symptom:** Recommendations don't capture recent user behavior

**Root Cause:**
```
- User embeddings updated once per day
- But user preferences change within hours
- New watch = no embedding update = stale preferences
```

**Solution: Incremental Updates**

```
Approach 1: Streaming updates
├─ Watch event arrives in Kafka
├─ Lightweight update: user_embed = 0.9 * old_embed + 0.1 * video_embed
├─ Write back to Redis
├─ Latency: <1ms

Approach 2: Embedding update stream
├─ Kafka stream processes watches
├─ Accumulate 1000 watches
├─ Recompute embeddings
├─ Every 10 minutes

Approach 3: Hybrid
├─ Streaming update (fast) for immediate effect
├─ Batch update (hourly) for accuracy
├─ Blend: 0.7 * streaming + 0.3 * batch

Result:
- User preferences adapt in <1 second
- No staleness
- Still accurate (batch smoothing)
```

### Failure Mode 4: Cascading Failures

**Scenario:** Feature store timeout → ranking slowdown → ranking timeout → recommendation timeout

```
BEFORE (No Graceful Degradation):
User Request
    ↓
Candidate Generation [OK]
    ↓
Ranking Service
    ├─ Gets features [TIMEOUT after 100ms]
    ├─ Waits for response
    └─ Times out at 200ms
    ↓
Return nothing [FAIL]
```

**Solution: Graceful Degradation**

```
AFTER (With Fallback):
User Request
    ↓
Candidate Generation [OK]
    ↓
Ranking Service
    ├─ Try to get features [TIMEOUT]
    ├─ Fallback: use cached features from 1 hour ago
    ├─ Ranking completes with stale features [OK-ISH]
    └─ Complete request in 50ms
    ↓
Return results (quality degraded, but serving)

Implementation:
def get_features(user_id, video_id):
    try:
        return redis.get(f"features:{user_id}:{video_id}", 
                         timeout=50ms)
    except TimeoutError:
        # Fallback
        return cache.get(f"features_cache:{user_id}:{video_id}")
        # TTL: 24 hours
```

**Cascading Prevention:**

```
Circuit breaker pattern:
├─ Monitor feature store latency
├─ If p99 > 100ms: open circuit
├─ Reject new requests, use fallback
├─ Check every 10 seconds
├─ Once latency recovers: close circuit

Benefits:
✓ Prevents cascading timeout
✓ Upstream sees fast failures (not hangs)
✓ Gives downstream time to recover
✓ User gets degraded service (not timeout)
```

### Production Monitoring

```
Metrics to track:
├─ Request latency (p50, p95, p99)
│  └─ Alert if p99 > 500ms
│
├─ Model performance
│  ├─ Watch time per recommendation
│  ├─ CTR (click through rate)
│  └─ Session length
│     └─ Alert if watch-time/rec drops >2%
│
├─ System health
│  ├─ GPU utilization
│  ├─ GPU queue depth
│  ├─ Cache hit rates
│  └─ Redis/DB latency
│
├─ Freshness
│  ├─ Embedding age distribution
│  ├─ Feature staleness (p99 age)
│  └─ Index update latency
│
└─ Errors
   ├─ Feature store timeout rate
   ├─ Ranking service errors
   ├─ FAISS query errors
   └─ Alert if error rate > 0.1%

Dashboards:
- Real-time: latency, errors, traffic
- Daily: watch-time, diversity metrics, costs
- Weekly: model performance trends, user retention

On-call response:
- Page if p99 latency > 500ms (SLA breach)
- Page if watch-time drops >5% (revenue impact)
- Page if error rate > 0.5% (availability)
```

---

## 📈 Phase 7: Scaling Challenges

### Challenge 1: Traffic Increase 100x

**Current:**
- 350K QPS (ranking)
- 100K GPUs
- 1TB embeddings
- 10 datacenters

**Scaled 100x:**
- 35M QPS
- 10M GPUs (impossible!!!)
- 100TB embeddings

**Solution: Optimize, don't brute-force scale**

```
Optimization 1: Model Quantization
├─ Change float32 → int8 (4x compression)
├─ Trade: slight accuracy drop (0.5% watch-time impact)
├─ Benefit: 4x faster inference, 4x less GPU memory
├─ New GPUs needed: 2.5M (vs 10M)

Optimization 2: Batch Optimization
├─ Current: batch size 1000
├─ Increased: batch size 10000
├─ Trade: increased latency (accumulation time)
├─ Benefit: 10x throughput per GPU
├─ New GPUs needed: 250K

Optimization 3: Model Distillation
├─ Train small student model on large teacher model
├─ Student: 1/10 size, 95% accuracy
├─ Inference: 10x faster on CPU (no GPU needed!)
├─ New GPUs needed: 0 (use CPUs instead)
├─ Approach: 
│   - Candidate generation: FAISS (stays same)
│   - Ranking: distilled model on CPU (now viable)

Optimization 4: Approximate Ranking
├─ Don't rank all 1000 candidates
├─ Use simple rules to filter to top 100
├─ Rank only those 100
├─ Trade: quality drop ~2%
├─ Benefit: 10x fewer ranking operations

Result:
Original: 35M QPS * 1000 ranks/req * 10ms/batch = 350M GPU-ms/sec = 10M GPUs
Optimized:
  - Quantization: 2.5M GPUs
  - Batching: 250K GPUs
  - Distillation: Use CPUs (scale easily)
  - Approximate: 1M ranking ops/sec (OK)
```

### Challenge 2: Embedding Retrieval Bottleneck

**Symptom:** Candidate generation becomes latency bottleneck

**Current:** 100ms to retrieve 1000 candidates

**At 35M QPS:** Even parallelizing FAISS becomes slow

**Solution: Hierarchical Retrieval**

```
Two-stage retrieval:

Stage 1: Coarse Retrieval (very fast)
├─ Cluster users into 10K cohorts
├─ For each user: query only relevant cohort's videos
├─ Use simple hash lookup
├─ Latency: <1ms
├─ Returns: 100K candidates

Stage 2: Fine Retrieval (ANN)
├─ Within 100K, find 1000 nearest neighbors
├─ FAISS on smaller index
├─ Latency: <10ms
├─ Returns: 1000 candidates

Total: <11ms (vs 100ms before)

Tradeoff:
- Slight quality loss (miss truly similar videos in other cohorts)
- Mitigated by cross-cohort boosting (small probability)
- Vastly faster
```

### Challenge 3: Vector DB Memory Explosion

**Current:** 2TB embeddings (with compression)
**Challenge:** At 100B videos (new content explosion), need 200TB

**Solution: Hierarchical Embedding Storage**

```
Hot tier (GPU memory):
├─ 100M actively watched videos
├─ 256D embeddings * 100M * 4 = 100GB
├─ Stored on GPUs (access latency: <1ms)

Warm tier (SSD):
├─ 1B videos total
├─ Stored on NVMe (access latency: 10-50ms)
├─ Accessed when needed (cache miss)

Cold tier (Disk):
├─ Archive embeddings
├─ Recomputed on demand

Access pattern:
├─ p95 requests hit hot tier
├─ p99 requests hit warm tier
├─ Very rare requests recompute on-demand

Cost: SSD is 10x cheaper than GPU memory
Latency: Still acceptable (SLAs have room)
```

---

## 🔧 Phase 8: Optimization Strategies

### Optimization 1: Caching Strategy

```
L1 Cache (Memory):
├─ User embeddings (100M users * 4KB) = 400GB
├─ Hot video embeddings (100M videos * 4KB) = 400GB
├─ Cache hit rate: ~90%
├─ TTL: 1 hour (refreshed by streaming)

L2 Cache (Redis):
├─ Ranked results (top 200 videos for user)
├─ Cache hit rate: ~60% (same user scrolling)
├─ TTL: 5 minutes

L3 Cache (CDN):
├─ Static recommendations (trending, category-based)
├─ Cache hit rate: ~80%
├─ TTL: 1 hour

Result:
- Fewer GPU inference calls (L2 cache hits)
- Faster responses (L1 memory access)
- Lower backend load
- Better cost efficiency
```

### Optimization 2: Model Serving

```
Current: Single large model (500MB)

Optimization: Model ensemble
├─ Model A: Small (100MB) - fast, 95% accuracy
├─ Model B: Large (500MB) - slow, 98% accuracy

Serving logic:
├─ For cold-start (unknown user): use Model A (fast)
├─ For warm user (known): use Model B (accurate)
├─ Blend results: 0.8 * ModelA + 0.2 * ModelB

Result:
- 80% of requests use fast model
- Latency reduced
- Quality maintained
```

### Optimization 3: Feature Engineering

```
Problem: Computing features is expensive

Solution: Precompute & cache common features

Precomputed features:
├─ User-video similarity (top 100 videos per user)
├─ User-category interaction (category affinity)
├─ Creator reputation (daily update)
├─ Seasonal trends (hourly update)

At inference time:
├─ Join precomputed features (fast)
├─ Compute only dynamic features (user context)
├─ Total latency: <10ms

Result:
- 50% reduction in feature computation
- Faster ranking
- Better cache locality
```

---

## 🤝 Phase 9: Tradeoff Analysis

### Decision Table 1: Retrieval Method

```
| Method | Latency | Quality | Compute | Use Case |
|--------|---------|---------|---------|----------|
| Collaborative | 30ms | Medium | Low | Engaged users |
| Content-based | 40ms | Medium-High | Medium | Cold start |
| Trending | 5ms | Low | Low | Discovery |
| Hybrid | 50ms | High | Medium | Default |

Choose: Hybrid (default) + fallback to trending if slow
```

### Decision Table 2: Model Architecture

```
| Type | Latency | Quality | Memory | Cost |
|------|---------|---------|--------|------|
| Shallow NN | 5ms | 80% | 100MB | $$ |
| Deep NN | 15ms | 95% | 500MB | $$$ |
| Distilled | 8ms | 92% | 50MB | $$ |
| GBDT | 10ms | 90% | 200MB | $$ |

Choose: Distilled for production (good balance)
```

### Decision Table 3: Storage

```
| Option | Throughput | Consistency | Cost | Complexity |
|--------|-----------|-------------|------|-----------|
| Redis | 1M ops/s | Eventual | $$ | Low |
| Cassandra | 10K ops/s | Eventual | $ | Medium |
| DynamoDB | 100K ops/s | Strong | $$$ | Low |
| HBase | 100K ops/s | Strong | $$ | High |

Choose: Redis for hot tier (speed) + Cassandra for cold (cost)
```

---

## 🔴 Phase 10: Challenging Follow-Ups (Real Interview)

**Interviewer Challenges:**

1. **"Your ranking model takes 15ms. At 35M QPS, that's 525M GPU-ms/sec. Why not 10ms?"**
   - Tradeoff: smaller model → lower quality
   - Quantization helps, but we're already at int8
   - Or: reduce batch size → latency stays same but throughput drops
   - Or: distillation → 8ms possible, slight quality loss
   - My choice: accept 15ms, focus on top-of-funnel (candidate gen)

2. **"What if freshness boost breaks and users only see old videos?"**
   - Monitoring: watch-time per recommendation suddenly drops
   - Within 1 minute: alerts page on-call
   - Fallback: trending videos visible in top 10
   - Rollback: revert freshness boost code
   - Impact: <1M users affected (95% don't notice)

3. **"Your FAISS index has 90% recall. What about the 10% miss?"**
   - Tradeoff: 90% recall = decent coverage + speed
   - 100% recall = ANN becomes exact search = 100ms (too slow)
   - Missing 10% = mainly long-tail content (OK to miss sometimes)
   - Mitigation: supplementary models catch some misses
   - Acceptable given constraints

4. **"Feature store is down for 30 seconds. What happens?"**
   - Ranking uses cached features (1 hour old)
   - Quality degrades slightly
   - Watch-time may decrease 2-3%
   - No error to user (graceful degradation)
   - After 30s: system recovers normally

5. **"Your model drifts and watch-time drops 10%. How fast can you roll back?"**
   - Rollback is automated: <2 minutes
   - During rollback: older model serves traffic
   - Users see older recommendations (slightly worse)
   - After rollback: investigate root cause
   - Retraining: fix bug, retrain in 4 hours

---

## 📚 Key Takeaways

**Architecture:**
- Retrieve 1000s fast (FAISS)
- Rank carefully (deep learning)
- Re-rank for business logic (freshness/diversity)

**ML:**
- Multiple retrieval methods (robustness)
- Collaborative + content-based (complementary)
- Online learning (adaptation)
- Exploration (ecosystem health)

**Production:**
- Monitoring everything (early detection)
- Graceful degradation (user experience)
- Incremental rollout (safety)
- Automated rollback (fast recovery)

**Scaling:**
- Optimize before scaling hardware
- Quantization & distillation (compute efficiency)
- Hierarchical systems (memory efficiency)
- Caching everywhere (latency reduction)

---

## 📝 Questions for Candidate to Answer

1. How would you change this for a non-personalized system (trending videos only)?
2. How does this system work for a new creator with 0 watches?
3. What if you had half the GPU budget - how would you redesign?
4. How would you A/B test a new ranking model?
5. How would you measure diversity objectively?
6. What's the single most important optimization if traffic 10x?

---

*Interview Duration: 3-4 hours for full coverage*
*Difficulty: Google L5 (Staff Engineer level)*
*Last Updated: 2026-05-28*
