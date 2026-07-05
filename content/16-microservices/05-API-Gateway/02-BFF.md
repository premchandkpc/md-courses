# Backend For Frontend (BFF)

A dedicated API gateway layer per client type (mobile, web, IoT) that exposes client-optimized endpoints rather than a one-size-fits-all API. Each BFF knows exactly what data its target client needs and how that client consumes it.

## Overview

The BFF pattern acknowledges that a mobile app has fundamentally different API needs than a browser SPA or a smart TV. A mobile BFF might batch multiple data sources into a single JSON response to minimize radio wake-ups, while a web BFF might stream HTML fragments. Each BFF is owned by the same team that builds the client, allowing parallel evolution without cross-team coordination.

## Key Characteristics

- **Client-Tailored APIs**: Each BFF returns exactly the data shape and size its client needs — no over-fetching or under-fetching.
- **Team Alignment**: The team owning the client also owns its BFF, reducing coordination overhead and enabling rapid iteration.
- **Isolated Evolution**: Changes to one client's BFF don't risk breaking another client — a mobile BFF can be refactored without touching the web BFF.

## Why It Matters

A generic API Gateway forces all clients to consume the same endpoints, leading to bloated responses (mobile pays for desktop data) or multiple round-trips. BFFs eliminate this tension by letting each client's backend evolve independently. They also reduce coupling — the mobile team can change its data aggregation strategy without coordinating with the web team or the underlying microservice owners.

## Related Concepts

- [API Gateway](01-API-Gateway.md) — The general pattern that BFF specializes.
- [Aggregator](03-Aggregator.md) — BFFs often use aggregation to merge multiple service responses.
- [GraphQL](../04-frontend/..md) — An alternative approach where clients query exactly the fields they need.

## Mental Model

Imagine a restaurant with three different menus: a printed menu for dine-in guests, a mobile app menu for takeout orders, and an oral menu for drive-through. Each menu presents the same kitchen (microservices) but organized differently for the specific customer type. The BFF is the waiter who translates each menu format into kitchen orders.
