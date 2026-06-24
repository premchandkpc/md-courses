---
title: Requirements & Capacity Estimation
topic: 15-system-design
difficulty: advanced
time: 45m
paths:
  - system-design
  - staff
  - interview-method
---

# Requirements & Capacity Estimation — How to Start Any Design Interview

## 1. The First 5 Minutes of Every Design Interview

Most candidates fail in the first 5 minutes. Not because they don't know the tech, but because they **jump to a diagram** before understanding what they're building.

### The Opening Script

**Interviewer:** "Design Twitter."

**Bad candidate:** Draws boxes (load balancer → API → DB → cache) in 30 seconds. Explains sharding. Gets anxious when interviewer adds constraints they didn't ask about.

**Good candidate:**

```
1. "Let me clarify what we're building."
2. "Let me scope the requirements."
3. "Let me estimate the scale."
4. "Now let me walk through a design."
```

That's it. The first 3 steps are **diagram-free**. No boxes, no arrows, no DB choices. Just conversation.

### Requirements Clarification Framework

Ask these in order:

| Layer | Question | Why |
|-------|----------|-----|
| Function | "Who's the user? What's the primary action?" | Prevents building for wrong persona |
| Scope | "MVP or full-featured? What's in/out?" | Prevents scope creep during interview |
| Scale | "How many users? Read/write ratio?" | Drives every architectural choice |
| Constraints | "Any latency, availability, or cost constraints?" | Surface hidden NFRs |
| Platform | "Web? Mobile? Both? Global or single region?" | Affects API design, CDN, geo |

### Real Example — URL Shortener

```
Candidate: "Let me clarify. Is this a public URL shortener like bit.ly,
            or an internal link resolver for a company?"

Interviewer: "Public, like bit.ly."

Candidate: "OK. MVP features — create short URL, redirect to long URL,
            track clicks? Anything else?"

Interviewer: "That's enough for now."

Candidate: "What scale should I design for?"

Interviewer: "100M URLs created per month. 1B redirects per month."

Candidate: "Any latency requirements?"

Interviewer: "Redirects should feel instant — under 100ms."

Candidate: "Global audience or US-only?"

Interviewer: "Global."
```

Now, and only now, do you know:
- **Write-heavy on creation** (100M/month)
- **Read-heavy redirects** (10:1 read:write)
- **Latency-sensitive** (<100ms)
- **Global** (need multi-region or CDN)

This 2-minute conversation **saves 20 minutes of wrong design**.

---

## 2. Functional Requirements

Functional requirements answer: **"What does the system do?"**

### How to Extract Them

Don't list every feature. Categorize:

```
Core (MVP must have):
  ├─ User can create a short URL
  ├─ User can visit a short URL and get redirected
  └─ User can see click count

Nice-to-have (Phase 2):
  ├─ Custom short URLs (bit.ly/my-link)
  ├─ QR code generation
  └─ Analytics dashboard

Out of scope (explicitly):
  ├─ User accounts / login
  └─ A/B testing URLs
```

### Prioritization Heuristic

In an interview, the interviewer is watching:
- Can you **separate essential from nice-to-have**?
- Do you **explicitly call out what's out of scope**?
- Do you **anchor every choice to a requirement**?

If you say "we need Kafka" and the interviewer asks "for what requirement?", you should have an answer.

### Common Functional Requirement Patterns by System Type

| System Type | Core CRUD | Async/Event | Real-time |
|-------------|-----------|-------------|-----------|
| URL shortener | Create URL, Read URL | Click event | — |
| Chat | Send msg, Read history | New msg notification | WebSocket delivery |
| Payment | Create payment, Read status | Settlement event | Fraud check |
| Feed | Write post, Read feed | Fan-out | Push notification |
| Video | Upload, Stream | Transcode | Live streaming |

### Staff+ Level: Functional Boundaries

At staff level, you're expected to think about **service boundaries** during requirements:

```
Single service (fine for MVP):
  URL Shortener Service
  ├─ POST /shorten
  ├─ GET /{short_code}
  └─ GET /{short_code}/stats

Eventually separate:
  ┌──────────────────────┐
  │ Redirect Service     │  ← needs to be fast, simple
  │ - GET /{short_code}  │     can cache aggressively
  │ - returns 302        │
  └──────────────────────┘
  ┌──────────────────────┐
  │ Creation Service     │  ← needs uniqueness check
  │ - POST /shorten      │     can be slower
  │ - validates URL      │
  └──────────────────────┘
  ┌──────────────────────┐
  │ Analytics Service    │  ← async, batch writes
  │ - ingests click      │     can use different DB
  │ - aggregates stats   │
  └──────────────────────┘
```

Mention this at staff level: "I'd start monolithic, but I can already see the split points."

---

## 3. Non-Functional Requirements

NFRs answer: **"How well does it perform?"**

### The Five NFRs That Matter in Every Interview

| NFR | How to Ask | What It Drives |
|-----|-----------|----------------|
| **Availability** | "What uptime do we need?" | Replication, failover, multi-region |
| **Latency** | "What's acceptable p95/p99?" | Caching, CDN, async paths, data locality |
| **Durability** | "Can we lose data on crash?" | Replication factor, backup, WAL |
| **Consistency** | "Can users see stale data?" | Read replica vs leader read, quorum |
| **Scale** | "How many users/requests/events?" | Sharding, partitioning, queue depth |

### Availability (Nines)

```
99%    → 3.65 days downtime/year   → no SLA, internal tools
99.9%  → 8.76 hours/year           → typical SaaS (Zendesk, Shopify basic)
99.99% → 52.56 minutes/year        → premium (Stripe, AWS)
99.999% → 5.26 minutes/year        → telecom, real-time trading
```

**Interview tip:** Never say "five nines" unless asked. It adds cost, complexity, and most systems don't need it.

### Latency Budgets

A request often crosses 3-10 services. Budget latency at each hop:

```
Total budget: 200ms (p99)

Breakdown:
  Client → LB: 10ms
  LB → API Gateway: 5ms
  Auth check: 10ms
  API → Cache: 5ms  (cache hit)
  Cache → API: 5ms
  API → DB (if miss): 30ms
  DB → API: 30ms
  API response serialization: 5ms
  Response to client: 10ms
  Buffer/unexpected: 90ms
                        ─────
  Total:                  200ms
```

Staff+ angle: "I'd set up latency budgets during requirements, not after deployment."

### Consistency Requirements (the one everyone gets wrong)

| Requirement | What to Say | Architecture Impact |
|-------------|-------------|-------------------|
| Strong consistency | "User must see their own write immediately" | Read from leader, quorum writes |
| Eventual consistency | "It's OK if replicas lag a few seconds" | Read from any replica |
| Read-your-writes | "User should see their data, others can wait" | Route user to leader, others to replicas |
| Monotonic reads | "User shouldn't see data disappear" | Consistent hash to same replica |

### Real NFR Table Example — Payment System

```
Functional: Process payment, update balance, send receipt

NFRs:
  Availability: 99.99% (Stripe baseline)
  Latency: <500ms at p99 for payment, <50ms at p99 for balance read
  Durability: Zero data loss (no acknowledged writes lost)
  Consistency: Strong for balance, eventual for receipts
  Scale: 1000 TPS average, 5000 TPS peak
```

---

## 4. Capacity Estimation

### The Formulas You Actually Need

#### DAU → QPS

```
DAU = Total users × % active daily
QPS = DAU × avg actions per user per day / 86400
Peak QPS = Avg QPS × 2-5× (traffic spike factor)
```

#### Storage

```
Storage per day = QPS_write × avg record size × 86400
Storage per year = per day × 365 × replication factor
```

#### Bandwidth

```
Bandwidth (bps) = QPS × avg response size × 8
```

#### Memory for Cache

```
Cache size = (QPS_read × record size × TTL) × hit ratio buffer
```

### Worked Example — Twitter Timeline

Step 1: Clarify scale

```
Users: 500M MAU → 200M DAU
Actions: User reads timeline 10×/day, tweets 2×/day
Reads: 200M × 10 = 2B timeline reads/day
Writes: 200M × 2 = 400M tweets/day
Ratio: 5:1 read:write
```

Step 2: Calculate QPS

```
Avg read QPS = 2B / 86400 ≈ 23,000 QPS
Peak read QPS = 23,000 × 3 = 69,000 QPS
Avg write QPS = 400M / 86400 ≈ 4,600 QPS
Peak write QPS = 4,600 × 3 = 13,800 QPS
```

Step 3: Storage

```
Tweet size: ~1KB (280 chars + metadata + media URL)
Media stored separately in object store
Storage per day: 400M × 1KB = 400GB/day
Storage per year: 400GB × 365 = 146TB/year
With 3× replication: ~440TB/year
```

Step 4: Memory for timeline cache (fan-out approach)

```
Timeline: 500 most recent tweet IDs per user
500 IDs × 8 bytes = 4KB per user
200M DAU: 200M × 4KB = 800GB
Add overhead: ~1TB of Redis
```

### Rules of Thumb (Sanity Check Everything)

```
DB write throughput:
  Single Postgres node: ~1K-5K writes/sec
  Single MySQL node: ~1K-5K writes/sec
  Cassandra: ~10K-100K writes/sec per node
  Kafka: ~100K-1M writes/sec per partition

DB read throughput:
  Single Postgres: ~5K-50K reads/sec (depends on index/cache)
  Redis single node: ~100K ops/sec

Network:
  1 Gbps ≈ 125 MB/s
  Cross-region latency: 50-200ms
  Same-region latency: <1ms

Storage:
  1M records of 1KB each ≈ 1GB
  SSD sequential read: ~500 MB/s
  HDD sequential read: ~100 MB/s
```

### Cost Estimation (Staff+ Level)

Interviewers rarely ask for dollar figures. But when they do:

```
AWS-like pricing (approximate, per month):
  EC2 m5.large (2 vCPU, 8GB): ~$70
  RDS db.r5.large (2 vCPU, 16GB): ~$200
  Redis cache.r5.large (13GB): ~$200
  S3: ~$23/TB (standard)
  Data transfer: ~$0.09/GB (out to internet)
```

**Staff+ angle:** "This design would cost roughly $X/month at our scale. We could reduce it by Y by [using spot/precomitting/cold storage]."

---

## 5. Production Angle: Java / Go / Python

### How Requirements Drive Runtime Choices

```
Latency requirement <10ms:
  → Go or Java (pre-warmed, JIT-compiled)
  → NOT Python (unless trivial)

CPU-bound computation (image processing, ML inference):
  → Go goroutines or Java virtual threads
  → Python with native extensions (numpy, onnx) but careful with GIL

IO-bound (DB queries, API calls):
  → Java CompletableFuture or Go goroutines
  → Python asyncio (single-threaded but cooperative)

Throughput requirement >100K QPS:
  → Java Netty or Go net/http (zero-copy, epoll/kqueue)
  → Python needs uvicorn/gunicorn with workers, but heavy GC at scale
```

### Capacity Estimation → Code Configuration

#### Java — Thread Pool Sizing

```java
// Requirements: 10K QPS, avg latency 50ms, 4 cores per instance
// Formula: threads = QPS × latency_seconds / cores
// threads = 10,000 × 0.05 / 4 = 125 threads

// But you also check queue depth:
// Queue = QPS × acceptable_queue_delay
// For 100ms acceptable delay: 10,000 × 0.1 = 1000

ExecutorService pool = new ThreadPoolExecutor(
    125,                    // corePoolSize
    125,                    // maxPoolSize
    60L, TimeUnit.SECONDS,
    new LinkedBlockingQueue<>(1000),  // queue depth from above
    new ThreadPoolExecutor.CallerRunsPolicy()  // backpressure
);

// Staff+ check: Calculate rejection probability
// Erlang-C or Little's Law: if avg latency > acceptable, queue grows unbounded
// Monitor pool queue depth as an SLO metric
```

#### Go — Goroutine Consideration

```go
// Go handles this differently — goroutines are cheap, but channels need sizing
// Requirements: 10K QPS, each request 3 downstream calls

// Fan-out pattern: each request spawns 3 goroutines
// Peak goroutines = 10,000 × 3 = 30,000 goroutines
// Go can handle 30K goroutines easily (~2GB memory overhead at ~64KB each)

// But: bounded concurrency for DB calls to prevent thundering herd
sem := make(chan struct{}, 100) // max 100 concurrent DB calls

for req := range requests {
    go func(r Request) {
        sem <- struct{}{}
        defer func() { <-sem }()
        // make DB call
    }(req)
}

// Capacity estimation insight:
// 100 concurrent DB calls × 50ms avg latency = 5K ops/instance
// Need 2 instances to handle 10K QPS
// This is the same math as Java, expressed differently
```

#### Python — GIL-Aware Capacity Planning

```python
# Requirements: 5K QPS, mostly IO-bound (API calls + DB)
# Python GIL blocks CPU-bound work across threads
# Solution: multiprocessing + asyncio

# asyncio: good for IO-bound, single-threaded cooperative
# 5K QPS / 1000 concurrent connections = 5 requests per connection
# Need async drivers for every downstream call

import asyncio
import aiohttp

async def handle_request(session, request):
    async with session.get(f"http://db-api/{request.id}") as resp:
        data = await resp.json()
    # process
    return data

# But: if any computation takes >10ms, GIL blocks everything
# Solution: offload CPU work to worker processes
from concurrent.futures import ProcessPoolExecutor

cpu_pool = ProcessPoolExecutor(max_workers=4)

async def handle_compute(data):
    loop = asyncio.get_event_loop()
    # offload CPU-bound transform to separate process
    result = await loop.run_in_executor(cpu_pool, heavy_transform, data)
    return result

# Capacity insight:
# 1 asyncio worker process + 4 CPU workers = ~5K QPS on 6 cores
# Python needs ~2× the instances of Go/Java for same throughput
# Factor this into cost estimation
```

### Common Capacity Mistakes in Production

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Estimating QPS from DAU without peak factor | Everything works at 2AM, falls over at 10AM | Measure actual peak/avg ratio (often 3-5×) |
| Ignoring GC pauses in latency budget | p99 good, p99.9 spikes every GC cycle | Size heap, use low-pause GC (ZGC, Go 1.22+) |
| Not accounting for connection pool limits | DB CPU at 20% but app gets timeout errors | Pool: connections = QPS × latency / concurrency |
| Cache TTL too aggressive | Cache miss storm every N minutes | Add jitter to TTLs, stagger expiry |

---

## 6. JPMC / Top-Company Interview Angle

### What JPMC Looks For in System Design

JPMC system design interviews are **not** "design WhatsApp." They're closer to:

- "Design a payment settlement system"
- "Design a trade reconciliation pipeline"
- "Design a customer account aggregation service"
- "Design a fraud detection pipeline"

The difference: **correctness and auditability matter more than latency and scale.**

### JPMC-Specific NFR Priorities

```
1. Correctness (immutable audit log, no data loss)
2. Compliance (regulatory requirements, data retention)
3. Consistency (money must reconcile)
4. Availability (transactions during market hours)
5. Latency (less critical — nightly batch is fine for many flows)
```

### JPMC Requirements Example — Payment Settlement

```
Functional:
  - Process incoming payment instructions
  - Match payments to invoices/obligations
  - Generate settlement instructions
  - Produce audit trail (immutable)
  - Support reconciliation (what settled vs what should have)

NFRs:
  - Zero data loss (durable writes before ack)
  - Immutable event log (no UPDATE, only INSERT + snapshot)
  - Audit retention: 7 years (regulatory)
  - Availability: 99.95% during market hours (6 days × 22 hours)
  - Consistency: Strong within ledger, eventual for reporting
  - Scale: 5M transactions/day (modest), 10K peak TPS (bursty)
  - Latency: <1s for single payment, <5min for batch settlement
```

Capacity estimation for this:

```
5M txns/day → 57 TPS average → 500 TPS peak (10× batch burst)
Each txn: ~2KB (payment details + metadata)
Storage: 5M × 2KB × 7 years × 3× replication = ~75TB
Archive after 90 days to cold storage for compliance retention
```

### What FAANG Looks For

| Company | Emphasis | Example Question |
|---------|----------|-----------------|
| Google | Scale, latency, global | "Design YouTube" |
| Meta | Consistency vs availability tradeoffs | "Design Facebook Feed" |
| Amazon | Cost, operational simplicity | "Design a shopping cart" |
| Stripe | Correctness, idempotency, API design | "Design a payment API" |
| Uber | Real-time, geo-distributed | "Design ride matching" |
| Netflix | Resilience, multi-region | "Design a recommendation API" |

### The Meta-Reqs Question

At senior+ levels, every interviewer asks some version of:

> "If you had to drop one requirement, which one and why?"

This tests whether you understand tradeoffs. Good answers:

- "Drop analytics. Redirect is the core path, analytics can be sampled."
- "Drop custom URLs. Auto-generated is fine for MVP, custom adds ID collision complexity."
- "Drop 99.99% availability. 99.9% saves us 3× infra cost and 80% operational complexity."

---

## 7. Failure Cases and Tradeoffs

### Failure: Estimation Without Validation

```
Situation: Estimated 10K QPS based on DAU × actions
Reality: Launch campaign drives 100K QPS (10× estimate)
Result: DB falls over, site down for 4 hours

Fix: Always plan for 2-5× headroom.
     Autoscaling + queue to absorb spikes.
     Measure actual traffic patterns post-launch.
```

### Failure: Over-Engineering Based on Wrong Estimate

```
Situation: "We need 99.999% availability!" (asked by architect)
          Designed multi-region active-active with 5× replication
Reality: Internal tool. Users OK with 5 minutes downtime/week.
Result: Wasted $2M/year on infrastructure nobody needed.

Fix: Match NFRs to business need, not aspirational numbers.
     "Five nines costs 10× more than four nines. Is it worth it?"
```

### Failure: Ignoring Peak Traffic

```
Situation: Estimated QPS from daily average (100M req / 86400 = 1157)
Reality: Traffic is bursty. Peak hour = 5000 QPS. Flash crowd = 15K QPS.
Result: System works during "testing" but fails in production.

Fix: Use P95/P99 of real traffic data, not averages.
     Design for peak × 1.5 buffer.
```

### Failure: No Capacity Room for Growth

```
Situation: Database sized for 1TB (1 year of data)
Reality: Product takes off, 1TB in 3 months
Result: Emergency migration at 2AM on a Sunday

Fix: "Design for 2× expected scale. Plan migration path for 10×."
```

### Tradeoff: Accuracy vs Speed in Estimation

| Estimation Approach | Time | Accuracy | When to Use |
|--------------------|------|----------|-------------|
| Back-of-envelope | 2 min | ±10× | During interview scoping |
| Spreadsheet model | 30 min | ±2× | Before writing RFC |
| Load test + monitoring | Days | ±20% | Production planning |

**Interview rule:** 2-minute back-of-envelope is fine. Say "this is a rough estimate, we'd validate with load testing."

### Tradeoff: Cost vs Latency

```
No caching:
  Cost: $0
  Latency: 200ms (DB every time)

Single Redis cache (100% hit):
  Cost: $200/month
  Latency: 5ms

Multi-region cache + CDN:
  Cost: $2000/month
  Latency: 2ms (for global users)

Staff+ question: "At what scale does each tier become worth it?"
  Answer: "At 1K QPS, DB is fine. At 10K QPS, we need cache.
           At 100K QPS global, we need multi-region + CDN."
```

---

## 8. Interview Execution Checklist

### Before You Draw Anything (First 5 Minutes)

```
☐ Clarify what system: "Just to confirm, we're designing X?"
☐ List functional reqs: core MVP features (3-5 max)
☐ Ask about NFRs: scale, latency, availability, consistency
☐ Estimate capacity: rough QPS, storage, bandwidth
☐ Nail one number: "The key constraint is Y (e.g., write throughput)"
```

### Staff+ Additions

```
☐ Call out service boundaries that will emerge
☐ Mention cost implication of design choices
☐ Flag which requirements could be relaxed for simplicity
☐ Show awareness of migration path ("would start monolithic")
```

### What Interviewers Write Down About You

```
□ Structured thinking (did they clarify before designing?)
□ Scale awareness (did they estimate, or guess?)
□ Tradeoff quality (did they explain why, not just what?)
□ Production sense (did they mention monitoring, failure, cost?)
□ Communication (did they guide me through their reasoning?)
```

---

## 9. Practice Problems for This Skill

Before designing any system, practice just the requirements + estimation phase:

1. **URL Shortener** — 100M URLs/month, 1B redirects/month, global
2. **Chat System** — 500M users, 10B messages/day, zero data loss
3. **Payment System** — 10M transactions/day, regulatory audit required
4. **Video Platform** — 100M users, 1B views/day, global
5. **Feed System** — 200M DAU, 5:1 read:write, 200ms latency budget

For each:
- Write the requirements table (functional + NFR)
- Do the capacity math (QPS, storage, bandwidth)
- Say "the bottleneck is X" and justify
- Identify which requirement you'd drop and why

---

## 10. Back-of-Envelope Estimation Reference

A standalone cheat sheet. Memorize this, and you never freeze on estimation.

### Constants You Should Have in Muscle Memory

```
Seconds per day:       86,400   (~10^5)
Days per month:          30     (~3×10^1)
Days per year:          365     (~4×10^2)
Months per year:         12
1 million:             10^6
1 billion:             10^9
1 TB:                  10^12 bytes
1 Gbps:               125 MB/s
```

### Formula Quick Reference

```
QPS = DAU × actions_per_user / 86400
Peak QPS = Avg QPS × peak_factor (use 3-5× if unknown)

Storage/day = write_QPS × record_bytes × 86400
Storage/year = storage/day × 365 × replication_factor

Cache_memory = read_QPS × record_bytes × TTL_seconds
Bandwidth_bps = QPS × response_bytes × 8

Connections_needed = QPS × avg_latency_seconds
Threads_needed = QPS × latency_seconds / cores
```

### Numbers Every Engineer Should Know (by Latency)

```
L1 cache reference:                  0.5 ns
Branch mispredict:                    5 ns
L2 cache reference:                    7 ns
Mutex lock/unlock:                    25 ns
Main memory reference:              100 ns
Send 1KB over 1 Gbps network:      8,000 ns    (8 µs)
Read 1MB sequentially from SSD:    50,000 ns   (50 µs)
Round trip same datacenter:       500,000 ns   (0.5 ms)
Disk seek:                      2,000,000 ns   (2 ms)
Round trip cross-region:        50,000,000 ns  (50 ms)
Round trip cross-continent:    150,000,000 ns (150 ms)
```

**Key insight:** A cache hit vs a DB call is the difference between 100ns and 10ms — **100,000× slower**. This is why cache design matters more than almost anything.

### Pre-Computed Interview Numbers

Use these as sanity-check anchors during interviews:

| Metric | Small | Medium | Large | X-Large |
|--------|-------|--------|-------|---------|
| DAU | 1M | 10M | 100M | 1B |
| Daily actions/user | 5 | 10 | 20 | 50 |
| Avg read QPS | 60 | 1,200 | 23,000 | 580,000 |
| Peak read QPS (3×) | 180 | 3,600 | 69,000 | 1.7M |
| Avg write QPS | 10 | 200 | 4,600 | 115,000 |
| Peak write QPS (3×) | 30 | 600 | 13,800 | 345,000 |
| Daily storage (1KB/record) | 1GB | 17GB | 400GB | 10TB |
| Yearly storage (3× repl) | 1TB | 18TB | 440TB | 11PB |

### System-Specific Pre-Computed Figures

These let you say "at that scale, X would require Y" without fumbling:

**URL Shortener (100M URLs/month, 1B redirects/month)**

```
Writes:   38 URLs/sec avg (100M / 30d / 86400)
Reads:   386 redirects/sec avg (1B / 30d / 86400)
Read:write ratio: ~10:1
Storage:  100M × 500 bytes × 12 months ≈ 600GB/year
Cache:    386 × 500 × 3600 (1hr TTL) ≈ 700MB Redis
Key length: 7 chars base62 = 62^7 ≈ 3.5T combinations
```

**Chat System (500M users, 10B messages/day)**

```
Writes:   115,000 msgs/sec (10B / 86400)
Storage:  115K × 1KB × 86400 ≈ 10TB/day → 3.6PB/year (with 3× repl)
Reads:    Varies by user (load historical on app open)
Key constraint: Write throughput. Need Kafka + Cassandra.
            115K writes/sec ≈ 3× Cassandra nodes
```

**Payment System (10M txns/day, regulatory)**

```
Writes:   115 txns/sec avg → 1,000 peak
Storage:  115 × 2KB × 86400 ≈ 20GB/day → 7GB/year raw
          7 years retention × 3× replication ≈ 150TB total
Key constraint: Correctness, not throughput.
            Single Postgres with WAL + read replicas is fine.
```

**Video Platform (100M users, 1B views/day)**

```
Views:    11,500 views/sec avg → 35,000 peak
Storage:  upload: 500 hours/min video × 500MB/hr ≈ 4TB/day raw
          transcoded (3 bitrates): 4TB × 3 = 12TB/day
          1 year: 12TB × 365 ≈ 4.4PB (object store)
Bandwidth: 35,000 views × 5Mbps / 8 ≈ 22 GB/s → 176 Gbps egress
Key constraint: Bandwidth cost. CDN required.
```

**Feed System (200M DAU, 5:1 read:write, 200ms p99)**

```
Writes:   4,600 posts/sec avg → 13,800 peak
Reads:   23,000 timeline reads/sec → 69,000 peak
Fan-out writes (celebrity): 10M followers × 1 post = 10M timeline inserts
Key constraint: Fan-out write amplification.
            Switch from push (all followers) to pull (celebrities > 100K followers)
```

### Quick Cost Math (AWS, Approximate Monthly)

```
Per instance:
  Web server (2 vCPU, 8GB):              $70
  App server (4 vCPU, 16GB):            $140
  DB (db.r5.large, 2 vCPU, 16GB):       $200
  DB (db.r5.xlarge, 4 vCPU, 32GB):      $400
  Redis (cache.r5.large, 13GB):          $200
  Redis (cache.r5.xlarge, 26GB):         $400

Per GB:
  S3 standard:                           $0.023/GB
  S3 infrequent access:                  $0.0125/GB
  EBS gp3 SSD:                           $0.08/GB
  Data transfer out to internet:         $0.09/GB
  Data transfer cross-region:            $0.02/GB

Quick monthly estimate:
  (instances × per_instance) + (storage_GB × per_GB) + (egress_GB × 0.09)
```

### Language-Specific Quick Math

```
Java thread per request:
  1 thread ≈ 1MB stack → 1000 threads ≈ 1GB memory overhead
  Virtual threads: ~10KB each → 100K threads ≈ 1GB

Go goroutine:
  1 goroutine ≈ 4KB stack (grows as needed)
  100K goroutines ≈ 400MB (but scheduler handles them)
  Context switch: ~100ns vs ~1µs for OS threads

Python:
  1 Python process ≈ 1 GIL
  Need 4 processes to match 1 Go binary on CPU
  asyncio: 10K connections ≈ 100MB (event loop overhead)
  Process pool: 4 workers × 100MB RSS ≈ 400MB base
```

### More Pre-Computed Systems

**Instagram / Photo Sharing (500M DAU, 100M photos/day)**

```
Writes:    1,150 photo uploads/sec (100M / 86400)
Reads:    23,000 feed views/sec (500M DAU × 4 views/day / 86400)
Storage:  1,150 × 2MB (photo) × 86400 ≈ 200TB/day raw
           Transcode (3 sizes): 600TB/day → 210PB/year
           Actual storage: ~10PB (aggressive compression, dedup, thumbs)
Bandwidth: 23,000 × 500KB (compressed) / 86400... won't fit.
           Peak: 100K views/sec × 500KB = 50GB/sec → 400 Gbps
Key insight: Photos must be served from CDN. App servers barely touch media.
            Metadata in Postgres (sharded by user_id), blobs in S3.
```

**Uber / Ride Hailing (100M DAU, 20M trips/day)**

```
Trips:     230 trips/sec avg → 1,000 peak (rush hour)
Writes:   Location pings: every 4 sec × 1M active drivers = 250K loc/sec
          Trip events (start/end/pay): 1,000/sec
Reads:   Rider looking for nearby drivers: every 2 sec × 5M active = 2.5M QPS
         ETA calculations: 100K/sec
Storage: Location: 250K × 100 bytes × 86400 ≈ 2TB/day → 730TB/year
         Trip history: 20M × 2KB × 365 ≈ 15TB/year
Key constraint: Location writes at 250K/sec need high-throughput ingestion.
              Redis Geohash or custom grid-based spatial index.
              Kafka for location stream, Cassandra for trip storage.
```

**Netflix (200M subscribers, 1B hours streamed/month)**

```
Streaming hours: 1B hours/month → 380 hours/sec
                 Each hour = 3GB (4K) / 1GB (HD) / 300MB (SD)
Bandwidth (HD avg): 380 × 1GB × 8 / 3600 ≈ 850 Mbps per subscriber
                    Wait — that's wrong. Let me redo.
                    Each stream: ~5 Mbps (HD)
                    380 concurrent streams/sec... no.
                    Peak: 10M concurrent streams × 5 Mbps = 50 Tbps
                    That needs CDN with edge caching heavily.
                    Netflix does this with Open Connect appliances at ISP peering.
Storage:  200M subscribers × 50GB (catalog) ≈ 10PB master storage
          But the real storage is the encoding pipeline.
          Origin: 200TB master files (raw). Encoded: 5PB (all bitrates/languages).
          CDN cache at edge: hottest 20% of catalog ≈ 1PB globally.

Key insight: Netflix doesn't stream from "a server." It pre-positions content at ISP edges.
            Back-of-envelope: "We'd need ~50 Tbps egress. No single cloud region can do that.
            We'd use edge CDN with local caches serving 95%+ of traffic."
```

**WhatsApp (2B users, 100B messages/day)**

```
Writes:   1.15M messages/sec (100B / 86400)
           Peak: 2-3M/sec (holidays, new year)
Storage:  1.15M × 1KB × 86400 ≈ 100TB/day
           365 days × 100TB × 2× repl (no need for 3×) ≈ 73PB/year
           Ephemeral: most messages delivered and deletable from server
           Actual persistence: ~7 days on server → 700TB rolling buffer
Key constraint: 1M+ writes/sec. Single tech can't handle it.
              Erlang (Ejabberd) on custom servers. Each server handles ~1M connections.
              Messages written to log, acked, then deleted.
              Back-of-envelope insight: This violates most textbook assumptions.
              They don't use Kafka. They don't Cassandra (mostly). Their whole system
              is memory-first, persistence-second.
```

**Google Search (5B searches/day — 2019 public number)**

```
Queries:  57,000 queries/sec avg → 200,000 peak
          5B / 86400 ≈ 58K... but Google does way more now.
          Let's use 100K avg for modern estimates.

Each query touches:
  1. Index servers (find matching docs) — 10-50ms
  2. Document servers (fetch snippets) — 5-20ms
  3. Ranking servers (ML model scoring) — 20-100ms

Backend QPS (amplification): 100K queries × 10-100 shards = 1M-10M internal QPS
Storage (web crawl): ~100PB index (compressed inverted index)
                     ~5PB document store (snippets, not full pages)

Key insight: The "query fan-out" is the bottleneck.
           100K user QPS × 100 index shards = 10M internal QPS.
            Each shard returns top 10, reranker picks top 10 from 1000.
```

### Back-of-Envelope for AI/ML Systems

**RAG / LLM Chat System (10M DAU, 5 queries/day)**

```
Queries:  10M × 5 / 86400 ≈ 580 QPS avg → 1,700 peak

Vector DB (retrieval step):
  Documents: 100M chunks × 768-dim embedding × 4 bytes = 300GB
  Memory for index (HNSW): ~300GB + 2× overhead = 1TB RAM
  Query latency: ~10ms (ANN search, 100K candidates)

LLM inference:
  Input tokens: ~500 per query (prompt + context)
  Output tokens: ~200 per query (response)
  Total tokens/sec: 580 × 700 = 406K tokens/sec

  GPU requirements:
    Llama 70B (FP16): 140GB VRAM → 4× A100-80GB
    Throughput: ~2K tokens/sec per A100
    Need: 406K / 2K = 200 A100 GPUs = ~50 nodes (4 GPU each)

  Cheaper alternative:
    Llama 8B (FP16): 16GB VRAM → 1× A100
    Throughput: ~8K tokens/sec per A100
    Need: 406K / 8K = 50 A100 GPUs = ~13 nodes

Cost estimate for LLM inference:
  200 A100 GPUs × $2/hr (on-demand) = $400/hr → $290K/month
  With reserved (1yr): $1.2/hr → $175K/month
  With quantization (INT8): 2× throughput → half the GPUs

Key insight: LLM inference cost dominates. 10M DAU × 5 queries × $0.001/query = $50K/day.
            Caching common queries (50% cache hit) cuts it to $25K/day.
            Prompt optimization (shorter context) cuts another 30%.
```

**Embedding Pipeline (batch processing 10M docs/day)**

```
Documents: 10M/day → 115 docs/sec
Each doc: 1K tokens → embedding vector (768-dim, FP32) = 3KB
Output: 115 × 3KB × 86400 ≈ 30GB embeddings/day → 11TB/year

GPU cost:
  Embedding model (e5-mistral-7b): ~4K tokens/sec per A100
  115 docs/sec × 1K tokens = 115K tokens/sec
  Need: 115K / 4K ≈ 30 A100 GPUs
  But this is a batch job. Can queue and process slower.
  With 8-hour batch window: 10M × 1K / (8×3600) = 347 tokens/sec → 1 GPU
```

**Feature Store (real-time ML inference)**

```
Features per prediction: 200 features × 4 bytes = 800 bytes
QPS: 10K predictions/sec
Feature read QPS: 10K × 200 = 2M feature reads/sec → Redis cluster (~20 nodes)
Feature write QPS: 10K × 200 = 2M feature writes/sec (if online learning)
                   More realistic: batch updates every hour → 555 writes/sec

Memory: 10K features × 1KB each (feature definition + values) = 10MB → trivial
        But: 10M entities × 200 features × 4 bytes = 8GB per entity set
        10 entity sets: 80GB → fits in 2-3 Redis nodes
```

### Database Throughput Numbers (Realistic Bounds)

These are **per-node** numbers for back-of-envelope. Actual varies by workload.

```
PostgreSQL:
  Writes (single row, indexed):         1K-5K/sec
  Writes (batched, 100 rows):          50K-100K/sec
  Reads (by PK, cached):               10K-50K/sec
  Reads (full scan, 1GB table):        500/sec
  Max connections:                      500 (default) — don't exceed
  Practical max per node:              10K mixed ops/sec

MySQL:
  Similar to Postgres:                 1K-10K writes/sec
  Read replicas:                       10K-50K reads/sec
  InnoDB buffer pool:                  fit working set in memory

Cassandra:
  Writes per node:                     10K-50K/sec (log-structured, fast)
  Reads per node:                      1K-10K/sec (depends on disk)
  Max nodes in cluster:                100-300 (before coordination overhead)

MongoDB:
  Writes per node:                     5K-20K/sec
  Reads per node:                      10K-50K/sec
  Sharding:                            auto, but hot keys still hurt

DynamoDB:
  Single partition throughput:         3K read + 1K write (hard limit)
  Total table throughput:              essentially unlimited (add partitions)
  Cost:                                $1.25/hr per 10K WCU + 50K RCU

Redis:
  Single node ops/sec:                 100K-200K (simple get/set)
  With pipelining:                     1M+ ops/sec
  Memory:                              capped by RAM (up to ~512GB in large nodes)
  Persistence:                         RDB/AOF — dont rely on it 100%

Elasticsearch:
  Indexing per node:                  2K-10K docs/sec
  Search per node:                    5K-50K queries/sec (depends on complexity)
  Max nodes:                          100+ (cluster state becomes bottleneck)

Kafka:
  Per partition throughput:           100K-1M msgs/sec (small msgs)
  Per broker throughput:              200MB-1GB/sec (limited by disk/NIC)
  Total cluster:                      essentially unbounded
  Retention:                          time or size based (disk cheap)

S3 / Object Store:
  First byte latency:                 50-200ms (warm)
  Throughput per prefix:              3.5K PUT/5.5K GET req/sec
  Can scale by adding prefixes:       10K prefixes → 35M PUT/sec theoretical
  Cost:                               10× cheaper than EBS for bulk
```

### Little's Law for Queue Estimation

Little's Law: `L = λ × W`

- L = average items in queue
- λ = arrival rate (QPS)
- W = average time each item spends in queue (seconds)

```
Example: 10K QPS arriving, each request takes 50ms to process

If we have 500 worker threads:
  Utilization: λ × W / threads = 10,000 × 0.05 / 500 = 1.0 (100% — BAD)
  Queue grows unbounded. Requests queue up, timeout.

If we have 1000 worker threads:
  Utilization: 10,000 × 0.05 / 1000 = 0.5 (50% — healthy)
  Queue: L = 10,000 × 0.05 = 500 items
  Avg wait: W = L / λ = 500 / 10,000 = 0.05 sec = 50ms
  Total response time: 50ms (service) + 50ms (wait) = 100ms

If 2000 threads:
  Utilization: 25%
  Queue: L = 10,000 × 0.01 (less contention) ≈ 100
  Total response time: ~60ms

Staff+ insight: Little's Law tells you your thread pool size isn't arbitrary.
              Threads = QPS × latency_target.
              If QPS doubles and thread count stays same, latency doubles (or queue overflows).
```

### Memory Estimation Patterns

```
In-memory cache (Redis):
  Each entry overhead:          ~50 bytes (key + pointer + metadata)
  String value overhead:        ~50 bytes + actual value
  Hash (field-value pairs):     ~50 + n × (field_overhead + value_overhead)
  Sorted set (zset):             ~50 + n × (key + score)
  Bitmap:                        1 bit per entry

Example: 10M entries, avg 500 bytes each
  Data: 10M × 500 = 5GB
  Overhead: 10M × 50 = 500MB
  Total: ~5.5GB → use a 10GB Redis instance (account for fragmentation)

In-memory data structures (Java/Go app):
  Java object overhead:          16-24 bytes per object
  String in Java (JDK 17+):      header + byte[] + length
     "hello" (5 chars):          ~24 + 16 + 4 + padding ≈ 48 bytes
     vs: char[] = 5 × 2 = 10 bytes stored
     Moral: String objects are 5-10× larger than the data they hold

  Go string:                     header (16 bytes) + pointer to bytes
     "hello" (5 chars):          16 + 5 = 21 bytes (much leaner)
  Go map entry:                  ~40 bytes (key + value + hash + bucket ptr)
  Go slice:                      24 bytes header + backing array

  Python int:                    28 bytes (PyObject header + value)
  Python string (5 chars):       49 bytes (PyObject + hash + length + char data)
  Python dict entry:             ~72 bytes (PyDictEntry × 3 per bucket)
  Python list:                   8 bytes per element (pointer) + object sizes
  Moral: Python in-memory is 2-5× heavier than Go for same data.
```

### Bandwidth Quick Calcs

```
Per NIC:
  1 Gbps → 125 MB/s
  10 Gbps → 1.25 GB/s
  25 Gbps → 3.1 GB/s
  100 Gbps → 12.5 GB/s

Per request type:
  JSON API response (200 bytes):    40K responses/sec on 1 Gbps
  REST API response (4 KB):         2K responses/sec on 1 Gbps   ← most APIs
  Image (500 KB):                   250 responses/sec on 1 Gbps
  Video chunk (4 MB):               31 responses/sec on 1 Gbps
  ML model download (500 MB):       0.25 downloads/sec on 1 Gbps

Cross-region transfer cost:
  1 Gbps sustained cross-region: ~$0.02/GB × 125 MB/s × 86400 × 30 = $6.5M/month  ← this is why CDN exists
  Same-region: usually free

CDN egress cost:
  CloudFront: ~$0.085/GB
  CloudFlare: ~$0.015/GB (or flat rate)
  Internal CDN (self-built): ~$0.005/GB (hardware amortized)
```

### Concurrency Estimation (How Many Instances?)

```
QPS per instance depends on:

  IO-bound workload (API calls, DB queries, cache reads):
    Python (asyncio):          2K-5K QPS per process
    Python (sync, 4 workers):  500-1K QPS per instance
    Go (net/http):             10K-50K QPS per instance
    Java (Netty/VT):           10K-50K QPS per instance
    Node.js:                   5K-20K QPS per instance

  CPU-bound workload (encoding, ML inference, image processing):
    Python:                    50-500 QPS per instance (GIL-limited)
    Go:                        1K-10K QPS per instance
    Java:                      1K-10K QPS per instance
    Rust:                      5K-50K QPS per instance

  Memory-bound workload (caching heavy, large dataset in RAM):
    All languages:             limited by GC behavior, not raw speed
    Java:                      needs large heap (16GB+), ZGC for <10ms pauses
    Go:                        smaller heap, less GC tuning needed
    Python:                    process-based (reload on mem growth)

Quick instance calculator:
  instances = peak_QPS / per_instance_capacity × safety_factor
  safety_factor = 0.5-0.7 (leave headroom for rolling deploys, traffic spikes)

Example: 100K peak QPS, Go service (30K QPS/instance)
  instances = 100K / 30K × 1.5 = 5 instances (3 minimum for 50% headroom)
  Cost: 5 × $70 = $350/month (compute only)

Example: Same 100K QPS, Python sync (1K QPS/instance)
  instances = 100K / 1K × 1.5 = 150 instances
  Cost: 150 × $70 = $10,500/month
  So Python costs 30× more for same throughput. This matters in design interviews.
```

### "Is This System Possible?" Quick Feasibility Check

Before going deep into a design, ask: "Is this even feasible at this scale?"

```
Can a single DB handle the writes?
  Writes needed: 50K/sec
  Postgres max: 5K/sec → Need 10 Postgres nodes or Cassandra

Can a single Redis handle the cache reads?
  Reads needed: 500K/sec
  Redis max: 100K/sec → Need 5 Redis nodes (or Redis Cluster)

Can a single Kafka cluster handle the event throughput?
  Events/sec: 5M/sec
  Per partition: 500K/sec → 10 partitions
  Per broker: 5 partitions → 2 brokers (with replication)
  This is fine.

Can the network handle the bandwidth?
  Bandwidth needed: 50 Gbps
  10 Gbps NIC limit → 5 instances behind load balancer
  Or 1 instance with 100 Gbps NIC → but expensive

Can the app handle the connection count?
  1M WebSocket connections:
    Python: maybe 100K per box (asyncio), need 10 boxes
    Go: 500K per box, need 2 boxes
    Java (Netty): 500K per box, need 2 boxes
    Node: 200K per box, need 5 boxes
```

### Estimation by Analogy (When You Have Zero Data)

When the interviewer gives vague numbers, anchor to known systems:

```
"100M DAU — that's similar to Twitter scale (2015)."
  → Twitter had 100M DAU, ~500M tweets/day, ~20K writes/sec

"500M DAU — that's similar to Instagram."
  → Instagram: 500M DAU, 100M photos/day, ~1K uploads/sec

"1B users — similar to WhatsApp or Facebook."
  → WhatsApp: 1B+ users, 40-100B msgs/day, ~1M writes/sec

"10M transactions/day — modest."
  → 115 TPS avg. Single Postgres can handle this. Don't overengineer.
```

### Total Cheat Sheet (The One Page)

```
╔══════════════════════════════════════════════════════════════╗
║              BACK-OF-ENVELOPE — COMPLETE                    ║
╠══════════════════════════════════════════════════════════════╣
║ FORMULAS                                                     ║
║ QPS = DAU × actions ÷ 86,400                                 ║
║ Peak = Avg × 3-5×                                             ║
║ Storage = QPS_w × bytes × 86,400 × 365 × repl               ║
║ Bandwidth (Gbps) = QPS × bytes × 8 ÷ 1e9                    ║
║ Cache = QPS_r × bytes × TTL_sec                              ║
║ Instances = PeakQPS ÷ capacity × 1.5                         ║
║ Connections = QPS × latency_sec                               ║
║                                                               ║
║ PER-NODE THROUGHPUT                                           ║
║ Postgres writes:      5K/sec     Redis ops:   100K/sec       ║
║ Cassandra writes:    50K/sec     Kafka/part:  500K/sec       ║
║ DynamoDB/part:      1K WPS       Elastic idx:  5K/sec        ║
║ Go HTTP:             30K/sec     Java Netty:   30K/sec       ║
║ Python asyncio:       5K/sec     Python sync:   1K/sec       ║
║                                                               ║
║ LATENCY (p99)                                                 ║
║ Same DC:    0.5-1ms    Cross-region:   50-200ms              ║
║ Cross-ocean: 150ms     CDN edge hit:   <5ms                  ║
║                                                               ║
║ STORAGE                                                       ║
║ 1M × 1KB records     ≈ 1GB                                   ║
║ 1B × 1KB records     ≈ 1TB                                   ║
║ 1B × 100KB           ≈ 100TB                                 ║
║ S3 cost:             $23/TB/month                             ║
║                                                               ║
║ AI/ML SHORTCUTS                                               ║
║ Llama 70B inference:   2K tok/s/A100                         ║
║ Llama 8B inference:    8K tok/s/A100                         ║
║ Embedding (7B model):  4K tok/s/A100                         ║
║ Vector search (1TB):   10ms (HNSW, 100K candidates)          ║
║                                                               ║
║ STAFF+ MOVES                                                  ║
║ "I'd validate this with a load test."                         ║
║ "At 2× this scale, we'd need to [shard/add cache/split svc]."║
║ "The bottleneck is [write throughput / bandwidth / cost]."    ║
║ "I'd start monolithic. Here's where I'd split."              ║
╚══════════════════════════════════════════════════════════════╝
```

### Estimation Flow — One More Time

Here's the complete mental flow for any system design interview:

```
Q: "Design X for Y users"
│
├─ CLARIFY (2 min)
│  ├─ Functional: "What does the user do?"
│  ├─ NFR: "Scale, latency, consistency, availability?"
│  └─ Scope: "MVP or full? Global or US?"
│
├─ ESTIMATE (3 min) ← Back-of-envelope starts here
│  ├─ DAU = total × daily_pct
│  ├─ QPS_read/write = DAU × actions ÷ 86400
│  ├─ Peak = avg × 3
│  ├─ Storage = QPS_w × bytes × time × repl
│  ├─ Cache = QPS_r × bytes × TTL
│  ├─ Bandwidth = peak_QPS × response_bytes × 8 (in bps)
│  └─ "Key constraint: [write throughput / bandwidth / storage]"
│
├─ HIGH-LEVEL DESIGN (10 min)
│  └─ Every choice anchored to: "The scale requires X"
│
└─ DEEP DIVE (10 min)
   └─ "At this scale, the bottleneck is Y"
```

**Every box you draw should trace back to a number.**
If you drew a cache, you should have estimated the cache size.
If you drew a queue, you should know the QPS and acceptable delay.

---

## 11. More Back-of-Envelope Patterns

### Batch Job Duration Estimation

ETL, nightly builds, backfills, data migrations — all batch work.

```
Data to process: 10TB
Throughput per worker: 50 MB/s (read + transform + write)
Workers: 20 parallel
Time: 10TB / (50 MB/s × 20) = 10,000 sec ≈ 2.8 hours

With contention (shared DB, network limits):
  Effective throughput drops to 60% → 4.5 hours

Staff+ move: "This batch window won't fit in the nightly 4-hour window.
             We need either more workers (cost) or incremental processing (complexity)."
```

**Common batch scenarios:**

```
Log archival (10TB/day → S3):
  10TB / (100 MB/s per stream × 5 streams) ≈ 20,000 sec ≈ 5.5 hours
  ✓ Fits in daily batch window

ML model training (1TB training data):
  Data loading: 1TB / 500 MB/s (SSD) ≈ 30 min
  Training (GPU): depends on model. Estimate by FLOPs.
  GPT-3 175B on 1024 A100: 34 days (no, that's real number).
  For back-of-envelope: "X hours on Y GPUs"
  Llama 70B fine-tune on 10M tokens: ~8 hours on 8 A100

DB migration (5TB, from Postgres to Cassandra):
  Export: 5TB / 50 MB/s (pg_dump) ≈ 28 hours ← painful
  Import: 5TB / 10 MB/s (Cassandra write) ≈ 140 hours ← very painful
  This is a weekend project. Or use CDC instead of bulk migration.
```

### P50 / P95 / P99 Relationship

Given one percentile, estimate others:

```
If p50 = X and no outlier distribution:
  p95 ≈ 2-3× p50    (typical web app)
  p99 ≈ 5-10× p50   (add GC pauses, network jitter)
  p99.9 ≈ 20-50× p50 (rare, but happens)

If p50 = 50ms (reasonable API):
  p95 ≈ 100-150ms
  p99 ≈ 250-500ms
  p99.9 ≈ 1-2.5s

If p50 = 5ms (cached, simple):
  p95 ≈ 10-15ms
  p99 ≈ 25-50ms
  p99.9 ≈ 100-250ms

Staff+ insight: "Our SLO is p99 < 200ms. Based on p50 = 30ms,
                we have about 170ms of budget. 90ms is buffer."
```

### Multi-Region Replication Lag

```
Single-region write, async replication to second region:
  Latency: same-region commit (~5ms) + cross-region copy (50-150ms)
  Replication lag: typically 50-500ms for async
  Can spike to seconds during network issues

Synchronous replication (no data loss):
  Latency: same-region commit (~5ms) + 2× cross-region (100-300ms)
  Total: 100-300ms per write — adds 20-60× to write latency

Consensus-based (Raft/Paxos cross-region):
  Requires majority across regions
  3 regions (us-east, us-west, eu-west):
    Leader in us-east, commit requires us-east + us-west or us-east + eu-west
    Latency: ~65ms (longest cross-region of the two confirmations)
```

### Rate Limiting Estimation

```
Token bucket: tokens = rate × time_window
  rate = 100 req/sec, bucket size = 1000 tokens
  Burst: up to 1000 in one second, then 100/sec sustained

Sliding window: requests in last 60 seconds
  Memory: user_id → [timestamp1, timestamp2, ...]
  Bad: O(n) per request, O(m × n) memory
  Better: counter per time bucket

Redis-backed rate limiter:
  Per user key in Redis: `rate_limit:{user_id}:{window}`
  Memory per user per window: ~50 bytes
  10M DAU, 1 limit per user: 10M × 50 bytes = 500MB → 1 Redis instance
  QPS to Redis: same as API QPS (each request checks limit)
  If 100K API QPS → 100K Redis QPS → 1 Redis instance (handles 100K)

Rate limit key design:
  Global rate limit: 1 key → no scalability issue
  Per-user rate limit: N users 
  Per-IP rate limit: N IPs (could be 100M → need sharded Redis)
```

### Data Serialization Size Estimation

```
Full JSON response (user profile):
  { "id": 123, "name": "John", "email": "j@x.co", "age": 30,
    "city": "NYC", "country": "US", "avatar": "https://..." }
  ≈ 400 bytes JSON (no whitespace)

Compressed JSON (gzip):
  ≈ 120 bytes (3-4× compression for text)

Protobuf (same data):
  ~60 bytes (schema-defined, binary, no field names)

Avro (with schema):
  ~50 bytes (similar to protobuf, better for streaming)

FlatBuffers / Cap'n Proto:
  ~45 bytes (no serialization step — read from buffer directly)

Thrift (binary):
  ~55 bytes

Per-request savings (10K QPS, JSON → Protobuf):
  400 bytes → 60 bytes = 340 bytes saved per request
  10K × 340 × 86400 = 294 GB/day bandwidth saved
  Egress cost = 294 GB × $0.09 = $26/day ≈ $800/month
  Plus: serialization CPU drops from ~200µs to ~10µs per request
  Net: ~$1K/month + 2-5% CPU reduction
```

### Database Index Size Estimation

```
B-tree index (Postgres/MySQL default):
  Index on 4-byte integer column
  B-tree node: ~8KB page
  Each entry: 4 bytes (key) + pointer (4-8 bytes) ≈ 12 bytes
  Entries per page: 8KB / 12 ≈ 680
  Index height for 1M rows: log_680(1M) ≈ 3 levels
  Index height for 1B rows: log_680(1B) ≈ 4 levels
  → Most indexes are 3-4 levels deep. No noticeable difference between 1M and 1B.

B-tree index on VARCHAR(255):
  Avg key: 20 bytes + pointer 6 bytes ≈ 26 bytes
  Entries per page: 8KB / 26 ≈ 315
  Index size for 1M rows: 1M × 26 = 26MB + overhead ≈ 40MB

Composite index (city, status, created_at):
  Key: 20 + 1 + 8 = 29 bytes + pointer 6 = 35 bytes
  For 10M rows: 10M × 35 = 350MB
  This fits in RAM on any reasonable server.

Inverted index (Elasticsearch/Lucene):
  Term dictionary: ~20% of source size
  Postings list (doc IDs): ~30% of source size
  Total inverted index: ~50-70% of source document size
  For 100GB of text: ~60GB inverted index → need ~100GB RAM for fast queries

Vector index (HNSW):
  Memory: ~1.1-1.3× the raw vector size (index overhead)
  100M vectors × 768 dim × 4 bytes (FP32) = 307GB
  HNSW index: ~350GB
  Must be in memory for fast ANN search (sub-10ms)
```

### Data Skew Estimation

```
User distribution (Pareto principle):
  Top 1% of users → 50% of traffic
  Top 10% of users → 90% of traffic
  Bottom 50% of users → 1% of traffic

Implication for caching:
  1M total users → 10K "heavy" users drive 90% of traffic
  Cache the top 10K users (their data fits in small Redis)
  Rest of users hit DB — fine because their traffic is low

Implication for sharding:
  Range shard by user_id → heavy users all in one shard
  Hash shard by user_id → heavy users spread evenly (✓)
  But if one user generates 50% of traffic (celebrity on Twitter):
    Hash shard helps a little, but one partition still overloaded
    Solution: sub-shard the celebrity (their data split across 100 partitions)

Implication for Kafka partitions:
  Partition by user_id → one partition gets 50% of messages
  Solution: partition by message_id (random) → even distribution
  Or: key by user_id but have 1000+ partitions
```

### Hot Key Estimation

```
Hot key: one cache key gets disproportionate traffic

Example: Super Bowl tweet goes viral
  Normal load: 23K reads/sec across 1M keys → 0.023 reads/sec per key
  Viral tweet: 100K reads/sec on ONE key
  Single Redis node can handle 100K reads/sec → just barely fine
  But if 10 viral items simultaneously → 1M reads/sec → Redis collapses

Solutions:
  Local cache on app server (caffeine/cachetools): absorbs 80% of reads
  Replicate hot key across Redis cluster (all N nodes have it)
  Client-side cache: browsers/CDN

Detection: identify keys with QPS > 10× average
  monitor per-key read rate in Redis
  prometheus metrics per cache key prefix (not per individual key)
```

### Fan-Out Amplification Estimation

```
Fan-out pattern: one action triggers N downstream actions

Read fan-out (search query hits multiple shards):
  100K QPS incoming × 10 index shards = 1M internal QPS
  Each shard returns top 10 results
  Network: 100K × 10 × 1KB (doc snippet) = 1GB/s internal bandwidth
  Combined: gigabit NIC is fine. But reranker receives 1M docs/sec.

Write fan-out (push model for feed):
  User posts, system pushes to 100K followers' timelines
  100 writes/sec × 100K followers = 10M fan-out writes/sec
  This is 10× what most databases can handle.
  That's why Twitter uses pull model for celebrities (>100K followers).

Notification fan-out:
  Group message: 1 send × 500 members = 500 push notifications
  50 group msgs/sec × 500 members = 25K notifications/sec
  FCM/APNS can handle 10K-100K/sec
  Need to throttle per provider to avoid rate limits

Event fan-out (CDC):
  1 DB write → 1 CDC event → N consumers (search cache, analytics, audit)
  With 5 consumers: 1K writes/sec → 5K internal events/sec
  Kafka handles this trivially. But if each consumer does fan-out...
  Consumer1 sends notification: 5K events × 10 followers = 50K/sec
  Consumer2 updates search: 5K × 3 replicas = 15K/sec  
  Total from 1K DB writes: 70K downstream ops/sec
```

### Connection Pool Sizing for DB

```
Formula: pool_size = QPS × avg_query_time / cores (adjusted)

Example: 10K QPS, avg query 10ms, 8 cores
  pool_size = 10,000 × 0.01 / 8 = 12.5 → 13 connections
  But each connection uses ~10MB memory (Postgres)
  13 × 10MB = 130MB — trivial

But wait:
  Kafka-style slow queries (analytics, 500ms):
  pool_size = 10,000 × 0.5 / 8 = 625 connections
  625 × 10MB = 6.25GB — significant
  Solution: separate pool for fast queries vs slow queries
  Or: queue slow queries separately, limit concurrency

PostgreSQL max_connections default: 100
  Each connection over 100 is queued by pgbouncer (connection pooler)
  Best practice: app → pgbouncer (50-200 connections) → Postgres (100)
  pgbouncer pools short-lived connections into the few Postgres connections

Quick rule:
  pool_size = (2-5) × CPU cores for fast queries
  pool_size = (10-50) × CPU cores for slow queries (but watch memory)
```

### Timeout / Retry Math

```
Expected additional latency from retries:

Single attempt, no retry:
  p99 latency = 200ms ← your base

With 1 retry on failure (timeout = 500ms, failure rate = 5%):
  P(need retry) = 5%
  Extra latency when retry needed: 500ms (timeout) + 200ms (retry) = 700ms
  Expected latency = 200ms + 5% × 700ms = 235ms
  p99 with retries ≈ 200ms + 500ms = 700ms ← higher than base p99

With exponential backoff (1s base, 2× factor, 3 retries):
  Max additional latency (all 3 fail): 1 + 2 + 4 = 7 seconds
  P(all 3 fail at 1% each): 0.01³ = 0.0001% → 1 in a million
  But client may retry 3 times within 100ms → server gets 3× load

Retry storm calculation:
  10K QPS, each server timeout triggers retry
  10% of requests timeout → 1K retries/sec → 11K total QPS
  Server gets 10% more load → another 10% timeout → 1.1K more retries
  This cascades. Formula: if retry causes > timeout_reduction, it's unstable.
  Fix: jitter (randomize retry timing), circuit breaker at client
```

### Compression Math

```
Text/JSON (API responses):
  gzip level 6: ~3-4× compression, ~100µs overhead per request
  zstd level 3: ~3-5× compression, ~50µs overhead per request
  Brotli level 4: ~4-5× compression, ~200µs overhead (better for static assets)

CPU vs bandwidth tradeoff:
  Without compression: 10K QPS × 4KB = 40MB/s egress → 320 Mbps
  With gzip: 10K QPS × 1KB = 10MB/s egress → 80 Mbps (4× less)
  CPU cost: 10K × 100µs = 1 CPU-second per second = 1 full core
  Net win: reduces bandwidth by 75%, costs 5-10% of a server's CPU

Binary vs text:
  Protobuf: ~4× smaller than JSON, ~10× less CPU to parse
  Avro: similar savings, better for streaming
  MessagePack: ~2× smaller than JSON, ~5× less CPU
  Tradeoff: debuggability. "I can curl and see JSON" vs "I need a tool for protobuf"
```

### GC / Memory Estimation

```
Java (G1GC, 16GB heap):
  Young GC: ~50ms every 10-20 seconds (tunable)
  Old GC: ~500ms every few hours (tunable)
  Pause frequency: increases with heap size
  Recommendation: don't exceed 32GB heap to avoid compressed OOPs penalty
  At 32GB: 1-2% CPU overhead for GC at moderate allocation rate

Java (ZGC, any heap):
  Pause: <1ms (sub-millisecond typically)
  CPU overhead: ~5-10% more than G1GC
  Good for: latency-sensitive apps (p99 < 10ms)
  Bad for: CPU-constrained apps (already at 90% CPU)

Go GC (non-generational, concurrent):
  Pause: <1ms typically (even with 100GB heap)
  CPU overhead: ~10-25% at high allocation rate
  Trigger: when heap grows 2× since last GC
  Tune: GOGC=50 (more frequent GC, less memory) or GOGC=200 (less GC, more memory)
  For high-throughput services: GOGC=100-200, expect 10-20% CPU on GC

Python GC (reference counting + generational):
  Reference counting: immediate, predictable cost (each decref is ~5ns)
  Generational GC: ~50ms every few seconds in typical web app
  Key issue: memory fragmentation for long-running processes
  Best: restart workers every few hours (gunicorn --max-requests)

Memory budget quick check:
  Java 16GB heap: RSS ~20GB (JVM overhead, metaspace, threads, off-heap)
  Go binary: RSS ~heap + 10-20% (GC metadata, small overhead)
  Python: RSS ~heap × 1.5-2× (object overhead, interpreter)
```

### Service Mesh Overhead

```
Envoy sidecar proxy (typical Istio setup):
  Per-request latency added: 1-5ms (depends on mesh depth)
  CPU per proxy: 0.1-0.5 vCPU per 10K QPS
  Memory per proxy: 50-100MB (mostly config + stats)
  MTLS overhead: additional 1-2ms if not using connection reuse

mTLS handshake:
  Full handshake: ~5ms (certificate exchange, key generation)
  After handshake (session reuse): ~0.1ms
  For long-lived connections (gRPC, HTTP/2): one handshake per connection

Back-of-envelope: "Adding Istio costs us ~5ms latency and ~0.3 vCPU per service.
                  For 20 services at 10K QPS each: 10 vCPU overhead.
                  Worth it for the observability and security, but not free."
```

### Encryption Overhead

```
TLS 1.3:
  Handshake: 1-RTT (~1 network round trip, ~0.5-1ms same DC)
  Per-request overhead: ~1-3% CPU (AES-NI hardware acceleration)
  Memory: negligible (session cache)

If no hardware acceleration (older CPUs):
  TLS overhead: ~5-10% CPU
  For 10K QPS on 4 cores: ~0.4-0.8 cores just for TLS

Field-level encryption (PII data):
  App encrypts before write, decrypts after read
  AES-256-GCM: ~100MB/s per core
  For 10M records/day with 100 bytes each: 1GB/day → trivial
  But: encrypted fields can't be indexed for search
  Solution: HMAC for exact match, blind indexes for range queries

Disk encryption (at rest):
  LUKS/AES-NI: <5% overhead (hardware-accelerated)
  No capacity estimation issue

End-to-end encryption (like WhatsApp):
  Every message encrypted with recipient's public key
  Server can't decrypt — affects search, analytics, spam detection
  No additional CPU estimation issue (client does the work)
  But: you can't run ML on encrypted data → affects feature requirements
```

### Eventual Consistency Convergence Time

```
Scenario: User updates profile picture in us-east
  Write committed to leader in us-east
  Async replication to us-west, eu-west, ap-southeast

Network:
  us-east → us-west: 60ms (one-way)
  us-east → eu-west: 80ms
  us-east → ap-southeast: 200ms

Best case (no contention):
  us-west updated: 60ms (replication lag)
  eu-west updated: 80ms
  ap-southeast updated: 200ms

Worst case (replication queue backed up):
  Each region has a replication queue
  If queue depth = 10K writes at 5K writes/sec: 2 seconds lag
  If network blip causes 30s outage: catch-up time = 30s + queue drain time

DNS propagation (for cache invalidation):
  Default TTL: 300 seconds
  If you need faster: 60 seconds (minimum recommended)
  If urgent: 5 seconds (with traffic increase on DNS servers)
  You cannot invalidate DNS instantly — design for this
```

### WebSocket / Connection Estimation

```
WebSocket connections per server:
  Each connection: ~10-20KB memory (kernel socket buffer + app state)
  100K connections: ~1-2GB RAM
  1M connections: ~10-20GB RAM

CPU for 100K connections:
  Polling (epoll/kqueue): O(1) per event → ~5% CPU for 100K idle
  Active (messages/sec): ~10% CPU per 10K msgs/sec
  For chat: each user sends 1 msg/10s, receives 1 msg/5s
  100K users: 30K msg/sec → ~30% CPU + 2GB RAM → ~3 servers for 100K users

Go vs Node vs Python for WebSocket:
  Go: 1M conn on 4GB RAM, ~40% CPU (gnet or gorilla/websocket)
  Node: 500K conn on 6GB RAM, ~50% CPU (heavier event loop per connection)
  Python (asyncio): 100K conn on 2GB, ~60% CPU (GIL, websockets lib)
  Java (Netty): 1M conn on 8GB, ~30% CPU (most optimized)

Staff+ insight: "WebSocket servers are memory-bound before CPU-bound.
                At 1M connections, we need ~16GB per server regardless of language.
                We'd horizontally scale by connection count, not CPU utilization."
```

### Load Balancer / Proxy Math

```
NGINX as reverse proxy:
  Memory: ~2.5MB per 10K idle connections
  CPU: ~1 core per 50K requests/sec (simple routing)
  Max connections: ~10K-50K per worker (depends on keepalive)
  Max throughput: ~10-20 Gbps per instance (single-threaded per worker)

HAProxy:
  Memory: ~15KB per connection (asymmetric — 1KB frontend, 14KB backend)
  CPU: ~1 core per 30K req/sec
  Max connections: ~100K (recommended), 1M+ possible (memory heavy)

Envoy:
  Memory: ~30-50MB base + ~1KB per connection
  CPU: ~1 core per 20K req/sec (with mTLS + observability)
  Threading model: worker per core (Linux) or goroutine-style (thread per connection)
  Config overhead: ~100ms to reload config (not per-request)

L4 (TCP) vs L7 (HTTP) load balancing:
  L4: less resource intensive (no header parsing)
     Throughput: ~10× higher than L7
     Use: database load balancing, memcached, any TCP protocol
  L7: more features (routing, headers, cookies)
     Use: HTTP APIs, gRPC, WebSocket

Quick sizing:
  100K QPS on L4 HAProxy: ~3-4 cores, ~2GB RAM → $140/month (2× m5.large)
  100K QPS on L7 NGINX: ~4-6 cores, ~4GB RAM → $280/month (2× m5.xlarge)
  100K QPS on Envoy with mTLS: ~8-12 cores, ~8GB RAM → $560/month
```

### DNS Resolution Overhead

```
DNS lookup time:
  First lookup (cache miss): 20-50ms (recursive resolver)
  Subsequent lookups (cache hit): <1ms (local cache)
  TTL: 60-300 seconds typical

For 10K QPS, if every request does DNS:
  10K × 50ms = 500 seconds of DNS wait per second → 500 parallel lookups
  But: DNS is cached. Real DNS QPS is much lower.
  ~1 lookup per new connection × connection reuse rate

Connection reuse (keep-alive):
  HTTP/1.1: reuse for ~5-30 seconds (browser default)
  HTTP/2: multiplexed, reuse for minutes
  gRPC: long-lived, reuse for hours

DNS resolution per actual request:
  10K QPS, 10 requests per connection → 1K DNS lookups/sec
  Cache hit rate: 95% → 50 real DNS queries/sec → trivial

But: DNS-based load balancing (DNS returns different IPs per request):
  Each DNS response rotates IPs → clients may not cache as aggressively
  TTL = 60 seconds: clients re-resolve every 60s → 10K/60 ≈ 170 DNS/sec
  For 500M users: 500M/60 ≈ 8M DNS queries/sec → expensive
  Solution: use anycast (same IP, BGP routing) instead of DNS-based LB
```

### Distributed Lock / Consensus Overhead

```
ZooKeeper:
  Write throughput: ~10K ops/sec per ensemble (limited by leader)
  Read throughput: ~100K ops/sec (any node can serve reads)
  Latency: 2-5ms per write (ZAB protocol, majority commit)
  Session timeout: 10-30s typical
  Node count: 3 or 5 (quorum: majority)

etcd:
  Write throughput: ~10K ops/sec per cluster
  Read throughput: ~100K ops/sec (with quorum reads) or ~1M (serialized)
  Latency: ~2ms writes (Raft, same DC), ~50-100ms multi-region
  Node count: 3 or 5

Redis RedLock:
  Write throughput: ~50K locks/sec per Redis node (single-threaded)
  5-node RedLock: ~10K-20K locks/sec (slowest node determines throughput)
  Latency: ~1ms per lock acquisition (lightweight compared to ZK/etcd)
  Controversial: not formally proven safe, but widely used in practice

When you need a distributed lock:
  Rate: 100 locks/sec → any solution works
  Rate: 1K locks/sec → Redis RedLock (ZK too slow, 10K write limit)
  Rate: 10K locks/sec → shard locks by key across Redis nodes
  Rate: 100K locks/sec → don't use distributed locks, rethink design
```

### Data Archival / Tiering Estimation

```
Hot data (accessed daily):
  Performance tier: SSD/NVMe + cache
  Cost: ~$0.20/GB/month (provisioned IOPS)

Warm data (accessed weekly/monthly):
  Performance tier: HDD or lower-cost SSD
  Cost: ~$0.05/GB/month

Cold data (accessed yearly/compliance):
  Storage tier: S3 Glacier / Azure Archive
  Cost: ~$0.004/GB/month (Glacier Deep Archive)
  Retrieval time: 12-48 hours (free tier) or minutes (premium)

Example: Payment system with 7-year retention
  Year 1-2 (hot): 10TB × $0.20 = $2,000/month
  Year 3-5 (warm): 30TB × $0.05 = $1,500/month
  Year 6-7 (cold): 20TB × $0.004 = $80/month
  Total monthly: ~$3,580

Without tiering (all hot): 70TB × $0.20 = $14,000/month
Savings: ~75% → $125K/year for a modest system

Staff+ move: "We save $125K/year with a data lifecycle policy.
             Define hot/warm/cold at requirements time, not after deployment."
```

### Container / Pod Resource Estimation

```
Kubernetes pod density per node:
  Node type: m5.xlarge (4 vCPU, 16GB RAM)
  Average pod resource: 0.5 vCPU, 1GB RAM
  Max pods: 4 vCPU / 0.5 = 8 pods (CPU bound) or 16GB/1GB = 16 pods (memory bound)
  Realistic: ~8-10 pods per node (leaving room for OS, kubelet, daemonsets)

Node sizing:
  Many small pods (microservices): 4-8 vCPU nodes (easier bin packing)
  Large pods (databases, ML): 16-64 vCPU nodes (less overhead per pod)

CPU overcommit:
  Kubernetes allows CPU overcommit (requests vs limits)
  Typical ratio: 3:1 (request 0.5, limit 1.5)
  Risk: CPU starvation if all pods peak simultaneously
  For latency-sensitive: no overcommit (requests = limits)
  For batch/background: 5:1 overcommit is fine

Memory overcommit:
  Dangerous — OOMKiller kills pods
  Best practice: no memory overcommit for stateful services
  For stateless: 1.2-1.5× overcommit with good monitoring

Quick cluster sizing:
  Microservice: 50 pods × 0.5 vCPU × 1GB = 25 vCPU + 50GB
    → 4× m5.xlarge nodes: 16 vCPU, 64GB → done
  With HA (3×): 12× m5.xlarge → ~$2,500/month (on-demand)
```

### CI/CD Pipeline Estimation

```
Build time estimation:
  Java (Maven/Gradle): 
    Clean build: 2-5 minutes (small), 10-20 minutes (large monorepo)
    Incremental: 30-60 seconds
    Docker image build: +1-3 minutes
    Total: ~5-15 minutes per build

  Go:
    Clean build: 10-60 seconds
    Docker image: +30-60 seconds
    Total: ~1-2 minutes (fastest ecosystem for builds)

  Python:
    No compilation (interpreted) → no build time
    But: dependency install + lint + tests
    pip install: 1-3 minutes (cached: 10-30 seconds)
    Tests: 1-10 minutes
    Total: ~2-15 minutes

  TypeScript (React frontend):
    tsc + vite build: 30-120 seconds (depends on project size)
    Docker image: +30-60 seconds
    Total: ~1-3 minutes

Compute for CI/CD:
  200 engineers, 10 builds/day each = 2,000 builds/day
  2,000 × 10 min avg × 4 vCPU = 20,000 vCPU-minutes/day
  Using 32-vCPU runners: 625 runner-minutes/day → 10.4 runner-hours/day
  Cost: ~$0.10/vCPU-hour → ~$65/day → ~$2K/month (CI/CD compute)

Artifact storage:
  Docker images per build: ~500MB compressed
  2,000 images/day × 500MB = 1TB/day
  Retention: 30 days → 30TB
  Cost: 30TB × $0.023/GB = $690/month (S3)
  Or: use Docker registry with cleanup (keep last 10 per branch)
```

### Data Lake / Warehouse Estimation

```
Data ingestion:
  100 services × 100 events/sec = 10K events/sec
  Each event: 1KB JSON → 10MB/sec → 860GB/day → 300TB/year

Raw storage (S3):
  300TB × $0.023 = $6,900/month (S3 standard)
  After 90 days, move to S3 Infrequent Access: $3,750/month
  After 365 days, archive: $1,200/month (Glacier Deep Archive)

ETL compute:
  Spark cluster: 10 nodes × 16 vCPU × 64GB
  Processing 1TB/day with Spark: ~1-2 hours
  Cost: 10 × $0.50/hr = $5/hr → $5-10/day → $150-300/month
  (Spot instances: ~$1.50/hr → $45-90/month)

Query compute (ad-hoc analytics):
  Trino/Presto on 5 nodes: ~10TB scanned per hour
  Most queries scan 100GB-1TB → complete in 1-10 minutes
  Cost per analyst query: ~$0.01-0.10 (serverless pricing)

Back-of-envelope:
  "Data pipeline: 10K events/sec → 860GB/day → 300TB/year.
   Storage cost: ~$7K/month raw → $4K/month tiered.
   Compute: ~$300/month on Spark spot."
```

### Estimating for "Unusual" Systems

```
Voting / Polling system (Super Bowl, 100M votes in 3 hours):
  Peak write QPS: 100M / (3 × 3600) ≈ 9,250 writes/sec
  But: Super Bowl happens in bursts. 50% of votes in final 10 minutes.
  Peak: 50M / 600 ≈ 83,000 writes/sec
  This is high. Need: Kafka at ingress (buffers 83K/sec), 
  then batch write to DB (throttled at 1K/sec).
  Design: "accept fast, persist slow"

Real-time leaderboard (100M players, top 100 shown):
  Updates: 10M players × 1 score update/min = 166K updates/sec
  Reads: 1M people view leaderboard/min = 16K reads/sec
  Challenge: sorted leaderboard at 166K writes/sec is O(log N) per write
  Solution: Redis sorted set with approximate ranking
  Or: only accept top 1000 scores, recalculate every 30 seconds
  Estimate: 166K writes/sec needs sharding. Shard by score range → 100 partitions × 1.6K writes/sec

Collaborative editing (Google Docs, 100M users):
  Per document: 2-100 users editing simultaneously
  Ops per user: ~1 op/second (keystroke)
  Concurrent ops for popular doc: 100 ops/sec → 100 ops/sec to one document
  Solution: CRDT (no central ordering), OT (central ordering, latency sensitive)
  Storage per doc: 1K ops × 50 bytes × session length ≈ 50KB per active session
  This is why Google Docs uses OT with a central server: simpler than CRDT at scale
```

### The "Rules of Thumb" Consolidated Table

```
┌─────────────────────────────────────────────────────────────────┐
│                 BACK-OF-ENVELOPE RULES OF THUMB                  │
├───────────┬─────────────────────────────────────────────────────┤
│ Category  │ Rule                                                │
├───────────┼─────────────────────────────────────────────────────┤
│ Scale     │ DAU = 10-50% of MAU (25% if unknown)                │
│           │ Peak = 2-5× average (3× if unknown)                 │
│           │ 1B req/day ≈ 11K QPS avg                            │
├───────────┼─────────────────────────────────────────────────────┤
│ Storage   │ 1K records/sec × 1KB × 1 year ≈ 30TB                │
│           │ 1 photo upload/sec × 2MB × 1 year ≈ 60TB            │
│           │ S3 cost: $23/TB/month, EBS: $80/TB/month            │
├───────────┼─────────────────────────────────────────────────────┤
│ DB        │ Postgres < 5K write/sec, < 50K read/sec per node    │
│           │ Cassandra < 50K write/sec per node (log-structured) │
│           │ Redis < 100K ops/sec per node (single-threaded)     │
│           │ Indexes add 20-50% storage overhead                 │
├───────────┼─────────────────────────────────────────────────────┤
│ Network   │ 1 Gbps ≈ 125 MB/s, 10 Gbps ≈ 1.25 GB/s             │
│           │ Cross-region latency 50-200ms                       │
│           │ DNS TTL: 60-300s, can't invalidate instantly        │
├───────────┼─────────────────────────────────────────────────────┤
│ Caching   │ Cache hit ratio: 80-95% for hot data                │
│           │ TTL: 5-60 min for most content                      │
│           │ Memory-mapped cache is 10× faster than network      │
├───────────┼─────────────────────────────────────────────────────┤
│ Languages │ Go/Java: 10-50K QPS per instance                    │
│           │ Python sync: 1K QPS per instance (3× more costly)   │
│           │ Node: 5-20K QPS per instance                        │
├───────────┼─────────────────────────────────────────────────────┤
│ Compute   │ 1 vCPU ≈ 100-200 API calls/sec (simple)             │
│           │ 1 vCPU ≈ 10-20 ML inferences/sec (small model)      │
│           │ Docker overhead: negligible (<1% CPU)               │
├───────────┼─────────────────────────────────────────────────────┤
│ Reliability│ 99.9% → 8.76 hr/yr, 99.99% → 52 min/yr            │
│           │ RTO < 1hr needs hot standby, < 15min needs active   │
│           │ MTTR for most incidents: 30 min-2 hr                │
├───────────┼─────────────────────────────────────────────────────┤
│ Cost      │ 1M API calls on Lambda: ~$2.50                      │
│           │ 1 server on EC2: $50-150/month                      │
│           │ Data egress: $0.09/GB (most expensive hidden cost)  │
│           │ Egress cost often exceeds compute + storage combined │
└───────────┴─────────────────────────────────────────────────────┘
```

This is Topic 1 of ~29. Continue with Topic 2 (Core Building Blocks: API Gateway, Load Balancer, Reverse Proxy) when ready.
