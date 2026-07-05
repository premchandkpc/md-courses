# 02-Retry

Retry is the automatic re-execution of a failed operation when the failure is likely transient. It is the simplest resilience mechanism but requires careful configuration to avoid amplifying load during an outage.

## Overview

Network partitions, DNS hiccups, connection pool exhaustion, and database deadlocks are often temporary. Retry logic intercepts the error, checks if the exception type is retryable, and re-issues the call up to a configured maximum number of attempts. Retries must be paired with exponential backoff and jitter to avoid overwhelming the downstream service.

## Key Characteristics

- **Retryable Exception Types**: Only retry on transient errors (timeouts, 503 Service Unavailable, network errors); never retry 4xx (client errors) or business logic failures.
- **Max Attempts**: Hard limit on total retries, including the initial call; typical values are 3–5.
- **Backoff Strategy**: Delay between retries increases (fixed, incremental, or exponential); exponential with jitter is the production standard.
- **Idempotency Requirement**: The operation must be safe to execute multiple times; check for idempotency keys or use the HTTP PUT/DELETE semantics.
- **Retry Budget**: Track retry volume as a fraction of total requests; if retries exceed budget, stop retrying to prevent overload.

## Why It Matters

Microservices depend on network calls that fail intermittently. Without retries, transient failures become user-facing errors. With too-aggressive retries, a minor blip turns into a self-inflicted DDoS. Retry must be scoped per-call, bounded, and coordinated with circuit breakers to avoid cascading failure.

## Related Concepts

- [Exponential Backoff](08-Exponential-Backoff.md) — The standard delay algorithm between retries; prevents synchronized retry storms.
- [Circuit Breaker](01-Circuit-Breaker.md) — Retry should attempt before the breaker trips; once the breaker is open, retries must stop.
- [Timeout](03-Timeout.md) — Each attempt must have its own timeout; total wall-clock time = sum(retry count × timeout).
- [Idempotency](../06-API-Gateway/04-Idempotency.md) — Only safe to retry if the operation is idempotent or the retry carries an idempotency key.

---

## Mental Model

Retry is like trying to call a friend whose phone keeps ringing busy. You wait a few seconds and try again. If it's still busy after five tries, you stop and send a text instead. You don't keep redialing every second — that would tie up your line and annoy everyone.
