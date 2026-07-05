# API Gateway

A single entry point that routes client requests to the appropriate internal microservices. It centralizes cross-cutting concerns like authentication, rate limiting, logging, and request transformation so individual services don't need to implement them.

## Overview

The API Gateway sits between clients and internal services, acting as a reverse proxy. Every client request hits the gateway first, which inspects the request, enforces security policies, and forwards it to the correct backend service. This pattern prevents clients from knowing about service topology and reduces the number of round-trips by consolidating multiple requests into one.

## Key Characteristics

- **Single Entry Point**: All external traffic converges through one hostname, simplifying client configuration and network security.
- **Cross-Cutting Concern Handler**: Authentication, TLS termination, rate limiting, request logging, and CORS are managed in one place.
- **Request Routing and Transformation**: Path-based or header-based routing directs traffic to the correct service; protocols, headers, and payloads can be rewritten.

## Why It Matters

Without a gateway, each microservice must separately handle auth, rate limiting, and TLS, leading to duplicated effort and inconsistent security. A gateway enforces uniform policies, abstracts service topology changes from clients, and provides a choke point for observability (metrics, tracing, access logs). It also mitigates the "N+1 problem" where a client would need to call many services to render a single page.

## Related Concepts

- [BFF](02-BFF.md) — Client-specific gateway variant that tailors APIs to each client type.
- [Rate Limiting](04-Rate-Limiting.md) — One of the key cross-cutting concerns enforced at the gateway.
- [Load Balancing](../06-Service-Discovery/07-Load-Balancing.md) — Gateways often distribute requests across service instances.

## Mental Model

Think of the API Gateway as a hotel concierge desk. Guests (clients) don't need to know which floor housekeeping is on or how to call maintenance directly — they just tell the concierge what they need, and the concierge routes the request, checks their room key (auth), and limits how many requests they can make at once.
