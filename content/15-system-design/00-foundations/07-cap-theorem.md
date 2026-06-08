---
title: CAP Theorem Deep Dive - L5 Fundamentals
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# CAP Theorem Deep Dive - L5 Fundamentals

> **[🎨 View Interactive Diagram](cap-architecture.html)** | [← Back to Index](../../systems-index.html)

*"You can't have consistency, availability, AND partition tolerance. Pick two."*

---

## 1. Problem Statement

**Core Question:** In a distributed system with network failures, what must you sacrifice?

Three properties:
- **C**onsistency: All replicas have same value
- **A**vailability: System responds to requests
- **P**artition tolerance: System survives network failure

CAP Theorem: you can have max 2 out of 3.

---

## 2. Real World Analogy

**Two Banks Scenario:**

Strong Consistency (CA):
- Customer withdraws $100 from Bank A
- Bank A calls Bank B: "update my account"
- Network fails: Bank B unreachable
- Bank A refuses withdrawal (can't confirm consistency)
- **Availability sacrificed**

Availability (AP):
- Customer withdraws $100 from Bank A
- Bank A processes immediately (fast!)
- Bank B eventually hears about it
- Network heals: $100 withdrawal reconciled
- **Consistency temporarily sacrificed** (temporary divergence)

Partition Tolerance (required):
- Network failures are unavoidable
- Must be designed into system

---

## 3. Why Problem Exists

### Network Failures Inevitable

```
In a distributed system:
  Server A (California)
  Server B (Virginia)
  
Network partition (fiber cut, router failure):
  A and B can't communicate

A's perspective: B is dead (offline)
B's perspective: A is dead (offline)

Both are right locally, but wrong globally
Problem: can't reach consensus
```

### Consistency vs Availability Trade

```
Scenario: write reaches A, not B (partition)

Consistency-first (CP):
  Don't ack write until B confirms
  But can't reach B (partition)
  → Reject write (unavailable)

Availability-first (AP):
  Ack write immediately to A
  B will catch up later
  → Write succeeds (available)
  But A and B diverge (inconsistent)
```

---

## 4. Naive Approach

**"Design for all three"**

Problems:
- Mathematically impossible (CAP theorem)
- Trying violates distributed system fundamentals
- Will fail under partition (guaranteed to happen)

---

## 5. Why Naive Fails

### Network Partitions Unavoidable

```
At scale (many servers, many networks):
  - Probability of partition: 100% eventually
  - When it happens: must choose CA or AP

Ignoring partition:
  System breaks under partition (not robust)
```

### False Sense of Security

```
"We have all three (C, A, P) in our design"
  Actually: system doesn't handle partition
  Under partition: cascading failures, data corruption
```

---

## 6. Evolution / Progression

### Stage 1: Single Datacenter (No Partition Risk)
- All servers connected locally
- Network failures rare
- Can enforce consistency
- Example: MySQL replication in single DC

### Stage 2: Multi-Datacenter (Partition Risk)
- Servers across regions
- Network failures possible (fiber cut)
- Must choose: sacrifice consistency or availability
- Example: DynamoDB (AP), Google Spanner (CP with TrueTime)

### Stage 3: CAP-Aware Design
- Understand your choice
- Design accordingly (consistency mechanism for CP, merge logic for AP)
- Test partition scenarios

---

## 7. Production Architecture

```
CP System (Consistency + Partition):
  Write coordinator election (leader)
  If partition: minority partition halts (consistency guaranteed)
  Availability reduced: stops serving until healed
  
AP System (Availability + Partition):
  No coordinator, all partitions serve requests
  Writes diverge during partition
  On healing: detect conflicts, merge

Trade: consistency vs availability under partition
```

---

## 8. Components

### Quorum-Based Consensus (CP)
**Purpose:** Maintain consistency despite partition

```
3 nodes total
Write needs majority (2 votes)

Partition A: 2 nodes (can write, has quorum)
Partition B: 1 node (can't write, no quorum)

Result: 
  A: writes continue (consistent)
  B: writes rejected (unavailable, but consistent globally)
```

### Vector Clocks / Timestamps (AP)
**Purpose:** Detect divergence, enable merging

```
Partition A: write X=1
Partition B: write X=2

On partition heal:
  Both see: X has two values (conflict)
  Resolve: last-write-wins, or custom merge logic
  
Availability: maintained during partition
Consistency: restored after healing
```

---

## 9. Internal Working

### CP System Partition

```
System: Primary (A) + Secondary (B)
Write: goes to A (quorum met, acks)

Partition occurs (A and B split):

Partition A (with Primary):
  New writes: succeed (A has majority)
  Consistency: maintained (all see same value)

Partition B (secondary only):
  New writes: rejected (no quorum)
  Availability: lost
  
On partition heal:
  B catches up from A
  Consistency never violated
```

### AP System Partition

```
System: distributed (no quorum needed)
Write: succeed on any node

Partition A: write X=1 (local node thinks X=1)
Partition B: write X=2 (local node thinks X=2)

Both partitions available (succeed writes)

On partition heal:
  See: X=1 on A, X=2 on B
  Conflict detected
  Merge: X=max(1,2)=2 (or custom logic)
```

---

## 10. Request Lifecycle

```
CP System (CP example: Raft):
  Write → Leader elected → Replicate to majority
       → Ack when majority acks
       → Minority rejects

Latency:
  Normal: 50-100ms (quorum replication)
  Partition in A: 100ms (A still works)
  Partition in B: timeout → error (rejected)

AP System (AP example: DynamoDB):
  Write → Node A accepts → Ack immediately
       → Replicate async (may diverge)
       
Latency:
  Normal: 10-20ms (no wait for replication)
  Partition in A: 10-20ms (still works)
  Partition in B: 10-20ms (still works, diverges)
```

---

## 11. Data Flow

### Partition Scenario: 3 Nodes

```
Normal: [A, B, C] all connected
Write: X=100

Partition: [A, B] | [C]
            (2)     (1)

CP System (Raft, quorum=2):
  A, B: can write (have quorum of 2)
  C: can't write (only 1, needs 2)
  
  A, B: stay consistent
  C: falls behind (reads stale)
  
  On heal: C catches up from A or B

AP System (DynamoDB):
  A: write X=200
  B: write X=300
  C: write X=150
  
  All succeed (no quorum needed)
  
  On heal:
    A: X=200, B: X=300, C: X=150 (conflict!)
    Merge: X=max=300 (or custom)
```

---

## 12. Key Strategy

### 1. Understand Your Choice

```
Consistency (CP):
  - Sacrifice: availability during partition
  - When to use: financial, critical operations
  
Availability (AP):
  - Sacrifice: temporary consistency
  - When to use: social media, non-critical data
```

### 2. Design for Your Choice

```
CP system:
  Implement: quorum consensus (Raft, Paxos)
  Handle partition: reject writes in minority
  
AP system:
  Implement: conflict detection, merge logic
  Handle partition: accept all writes, resolve conflicts
```

### 3. Test Partition Scenarios

```
Regular chaos engineering:
  Simulate fiber cut (network partition)
  Validate: correct behavior under partition
  Measure: availability, consistency preservation
```

---

## 13. Failure Scenarios

### Scenario 1: Partition Without Quorum

```
5-node cluster, quorum=3
Partition: 2 nodes vs 3 nodes

Minority (2):
  Can't get quorum (need 3)
  Writes rejected

Majority (3):
  Have quorum (3 of 5)
  Writes succeed
  
Result: consistency maintained, but availability reduced
```

### Scenario 2: Split Brain

```
Without consensus protocol:
  Partition: 2 nodes vs 2 nodes
  Both think they're majority
  Both accept writes
  Both diverge (data corruption)

With Raft:
  Partition: 2 vs 2
  Neither has quorum (need 3 of 4)
  Both reject writes (consistency, but unavailable)
```

---

## 14. Bottlenecks Table

| Issue | Consistency | Availability | Partition Tolerance |
|---|---|---|---|
| No replication | X | X | ✓ (but data loss) |
| CP design | ✓ | ✗ (under partition) | ✓ |
| AP design | ✗ (eventual) | ✓ | ✓ |
| Ignoring partition | ✗ | ✗ | ✗ (fails) |

---

## 15. Monitoring

### Key Metrics

```
Partition detection:
  ✓ Network connectivity: monitor links
  ✓ Node reachability: can all nodes reach quorum?

For CP systems:
  ✓ Quorum status: have quorum?
  ✓ Minority rejection rate: writes rejected?

For AP systems:
  ✓ Conflict rate: how often diverge?
  ✓ Merge success rate: conflicts resolved?
```

### Red Flags

- Nodes isolated from quorum (can't write)
- Divergence detected without merge (data corruption)
- Network partition lasting > 5 minutes (investigate)

---

## 16. Optimizations

### 1. Quorum Leases (CP Optimization)
```
Write to quorum, get lease (time-limited)
During lease: don't write to minority
  → Temporarily act like CP while consistent

Lease expires: require quorum again
  → Safe under partition (no stale leader)
```

### 2. Operational Transformation (AP Optimization)
```
Two concurrent writes diverge
Later merge using Operational Transformation:
  Write A: insert "hello" at position 0
  Write B: insert "world" at position 5
  
  Merge: both operations applied, result consistent
```

---

## 17. Security

### 1. Byzantine Failures (Beyond CAP)
```
CAP assumes honest servers
Byzantine: servers can lie, corrupt data

Requires: 3F+1 servers to tolerate F Byzantine failures
(vs 2F+1 for regular failures)

More expensive but handles malicious attacks
```

---

## 18. Tradeoffs Table

| Choice | Consistency | Availability | Partition | Use Case |
|---|---|---|---|---|
| CP | ✓ | Partial | ✓ | Banking, critical |
| AP | Eventual | ✓ | ✓ | Social, cache |
| CA | ✓ | ✓ | ✗ | Single datacenter |

---

## 19. Alternatives

### Eventual Consistency + Conflict Resolution
```
AP + merge logic:
  - Accept all writes during partition
  - Detect conflicts on partition heal
  - Merge using: last-write-wins, CRDTs, custom logic

Result: availability maintained, conflicts resolved
```

### Strongly Consistent with Weaker Partition Tolerance
```
Use TrueTime (Google Spanner approach):
  - Synchronized clocks (atomic clock + GPS)
  - Eliminate clock skew as source of conflict
  - Enables strong consistency globally

Cost: expensive infrastructure
Benefit: strong consistency without availability loss
```

---

## 20. When NOT to Use

### Don't Choose CP When:

1. **Availability more critical**
   - E-commerce: prefer available with stale data
   - "Sorry, inventory old" < "Sorry, we're down"

### Don't Choose AP When:

1. **Consistency critical**
   - Banking: must not diverge
   - Regulatory requirement: no data loss

---

## 21. Interview Questions

1. **Partition occurs between datacenters. Your choice: CP or AP?**
   - Why?
   - Implications?

2. **Design financial system (no data loss)**
   - Which property sacrifice?
   - Why?

3. **Compare Raft (CP) vs DynamoDB (AP)**
   - Tradeoffs?
   - When use each?

4. **Partition for 1 hour. System started with CAP in mind but no consensus**
   - What happens?
   - How prevent?

---

## 22. Common Mistakes

1. **Ignoring partition risk**
   - "We have consistency, availability, partition tolerance"
   - Mathematically impossible
   - Breaks under partition

2. **Choosing wrong for application**
   - Need consistency, built AP system
   - Or vice versa

3. **No partition testing**
   - Never simulated network failure
   - First partition in production: failure

4. **Misunderstanding eventual consistency**
   - Eventual: can diverge, but merge correctly
   - Not: "eventual, so don't worry about it"

---

## 23. Debugging Guide

### Step 1: Detect Partition
```
Monitor: can node A reach node B?
  ping: success
  TCP: fails
  → likely network partition

Alert: partition detected
```

### Step 2: Verify System Behavior
```
CP system:
  Are writes rejected? (correct)
  Or accepted in minority? (wrong, split brain)

AP system:
  Are both sides accepting writes? (correct)
  Did conflicts emerge? (expected)
```

### Step 3: Recovery
```
Partition heals: network restored

CP system:
  Minority catches up (automatic)
  No action needed

AP system:
  Detect conflicts
  Merge (automatic or manual)
  Verify consistency
```

---

## 24. Code Examples

### Go: Raft Consensus (CP)
```go
type RaftNode struct {
    id       int
    peers    []*RaftNode
    state    string // "follower", "candidate", "leader"
    term     int
    log      []LogEntry
}

func (rn *RaftNode) appendEntry(entry LogEntry) error {
    if rn.state != "leader" {
        return errors.New("not leader")
    }
    
    // Replicate to majority of followers
    ackCount := 1 // self
    for _, peer := range rn.peers {
        if peer.appendEntries(entry) {
            ackCount++
        }
    }
    
    // If majority acked: safe to apply
    if ackCount > len(rn.peers)/2 {
        rn.apply(entry)
        return nil
    }
    
    // No majority: reject (AP system: return error)
    return errors.New("no quorum")
}

// Usage:
node := &RaftNode{...}
err := node.appendEntry(logEntry)
if err != nil {
    // Under partition: write rejected (unavailable)
    http.Error(w, "no quorum", http.StatusServiceUnavailable)
    return
}
// Under partition: write accepted (available, consistent)
```

---

## 25. Visual Diagrams

### CAP Triangle
```
        C (Consistency)
       /  \
      /    \
     /      \
    /        \
   A -------- P
(Availability) (Partition)

Pick 2, sacrifice 1:
- CA (no partition) = single datacenter
- CP (no availability) = minority rejects writes
- AP (no consistency) = temporary divergence
```

---

## 26. Simulation Ideas

1. **Partition Impact Simulator**
   - Choose: CP or AP
   - Simulate: network partition duration
   - See: availability vs consistency behavior

2. **Quorum Election Simulator**
   - Show: when writes accepted/rejected
   - Show: partition scenarios

---

## 27. Case Studies

### Case 1: MongoDB Replica Sets (CP-Ish)
Consistency-leaning: majority quorum for writes

### Case 2: DynamoDB (AP)
Availability-leaning: any node accepts writes, merges later

### Case 3: Google Spanner (CP + TrueTime)
Achieves strong consistency globally using synchronized time

---

## 28. Related Topics

- **PACELC Theorem** (extends CAP)
- **Consensus Algorithms** (Raft, Paxos)
- **Eventual Consistency** (AP systems)

---

## 29. Advanced Topics

### Byzantine Fault Tolerance
```
Beyond CAP: assumes honest servers
Byzantine: servers can lie, corrupt

PBFT (Practical Byzantine Fault Tolerance):
  - Tolerate F failures with 3F+1 servers
  - Detect malicious behavior
  - Expensive but robust against attacks
```

---

## 30. Production Checklist

- [ ] Declare: CP or AP choice for your system
- [ ] Document: which property sacrificed
- [ ] Implement: consensus (CP) or conflict resolution (AP)
- [ ] Test: partition scenarios (monthly)
- [ ] Monitor: network connectivity (alert if partition)
- [ ] Monitor: quorum status (for CP)
- [ ] Monitor: conflict rate (for AP)
- [ ] Verify: behavior under partition matches design
- [ ] Document: recovery procedure
- [ ] Train: team on CAP implications

---

*Last Updated: 2026-05-28*
