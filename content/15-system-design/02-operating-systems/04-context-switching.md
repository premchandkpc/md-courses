---
title: Context Switching & Preemption Deep Dive - L5 Operating Systems
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# Context Switching & Preemption Deep Dive - L5 Operating Systems

> **[🎨 View Interactive Diagram](context-switching-architecture.html)** | [← Back to Index](../../systems-index.html)

*"What's the cost of switching between processes? How reduce overhead?"*

---

## 1. Problem Statement

**Core Question:** How switch between processes without corruption? How minimize switching cost?

Challenge:
- Register state: per-process (100+ registers)
- Cache: invalid after switch (slow startup)
- Frequency: 1000s switches per second

---

## 2. Real World Analogy

**Switching Desks:**

Task A at desk:
- Papers: scattered (working set in cache)
- Pens: organized
- Brain: focused

Switch to desk B:
- Clear desk A (save state)
- Move to desk B
- Disoriented: papers not there (cache miss)

Cost: 5 minutes setup (cold cache)

---

## 3. Why Problem Exists

### Cache Misses

```
Process A: L1 cache warm (data loaded)
  Access: 1 cycle (fast)

Context switch:
  Process B: different data
  L1 cache: invalid (A's data)
  
Process B: access cold cache
  Cost: 200 cycles (miss)
  Penalty: 1ms+
```

---

## 4. Naive Approach

**"Save nothing, start fresh"**

Problems:
- Data corruption: inconsistent state
- Slow: cache cold
- Cascading: faults everywhere

---

## 5. Why Naive Fails

### State Corruption

```
Process A: registers hold values
  Context switch: not saved
  Register overwritten: by process B

Resume A:
  Registers: corrupted (wrong values)
  Result: crash or data loss
```

---

## 6. Evolution / Progression

### Cooperative → Preemptive → Optimized (CPU affinity)

---

## 7. Production Architecture

```
[CPU Core]
  Register file (32 registers)
  L1 cache (32KB)

[Process A running]
  Registers: A's state
  L1: A's data

[Interrupt (timer): t=10ms]
  Save: A's registers → kernel stack
  Flush: TLB (address space change)
  Load: B's registers
  Restore: B's accessible pages

[Process B running]
  Registers: B's state
  L1: cold (rebuild on access)
```

---

## 8. Components

### Context Save

```
Registers: 64+ bytes
  General: rax, rbx, ... (128 bytes)
  Special: rip, rsp, ... (32 bytes)
  
Floating point: 128-256 bytes
  SIMD: xmm0-15, ymm0-15

TLB: flush (not saved, discarded)
  Cost: page walks on access (1-10 microseconds)

Total: 256-512 bytes
Time: <1 microsecond (fast hardware)
```

---

## 9. Internal Working

### Detailed Timeline

```
t=0us:       Timer interrupt fired
t=0-0.1us:   CPU: stops process A
t=0.1-0.5us: Save: A's registers (CPU stack)
t=0.5-1us:   Flush: TLB, L1 cache invalid
t=1-2us:     Load: B's registers (from stack)
t=2-3us:     Jump: to B's code

t=3-5us:     Process B starts
t=3-10us:    First accesses: cold misses
t=10-20us:   L1 cache: warming up

Total context switch: ~10 microseconds
Cache penalty: 1-10 milliseconds
Total overhead: 1-10ms per switch
```

---

## 10. Request Lifecycle

```
CPU executing process A for 10ms timeslice

t=0-10ms:    Process A running
  Cache: warming up
  L1: contains A's data
  Throughput: high

t=10ms:      Preemption (timer interrupt)
t=10-10.01ms: Context switch (1 microsecond hardware time, but context lost)

t=10-20ms:   Process B running
t=10-11ms:   Cold cache: misses on B's first accesses
t=11-20ms:   B's cache warming up

t=20ms:      Preemption again (restart A)
t=20-20.01ms: Context switch

t=20-30ms:   Process A resumes
t=20-22ms:   Cold cache: misses (lost A's cache)
```

---

## 11. Data Flow

### Cache Invalidation Example

```
Process A: matrix multiplication
  Cache: 100MB of matrix data (hot)

Context switch:
  TLB: flushed (all virtual→physical mappings invalid)
  L1/L2: not flushed (tagged by ASID, still invalid for wrong process)

Resume A:
  TLB: rebuild on access (slow)
  L1/L2: gradually refill

Cost: 1-10ms (depending on working set size)
```

---

## 12. Key Strategy

### 1. CPU Affinity

```
Pin process to core:
  Core 1: Process A (always)
  
Benefit:
  L1 cache: reused across timeslices
  L2 cache: warm when resumed
  Cost: single warm cache vs cold

Trade: load balancing vs cache locality
Solution: migrate on core idle, otherwise pin
```

### 2. Reduce Switching

```
Longer timeslices:
  10ms → 100ms
  Switches: 10x less
  
Cost: fairness (long waits)
  Long job: 100ms (noticeable)
  
Solution: priority-based switching
  Interactive: 10ms
  Batch: 100ms
```

---

## 13. Failure Scenarios

### Scenario 1: Thrashing from Switches

```
1000 threads, 8 cores
  Context switch: every ~10us
  Cache: cold on every resume
  
CPU: 50% just switching overhead

Solution:
  Cap threads: max 100
  Or: async model (no context switches)
```

### Scenario 2: Cache Bouncing

```
Process A & B: on same core
  A: modifies cache
  B: switch, invalidates
  A: switch back, cold again
  
Result: no cache benefit

Solution: pin to different cores
```

---

## 14. Bottlenecks Table

| Issue | Impact | Fix |
|---|---|---|
| Cold cache | Latency spike | Affinity |
| Too many switches | CPU overhead | Longer slices |
| Cache bouncing | Thrashing | Core pinning |

---

## 15. Monitoring

### Key Metrics

```
✓ Context switch rate (per second)
✓ Cache miss rate (per instruction)
✓ Cache hit ratio (target: >95%)
✓ IPC (instructions per cycle)
✓ TLB miss rate
```

---

## 16. Optimizations

### 1. ASID (Address Space Identifier)

```
Tag: TLB entries with ASID
  No flush: on context switch
  Reuse: cached entries

Benefit: TLB hit rate ~95% (vs 50% without)
Cost: 8-16 bits per TLB entry (negligible)
```

---

## 17. Security

### Spectre Side-Channel

```
Attack: measure cache timing to leak memory
Mitigation: TLB flushing on every switch (KPTI)
Cost: 5-30% performance loss
```

---

## 18. Tradeoffs Table

| Aspect | Frequent | Rare |
|---|---|---|
| Fairness | Good | Poor |
| Cache | Cold | Warm |
| Latency | Even | Spiky |

---

## 19. When NOT to Use

### Don't Switch When:

1. **Critical code path**
   - Disable preemption
   - Atomic sections only

---

## 20. Interview Questions

1. **Optimize context switch**
   - Affinity strategy?
   - Cache impact?

---

## 21. Common Mistakes

1. **Ignoring cache cost**
   - Impact: hidden
   - Monitor: cache metrics

---

## 22. Debugging Guide

### Check Context Switch Rate

```
vmstat 1 (cs = context switches/sec)
High: >1000/sec indicates thrashing
```

---

## 23. Code Examples

### Go: CPU Affinity

```go
package main

import "runtime"

func init() {
    // Pin main goroutine to CPU 0
    runtime.LockOSThread()
}
```

---

## 24. Visual Diagrams

### Cache Loss on Switch

```
Process A:        ████████████ (L1 warm)
Context Switch:   ──────────── (TLB flush)
Process B:        ░░░░░░░░░░░░ (L1 cold)
Resume A:         ░░░░░░░░░░░░ (L1 cold again)
```

---

## 25. Simulation Ideas

1. **Affinity Impact**
   - Vary: thread pinning
   - Show: cache hit rate

---

## 26. Case Studies

### Linux: CPU affinity kernel module
Result: 40% throughput gain for bound threads

---

## 27. Related Topics

- **CPU Scheduling**
- **Memory Management**

---

## 28. Advanced Topics

### Hardware Context

```
Some CPUs: multiple hardware contexts (threads per core)
Cost: context switch = register load (0.1us)
Benefit: no cache loss

Example: Intel SMT (Hyper-Threading)
```

---

## 30. Production Checklist

- [ ] CPU affinity enabled
- [ ] Timeslice tuned (balance switching vs fairness)
- [ ] Context switch rate monitored
- [ ] Cache metrics tracked
- [ ] Critical paths: preemption disabled
- [ ] TLB monitoring enabled
- [ ] ASID used (if available)
- [ ] Reduced latency: priority boost
- [ ] Load balanced dynamically
- [ ] Isolation: check for cache bouncing

---

*Last Updated: 2026-05-28*
