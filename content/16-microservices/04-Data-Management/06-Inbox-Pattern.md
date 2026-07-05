# 06-Inbox-Pattern

The Inbox pattern ensures reliable event consumption by storing incoming events in a local database table (the inbox) and processing them idempotently. This protects against duplicate delivery and crashes during processing, giving the consumer "exactly-once" processing semantics.

## Overview
- When a message broker delivers an event, the consumer first writes the event ID to an inbox table in its local database (within a transaction).
- After the inbox record is committed, the consumer processes the event (updates business data, calls external services, etc.).
- Duplicate events (same event ID) are detected and discarded before processing — the consumer simply skips or acknowledges them.
- If the consumer crashes after committing the inbox record but before processing completes, a recovery process picks up unprocessed inbox records and retries them.

## Key Characteristics
- **Idempotent Processing**: The inbox ensures that each event is processed exactly once, even if delivered multiple times. The event ID serves as the idempotency key.
- **Crash Recovery**: Unprocessed inbox records survive crashes. A background worker or startup handler retries them until successful.
- **Order Preservation**: Inbox processing can reorder events if a later event is processed before an earlier one. Services that require strict ordering need additional sequencing logic.
- **Storage Overhead**: The inbox table grows over time. Older records must be archived or deleted after a retention period.
- **Transactional Boundary**: The inbox record and business data update must happen in the same local transaction. This requires careful design of the processing handler.

## Why It Matters
The Inbox pattern is the consumer-side counterpart to the Outbox pattern. Together, they provide end-to-end reliability for event-driven communication in microservices. Without the inbox, a consumer crash during processing loses the event forever, or duplicate deliveries cause double-processing. It is essential for services that must not lose or duplicate state changes.

## Related Concepts
- [05-Outbox-Pattern](05-Outbox-Pattern.md) — Producer-side counterpart for reliable event publishing.
- [12-Idempotency](12-Idempotency.md) — The inbox enables idempotent event processing.
- [13-Deduplication](13-Deduplication.md) — Event ID-based deduplication is the core mechanism.

---

## Mental Model
The inbox is like a restaurant order ticket rack. When a waiter brings an order, it's hung on the rack (inbox write). The chef picks tickets one by one and prepares the meals (processing). If a waiter accidentally brings the same order twice, the chef sees it's already on the rack and ignores the duplicate. If the chef drops a pan, the tickets are still on the rack — work resumes when the chef is ready.
