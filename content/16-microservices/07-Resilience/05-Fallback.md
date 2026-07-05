# 05-Fallback

A fallback provides an alternative response when a primary operation fails, enabling graceful degradation instead of a hard error. It is the user-facing counterpart to circuit breakers, retries, and timeouts — the mechanism that turns a backend failure into a tolerable experience.

## Overview

When a call to a downstream dependency fails (after exhausting retries, or because the circuit breaker is open), the fallback handler returns a substitute response. Common strategies include serving a stale cached value, returning a sensible default, providing a null object, redirecting to a secondary service, or enqueuing the request for later processing.

## Key Characteristics

- **Stale Cache**: Return the last known good value from cache even if it is slightly outdated; acceptable for read-heavy workloads where eventual consistency is tolerable.
- **Default Value**: Return a static default (e.g. empty list, zero, "currently unavailable") that the caller can handle without breaking the user experience.
- **Null Object Pattern**: Return a no-op implementation that satisfies the interface but produces no side effects (e.g. a no-op payment processor for read-only mode).
- **Secondary Service**: Redirect to a degraded but functional alternative endpoint or a read-replica.
- **Queue for Later**: Persist the request to a queue for asynchronous reprocessing when the dependency recovers.
- **Composition**: Fallbacks can be chained — try primary, then cached value, then default, then error.

## Why It Matters

Users prefer a degraded experience over an error page. A fallback that shows "Comments temporarily unavailable — try again later" is far better than a 500 error or a spinning loader. Fallbacks maintain availability at reduced functionality and buy time for the operations team to fix the underlying issue.

## Related Concepts

- [Circuit Breaker](01-Circuit-Breaker.md) — The fallback is typically invoked when the circuit breaker is in the OPEN state.
- [Retry](02-Retry.md) — Fallback runs after all retry attempts are exhausted; it is the last line of defense.
- [Dead Letter Queue](06-Dead-Letter-Queue.md) — Messages that cannot be processed and have no valid fallback route to a DLQ for manual inspection.

---

## Mental Model

Fallback is like a restaurant that runs out of your first-choice dish. Instead of sending you away hungry, the chef offers a backup option: "We're out of salmon, but the sea bass is excellent." It's not what you ordered, but it fills the plate and keeps you happy. A cached response is yesterday's menu — not perfect, but edible.
