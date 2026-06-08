---
title: Performance Tuning & Profiling Deep Dive - L5 Operating Systems
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# Performance Tuning & Profiling Deep Dive - L5 Operating Systems

> **[← Back to Index](../../systems-index.html)**

*"Where's the bottleneck? How profile CPU, memory, I/O?"*

---

## 1. Problem Statement

**Core Question:** How find bottlenecks? How measure system performance?

Challenge:
- Bottleneck: invisible (CPU, memory, I/O hidden)
- Guessing: expensive
- Need: measurement, profiling

---

## 2. Real World Analogy

**Factory Bottleneck:**

No measurement:
- "Why slow?"
- Guess: maybe assembly?
- Wrong: actually shipping

With profiling:
- Measure: each station
- Find: shipping slowest (bottleneck)
- Optimize: shipping
- Result: 10x faster

---

## 3. Components

### CPU Profiling

```
Sampling: interrupt every 1ms
  Stack trace: current code
  Aggregate: histogram of where CPU spends time
  
Output: flame graph (visual)
```

### Memory Profiling

```
Track: allocations
  Size: per allocation
  Location: call stack
  
Output: heap map
```

### I/O Profiling

```
Track: I/O operations
  Latency: per syscall
  Device: which one slow
  
Output: latency distribution
```

---

## 7. Production Architecture

```
[Application with Instrumentation]
  Probes: CPU sampling, I/O tracking
  
[Profiler]
  Collect: stack traces, metrics
  Store: in-memory buffer
  
[Analysis]
  Aggregate: histogram
  Identify: bottlenecks
```

---

## 8. Internal Working

### Stack Sampling

```
Timer: every 1ms
Interrupt: CPU
Capture: stack trace (100 samples/sec)

Aggregate:
  Function A: 30% of CPU
  Function B: 20% of CPU
  
Insight: A is bottleneck
```

---

## 9. Failure Scenarios

### Scenario 1: Missing Bottleneck

```
Profiling: shows CPU 50%, memory 40%
Missed: I/O latency (50% of time)
  I/O profiler: wasn't enabled
  
Result: optimize CPU (no improvement)
  Should optimize: I/O
```

---

## 12. Key Strategy

### 1. Multi-Layer Profiling

```
CPU: where is time spent?
Memory: where is space used?
I/O: where are waits?
Lock contention: where blocked?

All together: complete picture
```

### 2. Baseline & Comparison

```
Baseline: before optimization
Optimized: after change
Compare: improvements measured

Trade: guess vs evidence
```

---

## 13. Bottlenecks Table

| Layer | Tool | Metric |
|---|---|---|
| CPU | perf, pprof | CPU time, flame graph |
| Memory | valgrind, heaptrack | Allocations, RSS |
| I/O | iotop, iostat | I/O latency, throughput |
| Lock | lockstat | Contention time |

---

## 15. Monitoring

### Key Metrics

```
✓ CPU profiling: enabled
✓ Memory profiling: periodic
✓ I/O profiling: sampled
✓ Latency distribution: percentiles
```

---

## 16. Optimizations

### 1. Hot Path Optimization

```
Profiling: shows hot function (90% CPU)
Optimize: that function
  Cost: high impact
  Reward: big speedup

Example: sorting in tight loop
  Switch: to faster algorithm
  Result: 5x improvement
```

---

## 19. Interview Questions

1. **Identify bottleneck**
   - Process?

2. **Optimize CPU vs memory**
   - Tradeoff?

---

## 21. Code Examples

### Go: CPU Profiling

```go
import _ "net/http/pprof"

func main() {
    go func() {
        log.Println(http.ListenAndServe("localhost:6060", nil))
    }()
    
    // Main app
}

// Access: http://localhost:6060/debug/pprof/
// Profile CPU: go tool pprof http://localhost:6060/debug/pprof/profile
```

---

## 22. Tools

### Linux Tools

```
perf: CPU sampling
  perf record -g
  perf report
  
flamegraph: visualize CPU
  
valgrind: memory profiling
  valgrind --leak-check=full app
  
iotop: I/O monitoring
  iotop -o
  
systemtap: dynamic tracing
  trace syscalls, function calls
```

---

## 30. Production Checklist

- [ ] Baseline profiling completed
- [ ] Profiling overhead <5%
- [ ] Monitoring: continuously
- [ ] Hot path identified
- [ ] CPU, memory, I/O profiled
- [ ] Lock contention measured
- [ ] Bottleneck prioritized
- [ ] Optimization: highest impact first
- [ ] Regression testing: before/after
- [ ] Alerts: performance degradation

---

*Last Updated: 2026-05-28*
