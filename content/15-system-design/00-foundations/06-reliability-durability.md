---
title: Reliability & Durability Deep Dive - L5 Fundamentals
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# Reliability & Durability Deep Dive - L5 Fundamentals

> **[🎨 View Interactive Diagram](reliability-architecture.html)** | [← Back to Index](../../systems-index.html)

*"Why does your database lose data during failures? How do you guarantee writes stick around?"*

---

## 1. Problem Statement

**Core Question:** If server crashes, can you recover the data you wrote?

Scenario:
```
User writes: $100 transfer
System acks: "committed"
Server crashes immediately after

On restart: was $100 transfer persisted?
  Option 1: Yes (durable) → no data loss
  Option 2: No (lost) → data corruption
```

---

## 2. Real World Analogy

**Legal Document Scenario:**

Reliability (MTBF: Mean Time Between Failures):
- Clerk processes 1000 documents per day
- Average: 1 error every 100 days
- Reliability: 99.7% (3 errors per year)

Durability (RPO: Recovery Point Objective):
- Document filed immediately: durable
- Document in hand: vulnerable to loss

Result: Reliable system can still lose data if durability is weak

---

## 3. Why Problem Exists

### Memory vs Disk

```
Data in memory: fast (microseconds), volatile (lost on crash)
Data on disk: slow (milliseconds), durable (survives crash)

Tradeoff: write to disk = durability, but cost = latency
```

### Asynchronous Writes

```
Optimization: buffer writes in memory, flush async

Write arrives → ack to user (fast, 1-5ms)
Background: flush to disk (slow, 10-100ms)

If crash between ack and flush: data lost
```

### Replication Delay

```
Write to primary: committed (durable on primary)
Replicate to standby: async (delayed)

Primary crashes before replicating: data loss
Failover to standby: lost recent writes (RPO violated)
```

---

## 4. Naive Approach

**"Sync to disk every write"**

```
Write arrives → write to disk → ack to user

Guarantees: durable (can't lose)
Cost: 10-100ms latency per write (slow)
Throughput: 10-100 writes/sec (too slow for production)
```

---

## 5. Why Naive Fails

### Write Amplification

```
User write: 100 bytes
Disk write (naive):
  1. Write data file: 100 bytes
  2. Write log file: 100 bytes
  3. Fsync data (flush): 4KB block
  4. Fsync log: 4KB block
  
Total: 8KB written (80x amplification!)
```

### Latency Cost

```
Disk fsync: 10ms per call
1000 writes/sec × 10ms = 10,000ms = 10 seconds overhead
Actual throughput: 1000 - 100 = 900 writes/sec (10% lost to fsync)
```

---

## 6. Evolution / Progression

### Stage 1: Memory Only (No durability)
- Crash → all data lost
- Availability: decent
- Durability: 0%

### Stage 2: Periodic Disk Flush
- Buffer writes in memory
- Flush to disk every 10 seconds
- RPO: 10 seconds (lose up to 10s of writes)

### Stage 3: Write-Ahead Logging (WAL)
- Log every write immediately to disk
- Actual data flush: async
- RPO: <100ms (durability high, throughput high)

### Stage 4: Replicated WAL
- WAL to local disk
- Replicate WAL to standby (async)
- RPO: 0 (no data loss even on primary crash)

### Stage 5: Quorum-Based Replication
- WAL to majority of replicas (sync)
- All writes replicated before ack
- RPO: 0, MTTR: <1 minute

---

## 7. Production Architecture

```
Write path (high durability):

[Client writes $100]
    ↓
[Primary in-memory buffer]
    ├─ Also write to WAL (disk) immediately
    └─ Also queue replication to standby
    ↓
[Ack to client] (fast, <5ms)
    ├─ WAL already on disk (durable)
    ├─ Standby has copy queued
    
[Background]
    ├─ Flush data from memory to disk (10-100ms later)
    ├─ Send WAL to standby replicas (20-100ms)
    ├─ Wait for majority ack (if sync replication)
    └─ Mark as fully replicated
```

---

## 8. Components

### Write-Ahead Logging (WAL)
**Purpose:** Durability guarantee

```
Before: change memory, then write to disk
  If crash: lost

WAL: write to log first, then change memory
  Log written to disk → durable
  Later: apply changes to data

On restart:
  Replay log → recover all committed writes
  Durability: 100%
```

### Checkpoints
**Purpose:** Optimize recovery

```
Without checkpoints:
  100M writes in log
  Crash: must replay 100M writes (slow recovery)
  Recovery time: hours

With checkpoints:
  Every 1M writes: snapshot data to disk
  Crash: replay from checkpoint + recent writes
  Recovery time: minutes
```

### Replication Quorum
**Purpose:** Multi-node durability

```
Single node: durable on write, but node crash = loss

3-node quorum:
  Write to node 1 (primary)
  Replicate to node 2, 3
  Ack only after majority (2 of 3) ack
  
Failure tolerance:
  Node 1 crash: data safe on 2, 3
  Node 2 crash: data safe on 1, 3
  Only lose if 2+ nodes crash simultaneously (rare)
```

---

## 9. Internal Working

### WAL Recovery

```
WAL entries:
  [1] INSERT user (id=1, name="Alice")
  [2] UPDATE user SET balance=100
  [3] DELETE user (id=2)
  [4] INSERT user (id=3, name="Bob")

Crash after entry [2]

Crash recovery:
  [1] Replay: INSERT user (id=1)
  [2] Replay: UPDATE user balance
  [3] Skip: DELETE not yet committed
  [4] Skip: INSERT not yet committed
  
Result: state consistent with log
```

### Durability Guarantees (ACID)

```
Atomicity: write either fully committed or not at all
  WAL ensures: partial writes recoverable

Consistency: data structure valid after crash
  Checkpoints + replay ensures: valid state

Isolation: concurrent writes don't interfere
  Locks + transactions ensure: isolated

Durability: committed writes survive crash
  WAL on disk ensures: durable
```

---

## 10. Request Lifecycle

```
User writes: $100 transfer

t=0ms:     Write arrives at primary
t=0-1ms:   Write WAL to disk (fsync)
t=1-2ms:   Write to in-memory buffer
t=2-3ms:   Queue replication message
t=3-5ms:   Ack to client ("committed")

← Durability guaranteed here (on disk)

t=5-25ms:  Network sends replication to standby 1
t=25-26ms: Standby 1 writes WAL
t=26ms:    Standby 1 sends ack

t=5-75ms:  Network sends replication to standby 2
t=75-76ms: Standby 2 writes WAL
t=76ms:    Standby 2 sends ack

t=100-200ms: Data flushed from memory to data file
t=200-300ms: Mark as fully persisted

Durability: achieved at t=5ms (WAL on disk)
Full replication: achieved at t=76ms (all nodes have WAL)
```

---

## 11. Data Flow

### Durability at Multiple Levels

```
Memory:     lost immediately on crash
WAL disk:   survives crash (recovered on restart)
Data disk:  survives crash, direct reads don't need WAL
Replica 1:  survives single-node crash
Replica 2:  survives 2-node crash
Replica 3:  survives 3-node crash (2 failures tolerated)
```

---

## 12. Key Strategy

### 1. Choose Durability Level

```
Critical data (banking, payments):
  - All writes to quorum (no data loss acceptable)
  - RPO: 0 (zero data loss)
  - RTO: <5 minutes (quick recovery)

Important data (user profiles):
  - Replicated, but async
  - RPO: <1 hour (can lose 1 hour of changes)

Non-critical data (cache, session):
  - Memory only (can lose on crash)
  - RPO: 0 (acceptable to lose)
```

### 2. Implement WAL

```
Every durable write:
  1. Write to WAL (disk)
  2. Ack to client (can happen now, durable)
  3. Later: flush to data file, replicate
```

### 3. Monitor Durability

```
Metrics:
  - Replication lag: how behind are standby?
  - WAL size: growing unbounded (checkpoint stuck?)
  - Recovery time: test regularly
```

---

## 13. Failure Scenarios

### Scenario 1: Power Loss During Write

```
Write arrives: $100
WAL partially written (50 bytes of 100)

Crash

Recovery:
  Incomplete WAL entry: discard (not fully written)
  No data lost (didn't ack yet)

If already acked before crash:
  Data might be lost (depends on fsync timing)
```

**Fix:** Always fsync before ack

### Scenario 2: Replication Lag

```
Write committed on primary
Not yet replicated to standby
Primary crashes

Failover to standby: lost recent write
User: "I wrote $100, it's gone!"
```

**Fix:** 
- Sync replication (wait for standby ack before client ack)
- Or accept: occasional data loss (weaker guarantee)

### Scenario 3: Corruption

```
Bit flip in data file (memory error)
Replicated to all standbys (corrupt data spreads)

Recovery from backup:
  All nodes corrupt, backup also corrupt
  Data loss: unrecoverable
```

**Fix:**
- Checksums (detect corruption)
- Separate backup location (independent)
- Immutable backup (can't corrupt)

---

## 14. Bottlenecks Table

| Bottleneck | Durability Impact | Symptoms | Quick Fix |
|---|---|---|---|
| Slow fsync | Data loss | WAL disk slow | Better disk, SSD |
| No replication | Single-point failure | Node crash = lost | Add replication |
| Async replication | Recent data loss | Failover loses writes | Sync replication |
| No checkpoints | Slow recovery | Recovery takes hours | Add checkpoints |
| Unbounded WAL | Disk full | Out of space | Checkpoint/trim WAL |
| Corruption undetected | Silent data loss | Corrupt silently | Add checksums |

---

## 15. Monitoring

### Key Metrics

```
Durability indicators:
  ✓ WAL fsync latency: 1-10ms
  ✓ Replication lag: <1 second
  ✓ Replica sync status: all in sync
  ✓ Checkpoint age: recent (not stale)
  ✓ Recovery time (RTO): tested, < target

Corruption detection:
  ✓ Checksum failures: should be 0
  ✓ Data inconsistency: 0 incidents
```

### Red Flags

- WAL fsync > 100ms (slow disk)
- Replication lag > 60 seconds (can't keep up)
- Checkpoint not progressing (stuck, WAL growing)
- Corruption detected (backup immediately)

---

## 16. Optimizations

### 1. Group Commits
```
Without:
  Write 1: fsync immediately (1 fsync)
  Write 2: fsync immediately (1 fsync)
  Write 3: fsync immediately (1 fsync)
  Total: 3 fsyncs

With:
  Write 1, 2, 3: batch together (1 fsync)
  Total: 1 fsync
  
Throughput: 3x (same disk cost, more data)
```

### 2. Asynchronous Replication with Write Buffer
```
Write committed on primary (ack to user)
Replicated async (background)

If crash before replication:
  Single-node loss (acceptable for non-critical data)
  But faster ack (1-5ms vs 50-100ms)
```

### 3. Compression
```
WAL: 1GB/day uncompressed
Compressed: 100MB/day

Benefit: smaller log, faster replication
Cost: CPU for compression
```

---

## 17. Security

### 1. Data Integrity Verification
```
Checksum (CRC, SHA-256) on every block
On read: verify checksum
  If mismatch: corrupted (alert, don't serve)
```

### 2. Encryption at Rest
```
Data on disk: encrypted
Key stored separately (key management service)

On crash: encrypted data unreadable without key
Prevents: data theft from stolen disk
```

---

## 18. Tradeoffs Table

| Approach | Durability | Latency | Complexity |
|---|---|---|---|
| Memory only | 0% | <1ms | Low |
| Async flush | 95% | 10-20ms | Low |
| WAL | 99% | 5-10ms | Medium |
| Sync replication | 99.99% | 50-100ms | High |
| Quorum replication | 99.999% | 100-200ms | High |

---

## 19. Alternatives

### Durability Strategies

```
Write-through (sync):
  Write to disk → ack to user
  Durable immediately, but slow

Write-back (async):
  Ack to user → write to disk later
  Fast, but data loss risk

Write-ahead logging:
  Log to disk → ack to user → flush data later
  Best of both: durable + reasonably fast
```

---

## 20. When NOT to Use

### Full Durability When:

1. **Data loss acceptable**
   - Session cache: can lose on restart
   - Temporary data: reconstructible

2. **Latency cost too high**
   - Real-time system: can't afford 50-100ms fsync
   - Use async, accept occasional loss

---

## 21. Interview Questions

1. **Design durable database (no data loss)**
   - How guarantee durability?
   - What happens on crash?
   - Recovery process?

2. **Write acked to client, server crashes immediately**
   - Data lost or safe?
   - Why?
   - How prevent?

3. **Choose: fast ack or guaranteed replication**
   - Which pick?
   - When trade off?

4. **Corruption detected in replica**
   - Can still use primary?
   - How recover?

---

## 22. Common Mistakes

1. **Acking before fsync**
   - Client: "data committed"
   - Crash before fsync
   - Data lost (violated durability promise)

2. **Ignoring replication lag**
   - Write safe on primary
   - Assume safe on standby (lag!)
   - Failover: recent writes lost

3. **No corruption detection**
   - Bit flip in data
   - Replicate silently (spreads corruption)
   - Unrecoverable loss

4. **WAL unbounded**
   - Keep growing
   - Disk fills
   - Service crashes (OOM)

---

## 23. Debugging Guide

### Step 1: Verify Durability Claims
```
Write received: t=0
Ack sent: t=5ms

WAL flushed: t=5ms or t=100ms?
  If t=5ms: durable ✓
  If t=100ms: not durable ✗
```

### Step 2: Check Replication
```
Write on primary: confirmed
Replica status: behind by 10 seconds

If primary crashes:
  → standby lacks last 10 seconds of data
  → data loss (violated RPO)
```

### Step 3: Recovery Test
```
Simulate crash: kill primary
Recover from standby:
  ✓ All writes present?
  ✓ Data consistent?
  ✓ Recovery time acceptable?
```

---

## 24. Code Examples

### Go: Write-Ahead Log
```go
type WriteAheadLog struct {
    file *os.File
    mu   sync.Mutex
}

func (wal *WriteAheadLog) LogWrite(data []byte) error {
    wal.mu.Lock()
    defer wal.mu.Unlock()
    
    // Write to log
    _, err := wal.file.Write(data)
    if err != nil {
        return err
    }
    
    // Fsync to disk (durable)
    err = wal.file.Sync()
    if err != nil {
        return err
    }
    
    // At this point: guaranteed durable on disk
    return nil
}

func (wal *WriteAheadLog) Replay(handler func([]byte) error) error {
    wal.file.Seek(0, 0)
    scanner := bufio.NewScanner(wal.file)
    
    for scanner.Scan() {
        entry := scanner.Bytes()
        // Replay: apply this entry
        if err := handler(entry); err != nil {
            return err
        }
    }
    
    return nil
}

// Usage:
wal := &WriteAheadLog{file: logFile}
if err := wal.LogWrite(userWrite); err != nil {
    // Durability failed
    http.Error(w, "write failed", http.StatusInternalServerError)
    return
}
// Safe to ack: write is durable
w.WriteHeader(http.StatusOK)
```

---

## 25. Visual Diagrams

### Durability Timeline
```
Write ack: when?

No durability:        [Write to mem] → [Ack] 
                                        1ms
Async flush:          [Write] → [Ack] → [Fsync] 
                       1ms      2ms      50ms
WAL:                  [Write to WAL] → [Ack]
                       (fsync)          5ms
Replication:          [Write] → [Replicate] → [Ack]
                       1ms      50ms
```

---

## 26. Simulation Ideas

1. **Crash Recovery Simulator**
   - Simulate crash at different points
   - Show: data lost vs recovered

2. **Durability Level Comparison**
   - Compare: memory vs WAL vs replicated
   - Show: crash scenarios

3. **Replication Lag Impact**
   - Vary replication delay
   - Show: data loss on failover

---

## 27. Case Studies

### Case 1: MySQL with InnoDB (WAL + replication)
Result: RPO <100ms, RTO <5 minutes

### Case 2: DynamoDB (distributed quorum)
Result: RPO 0, RTO <1 minute

---

## 28. Related Topics

- **ACID Properties**
- **Recovery Algorithms**
- **Data Replication**

---

## 29. Advanced Topics

### Crash Recovery Algorithms
```
ARIES (Algorithms for Recovery and Isolation Exploiting Semantics):
  - Analysis phase: scan log, identify uncommitted
  - Redo phase: replay committed writes
  - Undo phase: rollback uncommitted

Result: consistent state after crash
```

---

## 30. Production Checklist

- [ ] Implement WAL (every write to disk)
- [ ] Fsync before client ack (true durability)
- [ ] Implement replication (avoid single-point loss)
- [ ] Monitor WAL size (don't grow unbounded)
- [ ] Checkpoint regularly (fast recovery)
- [ ] Test recovery (monthly, full crash sim)
- [ ] Verify replication lag (< 1 second)
- [ ] Add checksums (detect corruption)
- [ ] Backup independently (separate location)
- [ ] Document RPO/RTO (set expectations)
- [ ] Monitor fsync latency (alert if slow)
- [ ] Measure recovery time (RTO testing)

---

*Last Updated: 2026-05-28*
