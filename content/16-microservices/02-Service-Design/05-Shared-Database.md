# 05-Shared-Database

The shared database anti-pattern occurs when multiple microservices read and write to the same database schema. While common in early microservices adoptions, it erodes the independence that microservices are meant to provide.

## Overview

A shared database couples services at the data layer — any schema change requires coordinated releases across teams, and any service can bypass another's business logic by writing directly to "its" tables. This creates a distributed monolith where services appear separate at the code level but are tightly bound at the data level.

## Key Characteristics

- **Schema Coupling**: A change to a table structure requires updates to every service that touches that table. Adding a column may break queries in unrelated services.
- **Bypassed Business Logic**: A service can read or modify data without going through the owning service's API, potentially violating invariants that the owning service enforces.
- **Single Point of Failure**: The shared database becomes a bottleneck and a high-value failure target. A schema migration that locks a table can take down multiple services simultaneously.
- **Technology Lock-In**: All services must use the same database technology, even if a different storage model would be more appropriate.

## Why It Matters

The shared database is the number-one indicator of a distributed monolith — a system that has the operational complexity of microservices with none of the independence benefits. Migration strategies include extracting one service at a time, introducing an API layer, and using database replication to decouple while maintaining availability. The goal is to reach database-per-service over time, not overnight.

## Related Concepts

- [04-Database-Per-Service](04-Database-Per-Service.md) — the target state this anti-pattern blocks
- [01-Service-Boundaries](01-Service-Boundaries.md) — shared databases indicate fuzzy boundaries
- [09-Contract-Driven-Development](09-Contract-Driven-Development.md) — contracts formalize the API as the only integration point

---

## Mental Model

A shared database is like two restaurants sharing the same kitchen. When the prep chef rearranges the walk-in, both restaurants' dinner service is affected. Each restaurant should have its own kitchen, just as each service should have its own database — connected by a well-defined doorway (the API).
