# 03-Timeout

A timeout bounds the maximum time a caller waits for a response before unblocking and treating the call as failed. It is the most fundamental resilience primitive — without timeouts, a single slow dependency can exhaust all threads and bring down the entire service.

## Overview

Three categories of timeout exist: connection timeout (time to establish TCP handshake), read timeout (time to receive the response body), and write timeout (time to send the request body). In microservices, each layer in the call chain must set its own timeout, and downstream timeouts should always be shorter than upstream timeouts (the chain timeout pattern).

## Key Characteristics

- **Chain Decrease**: Each downstream service gets a shorter timeout than its caller. If Service A calls B with a 5s timeout, B should call C with at most 4s.
- **Distinct Values**: Connection, read, and write timeouts are configured independently; connection timeout is typically short (500ms–1s), read timeout depends on the operation's expected latency.
- **Deadline Propagation**: Pass the remaining deadline as a header (e.g. `X-Deadline-Ms`) so downstream services can enforce their share without exceeding the total.
- **Fail-Fast on Timeout**: A timeout should immediately fail the call and count toward the circuit breaker, not retry silently.
- **No Magical Retries**: A timed-out call should not be automatically retried unless the retry has its own fresh timeout and the operation is idempotent.

## Why It Matters

Without timeouts, a downstream database slow-down causes upstream threads to pile up waiting for responses. Thread pools exhaust, requests queue, memory grows, and the service becomes unresponsive. Timeouts limit the blast radius of a slow dependency to the calls that experienced it.

## Related Concepts

- [Circuit Breaker](01-Circuit-Breaker.md) — Timeouts feed failure counts to the circuit breaker, causing it to trip and fast-fail subsequent requests.
- [Retry](02-Retry.md) — Each retry attempt must have its own timeout; the sum of all timeouts across retries sets the total latency bound.
- [Graceful Shutdown](10-Graceful-Shutdown.md) — In-flight requests during shutdown must still respect their timeout bounds.

---

## Mental Model

Timeouts are like elevator doors. If the doors don't close within 30 seconds, the elevator aborts and tries again — it doesn't stand there forever waiting. In a building with many floors, each floor's door has a shorter timeout than the main entrance, ensuring no single stuck door blocks the entire system.
