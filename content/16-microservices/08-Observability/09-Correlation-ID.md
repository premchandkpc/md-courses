# 09-Correlation-ID

A correlation ID is a unique identifier that propagates through all services involved in processing a single request. It ties together logs, traces, metrics, and error reports across distributed systems, enabling operators to reconstruct the full lifecycle of a request.

## Overview

When a request enters the system at the API gateway, a correlation ID (often a UUID) is generated and passed via HTTP headers (commonly `X-Request-ID` or `X-Correlation-ID`). Every downstream service includes this ID in its log entries, trace spans, and error responses. If the request fails, the correlation ID is returned to the client and logged on the server, providing a single key to look up the entire request path in the observability pipeline.

## Key Characteristics

- **Generation Point**: Created at the system boundary (API gateway, load balancer, ingress controller) and propagated throughout the request lifecycle.
- **Header Propagation**: Passed via standard HTTP headers (`X-Request-ID`, `X-Correlation-ID`, `X-Trace-ID`). W3C Trace-Context (`traceparent`) is the emerging standard.
- **Log Integration**: Every log line includes the correlation ID as a structured field (e.g. `correlation_id=abc-123`). Log aggregation tools filter by this field to show all logs for a single request.
- **Error Responses**: When a request fails, the correlation ID is returned to the client in the response body or header, enabling the client to reference it in support tickets.
- **Thread-Local Storage**: In synchronous request processing, the correlation ID is stored in thread-local or request-scoped context for automatic inclusion in log entries.
- **Async Propagation**: For asynchronous processing (message queues, background jobs), the correlation ID is carried in message headers and restored when the message is consumed.

## Why It Matters

Without correlation IDs, debugging a request that spans 5 services requires manually searching timestamps across 5 different log streams, guessing which log entries belong to the same request. A correlation ID collapses this to a single search query: "show me every log entry with `correlation_id=abc-123` across all services."

## Related Concepts

- [Logging](01-Logging.md) — The correlation ID is the first field added to structured log output in any microservice deployment.
- [Tracing](06-Tracing.md) — The trace ID serves as the correlation ID; in OpenTelemetry, the `trace_id` field fulfills this role.
- [API Gateway](../06-API-Gateway/01-API-Gateway.md) — The API gateway is typically responsible for generating the initial correlation ID for incoming requests.

---

## Mental Model

A correlation ID is a package tracking number. When you order something, the courier assigns a tracking number at the first scan. Every facility the package passes through scans and records that number. If the package is lost, you give the tracking number to support, and they locate every scan along the route. Without it, they'd ask "when did you order, what did it look like, which truck..." — a guessing game across the entire supply chain.
