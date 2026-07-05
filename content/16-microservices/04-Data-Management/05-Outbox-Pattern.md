# 05-Outbox-Pattern

The Outbox pattern ensures reliable event or message publishing by storing the event in the same database transaction as the business data. A separate process then reads from the outbox table and publishes events to the message broker — guaranteeing that events are never lost between the database commit and broker send.

## Overview
- In a microservice that uses both a database and a message broker, the dual-write problem occurs: saving to DB and publishing to broker are two separate systems, and one can fail while the other succeeds.
- The Outbox pattern solves this by writing both the business data and an "outbox event" record in a single ACID database transaction.
- A separate publisher process polls the outbox table (or tails the transaction log) and sends events to the broker.
- Once the broker acknowledges receipt, the outbox record can be deleted or marked as sent.

## Key Characteristics
- **Atomicity**: The business data and the outbox event are written in one DB transaction. If the DB commit succeeds, the event is guaranteed to exist for publishing.
- **At-Least-Once Delivery**: The publisher may send the same event multiple times (if it crashes after sending but before marking as sent). Downstream consumers must handle duplicates.
- **Polling or CDC-Based Publisher**: Polling reads the outbox table on a timer (simple but adds latency and DB load). Change Data Capture (CDC) tails the DB transaction log for near-real-time publishing.
- **Idempotent Consumers Required**: Since the publisher can deliver duplicates, consuming services must be idempotent or use deduplication.

## Why It Matters
The Outbox pattern is one of the most fundamental reliability patterns in event-driven microservices. Without it, systems lose events during broker outages, application crashes, or network failures. It is the standard approach for achieving "exactly-once" semantics at the source (at-least-once delivery plus deduplication at the consumer).

## Related Concepts
- [06-Inbox-Pattern](06-Inbox-Pattern.md) — Consumer-side counterpart for reliable event consumption.
- [09-CDC](09-CDC.md) — A zero-code alternative using transaction log tailing instead of explicit outbox tables.
- [13-Deduplication](13-Deduplication.md) — Required at the consumer because of at-least-once delivery.

---

## Mental Model
The Outbox pattern is like mailing a package with tracking. You fill out the order form and the shipping label in one sitting (single DB transaction). A postal worker later picks up all labeled packages and delivers them (publisher → broker). If the worker drops a package, they can check the pile of unfilled labels and try again — no package is lost.
