# 10-NATS

NATS is a lightweight, high-performance messaging system designed for cloud-native applications. It offers simple pub/sub, request-reply, and queue-based messaging with minimal overhead.

## Overview

NATS was built from the ground up for performance and simplicity. Its core offers at-most-once delivery with sub-millisecond latency, making it the fastest message broker in the cloud-native ecosystem. For applications that need stronger guarantees, NATS JetStream adds persistence, at-least-once delivery, exactly-once semantics, and stream replayability on top of the core NATS infrastructure.

## Key Characteristics

- **Lightweight Core**: The NATS core is minimal — pub/sub subjects, request-reply, and queue groups. There's no persistence, complex routing, or exchange types. This simplicity makes it blazingly fast.
- **Subjects and Wildcards**: Subjects are dot-delimited namespaces (`orders.europe.create`). Wildcards (`*` matches one token, `>` matches rest) enable flexible subscription patterns without complex routing configuration.
- **At-Most-Once Delivery**: NATS core delivers messages with best effort. If no consumer is listening, the message is dropped. This is acceptable for certain use cases (metrics, heartbeats, ephemeral notifications).
- **Queue Groups**: Multiple subscribers on the same subject can form a queue group. Messages are distributed among group members for load-balanced processing — similar to Kafka's consumer groups.
- **JetStream Persistence**: An extension that adds persistent streams, exactly-once delivery, consumer groups with durable state, and message replay. JetStream makes NATS competitive with Kafka while keeping NATS's operational simplicity.
- **Clustering**: NATS supports full mesh clustering for high availability. Cluster nodes share routing information, and clients can connect to any node.

## Why It Matters

NATS is the best choice when you need high-speed messaging with minimal operational complexity. It's ideal for IoT telemetry, microservices metrics, event notifications, and as the glue layer between cloud-native services. The JetStream extension makes it viable for use cases that need persistence without the operational burden of Kafka. NATS is also a popular choice for edge computing where resource constraints matter.

## Related Concepts

- [07-Message-Brokers](07-Message-Brokers.md) — broker landscape comparison
- [08-Kafka](08-Kafka.md) — NATS vs Kafka: simplicity vs feature depth
- [09-RabbitMQ](09-RabbitMQ.md) — NATS vs RabbitMQ: lightweight vs complex routing
- [01-Synchronous-vs-Asynchronous](01-Synchronous-vs-Asynchronous.md) — NATS enables lightweight async communication

---

## Mental Model

NATS is like a town crier in a small village. The crier shouts news (publishes) to the town square (subject). Villagers (subscribers) listen if they're interested. If a villager is at home when news is shouted, they hear it (at-most-once). If they're away, they miss it — the crier doesn't keep a log. JetStream is the town scribe who writes everything down, so villagers can check the record later if they missed the announcement.
