# 04-GraphQL

GraphQL is a query language and runtime for APIs that lets clients request exactly the data they need, nothing more and nothing less. It was developed by Facebook to solve the problems of REST's under-fetching and over-fetching.

## Overview

In GraphQL, the client sends a query describing the exact shape and fields of the data it wants. The server responds with a JSON object matching that shape. A single GraphQL endpoint replaces multiple REST endpoints — the client controls the data it receives. This shifts data-fetching responsibility from the server to the client.

## Key Characteristics

- **Schema-First**: The GraphQL schema defines types, queries, mutations, and subscriptions. The schema is the contract between client and server, written in GraphQL Schema Definition Language (SDL).
- **Resolver Pattern**: Each field in the schema maps to a resolver function. Resolvers are composable and can fetch data from different sources. The GraphQL runtime executes resolvers, potentially batching or deduplicating them (DataLoader pattern).
- **Client-Driven Queries**: The client specifies what it needs. This eliminates over-fetching (getting more data than needed) and under-fetching (making multiple requests to gather complete data).
- **Batching via DataLoader**: A utility that batches and caches resolver calls within a single request, preventing the N+1 query problem common in GraphQL implementations.
- **Subscriptions**: Real-time updates via WebSocket. The client subscribes to an event and the server pushes data when the event occurs.

## Why It Matters

GraphQL is best used as a Backend-for-Frontend (BFF) layer — a thin gateway between the user interface and the microservices backend. It's powerful for frontend teams that need to iterate quickly on data requirements without coordinating with backend teams. However, GraphQL adds complexity: query cost analysis, rate limiting, and resolver performance optimization are harder than REST. It's not recommended for service-to-service communication.

## Related Concepts

- [02-REST](02-REST.md) — GraphQL is often compared to REST as an alternative
- [05-WebSockets](05-WebSockets.md) — transport for GraphQL subscriptions
- [12-Choosing-Communication](12-Choosing-Communication.md) — when to use GraphQL as BFF

---

## Mental Model

A REST API is like a prix fixe menu — you get a fixed selection of dishes (endpoints) with predetermined portions (response shapes). GraphQL is a buffet — you walk through with your plate (query) and pick exactly what you want. The buffet can be more efficient (no wasted food/data) but requires the diner (client) to be more engaged in the process.
