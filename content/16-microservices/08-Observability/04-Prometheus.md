# 04-Prometheus

Prometheus is a pull-based monitoring and alerting toolkit designed for reliability and operational simplicity. It scrapes metrics from instrumented services at regular intervals, stores them in a time-series database, and provides a powerful query language (PromQL) for analysis and alerting.

## Overview

Unlike push-based systems where services send metrics to a central collector, Prometheus periodically pulls (scrapes) metrics from HTTP endpoints exposed by each service. This pull model makes it easy to detect when a service is down — if a scrape target stops responding, that absence is itself a signal. Prometheus integrates with service discovery to dynamically find targets as instances scale up and down.

## Key Characteristics

- **Pull Model**: Prometheus server scrapes `/metrics` endpoints on a configurable interval (typically 15–60s). The target is unreachable if it doesn't respond.
- **PromQL**: A functional query language for selecting, aggregating, and transforming time-series data. Examples: `rate(http_requests_total[5m])` (request rate), `histogram_quantile(0.99, rate(...))` (p99 latency).
- **Metric Types**: Counter, Gauge, Histogram, Summary — each with well-defined semantics that PromQL functions depend on.
- **Service Discovery**: Integrates with Kubernetes, Consul, EC2, and other platforms to automatically discover scrape targets.
- **Alertmanager**: Prometheus evaluates alerting rules and pushes alerts to Alertmanager, which handles deduplication, grouping, silencing, and routing to notification channels (PagerDuty, Slack, email).
- **Local Storage**: On-disk time-series storage with configurable retention. For long-term storage, Prometheus data is forwarded to remote storage systems (Thanos, Cortex, Mimir).
- **Pull vs Push Exceptions**: The Pushgateway supports short-lived jobs (batch processes, cron jobs) that cannot be scraped because they exit before the next scrape interval.

## Why It Matters

Prometheus is the de facto standard for metrics in cloud-native environments. Its pull model naturally detects down instances, PromQL enables sophisticated alerting (e.g. "alert if error rate exceeds 5% over 5 minutes"), and the ecosystem of exporters covers databases, hardware, and third-party services.

## Related Concepts

- [Metrics](03-Metrics.md) — Prometheus is the storage and query layer for the metrics that services expose.
- [Grafana](05-Grafana.md) — Grafana connects to Prometheus as a data source to build dashboards on top of Prometheus metrics.
- [SLI](10-SLI.md) — Prometheus queries define the SLI (e.g. `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))`).

---

## Mental Model

Prometheus is like a security guard doing rounds. Every 30 seconds, the guard walks past each door (scrape target) and checks whether it's locked, the light is on, and the temperature is normal (metrics). If a door is wide open or the room is on fire (alerting rule), the guard radios headquarters (Alertmanager) to dispatch the right team. If a door isn't checked on two consecutive rounds, that's also a problem — the office might be empty or the guard can't get through.
