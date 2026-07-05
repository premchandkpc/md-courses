# Event-Driven

Event-Driven architecture is a communication model where services exchange information by publishing and consuming events rather than making direct synchronous calls. Producers emit events without knowing which consumers will react.

## Overview
In an event-driven microservices architecture, services are decoupled in both space and time. A service publishes an event (e.g., `OrderPlaced`, `PaymentCaptured`) to a message broker or event stream. Other services subscribe to relevant events and react asynchronously. This contrasts with request-driven architectures where a service directly calls another service's API and waits for a response. Event-driven systems are inherently more resilient, scalable, and adaptable to change — new consumers can subscribe without modifying the producer.

## Key Characteristics
- **Loose Coupling**: Producers and consumers have zero direct dependencies; they only share event schemas.
- **Asynchronous Flow**: Producers don't wait for consumer processing; they publish and continue immediately.
- **Fan-Out**: A single event can trigger reactions in multiple unrelated services (billing, shipping, analytics).
- **Event Durability**: Events are persisted in the broker, allowing consumers to replay or catch up after downtime.
- **Schema Evolution**: Events follow versioned schemas (Avro, Protobuf) enabling producer-consumer compatibility.
- **Eventually Consistent**: Systems converge to consistency over time rather than maintaining strict transactional boundaries.

## Why It Matters
Request-driven microservices often devolve into distributed monoliths — every service call is synchronous, creating chains of dependencies that amplify latency and failures. Event-driven communication breaks these chains. A slow consumer doesn't block the producer. New services can be added without touching existing code. Event streams also serve as an audit log — every state change is recorded as an immutable event.

## Related Concepts
- [Observer](08-Observer.md) — the design pattern that underlies event-driven architectures.
- [Workflow](11-Workflow.md) — often event-driven; each completed step emits an event that triggers the next step.
- [Pipeline](10-Pipeline.md) — event streams can feed into processing pipelines for transformation and enrichment.

---

## Mental Model
A radio station. The station broadcasts music (events) on a frequency. Anyone with a radio tuned to that frequency can listen. The station doesn't know how many listeners there are, who they are, or whether they're even listening. A new listener can tune in at any time (start consuming events). If a listener's radio breaks (consumer crashes), they miss some songs but can't affect the broadcast. This is event-driven communication: one producer, many potential consumers, no direct coupling.
