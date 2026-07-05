# 12-DDD-in-Microservices

Domain-Driven Design provides the theoretical foundation for decomposing a system into microservices. The core insight: a bounded context maps directly to a microservice boundary; each service owns its domain model, data, and business logic. DDD prevents the distributed monolith antipattern by giving architects a principled way to draw service boundaries.

## Overview
The mapping from DDD to microservices is straightforward but requires discipline. Each bounded context becomes one service (or a small cluster of closely related services). Each aggregate root within a context defines a transactional consistency boundary. Aggregates in different services communicate via domain events (eventual consistency) or via anti-corruption layers (synchronous calls). The ubiquitous language becomes the service's public API vocabulary.

## Key Characteristics
- **Bounded Context = Service Boundary**: Each microservice owns one bounded context. Service boundaries are business boundaries, not technical layers.
- **Database per Service**: Each service owns its data store. The database schema reflects the bounded context's model, not a shared enterprise model.
- **Eventual Consistency Across Services**: Domain events replace distributed transactions. Services converge to consistency asynchronously.
- **Anti-Corruption Layers for Integration**: When integrating with legacy systems or external services, an ACL protects the service's domain model.
- **Team Alignment**: Teams are organized around bounded contexts (inverse Conway maneuver). The team's span of ownership matches the service's scope.

## Key Characteristics (continued)
- **Small Aggregates for Performance**: Aggregates in microservices should be deliberately small to minimize contention and enable independent scaling.
- **Published Language**: Each service exposes a stable, versioned contract (API contracts, event schemas) that other services consume.

## Why It Matters
Without DDD, microservice decomposition is guesswork — based on entities, layers, or technology rather than business capabilities. The result is chatty services, shared databases, and coordination bottlenecks. DDD provides a repeatable, domain-driven decomposition process: understand the domain, identify bounded contexts, define context maps, implement aggregates within each context, and let domain events flow between them.

## Related Concepts
- [DDD Basics](01-DDD-Basics.md) — the foundational methodology
- [Bounded Context](03-Bounded-Context.md) — maps directly to service boundaries
- [Context Mapping](11-Context-Mapping.md) — defines service integration patterns
- [Domain Events](10-Domain-Events.md) — asynchronous communication between services
- [Aggregates](06-Aggregates.md) — transactional consistency within a service

---

## Mental Model
Think of a large corporation. Each department (Engineering, Sales, Support) has its own budget, data, and processes — they are bounded contexts. The corporation doesn't have a single massive database where every department sees everything. Instead, departments communicate through formal channels: reports (domain events), inter-department transfers (ACL), and shared service-level agreements (context maps). This is exactly how DDD-based microservices work.
