# 15-Pessimistic-Locking

Pessimistic locking prevents concurrent access to a resource by acquiring an exclusive lock before any read or write operation. It assumes conflicts are likely and pays the cost of locking upfront to guarantee serial access.

## Overview
- The lock is acquired at the start of the transaction and held until commit or rollback. Other transactions that need the same resource block or fail.
- In databases, this is typically implemented with `SELECT ... FOR UPDATE`, which locks the selected rows against concurrent writes and `SELECT ... FOR UPDATE` from other transactions.
- Pessimistic locking can also be implemented at the application level using mutexes (distributed or local) to protect critical sections.
- The cost is reduced concurrency due to blocking, plus the risk of deadlocks if locks are acquired in inconsistent order.

## Key Characteristics
- **Prevents Conflicts**: Since access is serialized, there are no version conflicts, lost updates, or write skew — the transaction either gets the lock and proceeds, or waits.
- **Blocking**: Contention causes queuing. Under load, lock wait times increase, potentially cascading to timeouts and reduced throughput.
- **Deadlock Risk**: If two transactions acquire locks in different order, each may wait for the other — creating a deadlock. Databases detect deadlocks and abort one transaction (the victim), which must retry.
- **Lock Escalation**: Row-level locks can escalate to page or table locks, causing unintended contention. Monitoring lock granularity is important in production.
- **Best for High Contention**: When conflicts are frequent (booking systems, inventory counters, financial ledgers), the retry cost of optimistic locking exceeds the blocking cost of pessimistic locking.

## Why It Matters
Pessimistic locking is the right choice when the cost of a conflict is high or conflicts are inevitable. It simplifies application logic because the developer doesn't need to handle version conflicts and retries. However, it requires careful tuning: lock timeouts, deadlock detection, lock granularity, and transaction duration all affect system throughput. In distributed systems, pessimistic locking via `SELECT FOR UPDATE` works within a single database but must be replaced with distributed locks across service boundaries.

## Related Concepts
- [14-Optimistic-Locking](14-Optimistic-Locking.md) — The optimistic alternative with lower blocking but higher retry cost under contention.
- [16-Distributed-Locks](16-Distributed-Locks.md) — Pessimistic locking across service boundaries.
- [10-MVCC](10-MVCC.md) — MVCC provides snapshot isolation; pessimistic locking provides serial access.

---

## Mental Model
Pessimistic locking is like a single-user bathroom in a coffee shop. The door locks from the inside (exclusive access). When occupied, everyone else waits in line (blocking). If someone forgets to unlock the door after leaving (no release), a manager must intervene (deadlock detection). For a busy shop, a multi-user bathroom (optimistic) would reduce waiting, but occasionally two people show up at the same door.
