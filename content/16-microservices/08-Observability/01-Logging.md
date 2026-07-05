# 01-Logging

Logging is the emission of timestamped event records from a running service. It is the most basic form of observability and the first tool engineers reach for when debugging, but it requires structure and discipline to be useful at scale.

## Overview

In microservices, logs are produced by every instance of every service. Without a centralized logging pipeline, operators would need to SSH into hundreds of containers to find relevant entries. Production logging mandates structured JSON output to stdout/stderr, log levels that are honored in configuration, and correlation IDs that connect log entries across service boundaries.

## Key Characteristics

- **Log Levels**: DEBUG (diagnostic, typically disabled in production), INFO (normal operational events), WARN (unexpected but non-fatal), ERROR (failure that requires attention), FATAL (unrecoverable, process will exit).
- **Stdout/Stderr**: Logs are written to standard output (INFO) and standard error (ERROR). The execution environment (Docker, Kubernetes) captures these streams and forwards them to a log aggregator.
- **Centralized Aggregation**: Logs from all instances flow to a central store (Elasticsearch, Loki, CloudWatch, Splunk) for search and analysis.
- **Log Rotation**: The service does not rotate logs — the container runtime or log shipper handles rotation to prevent disk exhaustion.
- **Rate Limiting**: High-volume log statements (especially DEBUG) must be rate-limited to avoid overwhelming the log pipeline or incurring excessive storage costs.
- **PII Protection**: Personally identifiable information must be redacted before logs leave the service to comply with privacy regulations (GDPR, CCPA).

## Why It Matters

Logs are the primary tool for post-mortem analysis, error investigation, and audit trails. Without structured logging and centralized aggregation, finding the root cause of a production issue becomes a needle-in-a-haystack exercise across hundreds of containers.

## Related Concepts

- [Structured Logging](02-Structured-Logging.md) — The evolution from unstructured text to JSON-structured logs with a consistent schema.
- [Correlation ID](09-Correlation-ID.md) — A unique ID propagated through all services in a request chain, enabling log correlation across services.
- [Metrics](03-Metrics.md) — Logs record events; metrics aggregate counts and distributions. Both are needed for full observability.

---

## Mental Model

Logging is an airplane's flight data recorder. It continuously records events (engine telemetry, pilot actions, system alerts) to a durable stream. When something goes wrong, investigators replay the recorder to reconstruct the sequence of events. Without it, you only know the plane crashed — not why.
