# 01-Distributed-Transactions

A distributed transaction spans multiple services, databases, or nodes, requiring coordination to maintain atomicity and consistency. Traditional ACID transactions assume a single database — they break when operations must commit across independent services.

## Overview
- Distributed transactions coordinate multiple participants (services, databases) to reach a single atomic outcome: all commit or all abort.
- ACID guarantees (Atomicity, Consistency, Isolation, Durability) assume a single transaction manager controlling one database. In microservices, each service owns its own data store — no single DB can enforce cross-service consistency.
- Two-Phase Commit (2PC) is the classic protocol but introduces blocking, single-point-of-failure, and scalability bottlenecks.

## Key Characteristics
- **Atomic Commit Problem**: All participants must agree on the outcome. A single "no" vote forces abort, yet partial failures can leave participants uncertain of the decision.
- **Blocking Protocol**: In 2PC, the coordinator and participants hold locks during the prepare phase. If the coordinator crashes after prepare, participants block until recovery — a severe availability risk.
- **Coordinator Single Point of Failure**: The transaction coordinator must be highly available and durable; if lost, in-doubt transactions may linger indefinitely.
- **Performance Overhead**: 2PC requires multiple round trips (prepare → vote → commit/abort), increasing latency proportionally to the number of participants.

## Why It Matters
Distributed transactions are the default mental model from monolithic databases, but they do not scale in microservices. Most teams abandon cross-service ACID in favor of eventual consistency, sagas, and compensating actions. When strong consistency across services is truly required (financial ledgers, inventory), 2PC remains an option but demands careful infrastructure — XA transactions, distributed coordinators, and idempotent participants.

## Related Concepts
- [02-Saga-Pattern](02-Saga-Pattern.md) — Sagas replace distributed transactions with local transactions + compensation.
- [11-Data-Consistency](11-Data-Consistency.md) — The CAP theorem tradeoff between consistency and availability.
- [16-Distributed-Locks](16-Distributed-Locks.md) — Lock coordination across services, needed in some transaction protocols.

---

## Mental Model
Think of 2PC like a group camping trip where everyone must agree on the destination. Phase 1: the leader asks "can we all go to Lake Tahoe?" and everyone checks their schedule. Phase 2: if everyone said yes, the leader says "confirmed — Lake Tahoe." But if the leader's phone dies after phase 1, some people drive to Tahoe while others wait at home, not knowing the final decision.
