# Backpressure Deep Dive - L5 Fundamentals

> **[🎨 View Interactive Diagram](backpressure-architecture.html)** | [← Back to Index](../../systems-index.html)

*"Requests arriving faster than you can process. How do you not get crushed?"*

---

## 1. Problem Statement

**Core Question:** When downstream is overloaded, how does upstream know to slow down?

Scenario:
```
Database saturated (100% CPU)
API still accepts requests
Requests queue up
Memory exhausted
System crashes (cascading failure)

Solution: Tell upstream "I'm overloaded, slow down"
```

---

## 2. Real World Analogy

**Water Pipe Scenario:**

No backpressure (bad):
- Water flows into pipe as fast as source sends
- Drain can only handle 10L/sec
- Pipe fills up, overflows, breaks

With backpressure (good):
- Source: "How much can you handle?"
- Drain: "10L/sec max"
- Source: throttles to 10L/sec
- Pipe never overflows

---

## 3. Why Problem Exists

### Speed Mismatch

```
Source throughput: 100K req/sec (fast producer)
Sink throughput: 10K req/sec (slow consumer)

Without backpressure:
  Queue: fills at (100K - 10K) = 90K req/sec
  After 1 second: 90K items in queue (90K × 1KB = 90MB)
  After 10 seconds: 900K items in queue (900MB memory)
  Memory exhausted → system crash
```

### Cascading Failures

```
A (fast) → B (slow) → C (very slow)

B overloads, queues fill
A keeps sending (no backpressure)
B memory exhausted → crashes
A sees: B offline, keeps retrying
A memory exhausted → crashes
C alone (can't handle all traffic)

Cascading failure: entire system down
```

---

## 4. Naive Approach

**"Let queue grow unbounded"**

Problems:
- Queue fills memory
- OOM crash
- No signal to upstream
- Cascading failure

---

## 5. Why Naive Fails

### Memory Wall

```
Queue size: unlimited
Arrival rate: 100K req/sec
Processing rate: 10K req/sec

Memory consumed: ~100MB/sec

System memory: 10GB
Time to crash: 100 seconds (if no recovery)

Uncontrolled growth → guaranteed crash
```

### Loss of Data

```
On crash: queue lost (requests in memory, not persisted)
Clients: think requests failed, retry
Cascading retries → more load
System: more overloaded
```

---

## 6. Evolution / Progression

### Stage 1: Unbounded Queue
- No backpressure
- System crashes when overloaded

### Stage 2: Bounded Queue
- Max queue size (reject excess)
- Backpressure via rejection (503 Overloaded)
- Upstream sees: errors, knows to reduce load

### Stage 3: Adaptive Backpressure
- Queue depth monitoring
- Signal: queue 50% → slow requests slightly
- Queue 80% → slow requests significantly
- Queue 100% → reject requests

### Stage 4: Distributed Backpressure
- Backpressure propagates across services
- A tells B: "slow down"
- B tells C: "slow down"
- Prevents cascades

---

## 7. Production Architecture

```
Backpressure signaling:

[Client]
    ↓ (100K req/sec)
[API Gateway]
    ├─ Queue: 0-10K (healthy)
    ├─ Queue: 10K-50K (warning, slow down slightly)
    ├─ Queue: 50K-100K (critical, slow down significantly)
    └─ Queue: >100K (full, reject 503)
    ↓
[Service A]
    ├─ Monitor: queue depth
    ├─ If queue high: set status = "overloaded"
    └─ Return: 503 (backpressure signal)
    ↓
[Downstream Service B]
    ├─ Receive: 503
    ├─ Know: A is overloaded
    ├─ Action: reduce rate to A, use fallback cache
    └─ No cascading failure
```

---

## 8. Components

### Bounded Queue
**Purpose:** Limit memory growth, prevent OOM

```
Max queue size: 10,000
Logic:
  If queue.size() < 10K: enqueue
  Else: reject with 503
  
Result: doesn't grow unbounded, bounded memory
```

### Backpressure Signal
**Purpose:** Tell upstream "I'm overloaded"

```
HTTP Status Codes:
  429 Too Many Requests (rate limited)
  503 Service Unavailable (overloaded)
  
Custom header:
  Retry-After: 60 (retry in 60 seconds)

Effect: client knows to back off
```

### Adaptive Throttling
**Purpose:** Graceful degradation

```
Queue depth thresholds:
  0-30%: normal (no throttling)
  30-60%: warn (slow down 10%)
  60-80%: caution (slow down 30%)
  80-100%: critical (slow down 50%)
  >100%: reject (backpressure)
```

---

## 9. Internal Working

### Queue Fill Dynamics

```
Without backpressure (unbounded):
  Queue size: 0
  Rate in: 100K/sec
  Rate out: 10K/sec
  
  After 1s: 90K (growing)
  After 2s: 180K (still growing)
  ...exponential until OOM

With backpressure (bounded):
  Queue size: 0
  Rate in: 100K/sec → queue full → reject → client sees 503
  Rate out: 10K/sec (processing)
  
  Equilibrium: queue stable at max capacity
  Overflow: rejected (backpressure signal)
```

### Rejection Propagation

```
System A (overloaded, queue 100%): rejects requests (503)
Upstream B: receives 503
  ├─ Know: A is overloaded
  ├─ Reduce: rate to A by 50%
  ├─ Queue to B: starts filling
  └─ B also near capacity

B (overloaded, queue 80%): rejects some requests (429)
Upstream C: receives 429
  ├─ Reduce: rate to B
  └─ No overload propagates further

Result: backpressure propagates, system stabilizes
```

---

## 10. Request Lifecycle

```
Normal load:
  Request arrives → queue (size 5K) → process
  Latency: ~5ms (queue wait) + 10ms (process) = 15ms
  Status: 200 OK

High load (queue 50K):
  Request arrives → queue (size 50K) → slow down → process
  Latency: ~50ms (queue wait) + 10ms (process) = 60ms
  Status: 200 OK (but throttled)

Critical load (queue 100K+):
  Request arrives → queue full
  Reject immediately
  Latency: <1ms (no processing)
  Status: 503 Service Unavailable (backpressure signal)
```

---

## 11. Data Flow

### Load Balancing with Backpressure

```
3 backend servers

Server A: queue 2K (healthy) → weight 1
Server B: queue 5K (okay) → weight 0.7
Server C: queue 9K (warning) → weight 0.3

Next 100 requests:
  A: 50 requests (50%)
  B: 35 requests (35%)
  C: 15 requests (15%)

Effect: load shifted away from overloaded C
```

---

## 12. Key Strategy

### 1. Monitor Queue Depth

```
Real-time metrics:
  ✓ Queue size (current)
  ✓ Queue rate (growing, stable, shrinking)
  ✓ Rejection rate (% of requests rejected)
```

### 2. Implement Bounded Queues

```
Max queue: 10K items
Full → reject with 503
Never grow beyond capacity
```

### 3. Propagate Backpressure

```
Downstream returns 503 → Upstream:
  ├─ Reduce: rate to downstream
  ├─ Route: to healthier servers
  ├─ Cache: use fallback response
  └─ Retry: with exponential backoff
```

### 4. Alert on High Queue Depth

```
Thresholds:
  Queue > 5K (warning) → investigate
  Queue > 50% capacity (caution) → scale up
  Queue > 80% capacity (critical) → alert on-call
  Rejection rate > 1% → investigate
```

---

## 13. Failure Scenarios

### Scenario 1: Queue Full, Nowhere to Shed Load

```
System A: all load from critical services
No fallback available
Queue 100% → reject → critical users affected

Fix:
  Prioritize: critical traffic (queue priority)
  Fallback: serve stale data if possible
  Drain: batch processing, reduce latency
```

### Scenario 2: Backpressure Ignorance

```
Client ignores 503 response
Keeps retrying (exponential backoff not implemented)
Amplifies load
System overloaded → worse

Fix:
  Clients: implement exponential backoff on 503
  Server: track retry rate, circuit break bad clients
```

### Scenario 3: Cascading Rejects

```
A overloaded → rejects B requests
B receives: 50% of requests rejected
B overloaded → rejects C requests
C receives: 25% of original traffic (still too much)
C overloaded

System: cascade of failures
```

**Fix:**
- Probabilistic backpressure (reject X% gradually, not all-or-nothing)
- Token bucket: rate-limit upstream
- Queue reordering: prioritize critical requests

---

## 14. Bottlenecks Table

| Issue | Impact | Symptoms | Fix |
|---|---|---|---|
| Unbounded queue | OOM crash | Memory exhaustion | Bounded queue |
| Ignoring backpressure | Cascading failure | Chain of failures | Propagate 503 |
| No fallback | Service unavailable | Outage even if temporary | Cache fallback |
| Slow drain | Queue buildup | High queue depth | Scale processing |
| No prioritization | All equally rejected | Critical requests failed | Priority queue |

---

## 15. Monitoring

### Key Metrics

```
Backpressure health:
  ✓ Queue depth: current, max (target: <50% capacity)
  ✓ Queue growth rate: growing/stable/shrinking
  ✓ Rejection rate: % rejected (target: <0.1%)
  ✓ Processing rate: throughput (processing capacity)
  ✓ Wait time: latency from arrival to processing

Downstream signals:
  ✓ Status 503 rate: overload signals from downstream
  ✓ Retry rate: clients retrying (good if follows backoff)
  ✓ Error rate: cascading failures detected?
```

### Red Flags

- Queue depth > 50% (scaling needed)
- Rejection rate > 1% (system struggling)
- Queue growing unbounded (leak, no drain)
- High cascading errors (backpressure not propagating)

---

## 16. Optimizations

### 1. Probabilistic Rejection
```
Instead of: all-or-nothing rejection at 100% queue
Use: probabilistic (reject X% at 80%, more at 90%)

Benefit:
  - Gradual degradation
  - Some requests succeed even when overloaded
  - Smoother than cliff at 100%
```

### 2. Priority Queue
```
Queue: separate for critical vs non-critical
Critical: max 5K (reserved)
Non-critical: max 5K (shared)

On overload:
  Critical: still process
  Non-critical: reject

Benefit: critical services remain available
```

### 3. Token Bucket
```
Tokens: refill at processing rate (10K/sec)
Request: costs 1 token
No tokens: reject

Effect: upstream auto-throttles to processing rate
```

---

## 17. Security

### 1. DDoS Backpressure
```
Attack: 1M req/sec
System: can handle 100K req/sec

Backpressure:
  Reject: 900K req/sec (return 503)
  Legitimate traffic: 100K succeeds

Result: legitimate traffic preserved, attack contained
```

### 2. Slowloris Protection
```
Slowloris: open connections, send slowly
Connection pool exhausted → no legitimate connections

Backpressure:
  Monitor: connection count
  Reject: new connections if pool 90% full
  Kill: idle connections

Result: DoS mitigated
```

---

## 18. Tradeoffs Table

| Approach | Availability | Fairness | Complexity |
|---|---|---|---|
| No backpressure | Low (crash) | N/A | Low |
| Bounded queue | Medium (reject) | Equal | Medium |
| Priority queue | High (critical OK) | Prioritized | High |
| Adaptive throttling | High | Gradual | High |
| Token bucket | High | Fair rate | Medium |

---

## 19. Alternatives

### Bulkhead Pattern
```
Separate resource pools per service
A overloaded: only affects A's pool
B unaffected (has own pool)

Trade: isolation vs resource utilization
```

---

## 20. When NOT to Use

### Don't Reject (Backpressure) When:

1. **Requests are critical**
   - Safety-critical: must process (no rejection)
   - Accept: increased latency, queue growth
   - Use: prioritization instead

2. **No alternative (no fallback)**
   - Rejection leaves user with nothing
   - Better: slow response than error
   - Use: adaptive throttling instead

---

## 21. Interview Questions

1. **System receives 10x traffic spike (overloaded)**
   - How prevent crash?
   - How signal upstream?
   - Trade-offs?

2. **Queue grows unbounded**
   - Root cause?
   - Solutions?

3. **Cascading failures (A → B → C all fail)**
   - Why cascading?
   - How prevent with backpressure?

4. **Design rate limiter (reject excess traffic)**
   - Token bucket or sliding window?
   - Trade-offs?

---

## 22. Common Mistakes

1. **Unbounded queues**
   - "Queue will drain eventually"
   - Reality: can grow until OOM
   - Result: unpredictable crash

2. **Ignoring 503 responses**
   - Client: keeps retrying without backoff
   - Result: amplifies load, cascading failure

3. **No fallback on rejection**
   - Reject with 503 → user gets nothing
   - Better: serve stale, degraded, or error gracefully

4. **Backpressure only local**
   - A overloaded, tells B (upstream) to slow
   - But B unaware of C (further upstream)
   - Result: B still sends to A, still overloaded

5. **No prioritization**
   - Critical and non-critical equally rejected
   - Result: critical services fail too
   - Better: reserve capacity for critical

---

## 23. Debugging Guide

### Step 1: Identify Queue Growth
```
Monitor queue depth:
  t=0s:    100 items
  t=10s:   5K items (growing fast)
  t=20s:   10K items
  
Issue: queue growing linearly (not draining)
```

### Step 2: Find Root Cause
```
Arrival rate: 100K req/sec (normal)
Processing rate: 5K req/sec (down from 10K)

Root cause: processing rate dropped by 50%

Why? 
  - Database slow (check: CPU, IO)
  - Dependency slow (check: timeout, errors)
  - Code change (check: recent deploy)
```

### Step 3: Implement Backpressure
```
Max queue: 10K (currently unbounded)
Add: rejection logic (when queue > 10K, return 503)

Verify:
  Upstream sees 503
  Clients: backoff
  Queue: stabilizes
  System: stable (no crash)
```

---

## 24. Code Examples

### Go: Bounded Queue with Backpressure
```go
type BoundedQueue struct {
    ch       chan Task
    maxSize  int
    mu       sync.RWMutex
}

func NewBoundedQueue(maxSize int) *BoundedQueue {
    return &BoundedQueue{
        ch:      make(chan Task, maxSize),
        maxSize: maxSize,
    }
}

func (bq *BoundedQueue) Enqueue(task Task) error {
    select {
    case bq.ch <- task:
        // Successfully enqueued
        return nil
    default:
        // Queue full, return backpressure signal
        return fmt.Errorf("queue full: %d/%d", len(bq.ch), bq.maxSize)
    }
}

// HTTP handler that respects backpressure
func handleRequest(w http.ResponseWriter, r *http.Request) {
    task := parseRequest(r)
    
    err := queue.Enqueue(task)
    if err != nil {
        // Queue full: signal backpressure
        w.Header().Set("Retry-After", "60")
        http.Error(w, "service overloaded", http.StatusServiceUnavailable)
        return
    }
    
    // Task enqueued, can respond
    w.WriteHeader(http.StatusAccepted)
    json.NewEncoder(w).Encode(map[string]string{"status": "accepted"})
}

// Client respects backpressure (exponential backoff)
func clientWithBackoff(task Task) error {
    backoff := time.Millisecond * 100
    
    for attempt := 0; attempt < 10; attempt++ {
        err := sendRequest(task)
        
        if err == nil {
            return nil
        }
        
        if isBackpressure(err) { // 503 or 429
            time.Sleep(backoff)
            backoff *= 2 // exponential
            continue
        }
        
        return err
    }
    
    return fmt.Errorf("max retries exceeded")
}
```

### Go: Token Bucket Rate Limiter
```go
type TokenBucket struct {
    tokens    float64
    maxTokens float64
    refillRate float64 // tokens per second
    lastRefill time.Time
    mu        sync.Mutex
}

func (tb *TokenBucket) Allow(cost float64) bool {
    tb.mu.Lock()
    defer tb.mu.Unlock()
    
    // Refill tokens based on elapsed time
    elapsed := time.Since(tb.lastRefill).Seconds()
    tb.tokens = math.Min(tb.maxTokens, tb.tokens+elapsed*tb.refillRate)
    tb.lastRefill = time.Now()
    
    // Check if enough tokens
    if tb.tokens >= cost {
        tb.tokens -= cost
        return true
    }
    
    return false
}

// Usage: rate limit to 10K req/sec
bucket := &TokenBucket{
    maxTokens: 1000,
    refillRate: 10000, // refill 10K per second
    tokens: 1000,
    lastRefill: time.Now(),
}

func handleRequest(w http.ResponseWriter, r *http.Request) {
    if !bucket.Allow(1.0) {
        // Not enough tokens: apply backpressure
        w.Header().Set("Retry-After", "1")
        http.Error(w, "rate limited", http.StatusTooManyRequests)
        return
    }
    
    // Process request
    w.WriteHeader(http.StatusOK)
}
```

---

## 25. Visual Diagrams

### Queue Dynamics Under Load
```
Queue size (items)
   10K │         ╱╱╱╱╱╱ no backpressure (unbounded)
        │        ╱╱╱╱╱╱╱╱╱╱
    5K │    ┌───╱╱╱╱╱╱╱ with backpressure (bounded)
        │    │ ╱╱╱╱╱╱╱
    1K │────┴────────── equilibrium (max queue)
        │
      0 └──────────────────────── time
        Normal  Spike   Recovery
        
Unbounded: grows without limit (OOM crash)
Bounded: hits ceiling, rejects excess
```

---

## 26. Simulation Ideas

1. **Overload Simulator**
   - Vary: arrival rate, processing rate
   - Compare: unbounded vs bounded queue
   - Show: rejection impact on availability

2. **Cascade Failure Simulator**
   - Chain: A → B → C
   - Show: how cascade happens without backpressure
   - Show: how backpressure prevents cascade

3. **Token Bucket Simulator**
   - Visualize: token refill
   - Show: rate limiting effect

---

## 27. Case Studies

### Case 1: Netflix Hystrix (Backpressure & Circuit Breaker)
Combines bounded queues + circuit breaker
Result: system stable under overload, no cascading failures

### Case 2: Kafka (Backpressure in Streaming)
Producer push-back when consumer can't keep up
Result: streaming system never crashes, just slower

---

## 28. Related Topics

- **Rate Limiting** (token bucket, leaky bucket)
- **Circuit Breaker** (fail-fast backpressure)
- **Bulkhead Pattern** (resource isolation)
- **Load Shedding** (graceful degradation)

---

## 29. Advanced Topics

### Probabilistic Backpressure
```
Instead of hard reject at 100%:
  Queue 80%: reject 20% of requests (probabilistic)
  Queue 90%: reject 50% of requests
  Queue 100%: reject 100% of requests

Benefit:
  - Smoother degradation
  - Some traffic always succeeds
  - Avoids cliff effect
```

### Load Shedding with Prioritization
```
Priority levels:
  Critical: never reject
  Important: reject if queue > 80%
  Optional: reject if queue > 50%

Benefit:
  - Critical services always available
  - Non-critical gracefully degrade
```

---

## 30. Production Checklist

- [ ] Implement: bounded queues (max size based on capacity)
- [ ] Add: rejection logic (when queue full, return 503)
- [ ] Monitor: queue depth (alert if > 50% capacity)
- [ ] Monitor: rejection rate (alert if > 0.1%)
- [ ] Propagate: 503 signals to upstream (reduce rate)
- [ ] Implement: exponential backoff on 503/429 (clients)
- [ ] Add: Retry-After header (inform clients when to retry)
- [ ] Test: overload scenarios (queue filling, rejection working)
- [ ] Document: backpressure behavior (expected 503 responses)
- [ ] Consider: priority queues (protect critical traffic)
- [ ] Consider: fallback responses (serve stale vs error)

---

*Last Updated: 2026-05-28*
