# 08-Backward-Compatibility

Backward compatibility means a new version of a service API can serve existing consumers without breaking them. Consumers written against the old contract continue to work unmodified.

## Overview

The goal of backward compatibility is to avoid version bumps — and the operational burden of running multiple versions — by making changes that old clients can tolerate. The core rules are simple: never remove or rename a field, never make an optional field required, and never tighten validation rules. When all changes are backward-compatible, a single API version can serve all consumers indefinitely.

## Key Characteristics

- **Add Only**: New fields, new endpoints, new enum values — these are safe additions. Old clients ignore fields they don't understand (if the system is designed to tolerate unknown fields).
- **Never Remove**: Removing a field, endpoint, or enum value is a breaking change. Deprecate instead, and remove only when telemetry shows zero usage.
- **Loosen Input, Tighten Output Carefully**: Making an input field optional (loosening) is backward-compatible. Making an output field required (tightening) is not — old clients may not be ready for it.
- **Tolerant Reader Pattern**: Services should ignore unknown fields in requests/responses. This is the implementation pattern that enables add-only evolution.

## Why It Matters

Backward compatibility is the difference between a system that evolves smoothly and one that requires constant coordinated deploys. In microservices, where hundreds of services may depend on each other, breaking changes cascade catastrophically. Strive to design APIs that can evolve through additive changes only — this is the "expand and contract" pattern.

## Related Concepts

- [07-Service-Versioning](07-Service-Versioning.md) — versioning is the fallback when backward compatibility cannot be maintained
- [10-Schema-Evolution](10-Schema-Evolution.md) — the schema evolution rules that implement backward compatibility
- [09-Contract-Driven-Development](09-Contract-Driven-Development.md) — consumer contracts encode compatibility expectations

---

## Mental Model

Backward compatibility is like renovating a house while tenants live in it. You can add a new room (addition), repaint walls (cosmetic change), or upgrade the water heater (internal change). But you can't move the front door or remove the staircase — the tenants need those to keep living their lives. Your API consumers are the tenants.
