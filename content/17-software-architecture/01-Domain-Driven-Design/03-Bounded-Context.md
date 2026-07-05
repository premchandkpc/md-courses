# 03-Bounded-Context

A Bounded Context is an explicit boundary around a domain model, defining where a particular ubiquitous language applies. Inside the boundary, all terms have precise, consistent meanings. Outside, the same term may mean something different. In microservices, each service typically owns exactly one bounded context.

## Overview
Bounded contexts are the primary output of strategic DDD. They decompose a large domain into manageable, loosely coupled subsystems. Communication between contexts happens through defined translation mechanisms (context maps). The most common mistake is making contexts too large (monolithic) or letting them leak into each other through shared databases or models.

## Key Characteristics
- **Explicit Boundary**: The context defines what is inside and what is outside. Models inside are consistent; models outside are irrelevant or translated.
- **One Ubiquitous Language per Context**: Each context has its own language. "Order" in the Sales context may mean "confirmed purchase" while in the Shipping context it means "package to deliver."
- **Autonomous Model**: A bounded context owns its data, its schema, and its logic. It does not share internal models with other contexts.
- **Integration via Translation**: Communication between contexts uses explicit translators — anti-corruption layers, published language, or events.

## Why It Matters
Bounded contexts map directly to microservice boundaries. A well-identified bounded context becomes a single service with its own database, deployment pipeline, and team ownership. This alignment prevents the "distributed monolith" anti-pattern where services share databases, shared models, or deep synchronous dependencies.

## Related Concepts
- [Context Mapping](11-Context-Mapping.md) — the relationships between bounded contexts
- [Ubiquitous Language](02-Ubiquitous-Language.md) — the language that lives inside a bounded context
- [DDD in Microservices](12-DDD-in-Microservices.md) — how bounded contexts decompose into services
- Aggregate — the transactional boundary *inside* a bounded context

---

## Mental Model
A bounded context is like a country with its own laws, language, and currency. Inside the country, everyone uses the same rules. When you cross the border, you must convert money, translate documents, and follow different laws. The border protects each country's internal consistency — just as a bounded context protects each domain model's integrity.
