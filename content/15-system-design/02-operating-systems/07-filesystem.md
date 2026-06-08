---
title: File System Internals Deep Dive - L5 Operating Systems
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# File System Internals Deep Dive - L5 Operating Systems

> **[🎨 View Interactive Diagram](filesystem-architecture.html)** | [← Back to Index](../../systems-index.html)

*"How survive crashes without data loss? How organize files efficiently?"*

---

## 1. Problem Statement

**Core Question:** How persist data safely? How recover from crashes?

Challenge:
- Crashes happen (power loss, kernel panic)
- Data: on disk (slow)
- Writes: not atomic (multiple steps)

---

## 2. Real World Analogy

**Ledger Book:**

No recovery:
- Write: multiple pages
- Power off: some written, some not
- Recovery: incomplete transaction

With logging:
- Record: intent to change
- Atomic: commit (1 write)
- Recovery: replay log

---

## 3. Components

### Inode

```
Metadata: file size, owner, permissions
Pointers: to data blocks
  Direct: 10-15 blocks (small files)
  Indirect: points to block of pointers
  Double-indirect: for large files
```

### Journal

```
Write-ahead logging:
  Record: intent
  Execute: operation
  Commit: mark done
  
Recovery: replay uncommitted entries
```

---

## 7. Production Architecture

```
[Application]
  Write: call fsync()
  
[Page Cache]
  Buffer: in-memory
  
[Journal (disk)]
  Log entry: write-ahead
  
[Data Blocks (disk)]
  Actual: data written
```

---

## 8. Internal Working

### Crash Recovery

```
Operation: write file + update inode

t=0: write inode metadata (not done)
t=1: crash (power loss)

Recovery:
  Inode: invalid (incomplete)
  Journal: has intent
  Replay: complete operation
```

---

## 9. Failure Scenarios

### Scenario 1: Corruption After Crash

```
File: lost or corrupted
Cause: write not atomic
Fix: journal replay
```

---

## 12. Key Strategy

### 1. Ordered Writes

```
Data: write first
  Inode: then update pointer
  
Invariant: if inode valid, data present
Result: always consistent
```

---

## 15. Monitoring

### Key Metrics

```
✓ Fsync rate
✓ Journal size
✓ Corruption errors
✓ Recovery time
```

---

## 19. Interview Questions

1. **Prevent data loss**
   - Strategy?

---

## 21. Code Examples

### Go: Safe Write

```go
f, _ := os.Create("file.txt")
defer f.Close()
f.WriteString("data")
f.Sync() // Fsync: ensure written
```

---

## 30. Production Checklist

- [ ] Journal enabled
- [ ] Fsync on critical writes
- [ ] Regular backups
- [ ] Corruption detection
- [ ] Recovery tested
- [ ] Disk health monitored
- [ ] Cache: ordered writes
- [ ] Quota: enforce limits
- [ ] Integrity: checksums
- [ ] Space: trend monitoring

---

*Last Updated: 2026-05-28*
