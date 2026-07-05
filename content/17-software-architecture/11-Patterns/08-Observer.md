# Observer

The Observer pattern establishes a one-to-many dependency: when one service publishes an event, multiple consumers are notified and react independently. This is the foundational pattern for event-driven microservices.

## Overview
In the Observer pattern, a subject (publisher) maintains a list of observers (subscribers) and automatically notifies them of state changes. In microservices, this maps directly to event publishing and consuming — services emit events (OrderPlaced, PaymentReceived) without knowing who listens. Message brokers like Kafka, RabbitMQ, or NATS implement the Observer pattern at scale, providing durability, partitioning, and guaranteed delivery.

## Key Characteristics
- **Loose Coupling**: Publishers and subscribers have no direct knowledge of each other; they interact only through events.
- **Broadcast Semantics**: A single event can trigger reactions in multiple independent subscribers.
- **Dynamic Subscription**: Subscribers can register or unregister at runtime without affecting the publisher.
- **Pull vs Push**: Observers can be notified (push) or periodically check for new events (pull).
- **Event Schema**: Events follow a defined schema (Avro, Protobuf, JSON Schema) enabling evolution and validation.

## Why It Matters
Synchronous request-response chains create temporal coupling — if one service is slow, the whole chain is slow. Observer-based communication decouples services in time (subscribers can process when ready) and space (subscribers don't need the publisher's address). This enables independent scaling, asynchronous processing, and resilient architectures where the failure of one subscriber doesn't affect others.

## Related Concepts
- [Event-Driven](12-Event-Driven.md) — the broader architectural style built on Observer principles.
- [Workflow](11-Workflow.md) — uses events to trigger the next step in a long-running process.
- [Chain of Responsibility](09-Chain-of-Responsibility.md) — passes a request through handlers sequentially; Observer fans out to all subscribers concurrently.

---

## Mental Model
A YouTube channel subscription. You subscribe to a channel (register as observer). When the creator uploads a video (event), all subscribers are notified simultaneously. Each subscriber reacts independently: one watches immediately, another saves for later, a third ignores it. The creator doesn't know or care who is subscribed — they just publish content to their channel.
