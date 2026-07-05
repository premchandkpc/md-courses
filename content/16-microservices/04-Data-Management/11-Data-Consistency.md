# 11-Data-Consistency

Data consistency in microservices describes how quickly and predictably a write to one service propagates to other services that read or depend on that data. The spectrum ranges from strong consistency (immediate, ACID) to eventual consistency (convergent over time).

## Overview
- In a monolithic system with a single database, strong consistency is the default: a write is immediately visible to all subsequent reads within the same transaction scope.
- In microservices, data is distributed across independently owned databases. Cross-service reads cannot use a single transaction, so consistency loosens.
- The CAP theorem states that a distributed system can guarantee at most two of: Consistency, Availability, Partition Tolerance. Network partitions (P) are inevitable, so the choice is between CP (sacrifice availability) and AP (sacrifice consistency).
- PACELC extends CAP: even without partitions (P), there is a tradeoff between latency (L) and consistency (C).

## Key Characteristics
- **Strong Consistency**: All reads return the most recent write. Requires coordination (quorum, distributed transactions, consensus). High latency, low availability during partitions.
- **Eventual Consistency**: Given enough time without updates, all replicas converge to the same value. Low latency, high availability. Stale reads are possible.
- **Read-Your-Writes Consistency**: A user always sees their own writes, even if other users may see stale data. Achieved with session stickiness or version vectors.
- **Monotonic Reads**: Once a user reads a value, subsequent reads never return an older value. Prevents "time travel" anomalies.
- **Causal Consistency**: Operations that are causally related (A happens-before B) are seen in order by all processes. Concurrent operations can be seen in any order.

## Why It Matters
Choosing the right consistency model is one of the most consequential decisions in microservices architecture. Strong consistency simplifies application logic but hurts availability and performance. Eventual consistency enables independent service evolution and high throughput but requires careful handling of stale reads, conflict resolution, and user-facing implications. Most production systems use a mix: strong consistency within a service's boundary, eventual consistency across services.

## Related Concepts
- [01-Distributed-Transactions](01-Distributed-Transactions.md) — Mechanism for strong consistency across services (costly).
- [02-Saga-Pattern](02-Saga-Pattern.md) — Provides eventual consistency with compensating transactions.
- [10-MVCC](10-MVCC.md) — Implementation of snapshot isolation for consistency within a database.
- [12-Idempotency](12-Idempotency.md) — Critical for achieving consistency under retry.

---

## Mental Model
Data consistency is like a shared group calendar. Strong consistency: when Alice adds a meeting, Bob sees it instantly or the system refuses to show the calendar until it syncs (CP). Eventual consistency: Alice adds a meeting, and Bob sees it within a few seconds — but for a brief moment, he might schedule over it. "Read-your-writes" means Alice always sees her own meeting immediately, even if Bob hasn't yet.
