# Aggregator

A service or gateway component that calls multiple downstream microservices in parallel, merges their responses, and returns a single unified payload to the client. It reduces chatty client-to-service communication.

## Overview

In a microservices architecture, a single client request often needs data from several services — user profiles, orders, inventory, and recommendations. Without an aggregator, the client must make multiple sequential calls, increasing latency and complexity. The aggregator receives the client's request, fans out calls to the relevant services in parallel (or in a defined dependency order), combines the results, and sends back one response.

## Key Characteristics

- **Parallel Fan-Out**: Independent service calls execute concurrently, keeping total latency close to the slowest service rather than the sum.
- **Response Composition**: Raw data from multiple sources is merged, filtered, or transformed into the exact shape the client needs.
- **Error Aggregation**: Partial failures are handled gracefully — the aggregator can return a best-effort response with error annotations rather than failing entirely.

## Why It Matters

Mobile clients and browser SPAs suffer when they must orchestrate multiple API calls themselves. An aggregator shifts this orchestration to the server side, where network latency between services is far lower than between client and server. It also encapsulates orchestration logic: when the underlying service topology changes, only the aggregator needs updating, not every client.

## Related Concepts

- [BFF](02-BFF.md) — A BFF commonly uses aggregation to build client-specific responses.
- [API Gateway](01-API-Gateway.md) — Gateways often include aggregation as a built-in feature.
- [GraphQL](../04-frontend/..md) — An alternative declarative approach to server-side data aggregation.

## Mental Model

An aggregator is like a personal shopper at a mall. You give them a list (one request), they visit multiple stores (microservices), pick up items from each, and return with everything in one bag. Without the shopper, you'd have to visit each store yourself, wait in each line, and carry separate bags home.
