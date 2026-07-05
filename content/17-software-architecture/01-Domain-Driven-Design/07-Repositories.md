# 07-Repositories

A Repository provides a collection-like interface for accessing domain objects from persistent storage, abstracting away the underlying data technology. Each aggregate type typically has exactly one repository. Repositories create the illusion of an in-memory collection of all objects of a given type.

## Overview
Repositories sit between the domain model and the persistence layer (database, cache, external API). They retrieve aggregates from storage, reconstitute them as in-memory objects, and persist changes back. The domain layer never deals with SQL queries, ORM sessions, or HTTP calls — it only calls repository methods with domain language like `findById()`, `save()`, or `remove()`.

## Key Characteristics
- **Per-Aggregate Repository**: One repository per aggregate root type. If you have an `Order` aggregate, you have an `OrderRepository`. No generic "repository for everything."
- **Collection Metaphor**: The repository feels like a collection — `add(order)`, `remove(order)`, `findById(id)`, `findByCriteria(criteria)`.
- **Persistence Ignorance**: The domain layer has no dependencies on databases, ORMs, or data formats. The repository interface lives in the domain; the implementation lives in infrastructure.
- **Full Object Retrieval**: Repositories return fully populated aggregate instances, not partial data. The caller should not need lazy loading or repeated queries.

## Why It Matters
Repositories keep the domain model clean and testable. Domain logic can be unit-tested by mocking repositories, without a real database. When the persistence technology changes (e.g., PostgreSQL to DynamoDB), only the repository implementations change — the domain model stays untouched. In microservices, repositories also encapsulate the boundary of data ownership for each service.

## Related Concepts
- [Aggregates](06-Aggregates.md) — repositories persist aggregates, the unit they work with
- [Entities](04-Entities.md) — the objects returned by repository queries
- [Application Services](09-Application-Services.md) — the caller that coordinates repository + domain logic

---

## Mental Model
A repository is like a library catalog. You don't enter the stacks and hunt for books — you ask the catalog. The catalog knows where every book is, how to retrieve it, and how to put it back. You get the book in your hands; you don't worry about which shelf it was on. The repository is that catalog for your domain objects.
