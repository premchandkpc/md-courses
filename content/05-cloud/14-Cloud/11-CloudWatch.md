# 11-CloudWatch

Amazon CloudWatch is the monitoring and observability service for AWS. It collects metrics, logs, and events from AWS resources and applications, enabling dashboards, alarms, automated actions, and centralized log analysis.

## Overview
CloudWatch consists of several integrated services. CloudWatch Metrics collect data points from AWS services (EC2 CPU, Lambda invocations, DynamoDB consumed capacity, API Gateway 5xx counts) and custom application metrics. Metrics are stored for 15 months and can be visualized in dashboards. CloudWatch Logs ingests log data from services (Lambda, ECS, API Gateway) and EC2 agents. Logs can be searched, filtered, and exported to S3 or Elasticsearch. CloudWatch Alarms monitor metrics and trigger actions (SNS notification, Auto Scaling, EC2 recovery). CloudWatch Events (now part of EventBridge) routes system events to targets.

## Key Characteristics
- **Structured and unstructured data**: Metrics are numeric time-series (scalar values with timestamps). Logs are text-based with structured JSON support. Both are searchable.
- **Metric dimensions**: Each metric can have up to 10 dimensions (key-value pairs like ServiceName, Environment, Region). Dimensions enable filtering and aggregation across similar resources.
- **Log Insights**: A query language for searching, filtering, and aggregating log data. Example: `fields @timestamp, @message | filter @message like /ERROR/ | stats count() by bin(5m)`. No external log aggregation tooling needed for moderate scale.
- **Alarms**: Evaluate a metric against a threshold over a time period. States: OK, ALARM, INSUFFICIENT_DATA. Actions: SNS (email, SMS, Lambda), Auto Scaling, EC2 Stop/Terminate/Reboot/Recover.
- **Embedded Metric Format (EMF)**: Emit custom metrics from logs. Structured JSON logs with embedded metric definitions are automatically extracted as CloudWatch metrics. Reduces cost (no PutMetricData calls) and ensures correlation between logs and metrics.
- **Contributor Insights**: Analyzes log data to identify top contributors (e.g., top IP addresses by request count, top error messages). Useful for identifying hot partitions and abusive clients.
- **ServiceLens**: Integrated view of traces (X-Ray), metrics, logs, and alarms in a single console. Provides end-to-end visibility for microservices.

## Why It Matters
CloudWatch is the default observability platform for AWS-based microservices. Every AWS service publishes metrics to CloudWatch automatically. Combined with X-Ray for distributed tracing and Contributor Insights for log analysis, it provides the three pillars of observability (metrics, logs, traces) without third-party tools. However, at high volume, CloudWatch Logs costs can be significant — many teams use a tiered strategy (CloudWatch for operation, third-party for retention/analytics).

## Related Concepts
- [X-Ray](12-XRay.md) — Distributed tracing, integrated with CloudWatch ServiceLens
- [Lambda](04-Lambda.md) — Lambda automatically publishes invocation metrics, duration, errors, throttles to CloudWatch
- [API Gateway](05-API-Gateway.md) — Publishes 4xx/5xx counts, latency, cache hit ratio, and execution logs

---

## Mental Model
The control room of a power plant (CloudWatch dashboard). Walls of gauges (metrics) show temperature, pressure, and output. Logs (operator notes) record every event. Alarm panels light up when any gauge passes a danger threshold. The operator can see everything in one place, drill into anomalies, and trigger automated responses (shut down a valve, spin up a backup generator) when alarms fire.
