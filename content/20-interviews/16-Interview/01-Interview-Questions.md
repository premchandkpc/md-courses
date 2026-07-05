# 01-Interview-Questions

Common microservices interview questions covering design patterns, architectural decisions, tradeoffs, and operational practices — organized by category for interview preparation.

## System Design Questions
- **Design a URL shortener**: Discuss key generation, redirect latency, analytics pipeline, and cache strategy. Emphasize pre-generated key pools and 301 vs 302 tradeoffs.
- **Design a chat system**: WebSocket management, presence tracking, offline message queues, ordering guarantees, multi-device sync. Cover horizontal scaling of connection state.
- **Design a ride-hailing service**: Geospatial indexing (geohash/S2), matching algorithms, surge pricing, ETA calculation, real-time location streaming.
- **Design a news feed**: Fan-out on write vs fan-out on read, hybrid approach for celebrities, ranking algorithms, real-time vs pre-computed feeds.
- **Design a payment system**: Idempotency keys, authorization vs capture, double-entry ledger, reconciliation, PCI-DSS compliance scope.

## Architecture & Pattern Questions
- **When should you NOT use microservices?** Small team (<10), simple domain, early-stage product, no clear service boundaries. Monolith-first is often the right answer.
- **How do you handle distributed transactions?** Sagas over two-phase commit. Choreography (event-driven) vs orchestration (central coordinator). Compensating actions for rollback.
- **Explain service discovery**: Client-side (load balancer per client) vs server-side (DNS/load balancer). Consul, Eureka, Kubernetes DNS-based discovery. Health checks and circuit breakers.
- **How do you version APIs?** URL path versioning (`/v1/`) for public APIs. Header/content negotiation for internal APIs. Graceful deprecation with sunset headers.
- **Compare message brokers**: Kafka for event streaming (high throughput, replayable). RabbitMQ for task distribution (reliable delivery, complex routing). SQS for simplicity.

## Operational & Reliability Questions
- **How do you debug a latency spike?** Check P99/P50 gap, look for GC pauses, slow downstream services, hot partitions, resource exhaustion. Use distributed tracing to pinpoint.
- **What's your incident response process?** Detect → scope → mitigate → resolve → RCA. Clear severity levels. Communication channels. Postmortem without blame.
- **How do you handle database migrations in microservices?** Expand-migrate-contract pattern. Backward-compatible schema changes. Parallel runs with feature flags. Zero-downtime migrations.
- **Explain circuit breaker patterns**: Three states (closed, open, half-open). Failure thresholds and reset timeouts. Bulkhead isolation to prevent cascade failures.

## Related Concepts
- [02-Scenario-Questions](02-Scenario-Questions.md) — Real-world scenario-based questions
- [03-Architecture-Questions](03-Architecture-Questions.md) — Deeper architecture-focused questions
- [06-Trade-Offs](06-Trade-Offs.md) — Tradeoff analysis for common microservices decisions

---

## Mental Model
Interview questions are like a toolbox check — the interviewer wants to see which tools you reach for given a problem. A strong candidate doesn't just pick the right tool but explains why they chose it over the alternatives and when they'd switch to another tool.
