# 10-Domain-Events

A Domain Event records something significant that happened in the domain, expressed as a past-tense fact. Domain events are immutable, published asynchronously, and consumed by other parts of the system — often by other bounded contexts. They are the primary mechanism for achieving eventual consistency across aggregate and service boundaries.

## Overview
Domain events capture business occurrences: `OrderPlaced`, `PaymentReceived`, `InventoryDepleted`. They represent facts that cannot be undone (a compensating event can follow, but the original event stays). Events are published by the aggregate root after a state change and are typically stored in an event log or message broker. Consumers react independently — the publisher never knows who consumes its events.

## Key Characteristics
- **Past-Tense Naming**: Events are named after the completed fact: `OrderShipped`, `InvoicePaid`, `UserRegistered`.
- **Immutable**: Once created, domain events never change. They are historical records.
- **Asynchronous by Default**: The publisher does not wait for consumers. This decouples services and enables eventual consistency.
- **Contains Relevant Data**: An event carries the data consumers need — the aggregate ID, the changed values, and a timestamp. Not the entire aggregate state.
- **Publish Side-Effect**: Domain events are published as part of the aggregate's state change, typically collected in a list on the aggregate and dispatched after persistence.

## Why It Matters
Domain events are the foundation of event-driven microservices. They allow services to react to changes in other services without synchronous coupling. `OrderPlaced` in the Ordering service triggers `ReserveInventory` in the Inventory service, `ChargeCustomer` in the Billing service, and `ScheduleShipment` in the Shipping service — all without the Ordering service knowing about those services.

## Related Concepts
- [Aggregates](06-Aggregates.md) — aggregates publish domain events
- [Application Services](09-Application-Services.md) — dispatch events after persisting aggregates
- [Context Mapping](11-Context-Mapping.md) — events are a communication pattern between bounded contexts
- [DDD in Microservices](12-DDD-in-Microservices.md) — events enable service autonomy

---

## Mental Model
A domain event is like a newspaper headline. "City Bridge Reopens After Repairs" is an immutable fact. Readers (subscribers) react however they want: commuters change their route, news sites post updates, nearby businesses run promotions. The bridge authority doesn't call each person individually — it publishes the fact, and interested parties consume it when ready.
