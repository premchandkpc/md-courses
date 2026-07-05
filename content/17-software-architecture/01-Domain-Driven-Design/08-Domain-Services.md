# 08-Domain-Services

A Domain Service is a stateless object that encapsulates domain logic that does not naturally fit inside a single entity or value object. Domain services coordinate operations across multiple aggregates or entities within the same bounded context. They are named after business activities, not technical concerns.

## Overview
Not every piece of domain logic belongs on an entity or value object. Some operations involve multiple objects — for example, calculating a transfer fee between two accounts, or routing a shipment through multiple carriers. Domain services hold this cross-object logic. They are stateless (no mutable fields), operate on domain objects passed as parameters, and return results or side-effect the objects.

## Key Characteristics
- **Stateless**: Domain services have no mutable state. Any configuration they need is passed in or injected at construction (as dependencies, not state).
- **Domain-Focused**: The service name and methods use ubiquitous language. `PricingService.calculatePremium(policy)` is a domain service; `EmailService.sendEmail()` is an infrastructure service.
- **Cross-Object Logic**: When logic spans multiple aggregates or entities, a domain service is the right place.
- **Interface in Domain, Implementation in Infrastructure**: The interface is defined in the domain layer. The implementation may call repositories, external APIs, or other domain services.

## Why It Matters
Domain services prevent logic leakage into application services (which should be thin) or into entities (which become bloated). They make domain concepts explicit — a "funds transfer" domain service reveals the business rule that transferring between account types has different fee structures. In microservices, domain services operate within a single bounded context and are called by application services.

## Related Concepts
- [Application Services](09-Application-Services.md) — the orchestration layer that calls domain services
- [Entities](04-Entities.md) — one of the objects domain services operate on
- [Aggregates](06-Aggregates.md) — domain services coordinate across multiple aggregates
- [Repositories](07-Repositories.md) — domain services may fetch aggregates via repositories

---

## Mental Model
A domain service is like a tax accountant. The accountant doesn't *own* your money or your documents (those belong to you — you are the entity). But the accountant performs calculations that involve rules spread across many forms, receipts, and regulations. You bring the documents, the accountant applies the domain knowledge, and you get the result. The accountant is the domain service.
