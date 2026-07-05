# 08-Event-Sourcing

Event Sourcing persists state changes as an append-only log of events, rather than storing the current state directly. The current state is derived by replaying all events in order. This provides a complete audit trail, temporal querying, and a natural event stream for microservices integration.

## Overview
- Instead of updating a record in place (e.g., `UPDATE orders SET status = 'shipped'`), Event Sourcing appends an event: `OrderShipped { orderId, timestamp }`.
- The current state is the aggregate (fold/reduce) of all past events. To determine if an order is shipped, replay all events for that order and check the latest status.
- The event store is the single source of truth. Current state is a derived artifact, which can be cached, indexed, or projected into read models.
- Events are immutable and never deleted. New events are appended to correct mistakes (compensating events).

## Key Characteristics
- **Complete Audit Trail**: Every state change is recorded with full context — who, what, when, and why. This is invaluable for compliance (finance, healthcare, regulated industries).
- **Temporal Queries**: The system can reconstruct state as of any point in time by replaying events up to that moment. This enables debugging, analysis, and point-in-time reports.
- **Event-Driven Native**: The event stream is a first-class integration point. Other services can subscribe to specific event types without additional publishing infrastructure.
- **Storage Growth**: The event log grows indefinitely. Strategies include snapshotting (periodically saving the aggregate state to avoid replaying all events from the beginning) and event archiving.
- **Event Schema Evolution**: Events are immutable but their schemas change over time. Versioning strategies (upcasting, versioned event types) are required.

## Why It Matters
Event Sourcing is powerful when you need complete history, auditability, and temporal reasoning. In microservices, it naturally produces the events needed for integration, CQRS read models, and analytics. The main downside is operational complexity: event stores, schema versioning, and projection management require mature tooling (EventStoreDB, Kafka with Schema Registry, Axon Framework).

## Related Concepts
- [07-CQRS](07-CQRS.md) — Event Sourcing pairs naturally with CQRS (events build read models).
- [09-CDC](09-CDC.md) — CDC captures database changes as events, similar to Event Sourcing but from existing databases.
- [13-Deduplication](13-Deduplication.md) — Events must be idempotent: replaying them produces the same final state.

---

## Mental Model
Event Sourcing is like a financial ledger, not a whiteboard. A ledger never erases an entry — you add a new line to correct a mistake ("voided transaction + re-credit"). To know your current balance, you add up all entries from the beginning. If you want to know what your balance was on March 15th, you only sum entries up to that date.
