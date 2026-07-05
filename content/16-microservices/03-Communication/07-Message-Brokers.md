# 07-Message-Brokers

A message broker is an intermediary that receives messages from producers and routes them to consumers. It decouples the sender from the receiver, providing buffering, routing, and delivery guarantees.

## Overview

Message brokers sit between services, accepting messages from producers and delivering them to interested consumers. This decouples services in both time (producer and consumer don't need to be online simultaneously) and space (they don't need to know each other's network locations). Brokers handle buffering, routing based on rules or topics, and delivery semantics ranging from at-most-once to exactly-once.

## Key Characteristics

- **Producer-Consumer Decoupling**: Producers emit messages without knowing who (or if anyone) will consume them. Consumers subscribe without knowing who produced the message. This is the foundation of event-driven architectures.
- **Buffering**: If a consumer is slow or unavailable, the broker buffers messages. This prevents backpressure from propagating to producers. Buffering also absorbs traffic spikes — the broker acts as a shock absorber.
- **Routing**: Brokers route messages using topics (Kafka), exchanges and routing keys (RabbitMQ), or subjects (NATS). This allows flexible message distribution patterns: point-to-point, pub/sub, and complex routing topologies.
- **Delivery Guarantees**: Brokers offer different guarantees: at-most-once (fire and forget, may lose messages), at-least-once (guaranteed delivery, may duplicate), and exactly-once (guaranteed delivery without duplicates, highest overhead).
- **Persistence**: Messages can be persisted to disk, surviving broker restarts. Kafka and RabbitMQ offer configurable persistence. NATS JetStream adds persistence to the lightweight NATS core.

## Why It Matters

Message brokers are the backbone of asynchronous, event-driven microservices. They enable decoupled architectures where services react to events rather than calling each other directly. The choice of broker depends on throughput requirements, routing complexity, delivery guarantees, and operational maturity. Kafka dominates high-throughput event streaming; RabbitMQ excels at complex routing; NATS fills the niche for lightweight, high-speed messaging.

## Related Concepts

- [08-Kafka](08-Kafka.md) — distributed event log broker
- [09-RabbitMQ](09-RabbitMQ.md) — AMQP-based broker with rich routing
- [10-NATS](10-NATS.md) — lightweight, high-performance messaging
- [01-Synchronous-vs-Asynchronous](01-Synchronous-vs-Asynchronous.md) — brokers enable async communication

---

## Mental Model

A message broker is like a postal service. You (producer) drop a letter in a mailbox with an address (routing key). The postal service (broker) sorts, buffers, and delivers the letter to the recipient (consumer). You don't need to know where the recipient lives or whether they're home when you mail it. The postal service handles storage and forwarding, just like a broker handles message buffering and delivery.
