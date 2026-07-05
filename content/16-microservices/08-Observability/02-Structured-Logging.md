# 02-Structured-Logging

Structured logging emits log entries as structured data (JSON) rather than unstructured text, with a consistent schema that machines can parse, filter, and aggregate efficiently. It is the standard for production microservices.

## Overview

An unstructured log might say `"User 42 logged in from 192.168.1.1"`, requiring regex parsing to extract the user ID and IP. A structured log entry is a JSON object: `{"timestamp": "...", "level": "INFO", "message": "User logged in", "user_id": 42, "client_ip": "192.168.1.1", "trace_id": "abc-123"}`. This format enables exact field queries (`user_id:42`), automated dashboards, and alerting on specific field values without fragile parsing.

## Key Characteristics

- **Consistent Schema**: Every log entry includes standard fields: `timestamp`, `level`, `message`, `service`, `hostname`, `trace_id`, `span_id`, `environment`.
- **Contextual Fields**: Business-specific fields (user ID, order ID, error code) are added to the JSON payload without polluting the message string.
- **Machine-Parseable**: Tools like jq, LogQL, and Elasticsearch DSL can query and aggregate structured logs directly.
- **Structural Types**: Numbers, booleans, and nested objects are preserved as native types, not stringified.
- **Log Correlation**: `trace_id` and `span_id` fields link log entries across services and to distributed traces.
- **Zero-Allocation in Hot Paths**: High-performance logging libraries (slog, zap, zerolog) minimize heap allocations to avoid GC pressure on critical code paths.

## Why It Matters

Unstructured logs require fragile regex parsing for any automated analysis. When investigating an incident across 50 services, engineers need to query "find all ERROR-level logs with `order_id=5000` in the last 10 minutes" — a trivial query with structured logging and impossible with free-text.

## Related Concepts

- [Logging](01-Logging.md) — Structured logging is an evolution of basic logging; it adds schema and machine-readability.
- [Tracing](06-Tracing.md) — Structured logs carry `trace_id` and `span_id` fields that correlate log entries with distributed traces.
- [Correlation ID](09-Correlation-ID.md) — The correlation ID is included as a structured field to group logs by request across service boundaries.

---

## Mental Model

Structured logging is like a spreadsheet vs a paragraph. An unstructured log is a sentence: "John bought 3 apples for $5." A structured log is a spreadsheet row: `{customer: "John", item: "apple", quantity: 3, total: 5.00}`. You can sum the total column, filter by customer, or find the most-bought item — operations that require tedious parsing with the sentence format.
