# 06-API-First

API-first development means designing the API contract before writing any implementation code. The contract becomes the source of truth that server and client teams build against in parallel.

## Overview

In an API-first workflow, the team specifies the API using a formal description language — OpenAPI (Swagger) for REST, Protobuf for gRPC, or GraphQL SDL for GraphQL — and validates it with stakeholders before writing a single line of business logic. This contract serves as the single source of truth for both providers and consumers, enabling parallel development and early feedback.

## Key Characteristics

- **Contract as Source of Truth**: The API specification lives in version control, is reviewed like code, and drives documentation, mock servers, client SDK generation, and tests.
- **Parallel Development**: Client teams can develop against the contract or a mock server before the provider is implemented. This decouples delivery timelines.
- **Tooling Ecosystem**: OpenAPI generates server stubs, client libraries, API docs, and test harnesses. Protobuf generates strongly typed clients in any supported language.
- **Early Validation**: Design flaws are caught during contract review, not after implementation. This saves weeks of rework.

## Why It Matters

API-first forces the team to think from the consumer's perspective before being influenced by implementation convenience. It prevents the common anti-pattern where the API mirrors the internal database schema rather than serving the client's needs. In microservices, where each service has its own API, this discipline ensures consistency and usability across the system.

## Related Concepts

- [07-Service-Versioning](07-Service-Versioning.md) — versioning strategy should be part of the contract
- [09-Contract-Driven-Development](09-Contract-Driven-Development.md) — extends API-first to consumer-driven testing
- [02-REST](../03-Communication/02-REST.md) — common API-first contract format

---

## Mental Model

API-first is like signing a construction contract before hammering the first nail. The blueprints (the API spec) are agreed upon by everyone — architect, electrician, plumber — before any work starts. Changes to the blueprint are reviewed by all parties. Building without blueprints (implementation-first) guarantees costly rework.
