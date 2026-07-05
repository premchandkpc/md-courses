# Adapter

An Adapter converts the interface of one service into another interface that a client expects. It wraps legacy or incompatible systems to integrate them into a modern microservices ecosystem without modifying the original service.

## Overview
The Adapter pattern bridges mismatched interfaces between services. In microservices, it is commonly used to wrap legacy monoliths, third-party APIs, or protocols (e.g., SOAP → REST, XML → JSON) behind a consistent interface. The adapter translates calls and data formats transparently so that client services depend only on the target interface, not on the adapted system's quirks.

## Key Characteristics
- **Interface Translation**: Converts method signatures, parameter types, and return formats between source and target.
- **Legacy Isolation**: Wraps older systems that cannot be modified, allowing gradual migration without breaking consumers.
- **Protocol Bridging**: Enables communication across different transport protocols (HTTP, gRPC, AMQP, SOAP).
- **Transparent to Clients**: Consumers interact with a standard interface and have no knowledge of the adapted system.
- **Single Responsibility**: The adapter's sole job is conversion — it contains no business logic.

## Why It Matters
Legacy systems and third-party services rarely share the same interface contract. Without adapters, every consumer must handle protocol and format differences individually, creating tight coupling and duplicated conversion code. Adapters centralize translation logic, making the system easier to evolve. When a legacy system is decommissioned, only the adapter changes — consumers are unaffected.

## Related Concepts
- [Proxy](02-Proxy.md) — controls access rather than converting interfaces; Proxy preserves the same interface.
- [Facade](03-Facade.md) — simplifies a subsystem's interface; Facade deals with complexity, Adapter deals with mismatch.
- [Decorator](04-Decorator.md) — adds behavior dynamically rather than converting interfaces.

---

## Mental Model
A power plug adapter. You have a device with a European two-pin plug and a US socket expecting a flat prong. The adapter physically converts one shape to the other — no electrical transformation, just an interface match. Similarly, a service adapter translates calls from one contract to another so two systems that weren't designed to talk can still communicate.
