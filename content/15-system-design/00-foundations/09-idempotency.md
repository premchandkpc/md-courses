---
title: Idempotency Deep Dive - L5 Fundamentals
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# Idempotency Deep Dive - L5 Fundamentals

> **[🎨 View Interactive Diagram](idempotency-architecture.html)** | [← Back to Index](../../systems-index.html)

*"Same request sent twice. How do you ensure it doesn't charge twice?"*

---

## 1. Problem Statement

**Core Question:** If a request is retried due to timeout, how prevent duplicate processing?

Scenario:
```
Client: "Transfer $100 from A to B"
Server: processes, starts response
Network: times out (client doesn't see response)
Client: retries (thinks request failed)
Server: receives again, processes again
Result: $200 transferred (should be $100)
```

---

## 2. Real World Analogy

**Doorbell Scenario:**

Non-idempotent (bad):
- Press doorbell
- Bell rings
- Press again
- Bell rings twice
(State changed twice: unwanted)

Idempotent (good):
- Press doorbell
- Door unlocks
- Press again
- Door already unlocked (no change)
(State same: idempotent)

---

## 3. Why Problem Exists

### Network Unreliability

```
Retry scenario:
  Request A sent → server processes → response sent
  Network fails (response lost)
  Client: "request failed?" → retries
  Server: receives again

Without idempotency:
  Processed twice (duplicate effect)
```

### Distributed System Guarantees

```
HTTP: at-most-once delivery (no retries by default)
  But clients retry on timeout (common pattern)
  
With retries:
  "At-least-once" delivery (may receive multiple times)
  
Idempotency: ensures duplicate requests are safe
```

---

## 4. Naive Approach

**"Trust that clients don't retry"**

Problems:
- Network timeouts are inevitable
- Clients will retry (standard behavior)
- Leads to duplicate processing, data corruption

---

## 5. Why Naive Fails

### Distributed Systems Reality

```
Network partitions, timeouts: guaranteed to happen
Client retries: standard behavior
Not idempotent: duplicate effects

Example:
  Debit $100: processed twice
  Transfer: occurs twice
  Order: created twice
  
Result: data corruption
```

---

## 6. Evolution / Progression

### Stage 1: No Idempotency
- Same request processed twice
- Duplicate effects
- Data corruption

### Stage 2: Request Deduplication (ID-Based)
- Client: generates request ID
- Server: checks if ID already processed
- If exists: return cached response
- If not: process, cache response

### Stage 3: Distributed Deduplication
- Dedup cache replicated across servers
- Request ID valid across system
- Can safely retry across servers

### Stage 4: Idempotent Operations
- Operations inherently idempotent
- Duplicate requests have no extra effect
- Example: SET instead of INCREMENT

---

## 7. Production Architecture

```
Idempotent request processing:

[Client sends request]
    │ (with idempotency key / request ID)
    ▼
[API Gateway]
    ├─ Extract request ID
    ├─ Check: ID in dedup cache?
    │  ├─ Yes: return cached response (fast)
    │  └─ No: proceed to handler
    ▼
[Request Handler]
    ├─ Process request
    ├─ Generate response
    ├─ Store response in cache (key = request ID)
    └─ Ack to client
    
[Retry scenario]
    ├─ Client retries (same request ID)
    ├─ Cache hit: immediate response (same as before)
    ├─ No duplicate processing
    └─ Client: satisfied
```

---

## 8. Components

### Request ID / Idempotency Key
**Purpose:** Identify duplicate requests

```
Client generates: UUID (e.g., "req_12345")
Header: "Idempotency-Key: req_12345"

Server:
  - Uses key to detect duplicates
  - Ensures same response for same key
```

### Deduplication Cache
**Purpose:** Store response for idempotent replay

```
Key: request ID
Value: response (cached)
TTL: 24 hours (or longer)

On duplicate request:
  Cache hit → return stored response
  No reprocessing
```

### Idempotent Operations
**Purpose:** Safe even without dedup cache

```
Non-idempotent: INCREMENT balance (count=count+1)
  Twice: count increases by 2

Idempotent: SET balance = 100
  Twice: balance is 100 (no change)

Idempotent: PUT (create or overwrite)
  Twice: same result
```

---

## 9. Internal Working

### Deduplication Lookup

```
Request arrives: "Transfer $100"
Idempotency key: "txn_abc123"

Step 1: Check cache
  Cache[txn_abc123] exists?
    Yes → return stored response (done)
    No → proceed

Step 2: Process request
  Actually execute transfer

Step 3: Store response
  Cache[txn_abc123] = response
  TTL: 24 hours

Step 4: Return
  Send response to client
```

### Cache Eviction

```
Dedup cache TTL: 24 hours (default)
After 24h: entry evicted
Later retry: treated as new request (processed again)

Risk: if retry after 24h, duplicate processing
Safe: if retry within 24h, idempotent
```

---

## 10. Request Lifecycle

```
First request:
  t=0ms:     Client sends (key=req_123)
  t=10ms:    Server receives
  t=11ms:    Cache miss (not seen before)
  t=20ms:    Process request
  t=25ms:    Store response in cache
  t=30ms:    Send response

Second request (retry, same key):
  t=100ms:   Client retries (same key=req_123)
  t=110ms:   Server receives
  t=111ms:   Cache hit (seen req_123 before)
  t=112ms:   Return cached response
  t=115ms:   Response arrives (instant, no reprocessing)

Result: idempotent (second request safe, no duplicate effect)
```

---

## 11. Data Flow

### Cache Architecture

```
Request A (key=X)
  ├─ Redis Cache: store response
  ├─ Replicate to backup cache (async)
  └─ Both have response X

Request B (key=Y)
  ├─ Cache miss on Redis
  ├─ Process request
  ├─ Store response Y in Redis

Request A retry (key=X)
  ├─ Cache hit: response X (immediate)
  ├─ Avoid: reprocessing

Distributed:
  If Redis down, replica still has responses
  Fallback: process again (worst case duplicate)
```

---

## 12. Key Strategy

### 1. Require Idempotency Key

```
POST /transfer
{
  "from": "A",
  "to": "B",
  "amount": 100,
  "idempotency_key": "txn_abc123" ← client generates
}
```

### 2. Implement Dedup Cache

```
Cache: in-memory (fast) + Redis (distributed)
TTL: 24 hours (or business requirement)
Key: idempotency_key
Value: entire response
```

### 3. Use Idempotent Operations

```
Where possible: replace non-idempotent ops
  DELETE then INSERT → UPSERT
  INCREMENT → SET
  APPEND → REPLACE
```

---

## 13. Failure Scenarios

### Scenario 1: Cache Loss

```
Request cached in memory (server)
Server crashes
Cache lost

Retry arrives after restart:
  Cache miss (lost)
  Reprocess request
  Duplicate effect (unideal)
```

**Fix:** 
- Persistent cache (Redis)
- Replicated cache (high availability)

### Scenario 2: Stale Response

```
Request 1: Transfer $100 (successful)
Cache stores: response = "success"

Request 2: Retry (same key)
Cache hit: return "success"

But conditions changed:
  Account now overdrawn
  Should have failed, but returned success

Result: inconsistent response
```

**Fix:**
- Cache includes: timestamp, state snapshot
- Validate: conditions still match
- If not: reprocess

### Scenario 3: Cache TTL Expiration

```
Request: key=X
Response cached

24 hours later: retry with same key=X
Cache entry expired

Reprocess: duplicate effect
```

**Fix:**
- Longer TTL (business requirement)
- Or: permanent dedup log (immutable)

---

## 14. Bottlenecks Table

| Issue | Impact | Symptoms | Fix |
|---|---|---|---|
| No dedup cache | Duplicates | Same request, processed twice | Add cache |
| Cache loss | Occasional duplicates | Server crash → duplicate | Persistent cache |
| Short TTL | Too many duplicates | Retry after expiry → reprocess | Extend TTL |
| Cache not replicated | Failover duplicates | Standby server has empty cache | Replicate cache |
| No idempotency key | Can't identify duplicates | How to tell if same request? | Require key |

---

## 15. Monitoring

### Key Metrics

```
Idempotency health:
  ✓ Cache hit rate: % of requests hitting cache (target: low)
  ✓ Duplicate requests: % of retries (should be low)
  ✓ Cache eviction rate: how often expired? (should be low)
  ✓ Dedup latency: time to cache lookup (<1ms)

Duplication incidents:
  ✓ Duplicate transactions: count (target: 0)
  ✓ False positives: requests incorrectly marked duplicate
```

### Red Flags

- No cache hits (dedup not working)
- High duplicate rate (not catching retries)
- Cache full (evicting too fast)
- Stale responses served (conditions changed)

---

## 16. Optimizations

### 1. Eager Cache Cleanup
```
Request successful: mark as "completed"
After confirmation: remove from cache (free space)

Result: smaller cache, longer TTL for recent requests
```

### 2. Checksum-Based Dedup
```
Instead of storing response: store checksum
Retry: compute checksum, compare
Cost: lower (checksum < response), but verify not cache

Trade: storage vs verification cost
```

### 3. Distributed Cache
```
Local cache: fast, loses on crash
Remote cache (Redis): slower, persistent
Hybrid: check local first (hit = instant)
        if miss, check Redis (hit = 1-5ms)
        if miss, process (hit = 10-100ms)
```

---

## 17. Security

### 1. Idempotency Key Predictability
```
Bad: key based on user ID (predictable)
  Attacker: can reuse keys, cause fraud

Good: client generates UUID (random, unpredictable)
  Can't guess keys, can't abuse idempotency
```

### 2. Cache Poisoning
```
Attack: cache response with attacker-controlled key
  Later: legitimate request uses same key
  Serves: poisoned response

Prevent:
  - Validate: request matches cached response
  - Signature: response signed with key
  - Immutable: cache can't be modified
```

---

## 18. Tradeoffs Table

| Approach | Latency | Storage | Correctness |
|---|---|---|---|
| No dedup | Fast | None | Duplicates |
| In-memory cache | Instant | Medium | Loses on crash |
| Redis cache | 1-5ms | Low | Persistent |
| Persistent log | 10-50ms | High | Guaranteed |

---

## 19. Alternatives

### Exactly-Once Semantics via Transactions
```
Instead of dedup: ACID transactions
  Write: atomic, or not at all
  Duplicate requests: one succeeds, others fail

Cost: distributed transaction complexity
Benefit: no dedup cache needed
```

---

## 20. When NOT to Use

### Don't Require Idempotency Key When:

1. **Operation naturally idempotent**
   - SET value: already idempotent
   - No need for explicit dedup

2. **At-most-once acceptable**
   - Non-critical operation
   - Duplicate acceptable (rare)

---

## 21. Interview Questions

1. **Design payment system (no duplicate charges)**
   - How ensure idempotency?
   - What if retry after 24 hours?

2. **Request dedup cache fails (loss of data)**
   - How prevent duplicates?
   - Design failover?

3. **Same request sent twice (same idempotency key)**
   - First: succeeds
   - Second: should return what?

4. **Compare: idempotency key vs distributed transaction**
   - Trade-offs?
   - When use each?

---

## 22. Common Mistakes

1. **Relying on idempotency key alone**
   - Without cache: key doesn't prevent duplicates
   - Must: store and check cache

2. **Short TTL on cache**
   - Retry after expiry: duplicate
   - TTL should match: retry window + buffer

3. **Cache loss under failover**
   - Server crashes: cache lost
   - Duplicate retry served
   - Must: replicate cache

4. **Not validating idempotency key**
   - Attacker: reuses key from successful request
   - Returns: old response (wrong result)
   - Validate: request matches cached response

5. **Idempotency on read operations**
   - Unnecessary: reads have no side effects
   - Use: only for writes (POST, PUT, DELETE)

---

## 23. Debugging Guide

### Step 1: Verify Dedup Cache
```
Request 1: key=X, process, response=Y
Request 2: key=X, retry

Check cache:
  Cache hit? → return Y (correct)
  Cache miss? → reprocess (wrong, duplicate)
```

### Step 2: Check Cache Replication
```
Server 1: cache has request X
Server 2: failed over, cache empty

Retry reaches Server 2:
  Cache miss (different server)
  Reprocess (duplicate)

Fix: replicate cache to Server 2
```

### Step 3: TTL Analysis
```
Request cached: t=0
Retry: t=25 hours

TTL: 24 hours (expired)
Cache miss: reprocess (duplicate)

Fix: increase TTL or accept duplicates after 24h
```

---

## 24. Code Examples

### Go: Request Deduplication
```go
type DeduplicationCache struct {
    cache map[string]*CachedResponse
    mu    sync.RWMutex
}

type CachedResponse struct {
    Response  interface{}
    Timestamp time.Time
    TTL       time.Duration
}

func (dc *DeduplicationCache) GetOrProcess(key string, processor func() (interface{}, error)) (interface{}, error) {
    // Check cache
    dc.mu.RLock()
    cached, exists := dc.cache[key]
    dc.mu.RUnlock()
    
    if exists && time.Since(cached.Timestamp) < cached.TTL {
        // Cache hit: return stored response
        return cached.Response, nil
    }
    
    // Cache miss: process request
    response, err := processor()
    if err != nil {
        return nil, err
    }
    
    // Store response for future retries
    dc.mu.Lock()
    dc.cache[key] = &CachedResponse{
        Response:  response,
        Timestamp: time.Now(),
        TTL:       24 * time.Hour,
    }
    dc.mu.Unlock()
    
    return response, nil
}

// Usage in HTTP handler:
func handleTransfer(w http.ResponseWriter, r *http.Request) {
    idempotencyKey := r.Header.Get("Idempotency-Key")
    if idempotencyKey == "" {
        http.Error(w, "idempotency key required", http.StatusBadRequest)
        return
    }
    
    response, err := dedup.GetOrProcess(idempotencyKey, func() (interface{}, error) {
        return processTransfer(r)
    })
    
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    
    json.NewEncoder(w).Encode(response)
}
```

### Go: Redis-Based Deduplication
```go
func (dc *DeduplicationCache) GetOrProcessRedis(ctx context.Context, key string, processor func() (interface{}, error)) (interface{}, error) {
    // Check Redis cache
    cachedVal, err := dc.redis.Get(ctx, key).Result()
    if err == nil {
        // Cache hit: deserialize and return
        var response interface{}
        json.Unmarshal([]byte(cachedVal), &response)
        return response, nil
    }
    
    // Cache miss: process request
    response, err := processor()
    if err != nil {
        return nil, err
    }
    
    // Store in Redis (24 hour TTL)
    respJSON, _ := json.Marshal(response)
    dc.redis.Set(ctx, key, respJSON, 24*time.Hour)
    
    return response, nil
}
```

---

## 25. Visual Diagrams

### Idempotency Cache Lifecycle
```
Request 1 (key=X)    Request 2 (key=X, retry)    Request 3 (key=X, after TTL)
    │                         │                          │
    ▼                         ▼                          ▼
  Cache miss           Cache hit ✓                   Cache expired
  Process              Return cached                Process (duplicate)
  Store (24h)          No reprocessing

Timeline:
[0h--------24h]
 ↑           ↑
 Store    Evict
 Requests within: idempotent (safe)
 After TTL: duplicate (risk)
```

---

## 26. Simulation Ideas

1. **Idempotency Cache Simulator**
   - Vary: TTL, request rate
   - Show: duplicate processing vs cache coverage

2. **Retry Scenario Simulator**
   - Vary: network timeout pattern
   - Show: idempotency key effectiveness

---

## 27. Case Studies

### Case 1: Stripe Payments
Uses idempotency keys required on all API calls
Result: safe retry without duplicate charges

### Case 2: AWS API
Idempotency tokens per request type
Result: clients can retry safely

---

## 28. Related Topics

- **Exactly-Once Semantics**
- **Retry Strategies**
- **Distributed Transactions**

---

## 29. Advanced Topics

### At-Least-Once with Deduplication
```
Guarantee: every request processed ≥ 1 time
Dedup: prevents duplicate effects
Result: exactly-once semantics (without complexity of distributed TX)
```

---

## 30. Production Checklist

- [ ] Require: idempotency key on all write operations
- [ ] Implement: dedup cache (Redis + backup)
- [ ] Set: appropriate TTL (24h default)
- [ ] Replicate: cache across servers
- [ ] Monitor: cache hit rate (should be low for health)
- [ ] Alert: cache eviction rate (should be low)
- [ ] Test: retry scenarios (same key, different servers)
- [ ] Document: idempotency key generation (UUID standard)
- [ ] Validate: request matches cached response (security)

---

*Last Updated: 2026-05-28*
