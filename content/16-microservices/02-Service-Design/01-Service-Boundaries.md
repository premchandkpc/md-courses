# 01-Service-Boundaries

Service boundaries define where one microservice ends and another begins, determining ownership of business capabilities and data. They are the single most impactful architectural decision in a microservices system.

## Overview

Boundaries should align with business capabilities and follow Domain-Driven Design (DDD) bounded contexts. Each bounded context encapsulates a distinct domain model, ubiquitous language, and set of responsibilities. When boundaries are well-drawn, teams can work independently on their services with minimal coordination.

## Key Characteristics

- **Business Capability Alignment**: Each boundary wraps a coherent business function (e.g., Inventory, Shipping, Payments) that a single team can own end-to-end.
- **DDD Bounded Contexts**: A formal DDD technique where you model the domain, identify sub-domains, and define context maps showing relationships between them.
- **Data Ownership**: A service boundary implies exclusive ownership of the data within that context. No other service accesses the database directly.
- **Communication Overhead**: Poor boundaries cause excessive cross-service calls. Well-drawn boundaries minimize coordination while keeping services autonomous.

## Why It Matters

Incorrect service boundaries lead to chatty communication, distributed monoliths, and painful refactors. Getting them right — even if it means starting coarser and splitting later — is the foundation of a sustainable microservices architecture. Boundaries also dictate team topology: Conway's Law ensures teams will organize around service boundaries.

## Related Concepts

- [02-Service-Granularity](02-Service-Granularity.md) — boundaries determine granularity
- [03-Single-Responsibility](03-Single-Responsibility.md) — each boundary should have one reason to change
- [04-Database-Per-Service](04-Database-Per-Service.md) — data ownership enforces boundaries

---

## Mental Model

Think of a well-organized warehouse: each aisle has a clear category (produce, dairy, frozen). Aisle boundaries keep items easy to find and restock without interfering with other aisles. If you mix unrelated items in the same aisle, both stocking and retrieval become chaotic — just like a microservice with fuzzy boundaries.
