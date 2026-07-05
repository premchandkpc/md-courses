# 10-MVCC

Multi-Version Concurrency Control (MVCC) is a database concurrency method where each write creates a new version of a data row rather than overwriting the existing one. Readers see a consistent snapshot as of the time their transaction started, eliminating the need for read locks.

## Overview
- MVCC is the standard concurrency model in modern databases: PostgreSQL, MySQL (InnoDB), Oracle, CockroachDB, and others.
- When a transaction writes a row, the database keeps the old version accessible to concurrent readers that started before the write.
- Each transaction sees a snapshot of the database at its start time (snapshot isolation). Writes from other transactions are invisible until the writing transaction commits.
- MVCC eliminates the conflict between readers and writers: reads never block writes, and writes never block reads.

## Key Characteristics
- **Snapshot Isolation**: Each transaction operates on a consistent snapshot of the database as of the transaction's start. Dirty reads, non-repeatable reads, and phantom reads are prevented without locks.
- **Write Skew Anomaly**: MVCC with snapshot isolation is vulnerable to write skew — two concurrent transactions read overlapping data and make independent decisions that are inconsistent when both commit. Example: two doctors both check "on-call count > 1" and both go off-call, leaving zero.
- **Version Storage**: Old row versions must be stored somewhere. PostgreSQL stores them in the same table (dead tuples, cleaned by VACUUM). MySQL/InnoDB stores them in the undo log.
- **Visibility Rules**: Each row version carries a creation and expiration transaction ID. The visibility check determines whether a version is visible to the current transaction.
- **Serializable Snapshot Isolation (SSI)**: Some databases (PostgreSQL, CockroachDB) offer SSI — true serializability using MVCC plus conflict detection for write skew.

## Why It Matters
MVCC is the backbone of isolation in modern databases. It enables high concurrency without read-write lock contention. In microservices, where multiple services or instances access the same database, MVCC's lock-free reads are critical for performance. Understanding MVCC helps diagnose anomalies (write skew, phantom reads) and choose the right isolation level for each operation.

## Related Concepts
- [14-Optimistic-Locking](14-Optimistic-Locking.md) — Often implemented on top of MVCC to prevent write skew.
- [15-Pessimistic-Locking](15-Pessimistic-Locking.md) — An alternative concurrency model that uses explicit locks instead of versions.
- [11-Data-Consistency](11-Data-Consistency.md) — Isolation levels determine consistency guarantees.

---

## Mental Model
MVCC is like a version control system (Git) for database rows. When you edit a file, Git doesn't overwrite the original — it saves a new version. Your colleague sees the original until you commit your changes. If you both edit the same file, Git detects the conflict at merge time (write skew), forcing you to reconcile.
