---
title: Deadlock Prevention & Detection Deep Dive - L5 Operating Systems
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# Deadlock Prevention & Detection Deep Dive - L5 Operating Systems

> **[🎨 View Interactive Diagram](deadlock-architecture.html)** | [← Back to Index](../../systems-index.html)

*"How prevent systems from hanging due to deadlock? How detect when stuck?"*

---

## 1. Problem Statement

**Core Question:** When can deadlock occur? How prevent or detect?

Conditions (all must be true):
- Mutual exclusion: resource can't be shared
- Hold-and-wait: hold while requesting
- No preemption: can't forcibly take
- Circular wait: A→B→C→A

---

## 2. Real World Analogy

**Traffic Intersection:**

Deadlock:
- Car A: straight, Car B: right
- A blocks B, B blocks A
- Both: stuck

Prevention:
- Order: all take right first, then straight
- Or: traffic light (mutual exclusion of intersection)

---

## 3. Prevention Strategies

### Eliminate Conditions

```
Mutual exclusion: can't eliminate (resource nature)
Hold-and-wait: request all before acquiring
No preemption: timeout, forced release
Circular wait: strict ordering
```

---

## 7. Production Architecture

```
[Lock Manager]
  Request order: A → B → C (always)
  Violation: reject request
  
[Resource Graph]
  Nodes: processes, resources
  Edges: allocation, request
  Cycle: deadlock detected
```

---

## 8. Components

### Wait-For Graph

```
Process → Lock (waiting)
Cycle: deadlock exists
Detection: DFS/BFS cycle check
```

---

## 9. Internal Working

### Deadlock Detection Algorithm

```
Step 1: build resource graph
Step 2: check for cycles (DFS)
Step 3: if cycle found, deadlock exists
Step 4: break cycle (kill process or roll back)
```

---

## 10. Failure Scenarios

### Scenario 1: Multi-Resource Deadlock

```
Thread A: holds DB lock, needs file lock
Thread B: holds file lock, needs DB lock
Result: deadlock
```

### Scenario 2: Phantom Deadlock

```
False positive: thought deadlocked
  But timeout expired, resumed
  
Harm: incorrectly killed process
```

---

## 12. Key Strategy

### 1. Lock Ordering

```
Global order: DB < File < Memory
All threads: acquire in same order
Guarantee: no circular wait
Result: no deadlock
```

### 2. Timeout

```
Acquire lock: timeout 5s
Exceed: release, retry
  Or: fail gracefully
  
Trade: liveness vs atomicity
```

---

## 13. Bottlenecks Table

| Issue | Impact | Fix |
|---|---|---|
| Undetected deadlock | Hang | Detection timeout |
| False deadlock kill | Data loss | Careful roll back |
| Lock ordering violation | Deadlock | Enforce ordering |

---

## 15. Monitoring

### Key Metrics

```
✓ Potential deadlock cycles
✓ Lock wait chains
✓ Timeout occurrences
✓ Recovery success
```

---

## 16. Optimizations

### 1. Early Detection

```
Detect: before deadlock
  Track: every acquisition
  Check: cycles immediately
  
Cost: CPU overhead
Benefit: faster prevention
```

---

## 19. Interview Questions

1. **Deadlock prevention**
   - Conditions?
   - Strategies?

---

## 20. Common Mistakes

1. **No timeout**
   - Deadlock: permanent hang
   - Add: timeout mechanism

---

## 21. Code Examples

### Go: Timeout on Lock

```go
select {
case <-time.After(5 * time.Second):
    return errors.New("lock timeout")
default:
    mu.Lock()
    defer mu.Unlock()
}
```

---

## 30. Production Checklist

- [ ] Lock ordering documented
- [ ] Timeout configured
- [ ] Deadlock detection enabled
- [ ] Monitoring: cycles, timeouts
- [ ] Testing: stress test
- [ ] Recovery: graceful on detection
- [ ] Alerts: deadlock detected
- [ ] Periodic: audit lock usage
- [ ] Documentation: critical resources
- [ ] Training: lock discipline

---

*Last Updated: 2026-05-28*
