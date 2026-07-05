# 12-Consistency

The guarantees a data store provides about when a write becomes visible to subsequent reads. Consistency models sit on a spectrum from strong (linearizability) to eventual (no guarantees), with several practical intermediate points.

## Overview
Consistency defines the contract between the application and the data store regarding data freshness. Strong consistency (linearizability) ensures that once a write completes, all subsequent reads across all nodes return the value of that write — as if there were a single, globally ordered copy of the data. This requires coordination (Paxos, Raft, synchronous replication) and adds latency. Eventual consistency guarantees that if no new writes are made, all replicas will converge to the same value — but reads may return stale data for an unbounded period. Causal consistency (a middle ground) guarantees that causally related operations (I replied to your post → you see my reply after seeing your post) are seen in the correct order by all nodes, while concurrent operations may be reordered.

## Key Characteristics
- **Strong consistency**: Clients always see the latest write. Requires consensus. Used for financial transactions, inventory, leader election. Performance cost increases with geographical distribution.
- **Eventual consistency**: Replicas converge over time. Reads may return stale data. Simple, fast, highly available. Used for social feeds, analytics, content delivery.
- **Causal consistency**: Preserves causal order (happens-before relationships). Concurrent operations can be reordered. Provides a useful sweet spot: stronger than eventual but cheaper than strong.
- **Read-after-write consistency**: A user always sees their own writes. Also called read-your-writes consistency. Critical for user-facing applications — a user who posts a comment expects to see it immediately.
- **Monotonic reads**: After a user reads a value, subsequent reads will never return a version older than what they already saw. Prevents confusing "time travel" effects.
- **Consistency level tradeoffs**: Systems like Cassandra and DynamoDB allow per-request consistency choice. A read with ALL/strong consistency goes to all replicas; ONE/eventual reads from the nearest replica.

## Why It Matters
Consistency choices directly affect user experience and system complexity. A social media feed using eventual consistency is acceptable — stale posts aren't critical. A payment service with eventual consistency could cause double-spending. Microservices architects must understand the guarantees their data stores offer and choose the weakest acceptable model for each operation, because weaker consistency means better performance, higher availability, and simpler operations.

## Related Concepts
- [CAP Theorem](10-CAP-Theorem.md) — Consistency vs. availability is the fundamental tradeoff
- [PACELC](11-PACELC.md) — Extends the tradeoff to latency vs. consistency during normal operation
- [Replication](05-Replication.md) — Replication lag is the primary source of inconsistency in distributed systems

---

## Mental Model
A classroom whiteboard is visible to all students. Strong consistency: the teacher erases and rewrites every change before anyone looks up — everyone sees the same thing. Eventual consistency: students see slightly different versions depending on when they last looked; eventually the board is erased and rewritten, and everyone agrees. Causal consistency: if the teacher writes "Step 1: Mix flour," then "Step 2: Add eggs," no student sees "Add eggs" without first seeing "Mix flour."
