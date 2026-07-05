# 02-Saga-Pattern

A saga is a sequence of local transactions where each step publishes an event or message that triggers the next step. If a step fails, the saga runs compensating transactions to undo prior steps — providing data consistency without distributed transactions.

## Overview
- Sagas break a multi-service business transaction into a series of local ACID transactions, each executed within a single service.
- Each step publishes an event (or sends a message) that triggers the subsequent step. No cross-service locking or two-phase commit is needed.
- When a step fails, the saga executes compensation logic — service-specific operations that semantically undo the effect of each completed step.
- Two execution models exist: choreography (event-driven, decentralized) and orchestration (central coordinator).

## Key Characteristics
- **Compensating Transactions**: Each step must define a compensating action that can roll back its effect. Compensation is semantic (e.g., "cancel order" refunds inventory), not the DB rollback of ACID.
- **Eventually Consistent**: Sagas provide eventual consistency. There is a window where partial updates are visible to other services — the system must tolerate this.
- **Failure Handling**: Three strategies — forward recovery (retry), backward recovery (compensate), or mixed. The choice depends on error type and business requirements.
- **No Isolation**: Sagas lack the isolation (I in ACID) of distributed transactions. Concurrent sagas may see intermediate states unless compensating or semantic locking is added.

## Why It Matters
Sagas are the most widely adopted alternative to distributed transactions in microservices. They preserve service autonomy (each service owns its data and transaction boundaries) while guaranteeing eventual consistency. Major patterns like order-fulfillment, booking systems, and multi-step workflows rely on sagas. The tradeoff is added complexity: developers must write, test, and monitor compensating logic.

## Related Concepts
- [01-Distributed-Transactions](01-Distributed-Transactions.md) — Sagas replace distributed transactions.
- [03-Choreography](03-Choreography.md) — Event-driven saga execution model.
- [04-Orchestration](04-Orchestration.md) — Coordinator-driven saga execution model.
- [11-Data-Consistency](11-Data-Consistency.md) — Saga provides eventual consistency.

---

## Mental Model
A saga is like a multi-stop road trip where each leg is independently booked. If the third hotel is unavailable, you don't undo everything magically — you call the first two hotels to cancel (compensation). The trip is eventually consistent: during the cancellation calls, your credit card still shows charges for all three hotels.
