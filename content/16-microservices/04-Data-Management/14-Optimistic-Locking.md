# 14-Optimistic-Locking

Optimistic locking assumes that conflicts between concurrent transactions are rare. Instead of locking resources upfront, the transaction reads a version field, performs its work, and checks the version before writing. If the version has changed, the write fails and the transaction retries.

## Overview
- Each record carries a version number (or timestamp) that is incremented on every update.
- A transaction reads the record, captures the version, performs business logic, and writes back: `UPDATE ... SET version = version + 1 WHERE id = ? AND version = old_version`.
- If another transaction updated the same record concurrently, the version won't match — the update affects zero rows. The application detects this and retries the entire transaction.
- No locks are held during the transaction, so there is no blocking or deadlock risk.

## Key Characteristics
- **No Lock Overhead**: Readers and writers proceed without acquiring locks. This maximizes concurrency in read-heavy workloads.
- **Retry Required**: When a conflict is detected (0 rows updated), the application must retry from the beginning. Under high contention, retries can be frequent and expensive.
- **Best for Low Contention**: Optimistic locking performs well when conflicts are rare (<5% of transactions). As contention rises, retry costs (re-reading data, re-computing logic) mount quickly.
- **Version Field**: Typically an integer or UUID. Timestamps can cause issues with clock skew in distributed systems — monotonic counters are preferred.
- **Compare-and-Swap (CAS)**: The core of optimistic locking is the CAS pattern: read current value, compute new value, atomically swap if unchanged. Databases implement this with atomic UPDATE with WHERE clause; Redis has WATCH/MULTI/EXEC.

## Why It Matters
Optimistic locking is a fundamental tool for microservices that share database records. It avoids the availability and scalability problems of pessimistic locking while still preventing lost updates. It pairs naturally with MVCC databases and is the default choice for REST API concurrency control (ETags, If-Match headers). The critical design factor is choosing the right granularity — per-row, per-aggregate, or per-document.

## Related Concepts
- [10-MVCC](10-MVCC.md) — MVCC provides snapshot isolation; optimistic locking adds conflict detection.
- [15-Pessimistic-Locking](15-Pessimistic-Locking.md) — The pessimistic alternative for high-contention scenarios.
- [16-Distributed-Locks](16-Distributed-Locks.md) — Optimistic locking at the application level across services.

---

## Mental Model
Optimistic locking is like editing a shared Google Doc. You edit freely without locking anyone out (no upfront lock). When you save, if someone else edited the same paragraph, Google shows a conflict (version mismatch) and you must merge. If nobody else touched it, your save succeeds instantly. Most of the time, this works because concurrent edits on the same paragraph are rare.
