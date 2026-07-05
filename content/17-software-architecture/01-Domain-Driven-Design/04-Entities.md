# 04-Entities

An Entity is an object defined by its identity rather than its attributes. Entities have a continuous lifecycle and can change state over time while remaining the same object. Examples include User, Order, Invoice, and Product — things that must be tracked and distinguished from one another.

## Overview
Entities form the backbone of most domain models. Two entities with identical attribute values are still different objects if they have different IDs. Equality is determined by identity, not by field comparison. Entities are mutable — their state changes as the domain process progresses, but their identity stays constant.

## Key Characteristics
- **Identity Continuity**: An entity persists as the same object across state changes and even persistence. A User who changes their name and email is still the same User.
- **Mutable State**: Entities change over time. An Order progresses from "pending" to "shipped" to "delivered" — it remains the same Order.
- **Identity Comparison**: Equality is checked via ID, not attributes. The entity type and its ID together distinguish instances.
- **Lifecycle**: Entities are created, updated, read, deleted, and sometimes archived. The identity survives the entire lifecycle.

## Why It Matters
In microservices, entities define what each service is responsible for tracking. The Billing service owns Invoice entities; the Shipping service owns Shipment entities. Getting entity identity right prevents data duplication and synchronization nightmares across services. Each service should be the authoritative source for its entities' identities.

## Related Concepts
- [Value Objects](05-Value-Objects.md) — objects without identity, complementary to entities
- [Aggregates](06-Aggregates.md) — entities often serve as aggregate roots
- [Repositories](07-Repositories.md) — persistence access to entities and aggregates

---

## Mental Model
A person with a government-issued ID number is an entity. They may change their name, address, job, and appearance — but they are still the same person. The ID number is what matters. In contrast, the dollar amount in their wallet is a value object: swap one $20 bill for another $20 bill, and nothing meaningful changes.
