# Factory

A Factory creates service client instances without specifying concrete classes. It centralizes configuration, connection setup, and lifecycle management for external service dependencies.

## Overview
Microservice clients often need configuration: base URLs, timeouts, retry policies, TLS certificates, API keys. The Factory pattern encapsulates this creation logic so that consuming code asks for a "PaymentClient" or "NotificationClient" without knowing how it is constructed or configured. Factories can return different implementations based on environment, feature flags, or runtime context — enabling seamless switching between real services, mocks, or fallback stubs.

## Key Characteristics
- **Creation Centralization**: All construction logic for a service client lives in one place, not scattered across callers.
- **Configuration Encapsulation**: Timeouts, retries, auth tokens, and connection pools are configured once in the factory.
- **Implementation Swapping**: The factory can return a mock, a stub, or a real client based on environment or config.
- **Lifecycle Management**: Factories can manage connection pooling, health checks, and graceful shutdown of clients.
- **Abstract Return Type**: Callers depend on an interface, not on a concrete class — enabling loose coupling.

## Why It Matters
Without factories, every service that calls external dependencies hard-codes client creation logic. Configuration changes require hunting through dozens of files. Testing becomes difficult because real clients can't easily be swapped for mocks. A factory provides a single point of configuration change and makes dependency injection cleaner — services declare what they need, and the factory provides the right implementation.

## Related Concepts
- [Adapter](01-Adapter.md) — wraps existing systems; Factory creates new instances, possibly returning adapters.
- [Strategy](06-Strategy.md) — selects algorithms at runtime; Factory may return different Strategy implementations based on context.

---

## Mental Model
A vending machine. You press a button (request a "PaymentClient") and the machine handles everything: it accepts your coin (config), checks inventory (implementation availability), dispenses the product (creates the client instance). You don't care where the product came from or how the machine's internals work — only that you get a working instance of what you requested.
