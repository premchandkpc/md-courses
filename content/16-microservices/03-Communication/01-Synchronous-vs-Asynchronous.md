# 01-Synchronous-vs-Asynchronous

Synchronous and asynchronous communication are the two fundamental interaction patterns between microservices. The choice between them shapes every aspect of the system — latency, coupling, resilience, and consistency.

## Overview

Synchronous communication (HTTP/gRPC) blocks the caller until the callee responds. It's simple, intuitive, and familiar, but it couples the caller's availability to the callee's. Asynchronous communication (messages/events) decouples the caller from the callee via a broker — the caller emits a message and continues without waiting for a response. This improves resilience but introduces complexity in eventual consistency, error handling, and observability.

## Key Characteristics

- **Latency and Coupling**: Sync gives predictable per-request latency but couples availability — if a downstream service is down, the caller is down too. Async breaks this coupling but adds unpredictable end-to-end latency.
- **Consistency Model**: Sync enables strong consistency within a single request scope. Async forces eventual consistency — the caller must handle the case where the callee hasn't processed the message yet.
- **Error Handling**: Sync errors are immediate and familiar (HTTP status codes, timeouts). Async errors are deferred — the caller emits a message and must implement retry logic, dead letter queues, and compensating transactions.
- **Complexity**: Sync is simpler to reason about (request-response). Async requires idempotency, deduplication, outbox patterns, and saga coordination.

## Why It Matters

A common pattern is sync for queries (where you need an immediate answer) and async for commands (where you want fire-and-forget or event-driven workflows). Most mature microservice systems use a mix of both, choosing based on use case rather than ideology. The rule of thumb: if the caller needs a response to proceed, use sync; if the work can happen later (or not at all), use async.

## Related Concepts

- [12-Choosing-Communication](12-Choosing-Communication.md) — decision framework for choosing between patterns
- [02-REST](02-REST.md) — typical synchronous protocol
- [07-Message-Brokers](07-Message-Brokers.md) — infrastructure for async communication

---

## Mental Model

Synchronous is like a phone call: you dial, someone picks up, you have a conversation, you hang up. Both parties are present for the duration. Asynchronous is like email: you send a message and go about your day. The recipient reads it whenever they're ready and replies. Email is more resilient (the sender doesn't need the recipient to be online), but you don't get an immediate answer.
