# 05-Value-Objects

A Value Object is an immutable object defined entirely by its attributes. It has no conceptual identity — two value objects with the same attribute values are considered equal and interchangeable. Examples include Money, Address, Email, PhoneNumber, Color, and DateRange.

## Overview
Value objects are the workhorses of a domain model. They encapsulate primitive concepts into typed, self-validating objects that carry domain meaning. Because they have no identity, they can be freely created, discarded, and shared. Immutability ensures they are thread-safe and predictable — operations produce new instances rather than modifying existing ones.

## Key Characteristics
- **No Identity**: Two Email objects with "a@b.com" are identical. Replacing one with the other has no semantic difference.
- **Immutable**: State cannot change after creation. A Money object with amount=50 cannot be mutated to amount=100 — a new Money object must be created.
- **Self-Validating**: Value objects enforce their own invariants. An Email object rejects invalid formats at construction; a Money object ensures the currency code is valid.
- **Behaviorally Rich**: Value objects contain domain logic. Money can add, subtract, and convert currencies. Address can format itself for shipping labels.

## Why It Matters
Value objects eliminate primitive obsession — the anti-pattern of using raw strings, ints, and floats for domain concepts. A `String` for an email address misses validation, formatting, and comparison logic. An `Email` value object encapsulates all of it. In microservices, value objects are the primary payload in service-to-service communication (commands, events, responses).

## Related Concepts
- [Entities](04-Entities.md) — objects with identity, the counterpart to value objects
- [Aggregates](06-Aggregates.md) — aggregates contain entities and value objects
- [DDD Basics](01-DDD-Basics.md) — value objects are a tactical DDD building block

---

## Mental Model
A dollar bill is a value object. You don't care about *which* specific $20 bill you have — you care that it's $20. Swap it for another $20 bill and nothing changes. Compare this to a person (an entity): you care very much *which* person is your doctor, even if another doctor has the same qualifications.
