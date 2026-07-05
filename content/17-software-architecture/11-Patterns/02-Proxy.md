# Proxy

A Proxy acts as a surrogate or placeholder for another service to control access, add caching, logging, authentication, or lazy initialization. The caller interacts with the proxy as if it were the real service.

## Overview
The Proxy pattern interposes an intermediary between a client and a target service. Unlike the Adapter (which changes the interface) or Decorator (which adds behavior to the same interface), a Proxy typically preserves the exact interface of the target while controlling how and when requests reach it. Common microservice proxies include API gateways, sidecar proxies, and reverse proxies that handle cross-cutting concerns centrally.

## Key Characteristics
- **Interface Preservation**: The proxy exposes the same interface as the target service; callers cannot distinguish proxy from real service.
- **Access Control**: Enforces authentication, authorization, IP whitelisting, and rate limiting before forwarding.
- **Caching Layer**: Stores responses for idempotent requests, reducing load on the target service.
- **Lazy Initialization**: Defers connection setup or resource creation until the first actual request.
- **Request/Response Logging**: Captures telemetry data without modifying service code.
- **Load Balancing**: Distributes requests across multiple target instances transparently.

## Why It Matters
In microservices, cross-cutting concerns like auth, caching, and logging would otherwise be duplicated in every service. A proxy layer centralizes these responsibilities, allowing individual services to focus on business logic. Proxies also enable blue-green deployments, canary releases, and circuit breaking without service awareness.

## Related Concepts
- [Adapter](01-Adapter.md) — converts interfaces; Proxy preserves the interface.
- [Facade](03-Facade.md) — provides a simplified interface to a subsystem; Proxy preserves and controls the existing interface.
- [Decorator](04-Decorator.md) — dynamically adds behavior via wrapping; Proxy focuses on access control rather than augmenting behavior.

---

## Mental Model
A personal assistant who answers your phone calls. Callers speak to the assistant using the same greeting they'd expect from you. The assistant screens calls (access control), takes messages if you're busy (caching/queuing), and only forwards urgent matters. The caller never knows whether they're talking to you or the assistant.
