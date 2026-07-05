# 12-XRay

AWS X-Ray is a distributed tracing service that helps developers analyze and debug microservices applications. X-Ray traces requests as they travel through AWS services, providing an end-to-end view of request flow, latency breakdowns, and error propagation.

## Overview
X-Ray traces requests by tracking them with trace IDs from entry to exit. Each service along the path sends trace data (segments) to X-Ray, including timing data, annotations, metadata, and error information. The X-Ray console displays a service map (nodes for each service, edges for connections) and a trace timeline (per-request waterfall view showing each segment's duration). X-Ray integrates natively with Lambda, API Gateway, ECS, EKS (via the X-Ray sidecar), ELB, and SNS/SQS.

## Key Characteristics
- **Trace segments and subsegments**: A segment represents the work done by a service (e.g., a Lambda invocation). Subsegments break down internal operations (database query, external HTTP call, S3 download). Each subsegment shows duration and errors.
- **Service map**: Auto-generated graph showing all traced services and their connections. Node colors indicate health (green = OK, red = error, yellow = throttled). Click a node to see traces for that service.
- **Annotations and indexes**: Annotations are key-value pairs indexed for searchable traces (e.g., annotation `customerId: 12345` lets you find all traces for that customer). Metadata is non-indexed data included in trace details.
- **Sampling rules**: Recording every trace is expensive and unnecessary. X-Ray uses sampling: a configurable rate (e.g., 1 request per second + 5% of additional requests). Reservoir sampling ensures diverse traces are captured. Custom sampling rules can prioritize high-value paths (e.g., payment endpoints).
- **Trace IDs propagate across services**: X-Ray injects trace headers into HTTP requests and propagates them via the SDK. Services downstream that also use X-Ray participate in the same trace. Lambda integrates automatically — if the caller has X-Ray headers, the Lambda trace continues the same trace.
- **Integration with CloudWatch**: ServiceLens combines X-Ray traces with CloudWatch metrics and logs. Click from a trace segment to the corresponding CloudWatch log. This correlation is critical for debugging — "this request was slow, what was the log context?"

## Why It Matters
In a microservices architecture, a single user request can traverse 5–15 services. Without distributed tracing, debugging latency or errors is nearly impossible — you don't know which service caused the problem. X-Ray provides a unified view across service boundaries. It answers: "Which service is the slowest? Where do errors originate? What does the dependency graph look like?" For teams adopting observability, X-Ray is the tracing pillar alongside CloudWatch (metrics) and logs.

## Related Concepts
- [CloudWatch](11-CloudWatch.md) — Metrics and logs that complement X-Ray traces in ServiceLens
- [Lambda](04-Lambda.md) — X-Ray integration is automatic with Lambda: no code changes needed
- [API Gateway](05-API-Gateway.md) — API Gateway can generate trace IDs and propagate them to backend services

---

## Mental Model
A package delivery service tracks every package from origin to destination (trace). At each sorting facility (service), the package is scanned: arrival time, processing time, departure time (subsegments). The tracking system (X-Ray console) shows a map of all facilities and the routes packages take (service map). When a package is delayed, you see exactly which facility caused the delay and how long it took at each step.
