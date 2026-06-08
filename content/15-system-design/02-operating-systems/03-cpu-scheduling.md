---
title: CPU Scheduling Algorithms Deep Dive - L5 Operating Systems
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# CPU Scheduling Algorithms Deep Dive - L5 Operating Systems

> **[🎨 View Interactive Diagram](cpu-scheduling-architecture.html)** | [← Back to Index](../../systems-index.html)

*"How does OS decide which process runs next? Fair or optimal?"*

---

## 1. Problem Statement

**Core Question:** How allocate CPU among competing processes? How balance fairness vs throughput?

Challenge:
- Processes: 100+ waiting
- CPU: 1-16 cores
- Goals: fairness, throughput, low latency

---

## 2. Real World Analogy

**Supermarket Checkout:**

FCFS (First-Come-First-Served):
- Fair: first customer served first
- Unfair to short orders: waits behind long checkout

Priority queue:
- Fairness: gone
- Short orders: served fast
- But: long orders starve

Round-robin:
- Each customer: 5 minute turn
- Requeue: if not done
- Fairness: all get turns

---

## 3. Why Problem Exists

### Competing Goals

```
Goal 1: throughput (complete jobs fast)
  Solution: long job first

Goal 2: fairness (all make progress)
  Solution: equal slices

Goal 3: latency (interactive responsive)
  Solution: short jobs first

Tradeoff: can't optimize all simultaneously
```

---

## 4. Naive Approach

**"Run until completion"**

Problems:
- Long job: blocks short jobs
- User-facing: feel frozen
- Unfair

---

## 5. Why Naive Fails

### Interactivity Suffers

```
Long job: 10 seconds
Short job: arrives after 5s
  Waits: 5 seconds more (frustrating)

With preemption:
  Long: runs 100ms, pause
  Short: gets turn
  Both: making progress (user sees responsiveness)
```

---

## 6. Evolution / Progression

### FCFS → SJF → Priority → Round-Robin → Multilevel Feedback

---

## 7. Production Architecture

```
[Scheduler Queue]
  Priority 0: long jobs (background)
  Priority 1: normal (default)
  Priority 2: interactive (UI)
  Priority 3: realtime (deadline)

[CPU cores: 8]
  Core 1: Process A (priority 3)
  Core 2: Process B (priority 2)
  Core 3: Process C (priority 1)
  Core 4: Process D (priority 1)
  ...
  Core 8: idle (waiting for work)
```

---

## 8. Components

### Scheduling Algorithms

```
Round-Robin (timeslice 10ms):
  Fair, but overhead from context switches

Priority-based:
  Realtime: 20ms latency guarantee
  Normal: ~100ms
  Background: seconds

CFS (Completely Fair Scheduler):
  Virtual runtime: tracks time given
  Always: pick least time given process
  Result: fair but interactive
```

---

## 9. Internal Working

### Example Schedule

```
Jobs: A(10s), B(2s), C(1s) arrive

FCFS:
  A: 0-10s
  B: 10-12s
  C: 12-13s
  
Fair (10ms slices):
  A: 0-10ms
  B: 10-20ms
  C: 20-30ms
  A: 30-40ms
  ... (interleaved)
  
Wait times: Fair much better for short jobs
```

---

## 10. Request Lifecycle

```
Process: arrives, waits

t=0ms:       Process joins queue
t=0-10ms:    Running on core (timeslice)
t=10ms:      Interrupt (timer)
t=10-12ms:   Context switch
t=12-22ms:   Running again
t=22ms:      Done (if early)
t=22ms:      Back to queue
t=22-32ms:   Another process runs
t=32ms:      Gets another turn
```

---

## 11. Data Flow

### Interactive Response

```
User: clicks button
Process: waiting in queue
  Priority: boosted (interactive)
  
Scheduler: sees boost
  Switch: immediately (preempt)
  Result: <50ms response

User: perceives instant response
```

---

## 12. Key Strategy

### 1. Priority Levels

```
Realtime (priority 0):
  Deadline: hard (must meet)
  Reserved: CPU capacity
  Example: audio, haptics

Interactive (priority 1):
  Latency: <100ms expected
  Example: UI threads, web servers

Normal (priority 2):
  Latency: ~1s acceptable
  Example: background tasks

Batch (priority 3):
  Latency: seconds acceptable
  Example: log processing
```

### 2. Reduce Preemption

```
Problem: frequent context switches (overhead)

Solution:
  Affinity: pin process to core
  Batching: hold process longer if related work
  
Trade: fairness vs overhead
```

---

## 13. Failure Scenarios

### Scenario 1: Priority Inversion

```
Realtime process: waiting for mutex
Normal process: holds mutex, not scheduled
  Realtime: blocked by normal (inverted!)
  
Solution: priority inheritance
  Lock holder: temporarily boosted
  Release: reverts priority
```

### Scenario 2: Starvation

```
Realtime jobs: always in queue
Background job: never scheduled
  Result: starves

Prevention:
  Allocate: percentage per priority
  Realtime: max 80%, rest: min 20%
```

---

## 14. Bottlenecks Table

| Issue | Impact | Fix |
|---|---|---|
| Context switch overhead | CPU wasted | Increase timeslice |
| Priority inversion | Latency spike | Inherit priority |
| Starvation | Jobs never run | Reserve capacity |

---

## 15. Monitoring

### Key Metrics

```
✓ Scheduling latency (wait time)
✓ Context switch rate
✓ Per-core utilization
✓ Run queue depth
✓ Priority distribution
```

---

## 16. Optimizations

### 1. Scheduler Domains

```
Divide: CPUs into groups
  Local: within group (fast migration)
  Remote: between groups (slower)

Result: better cache locality
```

---

## 17. Security

### Timing Side-Channels

```
Attack: measure scheduling delay to infer secrets
Mitigation: constant-time scheduling
```

---

## 18. Tradeoffs Table

| Algorithm | Fairness | Throughput | Latency |
|---|---|---|---|
| FCFS | Poor | Good | Bad |
| SJF | Unfair | Good | Good |
| RR | Fair | OK | OK |
| Priority | Unfair | Good | Best |

---

## 19. When NOT to Use

### Don't Preempt When:

1. **Critical section execution**
   - Atomic: must complete
   - Use: disinterruptible sections

---

## 20. Interview Questions

1. **Design scheduler (1000 tasks)**
   - Algorithm choice?
   - Fairness vs latency?

2. **Priority inversion**
   - Detect?
   - Prevent?

3. **Starvation prevention**
   - How ensure progress?

---

## 21. Common Mistakes

1. **Ignoring context switch cost**
   - Too frequent: wasted CPU
   - Tune: timeslice to workload

2. **No priority levels**
   - Interactive: slow
   - Add: priority buckets

---

## 22. Debugging Guide

### Step 1: Check Scheduling

```
ps -eo pid,pri,cmd (process priorities)
chrt -p PID (current scheduling policy)
```

---

## 23. Code Examples

### Go: Priority Task Queue

```go
type Task struct {
    id       int
    priority int
}

type PriorityQueue struct {
    tasks []Task
}

func (pq *PriorityQueue) Next() Task {
    // Pick highest priority
    maxIdx := 0
    for i := 1; i < len(pq.tasks); i++ {
        if pq.tasks[i].priority > pq.tasks[maxIdx].priority {
            maxIdx = i
        }
    }
    return pq.tasks[maxIdx]
}
```

---

## 24. Visual Diagrams

### Scheduling Timeline

```
P1 [####] P2 [####] P3 [####] P1 [####]
0  10    20  30    40  50    60  70
```

---

## 25. Simulation Ideas

1. **Scheduling Impact**
   - Vary: timeslice
   - Show: latency vs throughput

---

## 26. Case Studies

### Linux CFS: fair scheduling
Result: balanced latency and throughput

---

## 27. Related Topics

- **Context Switching**
- **Priority Inversion**

---

## 28. Advanced Topics

### Energy Awareness

```
DVFS: reduce CPU frequency when idle
Power: save, but heat less
Use: mobile, battery-powered systems
```

---

## 30. Production Checklist

- [ ] Scheduler tuned to workload
- [ ] Priority levels configured
- [ ] CPU affinity enabled
- [ ] Monitoring: scheduling latency
- [ ] Priority inversion prevention
- [ ] Starvation detection
- [ ] Load balanced across cores
- [ ] Realtime: FIFO/RR policy
- [ ] Timeslice: tuned (not too frequent)
- [ ] Priority aging: prevent starvation

---

*Last Updated: 2026-05-28*
