# 12-Choosing-Communication

Choosing the right communication pattern and protocol is a foundational decision in microservices architecture. The wrong choice leads to unnecessary complexity, performance bottlenecks, or tight coupling.

## Overview

There is no single best communication pattern. Each has tradeoffs across latency, coupling, resilience, consistency, complexity, and operational overhead. The right choice depends on the specific use case: whether the caller needs a response, whether real-time delivery is required, what throughput is expected, and what consistency guarantees the business needs.

## Key Characteristics

- **Sync vs Async Decision**: If the caller needs an immediate response to proceed → synchronous (REST, gRPC). If the work can happen later, can fail independently, or needs to fan out to multiple consumers → asynchronous (Kafka, RabbitMQ, NATS).
- **Protocol Selection for Sync**: REST for external APIs, browser clients, and simple CRUD. gRPC for internal service-to-service where performance and strong typing matter. GraphQL as a BFF for frontend flexibility.
- **Protocol Selection for Async**: Kafka for high-throughput event streaming with replayability. RabbitMQ for complex routing and work queues. NATS for lightweight, low-latency messaging. Redis PubSub for ephemeral, fire-and-forget notifications.
- **Latency Requirements**: Sub-millisecond → NATS or Redis PubSub. Low latency → gRPC. Moderate latency → REST, Kafka. High latency tolerant → message queues with buffering.
- **Consistency Requirements**: Strong consistency → synchronous (use sagas for multi-service transactions). Eventual consistency → asynchronous with outbox pattern. Exactly-once semantics → Kafka with idempotent producers.

## Why It Matters

A systematic decision framework prevents the common pitfall of using one pattern everywhere. The typical mistake is defaulting to REST for everything (creating chatty, tightly coupled systems) or defaulting to Kafka for everything (adding complexity where simple request-response would suffice). A heterogeneous approach — picking the right tool for each job — yields systems that are simpler, more performant, and easier to evolve.

## Decision Matrix

| Use Case | Pattern | Protocol |
|---|---|---|
| Query data, need immediate answer | Sync | REST or gRPC |
| Command, fire-and-forget | Async | Message broker |
| Event broadcasting (1:N) | Async | Pub/sub (Kafka, NATS) |
| Real-time push to UI | Sync (persistent) | WebSocket or SSE |
| Frontend data fetching | Sync | GraphQL (BFF) |
| High-throughput stream | Async | Kafka |
| Complex routing to workers | Async | RabbitMQ |

## Related Concepts

- [01-Synchronous-vs-Asynchronous](01-Synchronous-vs-Asynchronous.md) — the fundamental tradeoff
- [02-REST](02-REST.md) — most common sync protocol
- [03-gRPC](03-gRPC.md) — high-performance sync alternative
- [07-Message-Brokers](07-Message-Brokers.md) — broker selection criteria
- [08-Kafka](08-Kafka.md) — event streaming at scale

---

## Mental Model

Choosing a communication protocol is like choosing a vehicle for a trip. A bicycle (NATS/Redis PubSub) is great for quick trips around the neighborhood. A sedan (REST/gRPC) handles most daily commutes. A cargo truck (Kafka) moves bulk goods across the country. A delivery van (RabbitMQ) is perfect for routing packages through a complex distribution network. You wouldn't use a cargo truck to get groceries, and you wouldn't use a bicycle to move freight.
