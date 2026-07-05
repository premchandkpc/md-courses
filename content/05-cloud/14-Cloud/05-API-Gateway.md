# 05-API-Gateway

AWS API Gateway is a fully managed service for creating, publishing, maintaining, monitoring, and securing APIs at any scale. It acts as the front door for microservices, handling request routing, authentication, throttling, caching, and response transformation.

## Overview
API Gateway supports three API types: REST APIs (full-featured, request/response transformation, API keys, usage plans), HTTP APIs (lower-latency, simpler, cheaper — ideal for Lambda proxies), and WebSocket APIs (bidirectional, persistent connections for real-time applications). APIs are defined in OpenAPI 3.0 or via the AWS console/CLI. API Gateway integrates with Lambda (proxy integration), HTTP backends (ALB, EC2, ECS), AWS services (Step Functions, SQS, SNS), and VPC-linked services via VPC Link.

## Key Characteristics
- **Request lifecycle**: Client → API Gateway endpoint → authorization (IAM, Cognito, Lambda authorizer, JWT) → request validation → integration (Lambda/HTTP) → response transformation → client.
- **Throttling and rate limiting**: Account-level and per-API throttling limits prevent abuse. Burst and rate limits are configurable. Usage plans associate API keys with throttling and quota limits for tiered access.
- **Caching**: API Gateway can cache responses with configurable TTL (30s–3600s). Cache capacity ranges from 500MB to 237GB. Reduces backend load for read-heavy endpoints.
- **CORS support**: Built-in CORS configuration for browser-based clients. Preflight OPTIONS requests are handled automatically when configured.
- **Stage-based deployments**: APIs are deployed to stages (dev, test, prod) with stage variables for environment-specific configuration. Canary deployments enable traffic shifting for testing.
- **Cost**: Pay per API call (REST: $3.50/M; HTTP: $1.00/M; WebSocket: $1.00/M) plus data transfer and cache hours. Very low cost for low-to-moderate traffic volumes.

## Why It Matters
API Gateway is the standard entry point for AWS-based microservices. It decouples clients from backend implementation — the same API endpoint can route to Lambda, ECS, or on-premises services without client changes. Its throttling, auth, and caching features offload cross-cutting concerns that would otherwise need to be built into every service.

## Related Concepts
- [Lambda](04-Lambda.md) — Most common integration target; API Gateway proxies HTTP requests to Lambda
- [CloudWatch](11-CloudWatch.md) — API Gateway publishes execution logs, access logs, and metrics (4xx/5xx counts, latency, cache hit ratio)
- [AWS](01-AWS.md) — API Gateway is the API management layer in the AWS ecosystem

---

## Mental Model
A hotel concierge desk (API Gateway). Guests (clients) bring requests — "book a tour," "recommend a restaurant." The concierge checks your ID (auth), verifies you're within your service limits (throttling), remembers common answers from a card (caching), and routes your request to the right department (backend). The concierge handles all the front-of-house concerns so each department focuses on its specialty.
