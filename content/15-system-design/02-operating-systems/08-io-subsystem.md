---
title: I/O Subsystem & Device Management Deep Dive - L5 Operating Systems
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# I/O Subsystem & Device Management Deep Dive - L5 Operating Systems

> **[🎨 View Interactive Diagram](io-architecture.html)** | [← Back to Index](../../systems-index.html)

*"How minimize I/O latency? How use DMA for efficiency?"*

---

## 1. Problem Statement

**Core Question:** How handle I/O without blocking CPU? How maximize throughput?

Challenge:
- Disk I/O: 1-10ms (very slow vs CPU: 1ns)
- Network I/O: 1-100ms
- Can't block CPU (waste)

---

## 2. Real World Analogy

**Restaurant Order:**

Blocking (CPU polling):
- Chef: waits by oven
- Oven: cooks (10 minutes)
- Chef: idle (wasteful)

Non-blocking (interrupts):
- Chef: takes order
- Oven: cooks
- Chef: serves other customers
- Oven: signals when done
- Chef: retrieves food

Result: multitasking, no waste

---

## 3. Components

### DMA (Direct Memory Access)

```
Transfer: without CPU
  Device: reads from disk
  Writes: directly to memory
  CPU: not involved
  
Benefit:
  CPU: not occupied
  Throughput: higher
  Latency: same
```

### Interrupts vs Polling

```
Interrupt:
  Device: signals when ready
  CPU: handles immediately
  Cost: context switch

Polling:
  CPU: asks periodically
  Latency: higher
  Cost: wasted cycles
  
Use interrupt: low frequency events
Use polling: high frequency, predictable
```

---

## 7. Production Architecture

```
[Application]
  Issue: async read request
  Continue: not blocked
  
[I/O Controller]
  DMA: transfer disk → memory
  (CPU free to other work)
  
[Interrupt Handler]
  Device: signals completion
  Callback: notify application
```

---

## 8. Internal Working

### I/O Request Lifecycle

```
t=0us:       Application requests read
t=0-1us:     Create I/O request, queue
t=1us:       Return to application (not blocked)
t=1-10000us: Disk I/O happens (DMA, CPU free)
t=10000us:   Interrupt triggered
t=10000-10010us: Interrupt handler: callback
t=10010us:   Application notified (data ready)
```

---

## 9. Failure Scenarios

### Scenario 1: I/O Timeout

```
Device: stuck (no completion)
Timeout: 30 seconds
Result: I/O error reported
```

---

## 12. Key Strategy

### 1. Async I/O

```
Fire and forget: submit requests
  Reap: completions later
  
Benefit:
  Batching: multiple requests
  CPU: not blocked
  Throughput: higher
```

---

## 15. Monitoring

### Key Metrics

```
✓ I/O latency (P95, P99)
✓ I/O throughput (ops/sec)
✓ Queue depth
✓ Device utilization
```

---

## 19. Interview Questions

1. **I/O performance bottleneck**
   - Diagnosis?

---

## 21. Code Examples

### Go: Async I/O

```go
import "os"

f, _ := os.Open("file.txt")
defer f.Close()
buffer := make([]byte, 4096)
n, _ := f.Read(buffer) // Blocks in Go
// Use: goroutines for concurrency
```

---

## 30. Production Checklist

- [ ] Async I/O enabled
- [ ] DMA configured
- [ ] Interrupt handling optimized
- [ ] Queue depth monitored
- [ ] I/O timeout configured
- [ ] Error detection enabled
- [ ] Batching strategy tuned
- [ ] Device: health monitored
- [ ] Alerts: I/O latency spike
- [ ] Caching: reduce I/O

---

*Last Updated: 2026-05-28*
