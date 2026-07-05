# 05-Production-Issues

Common production issues in distributed systems — their symptoms, root causes, and remediation strategies. Understanding these patterns helps engineers build resilient systems and respond effectively to incidents.

## Latency Spikes
- **Symptoms**: P99 latency increases 5-10x, P50 may be normal. Error rate may stay flat. Users report slowness but no errors.
- **Common root causes**: GC pauses (Java/Go stop-the-world), event loop blocking (Node.js CPU-bound task), database query degradation (missing index, bad plan cache), connection pool exhaustion (connections queued), DNS resolution delays, TLS negotiation overhead.
- **Remediation**: Profile CPU/memory with flame graphs. Check database slow query log. Add tracing around the suspicious spans. Tune GC settings. Increase connection pool limits. Pre-warm connections.

## Memory Leaks
- **Symptoms**: Container/OOM-killed, gradual memory growth over hours/days, increasing GC frequency, swap usage.
- **Common root causes**: Unbounded caches without eviction, unclosed resources (file handles, DB connections), event listener leaks (accumulating callbacks), thread-local storage growth, string interning gone wrong.
- **Remediation**: Heap dump analysis (find growing object graphs). Set cache TTLs and max sizes. Add memory-usage monitoring and alerting at 70% threshold. Configure resource limits at the container level.

## Cascading Failures
- **Symptoms**: One service fails → its consumers start failing → the failure propagates to more services → eventually a broad outage.
- **Common root causes**: No circuit breakers (consumers keep calling a failing service), retry storms (retry amplification), connection pool exhaustion (all threads blocked waiting for the failing service), resource starvation (CPU/mem consumed by failing processes).
- **Remediation**: Circuit breakers at every service boundary. Bulkheads with per-downstream connection pools. Exponential backoff with jitter on retries. Capacity limits and graceful degradation (serve cached/stale data).

## Data Inconsistency
- **Symptoms**: User sees stale data after a write. Different services show different states for the same entity. Financial totals don't reconcile.
- **Common root causes**: Missing compensating actions in sagas, race conditions in eventually-consistent systems, failed event replay, dual-write problem (writing to DB and queue without atomicity).
- **Remediation**: Transactional outbox pattern. Event replay mechanisms with idempotency. Data reconciliation jobs that compare aggregates across services. Stronger consistency where needed (use distributed locks).

## Hot Partitions
- **Symptoms**: Some database shards/partitions are overloaded while others are idle. Kafka consumer lag on one partition. Uneven query latency.
- **Common root causes**: Skewed key distribution (celebrity user, popular product), bad shard key selection, time-based partitioning with all writes to the latest partition.
- **Remediation**: Choose shard keys with natural spread (user_id, not status). Sub-partition hot keys. Use consistent hashing. Monitor partition size and throughput. Rebalance periodically.

## Configuration Drift
- **Symptoms**: One deployment of a service behaves differently from another, even though the code is the same. Sporadic errors in one region.
- **Common root causes**: Config values differ across environments (staging vs production), feature flags misconfigured, secrets rotation not synchronized, different library versions.
- **Remediation**: Centralized configuration service (Consul, etcd, AWS AppConfig). Immutable infrastructure (AMI/container images with config baked in). Config-as-code reviewed like code. Regular config audits.

## Related Concepts
- [04-Debugging](04-Debugging.md) — Systematic approaches to diagnosing production issues
- [02-Scenario-Questions](02-Scenario-Questions.md) — Scenario-based questions covering incident response
- [07-Staff-Level-Discussions](07-Staff-Level-Discussions.md) — Organizational learning from incidents

---

## Mental Model
Production issues are like chronic health problems in a living organism. A latency spike is a fever (symptom of underlying infection). A memory leak is a slow bleed. Cascading failure is organ failure spreading to other systems. The goal is not just to treat the symptom but to strengthen the body's immune system (resilience patterns) so it can survive future outbreaks.
