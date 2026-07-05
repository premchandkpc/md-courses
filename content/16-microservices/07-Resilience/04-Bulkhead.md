# 04-Bulkhead

A bulkhead partitions resources (thread pools, connection pools, queues) so that failure or saturation in one dependency does not starve another. Named after the compartments in a ship's hull, the pattern prevents cascading failures through resource exhaustion.

## Overview

In a typical microservice, a single shared thread pool means one slow downstream can occupy all threads and block requests to healthy dependencies. Bulkheads replace the shared pool with dedicated pools per dependency (or per group of dependencies). When the payment service thread pool is exhausted, order-processing threads remain unaffected and continue serving requests.

## Key Characteristics

- **Isolated Thread Pools**: Each dependency (or dependency group) gets its own thread pool with a fixed maximum size.
- **Separate Connection Pools**: Database and HTTP client connection pools are scoped per downstream, preventing one service from consuming all connections.
- **Queue Bounding**: Incoming requests to a bulkhead-backed service go into a bounded queue; once the queue is full, requests are rejected immediately.
- **Semaphore vs Thread Pool**: Semaphore bulkheads block the caller thread (no context switch, lightweight), while thread pool bulkheads use a separate executor (isolated, but more overhead).
- **Metric Visibility**: Monitor queue depth, active count, and rejection rate per bulkhead to detect saturation before it causes cascading issues.

## Why It Matters

In a shared-resource architecture, a single misbehaving dependency can exhaust threads, connections, or memory and take down the entire process. Bulkheads enforce fairness at the resource level — each dependency gets only its allocated share, and a flood of failures in one area cannot starve others.

## Related Concepts

- [Circuit Breaker](01-Circuit-Breaker.md) — Bulkheads isolate resources; circuit breakers detect failures and fast-fail. They work together: the breaker stops calls that would waste bulkhead capacity.
- [Backpressure](07-Backpressure.md) — When a bulkhead's queue fills, backpressure signals upstream to slow down rather than dropping requests.
- [Graceful Shutdown](10-Graceful-Shutdown.md) — Bulkhead threads must be drained during shutdown, respecting in-flight requests.

---

## Mental Model

A ship's hull has watertight compartments (bulkheads). If a hole floods one compartment, the other compartments stay dry and the ship stays afloat. Without bulkheads, one hole sinks the entire ship. In microservices, each dependency is a compartment — when one floods with slow requests, the others keep sailing.
