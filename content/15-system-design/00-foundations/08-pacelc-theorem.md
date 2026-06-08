---
title: PACELC Theorem Deep Dive - L5 Fundamentals
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# PACELC Theorem Deep Dive - L5 Fundamentals

> **[🎨 View Interactive Diagram](pacelc-architecture.html)** | [← Back to Index](../../systems-index.html)

*"CAP Theorem says pick 2. PACELC goes further: even without partition, there are tradeoffs."*

---

## 1. Problem Statement

**Core Question:** CAP Theorem is incomplete. What about latency vs consistency trade-off even when network is healthy?

CAP: P (partition) → trade C (consistency) for A (availability)

PACELC: **if P then (A or C), Else (C or L)**
```
If there's a partition:
  Then choose: Availability or Consistency
Else (no partition):
  Then choose: Consistency or Latency
```

---

## 2. Real World Analogy

**Video Streaming:**

Partition: No, network healthy

Consistency vs Latency:
- Consistency-first: wait for server ack (100ms latency, consistent)
- Latency-first: ack immediately (5ms latency, eventual consistency)

Choice: consistency costs latency even without partition

---

## 3. Why Problem Exists

### Replication Consistency Cost

```
Network healthy, no partition
But write must replicate to multiple datacenters

Option 1 (Strong Consistency):
  Write → replicate to all (sync) → ack
  Latency: 50-100ms (wait for slowest datacenter)

Option 2 (Eventual Consistency):
  Write → ack → replicate (async)
  Latency: 5-10ms (don't wait)
```

### Synchronous vs Asynchronous Replication

```
Sync: slow but consistent
Async: fast but divergence
```

---

## 4. Naive Approach

**"Have both: strong consistency and low latency"**

Violates PACELC theorem
Impossible without specialized infrastructure (TrueTime)

---

## 5. Why Naive Fails

### Physics Constraints

```
Latency limited by speed of light:
  US to EU: ~100ms (minimum, physics limit)
  
Strong consistency requires sync replication:
  Write → wait for EU ack → reply
  Minimum: 100ms (can't beat physics)

Can't have <50ms latency AND strong consistency across regions
```

---

## 6. Evolution / Progression

### Stage 1: Single Datacenter
- Consistency: strong (local replicas, 1-5ms)
- Latency: low
- No partition risk

### Stage 2: Multi-Datacenter (Geo-Distributed)
- Choose: strong consistency (high latency) or eventual (low latency)
- Can't have both

### Stage 3: Specialized Infrastructure (TrueTime)
- Synchronized clocks eliminate clock skew
- Enables: strong consistency globally with reasonable latency
- Cost: expensive infrastructure

---

## 7. Production Architecture

```
E (without partition): Consistency vs Latency

System 1: Priority Consistency
  Write → replicate to all (sync) → ack
  Latency: 100ms (EU, Asia, US)
  Consistency: strong

System 2: Priority Latency
  Write → ack → replicate (async)
  Latency: 10ms (local region)
  Consistency: eventual (lag = seconds)
```

---

## 8. Components

### Quorum-Based Write
**Purpose:** Balance consistency and latency

```
3 datacenters, quorum = 2

Write:
  Send to all 3 (parallel)
  Wait for 2 acks (quorum)
  Ack to client

Latency: max of 2 fastest (not all 3)
Consistency: guaranteed on quorum
```

### Local Caching
**Purpose:** Low latency with eventual consistency

```
Write to primary (US)
Replicate to cache (EU, APAC)
Read from cache (1ms latency)

Tradeoff: latency (1ms) vs consistency (lag = seconds)
```

---

## 9. Internal Working

### Consistency-First System

```
Write path:
  t=0ms:   Write received
  t=0-50ms: Send to EU, Asia, US
  t=50ms:   EU acks
  t=100ms:  Asia acks (slowest)
  t=100ms:  Ack to client

Latency: 100ms (wait for slowest)
Consistency: guaranteed (all replicated)
```

### Latency-First System

```
Write path:
  t=0ms:    Write received
  t=1-5ms:  Ack to client (fast!)
  t=10-100ms: Replicate to EU, Asia (in background)

Latency: 5ms (no wait for replication)
Consistency: eventual (lag = ~100ms)
```

---

## 10. Request Lifecycle

```
User in Asia writes data

Consistency-first:
  Write → Send to US, EU, Asia (parallel)
       → Wait for 2 acks
       → Ack (after 100ms)

Latency-first:
  Write → Ack immediately (5ms)
       → Send to US, EU (async)

Perceived latency: 100ms vs 5ms (20x difference)
```

---

## 11. Data Flow

### Multi-Region Latency

```
Write in US datacenter:

Consistency-first (sync replication):
  US: 0ms
  EU: +50ms (network)
  APAC: +100ms (network)
  Total latency: 100ms

Latency-first (async replication):
  US: 0ms (ack immediately)
  EU: +50ms (background)
  APAC: +100ms (background)
  Total latency: 0ms (to client)
```

---

## 12. Key Strategy

### 1. Categorize Data by Tradeoff

```
Consistency-critical:
  - Payment info
  - Account balance
  - Accept: 100ms latency

Latency-critical:
  - Recommendations
  - Feeds
  - Accept: eventual consistency

Flexible:
  - User profile (can use quorum: 50ms latency, consistent)
```

### 2. Use Quorum for Balance

```
3 datacenters, write quorum = 2:
  Latency: wait for 2 fastest (50-80ms)
  Consistency: guaranteed on quorum (not single node)

Better than:
  100ms (wait for all 3)
  5ms (single node, eventual)
```

---

## 13. Failure Scenarios

### Scenario 1: Slow Datacenter

```
Consistency-first, all 3 must ack:
  EU: 50ms
  US: 30ms
  APAC: 200ms (slow!)
  
Latency: 200ms (limited by slowest)

If APAC network degraded:
  Overall latency increases
  Users experience slowness
```

**Fix:** Quorum-based (only wait for majority)

### Scenario 2: Incomplete Replication

```
Write acked (replicated to 2 of 3)
Node goes down before 3rd replication
Failover: different value depending on which node becomes primary
```

**Fix:** Sync replication (all or none) or accept eventual consistency

---

## 14. Bottlenecks Table

| Scenario | Consistency | Latency | Solution |
|---|---|---|---|
| Sync replication everywhere | ✓ | ✗ (100ms) | Quorum-based |
| Async everywhere | ✗ (eventual) | ✓ (5ms) | Quorum-based |
| Partition + sync | ✗ (unavailable) | ✗ | Quorum-based |

---

## 15. Monitoring

### Key Metrics

```
PACELC monitoring:
  ✓ Consistency: replication lag per datacenter
  ✓ Latency: response time (P50, P99)
  ✓ Tradeoff: can we improve latency without sacrificing consistency?
```

### Red Flags

- Latency increasing (check: sync replication bottleneck)
- Consistency lag > 1 second (async replication slow)
- Datacenter latency imbalanced (one slow, pulling down others)

---

## 16. Optimizations

### 1. Read Preferences
```
Consistency critical: read from primary (strong)
Latency critical: read from nearest (eventual)
Balanced: read from quorum (intermediate)
```

### 2. Adaptive Consistency
```
Normal conditions: eventual consistency (fast)
High-risk operations: upgrade to strong consistency
  → Example: payment authorization (temporarily strong)
             recommendation feed (stay eventual)
```

---

## 17. Security

### 1. Consistency vs Security
```
Quick auth (AP, eventual):
  Risk: stale auth token accepted
  Fix: strong consistency for auth (priority consistency)

Regular data (AP, eventual):
  Acceptable: stale data

Trade: accept slower auth for security
```

---

## 18. Tradeoffs Table

| Approach | Consistency | Latency | Use Case |
|---|---|---|---|
| Sync all replicas | Strong | 100ms | Critical data |
| Async all | Eventual | 5ms | Cache, feeds |
| Quorum write | Strong on quorum | 50ms | Balanced |
| Read from primary | Strong | 100ms | Strongest guarantee |
| Read from cache | Eventual | 5ms | Speed priority |

---

## 19. Alternatives

### Tunable Consistency Per Operation
```
Write A (payment): quorum (50ms, strong)
Write B (feed): async (5ms, eventual)
Both coexist in same system
```

### Read Repair
```
Read stale value → also fetch from primary
Detect divergence → client decides
Cost: extra RPC, benefit: detect inconsistency
```

---

## 20. When NOT to Use

### Don't Force Consistency When:

1. **Latency more critical**
   - Real-time system: can't afford 100ms
   - Use eventual, manage divergence

### Don't Force Latency When:

1. **Consistency critical**
   - Banking: must prioritize consistency
   - Accept latency cost

---

## 21. Interview Questions

1. **Design global system (no partition)**
   - Consistency or latency priority?
   - Why?
   - Trade-offs?

2. **Write takes 100ms (EU replication latency)**
   - How reduce without sacrificing consistency?
   - Options?

3. **Payment system across regions**
   - Strong consistency, but latency must be <50ms**
   - Possible?
   - How?

4. **Compare: sync replication vs quorum**
   - Latency comparison?
   - Consistency comparison?

---

## 22. Common Mistakes

1. **Assuming no network = no tradeoffs**
   - Even without partition, must trade consistency for latency
   - Physics limit: 100ms to replicate globally

2. **Not measuring replication latency**
   - Assume fast
   - Reality: 50-200ms per continent
   - Consistency cost = that latency

3. **Applying CAP to no-partition case**
   - CAP only applies during partition
   - PACELC applies always

4. **Ignoring slow datacenters**
   - If waiting for all: limited by slowest
   - Latency increases as network varies

---

## 23. Debugging Guide

### Step 1: Measure Baseline
```
Write latency: 150ms
Why?
  → trace replication time
  → see: waiting for EU (50ms) + Asia (100ms)
```

### Step 2: Identify Bottleneck
```
EU fast (50ms)
Asia slow (100ms)
Network or processing?
  → check: network latency (ping)
  → check: replica processing (CPU, disk)
```

### Step 3: Optimize
```
If network slow:
  → use compression, reduce payload
  
If replica processing slow:
  → upgrade replica hardware, add index

If both slow:
  → use quorum instead of all (only need 2, not 3)
  → latency: max(EU, US) = 50ms (Asia optional)
```

---

## 24. Code Examples

### Go: Quorum Write
```go
func (db *Database) QuorumWrite(key string, val interface{}, quorumSize int) error {
    peers := db.replicas // [US, EU, Asia]
    
    // Send to all in parallel
    acks := make(chan error, len(peers))
    for _, peer := range peers {
        go func(p *Replica) {
            acks <- p.Write(key, val)
        }(peer)
    }
    
    // Wait for quorum
    successCount := 0
    for i := 0; i < len(peers); i++ {
        err := <-acks
        if err == nil {
            successCount++
            if successCount >= quorumSize {
                // Quorum reached, can return
                return nil
            }
        }
    }
    
    // Not enough acks
    return fmt.Errorf("write failed: only %d/%d acks", successCount, len(peers))
}

// Usage:
// Write quorum = 2 of 3 datacenters must ack
db.QuorumWrite("user:123:balance", 100, 2)
// Latency: ~50ms (wait for 2 fastest, not all 3)
// Consistency: guaranteed on quorum
```

---

## 25. Visual Diagrams

### PACELC Tradeoff Space
```
Latency (ms)
  100 │  Sync Replication (strong consistency)
      │  ════════════════════
   50 │              Quorum
      │              ═══════
    5 │  Async (eventual consistency)
      │  ════════════════════════════
      └──────────────────────────────
        All  Majority  Async
        Consistency/Availability
```

---

## 26. Simulation Ideas

1. **Latency vs Consistency Simulator**
   - Vary: sync/async, quorum size
   - Show: latency vs consistency achieved

2. **Datacenters Latency Impact**
   - Vary: network delay per DC
   - Show: how slowest DC pulls down latency

3. **Replication Cost Calculator**
   - Choose: approach (sync, quorum, async)
   - Output: expected latency at given percentile

---

## 27. Case Studies

### Case 1: DynamoDB (AP, Latency-First)
Result: 10ms latency, eventual consistency

### Case 2: Google Spanner (CP, TrueTime)
Result: 10ms latency globally (with expensive clock sync)

### Case 3: Cassandra (AP, Tunable)
Result: quorum writes provide balance

---

## 28. Related Topics

- **CAP Theorem**
- **Consistency Models**
- **Network Latency Physics**

---

## 29. Advanced Topics

### TrueTime (Google Spanner)
```
Atomic clocks + GPS = bounded clock skew
Enables: strong consistency without waiting for distant datacenters
Cost: expensive infrastructure
```

---

## 30. Production Checklist

- [ ] Measure: replication latency per datacenter
- [ ] Identify: consistency vs latency tradeoff for your data
- [ ] Choose: approach (sync, quorum, async)
- [ ] Document: consistency guarantees per operation
- [ ] Monitor: latency (P50, P99, P999)
- [ ] Monitor: replication lag (alert if > 1s)
- [ ] Test: slow datacenter scenarios
- [ ] Optimize: reduce replication latency (compression, etc)
- [ ] Consider: quorum-based for balance

---

*Last Updated: 2026-05-28*
