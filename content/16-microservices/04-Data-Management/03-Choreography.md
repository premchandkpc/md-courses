# 03-Choreography

Choreography is a saga execution model where each service, after completing its local transaction, publishes an event that other services consume to decide their next action. There is no central coordinator — the "workflow" emerges from distributed event reactions.

## Overview
- Services communicate exclusively through events (via message broker like Kafka, RabbitMQ, or NATS).
- Each service knows what event to publish after success and what compensating action to take on failure events.
- The order of steps is implicit in the event flow, not encoded in a central state machine.
- Simple to start, but complex workflows become hard to trace and debug.

## Key Characteristics
- **Decentralized Control**: No single point of coordination. Each service independently subscribes to relevant events and reacts autonomously.
- **Loose Coupling**: Services know only about events, not about other services' APIs. Adding new steps requires only subscribing to existing events.
- **Difficult to Debug**: The control flow is distributed across all services. Following a single transaction through the event stream requires correlating events across multiple logs and topics.
- **Cyclic Dependency Risk**: Services can inadvertently create event cycles (A → B → C → A) if compensation events flow back through the same topics.
- **No Explicit Workflow**: The saga's progress is not captured in a single location — it's distributed across event topics and service subscriptions.

## Why It Matters
Choreography is ideal for simple sagas (2-4 steps) where the flow is unlikely to change. It is the most "microservices-native" approach — maximum autonomy, minimal coupling, no coordinator bottleneck. However, as the workflow grows in complexity or the number of services increases, teams often migrate to orchestration for observability and control.

## Related Concepts
- [02-Saga-Pattern](02-Saga-Pattern.md) — Choreography is one of two saga execution models.
- [04-Orchestration](04-Orchestration.md) — The centralized alternative to choreography.
- [05-Outbox-Pattern](05-Outbox-Pattern.md) — Reliable event publishing from services.

---

## Mental Model
Choreography is like a dance floor where each dancer watches others and moves accordingly — no choreographer. If dancer A spins, dancer B knows to dip, then dancer C knows to clap. It works beautifully for small groups but becomes chaos with 20 dancers who all need to coordinate an elaborate routine.
