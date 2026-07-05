# 09-Application-Services

An Application Service is a thin, stateless coordinator that orchestrates domain logic, manages transactions, and handles cross-cutting concerns like security and logging. Application services contain zero business logic — they delegate all domain decisions to entities, value objects, domain services, and aggregates.

## Overview
Application services are the entry point to the domain layer from the outside world (controllers, message handlers, scheduled tasks). They receive a request (a DTO or command), fetch the necessary aggregates from repositories, invoke domain logic on those aggregates or via domain services, persist changes, and publish any resulting domain events. The application service's job is to *coordinate*, not to *decide*.

## Key Characteristics
- **Thin**: Application services are minimal. If you see an `if` statement with business meaning in an application service, the logic likely belongs in the domain.
- **Coordinator**: They fetch, invoke, persist, and publish — in that order. They do not compute prices, validate rules, or make business decisions.
- **Transaction Manager**: The application service opens and commits a transaction (or a unit of work). If something fails, it rolls back.
- **DTO Translation**: They translate between inbound DTOs/commands and domain objects, and between domain results and outbound DTOs/response objects.

## Why It Matters
In microservices, application services define the public API contract of each service. They are the thin layer that translates external requests into domain operations. Keeping them thin ensures that business rules live in the domain model where they are testable and reusable, not scattered across controllers and handlers. Changes to infrastructure (HTTP vs gRPC vs message queue) only affect the application service layer, not the domain.

## Related Concepts
- [Domain Services](08-Domain-Services.md) — the domain logic that application services call
- [Repositories](07-Repositories.md) — what application services use to fetch and persist aggregates
- [Domain Events](10-Domain-Events.md) — published by application services after domain operations
- [Entities](04-Entities.md) — the domain objects that application services work with

---

## Mental Model
An application service is like a restaurant host. The host seats guests (routes requests), hands them menus (prepares inputs), calls the chef (invokes domain logic), and delivers the food to the table (returns results). The host does not decide what ingredients go into the dish — that's the chef's job (domain logic). The host coordinates, the chef creates.
