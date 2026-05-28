# Scalability: The Art of Handling More

> "A system that doesn't scale is destined to fail under its own success."

---

## 1. Problem Statement

Your startup's API handles 100 requests/second perfectly. Success. Then growth happens:
- 1,000 RPS → slow responses
- 10,000 RPS → errors start
- 100,000 RPS → complete failure

**Question:** Why does adding more hardware not proportionally increase performance?

**Answer:** Scalability isn't just about capacity—it's about architecture.

---

## 2. Real World Analogy

**Restaurant with 100 customers:**
- 1 chef, 1 waiter → works fine
- 1,000 customers → add 10 chefs?
  - Kitchen gets crowded
  - Equipment becomes bottleneck
  - Communication overhead explodes
  - Quality degrades

**Key insight:** Scaling isn't linear. Bottlenecks shift. Coordination costs grow.

---

## 3. Why This Problem Exists

Systems accumulate **hidden dependencies:**
1. **Shared resources** (database, cache, message queue)
2. **Coordination overhead** (locking, consensus)
3. **Network communication** (latency, bandwidth)
4. **State management** (consistency checks, synchronization)
5. **Operational friction** (deployment, monitoring, debugging)

Single-server systems hide these costs.

Distributed systems expose them ruthlessly.

---

## 4. Naive Approach

**"Just buy a bigger server"**

```
Request rate: 100 → 1,000 RPS
Solution: Buy 10x faster CPU

Problem:
├─ CPU scales
├─ But memory doesn't (limited per machine)
├─ Network bandwidth doesn't
├─ Disk IOPS don't
└─ Eventually hit hard ceiling
```

**Why this fails:** Physical limits exist.
- Single CPU: ~64 cores max
- Single machine RAM: 1-2 TB practical
- Single NIC: 100 Gbps limit
- Disk IOPS: ~100K per drive

You will hit a wall.

---

## 5. Why Naive Approach Fails

**Vertical scaling problems:**

| Problem | Impact |
|---------|--------|
| Physical limits | Can't go beyond hardware maximum |
| Cost exponential | 10x capacity ≈ 100x cost (diminishing returns) |
| No redundancy | Single machine failure = complete outage |
| Deployment window | Can't upgrade without downtime |
| Network limit | Single NIC becomes bottleneck (10→100 Gbps huge jump in cost) |
| Thermal limits | CPU cooling becomes problem |
| NUMA effects | Memory access latency on large systems |

**Real example:**
- Server with 2 CPUs → linear scaling up to ~32 cores
- Server with 96 cores → scaling collapses (NUMA penalties, lock contention, cache coherency overhead)

---

## 6. Evolution Step By Step

### Stage 1: Monolith (0-100K RPS)
```
Client → Single Server
         ├─ API
         ├─ Database
         ├─ Cache
         └─ Everything
```

**Works until:** Database becomes bottleneck

---

### Stage 2: Separate Read Replicas (100K-1M RPS)
```
Client → Load Balancer
         ├─ API 1 → Read Replica 1
         ├─ API 2 → Read Replica 2
         ├─ API 3 → Primary DB (writes)
         └─ API 4 → Cache
```

**Works until:** Primary database can't handle write volume

**Scaling bottleneck:** Database writes (single node)

---

### Stage 3: Database Sharding (1M-10M RPS)
```
Client → Load Balancer → Request Router
                         ├─ Shard 1 (users A-M)
                         ├─ Shard 2 (users N-Z)
                         └─ Shard 3 (new users)

Each shard:
├─ Primary DB
├─ Read replicas
└─ Cache
```

**Works until:** Hot shard becomes bottleneck

---

### Stage 4: Microservices (10M-100M RPS)
```
Client → API Gateway
         ├─ User Service → Shard 1, 2, 3
         ├─ Order Service → Shard 1, 2, 3
         ├─ Payment Service → Isolated DB
         ├─ Notification Service → Kafka
         └─ Analytics Service → Event Stream
```

**Works until:** Coordination overhead crushes you

---

## 7. Final Production Architecture

**Spotify's architecture (100M+ users, billions RPS):**

```
┌─────────────────────────────────────────┐
│         Global CDN (Cloudflare)         │
│  (cache static content, DDoS protection)│
└──────────────────┬──────────────────────┘
                   │
┌──────────────────┴──────────────────────┐
│    Multi-region Load Balancing          │
│  (US, EU, APAC - route by latency)      │
└──────────────────┬──────────────────────┘
         ┌─────────┼─────────┐
         │         │         │
    ┌────▼───┐ ┌──▼───┐ ┌───▼────┐
    │ US-EAST│ │EU    │ │APAC    │
    └────┬───┘ └──┬───┘ └───┬────┘
         │        │        │
    ┌────▼────────▼────────▼─────────┐
    │  Service Mesh (Kubernetes)     │
    │  ├─ User Service              │
    │  ├─ Playlist Service          │
    │  ├─ Streaming Service         │
    │  ├─ Payment Service           │
    │  └─ Analytics Service         │
    └────┬────────┬────────┬────────┘
         │        │        │
    ┌────▼───┐┌───▼────┐┌──▼────┐
    │ Search ││Cache   ││Message │
    │Engine  ││Layer   ││Queue   │
    └────────┘└────────┘└────────┘
```

**Key principles:**

1. **No single point of failure**
   - Multiple regions
   - Multiple data centers per region
   - Replicated services

2. **Horizontal scaling all layers**
   - API servers (stateless)
   - Microservices (partitioned by domain)
   - Databases (sharded by user/region)
   - Caches (distributed)
   - Message queues (partitioned topics)

3. **Bounded resource usage**
   - Connection pools (max size)
   - Queue depths (drop if overloaded)
   - Timeouts (fail fast)
   - Rate limiting (circuit breaker)

4. **Asynchronous processing**
   - Requests don't wait for slow operations
   - Use message queues (Kafka)
   - Background workers scale independently

---

## 8. Component Breakdown

### Load Balancer
```
Input: 100K RPS from clients
Task: Distribute across 100 servers

Naive: Round-robin
Problem: Doesn't account for server state

Better: Least connections
├─ Track open connections per server
├─ Route to least loaded
└─ Still doesn't account for CPU

Best: Adaptive feedback
├─ Monitor response time per server
├─ Route based on health + load
├─ Remove slow/down servers
└─ Add servers when queue builds
```

### Stateless Application Layer
```
Key insight: Each request is independent

Benefits:
├─ Any server can handle any request
├─ Add/remove servers without disruption
├─ Single server failure = automatic reroute
└─ Can scale horizontally infinitely

Implementation:
├─ No session stored in-process
├─ Use external session store (Redis)
├─ No local cache
└─ All state in database or cache
```

### Database Layer
```
Without sharding:
├─ All requests hit single database
├─ CPU becomes bottleneck
├─ Memory becomes bottleneck
└─ Can't scale past ~50K RPS

With sharding (by user_id % 10):
├─ User 1-100K → Shard 1
├─ User 100K-200K → Shard 2
├─ ...
└─ User 900K-1M → Shard 10

Each shard:
├─ 1/10th the data
├─ 1/10th the QPS
├─ Can have read replicas
└─ Can replicate to other datacenters
```

### Cache Layer
```
Problem: Database still bottleneck for reads

Solution: Distributed cache

Scaling:
├─ Memcached cluster (1000s of nodes)
├─ Each node holds 64GB
├─ Consistent hashing (shard key = object_id)
├─ Add nodes without rehashing everything
└─ Can scale cache independently from DB
```

---

## 9. Internal Working

### How Horizontal Scaling Actually Works

```
Single server (serial processing):
Request 1 → Process (100ms) → Response
Request 2 → Wait (100ms) → Process (100ms) → Response
Request 3 → Wait (200ms) → Process (100ms) → Response

Throughput: 1 req / 100ms = 10 RPS
Latency: 1st=100ms, 2nd=200ms, 3rd=300ms (queuing)

With 10 servers (parallel):
Request 1 → Server 1 (100ms) → Response
Request 2 → Server 2 (100ms) → Response (simultaneously)
Request 3 → Server 3 (100ms) → Response (simultaneously)

Throughput: 10 requests / 100ms = 100 RPS
Latency: All ~100ms (no queuing)
```

**Key insight:** Scaling is about parallelism, not just raw power.

---

## 10. Request Lifecycle

```
Client Request
    │
    ▼
┌─────────────────┐
│ DNS Resolution  │  (cached, <1ms usually)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ Load Balancer Selection      │  (health aware)
│ (least connections / latency)│
└────────┬────────────────────┘
         │
         ▼
┌────────────────────────┐
│ Route to API Server 42 │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Check Cache (Redis)            │
│ Cache hit: return instantly    │
│ Miss: query database           │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────┐
│ Database Query         │  (sharded)
│ (hits shard 3 of 10)   │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ Update Cache           │
└────────┬───────────────┘
         │
         ▼
    Response
```

---

## 11. Data Flow

**At 1M RPS across 100 servers:**

```
1M RPS → Load Balancer (40 Gbps inbound)
├─ Distributed across 100 servers
├─ 10K RPS per server (10 Mbps each)
│
├─ 70% cache hits (7K RPS) → Redis cluster
│  └─ 300 Redis nodes (30 QPS each)
│
├─ 30% cache misses (3K RPS) → Database shards
│  ├─ 10 shards × 300 RPS each
│  ├─ Each shard (1 primary + 2 replicas)
│  ├─ Primary: 300 write QPS
│  └─ Replicas: 300 read QPS each
│
└─ 200 Gbps outbound (responses to clients)
```

---

## 12. Scaling Strategy

### Vertical Scaling Limits (How High Can One Server Go?)

```
Desktop CPU:  8 cores, $200
Server CPU:   64 cores, $5K
But scaling degrades:
├─ 8 cores linear (8x throughput)
├─ 16 cores ~7.5x (diminishing returns)
├─ 32 cores ~28x (lock contention, NUMA)
└─ 64 cores ~35x (memory access penalty)

Physical ceiling: ~50K RPS per server
Beyond: horizontal scaling required
```

### Horizontal Scaling Strategy

**Phase 1: Simple replication (0-10x)**
```
1 → 2 → 4 → 8 servers
Linear scaling if:
├─ Stateless
├─ Load balanced properly
├─ No shared bottleneck
└─ Database can keep up
```

**Phase 2: Database replication (10-100x)**
```
Reads scale (read replicas)
But writes bottlenecked on primary

Solutions:
├─ Sharding (partition by user_id, region)
├─ CQRS (separate read/write models)
└─ Event sourcing (append-only log)
```

**Phase 3: Service decomposition (100x+)**
```
Monolith splits:
├─ User Service (can scale 10x)
├─ Payment Service (can scale 5x)
├─ Notification Service (can scale 1000x - async)
└─ Each scales independently
```

---

## 13. Failure Scenarios

### Failure 1: Load Balancer Bottleneck
```
Symptom: Adding servers doesn't increase throughput

Cause: Load balancer CPU maxed

Root: Single load balancer can't distribute
100K requests/second

Fix: 
├─ Multiple load balancers (active-active)
├─ Or use L4 switching (hardware, <1% overhead)
├─ Or use DNS round-robin (clients distribute)
└─ Monitor load balancer CPU (should be <20%)
```

### Failure 2: Hot Partition
```
Symptom: One database shard overloaded

Example: Users sharded by user_id % 10
But shard 0 gets 50% of traffic

Root: 
├─ User ID distribution skewed
├─ Celebrity account on shard 3
├─ Or time-based ID (hot shard newer)

Fix:
├─ Re-shard (redistribute data)
├─ Add replicas to hot shard
├─ Move hot accounts to own shard
└─ Use consistent hashing (more uniform)
```

### Failure 3: Scaling Ceiling
```
Symptom: Performance plateaus despite adding servers

Causes:
├─ Amdahl's law: 10% serial code = 10x max (N→∞)
├─ Shared resource bottleneck (disk, NIC, CPU)
├─ Synchronization overhead exceeds parallelism gain
└─ Network becomes bottleneck

Fix: Identify serial component
├─ Profile where time spent
├─ Parallelize critical path
├─ Or redesign around bottleneck
```

---

## 14. Bottlenecks

**Common bottlenecks in order of frequency:**

| Bottleneck | Symptom | Fix |
|------------|---------|-----|
| Database writes | Latency increases under load | Sharding, CQRS |
| Shared cache | Hit rate drops | Distributed cache, partitioning |
| Lock contention | CPU higher than load | Lock-free structures, partitioning |
| Network bandwidth | Packet drops, retransmissions | Compression, protocol optimization |
| Single load balancer | Stops distributing evenly | Multiple LBs, DNS RR |
| Uneven sharding | One shard slow | Rebalance, consistent hashing |
| Synchronous operations | Queuing | Async, batching, pipelining |
| Memory allocation | GC pauses, latency spikes | Object pooling, streaming |

---

## 15. Monitoring

**What to measure:**

```
Throughput:
├─ Requests/second (by endpoint)
├─ Latency percentiles (p50, p95, p99)
├─ Queue depth (pending requests)
└─ Error rate

Utilization:
├─ CPU per server
├─ Memory per server
├─ Disk IOPS
├─ Network bandwidth
└─ Database connections

Scaling health:
├─ Latency vs. load curve (should stay flat)
├─ Throughput vs. servers (should increase linearly)
├─ Error rate vs. load (should stay 0)
└─ GC pause time (should not increase)
```

**Red flags:**

```
✗ Latency increasing with load (not scaling)
✗ Error rate > 0 (overloaded)
✗ Queue depth growing (backlog accumulating)
✗ One server 2x busier than others (uneven distribution)
✗ Any component 80%+ utilized (approaching limit)
```

---

## 16. Production Optimizations

### Optimization 1: Connection Pooling
```
Without:
├─ Each request creates new DB connection
├─ Handshake overhead (~10ms)
├─ At 1K RPS: 10 seconds pure overhead

With pool of 100 connections:
├─ Reuse existing connections
├─ Overhead: ~0ms
└─ But must manage pool size (too large = waste, too small = waits)
```

### Optimization 2: Request Batching
```
Without:
├─ 1000 requests = 1000 database queries

With:
├─ Group 100 requests
├─ Execute as single batch query
├─ 10x reduction in network round trips
└─ 5-10x throughput improvement
```

### Optimization 3: Async I/O
```
Synchronous (blocks):
Request → Query DB (100ms) → Response
└─ Can only handle 10 RPS per thread

Asynchronous (non-blocking):
Request 1 → Query DB (in background) → Response
Request 2 → Query DB (in background) → Response
└─ Can handle 10K RPS per thread
```

---

## 17. Security Considerations

**Scaling exposes security issues:**

```
Single server: Can manually review requests
Multiple servers: Can't monitor all traffic

Rate limiting:
├─ Must be distributed
├─ Shared counter (Redis)
├─ Prevents abuse across servers

DDoS mitigation:
├─ Early filtering (at load balancer/edge)
├─ Don't scale compute to fight attack
└─ Protect load balancer itself

Cross-shard consistency:
├─ Distributed transactions risky
├─ Design for eventual consistency
└─ Accept temporary inconsistency
```

---

## 18. Tradeoffs

| Choice | Pro | Con | Use When |
|--------|-----|-----|----------|
| **Vertical scaling** | Simple, low latency between components | Expensive, single point of failure, limited ceiling | <50K RPS, simple system |
| **Horizontal scaling** | Cost efficient, redundancy, flexibility | Complexity, eventual consistency, operational overhead | >50K RPS, can afford operational cost |
| **Database replication** | Read throughput improves | Writes still bottlenecked, lag between replicas | Read-heavy workload |
| **Sharding** | Write throughput improves | Complex joins, distributed transactions hard | Write-heavy workload |
| **Caching** | Latency drops, database load reduces | Cache invalidation problem, stale data | High-read low-write |
| **Async processing** | Better responsiveness, throughput improves | Complexity, eventual consistency | Non-critical operations |

---

## 19. Alternatives

### Alternative to Sharding: Column-Oriented Storage
```
Benefits:
├─ Better compression
├─ Parallel scanning
└─ Analytical queries

Downside:
├─ Not good for OLTP
├─ Write amplification
└─ More complex

Use: Analytics, reporting (not primary database)
```

### Alternative to Microservices: Service Mesh
```
Instead of breaking into separate services:
├─ Keep monolith
├─ Add service mesh (Istio)
├─ Automatically handles:
│  ├─ Load balancing
│  ├─ Retries
│  ├─ Circuit breaking
│  └─ Monitoring

Benefit: Scale without code changes
Downside: Operational complexity
```

---

## 20. When NOT To Use

**Horizontal scaling is NOT the answer when:**

```
✗ Bottleneck is algorithmic (O(n²) query)
  → Optimize algorithm first
  
✗ Single server already fast enough
  → YAGNI (you aren't gonna need it)
  → Complexity cost > benefit
  
✗ Bottleneck is synchronization/consistency
  → Adding servers makes worse
  → Need architectural redesign
  
✗ Problem is operational (bad deployment)
  → Scaling doesn't fix process issues
  → Fix ops first
```

---

## 21. Interview Questions

1. **"Our app serves 10K RPS on 1 server. Traffic will double in 2 months. What's your scaling plan?"**
   - Identify bottleneck (likely database)
   - Add read replicas if reads dominant
   - Shard if writes dominant
   - What's the cost/complexity tradeoff?

2. **"One database shard is 5x slower than others. Why? How to fix?"**
   - Root: Hot partition (skewed data)
   - Fix: Rebalance, consistent hashing, or split hot shard
   - Discuss redistribution strategy

3. **"Adding servers doesn't increase throughput. Why?"**
   - Identify shared bottleneck (load balancer, database, cache)
   - Profile to find serial component
   - Discuss Amdahl's law (10% serial = 10x max)

4. **"How do you know when to stop scaling vertically and switch to horizontal?"**
   - Vertical: when hitting hardware ceiling (~50K RPS)
   - Or when cost becomes unreasonable
   - Or when redundancy needed (no single point of failure)

5. **"Design a system that can scale from 100 RPS to 1M RPS."**
   - Discuss evolution path (stages 1-4 from section 6)
   - Identify key transitions
   - Consider operational burden at each stage

---

## 22. Common Mistakes

```
❌ Scaling too early
   → Build monolith first, scale when needed
   → Premature optimization kills simplicity

❌ Assuming linear scaling
   → Real systems have limits (Amdahl's law)
   → Test at realistic scale

❌ Forgetting operational overhead
   → 10 servers = 10x operational cost
   → Must account in architecture

❌ Hot partition ignored
   → Sharding doesn't guarantee even distribution
   → Monitor per-shard metrics

❌ Scaling compute to fix slow database
   → Won't help if database is bottleneck
   → Need structural fix (replication/sharding)

❌ Consistency guarantees at scale
   → Distributed transactions very expensive
   → Design for eventual consistency
```

---

## 23. Debugging Guide

**System slowing down as load increases:**

```
Step 1: Identify bottleneck
├─ Monitor CPU, memory, disk, network per component
├─ Which component maxed out?
├─ Load balancer, API server, database, cache?

Step 2: Drill into component
├─ If database: check slow query log
├─ If cache: check hit rate
├─ If network: check bandwidth usage
├─ If CPU: profile to find hot function

Step 3: Apply targeted fix
├─ Slow query: add index, optimize query
├─ Low cache hit rate: increase cache size or partitions
├─ High latency: reduce request size or pipeline requests
├─ CPU: parallelize, use async IO

Step 4: Validate
├─ Monitor same metric under load
├─ Latency should flatten as load increases
├─ If still climbing: return to step 1
```

**Example scenario:**

```
Symptom: p99 latency 100ms → 1000ms when load 10x
├─ Hypothesis 1: Database slow
│  ├─ Check slow query log
│  ├─ Might be missing index
│  └─ Add index, retest
│
├─ Hypothesis 2: Queuing
│  ├─ Check response time distribution
│  ├─ If p99 >> p95, queuing is problem
│  ├─ Solution: more servers or optimize per-server throughput
│  └─ Retest
│
└─ Hypothesis 3: Cache stampede
   ├─ Check cache hit rate
   ├─ If hit rate drops as load increases, stampede happening
   └─ Solution: probabilistic early expiration, lock-free caching
```

---

## 24. Code Examples

### Example 1: Horizontally Scalable Request Handler (Go)

```go
// Stateless handler - can run on any server
func handler(w http.ResponseWriter, r *http.Request) {
    userID := r.URL.Query().Get("user_id")
    
    // Check cache (distributed, not in-process)
    val, err := cache.Get(ctx, userID)
    if err == nil {
        w.Write([]byte(val))
        return
    }
    
    // Cache miss - query database
    // Database is sharded by user_id
    shard := userID % 10
    db := shards[shard]
    result := db.Query("SELECT * FROM users WHERE id = ?", userID)
    
    // Store in cache for next request
    cache.Set(ctx, userID, result, 1*time.Hour)
    
    w.Write([]byte(result))
}
```

**Why scalable:**
- No session stored in handler
- Can run on any server
- Add/remove servers dynamically
- Load balancer routes requests freely

### Example 2: Connection Pooling

```go
// Initialize pool once
db, err := sql.Open("postgres", "...")
db.SetMaxOpenConns(100)    // Max 100 connections
db.SetMaxIdleConns(10)     // Keep 10 idle
db.SetConnMaxLifetime(5*time.Minute)

// Reuse pool for all requests
func query(userID string) {
    row := db.QueryRow("SELECT name FROM users WHERE id = $1", userID)
    // Connection from pool reused
    // No handshake overhead
}
```

### Example 3: Sharding Logic

```go
// Shard key = user_id
// 10 shards total
func getShardIndex(userID string) int {
    hash := hashFunc(userID)
    return hash % 10
}

// Route request to correct shard
func queryUser(userID string) Result {
    shardIdx := getShardIndex(userID)
    db := dbs[shardIdx]  // Each shard separate database
    return db.Query("SELECT * FROM users WHERE id = ?", userID)
}
```

---

## 25. Visual Diagrams

### Scaling Evolution Map

```
Load: 100 RPS        Load: 10K RPS       Load: 100K RPS      Load: 1M RPS
├─ Single Server     ├─ 10 API servers   ├─ 100 API servers  ├─ 1000 API servers
├─ 1 Database        ├─ 1 Database       ├─ 10 DB shards     ├─ 100 DB shards
└─ 1 Cache           ├─ 10 Cache nodes   ├─ 100 Cache nodes  └─ 1000 Cache nodes
                     └─ Load balancer    ├─ Load balancer
                                         ├─ Service mesh
                                         └─ Multiple regions
```

### Throughput vs Servers (Linear Scaling)

```
Ideal scaling:     Real world:
1000 RPS │          1000 RPS │
  500    │           500    │····· (ceiling)
  100    │           100    │  ··· (diminishing returns)
    0    │────────   0      │────
        0 5 10            0 5 10
        servers          servers
```

---

## 26. Simulation Ideas

- **What-if simulator:** "If we 10x traffic, which component breaks first?"
- **Amdahl's law visualizer:** Show impact of serial code on max throughput
- **Hot partition detector:** Highlight uneven shard distribution
- **Scaling cost calculator:** Estimate hardware cost at different RPS
- **Queue behavior simulator:** Show effect of queue length on latency

---

## 27. Case Studies

### Case Study 1: Instagram's Scaling Journey
```
2010: 50K users → Single server
2011: 1M users → Vertical scaling hit
2012: 10M users → Sharding by user_id
2013: 100M users → Microservices (photo service, comment service)
2014: 1B users → Multi-region, service mesh, async processing
```

**Lessons:**
- Started monolith (right choice for MVP)
- Sharding when database hit ceiling
- Split into services as complexity grew

### Case Study 2: Stripe's API Scaling
```
Challenge: Handle payments (can't shard by transaction - global consistency needed)

Solution:
├─ Not traditional sharding
├─ Instead: partition by account/region
├─ Global coordination only when necessary
└─ Local consistency within partition
```

---

## 28. Related Topics

- Little's law (queue theory)
- Universal Scalability Law (Gunther)
- Amdahl's law
- Load balancing algorithms
- Database replication
- Distributed consensus
- Event-driven architecture

---

## 29. Advanced Topics

- **Consistent hashing** (intelligent sharding)
- **Rendezvous hashing** (simple consistent hashing)
- **Virtual nodes** (better distribution in consistent hashing)
- **Bounded staleness** (eventual consistency with guarantees)
- **Causality tracking** (vector clocks, version vectors)

---

## 30. Production Checklist

Before claiming "system scales to 1M RPS":

- [ ] Load test at 1.5x peak expected load
- [ ] Monitor all components under load (CPU, memory, disk, network)
- [ ] No component >70% utilized
- [ ] Latency p99 stays <budget even at peak
- [ ] Error rate = 0
- [ ] No queuing in logs
- [ ] Gracefully shed load if overloaded (circuit breaker)
- [ ] Can add servers without restart
- [ ] Can remove servers without user impact
- [ ] Slowest component identified (next bottleneck)
- [ ] Operational runbook for scaling out
- [ ] Alerting on key metrics
- [ ] Post-incident review process for outages

---

**Key Insight:** Scalability isn't magic. It's understanding your bottleneck and removing it. Then the next one. Repeat infinitely.

