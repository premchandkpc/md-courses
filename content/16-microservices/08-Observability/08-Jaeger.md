# 08-Jaeger

Jaeger is a distributed tracing backend originally built at Uber for monitoring and troubleshooting microservice architectures. It ingests trace data, stores spans, provides a UI for trace search and visualization, and generates service dependency graphs.

## Overview

Jaeger receives spans from instrumented services (via OpenTelemetry, Jaeger SDKs, or Zipkin-compatible clients), stores them in a backend (Cassandra, Elasticsearch, or Badger), and exposes them through a query service and web UI. Engineers use Jaeger to find slow traces, investigate error spans, and understand service interaction patterns.

## Key Characteristics

- **Trace Search**: Query traces by service, operation, tags, duration range, time range, and error status. Results show trace lists sorted by duration, timestamp, or service.
- **Trace Waterfall View**: Each trace is displayed as a timeline with parent-child span relationships, durations, and service boundaries clearly visible. Red spans indicate errors; wide spans indicate slow operations.
- **Service Dependency Graph**: Aggregated traces generate a directed graph showing which services call which, with edge weights representing request volume and latency percentiles.
- **Sampling Strategies**: Probabilistic (sample X% of traces), rate-limiting (max traces/sec per service), and adaptive (automatically adjust sampling based on traffic volume).
- **gRPC and HTTP Storage**: Supports Cassandra (high-scale), Elasticsearch (flexible querying), and Badger (single-node development). The gRPC storage plugin system enables custom backends.
- **Spark Jobs**: Apache Spark jobs process stored traces to compute service dependencies, latency distributions, and usage statistics for large-scale deployments.
- **Search Filtering**: Tags, process attributes, and log annotations are indexed and searchable, enabling queries like "traces with `error=true` and `http.method=POST` in the last hour."

## Why It Matters

When a user reports a slow page load, the response might involve 8 services and 15 network calls. Jaeger shows exactly which call was slow — was it the database query taking 2 seconds, or the payment service timing out after 4 seconds? Without Jaeger, engineers guess. With Jaeger, they pinpoint the offending span in seconds.

## Related Concepts

- [Tracing](06-Tracing.md) — Jaeger is a storage and visualization backend for distributed traces.
- [OpenTelemetry](07-OpenTelemetry.md) — Modern Jaeger deployments ingest traces via the OpenTelemetry Protocol (OTLP).
- [Grafana](05-Grafana.md) — Jaeger traces can be viewed within Grafana via the Jaeger data source plugin, unifying traces with metrics and logs.

---

## Mental Model

Jaeger is the airport control tower's flight radar. Each flight (trace) is shown as a path through waypoints (spans). The radar shows which flights are on time, which are delayed, and where the bottleneck is — waiting on the runway, circling in a holding pattern, or stuck at the gate. Without the radar, you only know the plane is late, not why.
