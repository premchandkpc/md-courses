# 06-Tracing

Distributed tracing tracks a single request as it propagates through multiple microservices. Each service adds a span — a named, timed operation — to the trace, creating a complete picture of the request's end-to-end lifecycle, including which services were called, in what order, and how long each took.

## Overview

A trace is a tree of spans, each representing work done by a service. The root span covers the entire request from ingress to response. Child spans represent downstream calls, database queries, message publishes, or internal processing. Every span carries a trace ID (shared across all spans in the tree), a span ID (unique), and a parent span ID (links to the caller). Context propagation headers (traceparent, x-b3-traceid) carry these IDs across service boundaries.

## Key Characteristics

- **Trace**: The complete end-to-end record of a single request, composed of a tree of spans sharing the same trace ID.
- **Span**: A named, timed operation with a start time, duration, status, and optional tags/annotations. Examples: `HTTP POST /orders`, `SELECT FROM orders`, `publish order.created`.
- **Context Propagation**: Trace and span IDs are propagated via HTTP headers (W3C Trace-Context, Zipkin B3), gRPC metadata, or message broker headers.
- **Sampling**: Not every request is traced; sampling strategies (head-based, tail-based, probabilistic) control trace volume. Typical rates are 1–10% for high-traffic services.
- **Span Attributes**: Key-value pairs attached to spans (HTTP method, status code, database statement, error message) enrich the trace without creating separate log entries.
- **Service Dependency Graph**: Aggregated traces reveal which services call which others, latency distributions per edge, and error rates per edge.

## Why It Matters

In a monolith, a stack trace shows the full call path. In a microservice architecture, a single request might traverse 10–20 services. Without distributed tracing, engineers cannot determine which service is slow, where errors originate, or how dependencies affect end-to-end latency. Tracing makes the invisible call graph visible.

## Related Concepts

- [OpenTelemetry](07-OpenTelemetry.md) — The vendor-neutral standard for generating, collecting, and exporting trace data.
- [Jaeger](08-Jaeger.md) — A distributed tracing backend that stores and visualizes traces collected via OpenTelemetry.
- [Correlation ID](09-Correlation-ID.md) — The trace ID serves as the correlation ID for logs; trace IDs in structured logs connect log entries to spans.

---

## Mental Model

Tracing is a flight tracking system for a package delivery. The package (request) starts at the sender (entry point). Each scan point along the way — sort facility, truck, hub, delivery van — records a timed entry (span). If the package is delayed, the tracking system shows exactly which facility held it longest. Without tracing, you know the package left and arrived, but not what happened in between.
