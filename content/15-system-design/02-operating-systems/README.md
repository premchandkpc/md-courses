---
title: Operating Systems Deep Dive
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# Operating Systems Deep Dive

System fundamentals: how OS manages hardware resources, processes, memory, concurrency.

## Topics

### 1. Process & Thread Management
- Process lifecycle (create, ready, running, blocked, terminated)
- Context switching overhead
- Thread pools & work queues
- Green threads vs OS threads

### 2. Memory Management & Virtual Memory
- Virtual address spaces
- Page tables & TLB
- Paging vs segmentation
- Memory fragmentation (internal/external)

### 3. CPU Scheduling Algorithms
- FCFS, Round-robin, Priority, Multilevel feedback
- Context switch cost
- Preemption & fairness
- Scheduling for throughput vs latency

### 4. Context Switching & Preemption
- Cost of context switch (L1/L2/L3 cache loss)
- Preemptive vs cooperative multitasking
- Reducing context switches
- CPU affinity & cache locality

### 5. Synchronization & Mutual Exclusion
- Critical sections & race conditions
- Locks, semaphores, mutexes
- Deadlock potential
- Lock-free data structures

### 6. Deadlock Prevention & Detection
- Deadlock conditions (circular wait, hold-and-wait)
- Resource allocation graph
- Prevention vs detection vs avoidance
- Recovery strategies

### 7. File System Internals
- Inode structure & directories
- Block allocation
- Write-ahead logging (WAL)
- Journaling for crash recovery

### 8. I/O Subsystem & Device Management
- Synchronous vs asynchronous I/O
- DMA (direct memory access)
- Interrupts & polling
- I/O buffering & caching

### 9. Kernel vs User Space
- System calls & context switches
- Privilege levels (ring 0, ring 3)
- System call overhead
- Memory protection

### 10. Performance Tuning & Profiling
- CPU profiling (flame graphs)
- Memory profiling (heap, RSS)
- I/O monitoring (iostat, iotop)
- Bottleneck identification

---

Each topic covers: fundamentals, production patterns, failure modes, debugging, code examples, monitoring, and optimization strategies.

**Prerequisites:** System Design Foundations (scalability, latency, throughput, availability).
