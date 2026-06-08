---
title: Latency Deep Dive - L5 Fundamentals
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# Latency Deep Dive - L5 Fundamentals

> **[🎨 View Interactive Diagram](latency-architecture.html)** | [← Back to Index](../../systems-index.html)

*"Why does your 100ms service feel slow? Where did the other 99ms go?"*

---

## 1. Problem Statement

**Core Question:** Why do fast components produce slow systems?

When you have a 10ms database query, 5ms network roundtrip, 2ms application logic, and 1ms caching layer, why does the user experience 200ms latency?

Answer: Cascading delays, queueing, and hidden overhead.

---

## 2. Real World Analogy

**Restaurant Service:** Imagine a fine dining restaurant where:
- Chef prepares dish: 5 minutes
- Waiter carries plate: 1 minute
- Customer eats: 20 minutes

Total service time: 26 minutes. But if 100 customers arrive simultaneously:
- Waiter can only carry 1 plate at a time → customers wait 100 minutes for their food
- Kitchen has 3 ovens → dishes queue, waiting for space
- Bathroom has 1 stall → customers queue

**Latency = service time + queueing delay**

---

## 3. Why Problem Exists

### Sources of Latency

**A. Network Roundtrips**
```
Client → Server: 10ms
Processing: 1ms
Server → Client: 10ms
Total: 21ms (but you measure 50ms because of packet loss, retransmits, TCP slow start)
```

**B. Queueing**
- Tasks arrive faster than server can process
- Example: 100 requests arrive in 1s, server handles 50/s
- First 50: 0ms wait. Requests 51-100: up to 50ms wait
- Tail latency (P99) explodes

**C. Synchronous Dependencies**
```
Request blocks on 3 services:
  Service A: 10ms
  Service B: 10ms
  Service C: 10ms
Total: 30ms (serial)

Even if each is "fast", serial adds up
```

**D. GC Pauses**
- JVM stop-the-world: 50-200ms pause (young gen), 2000ms (full GC)
- During pause: no requests processed
- Causes traffic jams downstream

**E. Disk I/O**
- SSD random read: 100µs
- HDD random read: 10ms
- But contention → multiple requests wait for disk

**F. Lock Contention**
- Thread A holds lock
- Threads B, C, D wait
- Latency = lock wait time + service time

---

## 4. Naive Approach

**"Make everything fast"**

- Buy faster hardware
- Optimize code hot paths
- Use caching
- Parallel processing everywhere

Problems:
- Ignores queueing (Queueing Theory 101)
- Doesn't measure where time actually goes
- Assumes components work in isolation (they don't)

---

## 5. Why Naive Fails

### The Queueing Trap

Assume 10ms response time per request. Server has 1 worker thread.
- Arrival rate: 120 req/s
- Service rate: 100 req/s (10ms each)
- **Utilization: 120%** → queue grows infinitely

At 95% utilization (10% headroom):
- Average queue wait: ~2 seconds
- P99 wait: 10+ seconds

**Moral:** Optimizing individual components doesn't help if you're bottlenecked at queueing layer.

### The Little's Law Wall

```
L = λ × W

L = average number in queue
λ = arrival rate
W = average wait time

If λ grows 10x, W grows 10x (all else equal)
```

Cannot escape by making service time faster if you can't increase capacity proportionally.

### Cascade Failures

When one service slows:
- Upstream services accumulate requests
- Timeouts trigger retries
- Retries amplify load
- Entire system degrades

---

## 6. Evolution / Progression

### Stage 1: Monolithic + Caching (0-100ms P99)
- Single application
- Redis cache in front
- Database primary bottleneck

Latency breakdown: 5ms app + 5ms DB + 10ms network overhead = 20ms (P50), 50-100ms (P99)

### Stage 2: Service Decomposition (100ms-500ms P99)
- Split into microservices
- Add service-to-service calls
- Batch requests to reduce roundtrips

Latency breakdown: 5ms app + 10ms RPC to service A + 10ms RPC to service B + 5ms DB + 20ms queueing = 50ms (P50), 500ms+ (P99)

### Stage 3: Async + Caching (500ms-2s P99)
- Decouple critical paths
- Return early responses
- Complete work asynchronously

Latency breakdown: 5ms app + 2ms cache lookup + return = 7ms (P50), 50ms (P99 with cache miss)

### Stage 4: Low-Latency Infrastructure (2s-10s+ P99)
- Edge caching (CDN, local replicas)
- Connection pooling + HTTP/2 multiplexing
- Speculative execution
- Predictive precomputation

Latency breakdown: 1ms edge response + <1ms network = <2ms (P50), <10ms (P99)

---

## 7. Production Architecture

```
Client Request
    │
    ├─→ [CDN Cache] ← Hit: 1ms latency
    │
    ├─→ [API Gateway]
    │   ├─ Rate limiting
    │   ├─ Request deduplication
    │   └─ Connection pooling
    │
    ├─→ [Load Balancer]
    │   ├─ Least-loaded routing
    │   └─ Timeout enforcement
    │
    ├─→ [Application Layer]
    │   ├─ In-process cache (L1)
    │   ├─ Parallel RPC (non-blocking)
    │   ├─ Request deadline propagation
    │   └─ Circuit breaker (fail fast)
    │
    ├─→ [Downstream Services]
    │   ├─ Timeouts (2s standard)
    │   └─ Fallback to cached result
    │
    └─→ [Database]
        ├─ Connection pool
        ├─ Query cache (10-100ms results)
        └─ Read replicas
```

---

## 8. Components

### Request Tracing System
**What:** Distributed tracing (X-Trace, Jaeger, Datadog APM)

**Purpose:** Attribute latency to specific components

```
Request:
  API → Service A (5ms) → Service B (50ms) → DB (100ms) → Response
  Total: 155ms

Identifying 50ms in Service B as anomaly enables targeted fix
```

### Deadline Propagation
**What:** Pass time budget through microservices

```go
ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
defer cancel()

// Service A: 20ms budget
resp1, _ := svcA.Call(ctx)

// Service B: 80ms remaining
resp2, _ := svcB.Call(ctx)
// If 20ms passed, Service B gets 60ms deadline
```

**Benefit:** Fast-fail if we can't meet user deadline

### Adaptive Queueing
**What:** Reject requests when queue grows too deep

```
Max queue depth: 1000
Current queue: 900
Incoming request would wait 9 seconds
→ Reject with 503 (overloaded)
→ Client retries elsewhere / falls back to cache
```

---

## 9. Internal Working

### Anatomy of a Request

```
t=0ms:     Client sends SYN
t=10ms:    Server receives (network latency)
           Server sends SYN-ACK

t=20ms:    Client receives (network latency)
           Client sends HTTP GET (piggybacked with ACK)

t=30ms:    Server receives request
           TCP: already established (if persistent connection)
t=31ms:    Application code starts
t=36ms:    DB query sent
t=46ms:    DB response received
t=47ms:    Application generates response
t=48ms:    Response sent to client

t=58ms:    Client receives response

Total User-Perceived Latency: 58ms
```

### Queueing Model

```
M/M/c queue (Poisson arrivals, exponential service, c workers):

Utilization ρ = λ / (c × μ)
  λ = arrival rate (requests/sec)
  μ = service rate per worker (requests/sec)
  c = number of workers

Average wait time in queue:
  W = (1 / (c × μ × (1 - ρ))) × (ρ^c / (c! × (1-ρ)))

Example:
  λ = 900 req/s
  μ = 100 req/s per worker
  c = 10 workers
  ρ = 900 / (10 × 100) = 0.9

  W ≈ 0.9 seconds (average queueing delay!)
```

### Percentile Behavior

```
Response times (1000 requests):
  P50: 5ms (50% finish in 5ms)
  P95: 25ms (95% finish in 25ms)
  P99: 150ms (99% finish in 150ms, 1% take 150ms+)
  P999: 500ms

User perceives slowest experience: P99
  → Optimizing P50 doesn't fix user complaints
```

---

## 10. Request Lifecycle

**User perspective:**

1. User clicks button (t=0)
2. Browser renders page → sends request
3. **Network delay to server: 10-50ms**
4. Server receives request
5. **API gateway processing: 1-5ms**
6. **Application logic: 5-20ms**
7. **Downstream calls (if parallel): max(latency of each) = 10-50ms**
8. **Database query: 5-100ms**
9. **Response serialization: 1-5ms**
10. Server sends response
11. **Network delay to client: 10-50ms**
12. Browser renders response
13. **JavaScript execution: 50-500ms** (rendering, layout, paint)

**Total "perceived" latency: 100ms-2s** (even with 50ms backend)

---

## 11. Data Flow

### Single Request Through System

```
Time (ms)  Component           Action              Latency
0-10       Network             Request transit     10ms
10-15      Load Balancer       Route decision      5ms
15-20      API Layer           Auth check          5ms
20-25      Cache L1            Check hot data      5ms (hit: return)
25-30      Request Router      Service selection   5ms
30-35      RPC Client          Connection pool     5ms (pooled)
35-45      Network             RPC roundtrip       10ms
45-50      Service B           Business logic      5ms
50-60      Database            Query execution     10ms
60-65      Database            Network roundtrip   5ms
65-70      Service B           Response building   5ms
70-80      Network             RPC response        10ms
80-85      Cache Layer         Store result        5ms
85-90      Response Encoding   JSON serialization  5ms
90-100     Network             Response transit    10ms

Total: 100ms (serial), less if parallelized
```

### What Slows Down Traffic

```
Early morning (low traffic):
  - Requests arrive: 10 req/sec
  - Servers process: 100 req/sec each
  - Queue: 0
  - Wait time: 0
  - P99 latency: 10ms

Peak traffic (shopping event):
  - Requests arrive: 10,000 req/sec
  - Servers process: 100 req/sec each
  - Need: 100 workers to keep up
  - But have: 50 workers
  - Queue: 5000 requests
  - Wait time: 50 seconds per request
  - P99 latency: 50+ seconds
```

---

## 12. Key Strategy

### 1. Measure First
**Establish baseline:**
- P50, P95, P99, P999 latency
- Where time goes (service breakdown via tracing)
- Bottleneck components

**Typical target:** <100ms P99 for user-facing APIs

### 2. Identify Bottleneck
**Find:** Which service/operation consumes most time?

Example: 40ms of 100ms total in database queries
- Optimize there, not in rendering

### 3. Eliminate Queueing
**Strategies:**
- Scale workers to match traffic
- Use bounded queues (fail fast)
- Implement backpressure

### 4. Parallelize Serial Calls
```
Serial: A (10ms) → B (10ms) → C (10ms) = 30ms
Parallel: A, B, C in parallel = 10ms (max of three)
```

### 5. Push to Edge
**Move computation closer to users:**
- Cache at CDN edge
- Precompute results
- Use local replicas

---

## 13. Failure Scenarios

### Scenario 1: Cascading Timeouts
```
Client timeout: 5s
Service A timeout to B: 3s
Service B timeout to DB: 1s

Burst of slow queries (DB overloaded):
  - DB responds in 2s (timeout!)
  - B times out B's callers
  - A times out client requests
  - Upstream sees failures / timeouts
  - Increases load (retries)
  - More failures

Result: Entire system appears down, even though DB is just slow
```

**Fix:** Deadline propagation, circuit breakers, fallback to cache

### Scenario 2: GC Pauses
```
Java service with 4GB heap, 100 req/sec, 10ms avg response time

GC full pause: 200ms

During pause:
  - No requests processed
  - 100 req/sec × 0.2s = 20 requests piled up
  - When GC completes, 20 requests process in 200ms
  - Downstream sees spike

Frequent full GCs → systematic latency increase
```

**Fix:** Tune heap size, use low-latency GC (ZGC, Shenandoah), or language choice

### Scenario 3: CPU Throttling
```
Server overheated → CPU throttles to 70%

Requests that took 10ms now take 14ms (30% slower)
P99 goes from 50ms → 70ms
P999 goes from 200ms → 300ms

User experience degrades
```

**Fix:** Monitor CPU temperature, thermal management, better cooling

### Scenario 4: Tail at Scale
```
User request fans out to 100 backend services
Each has P99 latency: 100ms

Probability all 100 finish within 100ms: (0.99)^100 ≈ 37%
Most requests will hit slowest service

P99 of fan-out: 5+ seconds (even though individual P99 is 100ms)
```

**Fix:** Hedged requests, request multiplication, adaptive timeouts

---

## 14. Bottlenecks Table

| Bottleneck | Latency Impact | Symptoms | Quick Fix |
|---|---|---|---|
| Network roundtrips | 10-50ms per RPC | Lots of microservices | Reduce RPC calls, batch requests |
| Database queries | 5-100ms | Slow queries, high CPU | Index missing fields, query optimization |
| Lock contention | 10-1000ms | Thread stalls, CPU underutilized | Reduce critical section, use concurrent structures |
| Queueing | 1-60s | Variable latency, high variance | Scale workers, shed load |
| GC pauses | 50-2000ms | Periodic spikes, predictable patterns | Tune heap, change language |
| CPU throttling | 10-50% slowdown | Consistent slow-down under load | Better cooling, CPU isolation |
| Network congestion | 20-200ms | Packet loss, retransmits | Upgrade bandwidth, optimize packet size |
| Disk I/O | 100µs-10ms per access | Sustained high latency | SSD cache, batch writes |
| Memory bandwidth | 1-5ms per large transfer | Spiky latency | Compression, reduce payload size |
| Serialization | 1-10ms | CPU spike, larger payloads | Protocol buffers, binary format |

---

## 15. Monitoring

### Key Metrics

```
Latency Distribution:
  ✓ Measure: P50, P95, P99, P999 (not average!)
  ✓ Dashboard: Histogram of request times
  ✓ Alert: P99 > 500ms

Breakdown by Component:
  ✓ API layer latency (application logic)
  ✓ Database latency (query time)
  ✓ Network latency (RPC roundtrip)
  ✓ Queue depth (waiting requests)

Service Health:
  ✓ Error rate (4xx, 5xx)
  ✓ Timeout rate (% requests exceeding deadline)
  ✓ Traffic rate (requests/sec)
```

### Distributed Tracing

```
Trace example (request A):
  Request A (0-100ms)
    ├─ API gateway (0-5ms)
    ├─ Service B call (5-55ms)
    │   ├─ Network (5-15ms)
    │   ├─ Service B processing (15-50ms)
    │   │   ├─ Auth (15-20ms)
    │   │   ├─ DB query (20-45ms)
    │   └─ Response (50-55ms)
    ├─ Cache update (55-60ms)
    └─ Client response (60-100ms)

Trace identifies: DB query took 25ms, largest single component
```

### Red Flags

- P99 increasing while P50 stable → tail latency growing
- Variable latency → queueing or GC
- Correlated spikes → cascading failures or resource saturation
- Increasing variance → system approaching saturation

---

## 16. Optimizations

### 1. Connection Pooling
```go
// Bad: new connection per request
func handleRequest(w http.ResponseWriter, r *http.Request) {
    db, _ := sql.Open("mysql", dsn) // NEW CONNECTION
    defer db.Close()
    // Query...
}

// Good: reuse connections
var dbPool *sql.DB
func init() {
    dbPool, _ = sql.Open("mysql", dsn)
    dbPool.SetMaxOpenConns(100)
    dbPool.SetMaxIdleConns(50)
}
func handleRequest(w http.ResponseWriter, r *http.Request) {
    dbPool.QueryRow(...) // POOLED
}
```

**Benefit:** 50-100ms saved per request (avoid TCP handshake + SSL negotiation)

### 2. Request Batching
```
Before: 100 requests, each gets own DB query (100 queries, 100ms each)
After: Batch 100 requests into 1 query (1 query, 100ms total)
→ 100x throughput improvement
```

### 3. Caching at Multiple Layers
```
L1 Cache (in-process): 0.1ms hit latency (milliseconds of data)
L2 Cache (Redis): 1ms hit latency (minutes of data)
L3 Cache (CDN): 5-20ms hit latency (hours of data)
Database: 10-100ms (source of truth)

Hit rate:
  L1: 70% → 70% of requests: 0.1ms
  L2: 20% → 20% of requests: 1ms
  L3: 7% → 7% of requests: 20ms
  DB: 3% → 3% of requests: 50ms
Average: 0.70×0.1 + 0.20×1 + 0.07×20 + 0.03×50 ≈ 3ms
```

### 4. Parallelism
```
Service needs: user info + recommendations + ads + social graph

Serial: 10 + 15 + 8 + 12 = 45ms
Parallel: max(10, 15, 8, 12) = 15ms

Speedup: 3x (but now dealing with failures, timeouts)
```

### 5. Early Returns
```
User requests: product page
Order of operations:
  1. Get product (5ms) — return this
  2. Get reviews (100ms) — lazy load
  3. Get similar products (80ms) — lazy load

Return at step 1, fetch 2 & 3 in background
User sees page in 5ms instead of 185ms
```

### 6. Protocol Optimization
```
HTTP/1.1: 1 request per connection (sequential)
HTTP/2: Multiplex 100 requests over 1 connection
  → Each RPC: 10ms network
  → Serial: 100 × 10ms = 1s
  → Multiplexed: max(10ms) = 10ms
```

### 7. Speculative Execution
```
User clicks "search"
System can predict: likely query is autocomplete suggestion

Speculatively fetch results for top 3 suggestions
User picks suggestion → results already cached
Instant response (1-5ms instead of 100ms)
```

---

## 17. Security

### 1. DDoS & Latency
```
Attack: Send 1M requests/sec
System: Can handle 100K req/sec

Result:
  - Queue depth: 9M requests
  - Average wait: 90 seconds per request
  - Legitimate users: severe latency

Mitigation:
  - Rate limiting per IP (1000 req/s max)
  - Shed load at edge (fail-open or drop)
  - Anycast (distribute across global edge)
```

### 2. Slowloris Attacks
```
Attack: Send partial HTTP requests slowly
  GET /large-file HTTP/1.1\r\n
  [wait 30s]
  Header: value\r\n
  [wait 30s]
  ...

Server waits for complete request (holding connection)
Attacker ties up all server connections

Latency: Legitimate users get no connection
```

**Fix:** Connection timeouts, max header size limits

### 3. Request Deduplication for Idempotency
```
Request A (ID=1234) arrives
  → Processing (takes 100ms)
  → Response sent

Request A (ID=1234) arrives again (retry)
  → Return cached response (0ms)
  → Same semantics

Without dedup: Request processed twice, database corrupted
```

---

## 18. Tradeoffs Table

| Approach | Latency Improvement | Cost | Complexity |
|---|---|---|---|
| Caching | 10-100x (hit) | Memory, invalidation logic | Medium |
| Service decomposition | 3-5x (parallelization) | Operational, network calls | High |
| Batching | 10-100x (throughput) | Latency variance, complexity | Medium |
| Database sharding | 5-20x (read scalability) | Consistency, operational | High |
| Connection pooling | 10-50x (per request) | Memory | Low |
| Protocol optimization (HTTP/2) | 2-5x (multiple requests) | Complexity | Medium |
| Early response + background work | 5-10x | Inconsistency, complexity | Medium |
| Speculative execution | 50-200x (hit rate 30%) | Over-processing, power | High |
| CDN edge caching | 5-10x | Geographic distribution | Medium |

---

## 19. Alternatives

### Real-Time vs Batch Latency
```
Real-time system:
  - User clicks → instant response (100ms)
  - Requires: fast infrastructure, expensive

Batch system:
  - Precompute results offline (1s)
  - Serve from cache (1ms)
  - Staleness acceptable

Trade: Latency vs Infrastructure cost
```

### QoS vs Infrastructure Cost
```
Ultra-low latency: <10ms P99
  - Requires: custom hardware, single-digit machine count, expensive ops
  - Used for: High-frequency trading, real-time auctions

Low latency: <100ms P99
  - Requires: good cloud setup, moderate scaling
  - Used for: Web apps, mobile apps

Acceptable latency: <1s P99
  - Requires: standard infrastructure, auto-scaling
  - Used for: Batch reports, background jobs
```

### Optimistic vs Pessimistic
```
Optimistic (assume success):
  - Send request, assume response arrives
  - If timeout, retry or fallback
  - Latency: Low (no blocking), but variance high

Pessimistic (guarantee success):
  - Get lock before read
  - Ensure consistency before returning
  - Latency: Consistent but higher
```

---

## 20. When NOT to Use

### Don't Optimize Latency When:

1. **Cost not worth it**
   - Reducing latency from 500ms → 100ms costs 10x infrastructure
   - Users don't care about < 1s for batch processes
   - Not user-facing

2. **Algorithm is bottleneck**
   - Service in 5ms, but algorithm is O(n²)
   - Fix algorithm first, not infrastructure

3. **Premature optimization**
   - System not deployed yet
   - No performance baselines
   - Measure first, optimize second

4. **Consistency or correctness required**
   - Eventual consistency saves latency
   - But CAP theorem: trade consistency for low latency
   - If consistency required, don't sacrifice it

5. **Operations complexity not worth it**
   - Speculative execution saves 50ms but adds 20% complexity
   - Onboarding, debugging costs higher than benefit

---

## 21. Interview Questions

1. **Design a system with <100ms P99 latency at 1M QPS**
   - What's your approach to eliminate bottlenecks?
   - How do you handle tail latency?
   - What monitoring would you set up?

2. **Your system latency spiked from 50ms → 500ms P99**
   - How would you diagnose the problem?
   - What tools would you use?
   - What are top 3 likely causes?

3. **Database query takes 100ms, service has 500ms budget, but 50% of requests timeout**
   - Why? (Queueing)
   - How to fix?
   - Trade-offs?

4. **Compare caching vs sharding for reducing latency**
   - When use each?
   - What are failure modes?
   - Consistency implications?

5. **Your P99 latency is high, but P50 is low. What's happening?**
   - Heavy tail (GC pauses, occasional slowness)
   - How to identify root cause?
   - Solutions?

---

## 22. Common Mistakes

1. **Optimizing P50 instead of P99**
   - If 1% of users experience 10s latency, they churn
   - Focus on: P95, P99, P999

2. **Ignoring queueing**
   - Make each service 2x faster
   - But if 2x more traffic arrives, queue still grows
   - Need proportional scaling

3. **Using averages**
   - "Average latency 50ms" (meaningless)
   - Use percentiles: P50, P95, P99
   - Histogram is best

4. **Not measuring end-to-end**
   - Measure each service in isolation (10ms each)
   - But end-to-end is 500ms (why?)
   - Must trace full request

5. **Cascading failures from slow services**
   - Service A slow → timeouts propagate → entire system slow
   - Missing circuit breakers, fallbacks
   - Design: fast-fail if dependency is slow

6. **Forgetting network is the bottleneck**
   - Optimize code path (save 1ms)
   - But network calls (10ms each) dominate
   - Reduce RPC count, batch requests

---

## 23. Debugging Guide

### Step 1: Establish Baseline
```
Current state:
  API latency: 150ms P99
  Database latency: 50ms P99
  Network latency: 10ms (per RPC)

Question: Where is the 90ms going?
```

### Step 2: Instrument Tracing
```
Enable distributed tracing (Jaeger, Datadog)
Trace single slow request through system

Example slow request:
  API Gateway: 5ms
  Service B call: 100ms
    - Network: 10ms (2 RPC calls = 20ms expected, but actual 100ms?)
    - Service B logic: 50ms
    - DB query: 30ms
  Cache update: 10ms
  Response: 5ms
Total: 125ms

Issue: Service B call took 100ms (network + service logic + DB)
  - Network should be 10ms, but took time
  - Service B added 50ms (why?)
  - DB took 30ms

Next: Deep dive into Service B
```

### Step 3: Identify Bottleneck
```
Slow component: Service B DB query

Hypothesis: Missing index on frequently-queried column

Validation:
  EXPLAIN QUERY: shows full table scan (1000 ms potential)
  Fix: Add index on (user_id, timestamp)
  After: Query time: 5ms (was 30ms)

Result: Overall latency 150ms → 125ms
```

### Step 4: Repeat
```
Remaining: 125ms (was 150ms, saved 25ms)

Next target: Service B network latency

Current: RPC call takes 30ms per service
  - Expected: 10ms network + 5ms processing
  - Actual: 30ms

Issue: No connection pooling, new connection per RPC
Fix: Implement connection pooling

Result: 125ms → 100ms overall
```

---

## 24. Code Examples

### Go: Request Deadline Propagation
```go
func handleRequest(w http.ResponseWriter, r *http.Request) {
    // Propagate deadline from client context
    ctx, cancel := context.WithTimeout(r.Context(), 100*time.Millisecond)
    defer cancel()

    // Service A gets full budget
    start := time.Now()
    respA, err := svcA.Call(ctx)
    elapsed := time.Since(start)

    // Service B gets remaining budget
    remaining := time.Until(ctx.Deadline())
    if remaining < 10*time.Millisecond {
        http.Error(w, "deadline exceeded", http.StatusGatewayTimeout)
        return
    }

    respB, err := svcB.Call(ctx) // Uses remaining deadline
    // ...
}
```

### Go: Connection Pooling
```go
var dbPool *sql.DB

func init() {
    var err error
    dbPool, err = sql.Open("mysql", "user:pass@/dbname")
    
    // Tune for your workload
    dbPool.SetMaxOpenConns(100)        // Max connections in pool
    dbPool.SetMaxIdleConns(50)         // Keep 50 idle for reuse
    dbPool.SetConnMaxLifetime(5 * time.Minute) // Rotate old connections
    
    if err = dbPool.Ping(); err != nil {
        panic(err)
    }
}

func queryUser(id int64) (*User, error) {
    row := dbPool.QueryRowContext(context.Background(),
        "SELECT id, name FROM users WHERE id = ?", id)
    // ...
}
```

### Go: Parallel RPC Calls
```go
func fetchUserData(ctx context.Context, userID int64) (*UserData, error) {
    // Fan out to multiple services in parallel
    profileChan := make(chan *Profile, 1)
    recommendChan := make(chan []*Recommendation, 1)
    friendsChan := make(chan []*Friend, 1)
    
    // Start all 3 calls in parallel
    go func() {
        p, _ := svcProfile.Get(ctx, userID)
        profileChan <- p
    }()
    
    go func() {
        r, _ := svcRecs.Get(ctx, userID)
        recommendChan <- r
    }()
    
    go func() {
        f, _ := svcFriends.Get(ctx, userID)
        friendsChan <- f
    }()
    
    // Wait for all (max of 3 service latencies, not sum)
    profile := <-profileChan
    recs := <-recommendChan
    friends := <-friendsChan
    
    return &UserData{profile, recs, friends}, nil
}
```

### Go: Request Deduplication
```go
type RequestCache struct {
    mu    sync.RWMutex
    cache map[string]*CachedResponse
}

func (rc *RequestCache) Execute(reqID string, fn func() interface{}) interface{} {
    rc.mu.RLock()
    if cached, ok := rc.cache[reqID]; ok {
        rc.mu.RUnlock()
        return cached.Result
    }
    rc.mu.RUnlock()
    
    // First request processes
    result := fn()
    
    rc.mu.Lock()
    rc.cache[reqID] = &CachedResponse{
        Result:    result,
        Timestamp: time.Now(),
    }
    rc.mu.Unlock()
    
    // Clean old entries (older than 1 minute)
    // (background goroutine)
    
    return result
}

// Usage:
resp := cache.Execute("user:123:profile",
    func() interface{} {
        return db.GetProfile(123)
    },
)
```

---

## 25. Visual Diagrams

### Queueing Model
```
Arrival Rate λ = 100 req/s
Service Rate μ = 200 req/s (20 req/s per worker × 10 workers)
Utilization ρ = 0.5

Queue Length (L) = ρ² / (1 - ρ) = 0.25 / 0.5 = 0.5 requests
Wait Time (W) = 0.5s / 200 = 2.5ms

[Arrivals] ──→ [Queue] ──→ [Workers] ──→ [Output]
  100/s        0.5 req     10 workers      100/s
                (2.5ms)
```

### Latency Evolution
```
Latency (ms)  Progress
1000 │         ╱─────── Full GC (200ms pause)
     │        ╱
 500 │   ╱────╱
     │  ╱
 100 │╱─────────────── Stable (optimized)
     │
  10 │✓ Target
     └─────────────────────────────→ Time
       Initial  Optimize  Scale  Maintain
```

### Request Fan-Out Tail Latency
```
Request → 100 backend services
          Each P99 latency: 100ms

Probability all 100 finish ≤100ms: (0.99)^100 ≈ 37%

P99 of fan-out:
  [Request] ──→ [Svc 1] (10ms) ─┐
             ──→ [Svc 2] (150ms) ├─→ [Aggregate]
             ──→ [Svc 3] (20ms) ─┤
             ...
             ──→ [Svc 100] (95ms) ─┘

Result: max(10, 150, 20, ..., 95) = 150ms
  (Slowest service determines P99)
```

---

## 26. Simulation Ideas

1. **Queueing Simulator**
   - Input: arrival rate, service rate, num workers
   - Output: P50, P95, P99 latency, queue depth
   - Interactive: adjust parameters, see effect

2. **Little's Law Visualizer**
   - Show: L = λ × W
   - Adjust: arrival rate, watch queue grow
   - Demonstrate: why scaling matters

3. **Cascade Failure Simulator**
   - Service A slow → causes B to slow → causes C to slow
   - Show: how slowdown propagates
   - Demonstrate: circuit breaker value

4. **Latency Budget Allocator**
   - Total budget: 100ms
   - Services: A (10ms), B (20ms), C (5ms), Network (20ms)
   - Remaining: 45ms for overhead
   - If any service grows, others must shrink

5. **P99 vs P50 Comparison**
   - Show: optimizing P50 doesn't help P99
   - Focus on tail (P95+)
   - Identify GC pauses, queueing

---

## 27. Case Studies

### Case 1: Google Search at 10M QPS
**Problem:** Latency spiked to 1s P99 (target: 100ms)

**Root Cause:** Traffic peak during breaking news event. Hit query timeout (500ms queue depth × 2ms service = 1000ms wait)

**Solution:**
1. Deadline propagation (fail fast if can't meet deadline)
2. Circuit breaker (reject requests if backend slow)
3. Fallback to cache (cached results for popular queries)
4. Scale workers (add 2x capacity)

**Result:** P99 back to 150ms (still high), but recovered quickly

### Case 2: Netflix Streaming (High Bandwidth, Low Latency)
**Problem:** Video buffering on mobile networks (2G, 3G)

**Root Cause:** Large video chunks (10MB per segment), poor network = 30s wait per segment

**Solution:**
1. Adaptive bitrate (reduce quality on slow networks)
2. Smaller chunks (500KB instead of 10MB, faster initial segment)
3. Predictive prefetch (buffer next segment while watching current)
4. Regional CDN (serve from nearest geography)

**Result:** <2s startup time (was 10s), smooth playback

### Case 3: Amazon DynamoDB Latency
**Problem:** P99 latency 100ms (target: <10ms), but P50 is 2ms

**Root Cause:** Hot partitions (some users' data queried more than others, bottleneck at single partition)

**Solution:**
1. Better partitioning strategy (split hot keys)
2. Read replicas (replicate hot partitions across multiple servers)
3. DynamoDB adaptive partitioning (auto-detect and split)

**Result:** P99 down to 20ms, more consistent

---

## 28. Related Topics

- **Little's Law:** L = λ × W (latency driven by queue length)
- **Queueing Theory:** M/M/c models, arrival/service rates
- **Amdahl's Law:** Parallel speedup limited by serial components
- **Deadline Scheduling:** How to allocate time budget across services
- **Distributed Tracing:** Measuring latency across services
- **Load Testing:** Simulating latency under various traffic patterns

---

## 29. Advanced Topics

### Tail Latency in Distributed Systems
```
Problem: 100 services, each P99 = 100ms
→ System P99 ≈ 5000ms (not 100ms!)

Solutions:
  - Hedged requests: send request to 2 replicas, use first response
  - Backup requests: if no response in 80ms, send backup
  - Request replication: send to k services, use earliest
  - Adaptive timeout: adjust timeout based on observed latency
```

### Speculative Execution
```
User types "weather"
  Speculatively fetch 3 completions: "weather NYC", "weather API", "weather forecast"
User picks "weather NYC"
  → Result already in cache
  → Instant response

Cost: 3x compute for speculative requests, but 90% hit rate saves latency
```

### Deadline-Aware Routing
```
Request deadline: 100ms
Service A: 80ms (can accept)
Service B: 20ms (can accept)
Service C: 150ms (can NOT accept)

Route to A or B (and fallback if slow)
Skip C (would violate deadline)
```

---

## 30. Production Checklist

- [ ] Measure baseline latency (P50, P95, P99, P999)
- [ ] Identify bottleneck (which service consumes most time?)
- [ ] Set latency budget (max acceptable per service)
- [ ] Implement distributed tracing (measure where time goes)
- [ ] Enable connection pooling (all databases, RPC clients)
- [ ] Implement request deadline propagation (fail fast)
- [ ] Set aggressive timeouts on dependencies (<2s standard)
- [ ] Implement circuit breakers (don't cascade failures)
- [ ] Add caching (L1 in-process, L2 Redis, L3 CDN)
- [ ] Parallelize serial calls (fan out to services)
- [ ] Batch requests where possible (reduce RPC count)
- [ ] Monitor queue depth (alert if > 1000 items)
- [ ] Monitor GC pause time (alert if > 50ms)
- [ ] Dashboard for latency percentiles (auto-updated)
- [ ] Alert on P99 increase > 20% (relative to baseline)
- [ ] Load test with expected traffic (measure tail latency)
- [ ] Test failure scenarios (slow downstream, timeouts)
- [ ] Implement backpressure (shed load when overwhelmed)
- [ ] Plan for multi-region (reduce network latency geographically)
- [ ] Regular latency audits (quarterly, before major launches)

---

*Last Updated: 2026-05-28*

<!-- html-live -->
<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>
    .slider-title {color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:12px;letter-spacing:1px}
    .slider-container {display:flex;flex-direction:column;gap:12px}
    .slider-label {color:#e3eaf0;font-family:monospace;font-size:12px}
    .slider-wrapper {display:flex;align-items:center;gap:12px}
    .slider-input {flex:1;height:6px;border-radius:3px;background:#1e3a5f;outline:none;-webkit-appearance:none;appearance:none}
    .slider-input::-webkit-slider-thumb {-webkit-appearance:none;appearance:none;width:18px;height:18px;border-radius:50%;background:#00d4ff;cursor:pointer;box-shadow:0 0 8px #00d4ff;border:2px solid #0b0e14}
    .slider-input::-moz-range-thumb {width:18px;height:18px;border-radius:50%;background:#00d4ff;cursor:pointer;box-shadow:0 0 8px #00d4ff;border:2px solid #0b0e14}
    .slider-value {font-family:monospace;color:#34d399;min-width:80px;text-align:right;font-size:12px;font-weight:bold}
  </style>
  <div class="slider-title">Latency Impact: Network Distance</div>
  <div class="slider-container">
    <label class="slider-label">Network Distance (km):</label>
    <div class="slider-wrapper">
      <input type="range" min="0" max="15000" value="5000" class="slider-input" id="param-slider">
      <span class="slider-value" id="param-value">5,000 km</span>
    </div>
  </div>
  <script>
    const slider = document.getElementById('param-slider');
    const valueDisplay = document.getElementById('param-value');
    slider.addEventListener('input', (e) => {const val = parseInt(e.target.value); valueDisplay.textContent = val.toLocaleString() + ' km';});
  </script>
</div>

<!-- html-live -->
<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>
    .obs-title {color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px;letter-spacing:1px}
    .obs-grid {display:grid;grid-template-columns:repeat(auto-fit, minmax(150px, 1fr));gap:12px}
    .obs-card {padding:12px;background:#1a2332;border:1px solid #1e3a5f;border-radius:4px;display:flex;flex-direction:column;align-items:center;transition:all 0.3s}
    .obs-card:hover {border-color:#00d4ff;box-shadow:0 0 8px rgba(0, 212, 255, 0.3)}
    .obs-label {color:#a3aab8;font-family:monospace;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px}
    .obs-value {font-family:monospace;font-size:20px;font-weight:bold;margin-bottom:4px;letter-spacing:0.5px}
    .obs-unit {color:#a3aab8;font-family:monospace;font-size:10px;text-transform:uppercase}
    .metric-healthy {color:#34d399}
    .metric-warning {color:#fbbf24}
    .metric-critical {color:#ef4444}
  </style>
  <div class="obs-title">Latency Breakdown (5000km)</div>
  <div class="obs-grid">
    <div class="obs-card">
      <div class="obs-label">Network RTT</div>
      <div class="obs-value metric-warning">150</div>
      <div class="obs-unit">ms</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Cache Hit</div>
      <div class="obs-value metric-healthy">5</div>
      <div class="obs-unit">ms</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">DB Query</div>
      <div class="obs-value metric-warning">45</div>
      <div class="obs-unit">ms</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">P99 Latency</div>
      <div class="obs-value metric-warning">250</div>
      <div class="obs-unit">ms</div>
    </div>
  </div>
</div>
