# 04-Debugging

Debugging distributed systems requires fundamentally different techniques than debugging a single process — tracing requests across service boundaries, correlating logs, reproducing race conditions, and navigating the inherent uncertainty of networked systems.

## Core Debugging Strategies
- **Distributed tracing**: Every request receives a trace ID propagated via HTTP headers (or message metadata). Use OpenTelemetry or Jaeger/Zipkin. Traces span service boundaries. Look for spans with high latency or errors. Trace IDs should be logged in every service.
- **Structured logging**: JSON-formatted logs with trace_id, service_name, span_id, user_id, and duration_ms. Centralized log aggregation (Elasticsearch, Loki, CloudWatch Logs). Queries filter by trace_id to reconstruct the full request path across services.
- **Metrics-driven investigation**: Start with dashboards — which service's error rate spiked? Which endpoint's latency increased? Follow the signal: frontend → API gateway → service → database. Use RED metrics (Rate, Errors, Duration) per service.
- **Reproduction strategies**: Hard to reproduce in distributed systems — use record/replay (traffic mirroring), fault injection testing (Chaos Monkey/Simian Army), or replay production traffic in a staging environment.

## Common Debugging Patterns
- **It works in staging but not production**: Resource differences (staging has 1 replica, production has 20 and hits contention), data differences (staging has 100 users, production has 10M with hot partitions), configuration differences (timeouts, feature flags). Compare configurations. Mirror production data for staging.
- **Intermittent failures**: These are often caused by race conditions, GC pauses, or resource contention. Add more logging around the failure point. Increase the sample size. Use thread/goroutine dumps at the point of failure to detect deadlocks or contention.
- **Slow requests in a fast system**: P99 latency spikes are often caused by head-of-line blocking — a slow request blocks subsequent requests in the thread/event loop. Look for long database queries, large payloads (serialization), or slow external API calls. Use concurrent request tracing.
- **Data inconsistency between services**: Often stems from a failed saga step that wasn't compensated, or a race condition in an eventually-consistent system. Check the saga state machine. Look for missing compensating actions. Compare event logs from both services.

## Tooling & Techniques
- **Flame graphs**: Visualize CPU time spent in each code path. Useful for identifying unexpected hot paths.
- **Heap dumps**: Capture and analyze memory. Look for objects that shouldn't be growing (leak suspects).
- **Slow query analysis**: Database query logs with duration. Look for sequential scans, missing indexes, or queries that don't use indexes.
- **Network captures**: tcpdump/Wireshark for identifying retransmissions, TLS handshake overhead, or dropped connections.
- **Chaos experiments**: Proactively test resilience by injecting failures (network latency, packet loss, instance termination) in a controlled way.

## Related Concepts
- [05-Production-Issues](05-Production-Issues.md) — Common production issue patterns and root causes
- [03-Architecture-Questions](03-Architecture-Questions.md) — Resilience patterns that prevent the need for debugging
- [07-Staff-Level-Discussions](07-Staff-Level-Discussions.md) — Incident review culture and postmortems

---

## Mental Model
Debugging a distributed system is like solving a mystery across multiple cities. You can't just look at the scene of the crime (one service) — you need to check train schedules (network latency), interview witnesses in each city (logs), and track the suspect's movements across city lines (distributed tracing). The timeline reconstruction (trace) is your most powerful tool.
