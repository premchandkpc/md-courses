# 04-Lambda

AWS Lambda is a serverless compute service that runs code in response to events and automatically manages the underlying compute resources. Lambda is the simplest execution model in AWS — upload code, set a trigger, and it scales from zero to thousands of concurrent executions with no infrastructure management.

## Overview
Lambda runs functions (Node.js, Python, Java, Go, Ruby, .NET, or custom runtimes) in response to triggers: API Gateway requests, S3 events, SQS messages, DynamoDB streams, CloudWatch scheduled events, and more. Each invocation runs in its own sandbox with allocated memory (128MB–10GB) and a maximum execution duration of 15 minutes. Lambda scales concurrency automatically — each incoming request gets its own execution environment, up to the regional concurrency limit (default 1000, adjustable).

## Key Characteristics
- **Event-driven and stateless by design**: Lambda functions receive events, process them, and terminate. Any state must be stored externally (DynamoDB, S3, ElastiCache). No local filesystem persistence between invocations.
- **Cold starts**: When a new execution environment is provisioned, there's a startup delay (cold start). This adds latency to sporadic invocations. Provisioned Concurrency keeps environments warm for predictable latency.
- **Concurrency limits**: The account-level concurrency limit caps how many functions can run simultaneously. Reserved concurrency guarantees capacity for critical functions. Burst concurrency provisions environments in waves (500–3000 per minute per region).
- **Pay-per-invocation**: Billed on requests (first 1M free) and duration in GB-seconds. Idle functions cost nothing. This makes Lambda ideal for variable, spiky, or low-traffic workloads.
- **15-minute timeout**: Lambda is not suited for long-running processes. Tasks exceeding 15 minutes need ECS, EKS, or a Step Functions workflow that chains Lambda executions.
- **Layered architecture**: Lambda layers provide shared code (SDKs, utilities) across functions. Extensions integrate monitoring agents (Datadog, New Relic) without code changes.

## Why It Matters
Lambda enables extreme operational simplicity. A microservice can be a single function behind API Gateway — no servers, no containers, no orchestration. Lambda fits perfectly for event-driven architectures, data processing pipelines, webhook handlers, and as glue between AWS services. Combined with SQS, SNS, and DynamoDB Streams, it forms the foundation of serverless microservices.

## Related Concepts
- [API Gateway](05-API-Gateway.md) — Common front-end for Lambda-based HTTP APIs
- [SQS](06-SQS.md) — Event source for Lambda; Lambda polls SQS and processes messages in batches
- [Horizontal Scaling](13-Scalability/01-Horizontal-Scaling.md) — Lambda achieves perfect horizontal scaling: each request gets its own environment

---

## Mental Model
A food truck that appears whenever someone calls and places an order. The truck arrives, cooks your specific meal, serves you, and drives away. You pay only for what you ordered. If 100 people call simultaneously, 100 trucks appear — each handles one customer, then disappears. If nobody calls, zero trucks, zero cost.
