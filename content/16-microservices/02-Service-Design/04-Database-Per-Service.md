# 04-Database-Per-Service

The Database-Per-Service pattern mandates that each microservice owns its database exclusively. No other service or external client can access that database directly — all access goes through the service's API.

## Overview

This pattern is a cornerstone of microservices architecture because it enforces loose coupling at the data layer. Each service chooses the database technology best suited to its needs (relational, document, graph, key-value) without impacting other services. It also prevents "database integration" — the tight coupling that occurs when multiple services read and write the same tables.

## Key Characteristics

- **Exclusive Data Ownership**: The service is the sole gatekeeper for its data. Other services must call the owning service's API to read or modify data.
- **Technology Independence**: Each service can use PostgreSQL, MongoDB, Redis, or any database that fits its access patterns. There is no mandated stack.
- **Encapsulated Schema Changes**: Schema migrations happen within one service's deployment scope. No coordination with other teams is needed for adding columns or indexes.
- **Data Duplication**: Some data may be duplicated across services (e.g., a user's name in both the Order and Profile services). This is acceptable — each service owns its copy and its representation.

## Why It Matters

Database-per-service prevents the shared-database anti-pattern, which creates tight coupling and erodes the independence that microservices are meant to provide. It enables polyglot persistence, independent deployability, and team autonomy. The cost is increased complexity around data consistency — since a transaction can't span databases, you must use eventual consistency, sagas, or compensating transactions.

## Related Concepts

- [05-Shared-Database](05-Shared-Database.md) — the anti-pattern this replaces
- [09-Contract-Driven-Development](09-Contract-Driven-Development.md) — API contracts formalize what data the service exposes
- [10-Schema-Evolution](10-Schema-Evolution.md) — each service evolves its schema independently

---

## Mental Model

Each service is like a house with its own private fenced yard. You can have any kind of yard you want (pool, garden, patio) and change it whenever you like. If your neighbor needs something from your yard, they knock on your front door (the API) — they don't climb the fence.
