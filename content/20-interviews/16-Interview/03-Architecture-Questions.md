# 03-Architecture-Questions

Architecture interview questions focusing on system design reasoning, service boundary identification, technology selection, and tradeoff analysis — designed to test depth beyond surface-level patterns.

## Service Boundary Identification
- **How do you decide where one service ends and another begins?** Look for bounded contexts in the domain (DDD). Services should map to business capabilities, not technical layers. Common heuristics: independent deployability, data ownership (a service owns its data), change velocity (different services evolve at different rates).
- **Should services share a database?** Generally no — each service should own its data. Shared databases create coupling. Exception: reporting/analytics where a read replica of multiple services' data is acceptable.
- **How fine-grained should services be?** Too fine = orchestration hell (chatty services). Too coarse = deployment bottleneck. Start with coarse boundaries, split when a service has multiple reasons to change.

## Technology Selection
- **SQL vs NoSQL for your service?** SQL: ACID required, complex queries, structured data, joins needed. NoSQL: high write throughput, simple query patterns, flexible schema, horizontal scaling. CQRS can use both — SQL for writes, NoSQL for reads.
- **Synchronous vs asynchronous communication?** Sync: low latency, immediate feedback, simpler error handling (HTTP/gRPC). Async: decoupling, buffering, fault isolation, but adds latency and complexity (queues, events, sagas). Prefer async for cross-service workflows, sync for query/response.
- **REST vs gRPC?** REST: widely understood, browser-friendly, easy debugging, flexible. gRPC: strongly typed with protobuf, streaming, bidirectional, high performance. Use gRPC for internal service-to-service, REST for public APIs.

## Scalability & Performance
- **How do you handle hot partitions?** A user with 100M followers creates a hot write partition in the feed queue. Solution: sub-partition by entity ID hash, or use a separate high-throughput path for hot entities. Monitor partition skew metrics.
- **When do you need database sharding?** When a single node can't handle the data volume or write throughput. Sharding adds complexity (cross-shard queries, rebalancing). Start with replication + caching, shard only when necessary.
- **Read-heavy vs write-heavy optimization?** Read-heavy: cache aggressively (CDN, in-memory cache), read replicas, denormalized read models. Write-heavy: append-only logs, batch writes, queue-based writes, NoSQL (Cassandra for high write throughput).

## Resilience Patterns
- **Compare retry with exponential backoff vs circuit breaker.** Retries handle transient failures. Circuit breakers prevent cascading failures by failing fast when a downstream is down. Always combine both — retry with backoff first, circuit breaker open when retries keep failing.
- **How do you design for data center failure?** Multi-region active-active (expensive, complex consistency) or active-passive (simpler, failover on DNS). Use asynchronous replication across regions. Plan for full region failover and test it (Chaos Kong style).
- **What's the role of a bulkhead pattern?** Partition resources so one service's failure doesn't consume all threads/connections. Each downstream service gets its own connection pool. Limits blast radius.

## Related Concepts
- [01-Interview-Questions](01-Interview-Questions.md) — Foundational microservices questions
- [02-Scenario-Questions](02-Scenario-Questions.md) — Applied scenario-based questions
- [06-Trade-Offs](06-Trade-Offs.md) — Systematic tradeoff analysis

---

## Mental Model
Architecture questions are like an architect designing a building before anyone sees the blueprint. The interviewer wants to know: can you reason about load-bearing walls (data dependencies), traffic flow (API boundaries), material choices (tech selection), and what happens when an earthquake hits (failure modes)?
