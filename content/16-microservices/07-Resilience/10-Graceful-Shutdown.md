# 10-Graceful-Shutdown

Graceful shutdown is the process of stopping a service without abruptly terminating in-flight work or dropping connections. It ensures that ongoing requests complete, resources are released cleanly, and the service's removal from the load balancer is orderly.

## Overview

When a service receives a termination signal (SIGTERM, SIGINT), it enters shutdown mode: the readiness probe returns "not ready" to remove the instance from the load balancer, the HTTP server stops accepting new connections, in-flight requests are given a deadline to finish, connections to databases and message brokers are closed, and the process exits. The entire sequence must complete within the orchestrator's grace period (typically 30–60 seconds).

## Key Characteristics

- **Drain In-Flight Requests**: After the load balancer removes the instance, the server waits for active requests to complete up to a configurable timeout. Requests exceeding the timeout are force-cancelled.
- **Stop Accepting New Connections**: The TCP listener is closed first; new connections receive a polite refusal or are redirected by the load balancer.
- **Deregister from Service Registry**: The service removes itself from the discovery registry (Consul, Eureka, Kubernetes endpoints) to prevent new traffic from being routed to it.
- **Health Probe Marking**: The readiness endpoint immediately returns 503 so that load balancer health checks see the instance as unavailable.
- **Cleanup Resources**: Close database connection pools, flush buffers, close message broker sessions, release file handles, and stop background goroutines.
- **Sequenced Phases**: shutdown(1) mark unhealthy → (2) stop listener → (3) drain requests with deadline → (4) close dependencies → (5) exit.
- **Orchestrator Integration**: Kubernetes sends SIGTERM, waits for the terminationGracePeriodSeconds, then sends SIGKILL. The service must complete shutdown within that window.

## Why It Matters

An ungraceful shutdown (SIGKILL) kills in-flight requests, corrupts data mid-write, leaves database connections hanging, and causes 502 errors for clients. Graceful shutdown is essential for zero-downtime deployments, rolling updates, and cluster autoscaling — scenarios where instances are constantly being replaced.

## Related Concepts

- [Health Checks](09-Health-Checks.md) — Readiness probe returns unhealthy during shutdown to drain traffic before the process exits.
- [Bulkhead](04-Bulkhead.md) — Thread pools in bulkheads must be drained, not abruptly terminated, during shutdown.
- [Timeout](03-Timeout.md) — The drain timeout during shutdown must be shorter than the orchestrator's grace period to avoid SIGKILL interrupting in-flight requests.

---

## Mental Model

Graceful shutdown is like closing a restaurant for the night. First, the host puts up a "Closed" sign (mark unhealthy) and stops seating new customers (stop listener). The existing tables finish their meals (drain in-flight). The kitchen cleans up and the staff goes home (release resources). Nobody is thrown out mid-bite (no SIGKILL), and arriving guests see the closed sign and go elsewhere instead of waiting outside.
