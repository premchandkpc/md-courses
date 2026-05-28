# Memory Management & Virtual Memory Deep Dive - L5 Operating Systems

> **[🎨 View Interactive Diagram](memory-architecture.html)** | [← Back to Index](../../systems-index.html)

*"How does 16GB RAM support 100GB of virtual memory? How prevent memory exhaustion?"*

---

## 1. Problem Statement

**Core Question:** How manage limited physical memory for many programs? How isolate memory spaces?

Challenge:
- Programs: want unlimited memory
- Physical RAM: finite (8-64GB typical)
- Need: isolation (process A can't corrupt B's data)

Solution: virtual memory + paging

---

## 2. Real World Analogy

**City Parking:**

No virtual: each car has reserved spot
- Cost: 1M spots needed
- Waste: spots empty when cars away
- Unfair: some cars need 10 spots

Virtual: few actual spots, records in ledger
- Ledger: where cars are (disk or RAM)
- Actual: only busy cars get spots
- Swap: move car to other lot (disk) when needed

Result: 1M cars, 100K spots (virtual = real×10)

---

## 3. Why Problem Exists

### Memory Scarcity

```
Program needs: 100GB RAM
Physical RAM: 16GB

Solution 1: run 1 program (waste)
Solution 2: virtual memory (use disk as backup)

Virtual: program sees 100GB
  Actually: 16GB RAM + 84GB disk
  Swap: move to disk on demand
```

### Isolation

```
Program A accesses memory 0x1000
Program B accesses memory 0x1000

Same address: different data!
  A: sees own heap
  B: sees own heap
  
Mechanism: virtual address → physical address mapping
```

---

## 4. Naive Approach

**"Just use RAM, hope for best"**

Problems:
- Out of memory: crash
- No isolation: A corrupts B
- Fragmentation: can't allocate large blocks

---

## 5. Why Naive Fails

### Physical Fragmentation

```
RAM: 16GB
Allocations: 8GB, 8GB (full)

Free: 0B (no contiguous space)
Next: 10GB allocation → fails!

Solution: paging (divide into pages)
  All pages: 4KB (small, no fragmentation)
```

### Lack of Isolation

```
Program A & B: both in memory
  A writes: to arbitrary address 0x5000
  B's data: at same address (corrupted!)

Protection: virtual memory
  A: sees 0x5000 → physical 0x100000 (A's memory)
  B: sees 0x5000 → physical 0x200000 (B's memory)
```

---

## 6. Evolution / Progression

### Stage 1: Physical Memory Only
- Direct access to RAM
- No isolation

### Stage 2: Segmentation
- Base + limit registers
- Better isolation
- Still fragmentation

### Stage 3: Paging
- Fixed-size pages (4KB)
- Page tables (virtual → physical)
- Swap to disk

### Stage 4: TLB & Caching
- TLB: cache page table entries
- Hot pages: instant lookup
- Cold: page fault

---

## 7. Production Architecture

```
[Virtual Address Space (per process)]
    Code: 0x00400000
    Heap: 0x01000000
    Stack: 0x7fffffff
    
[Page Table]
    0x00400000 → 0x100000 (physical)
    0x01000000 → 0x200000
    0x7fffffff → 0x300000
    
[Physical Memory]
    0x100000: code page
    0x200000: heap page
    0x300000: stack page
    
[Disk]
    Pages not in RAM: swapped here
```

---

## 8. Components

### Page Table

```
Entry: virtual page → physical page

Example (4KB pages):
  Virtual 0x00401000 → Physical 0x100000
  Virtual 0x00402000 → Physical 0x101000
  Virtual 0x00403000 → (disk, not in RAM)
  
Structure:
  Size: 4MB per process (for 4GB address space)
  Hit: ~10 microseconds (TLB hit)
  Miss: ~100 nanoseconds (main memory)
```

### TLB (Translation Lookaside Buffer)

```
Cache: page table entries
  Fast: L1 cache (microseconds)
  Hit rate: 99%+ (working set fits)
  
Miss: go to page table (memory)
  Cost: 10-100x slower
  
Flush: context switch (new process, new mapping)
  Expensive: L1 cache gone
```

### Page Replacement

```
RAM full: new page needed
  Which to evict?
  
LRU (least recently used):
  Evict: oldest access
  Benefit: keeps hot pages
  
FIFO (first in, first out):
  Evict: oldest created
  Simple, worse hit rate

Optimal:
  Evict: future access furthest away
  Impossible to know
```

---

## 9. Internal Working

### Page Fault Handling

```
Process: access address 0x01000000
CPU: check TLB

TLB miss:
  CPU: consult page table
  Entry: 0x01000000 → (disk, not in RAM)
  
Page fault:
  CPU: interrupt OS
  OS: disk read (10ms)
  
While waiting:
  OS: context switch to other process
  CPU: not idle
  
After 10ms:
  Disk: page transferred to RAM
  Page table: updated
  Process: resume
```

### Address Translation

```
Virtual address: 0x00401234

Split:
  VPN (virtual page number): 0x00401
  Offset: 0x234
  
Lookup:
  Page table[VPN] = 0x100
  
Physical address:
  PPN (physical page number): 0x100
  Address: 0x100000 + 0x234 = 0x100234
```

---

## 10. Request Lifecycle

```
Program: allocate 1GB heap

t=0ms:       malloc(1GB) call
t=0-1ms:     Allocation recorded (page table)
t=1ms:       Return pointer (0x01000000)
t=1-10ms:    First access to page
t=10ms:      Page fault (disk read)
t=10-20ms:   Disk I/O (OS busy, context switch)
t=20ms:      Page loaded, retry
t=20-21ms:   Data access complete

Cost: first access 20ms (not 0)
Later accesses: <1ms (if in cache)
```

---

## 11. Data Flow

### Memory Pressure & Swapping

```
System: 16GB RAM, 100 processes

Status: 90% RAM used (high)

New process: requests 1GB
  Free: 1.6GB insufficient
  
OS action: evict pages
  Select: LRU pages
  Swap: write to disk (10ms per page)
  Free: space for new

Result: system slow (I/O busy)
```

---

## 12. Key Strategy

### 1. Reduce Page Faults

```
Working set: pages actively used
  Keep: in RAM
  Cost: N pages × 4KB
  
Example: 1GB app, working set 100MB
  100MB in RAM: 99% hit rate
  1GB in RAM: wasted

Technique:
  Profile: which pages hot
  Ensure: > working set in RAM
```

### 2. Manage Swap

```
Fast swap (SSD):
  10x slower than RAM (0.1ms vs 0.01ms)
  Acceptable if rare

Slow swap (HDD):
  100x slower (10ms)
  Unacceptable if frequent
  
Strategy: fast swap for spikes, SSD recommended
```

### 3. NUMA Awareness

```
Multi-socket system:
  Local NUMA: fast access
  Remote NUMA: slow (2-3x slower)

Optimization:
  Threads: pin to NUMA node
  Allocate: local memory
  Result: ~30% faster
```

---

## 13. Failure Scenarios

### Scenario 1: Thrashing

```
System: 16GB RAM
Working set: 100 programs × 200MB = 20GB

Mismatch: working set > RAM
  Constant: page eviction & reload
  CPU: 90% disk I/O, 10% actual work

Result: throughput collapse

Solution:
  Reduce: programs (fewer)
  Or: upgrade RAM
  Or: reduce: memory per program
```

### Scenario 2: OOM Killer

```
System: out of memory
  Linux: OOM killer activated
  Kill: largest process
  
Result: production crash

Prevent:
  Memory limit: enforced (cgroups)
  Graceful: shutdown on limit
  Alert: before hitting limit
```

### Scenario 3: Memory Leak

```
Process: allocates, forgets to free
  Memory: grows over time
  RAM: eventually exhausted

Detection: hard (looks like legitimate use)
Solution:
  Monitor: memory growth
  Alert: on steady increase
  Profile: find leak source
```

---

## 14. Bottlenecks Table

| Issue | Impact | Fix |
|---|---|---|
| Too many page faults | System slow | Increase RAM |
| Working set > RAM | Thrashing | Reduce load |
| Slow swap | I/O bound | Use SSD swap |
| Memory leak | Crash after N hours | Fix allocation |

---

## 15. Monitoring

### Key Metrics

```
✓ Memory utilization (% of total)
✓ Page fault rate (per second)
✓ Swap usage (should be minimal)
✓ Working set (pages accessed)
✓ TLB miss rate (% faults)
```

---

## 16. Optimizations

### 1. Huge Pages

```
Default: 4KB pages
Huge: 2MB pages (512x larger)

Benefit:
  TLB: fewer entries needed
  Fault: fewer (less overhead)
  
Cost:
  Internal fragmentation (allocate 2MB even if need 1KB)
  
Use: large memory applications
```

### 2. Memory Compression

```
Compress: pages before swap
  Before: 4KB page
  Compressed: 1KB
  Swap: 4x space saved

Trade: CPU (compression) vs I/O
  CPU cheap: compression recommended
```

---

## 17. Security

### 1. Spectre/Meltdown

```
Vulnerability: side-channel memory access
Attack: read kernel memory from user process
  
Mitigation:
  KPTI: kernel page table isolation
  Cost: 5-30% performance loss
```

---

## 18. Tradeoffs Table

| Aspect | More RAM | Swap Disk |
|---|---|---|
| Speed | Fast | Slow (10-100x) |
| Cost | Expensive | Cheap |
| Capacity | Limited | Unlimited |
| Use | Working set | Overflow |

---

## 19. Alternatives

### Shared Memory

```
Multiple processes: same pages
  Cost: memory saved
  Complexity: synchronization needed
  Use: IPC, databases
```

---

## 20. When NOT to Use

### Don't Rely On Swap When:

1. **Real-time systems**
   - Latency: must be bounded
   - Swap: unpredictable (10ms)

---

## 21. Interview Questions

1. **Design memory allocator**
   - Virtual memory?
   - Page faults?
   - Fragmentation?

2. **System thrashing**
   - Cause?
   - Detect?
   - Fix?

3. **Memory isolation**
   - How prevent corruption?
   - Performance cost?

---

## 22. Common Mistakes

1. **Ignoring page faults**
   - Impact: hidden (not obvious)
   - Monitor: measurement

2. **No swap space**
   - Crash: on spike
   - Add: swap (emergency buffer)

3. **Wrong page size**
   - Huge pages: internal fragmentation
   - Tune: to workload

4. **No NUMA awareness**
   - Performance: 30% worse
   - Align: threads to nodes

---

## 23. Debugging Guide

### Step 1: Check Memory Usage

```
free -h (RAM, swap)
ps aux | awk (per-process)
```

### Step 2: Check Page Faults

```
vmstat 1 (major faults/sec)
sar -B (paging activity)

High: page faults frequent
```

---

## 24. Code Examples

### Go: Memory Profiling

```go
import "runtime/debug"

func init() {
    debug.SetGCPercent(50) // Trigger GC at 50% growth
}

func main() {
    var m runtime.MemStats
    runtime.ReadMemStats(&m)
    
    fmt.Printf("Alloc: %v MB\n", m.Alloc/1024/1024)
    fmt.Printf("TotalAlloc: %v MB\n", m.TotalAlloc/1024/1024)
}
```

---

## 25. Visual Diagrams

### Virtual Memory Translation

```
Virtual Address:     [VPN:10 bits] [Offset:12 bits]
                            ↓
                     Page Table
                            ↓
Physical Address:    [PPN:20 bits] [Offset:12 bits]
```

---

## 26. Simulation Ideas

1. **Page Replacement Impact**
   - Vary: working set
   - Show: hit rate, latency

---

## 27. Case Studies

### Linux OOM Killer Incident
Result: production crash (insufficient monitoring)

---

## 28. Related Topics

- **CPU Scheduling**
- **I/O Subsystem**

---

## 29. Advanced Topics

### Copy-on-Write

```
Fork: new process
Cost: copy all memory (expensive)

Optimization:
  Share: pages initially
  Copy: only when written

Benefit: fork near-instant
```

---

## 30. Production Checklist

- [ ] Monitor page fault rate
- [ ] Swap space provisioned (2-4x RAM)
- [ ] Memory limits enforced (cgroups)
- [ ] OOM killer behavior configured
- [ ] Working set profiling done
- [ ] Swap on SSD (not HDD)
- [ ] NUMA affinity configured
- [ ] Memory leak detection enabled
- [ ] Alerts: memory utilization >80%
- [ ] Capacity planning: 6-month forecast

---

*Last Updated: 2026-05-28*
