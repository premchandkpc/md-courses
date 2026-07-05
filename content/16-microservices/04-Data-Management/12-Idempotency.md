# 12-Idempotency

Idempotency means that applying the same operation multiple times produces the same result as applying it once. In microservices, idempotent APIs and event handlers are essential for safe retries, duplicate detection, and reliable communication.

## Overview
- HTTP methods have inherent idempotency: GET, PUT, DELETE are idempotent; POST is not (it creates a new resource each time).
- In microservices, an operation is made idempotent by associating it with a unique idempotency key. The service checks if the key has been processed before running the operation.
- Idempotency protects consumers from double-processing due to network retries, broker redelivery, or client timeouts.
- Idempotency is a design property of the operation, not the transport — it must be implemented at the application level.

## Key Characteristics
- **Idempotency Key**: A unique identifier (UUID, hash of request body + timestamp) sent by the client or embedded in the event. The server stores processed keys (with TTL) to detect duplicates.
- **First-Write Wins**: On receiving a request with an idempotency key, the service checks if the key exists. If yes, return the previous response (idempotent replay). If no, execute and store the key+response.
- **TTL Window**: Idempotency keys have an expiration window (e.g., 24 hours). After expiry, the same key may be reused — the operation should still be safe because the business effect is complete.
- **Safe for Retries**: Clients can retry safely on network errors or timeouts without fear of creating duplicate resources or state.
- **Not the Same as Deduplication**: Idempotency prevents the same operation from changing state more than once. Deduplication discards duplicate messages at the event level. They overlap but are not identical concepts.

## Why It Matters
In distributed systems, network failures are inevitable. Clients retry. Brokers redeliver. Without idempotency, a single payment charge becomes multiple charges, a single order confirmation triggers multiple shipments, or a single account update overwrites previous changes. Idempotency is the foundation of safe retry and at-least-once delivery.

## Related Concepts
- [13-Deduplication](13-Deduplication.md) — Deduplication uses idempotency keys for event processing.
- [06-Inbox-Pattern](06-Inbox-Pattern.md) — Uses idempotency to process events exactly once.
- [05-Outbox-Pattern](05-Outbox-Pattern.md) — At-least-once delivery requires idempotent consumers.

---

## Mental Model
Idempotency is like a hotel check-in. The receptionist records your booking number when you take the key. If you return to the desk and hand over the same booking number, the receptionist says "you already checked in" rather than giving you a second room. The booking number is the idempotency key; the check-in is the idempotent operation.
