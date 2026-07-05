# 01-Circuit-Breaker

A circuit breaker is a stateful proxy that monitors for failures and temporarily stops requests to a failing dependency once a threshold is breached. It implements a state machine with three states — CLOSED (normal operation), OPEN (fast-fail), and HALF-OPEN (probing recovery) — and is one of the most critical resilience patterns in microservices.

## Overview

Circuit breakers prevent cascading failures by detecting when a downstream service is unhealthy and failing fast instead of wasting resources on doomed calls. The transition from CLOSED to OPEN happens when consecutive failures or error rates exceed a configured threshold. After a cooldown period, the breaker transitions to HALF-OPEN and allows a probe request; success moves back to CLOSED, while failure returns to OPEN.

## Key Characteristics

- **State Machine**: CLOSED → OPEN (on threshold breach) → HALF-OPEN (after timeout) → CLOSED (on success) or back to OPEN.
- **Failure Counting**: Sliding window or rolling counter tracks recent failures, not cumulative.
- **Fast-Fail**: In OPEN state, requests fail immediately without calling the downstream service.
- **Probe Recovery**: A single trial request in HALF-OPEN determines if the service has recovered.
- **Configurable Thresholds**: Failure count, error percentage, cooldown duration, and half-open max requests.
- **Trip on Multiple Signals**: Can respond to slow calls (timeouts), network errors, HTTP 5xx, or custom exceptions.

## Why It Matters

Without circuit breakers, a single degraded service can trigger retry storms that exhaust connection pools, block threads, and cascade failures across the entire system. The breaker acts as a load-shedding mechanism that isolates faults to their origin and preserves capacity for healthy dependencies.

## Related Concepts

- [Retry](02-Retry.md) — Circuit breakers and retries must coordinate; retry before tripping, but stop retrying once the breaker is open.
- [Bulkhead](04-Bulkhead.md) — Bulkheads isolate thread pools per dependency, complementing the circuit breaker's failure detection.
- [Timeout](03-Timeout.md) — Timeouts prevent slow calls from hanging threads, which feeds failure counts to the breaker.

---

## Mental Model

Think of a circuit breaker like a power breaker panel in your house. When a circuit draws too much current (faults), the breaker trips (OPEN) and cuts power to prevent fire. You don't keep flipping it back on immediately — you wait, then try once (HALF-OPEN), and if it holds, you leave it on (CLOSED). The breaker protects the entire house, not the failing appliance.
