# 03-Single-Responsibility

The Single Responsibility Principle (SRP) applied to microservices: each service should have exactly one reason to change, aligned with a single business capability or actor.

## Overview

Originating from Robert C. Martin's SRP in software design — "A class should have only one reason to change" — this principle translates naturally to microservices. A service that handles payments should change only when payment logic changes, not because shipping rules or user profiles change. This isolates change impact, making deployments safer and faster.

## Key Characteristics

- **One Business Capability**: The service encapsulates a complete, coherent business function. Examples: "Inventory Service," "Notification Service," "Billing Service."
- **One Reason to Change**: Changes to business rules, data formats, or workflows within that capability only affect that one service. Other services remain untouched.
- **Clear Ownership**: A single team owns the service end-to-end, reducing coordination overhead and enabling fast iteration.
- **Small, Focused API Surface**: The service exposes a minimal set of operations that correspond to the business capability, not a grab-bag of unrelated functions.

## Why It Matters

SRP in microservices enables independent deployability — the core promise of the architecture. When each service has a single responsibility, teams can release changes without coordinating across organizational boundaries. It also improves system resilience: a bug in one service doesn't cascade into unrelated domains. Violating SRP typically manifests as a "mega-service" that requires multi-team coordination for any change.

## Related Concepts

- [01-Service-Boundaries](01-Service-Boundaries.md) — how to identify the right scope for each responsibility
- [02-Service-Granularity](02-Service-Granularity.md) — granularity is the practical expression of SRP
- [04-Database-Per-Service](04-Database-Per-Service.md) — data ownership reinforces single responsibility

---

## Mental Model

A restaurant kitchen has separate stations: grill, prep, pastry, garde manger. Each station has a single purpose. When the pastry chef changes a recipe, the grill chef doesn't stop work. Your services should be organized the same way — each responsible for one "dish" on the menu.
