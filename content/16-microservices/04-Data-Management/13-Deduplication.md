# 13-Deduplication

Deduplication detects and discards duplicate events or messages so that each is processed exactly once. It is essential in distributed systems where message brokers and network protocols guarantee at-least-once delivery but not exactly-once.

## Overview
- Distributed messaging systems (Kafka, RabbitMQ, SQS) guarantee at-least-once delivery under normal operation. Duplicates can occur due to producer retries, broker failover, or consumer rebalancing.
- Deduplication assigns each event a unique dedup key (often the event ID or a hash of the content) and checks a dedup store before processing.
- Duplicate events are acknowledged but not processed — the consumer returns the previously computed result if available.
- Deduplication and idempotency are closely related but differ in scope: deduplication discards duplicates at the message level; idempotency ensures the operation is safe even without deduplication.

## Key Characteristics
- **Dedup Store**: A persisted key-value store (Redis, DynamoDB, database table) that records processed event IDs with a TTL. The store must be available for every event — if unavailable, the consumer may process duplicates.
- **TTL-Based Eviction**: Dedup keys have a retention window (e.g., 7 days). After TTL, duplicate delivery is theoretically possible but unlikely in practice. The window must exceed the maximum possible redelivery delay.
- **Exactly-Once Semantics**: Deduplication + at-least-once delivery = effectively-once processing. No system provides true exactly-once under all failure scenarios; deduplication brings it as close as possible.
- **Ordering Impact**: Strictly ordered processing (e.g., Kafka within a partition) simplifies deduplication. With unordered delivery, deduplication must handle out-of-order arrivals — a late duplicate might arrive after the original has been processed and evicted.
- **Storage vs. Performance Tradeoff**: A large dedup window reduces the chance of duplicates but increases storage cost. Some systems use probabilistic deduplication (Bloom filters) to reduce storage at the cost of false positives.

## Why It Matters
Without deduplication, a broker failover or client timeout can cause duplicate event processing — resulting in double charges, duplicate notifications, or inconsistent state. Deduplication is a prerequisite for building reliable, correct event-driven systems. It is the consumer-side counterpart to the Outbox pattern's at-least-once delivery guarantee.

## Related Concepts
- [12-Idempotency](12-Idempotency.md) — Deduplication implements idempotency at the event level.
- [06-Inbox-Pattern](06-Inbox-Pattern.md) — The Inbox uses deduplication to process events exactly once.
- [05-Outbox-Pattern](05-Outbox-Pattern.md) — Generates the at-least-once stream that deduplication consumes.

---

## Mental Model
Deduplication is like a bouncer with a guest list clipboard. The first time a guest arrives, the bouncer checks their name and crosses it off. If the same guest tries to enter again, the bouncer says "you're already inside" — the clipboard (dedup store) remembers. The clipboard is cleared every week (TTL), so a guest with an identical name showing up months later gets a fresh entry.
