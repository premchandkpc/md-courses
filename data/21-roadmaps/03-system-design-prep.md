# 🏗️ System Design Interview Prep — Complete Deep Dive

> **Scope:** A comprehensive, battle-tested preparation guide for system design interviews at FAANG/top-tier companies. Covers the interview format, assessment criteria, the standard framework, common design patterns, database selection guide, consistency-availability tradeoff matrix, and the top 30 questions with difficulty ratings, key patterns, and black belt tradeoffs.

## Table of Contents

- [Interview Format & Timeline](#interview-format--timeline)
- [Assessment Criteria (What Interviewers Measure)](#assessment-criteria-what-interviewers-measure)
- [System Design Framework](#system-design-framework)
- [Common Design Patterns (Reusable Building Blocks)](#common-design-patterns-reusable-building-blocks)
- [Database Selection Guide](#database-selection-guide)
- [Consistency vs Availability Tradeoff Matrix](#consistency-vs-availability-tradeoff-matrix)
- [Top 30 System Design Questions](#top-30-system-design-questions)
- [Black Belt Tradeoffs](#black-belt-tradeoffs)
- [Preparation Strategy](#preparation-strategy)

---

## Interview Format & Timeline

```
High-Level Design (HLD) — 45 minutes
─────────────────────────────────────
 0:00 – 05:00  Clarify requirements, scope, constraints
 5:00 – 15:00  Functional → Non-functional → Core entities → API
15:00 – 30:00  High-level design (whiteboard boxes & arrows)
30:00 – 45:00  Deep dive, tradeoffs, bottlenecks, failure scenarios

Low-Level Design (LLD) — 60 minutes
─────────────────────────────────────
 0:00 – 10:00  Requirements, entities, class diagram
10:00 – 30:00  Detailed design (DB schema, API contracts, protocols)
30:00 – 50:00  Implementation details (concurrency, consistency, edge cases)
50:00 – 60:00  Tradeoffs, follow-ups, scaling

Follow-up Rounds — 30 minutes each
─────────────────────────────────────
  - Capacity estimation drill
  - Failure mode analysis
  - Real-world tradeoff discussion (given a specific constraint)
  - Debugging a production issue in the designed system
```

## Assessment Criteria (What Interviewers Measure)

| Criterion | Weight | What They Look For |
|---|---|---|
| **Architecture** | 25% | Clear structure with logical boundaries, separation of concerns, suitable patterns |
| **Scalability** | 20% | Handles growth in users/data/traffic. Identifies bottlenecks and proposes solutions (sharding, caching, partitioning). |
| **Consistency & Availability** | 15% | Articulates tradeoffs. Chooses appropriate consistency model for the problem. |
| **Communication** | 15% | Structured, clear explanation. Uses diagrams, does not jump ahead. Invites feedback. |
| **Tradeoffs** | 15% | Can articulate why X over Y. Knows the downsides of the chosen approach. Proposes alternatives. |
| **Handling Feedback** | 10% | Incorporates hints. Adjusts design when asked. Doesn't get defensive. |

---

## System Design Framework

```
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                     System Design Framework Flowchart                        │
 └─────────────────────────────────────────────────────────────────────────────┘

 START
   │
   ▼
 ┌──────────────────┐
 │ 1. Requirements   │
 │ - Functional      │
 │ - Non-functional  │
 │ - Constraints     │
 └────────┬─────────┘
          │
          ▼
 ┌──────────────────┐
 │ 2. Core Entities  │
 │ (objects, data)   │
 └────────┬─────────┘
          │
          ▼
 ┌──────────────────┐
 │ 3. API Design     │
 │ (REST / gRPC / WS)│
 └────────┬─────────┘
          │
          ▼
 ┌──────────────────┐
 │ 4. Data Model     │
 │ (DB choice, schema)│
 └────────┬─────────┘
          │
          ▼
 ┌──────────────────┐
 │ 5. High-Level     │
 │    Design         │
 │ (boxes & arrows)  │
 └────────┬─────────┘
          │
          ▼
 ┌──────────────────┐
 │ 6. Deep Dive      │
 │ (key component)   │
 └────────┬─────────┘
          │
          ▼
 ┌──────────────────┐
 │ 7. Tradeoffs      │
 │ (pros/cons/downs) │
 └────────┬─────────┘
          │
          ▼
 ┌──────────────────┐
 │ 8. Scaling        │
 │ (10x, 100x, 1000x)│
 └────────┬─────────┘
          │
          ▼
 ┌──────────────────┐
 │ 9. Failure        │
 │    Analysis       │
 └────────┬─────────┘
          │
          ▼
       REPEAT / DEEPEN
```

### Step-by-Step Breakdown

**1. Requirements — 5 min**
- Functional: "What should the system do?" (e.g., upload photo, generate short URL, send message)
- Non-functional: "What properties?" (e.g., latency p99 < 200ms, 99.99% uptime, support 1B users)
- Constraints: DAU, peak QPS, storage estimate, data retention

**2. Core Entities — 2 min**
- Identify 3–6 key objects (User, Tweet, URL, Order, Video, etc.)
- Define their relationships

**3. API Design — 3 min**
- REST endpoints: POST /shorten, GET /{shortCode}
- Request/response schemas
- For data-heavy systems, discuss batch APIs

**4. Data Model — 5 min**
- Schema for core entities (denormalized or normalized?)
- Database selection (SQL vs NoSQL vs NewSQL)
- Index strategy

**5. High-Level Design — 15 min**
- Draw boxes (Client, LB, API Gateway, Service, DB, Cache, Queue, CDN)
- Draw arrows with protocol (HTTP, gRPC, WebSocket, Kafka)
- Data flow for a primary request

**6. Deep Dive — 10 min**
- Pick the most interesting or bottleneck component
- Zoom in: cache internals, database sharding, leader election, rate limiting algorithm

**7. Tradeoffs — 3 min**
- "Why did you choose SQL over NoSQL?"
- "What happens if our cache layer goes down?"
- "What's the consistency vs latency tradeoff in your design?"

**8. Scaling — 3 min**
- 10x traffic → what breaks first? (DB, cache hit ratio, network bandwidth, LB capacity)
- 100x → what architecture changes needed? (sharding, multi-region, CDN)
- 1000x → what fundamentally changes? (geo-distribution, eventual consistency, async everything)

**9. Failure Analysis — 2 min**
- Single component failure → what happens?
- Cascading failure → how to prevent? (circuit breaker, bulkhead, rate limiting)
- Data loss → durability guarantees?

---

## Common Design Patterns (Reusable Building Blocks)

| Pattern | Use When | Example |
|---|---|---|
| **Consistent Hashing** | Need to add/remove cache nodes with minimal rehashing | Memcached, Cassandra |
| **Read Replicas** | Read-heavy workload, eventual consistency acceptable | Instagram posts, blog |
| **CDN** | Global users, static or cacheable content | Netflix, YouTube, images |
| **Async Processing / Queue** | Slow operation doesn't need sync response | Email sending, video transcoding |
| **Sharding** | Data won't fit on single node, write throughput exceeds a single node | WhatsApp messages, Uber trips |
| **Caching (multi-tier)** | Hot data, reduce DB load, reduce latency | L1 (local LRU) → L2 (Redis) → DB |
| **Idempotency** | At-least-once delivery, network retry, duplicate requests are possible | Payment processing |
| **Rate Limiting** | Protect system from abuse, fair usage, cost control | API gateway (token bucket, sliding window) |
| **Circuit Breaker** | Protect system from cascading failure when dependency is slow/failing | Service mesh, Resilience4j |
| **Leader Election** | Need one node to act as coordinator, schedule tasks | Raft, ZooKeeper, etcd |
| **Load Balancing** | Distribute traffic across multiple servers | L4 (TCP), L7 (HTTP), DNS-based, Geo-LB |
| **Microservices** | Large team, independent deploy, polyglot, bounded contexts | Uber, Netflix, Amazon |
| **Event-Driven** | Decouple producers and consumers, async, extensible | Kafka, SQS, EventBridge |
| **CQRS** | Different read/write models, read performance optimized separately | Reporting, analytics |
| **Saga** | Distributed transaction across services without 2PC | Order → Payment → Inventory |
| **Bloom Filter** | Probabilistic membership check, cache stampede prevention | Caching layer (is key in DB?), web crawler URL dedup |
| **Merkle Tree** | Compare large datasets across nodes, detect inconsistency | Cassandra anti-entropy, Git, Bitcoin |
| **Gossip Protocol** | Decentralized failure detection, metadata dissemination | Cassandra, Redis Cluster, Consul |
| **Quorum** | Tune consistency vs latency with N, W, R | Dynamo-style storage |

---

## Database Selection Guide

```
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │                     DATABASE SELECTION DECISION TREE                         │
 └──────────────────────────────────────────────────────────────────────────────┘

 Do you need ACID transactions?
 ├── YES ──> Are you read-heavy? Scale reads via replicas?
 │             ├── YES ──> PostgreSQL / MySQL + read replicas
 │             └── NO  ──> Is latency critical?
 │                           ├── YES ──> Single-region SQL + caching tier
 │                           └── NO  ──> Distributed SQL (CockroachDB, TiDB)
 │
 └── NO ──> What is the data model?
              ├── Document (JSON, nested) ──> MongoDB, Couchbase
              ├── Key-Value ──> Redis (cache), DynamoDB, FoundationDB
              ├── Wide-Column ──> Cassandra, ScyllaDB, HBase
              ├── Graph ──> Neo4j, Amazon Neptune, Dgraph
              ├── Time-Series ──> InfluxDB, TimescaleDB, ClickHouse
              └── Search / Full-text ──> Elasticsearch, Meilisearch, Algolia
```

### Database Comparison Table

| Feature | PostgreSQL | MongoDB | Cassandra | Redis | CockroachDB | DynamoDB |
|---|---|---|---|---|---|---|
| Data Model | Relational | Document | Wide-column | KV + data structs | Relational | KV + Document |
| Consistency | Strong | Tunable | Eventual / Tunable | Strong (single node) | Strong (Serializable) | Eventual / Strong |
| Partitioning | Manual (sharding) | Hash-based | Consistent Hashing | Hash Slots | Auto range-split | Auto hash |
| Replication | Leader + replicas | Replica set | Peer-to-peer | Leader + replicas | Multi-active Raft | Multi-region |
| Transactions | ACID | Multi-doc ACID | Lightweight | MULTI/EXEC | Serializable | TransactGet |
| Query | SQL | MQL | CQL | Commands | SQL | PartiQL / API |
| Best for | General purpose | Rapid prototyping | Write-heavy, multi-DC | Caching, real-time | Geo-distributed SQL | Serverless KV |

---

## Consistency vs Availability Tradeoff Matrix

```
       AVAILABILITY
       HIGH <─────────────────────────────> LOW
         │                                      │
         │  AP Systems           │    CP Systems │
   HIGH  │  Cassandra            │    Spanner    │
         │  DynamoDB             │    etcd       │
         │  Riak                 │    ZooKeeper  │
   C      │  CouchDB              │    HBase      │
   O      │                       │               │
   N      │  [DNS, CDN,          │    [Leader     │
   S      │   Shopping cart,     │     election,  │
   I      │   Social feed]       │     meta-      │
   S      │                       │     data]     │
   T      │                       │               │
   E      ├───────────────────────┼───────────────┤
   N      │  Highly Available    │  Strict        │
   C      │  but may miss writes │  Consistency   │
   Y      │  Example: Cassandra  │  but may be    │
         │  W=1 R=1 Quorum      │  unavailable   │
   LOW   │  Quick responses      │  Example:      │
         │                       │  Spanner /     │
         │  "Eventual"           │  ZK / etcd     │
         │                       │                │
         │                       │  "Serializable"│
         └───────────────────────────────────────┘
```

### PACELC Distribution

| System | P → A/C | E → L/C | Notes |
|---|---|---|---|
| Cassandra | **A** (AP) | **L** (low latency, eventual) | W=1, R=1 |
| Spanner | **C** (CP) | **C** (strong, 2ε wait) | Serializable, high latency cross-region |
| DynamoDB | **A** (AP) | **L** (eventual default) | Strong consistent reads cost 2x |
| etcd | **C** (CP) | **C** (linearizable) | Core to Kubernetes |
| CockroachDB | **C** (CP) | **C** (serializable) | Leaseholder reads fast, writes at quorum latency |
| Redis | **C** (no partition) | **L** (fast, async) | Cluster mode sacrifices strong consistency |

---

## Top 30 System Design Questions

```
Difficulty Key:  ★★★★☆ Easy | ★★★★☆ Medium | ★★★★★ Hard | ★★★★★ Expert
```

| # | Question | Difficulty | Key Patterns |
|---|---|---|---|
| 1 | **Design URL Shortener (TinyURL)** | ★★★☆☆ | Hashing (base62, MD5, birthday problem), redirection (301 vs 302), NoSQL KV, idempotent creation, custom slug, analytics tracking, bloom filter for spam |
| 2 | **Design WhatsApp** | ★★★★★ | WebSocket long-lived connection, chat sharding (by chat_id hash), presence (heartbeat + disco), E2E encryption, media CDN, offline message store, last-seen |
| 3 | **Design Twitter** | ★★★★★ | Fan-out on write (pre-compute timeline for active users) vs fan-out on read (pull for celebrities), tweet ID (Snowflake), newsfeed ranking, timeline caching, social graph storage |
| 4 | **Design Uber** | ★★★★★ | Geohashing (quadtree for geo-indexing), state machine (idle → looking → assigned → picked_up → in_trip → completed), real-time location streaming via WebSocket, surge pricing, ETA prediction, geo-fencing |
| 5 | **Design YouTube** | ★★★★★ | Video upload pipeline (transcoding, thumbnails, chunked upload), CDN distribution (MPEG-DASH, HLS), stream protocol (adaptive bitrate), recommendation engine, comments, views counter (eventual + exact) |
| 6 | **Design Netflix** | ★★★★★ | CDN-first (Open Connect appliances at ISP), stateless client + stateful manifest, DRM, encoding pipeline, recommendation via matrix factorization + deep learning, A/B testing at scale |
| 7 | **Design Instagram** | ★★★★☆ | Photo storage (CDN: image resizing, WebP, AVIF), feed generation (fan-out with rank), stories (ephemeral, per-user TTL), hashtag index, direct messaging, real-time notifications |
| 8 | **Design Dropbox** | ★★★★☆ | File sync protocol (delta sync, block-level dedup, CouchDB-style merge), conflict resolution (CRDT or LWW + manual), chunk storage (S3/GCS), metadata DB (SQL), LAN sync, versioning |
| 9 | **Design Google Drive** | ★★★★☆ | Similar to Dropbox + real-time collaboration (CRDT/OT), document revision history, workspace integration, sharing permissions model, team drives, offline sync |
| 10 | **Design Amazon (e-commerce)** | ★★★★★ | Product catalog (sharded + denormalized), shopping cart (in-memory + persist), order management (saga: payment → inventory → shipping), inventory (real-time count, cache + DB), payment (idempotency, PCI DSS), recommendation engine |
| 11 | **Design Facebook Newsfeed** | ★★★★★ | Feed generation (fan-out: push for active friends, pull for pages), ranking (ML features: affinity, recency, content type), ads insertion, real-time updates via WebSocket, A/B experiment platform |
| 12 | **Design Google Maps** | ★★★★★ | Geo-indexing (quadtree, S2 geometry, H3), routing (Dijkstra/A* on road graph with traffic weights), real-time traffic, reverse geocoding, offline maps, tile rendering, navigation (voice + lane assist) |
| 13 | **Design Web Crawler** | ★★★★★ | URL frontier (politeness per domain, priority), deduplication (bloom filter + Merkle tree), content extraction (HTML parsing, text extraction), crawl schedule, robots.txt compliance, rate limiting per domain |
| 14 | **Design Chat System** | ★★★★☆ | WebSocket persistent connection (presence, typing indicator, read receipts), message storage (sharded by conversation_id + time), media upload, group chat (N² fan-out for small groups, single copy for large groups) |
| 15 | **Design Key-Value Store** | ★★★★☆ | SSTables + LSM-tree (write-optimized), Memtable → Flush → Compaction, bloom filters for point reads, consistent hashing, quorum replication, anti-entropy with Merkle trees, hinted handoff |
| 16 | **Design Distributed Cache** | ★★★☆☆ | Consistent hashing, LRU/LFU/2Q eviction, TTL, replication (sentinel/cluster), hot key mitigation (local cache + jitter), connection pooling, serialization (Protocol Buffers) |
| 17 | **Design Rate Limiter** | ★★★☆☆ | Token Bucket (burst), Leaky Bucket (smooth), Sliding Window Log (precise), Sliding Window Counter (memory efficient), Fixed Window (edge case at boundary). Distributed: Redis sorted sets, CAS with Lua scripts |
| 18 | **Design Distributed ID Generator** | ★★★☆☆ | Snowflake (timestamp + worker + seq), Leaf (segment + double-buffer), UUIDv7 (timestamp + random), Instagram-style (range allocation in SQL), Baidu UidGenerator |
| 19 | **Design Distributed Locking Service** | ★★★★☆ | Lease (TTL), fencing tokens, Redlock debate (Martin Kleppmann vs Antirez), ZooKeeper lock (sequential ephemeral znodes), etcd concurrency API, deadlock detection |
| 20 | **Design Distributed Queue (Kafka)** | ★★★★★ | Topics + partitions + consumer groups, offset management, exactly-once semantics (transactional producer, idempotent producer + consumer), log compaction, partition rebalance (cooperative sticky), KRaft (no ZooKeeper) |
| 21 | **Design Notification System** | ★★★★☆ | Push (APNs, FCM), email (SES/SendGrid), SMS (Twilio), in-app (WebSocket). Queue per type, delivery retry with backoff, deduplication, user preferences, rate limiting, template engine, analytics |
| 22 | **Design Payment System (Stripe)** | ★★★★★ | Idempotency key, 2-phase commit / Saga (authorize → capture → settle), double-entry ledger (debit/credit never balance, always sum to zero), settlement with card networks, fraud detection (ML), 3DS, reconciliation, audit log |
| 23 | **Design Ticketmaster** | ★★★★★ | Queue-it (virtual waiting room), seat inventory (distributed transaction challenge: two people buying same seat), optimistic locking at seat level, release held seats on timeout, real-time seat map via WebSocket |
| 24 | **Design Hotel Booking** | ★★★★☆ | Room inventory (overbooking tradeoff), rate calculation (dynamic pricing by season/demand), cancellation, refund policies, search by location + dates, availability cache |
| 25 | **Design Uber Eats** | ★★★★☆ | Courier assignment (nearest, multi-factor optimization), order matching (dispatch engine), real-time tracking (WebSocket), ETA prediction, schedule management (restaurant prep time + driver pickup), surge pricing |
| 26 | **Design Slack** | ★★★★★ | Real-time messaging (WebSocket), workspace → channel → thread hierarchy, search (Elasticsearch), file sharing, integrations (webhooks, slash commands), presence, typing indicators, read receipts |
| 27 | **Design Zoom** | ★★★★★ | Video/audio encoding (codec selection: H.264, VP9, AV1), SFU architecture (selective forwarding unit — no mixing, just forward streams), simulcast (multiple resolution streams), adaptive bitrate, WebRTC, breakout rooms, recording |
| 28 | **Design GitHub** | ★★★★★ | Repository storage (git packfiles on S3, metadata in SQL), PR flow (merge conflict detection via merge-base + 3-way merge), code review system (comments, inline, review threads), CI/CD integration (actions runner), issue tracking |
| 29 | **Design Search Autocomplete** | ★★★☆☆ | Trie (prefix tree), top-K completion (frequency + recency), frontend-side cache (debounce + local trie), personalization, trending queries, data freshness (MRU vs batch update), sharding by prefix |
| 30 | **Design Web Search Engine (Google)** | ★★★★☆ | Crawl → Index → Rank → Serve. Crawling (URL frontier, politeness, dedup), Index (inverted index, position, TF-IDF), Ranking (PageRank, BM25, learning-to-rank with neural signals), Query understanding (spelling correction, synonyms, entity recognition) |

---

## Black Belt Tradeoffs

These deep tradeoff questions separate Senior from Staff-level candidates:

| Tradeoff | What to Discuss |
|---|---|
| **Consistency vs Latency** | Tunable consistency (MongoDB, Cassandra): how many replicas to block on write? Strong consistency adds 1 RTT. When is it worth it? |
| **Cache vs DB for source of truth** | Cache-aside: cache miss → read DB → populate cache. What if cache and DB are inconsistent? TTL vs invalidation. |
| **Synchronous vs Asynchronous Processing** | Sync: simple, request-scoped. Async: decoupled, but need idempotency and handling eventual consistency. |
| **Push vs Pull for event delivery** | Push (low latency, hard to buffer). Pull (higher latency, easier to batch and retry). WebSocket vs polling vs long polling. |
| **SQL vs NoSQL for a given workload** | SQL: joins, ACID, schema evolution (migrations). NoSQL: auto-sharding, flexible schema, high write throughput. |
| **Stateful vs Stateless design** | Stateless: easier to scale (add more instances). Stateful: required for performance (session affinity, in-memory cache). Trade: externalize state to Redis/Memcached. |
| **Strong consistency vs High availability during partition** | CP: etcd, HBase, Spanner. AP: Cassandra, DynamoDB. Which one is correct for your use case? |
| **Eventual consistency acceptance criteria** | Define acceptable staleness window (Amazon: < 1 sec p99 DynamoDB). How does the application handle stale reads? |
| **Data locality vs Data distribution** | Colocate computation with data for performance (Hadoop, Spark data locality). Distribute data across regions for disaster recovery. |

---

## Preparation Strategy

### Timeline: 8–12 weeks

```
Week 1-2:  Learn the framework. Practice 5 easy questions (rate limiter, URL shortener, KV store, cache, ID generator)
Week 3-4:  Learn patterns (consistent hashing, bloom filter, gossip, quorum). Practice 5 medium questions
Week 5-6:  Deep dive on databases, consistency, replication. Practice 5 hard questions (WhatsApp, Uber, Twitter, Netflix, YouTube)
Week 7-8:  System design mock interviews (2x/week). Practice remaining hard questions
Week 9-10:  Expert-level designs (payment, search engine, GitHub, Zoom, Ticketmaster). Failure mode analysis
Week 11-12: Mock interviews with FAANG engineers. Capacity estimation drills. Tradeoff discussions
```

### Key Resources

| Resource | Purpose |
|---|---|
| *System Design Interview* (Vol 1 & 2) — Alex Xu | Framework + question walkthroughs |
| *Designing Data-Intensive Applications* | Deep distributed systems theory |
| *The System Design Primer* (GitHub) | Free, excellent patterns reference |
| *High Scalability* blog | Real-world architecture breakdowns |
| *InfoQ / Tech at Scale* | Engineering blogs from FAANG |
| Pramp / Interviewing.io | Mock interviews |
| *USENIX / SOSP / OSDI / NSDI* papers | Deep-dive on any component |

---

> **Next step:** Start with the [System Design Framework](#system-design-framework), practice [Question 1: URL Shortener](#top-30-system-design-questions) using the full 9-step process, then progressively work through the remaining 29 questions ranked by difficulty.
