# 10-CAP-Theorem

A theorem stating that a distributed data store can only guarantee two of three properties simultaneously: Consistency (C), Availability (A), and Partition Tolerance (P). In practice, partition tolerance is non-negotiable in distributed systems, so the real choice is between CP and AP.

## Overview
Formalized by Eric Brewer in 2000, CAP describes the tradeoffs inherent in distributed systems. Consistency means every read receives the most recent write or an error — all nodes see the same data at the same time. Availability means every request receives a non-error response, without guarantee it contains the most recent write. Partition tolerance means the system continues operating despite network failures that cause nodes to lose communication with each other. In a distributed system (especially microservices), network partitions are inevitable — the system must tolerate them, making P mandatory. The practical tradeoff becomes: during a partition, do you sacrifice consistency (AP — remain available with possibly stale data) or availability (CP — remain consistent by refusing some requests)?

## Key Characteristics
- **P is not optional in distributed systems**: Network failures happen. Any system that runs across multiple nodes must tolerate partitions.
- **CP systems (Choose consistency)**: During a partition, CP systems block writes or shut down replicas that can't coordinate. Examples: traditional RDBMS with synchronous replication, ZooKeeper, etcd (Raft consensus).
- **AP systems (Choose availability)**: During a partition, AP systems accept writes and serve reads from any replica, accepting that data may diverge. Examples: Cassandra, DynamoDB, CouchDB.
- **CA is a myth in distributed systems**: A "CA" system only works if there are no partitions — meaning it's not truly distributed. Single-node databases are CA only because they aren't partitioned.
- **Tradeoff is per-operation, not system-wide**: Modern systems let you tune the tradeoff per operation (e.g., DynamoDB's eventual vs. strongly consistent reads, Cassandra's tunable consistency levels).

## Why It Matters
Every microservice that uses a distributed data store — and most do — must understand CAP. Choosing between CP and AP determines how the service behaves during real-world failures. Payment services and inventory systems typically favor CP (better to reject a charge than double-charge). Social feeds and analytics favor AP (better to show slightly stale data than show nothing).

## Related Concepts
- [PACELC](11-PACELC.md) — An extension of CAP that accounts for latency tradeoffs even when the system isn't partitioned
- [Consistency](12-Consistency.md) — Strong, eventual, and causal consistency models flow from CAP choices
- [Replication](05-Replication.md) — The mechanism that creates the consistency-vs-availability tension

---

## Mental Model
Two accountants maintain the same ledger. If the phone line between them goes down (partition), they face a choice: continue updating their local copy (AP — available, but ledgers may diverge) or stop accepting new entries until the phone is restored (CP — consistent, but unavailable). You can't have both.
