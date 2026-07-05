# Throttling

A server-side mechanism that rejects or delays requests when the system is under heavy load, protecting services from being overwhelmed. Unlike rate limiting (which enforces client quotas), throttling is capacity-aware and dynamic.

## Overview

Throttling monitors the current load on the system — CPU, memory, connection pool depth, queue length — and rejects excess requests when utilization exceeds a threshold. It can be implemented as a fixed concurrency limit (max N concurrent requests), a queue with bounded depth (requests wait briefly then fail), or adaptive throttling (the limit adjusts based on latency or error rates). The goal is graceful degradation rather than total collapse.

## Key Characteristics

- **Capacity-Aware**: Throttling decisions reflect real-time system health, not static client quotas. If services are healthy, more requests pass through.
- **Queue-Based Buffering**: A bounded queue absorbs short bursts; requests beyond the queue depth receive 503 (Service Unavailable) immediately, preventing backlog cascades.
- **Graceful Degradation**: When throttled, the system can serve degraded responses (cached data, partial results) instead of failing entirely.

## Why It Matters

Without throttling, a traffic spike can saturate thread pools, exhaust database connections, and trigger a cascade of failures across the dependency graph. Throttling provides a backpressure mechanism — upstream services see errors fast (fail-fast) rather than timing out slowly. This containment prevents a localized spike from becoming a system-wide outage.

## Related Concepts

- [Rate Limiting](04-Rate-Limiting.md) — Client-side quota enforcement; throttling complements it from the server side.
- [Caching](06-Caching.md) — Served cached responses during throttling to reduce load.
- [Load Balancing](../06-Service-Discovery/07-Load-Balancing.md) — Distributes load across instances; throttling protects individual instances from overload.

## Mental Model

Throttling is like a highway on-ramp metering light. During light traffic, cars merge freely. When the highway is congested, the metering light lets one car through per green cycle, keeping the main road flowing at a sustainable speed. Cars that can't merge wait on the ramp (queue) or take an alternate route (degraded response).
