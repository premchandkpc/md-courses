# Consistency Models Deep Dive - L5 Fundamentals

> **[🎨 View Interactive Diagram](consistency-architecture.html)** | [← Back to Index](../../systems-index.html)

*"You update data on server A, read from server B. Why is the old value returned?"*

---

## 1. Problem Statement

**Core Question:** When you write to database and immediately read, which replicas show the new value?

Single-datacenter: always consistent (same value)
Multi-datacenter: depends on replication strategy

```
Write to Server A: user.balance = $100
Read from Server B (immediately): user.balance = ?
  Option 1 (Strong): $100 (consistent)
  Option 2 (Eventual): $50 (replica lag)
  Option 3 (Causal): depends on causality
```

---

## 2. Real World Analogy

**Bank Account Scenario:**

Strong Consistency:
- You withdraw $50 at ATM A
- Go to ATM B immediately
- Balance: $50 (new value, verified)

Eventual Consistency:
- You withdraw $50 at ATM A
- Go to ATM B immediately
- Balance: $100 (old value, not updated yet)
- Check again in 5 seconds: $50 (now updated)

Causal Consistency:
- You withdraw $50 at ATM A
- Text friend: "withdrew $50"
- Friend goes to ATM B (knows about withdrawal from your text)
- Balance: $50 (sees updated value due to causal link)

---

## 3. Why Problem Exists

### Replication Lag

```
Primary writes new value: t=0ms
Network sends to replica: 10ms
Replica applies: t=20ms

Between 0-20ms: replicas have different values (inconsistency)
```

### Synchronous vs Asynchronous

```
Synchronous replication (slow, consistent):
  Write acknowledged only after replicated to majority
  Latency: 50-100ms (waiting for network + apply)
  Consistency: strong (all readers see same value)

Asynchronous replication (fast, eventual):
  Write acknowledged immediately on primary
  Replicate later (in background)
  Latency: 1-10ms (no wait for replication)
  Consistency: eventual (replicas lag behind)
```

### Distributed Systems Theorem (CAP)

You can only have 2 of 3:
- Consistency (all replicas same value)
- Availability (system responds to requests)
- Partition tolerance (system survives network failure)

---

## 4. Naive Approach

**"Make it strongly consistent"**

```
Force all writes to wait for replication:
  Write → Wait for majority ack → Commit → Response

Guarantees: strong consistency (all reads see same value)
Problem: slow (50ms+ per write), expensive
Trade: latency vs consistency
```

---

## 5. Why Naive Fails

### Write Latency

```
Synchronous replication to 3 datacenters:
  US West: 0ms (local)
  US East: 50ms (cross-country)
  Europe: 100ms (transatlantic)

Write latency: max(0, 50, 100) = 100ms
User experiences: 100ms per write (slow!)
```

### Availability vs Consistency (CAP)

```
Partition: US and Europe datacenters split (network cuts)

Option 1 (Consistency):
  Can't write (need Europe ack, can't reach)
  Availability: reduced

Option 2 (Availability):
  Write in US (don't wait for Europe)
  Europe sees stale data (inconsistent)
  Consistency: sacrificed
```

---

## 6. Evolution / Progression

### Stage 1: Single Datacenter
- All replicas in same place
- Network latency: <1ms
- Consistency: strong (fast sync)

### Stage 2: Multi-Datacenter (Geo-Distributed)
- Replicas across regions
- Network latency: 50-200ms
- Consistency: eventual (async replication)

### Stage 3: Causal Consistency
- Order matters: preserve causality
- But allow concurrent updates
- Intermediate consistency model

### Stage 4: Tunable Consistency
- Choose per-operation: strong or eventual
- Critical data: strong (user auth)
- Non-critical: eventual (likes, views)

---

## 7. Production Architecture

```
Replication strategy (multi-region):

Write Path:
  Client → Primary DC (US)
    ├─ Write to primary DB
    ├─ Ack to client (fast, 1-5ms)
    └─ Replicate async to other DCs
        ├─ Send to DC EU (queue)
        ├─ Send to DC APAC (queue)
        └─ Both receive, apply (20-100ms later)

Read Path:
  Client in US → read from US primary (strong, <5ms)
  Client in EU → read from EU replica (eventual, but local)
  Client in APAC → read from APAC replica (eventual, but local)

Result: 
  - Fast writes (don't wait for replication)
  - Consistent reads in same region
  - Eventual consistency across regions
```

---

## 8. Components

### Write-Ahead Logging (WAL)
**Purpose:** Durability + replication

```
Operation: UPDATE user SET balance = 100
  1. Write to WAL (durable log)
  2. Write to memory buffer
  3. Ack to client
  4. Background: flush to disk, replicate

If crash: replay WAL, recover all durable writes
```

### Read Repair
**Purpose:** Fix replica divergence

```
Client reads from replica A (stale value)
Replica A sees: balance = $50
Primary has: balance = $100

Read repair:
  1. Request also goes to primary
  2. Compare: $50 vs $100
  3. Replica A: apply missing write
  4. Return: $100 to client

Benefit: repairs stale replicas on read
```

### Vector Clocks
**Purpose:** Order causal updates

```
Server A: (A:1, B:0, C:0)
  Write: user.name = "Alice"

Server B: (A:1, B:1, C:0)
  Write: user.age = 30

Causality: B's write happened after A's (B's clock > A's clock)

Result: can order updates correctly even with concurrent writes
```

---

## 9. Internal Working

### Replication Propagation

```
Write flow (synchronous):
  t=0ms:  Client sends write request to server A
  t=1ms:  Server A receives, writes to log
  t=2ms:  Server A replicates to B, C
  t=25ms: Server B receives, applies, sends ack
  t=25ms: Server C receives, applies, sends ack
  t=26ms: Server A receives both acks, confirms to client

Latency: 26ms (due to waiting for slowest replica)

Replication flow (asynchronous):
  t=0ms:  Client sends write request to server A
  t=1ms:  Server A receives, writes to log
  t=2ms:  Server A confirms to client (fast!)
  t=3ms:  Server A queues replication (background)
  t=25ms: Server B receives, applies (but client already confirmed)
  
Latency: 2ms (immediate, don't wait for replication)
Tradeoff: replicas lag
```

### CAP Theorem in Action

```
Network partition: US | EU (network cut)

Consistency-first (CP system):
  Both US and EU can serve reads (use local replicas)
  But writes blocked (can't confirm with other region)
  Availability: reduced

Availability-first (AP system):
  Both US and EU can serve writes (don't wait for confirmation)
  But they diverge (conflict)
  Consistency: eventual

Strong Consistency-first (CA system):
  Write must go to both regions (sync)
  But if partition: can't write at all
  Availability: down during partition
```

---

## 10. Request Lifecycle

```
User in EU writes to US-based primary:

t=0ms:     EU user sends write
t=50ms:    Request arrives at US primary (network)
t=51ms:    US primary receives, writes to log
t=52ms:    US primary sends replication to EU replica
t=55ms:    EU replica receives, applies
t=56ms:    EU replica sends ack
t=58ms:    US primary receives ack, confirms to user
t=108ms:   Confirmation arrives at user (50ms back)

Total latency: 108ms

If EU user then reads locally:
t=110ms:   EU user reads from local replica
t=110ms:   Local replica: returns NEW value (was just updated)
t=110ms:   User receives response

Consistency: reads always see latest (within that region)
```

---

## 11. Data Flow

### Multi-Region Consistency

```
Region 1 (US):
  Primary DB: balance = $100
  Replica DB: balance = $100 (synced)

Region 2 (EU):
  Replica DB: balance = $50 (hasn't received update yet, lag = 50ms)

Region 3 (APAC):
  Replica DB: balance = $50 (hasn't received update yet, lag = 50ms)

At t=0: write in Region 1
  Primary: $100 (immediately)
  Region 2 local read: $50 (will be $100 after 50ms)
  Region 3 local read: $50 (will be $100 after 50ms)

Caveat: "local consistency, eventual cross-region"
```

---

## 12. Key Strategy

### 1. Identify Consistency Requirements
```
Critical data:
  - User auth (password, email) → strong consistency
  - Payment info → strong consistency
  - Account balance → strong consistency

Non-critical data:
  - Likes/views/counters → eventual consistency (lag acceptable)
  - Recommendations → eventual consistency
  - Activity feeds → eventual consistency
```

### 2. Choose Replication Strategy

```
Strong consistency: wait for majority ack
  Cost: 50-100ms latency
  Benefit: all reads same value

Eventual consistency: ack immediately, replicate async
  Cost: temporary divergence (seconds)
  Benefit: 1-10ms latency

Causal consistency: preserve causality, allow concurrency
  Cost: 10-50ms latency
  Benefit: order of events preserved
```

### 3. Handle Divergence

```
Two replicas diverge (same key, different values):
  Replica A: version 1 (Alice)
  Replica B: version 2 (Bob)

Conflict resolution:
  Last-write-wins: pick by timestamp (simple, lossy)
  Custom resolver: app logic (delete/merge)
  Multi-value: return both, let client merge
```

---

## 13. Failure Scenarios

### Scenario 1: Replication Lag Cascade

```
User writes data, immediately reads different replica
  Write: balance = $100 (on primary)
  Read: balance = $50 (on replica, lag)
  
Result: User sees old value (stale read)
User perception: "my write didn't work!"
```

**Fix:** Read-your-writes consistency (read from primary if just wrote)

### Scenario 2: Partial Replication Failure

```
Write to primary, replicate to 3 replicas:
  Replica A: success (ack sent)
  Replica B: fails (network error)
  Replica C: success (ack sent)

With majority quorum: write confirmed (2 of 3 acked)
Later: Replica B becomes primary (network heals, B has stale data)

Result: recent write lost (RPO violated)
```

**Fix:** 
- Use stable quorum (acks from majority before commit)
- Replica B won't become primary until caught up

### Scenario 3: Concurrent Writes Conflict

```
User A writes: name = "Alice" (server 1)
User B writes: name = "Bob" (server 2)
Both replicate simultaneously

Replica A: sees Alice's write first
Replica B: sees Bob's write first

Result: inconsistent name (Alice on A, Bob on B)
```

**Fix:** 
- Conflict-free replicated data types (CRDTs)
- Or: Causal consistency via vector clocks
- Or: Last-write-wins (pick by timestamp)

---

## 14. Bottlenecks Table

| Bottleneck | Consistency Impact | Symptoms | Quick Fix |
|---|---|---|---|
| Replication lag | Stale reads | Users see old values | Read-your-writes consistency |
| Slow replica | Blocked writes (if sync) | Write timeouts | Async replication, fallback |
| Network partition | CAP tradeoff | Availability vs consistency | Choose AP or CP upfront |
| No conflict resolution | Divergence | Two versions of data | Implement resolver |
| Unbounded divergence | Corruption | Merged data invalid | Quorum enforcement |

---

## 15. Monitoring

### Key Metrics

```
Replication health:
  ✓ Replication lag: target <100ms
  ✓ Replica sync status: all replicas in sync?
  ✓ Conflict rate: how often conflicts occur?

Consistency guarantees:
  ✓ Stale reads: % of reads hitting lag
  ✓ Conflict resolution success rate
  ✓ RPO violations: data loss incidents
```

### Red Flags

- Replication lag > 1 second (critical)
- Replica out of sync (fix ASAP)
- High conflict rate (resolution failing)
- Read-your-writes not working (stale reads increasing)

---

## 16. Optimizations

### 1. Read-Your-Writes Consistency
```
User writes: balance = $100
Read immediately should return $100 (not stale)

Implementation:
  On read: if this user just wrote, read from primary
  Else: read from nearby replica
```

### 2. Causal+ Consistency (Bolt-on)
```
Each write gets session token
Later reads with that token know causality
Ensures: if you've seen write X, you'll see all its causal descendants
```

### 3. Quorum Reads/Writes
```
Write: must be replicated to majority (quorum) before ack
Read: must ask majority (quorum) for latest value

Guarantees: 
  - Any two quorum overlaps (at least one has latest)
  - Prevents stale reads

Cost: majority latency (slower)
Benefit: strong consistency
```

---

## 17. Security

### 1. Unauthorized Stale Reads
```
User A: sensitive data (balance = $1M)
User B: tries to read A's data

Stale replica:
  If security check not yet replicated
  User B might see old unprotected value

Prevention:
  - Replicate security metadata synchronously
  - Strong consistency for auth/permissions
```

---

## 18. Tradeoffs Table

| Model | Latency | Consistency | Use Case |
|---|---|---|---|
| Strong | 50-100ms | 100% consistent | Banking, auth |
| Eventual | 1-10ms | Consistent eventually | Likes, views |
| Causal | 10-50ms | Causal ordering | Comments, threads |
| Read-your-writes | 10-50ms | User perspective | General apps |
| Quorum | 50-200ms | Strong via quorum | Critical data |

---

## 19. Alternatives

### Consistency Levels

```
Strong: all replicas same value immediately
  Cost: high latency, reduced availability

Eventual: replicas converge over time
  Cost: temporary divergence

Causal: causal ordering preserved
  Cost: intermediate latency

Session: consistency within user session
  Cost: low latency, eventual cross-session
```

---

## 20. When NOT to Use

### Strong Consistency When:

1. **Latency too high for your app**
   - User facing web app, need <100ms
   - Can't afford strong consistency overhead

2. **Availability more important**
   - E-commerce: availability > perfect consistency
   - Customer can tolerate stale inventory (backorder after)

---

## 21. Interview Questions

1. **System spans 3 continents. Design consistency model.**
   - What's consistent? What's eventual?
   - Why?

2. **User writes, immediately reads different value**
   - Root cause?
   - How prevent?

3. **Compare strong vs eventual consistency**
   - Tradeoffs?
   - When use each?

4. **Two replicas have conflicting values**
   - How resolve?
   - Impact on user?

5. **Network partition between US and EU datacenters**
   - CAP theorem tradeoff?
   - Your choice?

---

## 22. Common Mistakes

1. **Assuming "replicated = consistent"**
   - Replicated async → eventual consistency
   - Not strong consistency

2. **Strong consistency everywhere**
   - Adds latency to all reads
   - Not necessary for all data

3. **No conflict resolution**
   - Data diverges
   - Merging corrupts

4. **Ignoring replication lag**
   - Write: happens on primary
   - Read from replica: sees old value
   - User confusion

5. **CAP theorem misunderstanding**
   - Can't have all 3
   - Must choose 2 and accept tradeoff

---

## 23. Debugging Guide

### Step 1: Measure Lag
```
Write timestamp: 10:00:00
Read from replica: balance = old value
Replica sync time: 10:00:05 (5 second lag!)

Issue: replication is slow
```

### Step 2: Identify Cause
```
Why 5 second lag?
  - Network slow? (check bandwidth)
  - Replica processing slow? (check CPU, disk)
  - Queue buildup? (replication can't keep up)
```

### Step 3: Fix
```
Queue backup: network too slow
  → Use compression, increase bandwidth
  
Replica processing: CPU bound
  → Add replicas (more processing capacity)
```

---

## 24. Code Examples

### Go: Read-Your-Writes
```go
type ConsistentRead struct {
    primary   *sql.DB
    replicas  []*sql.DB
}

func (cr *ConsistentRead) Read(ctx context.Context, key string, userId int64) (interface{}, error) {
    // Check if this user just wrote
    lastWrite := getLastWriteTime(userId)
    
    if time.Since(lastWrite) < 100*time.Millisecond {
        // Recent write: read from primary (consistent)
        return cr.readFromPrimary(ctx, key)
    }
    
    // Stale write: read from replica (faster, eventually consistent)
    return cr.readFromReplica(ctx, key)
}

func (cr *ConsistentRead) readFromPrimary(ctx context.Context, key string) (interface{}, error) {
    return cr.primary.QueryRowContext(ctx, "SELECT val FROM data WHERE key = ?", key).Scan(&val)
}

func (cr *ConsistentRead) readFromReplica(ctx context.Context, key string) (interface{}, error) {
    // Round-robin across replicas
    replica := cr.replicas[rand.Intn(len(cr.replicas))]
    return replica.QueryRowContext(ctx, "SELECT val FROM data WHERE key = ?", key).Scan(&val)
}
```

### Go: Quorum Read
```go
func (cr *ConsistentRead) QuorumRead(ctx context.Context, key string) (interface{}, error) {
    quorumSize := len(cr.replicas)/2 + 1 // majority
    
    values := make(map[interface{}]int)
    var maxVal interface{}
    
    for i, db := range cr.replicas {
        if i >= quorumSize {
            break // only need majority
        }
        
        var val interface{}
        db.QueryRowContext(ctx, "SELECT val FROM data WHERE key = ?", key).Scan(&val)
        
        values[val]++
        if values[val] > len(values)/2 {
            maxVal = val
        }
    }
    
    return maxVal, nil // most common value among quorum
}
```

---

## 25. Visual Diagrams

### Consistency vs Latency
```
Latency (ms)
   100 │     Strong
        │     Consistency
    50 │         ├─ Causal
        │         │  Consistency
    10 │         │      ├─ Eventual
        │         │      │  Consistency
     1  └─────────┴──────┴─────────
        0%   50%   100%
        Consistency guarantee
```

### Replication Lag Timeline
```
Primary:  [Write] → [Replicate] → [Ack A] → [Ack B] → [Ack C]
          t=0ms     t=10ms        t=30ms    t=60ms    t=100ms

Replica A: reads at 20ms → still old value (10ms lag)
Replica B: reads at 70ms → new value (10ms replicated)
Replica C: reads at 120ms → new value
```

---

## 26. Simulation Ideas

1. **Consistency Level Explorer**
   - Choose: strong, eventual, causal
   - See: latency, divergence scenarios

2. **Replication Lag Simulator**
   - Network latency: variable
   - Replica processing rate: variable
   - Observe: divergence over time

3. **Conflict Resolution Simulator**
   - Two concurrent writes
   - Different resolution strategies
   - See: outcomes (last-write-wins vs CRDT)

---

## 27. Case Studies

### Case 1: Amazon DynamoDB Global Tables
**Solution:** Eventual consistency with conflict-free replicated data types (CRDTs)

Result: any write succeeds globally, conflicts auto-resolve

### Case 2: Google Spanner
**Solution:** Synchronized clocks (TrueTime) + synchronous replication

Result: strong consistency globally with reasonable latency (10-100ms)

---

## 28. Related Topics

- **CAP Theorem**
- **PACELC Theorem**
- **Vector Clocks**
- **CRDTs (Conflict-Free Replicated Data Types)**

---

## 29. Advanced Topics

### CRDTs (Conflict-Free Replicated Data Types)
```
Two replicas diverge, no conflict:
  Replica A: {1, 2}
  Replica B: {2, 3}

CRDT merge:
  Result: {1, 2, 3} (union, no data loss)

Difference from last-write-wins:
  LWW might lose {1} if B's write is newer
  CRDT preserves both
```

### Causal Consistency via Vector Clocks
```
Event A: write X=1 (Server 1, clock: [1,0,0])
Event B: write Y=2 (Server 2, clock: [1,1,0])
Event C: write Z=3 (Server 1, clock: [2,1,0])

Causality: A < B < C (can order events correctly)

Result: reads respect causality even with async replication
```

---

## 30. Production Checklist

- [ ] Identify consistency requirements per data type
- [ ] Choose replication strategy (sync vs async)
- [ ] Implement read-your-writes consistency
- [ ] Monitor replication lag (alert if > 1s)
- [ ] Implement conflict resolution strategy
- [ ] Test convergence (replicas eventually consistent)
- [ ] Document consistency guarantees to users
- [ ] Test network partition scenarios
- [ ] Implement quorum read/write if needed
- [ ] Backup validation (ensure no corruption)
- [ ] Measure stale read rate (% reads hitting lag)
- [ ] Plan for multi-region eventually consistency

---

*Last Updated: 2026-05-28*
