# 05-Replication

Copying data from one node to others so that multiple copies exist across the system. Replication provides fault tolerance, high availability, and often read scalability. It is fundamental to distributed databases, caches, and storage systems.

## Overview
Replication maintains identical copies of data on separate nodes. If one node fails, another can serve requests without data loss. There are three main strategies. Leader-based replication (single-leader) designates one node as the writable source; followers replicate changes asynchronously or synchronously. Multi-leader replication allows writes on multiple nodes, requiring conflict resolution (last-write-wins, CRDTs, application-level merge). Quorum-based replication (used in Cassandra, DynamoDB) requires a configurable number of nodes (W + R > N) to acknowledge reads and writes for strong consistency.

## Key Characteristics
- **Fault tolerance**: N replicas tolerate N–1 node failures. Combined with automatic failover, this achieves high availability targets (99.99%+).
- **Read scaling**: Replicas can serve read traffic, offloading the leader. Applications distinguish read replicas from the write master.
- **Replication lag**: Asynchronous replication introduces a window where replicas are stale. This causes read-after-write inconsistencies unless the application explicitly reads from the leader.
- **Conflict risk**: Multi-leader and leaderless systems must handle concurrent writes to the same data. Conflict resolution adds complexity.
- **Network cost**: Every write generates N–1 network round trips. In geo-distributed setups, cross-region replication latency impacts write performance.

## Why It Matters
Replication is non-negotiable in production microservices. A database without replication is a single point of failure. Most services configure at least a primary and one replica, often across availability zones. Combined with automatic leader election (e.g., Raft, Paxos), replication becomes the foundation of self-healing infrastructure.

## Related Concepts
- [Sharding](03-Sharding.md) — Replication protects each shard against data loss
- [CAP Theorem](10-CAP-Theorem.md) — Replication introduces the consistency vs. availability tradeoff
- [Consistency](12-Consistency.md) — Defines the guarantees applications get when reading from replicas

---

## Mental Model
A company's financial records are photocopied and stored in three different safes in three different buildings. If a fire destroys one building, the records survive. The downside: when a transaction is recorded, it takes time for the photocopy machine to reach the other buildings (replication lag).
