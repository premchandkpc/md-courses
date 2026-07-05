# 16-Distributed-Locks

Distributed locks coordinate access to shared resources across multiple services or instances. Unlike database row locks, distributed locks must operate over a network, handle partial failures, and manage lease expiration — making them significantly more complex.

## Overview
- A distributed lock ensures that only one process (across all services) holds the lock at a time. The lock is acquired by writing to a shared store (Redis, ZooKeeper, etcd, database) and released explicitly or via lease expiry.
- Distributed locks are used to protect critical sections that span service boundaries: running a cron job on only one instance, serializing access to a shared resource, or ensuring only one saga coordinator handles a specific workflow.
- The fundamental challenge is distinguishing a crashed holder from a slow holder — both appear as unresponsive. Leases (TTL-based expiry) address this but introduce the "split brain" risk if the lease expires while the holder is still active.

## Key Characteristics
- **Lease-Based Locks**: Locks have a TTL. The holder must periodically refresh (heartbeat) to extend the lease. If the holder crashes or becomes unreachable, the lease expires and another process can acquire the lock.
- **Split Brain Problem**: If the holder's lease expires due to a network delay, a second process may acquire the lock while the first still believes it holds it. Both processes may then operate on the shared resource concurrently.
- **Redis Redlock**: A distributed lock algorithm by Redis creator Salvatore Sanfilippo. It acquires the lock from a majority of Redis nodes (typically 5) to reduce the split brain risk. It is controversial — some experts argue Redlock cannot guarantee safety under all failure scenarios.
- **ZooKeeper Locks**: ZooKeeper uses sequential ephemeral znodes for locking. Since ZooKeeper provides linearizable consistency, its lock is considered safer than Redis-based locks, but at the cost of lower throughput and higher latency.
- **Fencing Tokens**: A monotonically increasing token issued to each lock holder. The resource (e.g., a database write) includes the token, and the resource rejects any operation with a stale token. This eliminates the split brain problem.

## Why It Matters
Distributed locks are necessary when microservices need to coordinate access to shared resources, but they are frequently overused and misused. Many problems that seem to require distributed locks can be solved with optimistic locking, idempotency, or leader election (where only one process acts but others can take over on failure). When distributed locks are truly needed, the choice of implementation (Redis, ZooKeeper, etcd, database) depends on the safety-latency tradeoff: Redis for speed with weaker guarantees, ZooKeeper/etcd for safety with lower performance.

## Related Concepts
- [14-Optimistic-Locking](14-Optimistic-Locking.md) — Pessimistic locking across service boundaries.
- [15-Pessimistic-Locking](15-Pessimistic-Locking.md) — Distributed locks are a form of pessimistic locking.
- [11-Data-Consistency](11-Data-Consistency.md) — The consistency guarantees of the lock store determine lock safety.

---

## Mental Model
A distributed lock is like a shared bathroom pass in a summer camp. The pass (lock) hangs on a hook. To use the bathroom, you take the pass — no one else can enter while you hold it. You have 5 minutes (lease). If you take longer, a counselor may assume you're done and give the pass to someone else — leading to two kids in the same bathroom (split brain). A fencing token would be like giving each kid a unique badge number; the bathroom door rejects anyone whose number is smaller than the current occupant's.
