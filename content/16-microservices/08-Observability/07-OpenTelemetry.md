# 07-OpenTelemetry

OpenTelemetry (OTel) is a vendor-neutral observability standard for generating, collecting, and exporting telemetry data — traces, metrics, and logs — from cloud-native applications. It provides SDKs, APIs, and a collector that instrument code once and export to any backend (Jaeger, Prometheus, Datadog, New Relic, Grafana Tempo).

## Overview

OpenTelemetry replaces the fragmented landscape of vendor-specific instrumentation libraries with a single, standardized approach. Applications use the OTel API to create spans, record metrics, and emit logs. The OTel SDK handles batching, sampling, and exporting. The OTel Collector acts as a vendor-agnostic agent that receives telemetry, processes it (filter, transform, batch), and routes it to one or more backends.

## Key Characteristics

- **Single Instrumentation**: Write telemetry code once using the OTel API; switch backends by changing exporter configuration, not application code.
- **Three Signals**: Traces (distributed request tracing), metrics (counters, gauges, histograms), and logs (structured log records) — all under one specification.
- **Context Propagation**: W3C Trace-Context standard for propagating trace context across HTTP, gRPC, and message queues.
- **Auto-Instrumentation**: Language-specific agents (Java, Python, Node.js, .NET) automatically instrument common frameworks (Express, Flask, Spring, gRPC) with zero code changes.
- **Collector Pipeline**: The OTel Collector provides receivers (OTLP, Zipkin, Prometheus), processors (batch, filter, sample, transform), and exporters (Jaeger, Prometheus, Datadog, Splunk, stdout).
- **Semantic Conventions**: Standardized attribute names for HTTP, database, messaging, and RPC operations, ensuring consistency across services and organizations.
- **Sampling**: Head-based (probabilistic, rate-limited) and tail-based (decide to sample after seeing the full trace) strategies.

## Why It Matters

Vendor lock-in for observability is expensive and risky. OpenTelemetry decouples instrumentation from backend, giving teams the freedom to evaluate, switch, or run multiple backends without rewriting instrumentation code. It has become the industry standard, adopted by all major cloud providers and observability vendors.

## Related Concepts

- [Tracing](06-Tracing.md) — OpenTelemetry is the standard way to generate and propagate trace context.
- [Prometheus](04-Prometheus.md) — OTel metrics can be exported to Prometheus via the OTel Collector's Prometheus exporter.
- [Jaeger](08-Jaeger.md) — Jaeger accepts OTel trace data via the Jaeger exporter or OTLP protocol.

---

## Mental Model

OpenTelemetry is a universal power outlet adapter. Before OTel, each observability vendor had its own plug shape — Jaeger, Datadog, New Relic, Zipkin all required different instrumentation libraries. OTel is the international standard that every vendor now supports. Plug your instrumentation into the OTel socket, and a simple adapter change routes data to any backend.
