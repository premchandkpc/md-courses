---
title: Kernel vs User Space Deep Dive - L5 Operating Systems
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# Kernel vs User Space Deep Dive - L5 Operating Systems

> **[🎨 View Interactive Diagram](kernel-userspace-architecture.html)** | [← Back to Index](../../systems-index.html)

*"Why separate kernel and user modes? What's the cost of system calls?"*

---

## 1. Problem Statement

**Core Question:** How protect kernel from user code? What's the overhead of protection?

Challenge:
- User code: buggy, malicious
- Kernel: controls hardware (critical)
- Need: isolation without performance death

---

## 2. Real World Analogy

**Bank:**

No separation:
- Teller & customer: same access
- Customer: steals cash (no protection)

Separated:
- Teller: in secure area (vault access)
- Customer: in lobby (limited access)
- Request: teller handles (syscall)

Result: security, but slower

---

## 3. Why Problem Exists

### Hardware Access

```
Hardware: memory, I/O devices
User program: shouldn't directly access
  DMA: could corrupt any memory
  Disk: could read private files
  
Solution: kernel controls hardware
  User: requests via syscall
  Kernel: validates, executes
```

---

## 4. Components

### Privilege Levels

```
Ring 0: Kernel (full access)
Ring 3: User (limited access)

Transition:
  Syscall: user → kernel (privileged)
  Return: kernel → user
  
Cost: context switch + validation
```

### System Call

```
Call: read(fd, buffer, size)

Mechanism:
  1. User: put args in registers
  2. Trap: privileged instruction (syscall)
  3. CPU: switch to ring 0
  4. Kernel: execute read()
  5. Return: back to user mode
  
Cost: 1-10 microseconds
```

---

## 7. Production Architecture

```
[User Space]
  Application code
  Standard library
  
[Boundary]
  Syscall interface (well-defined)
  Parameter validation
  
[Kernel Space]
  Device drivers
  Memory management
  I/O handling
```

---

## 8. Internal Working

### Syscall Path

```
User program:
  read(fd, buf, size)
  
Register setup:
  rax: syscall number (0 = read)
  rdi: fd
  rsi: buf
  rdx: size
  
Trap instruction:
  syscall (CPU privilege check)
  
Kernel handler:
  Validate: fd valid, buffer writable
  Execute: filesystem read
  Return: bytes read in rax
  
Back to user mode: continue
```

---

## 9. Failure Scenarios

### Scenario 1: Buffer Overflow in Syscall

```
User: passes size=1MB
Kernel: validates
  Writable: only 100KB
  Reject: syscall fails (safe)
```

### Scenario 2: Spectre Leak

```
Attack: read kernel memory via timing
Mitigation: KPTI (separate page tables)
Cost: 5-30% slowdown
```

---

## 12. Key Strategy

### 1. Batch Syscalls

```
Multiple syscalls:
  10 syscalls × 10us = 100us overhead

Batch:
  1 syscall with bulk data = 10us
  
Trade: batch complexity vs speed
```

### 2. Memory Mapping

```
Shared buffer: mapped to both spaces
  Copy: avoid (not always safe)
  Direct: access (if read-only)
  
Benefit: reduce syscall overhead
```

---

## 13. Bottlenecks Table

| Issue | Impact | Fix |
|---|---|---|
| Frequent syscalls | CPU overhead | Batch syscalls |
| Privilege switch | Latency | Memory map |
| Validation cost | Slow | Caching |

---

## 15. Monitoring

### Key Metrics

```
✓ Syscall rate (per second)
✓ Syscall latency
✓ CPU time in kernel
✓ Context switch rate
```

---

## 16. Optimizations

### 1. vDSO (Virtual Dynamic Shared Object)

```
Time syscalls: avoided
  getclock(): fast path in userspace
  Result: no privilege switch

Cost: kernel maintains code in userspace
Benefit: ~10us saved
```

---

## 19. Interview Questions

1. **Reduce syscall overhead**
   - Strategy?

---

## 21. Code Examples

### Go: Syscall Batching

```go
import "syscall"

// Bad: many syscalls
for i := 0; i < 100; i++ {
    syscall.Write(fd, data)
}

// Better: one syscall
syscall.Write(fd, largeBuffer)
```

---

## 30. Production Checklist

- [ ] Syscall profiling enabled
- [ ] Batching implemented
- [ ] vDSO utilized
- [ ] Monitoring: kernel CPU time
- [ ] Latency: P99 tracked
- [ ] Validation: fast-path optimized
- [ ] Memory mapping: configured
- [ ] KPTI: mitigations enabled
- [ ] Secure: parameter validation
- [ ] Alerts: high syscall rate

---

*Last Updated: 2026-05-28*
