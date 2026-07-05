# 06-Aggregates

An Aggregate is a cluster of associated objects (entities and value objects) treated as a single unit for data changes. Each aggregate has a root entity that acts as the sole entry point for all operations. The aggregate boundary defines transactional consistency — all invariants inside the boundary must be satisfied on every write.

## Overview
Aggregates solve the problem of consistency in complex domain models. Without aggregates, any object could directly reference and modify any other object, creating an entangled web of relationships. The aggregate root controls access: external objects can only reach internal objects by going through the root. This controls complexity and makes transactional behavior predictable.

## Key Characteristics
- **Aggregate Root**: The root entity is the only object external clients can hold references to. It enforces invariants and delegates work to internal objects.
- **Consistency Boundary**: All rules and invariants within the aggregate must be correct after every transaction. This defines the atomic update unit.
- **Identity Scope**: Aggregate root IDs are globally unique. Internal entity IDs need only be unique within the aggregate.
- **One Repository per Aggregate**: Each aggregate type has exactly one repository for persistence operations.
- **Small by Default**: Start with small aggregates. A common mistake is making aggregates too large, which creates contention in concurrent systems.

## Why It Matters
Aggregates map directly to transactional boundaries in microservices. Each aggregate represents a unit of work that must be consistent. In distributed systems, this prevents the "distributed transaction" trap — if two aggregates must stay consistent, they belong in the same service, or you use eventual consistency via domain events between services.

## Related Concepts
- [Entities](04-Entities.md) — aggregate roots are always entities
- [Value Objects](05-Value-Objects.md) — common components within aggregates
- [Repositories](07-Repositories.md) — persistence interface for loading and saving aggregates
- [Domain Events](10-Domain-Events.md) — used for eventual consistency across aggregates
- [Bounded Context](03-Bounded-Context.md) — aggregates live within a bounded context

---

## Mental Model
An aggregate is like a company with a CEO (the root). External parties cannot walk into any department and give orders — they must go through the CEO. The CEO ensures the company stays consistent (budget checks out, headcount approved, etc.). If you need to talk to someone inside, you ask the CEO. The company's internal structure can change, but the CEO is always the single point of contact.
