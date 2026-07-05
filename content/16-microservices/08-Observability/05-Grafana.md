# 05-Grafana

Grafana is an open-source observability platform for visualizing metrics, logs, and traces on unified dashboards. It connects to multiple data sources (Prometheus, Loki, Elasticsearch, Jaeger, CloudWatch) and provides a rich query builder, alerting engine, and dashboard management system.

## Overview

Grafana is the visual layer of observability. Engineers use it to build time-series panels (graphs, heatmaps, stat panels) that display metric trends, log volume, and trace spans side-by-side. Dashboards are organized by service, team, or concern (latency overview, error budget, resource utilization). Grafana's alerting engine evaluates queries on a schedule and sends notifications through PagerDuty, Slack, or webhooks.

## Key Characteristics

- **Data Source Abstraction**: A single dashboard can combine Prometheus metrics, Loki logs, and Jaeger traces in unified views.
- **Dashboard-as-Code**: Dashboards are exported as JSON and version-controlled. Teams review dashboard changes alongside code changes.
- **Panels and Visualizations**: Graph (time series), Stat (single value), Gauge (dial), Heatmap (distribution over time), Table, Bar chart, and more.
- **Explore Mode**: Ad-hoc query interface for drilling into metrics or logs without creating a dashboard — essential for incident investigation.
- **Alerting**: Unified alerting engine evaluates PromQL/LogQL queries, handles silences, notification policies, and alert grouping.
- **Annotations**: Deployments, incidents, and config changes can be overlaid on graphs to correlate metric changes with events.
- **RBAC**: Role-based access control for dashboards, folders, and data sources across teams.
- **Templating**: Dashboard variables (service name, environment, region) let users dynamically filter without editing the dashboard JSON.

## Why It Matters

Raw metrics and logs are inaccessible to most team members. Grafana turns them into actionable visualizations that anyone can read during an incident. A well-designed Grafana dashboard answers "is the system healthy?" in under 5 seconds and guides the operator to the relevant data sources for deeper investigation.

## Related Concepts

- [Prometheus](04-Prometheus.md) — The primary metrics data source for Grafana dashboards.
- [Logging](01-Logging.md) — Grafana's Explore mode links from a metric spike to the corresponding logs via label matching.
- [Tracing](06-Tracing.md) — Grafana's Tempo or Jaeger data sources render trace spans alongside metrics.

---

## Mental Model

Grafana is the mission control center for your software. Each screen (dashboard) shows a different view: system health, error budgets, latency heatmaps, database performance. When an alarm sounds (alert fires), controllers glance at the main screen, see which subsystem is red, and drill into the detailed view for that subsystem — all from one console that integrates every telemetry source.
