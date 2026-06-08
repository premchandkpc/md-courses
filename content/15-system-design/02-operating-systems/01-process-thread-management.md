# Process & Thread Management Deep Dive - L5 Operating Systems

> **[🎨 View Interactive Diagram](process-thread-architecture.html)** | [← Back to Index](../../systems-index.html)

*"How do multiple programs run simultaneously? What's the difference between process and thread?"*

---

## 1. Problem Statement

**Core Question:** How share CPU among many programs? How enable concurrency?

Challenge:
- CPU: 1 processor (or few cores)
- Programs: 100+ running
- Need: fair sharing, isolation, speed

Solution: processes + threads + scheduling

---

## 2. Real World Analogy

**Restaurant Kitchen:**

Process: separate kitchen (isolated)
- Ingredients: private (no sharing)
- Recipes: private
- Cost: expensive, independent

Thread: shared kitchen, multiple chefs
- Ingredients: shared
- Recipes: shared
- Cost: cheap, but coordinate needed

Result: threads faster, but harder to manage

---

## 3. Why Problem Exists

### CPU Utilization

```
Program: I/O request (network, disk)
  CPU: idle waiting (wasteful)
  
Solution: run other program
  While program A waits: run program B
  Both: progress (sharing CPU)
  
Result: 100% utilization (vs idle)
```

### Process Isolation

```
Program A: crashes
Process: separate (OS protection)
  Program B: unaffected (survives)

Program A & B: shared memory (threads)
  A crashes: corrupts B's data
  Both: down
```

---

## 4. Naive Approach

**"Let program run until it finishes"**

Problems:
- I/O waits: CPU idle
- Program hangs: system frozen
- Unfair: long job starves short jobs

---

## 5. Why Naive Fails

### I/O Blocking

```
Task: read disk (10ms)
Program: blocks, waits
CPU: idle (wasteful)

Better: context switch
  OS: pause program
  Run: other program
  After 10ms: resume first

CPU: never idle
```

### Fairness

```
Long job: 1 minute
Short job: arrives

Without timeslicing:
  Long: runs entire time
  Short: waits 1 minute (unfair)

With timeslicing (50ms):
  Long: 50ms, pause
  Short: runs
  Both: progress

Fair: all programs make progress
```

---

## 6. Evolution / Progression

### Stage 1: Single Program
- 1 program at a time
- CPU: often idle

### Stage 2: Multiprogramming
- Many programs in memory
- OS switches on I/O
- Crude, not preemptive

### Stage 3: Multitasking (Preemptive)
- Timeslicing (quantum ~10-100ms)
- Fair scheduling
- Context switches automatic

### Stage 4: Threads
- Lightweight concurrency
- Shared memory
- Faster context switch

---

## 7. Production Architecture

```
[Operating System]
    ├─ Process 1 (isolated memory)
    │   ├─ Thread 1a
    │   ├─ Thread 1b
    │   └─ Thread 1c
    │
    ├─ Process 2 (isolated memory)
    │   ├─ Thread 2a
    │   └─ Thread 2b
    │
    └─ Process 3
        └─ Thread 3a

[CPU Scheduler]
    ├─ Time quantum: 10ms
    ├─ Current: running Thread 1a
    ├─ Queue: waiting [Thread 2a, Thread 3a, Thread 1b]
    └─ Update: every 10ms interrupt
```

---

## 8. Components

### Process

```
Isolated resources:
  Memory: virtual address space (heap, stack, code)
  Files: file descriptors
  Signals: process-specific
  Environment: variables

Cost:
  Memory: 10-100MB per process
  Context switch: expensive (TLB flush)
  Creation: slow (100ms)
```

### Thread

```
Shared within process:
  Memory: heap (shared)
  Files: descriptors (shared)
  Code: shared

Private:
  Stack: per-thread (1-8MB)
  TLS (thread-local storage)
  Registers

Cost:
  Memory: 1-8MB per thread (vs 10-100MB process)
  Context switch: fast (TLB valid)
  Creation: fast (1ms)
```

### Thread Pool

```
Pre-allocated threads:
  Workers: 100 threads ready
  Queue: incoming work

Benefit:
  No creation delay (already exists)
  No cascade (bounded workers)
  
Bad: fixed size
  Too few: underutilized
  Too many: thrashing

Solution: dynamic sizing (scale workers)
```

---

## 9. Internal Working

### Context Switch Timeline

```
Process A running:
  CPU: executing A's code
  L1 cache: A's data loaded
  TLB: A's page mappings cached

Interrupt (timer, I/O):
  CPU: pause A
  Save: A's registers (stack)
  
Load: B's state
  Load: B's registers (stack)
  Flush: TLB (different address space)
  L1 cache: still A's (miss on access)

Process B running:
  Cold start: L1 cache misses (~10-50ms penalty)
  
Total: context switch cost
  Process: 1-10 microseconds
  Plus: cache penalty (1-10ms)
  Total overhead: 1-10ms per switch
```

### Thread Creation

```
Process A calls: spawn thread

Step 1: Allocate
  Stack: 1MB (per thread)
  TCB (thread control block): 64 bytes

Step 2: Initialize
  Registers: reset
  Stack pointer: point to stack
  Return address: function to run

Step 3: Add to scheduler
  Queue: add to ready queue
  Next timeslice: scheduled

Cost: 1-5ms (process: 100-1000ms)
```

---

## 10. Request Lifecycle

```
Web server: 1000 concurrent requests

Architecture: thread pool (100 workers)

t=0ms:       Request 1 arrives
t=0-1ms:     Get thread from pool
t=1-5ms:     Process request
t=5-100ms:   I/O (database read)
t=100-101ms: Result received
t=101-102ms: Send response
t=102ms:     Thread back to pool

Meanwhile (0-102ms):
  999 other requests: using other threads
  
Result: 1000 served by 100 threads
  Throughput: 1000 requests
  CPU: multiple cores, shared
```

---

## 11. Data Flow

### Process Lifecycle

```
Create:
  Parent: fork() syscall
  OS: copy process (heap, stack, code)
  Child: new PID, separate address space
  
Ready:
  Waiting: CPU access
  Scheduler: picks when to run
  
Running:
  CPU: executing code
  Timeslice: ~10-100ms
  
Blocked:
  I/O wait: disk, network
  Mutex: waiting for lock
  
Terminated:
  exit(): process ends
  Zombie: waiting for parent to reap
```

---

## 12. Key Strategy

### 1. Thread Pool Sizing

```
Underutilized:
  100 worker threads
  10 requests/sec
  Cost: 100 threads waiting (waste)

Overutilized:
  10 worker threads
  1000 requests/sec
  Cost: queue backlog, latency

Optimal:
  CPUs: 8 cores
  Workers: 50-100 (2x-10x cores)
  Reason: some block on I/O, others run
  
Dynamic: scale based on queue depth
```

### 2. Reduce Context Switches

```
Problem: many threads, many switches
  Overhead: 10% CPU just switching

Solution:
  Threads: match CPU cores (fewer switches)
  Affinity: pin thread to core
  Batch: group related work
  
Trade: throughput vs latency (batch increases latency)
```

### 3. Stack Size

```
Default: 1MB per thread (many waste this)

Large stack:
  Memory: limits thread count (10GB for 10K threads)
  Unused: 900KB sitting

Small stack:
  Memory: efficient (100KB viable)
  Risk: overflow if deep recursion

Optimization: detect needs, size accordingly
```

---

## 13. Failure Scenarios

### Scenario 1: Thread Pool Exhaustion

```
100 workers, all blocked on I/O
  New request: no available thread
  Queue: growing
  
Result: backlog, latency spike

Solution:
  Dynamic sizing: spawn more threads
  Timeout: release hung threads
  Circuit breaker: reject if queue full
```

### Scenario 2: Context Switch Thrashing

```
1000 threads, 8 cores
  Context switch: every 10ms
  CPU: 50% just switching (cache thrashing)
  
Result: throughput collapse

Solution:
  Cap threads: limit to 100
  Or: async model (single thread, non-blocking I/O)
```

### Scenario 3: Stack Overflow

```
Deep recursion:
  Frame: 100 bytes per call
  Depth: 10,000 calls
  Total: 1MB (exceeds 1MB stack)
  
Result: SIGSEGV (segmentation fault)

Detection: hard (stack grows down)
Solution: increase stack, reduce recursion
```

---

## 14. Bottlenecks Table

| Issue | Impact | Fix |
|---|---|---|
| Too many threads | Context switch overhead | Cap threads |
| Too few threads | Queue backlog | Dynamic sizing |
| Large stack | Memory limit | Tune per app |
| No affinity | Cache misses | Pin threads |

---

## 15. Monitoring

### Key Metrics

```
✓ Thread count (total, per process)
✓ Context switch rate (per second)
✓ CPU utilization (per core)
✓ Queue depth (requests waiting)
✓ Thread pool availability (% free)
```

---

## 16. Optimizations

### 1. Thread Pool Tuning

```
Workers = CPUs × (1 + (I/O time) / (CPU time))

Example:
  CPUs: 8
  I/O time: 100ms
  CPU time: 10ms
  Workers: 8 × (1 + 100/10) = 88

Trade: memory vs throughput
```

### 2. CPU Affinity

```
Thread A: always on core 1
  L1 cache: warm (reused)
  TLB: valid
  
Result: 10-30% throughput gain
```

---

## 17. Security

### 1. Race Conditions

```
Shared data: counter
Thread A: read 100
Thread B: read 100
Thread A: increment → write 101
Thread B: increment → write 101
Result: 101 (should be 102)

Prevent: mutual exclusion (locks)
```

---

## 18. Tradeoffs Table

| Aspect | Process | Thread |
|---|---|---|
| Memory | 10-100MB | 1-8MB |
| Creation | 100-1000ms | 1-5ms |
| Context switch | 1-10ms | 0.1-1ms |
| Isolation | Strong | Weak |
| Use | Heavy isolation | Shared work |

---

## 19. Alternatives

### Async I/O

```
No threads: single-threaded
Event loop: handles many I/O
Cost: CPU low (no switches)
Trade: callback complexity
```

---

## 20. When NOT to Use

### Don't Use Many Threads When:

1. **Computation-bound work**
   - Threads: no benefit (blocking)
   - Use: process pool

---

## 21. Interview Questions

1. **Design web server (10K concurrent)**
   - Processes or threads?
   - Why?
   - Pool size?

2. **Context switch cost**
   - Why expensive?
   - How reduce?

3. **Thread pool starvation**
   - Cause?
   - Prevent?

---

## 22. Common Mistakes

1. **Unlimited threads**
   - Memory: exhausted
   - Cap: at reasonable limit

2. **Single-threaded I/O**
   - Blocked on one request
   - Use: threads or async

3. **No pool**
   - Create per request
   - Cost: high
   - Use: reusable pool

4. **Large default stacks**
   - Waste: per thread
   - Size: to needs

---

## 23. Debugging Guide

### Step 1: Check Thread Count

```
ps -eLf | wc -l (total threads)
jps (Java processes)
jstack (Java thread dump)
```

### Step 2: Check Context Switch Rate

```
vmstat 1 (context switches/sec)
cat /proc/stat (count)

High rate: too many threads
```

---

## 24. Code Examples

### Go: Thread Pool

```go
type WorkerPool struct {
    workers int
    jobs    chan Job
    results chan Result
}

func (wp *WorkerPool) Start() {
    for i := 0; i < wp.workers; i++ {
        go func() {
            for job := range wp.jobs {
                result := job.Execute()
                wp.results <- result
            }
        }()
    }
}

func (wp *WorkerPool) Submit(job Job) {
    wp.jobs <- job
}
```

---

## 25. Visual Diagrams

### Process vs Thread

```
Process:     [Heap] [Stack] [Code]   (isolated)
             ↓
             OS protection

Thread:      [Shared Heap] [Stack1] [Stack2] (shared)
             ↓
             same process
```

---

## 26. Simulation Ideas

1. **Context Switch Impact**
   - Vary: thread count
   - Show: CPU, latency

---

## 27. Case Studies

### Nginx: async I/O single thread
Result: 1M connections per server

---

## 28. Related Topics

- **Synchronization & Locking**
- **CPU Scheduling**

---

## 29. Advanced Topics

### Green Threads

```
User-level: threads in language (not OS)
Benefit: faster creation/switch
Cost: no true parallelism (1 OS thread)

Example: Go goroutines map to N OS threads
```

---

## 30. Production Checklist

- [ ] Thread pool sized dynamically
- [ ] CPU affinity configured
- [ ] Context switch monitoring
- [ ] Stack size tuned to app
- [ ] Max thread limit enforced
- [ ] Deadlock detection (timeout)
- [ ] Thread leak prevention (cleanup)
- [ ] Graceful shutdown (drain queue)
- [ ] Monitoring: thread count, switches
- [ ] Load test: concurrent load

---

*Last Updated: 2026-05-28*
