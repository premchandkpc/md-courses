# 08-Kafka

Apache Kafka is a distributed event streaming platform designed for high-throughput, fault-tolerant, and persistent message processing. It is built around the concept of an append-only commit log.

## Overview

Unlike traditional message brokers that route messages and delete them after consumption, Kafka persists all messages in a structured commit log. Messages are organized into topics, which are partitioned across brokers for parallelism and fault tolerance. Consumers read from the log at their own pace, maintaining an offset that tracks their position. This enables replayability — consumers can rewind and reprocess messages from any point in time.

## Key Characteristics

- **Topics and Partitions**: A topic is a logical channel. Topics are split into partitions (ordered, immutable sequences of records). Partitions are the unit of parallelism — each partition is consumed by exactly one consumer in a consumer group.
- **Offset Management**: Each consumer in a consumer group tracks its offset — the position in the partition it has read up to. Offsets can be committed manually or automatically, enabling exactly-once and at-least-once semantics.
- **Consumer Groups**: A group of consumers that collaboratively consume a topic. Partitions are distributed across consumers in the group. If a consumer fails, partitions are reassigned — this is Kafka's built-in rebalancing mechanism.
- **Replayability**: Because data is persisted for a configurable retention period (time or size based), consumers can rewind to any offset and reprocess. This is invaluable for debugging, backfilling, and building materialized views.
- **Exactly-Once Semantics (EOS)**: Kafka supports idempotent producers, transactional writes, and exactly-once processing via the Streams API. This enables reliable exactly-once pipelines without custom deduplication logic.
- **High Throughput**: Kafka is benchmarked at millions of messages per second on modest hardware. It achieves this through sequential disk I/O, zero-copy data transfer, and batch processing.

## Why It Matters

Kafka is the de-facto standard for event streaming in microservices. It's used for event sourcing, log aggregation, metrics, CQRS, and data pipeline integration. Its replayability separates it from other brokers — you can reprocess events to fix bugs or backfill analytics. The operational cost is higher than simpler brokers, but for high-volume, persistent, replayable event streams, Kafka is unmatched.

## Related Concepts

- [07-Message-Brokers](07-Message-Brokers.md) — Kafka compared to other brokers
- [09-RabbitMQ](09-RabbitMQ.md) — Kafka vs RabbitMQ: when to choose each
- [10-Schema-Evolution](../02-Service-Design/10-Schema-Evolution.md) — Avro schema registry with Kafka
- [01-Synchronous-vs-Asynchronous](01-Synchronous-vs-Asynchronous.md) — Kafka enables async, event-driven communication

---

## Mental Model

Kafka is like a library's archival records. Every event (book) is permanently stored in chronological order on the shelves (commit log). A researcher (consumer) can start reading from volume 1, page 1 (offset 0), or jump to any specific entry. Multiple researchers can read the same archive simultaneously, each at their own pace. New volumes are always appended to the end — nothing is ever deleted, just archived for a set period.
