---
title: Quick Reference Cheat Sheets
topic: cheat-sheets
difficulty: intermediate
time: 30m
---

# Quick Reference Cheat Sheets

Fast lookup guides for essential tools, commands, and numbers. Each sheet is self-contained — copy-paste ready.

---

## Programming Languages

| Sheet | Size | Topics |
|-------|------|--------|
| **[Git Commands](git-commands.md)** | 13KB | init, clone, commit, push, branch, merge, rebase, stash, log |
| **[Go Profiling](go-profiling.md)** | 11KB | pprof, CPU/memory/goroutine profiling, flame graphs, benchmarks |
| **[JVM Tuning](jvm-tuning.md)** | 9KB | heap, GC flags, young gen, old gen, G1GC, CMS tuning |

---

## Infrastructure & DevOps

| Sheet | Size | Topics |
|-------|------|--------|
| **[Kubectl Commands](kubectl-commands.md)** | 18KB | get, apply, logs, exec, scale, rollout, port-forward, debug |
| **[Docker Commands](docker-commands.md)** | 12KB | build, run, ps, rm, volume, network, compose, registry |
| **[PostgreSQL Tuning](postgresql-tuning.md)** | 12KB | shared_buffers, autovacuum, indexing (B+tree, GIN, BRIN), connection pooling |
| **[Linux Debugging](linux-debugging.md)** | 9KB | strace, ltrace, perf, gdb, valgrind, lsof, netstat, tcpdump |
| **[Networking Commands](networking-commands.md)** | 12KB | ip, netstat, ss, tcpdump, iptables, iperf, dig, nslookup, traceroute |

---

## Data & Analysis

| Sheet | Size | Topics |
|-------|------|--------|
| **[SQL Queries](sql-queries.md)** | 40KB | joins, aggregation, window functions, CTEs, transactions, locking |
| **[Big-O Complexity](big-o-complexity.md)** | 11KB | algorithm complexity, data structures (array, hash, tree, heap, graph) |

---

## Numbers & Performance

| Sheet | Size | Topics |
|-------|------|--------|
| **[Latency Numbers](latency-numbers.md)** | 18KB | CPU, memory, disk, network latencies; rule of thumb: L1→L3→RAM→SSD→HDD→network |
| **[System Design Numbers](system-design-numbers.md)** | 7KB | QPS, RPS, storage capacity, bandwidth, failure rates |

---

## Usage

**In markdown**: Link directly to specific sections.
```markdown
[See PostgreSQL tuning](../cheat-sheets/postgresql-tuning.md#autovacuum)
```

**In browser**: Search all sheets at once using the sidebar or ⌘K.

**Print-friendly**: Each sheet is single-column, code-light. Optimal for hardcopy reference.

---

## Coverage Map

- ✅ **Language internals**: Go, JVM
- ✅ **DevOps tools**: kubectl, Docker, PostgreSQL, Linux
- ✅ **Networking**: protocols, debugging, performance
- ✅ **Data structures**: Big-O, SQL, algorithms
- ✅ **Performance**: latency, system design numbers

Missing? Suggest additions at the repo issues.

---

**Related**: See domain READMEs for deep dives (e.g., [PostgreSQL internals](/08-databases/README.md), [Kubernetes](/07-kubernetes/README.md), [Networking](/11-networking/README.md)).
