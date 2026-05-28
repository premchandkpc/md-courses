# Synchronization & Mutual Exclusion Deep Dive - L5 Operating Systems

> **[🎨 View Interactive Diagram](synchronization-architecture.html)** | [← Back to Index](../../systems-index.html)

*"How prevent race conditions in multithreaded code? How ensure atomicity?"*

---

## 1. Problem Statement

**Core Question:** How coordinate access to shared resources? How prevent corruption from concurrent access?

Challenge:
- Multiple threads: accessing same data
- Non-atomic: operations take multiple steps
- Result: inconsistency, data loss

---

## 2. Real World Analogy

**Bank Account:**

Without locks:
- Balance: $100
- Thread A: withdraw $50 (read 100, write 50)
- Thread B: withdraw $50 (read 100, write 50)
- Result: $50 (should be $0)

With locks:
- Lock acquired: by first thread
- Operation: atomic
- Other waits: for unlock
- Result: correct

---

## 3. Why Problem Exists

### Race Conditions

```
Counter: shared = 0

Thread A: read 0, increment, write 1
Thread B: read 0, increment, write 1
Result: 1 (should be 2)

Thread safety: not guaranteed
```

---

## 4. Evolution / Progression

### Mutexes → Semaphores → Lock-free → Wait-free

---

## 7. Production Architecture

```
[Shared Resource: counter]

[Mutex Lock]
  Owner: none initially
  Waiters: queue

[Thread A]
  Lock: acquire (succeeds)
  Access: read/modify/write
  Unlock: release
  
[Thread B]
  Lock: try acquire (blocked, waiting)
  Wait: until A releases
  Access: when lock granted
```

---

## 8. Components

### Mutex

```
Binary lock (locked/unlocked)
Cost: fast (atomic operation)
Overhead: spinlock vs sleep (10us - 1ms)
```

### Semaphore

```
Counter-based (0 or positive)
Useful: for limiting resource count
Example: thread pool (N slots)
```

### Read-Write Lock

```
Multiple readers OR single writer
Readers: share (no conflict)
Writer: exclusive
Cost: more complex, slower
```

---

## 9. Internal Working

### Lock Acquisition

```
Thread: tries acquire

Spinlock:
  Loop: test-and-set
  Cost: CPU busy (good if fast)

Sleep lock:
  Blocked: by kernel
  Cost: context switch (bad if contended)

Adaptive: spin if likely fast, sleep if waiting
```

---

## 10. Request Lifecycle

```
Acquire lock:
  t=0us: try atomic operation
  t=0-1us: succeeds (unlocked)
  t=1us: own lock
  
Access critical section:
  t=1-100us: modify shared data
  
Release:
  t=100us: unlock
  t=100-101us: wake waiting thread
```

---

## 11. Data Flow

### Lock Contention

```
1 thread: lock free (no wait)
2 threads: 1 waits (avg 50% contentious)
10 threads: 9 wait (high contention)
100 threads: 99 wait (terrible)

Solution:
  Reduce: shared state
  Or: granular locks
  Or: lock-free algorithms
```

---

## 12. Key Strategy

### 1. Minimize Critical Section

```
Critical: 10 lines
  Lock duration: 10 microseconds
  Cost: acceptable

Critical: 1000 lines
  Lock duration: 1 millisecond
  Cost: huge contention

Optimize: release quickly
```

### 2. Lock Granularity

```
One lock: all data
  Simple, but contention

Many locks: per-data-structure
  Complex, but less contention

Trade: consistency vs performance
```

---

## 13. Failure Scenarios

### Deadlock

```
Thread A: holds lock X, waits for lock Y
Thread B: holds lock Y, waits for lock X
Result: both blocked forever
```

### Livelock

```
Threads: avoid each other
  Retry constantly
  Never progress
```

### Starvation

```
Low-priority: never gets lock
  High-priority: always first
```

---

## 14. Bottlenecks Table

| Issue | Impact | Fix |
|---|---|---|
| Lock contention | Throughput drop | Reduce critical section |
| Deadlock | Hang | Order locks, timeout |
| Starvation | Fairness | Priority queue |

---

## 15. Monitoring

### Key Metrics

```
✓ Lock contention rate
✓ Lock wait time (P95, P99)
✓ Critical section time
✓ Deadlock detection
```

---

## 16. Optimizations

### 1. Lock-Free

```
Atomic operations: CAS (compare-and-swap)
Cost: faster (no syscall)
Trade: complexity (hard to get right)
```

---

## 17. Security

### Malicious Lock Contention

```
Attack: force lock contention
  DOS: throughput collapse
  
Mitigation: rate limiting, per-user quotas
```

---

## 18. When NOT to Use

### Don't Lock When:

1. **Already atomic** (read-only access)
   - Cost: unnecessary

---

## 19. Interview Questions

1. **Prevent deadlock**
   - Strategy?

2. **Optimize lock contention**
   - Approach?

---

## 20. Common Mistakes

1. **Coarse locks**
   - Contention: high
   - Granularity: fine-grained better

2. **Lock ordering issues**
   - Deadlock: possible
   - Document: lock order

---

## 21. Code Examples

### Go: Mutex

```go
var mu sync.Mutex
var counter int

func increment() {
    mu.Lock()
    defer mu.Unlock()
    counter++
}
```

---

## 30. Production Checklist

- [ ] Deadlock detection enabled
- [ ] Lock timeout configured
- [ ] Contention monitoring
- [ ] Critical section minimized
- [ ] Lock granularity balanced
- [ ] Fairness: no starvation
- [ ] Documentation: lock ordering
- [ ] Testing: concurrency tests
- [ ] Performance: lock overhead <5%
- [ ] Priority: boost readers on writer

---

*Last Updated: 2026-05-28*
