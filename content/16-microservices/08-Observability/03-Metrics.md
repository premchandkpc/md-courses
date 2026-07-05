# 03-Metrics

Metrics are numeric measurements collected over time — counters, gauges, and histograms that reveal the health, performance, and behavior of a system. They are the backbone of monitoring dashboards and alerting rules.

## Overview

Two widely adopted frameworks guide metric selection. RED (Rate, Errors, Duration) focuses on user-facing service health: request rate (requests/sec), error rate (percentage or count of failed requests), and duration (latency distribution). USE (Utilization, Saturation, Errors) focuses on resource health: utilization (how full a resource is), saturation (queue depth or backlog), and errors (failed operations). Together they cover the service and infrastructure dimensions.

## Key Characteristics

- **Counter**: Monotonically increasing value (request count, error count). Resets on restart. Used for rate calculations via `rate()` or `irate()`.
- **Gauge**: Point-in-time value that can go up and down (CPU usage, memory bytes, queue depth, active connections).
- **Histogram**: Samples observations and counts them in configurable buckets (request latency distribution, response size distribution). Enables percentile calculations (p50, p99).
- **Summary**: Similar to histogram but calculates quantiles on the client side (useful when bucket configuration is impractical).
- **Labels/Dimensions**: Key-value pairs attached to metric names (endpoint, method, status_code, service). High-cardinality labels must be used sparingly to avoid exploding time-series cardinality.
- **Exposition Format**: Prometheus text-based format is the de facto standard, with metrics exposed at `/metrics` on a separate port.

## Why It Matters

Logs tell you what happened to a specific request; metrics tell you what is happening to the system as a whole. Without metrics, you cannot detect trends (latency creeping up over weeks), quantify impact (p99 increased from 200ms to 2s), or trigger alerts before users notice degradation.

## Related Concepts

- [Prometheus](04-Prometheus.md) — The dominant pull-based metric collection system; stores and queries metrics exposed by services.
- [Grafana](05-Grafana.md) — Visualizes metrics on dashboards; the primary interface for humans to consume metric data.
- [SLI](10-SLI.md) — Metrics are the raw data from which SLIs (Service Level Indicators) are derived.

---

## Mental Model

Metrics are a car's dashboard instruments. The speedometer (gauge) tells you the current speed, the odometer (counter) tells you total distance, and the fuel gauge (gauge) tells you remaining fuel. You don't need to read the engine's full event log to know you're low on gas — the gauge gives you the essential signal at a glance.
