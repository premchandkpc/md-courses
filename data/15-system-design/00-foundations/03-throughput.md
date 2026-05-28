# Throughput Deep Dive - L5 Fundamentals

> **[🎨 View Interactive Diagram](throughput-architecture.html)** | [← Back to Index](../../systems-index.html)

*"Your database can do 10K QPS, but system only handles 1K. Where did the other 9K go?"*

---

## 1. Problem Statement

**Core Question:** Why doesn't scaling linearly increase system throughput?

Observation: Single database can handle 100K QPS. Add 10 databases (shards). System now handles 50K QPS. Why not 1M?

Answer: Serialization bottlenecks, request routing, and resource sharing.

---

## 2. Real World Analogy

**Restaurant Kitchen:**
- Single chef: 20 dishes per hour (1 dish every 3 minutes)
- Hire 10 chefs: 150 dishes per hour (expected 200)

Why not linear?
- Single oven for 10 chefs → waitlist forms
- Single dishwasher → clean plates delay
- Single manager (orders, scheduling) → bottleneck
- Kitchen space → can't fit more equipment

Throughput = min(chef capacity, oven capacity, dishwashing, space)

---

## 3. Why Problem Exists

### A. Bottleneck Serialization
```
Request path:
  Load Balancer (1000 req/s) ← bottleneck!
    ↓
  API Layer (10K req/s)
    ↓
  Database Layer (100K req/s)

Throughput = min(1K, 10K, 100K) = 1K req/s
```

### B. Resource Contention
```
10 servers requesting same database resource:
  Server 1: acquires lock
  Servers 2-10: wait

Serialization: 10x slower than parallel
```

### C. Bandwidth Limitation
```
Network uplink: 1 Gbps (125 MB/s)
Average request size: 1 KB
Average response size: 10 KB
Total per request: 11 KB

Max throughput: 125 MB/s ÷ 11 KB ≈ 11,000 req/s

Can't exceed network bandwidth, no matter how fast service
```

### D. Synchronous Dependencies
```
Request requires responses from 3 services (serial):
  Service A: 10ms
  Service B: 10ms
  Service C: 10ms
Total: 30ms per request

Requests per second: 1000 ms ÷ 30 ms = 33 req/s

Throughput bottleneck: 33 QPS (even if each service can do 1000 QPS)
```

---

## 4. Naive Approach

**"Add more hardware"**

- Buy bigger servers
- Add more database shards
- Increase bandwidth

Problems:
- Doesn't address serialization (bigger server = bigger bottleneck)
- Doesn't help if synchronous dependencies are serialization
- Cost grows but throughput plateaus

---

## 5. Why Naive Fails

### Amdahl's Law

```
Speedup = 1 / (f + (1-f)/N)

f = fraction of work that's serial (can't parallelize)
N = number of processors

Example 1: f = 5% (95% parallelizable)
  1 processor: 1x
  10 processors: 1 / (0.05 + 0.95/10) = 6.9x
  100 processors: 1 / (0.05 + 0.95/100) = 17x
  ∞ processors: 1 / 0.05 = 20x MAX

  → Can't exceed 20x speedup, no matter how many processors

Example 2: f = 20% (80% parallelizable)
  ∞ processors: 1 / 0.20 = 5x MAX
```

**Lesson:** Optimizing parallelizable work doesn't help if serial work is bottleneck.

### The Database Wall

```
Single database: 100K QPS
Add replicas for reads: helps P99 latency, not throughput
Add shards for writes: helps throughput

Sharding constraints:
  - Hot shard gets 10x traffic
  - Still saturates faster than others
  - Throughput = capacity of hottest shard
```

---

## 6. Evolution / Progression

### Stage 1: Monolithic (0-1K QPS)
- Single database
- Single server
- Throughput limited by: DB write capacity

### Stage 2: Read Replicas (1K-10K QPS)
- Replicate DB for reads
- Writes still go to primary
- Throughput limited by: Primary DB write capacity

### Stage 3: Sharding (10K-100K QPS)
- Split data across multiple databases
- Distribute writes
- Throughput limited by: Hottest shard capacity

### Stage 4: Async Processing (100K-1M+ QPS)
- Move slow work to background
- Return response immediately
- Process later asynchronously
- Throughput limited by: Processing backend capacity

---

## 7. Production Architecture

```
Client Requests (100K QPS)
    │
    ▼
[Load Balancer]
    ├─ Distribution algorithm (round-robin, least-loaded)
    └─ Throughput: balanced across servers
    
    │ (50K QPS per path)
    ├────────────────┬───────────────┐
    │                │               │
    ▼                ▼               ▼
[API 1]         [API 2]         [API 3]
(read cache)    (write queue)   (background jobs)

    │ (for writes, 30K QPS)
    ▼
[Write Queue] (message broker, Kafka)
    │ Decouples client → backend
    │ Buffers burst traffic
    │
    ├─→ [Workers Pool]
    │   ├─ Worker 1 (shard A)
    │   ├─ Worker 2 (shard B)
    │   └─ Worker 3 (shard C)
    │
    ▼
[Sharded Database]
    ├─ Shard A: 10K QPS capacity
    ├─ Shard B: 10K QPS capacity
    └─ Shard C: 10K QPS capacity
    Total: 30K QPS (plus 70K QPS on reads via cache)
```

---

## 8. Components

### Load Balancer
**Purpose:** Distribute requests across servers

```
Algorithms:
  Round-robin: 1st → Server A, 2nd → Server B, 3rd → Server C, repeat
    ✓ Simple
    ✗ Doesn't account for server load

  Least-connections: send to server with fewest active requests
    ✓ Balances load better
    ✗ Requires tracking connections

  Weighted: Server A (2x capacity) gets 2x requests
    ✓ Accounts for capacity differences
    ✗ Needs manual tuning

  Resource-aware: CPU, memory, response time based
    ✓ Optimal
    ✗ Complex, requires agents
```

### Message Broker (Queue)
**Purpose:** Buffer requests, decouple producer from consumer

```
Without queue:
  Client → API → Database
  Blocking: must wait for DB response
  Throughput: limited by slowest link

With queue:
  Client → API → Queue → Workers → Database
  Non-blocking: return immediately
  Throughput: independent of backend speed
```

### Worker Pool
**Purpose:** Process tasks from queue in parallel

```
Queue depth: 10,000 messages
Workers: 10
Per-worker throughput: 100 msg/sec

Time to empty: 10,000 ÷ (10 × 100) = 10 seconds
Processing rate: 1,000 msg/sec (queue depth / time)
```

### Connection Pooling
**Purpose:** Reuse database connections, reduce overhead

```
Without pooling:
  Each request: new connection (3-way handshake, SSL negotiation)
  Overhead: 10ms per request
  Max throughput: 100 req/s (1000ms ÷ 10ms overhead)

With pooling:
  Reuse 100 connections
  Overhead: negligible
  Max throughput: 10,000 req/s
```

---

## 9. Internal Working

### Request Distribution
```
100K QPS arrives at load balancer
Distribute to 10 API servers

If round-robin:
  Server 1: 10K QPS
  Server 2: 10K QPS
  ...
  Server 10: 10K QPS

Each server processes in parallel → total 100K QPS
```

### Queueing Behavior Under Load
```
Queue size: 1000 (max)
Arrival rate: 500 req/s
Processing rate: 400 req/s

Sequence:
  t=0s: Queue empty
  t=1s: Queue = 1000 × (500-400) = 100 items
  t=2s: Queue = 200 items
  t=3s: Queue = 300 items
  t=10s: Queue = 1000 items (FULL)

At capacity: new requests rejected (502 Bad Gateway)
```

### Sharding Distribution
```
3 shards, 30K write throughput target

Naive: split traffic 10K each
  Shard A: 10K QPS capacity, 10K QPS actual ✓
  Shard B: 10K QPS capacity, 10K QPS actual ✓
  Shard C: 10K QPS capacity, 10K QPS actual ✓

Reality: data not equally distributed
  Shard A (US users): 15K QPS (150% capacity!) ✗
  Shard B (EU users): 10K QPS ✓
  Shard C (APAC users): 5K QPS (underutilized) ✓

Bottleneck: Shard A can only handle 10K → throughput capped at 10K total
```

---

## 10. Request Lifecycle

```
Time    Component              Action                  Impact
0ms     Client                 Send request            1
1ms     Network                Transit                 1
2ms     Load Balancer          Route decision          1
3ms     Connection Pool        Acquire connection      1 (already pooled)
4ms     API Server             Route request           1
5ms     API Server             Parse input             1
6ms     Cache                  Lookup                  0.9 (90% hit)
7ms     Serialization          JSON response           0.9
8ms     Network                Send response           0.9
9ms     Client                 Receive               0.9

Successful path completed.

If cache miss (10% of requests):
6ms     Database               Query                   0.1
10ms    Database               Response                0.1
11ms    Serialization          JSON response           0.1
12ms    Network                Send response           0.1
13ms    Client                 Receive                 0.1

Average throughput: 0.9 × (1 req/9ms) + 0.1 × (1 req/13ms) = 100K requests/sec
```

---

## 11. Data Flow

### Single Request Through System (100K QPS aggregate)

```
[100K QPS load]
    ↓
[Load Balancer]
  Round-robin distributes evenly
    ↓ (10K to each server)
[API Server 1] [API Server 2] ... [API Server 10]
    ↓ (90% cache hit)
[Redis Cache] — returns in 1ms
    ↓ (10% need database)
[Database]
    ↓ (multiple shards)
[Shard A] [Shard B] [Shard C]
    ↓ (writes go to queue)
[Kafka Topic] — buffers burst
    ↓
[Worker Pool] — 10 workers
    ↓
[DB Write] — 1K per second per worker
```

### Traffic Spike Handling

```
Normal traffic: 10K QPS
Spike arrives: 50K QPS suddenly

Sequence (first 100ms):
  t=0ms: Spike arrives
  t=10ms: Load balancer queues excess (40K over 10K capacity)
  t=50ms: Queue depth: 2000 items
  t=100ms: API servers overwhelmed, timeout requests
           Return 502 or 503 to clients

Without circuit breaker:
  Clients retry → even more load
  Cascading failure

With circuit breaker:
  Detect queue depth > threshold
  Return 503 immediately → client uses fallback/retry later
  Protects system from overload
```

---

## 12. Key Strategy

### 1. Identify Bottleneck
**Question:** Which component limits throughput?

- Load balancer? (distributing unevenly)
- Network? (bandwidth limited)
- Database? (can't process writes fast enough)
- Shards? (hottest shard is limit)

### 2. Decouple Request Path from Processing
```
Sync (blocks):
  Client → API → Database (sequential)
  Throughput: limited by slowest step

Async (decoupled):
  Client → API → Queue → return response
  Workers process from queue asynchronously
  Throughput: independent of backend speed
```

### 3. Distribute Hot Data
```
Monolithic DB: 100K QPS, but one hot table at 90K QPS
  → Table is bottleneck

Solution: Shard hot table across 10 databases
  Each handles 10K QPS
  Total: still 100K QPS, but distributed
```

### 4. Scale Bottleneck Layer
```
System throughput: 10K QPS, bottleneck: API layer
API layer:
  5 servers × 2K req/s each = 10K

Solution: Add servers
  10 servers × 2K req/s each = 20K
```

### 5. Vertical vs Horizontal Scaling
```
Vertical (bigger server):
  1 server: 10K QPS → 100K QPS (10x cost)
  But single point of failure

Horizontal (more servers):
  10 servers × 10K QPS = 100K QPS (10x servers, linear cost)
  Distributed, fault-tolerant
```

---

## 13. Failure Scenarios

### Scenario 1: Hot Partition
```
Sharded database: user data by user_id % 1000

User 0, 1000, 2000, ... (every 1000th user) get routed to shard 0
User celebrity with 100M followers gets user_id = 1000

Shard 0 throughput:
  Normal: 100K QPS (fair share)
  With celebrity: 100K (celebrity) + 99K (normal) = 199K! 
  Capacity: 100K
  
Result: Shard 0 drops/delays requests → celebrity (and 1000 others) slowed
```

**Fix:** Consistent hashing with virtual nodes, replica hot keys

### Scenario 2: Cascading Overload
```
Service A handles 100K QPS
  → Needs 50K QPS from Service B (dependency)
  
Service B capacity: 40K QPS

When traffic increases:
  Service A requests grow to 60K QPS
  → Service B gets 60K demands but can only handle 40K
  → Timeouts, retries
  → Retries amplify load to 80K
  → Cascading failure

Throughput: drops from 100K → 10K (90% failure)
```

**Fix:** Rate limiting, circuit breakers, adaptive backoff

### Scenario 3: Buffer Bloat
```
Queue size: 10,000 (unbounded)
Arrival: 100K QPS
Processing: 50K QPS

Queue grows:
  t=0s: 50K items
  t=1s: 100K items (queue overflows)
  
Memory exhaustion → service crashes
```

**Fix:** Bounded queue (10K max), reject when full (503)

---

## 14. Bottlenecks Table

| Component | Throughput Impact | Symptoms | Quick Fix |
|---|---|---|---|
| Load balancer | 10-100x | Uneven distribution | Better routing algorithm |
| Network I/O | 1-10x | Saturation, packet loss | Increase bandwidth |
| Database writes | 5-20x | High write latency | Sharding, async queue |
| Locking/mutex | 5-100x | Contention, low CPU util | Lock-free structures |
| Serialization | 2-10x | CPU spike, large payloads | Binary format (protobuf) |
| Queue depth | 1-10x | Cascading timeouts | Shed load, auto-scale |
| Hot partition | 5-50x | Uneven shard load | Consistent hashing |
| Memory exhaustion | 10-100x | OOM errors, crashes | Bounded cache, eviction |
| CPU throttling | 5-20x | Thermal, overclocking | Better cooling |
| Network jitter | 2-5x | Timeout spikes | Redundant paths |

---

## 15. Monitoring

### Key Metrics

```
QPS (Queries Per Second):
  ✓ Overall: 100K QPS
  ✓ Per server: 10K QPS (if balanced)
  ✓ Per service: which service at capacity?

Throughput Distribution:
  ✓ Load: is load balanced? (should be ~equal)
  ✓ Shard: which shards overloaded?
  ✓ Latency: does high load → high latency?

Error Rate:
  ✓ 5xx errors: service failure
  ✓ Timeouts: downstream slow
  ✓ Queue rejection (503): system overloaded
```

### Dashboards

```
Real-time monitoring:
  [QPS] [Error Rate] [P99 Latency]
    ↓       ↓           ↓
  100K    0.1%        150ms

Per-component:
  API Layer:
    QPS: 90K (target 100K)
    Errors: 0.05%
    Load: balanced (9-11K per server)
    
  Database:
    Writes: 30K QPS (capacity 40K)
    Shard distribution:
      A: 15K (hottest)
      B: 10K
      C: 5K
  
  Queue:
    Depth: 500 (max 10K)
    Processing rate: 5K/sec
    Age of oldest: 100ms
```

### Red Flags

- Uneven load distribution (one server 2x others)
- Queue depth growing unbounded (processing slower than arrival)
- P99 latency increasing linearly with QPS (near saturation)
- Error rate > 1% (system struggling)
- Hot shard at capacity while others idle (partitioning failure)

---

## 16. Optimizations

### 1. Batch Writes
```
Naive:
  100 requests → 100 database writes (100 round-trips)
  Latency: 100 × 10ms = 1000ms, throughput: 100 req/s

Batched:
  100 requests → 1 batch write (1 round-trip)
  Latency: 50ms, throughput: 2000 req/s
  
Speedup: 20x throughput
```

### 2. Cache Popular Data
```
Database: 100K QPS
  → Hot data (20% of keys) = 80K QPS
  
Add cache:
  Cache hit rate: 80% (cached = 80K, miss = 20K)
  Database load: 20K QPS (down from 100K)
  Throughput: cache handles 80K instantly
  
Effective throughput: 100K QPS with only 20K on database
```

### 3. Async Processing
```
Sync (blocks):
  Request → slow operation (100ms) → response
  Throughput: 10 req/s

Async (return immediately):
  Request → enqueue → response (1ms)
  Background: process from queue
  Throughput: 1000 req/s (throughput in queue independent of processing)
```

### 4. Compression
```
Average response: 100 KB
Network bandwidth: 1 Gbps

Max throughput:
  Uncompressed: (1 Gbps) ÷ (100 KB) = 10,000 req/s
  Compressed (10:1): (1 Gbps) ÷ (10 KB) = 100,000 req/s
  
Speedup: 10x (if compression CPU cost acceptable)
```

### 5. Connection Pooling
```
Without:
  Connection setup: 10ms
  Request: 1ms
  Total: 11ms per request
  Throughput: 91 req/s

With pooling (100 connections):
  Reuse: <1ms per request
  Throughput: 1000+ req/s
  
Speedup: 10x+
```

### 6. Sharding Strategy
```
Single shard: 100K QPS capacity
Bottleneck: hot partition gets 80K QPS (80% traffic)

Reshard to split hot partition:
  Shard A (50% hot data): 50K QPS
  Shard B (50% hot data): 50K QPS
  Cold shards: 25K, 25K
  Total: 150K QPS (up from 100K)
```

---

## 17. Security

### 1. Rate Limiting
```
Per-user rate limit: 1000 req/s
Malicious user sending 10K req/s: capped at 1000
  → Prevents single user from consuming all capacity

Per-endpoint rate limit: 100K req/s total
  → Prevents DOS

Distributed rate limiting:
  Each server tracks (user_id, endpoint)
  Shares state via Redis
  Consistent across fleet
```

### 2. Request Validation Early
```
Invalid request: large payload (1GB)

Bad: process fully, fail at database
  Cost: full request processing, network I/O, CPU

Good: validate early (size limits)
  Reject at gateway (10ms)
  Cost: minimal
  
Throughput improvement: can handle real requests instead
```

### 3. DDoS Mitigation
```
Attack: 1M req/sec random traffic
System capacity: 100K req/s

Mitigation:
  - Anycast distribution (spread across 10 edge locations)
  - Early packet filtering (drop obvious attacks)
  - Rate limit per source IP
  - Authentication requirement for heavy endpoints
  
Result: legitimate traffic prioritized, system handles 100K req/s
```

---

## 18. Tradeoffs Table

| Approach | Throughput Gain | Cost | Complexity |
|---|---|---|---|
| Batching | 10-100x | Higher latency variance | Medium |
| Caching | 2-10x (load reduction) | Memory, invalidation | Medium |
| Sharding | 3-10x (at hot spots) | Consistency, operational | High |
| Async queues | 5-50x (decoupling) | Staleness, ordering issues | High |
| Compression | 2-10x (bandwidth bound) | CPU cost | Low |
| Connection pooling | 2-5x | Memory | Low |
| Vertical scaling | 2-10x (single server) | Cost, single point of failure | Low |
| Horizontal scaling | 2-10x (per server added) | Operational complexity | Medium |

---

## 19. Alternatives

### Real-Time vs Batch Processing
```
Real-time (synchronous):
  - Throughput: limited by service latency
  - Example: web request → process → respond (100ms max)

Batch (asynchronous):
  - Throughput: limited by processing capacity
  - Example: queue 1M requests → process overnight
  - Throughput: not latency-constrained
  
Trade: Latency vs Infrastructure cost
```

### Monolithic vs Microservices
```
Monolithic:
  - Single database, single process
  - Throughput: 100K QPS (single bottleneck)
  
Microservices + sharding:
  - Multiple databases, distributed
  - Throughput: 1M QPS (distributed bottleneck)
  
Trade: Operational complexity vs throughput
```

### Strong vs Eventual Consistency
```
Strong consistency:
  - All replicas updated before response
  - Throughput: slow (write must coordinate)
  
Eventual consistency:
  - Return immediately, update replicas async
  - Throughput: fast (no coordination)
  
Trade: Consistency vs throughput
```

---

## 20. When NOT to Use

### Don't Optimize Throughput When:

1. **Latency is constraint**
   - User-facing API needs <100ms
   - Batching throughput fix causes latency → bad
   - Optimize latency first

2. **Cost not worth it**
   - Current throughput sufficient
   - Infrastructure cost to 10x > value gained
   - Not bottleneck

3. **Consistency matters**
   - Eventual consistency kills throughput gains
   - Can't parallelize (CAP theorem)
   - Keep consistency

4. **System not deployed yet**
   - Measure first
   - Premature optimization wastes effort

5. **Operational burden too high**
   - Sharding adds operational complexity
   - Maintenance cost > throughput benefit

---

## 21. Interview Questions

1. **Design system to handle 1M QPS**
   - What's your approach to bottlenecks?
   - How do you identify constraints?
   - What would you measure first?

2. **System throughput plateaus at 100K QPS despite adding servers**
   - What's likely bottleneck?
   - How would you diagnose?
   - Solutions?

3. **Shard A (hot) at capacity, Shard B (cold) underutilized**
   - Why uneven distribution?
   - How to fix?
   - Trade-offs?

4. **Compare sync vs async architecture**
   - When use each?
   - Throughput implications?
   - Failure modes?

5. **Queue depth growing unbounded**
   - Why?
   - How to prevent?
   - Monitoring?

---

## 22. Common Mistakes

1. **Optimizing the wrong layer**
   - Make database 2x faster
   - But network bottleneck at 1/5 throughput
   - Optimize bottleneck, not fastest component

2. **Not accounting for Amdahl's Law**
   - 20% serial work
   - Add 10x processors
   - Expect 10x throughput (wrong: only 1.2x)
   - Serial portion limits speedup

3. **Hot partition blindness**
   - Shard equally by hash
   - But one shard gets 10x traffic
   - Shard is bottleneck (not fixed by adding shards)
   - Need: repartition or consistent hashing

4. **Unbounded queues**
   - Queue grows until memory exhaustion
   - Service crashes (no graceful degradation)
   - Use: bounded queue, shed load when full

5. **Ignoring load distribution**
   - Server A: 20K QPS, Server B: 5K QPS
   - Assume balanced (wrong)
   - Load balancer broken or servers unequal capacity
   - Investigate distribution

6. **Synchronous dependencies everywhere**
   - Request serial: A → B → C → D
   - 4 × 10ms = 40ms latency
   - Throughput = 25 req/s
   - Parallelize: max(10ms) = 10ms, 100 req/s

---

## 23. Debugging Guide

### Step 1: Measure Baseline
```
Current throughput: 50K QPS
Target: 100K QPS
Bottleneck: unknown

Measure:
  API layer: 90K QPS capacity (not bottleneck)
  Database: 60K QPS capacity (BOTTLENECK)
  Network: 200K QPS capacity (not bottleneck)
```

### Step 2: Identify Bottleneck
```
Database bottleneck: why only 60K QPS?

Measure per-operation:
  Reads: 40K QPS capacity (fast, use cache)
  Writes: 20K QPS capacity (slow, lock contention)
  
Root cause: write lock contentio
```

### Step 3: Diagnose Lock Contention
```
Profile database locks:
  Lock A: 10ms average hold time, 2000 waiters
  Lock B: 5ms average, 100 waiters
  
Lock A is problem:
  Held by: UpdateUserScore operation
  Causes: serialization
  
Solution: use lock-free counter (atomic increment)
```

### Step 4: Validate Fix
```
After fix: atomic increment instead of locked update

New throughput: 60K → 90K QPS (+50%)
  Read throughput: unchanged 40K
  Write throughput: 20K → 50K QPS (2.5x)
  
Result: database now 90K, API now bottleneck
```

### Step 5: Next Iteration
```
Current bottleneck: API layer at 90K QPS

Measure per API:
  GET /user: 50K QPS (cached, fast)
  POST /order: 30K QPS (slow, compute-heavy)
  PUT /profile: 10K QPS
  
POST /order is bottleneck:
  JSON parsing: 5ms
  Validation: 3ms
  Processing: 12ms
  Total: 20ms
  Throughput: 50 req/s per worker
  
With 10 workers: 500 req/s
Expected 30K but getting 500

Issue: only 1 API worker assigned!
Solution: scale POST endpoint to 10 workers, others to 5 each
```

---

## 24. Code Examples

### Go: Load Balancer Round-Robin
```go
type LoadBalancer struct {
    servers []string
    current int
    mu      sync.Mutex
}

func (lb *LoadBalancer) NextServer() string {
    lb.mu.Lock()
    defer lb.mu.Unlock()
    
    server := lb.servers[lb.current]
    lb.current = (lb.current + 1) % len(lb.servers)
    
    return server
}

// Usage: for each request
server := lb.NextServer()
resp, _ := http.Get("http://" + server + "/api")
```

### Go: Bounded Queue with Shedding
```go
type BoundedQueue struct {
    ch chan Task
    mu sync.RWMutex
}

func NewBoundedQueue(maxSize int) *BoundedQueue {
    return &BoundedQueue{
        ch: make(chan Task, maxSize),
    }
}

func (bq *BoundedQueue) Enqueue(task Task) error {
    select {
    case bq.ch <- task:
        return nil
    default:
        // Queue full, shed load
        return fmt.Errorf("queue full, rejecting request")
    }
}

func (bq *BoundedQueue) Process(worker func(Task)) {
    for task := range bq.ch {
        go worker(task) // Process in background
    }
}

// Usage: 
queue := NewBoundedQueue(10000)
err := queue.Enqueue(myTask)
if err != nil {
    http.Error(w, "service overloaded", http.StatusServiceUnavailable)
}
```

### Go: Batch Writes
```go
type BatchWriter struct {
    ch    chan *Item
    batch []*Item
    size  int
}

func (bw *BatchWriter) Add(item *Item) {
    bw.ch <- item
}

func (bw *BatchWriter) Start(batchSize int, interval time.Duration) {
    ticker := time.NewTicker(interval)
    defer ticker.Stop()
    
    for {
        select {
        case item := <-bw.ch:
            bw.batch = append(bw.batch, item)
            if len(bw.batch) >= batchSize {
                bw.flush() // Write batch to DB
            }
        case <-ticker.C:
            if len(bw.batch) > 0 {
                bw.flush() // Write whatever we have
            }
        }
    }
}

func (bw *BatchWriter) flush() {
    // Single DB write for all items in batch
    db.BatchInsert(bw.batch)
    bw.batch = nil
}

// Usage:
writer := &BatchWriter{ch: make(chan *Item, 10000)}
go writer.Start(1000, 100*time.Millisecond)
for item := range items {
    writer.Add(item)
}
```

### Go: Multi-Level Caching
```go
type CacheStack struct {
    l1 *LocalCache
    l2 *RedisCache
    db Database
}

func (cs *CacheStack) Get(key string) (interface{}, error) {
    // L1: In-process (microseconds)
    if val, ok := cs.l1.Get(key); ok {
        return val, nil
    }
    
    // L2: Redis (milliseconds)
    if val, err := cs.l2.Get(key); err == nil {
        cs.l1.Set(key, val, 1*time.Minute) // Populate L1
        return val, nil
    }
    
    // L3: Database
    val, err := cs.db.Get(key)
    if err == nil {
        cs.l2.Set(key, val, 1*time.Hour) // Populate L2
        cs.l1.Set(key, val, 1*time.Minute) // Populate L1
    }
    
    return val, err
}

// Usage:
cache := &CacheStack{
    l1: NewLocalCache(1000), // 1000 items
    l2: NewRedisCache(redis.Client),
    db: myDatabase,
}
val, _ := cache.Get("user:123")
```

---

## 25. Visual Diagrams

### Throughput vs Utilization
```
Throughput (req/s)  Latency (ms)
     10K │                    500│
         │        ╱╱╱╱╱╱╱╱╱╱╱╱╱  │╱╱╱╱╱╱╱╱╱╱╱
      5K │   ╱╱╱╱╱╱╱╱╱╱      250 │╱╱╱╱╱╱╱╱╱
         │╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱  │╱╱╱╱╱╱╱╱╱
     0   └──────────────────────┘
        0%  50%  95%  99%  100%
         Utilization

Key insight: Latency explodes as system nears 100% util
Safe operating point: 70-80% utilization
```

### Sharding Distribution
```
Hottest shard: User data (celebrities, frequent queries)
Cold shards: Rare queries

Distribution (unequal):
  Shard A (hot): 50K QPS (50% of traffic)
  Shard B: 20K QPS
  Shard C: 20K QPS
  Shard D: 10K QPS

Bottleneck: Shard A capacity 40K QPS
  → System throughput capped at 40K (despite 170K total capacity)

Solution: Reshard A into 2 shards
  → New bottleneck: whichever shard still hottest
```

### Queueing Delay vs Utilization
```
Queue wait time vs Utilization (M/M/1 queue)

Wait time (ms)  
    1000 │              ╱╱╱╱╱╱╱╱╱╱
         │          ╱╱╱╱╱╱╱╱╱
     100 │      ╱╱╱╱╱╱╱╱╱
         │  ╱╱╱╱╱╱╱╱╱
      10 │╱╱╱╱╱╱
         │
      1  └─────────────────────
         0% 25% 50% 75% 90% 95%
            Utilization

Insight: Wait time grows exponentially past 80% utilization
```

---

## 26. Simulation Ideas

1. **Queueing Simulator**
   - Input: arrival rate, service rate, num workers
   - Output: throughput, queue depth, wait time
   - Interactive: adjust parameters, see effect

2. **Amdahl's Law Calculator**
   - Input: % parallelizable work, num processors
   - Output: speedup curve
   - Show: asymptotic limit

3. **Sharding Load Simulator**
   - Generate skewed traffic (Zipfian distribution)
   - Simulate hot partition
   - Show: how reshard improves throughput

4. **Cascade Failure Simulator**
   - Service A → Service B → Service C
   - Service B overloaded
   - Show: how timeout propagates, causing cascading failure

5. **Cache Hit Rate Impact**
   - Database throughput: 100K QPS
   - Add cache with variable hit rate
   - Show: how hit rate impacts overall throughput

---

## 27. Case Studies

### Case 1: YouTube Video Processing (100M views/day)
**Problem:** Throughput capped at 10K videos/second for transcoding

**Root Cause:** Single transcoding queue with 100 workers, but 50% of videos are 4K (takes 10x longer to process)

**Solution:**
1. Separate queues by video quality (HD, 4K, 8K)
2. Allocate workers by queue size (more to 4K)
3. Add speculative processing (start encoding before upload complete)

**Result:** Throughput increased to 50K videos/sec

### Case 2: Twitter Tweet Feed at 500M DAU
**Problem:** Can't handle tweet burst (100K tweets/sec expected, current capacity 50K)

**Root Cause:** Single write bottleneck in distributed transaction log (Kafka partition)

**Solution:**
1. Shard tweet stream by user_id (different partitions)
2. Use Kafka topic sharding (1000 partitions)
3. Add cache layer (Redis) for hot tweets

**Result:** Throughput: 500K tweets/sec, improved from 50K

### Case 3: Stripe Payment Processing (100K+ payments/sec)
**Problem:** Latency increased during burst (payment spikes during shopping events)

**Root Cause:** Credit card authorization (external service) became bottleneck

**Solution:**
1. Cache authorization results (same card, same amount often succeeds)
2. Use hedged requests (try multiple card networks in parallel)
3. Add async confirmation (accept payment immediately, confirm async)

**Result:** Throughput: 200K payments/sec with <100ms latency

---

## 28. Related Topics

- **Little's Law:** L = λ × W (throughput driven by queue length)
- **Amdahl's Law:** Speedup limits on parallelization
- **Scalability:** Vertical vs horizontal scaling
- **Latency:** How latency and throughput trade off
- **Queueing Theory:** M/M/1, M/M/c queue models
- **Load Balancing:** Distribution algorithms
- **Sharding:** Partitioning data for throughput

---

## 29. Advanced Topics

### Consistent Hashing
```
Problem: Simple sharding (key % N) breaks when N changes
  Old: key % 10 → shard 3
  New: key % 11 → shard 7
  → Must re-shard all data

Solution: Consistent hashing (ring-based)
  Assign keys to points on ring
  Shard responsible for arc of ring
  New shard: only affects 1/N of keys
```

### Load Balancing Algorithms
```
Round-robin: fair distribution
  Issue: doesn't account for unequal server capacity

Least-connections: considers active connections
  Issue: doesn't account for request complexity

Weighted round-robin: server capacity aware
  Issue: requires manual tuning

Resource-aware (adaptive): CPU, memory, response time
  Benefit: optimal load distribution
  Cost: requires monitoring agents
```

### Rate Limiting (Leaky Bucket, Token Bucket)
```
Leaky bucket:
  - Fixed rate of output (100 req/s)
  - Burst input buffered (up to 1000)
  - Excess rejected

Token bucket:
  - Tokens generated at rate r (100/s)
  - Each request costs k tokens
  - Burst: use tokens from accumulation

Difference:
  Leaky: enforces output rate
  Token: allows controlled bursts
```

---

## 30. Production Checklist

- [ ] Measure baseline throughput (QPS, per-server breakdown)
- [ ] Identify bottleneck (database, network, API, shard)
- [ ] Set throughput target (per-service, per-shard capacity)
- [ ] Implement connection pooling (all database clients)
- [ ] Add caching layer (reduces database load)
- [ ] Implement load balancing (even distribution across servers)
- [ ] Enable request batching where applicable
- [ ] Shard database (distribute hot partitions)
- [ ] Implement request queuing (decouple sync from async)
- [ ] Monitor queue depth (alert if growing unbounded)
- [ ] Monitor per-server load (detect uneven distribution)
- [ ] Implement rate limiting per user/endpoint
- [ ] Implement circuit breakers (prevent cascade)
- [ ] Test with load simulator (identify when throughput plateaus)
- [ ] Plan for hot partition handling (consistent hashing, repartitioning)
- [ ] Document capacity limits (per-service, per-shard)
- [ ] Alert on queue depth > 50% of max
- [ ] Alert on error rate > 1%
- [ ] Regular throughput audits (quarterly, before major features)
- [ ] Load test with expected peak traffic (black friday, launches)

---

*Last Updated: 2026-05-28*
