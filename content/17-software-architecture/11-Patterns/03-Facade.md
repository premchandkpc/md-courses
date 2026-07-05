# Facade

A Facade provides a simplified, unified interface to a set of services or subsystems. It hides the complexity of internal service interactions behind a single API endpoint.

## Overview
In a microservices architecture, a single user-facing feature often requires calls to multiple downstream services. The Facade pattern introduces an intermediary that orchestrates these calls, aggregates responses, and exposes a clean, coarse-grained API to clients. This reduces chattiness between frontends and backends and decouples clients from internal service topology. API gateways and BFF (Backend for Frontend) layers are practical applications of the Facade pattern.

## Key Characteristics
- **Simplification**: Exposes a single high-level interface instead of many fine-grained service endpoints.
- **Subsystem Hiding**: Clients have no knowledge of which internal services are called or how they interact.
- **Orchestration**: May coordinate multiple service calls, handle errors, and merge or transform responses.
- **Deployment Independence**: Internal services can be refactored, split, or replaced without changing the facade's contract.
- **Cross-Cutting Hook**: Auth, logging, and rate limiting can be applied once at the facade level.

## Why It Matters
Without a facade, frontend clients must understand the entire service topology — which service owns user data, which owns orders, which owns inventory. This creates tight coupling between UI and backend structure. A facade enforces encapsulation of service boundaries, reduces network round trips, and allows independent evolution of internal services.

## Related Concepts
- [Adapter](01-Adapter.md) — converts interfaces individually; Facade simplifies a whole subsystem.
- [Proxy](02-Proxy.md) — controls access to a single service; Facade orchestrates multiple services.
- [Pipeline](10-Pipeline.md) — sequential processing stages; Facade may internally use a pipeline to transform data.

---

## Mental Model
A hotel front desk. Guests don't need to know about housekeeping, maintenance, billing, or room service logistics. They call the front desk for anything — the desk routes to the right department, coordinates responses, and returns the result. The front desk is the facade for the entire hotel's operations.
