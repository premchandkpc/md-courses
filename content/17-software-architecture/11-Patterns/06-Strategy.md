# Strategy

The Strategy pattern encapsulates interchangeable algorithms and selects one at runtime. In microservices, this enables dynamic behavior switching — different payment providers, shipping carriers, authentication mechanisms, or data serialization formats.

## Overview
Strategy defines a family of algorithms, each implemented in its own class, all conforming to a common interface. The calling service selects which strategy to use at runtime based on context, configuration, or business rules. This decouples the algorithm selection logic from the algorithm implementation and allows new strategies to be added without modifying existing code.

## Key Characteristics
- **Algorithm Encapsulation**: Each strategy is a self-contained class or function with a uniform interface.
- **Runtime Selection**: The appropriate strategy is chosen dynamically — by feature flag, tenant config, A/B test, or input data.
- **Open/Closed**: New strategies can be added without changing the context that uses them.
- **Conditional Elimination**: Replaces long if/else or switch chains with polymorphic delegation.
- **Testable in Isolation**: Each strategy can be unit tested independently.

## Why It Matters
Microservices often need to support multiple providers, regions, or processing modes. A checkout service may need to switch between Stripe, PayPal, and Adyen depending on the user's country. A shipping service may route through FedEx, UPS, or DHL based on package weight. Hard-coding each path with conditionals creates tangled, hard-to-maintain code. Strategy cleanly separates each provider's logic behind a common interface.

## Related Concepts
- [Factory](05-Factory.md) — often paired with Strategy: a Factory creates the right Strategy instance based on config.
- [State](07-State.md) — State manages state-machine transitions; Strategy selects algorithms that don't track state.
- [Chain of Responsibility](09-Chain-of-Responsibility.md) — passes through handlers until one processes; Strategy selects exactly one algorithm to execute.

---

## Mental Model
A GPS navigation app with different route modes. You set your preference: fastest, shortest, avoid-tolls, or scenic. Each mode is a different routing algorithm (strategy) that takes the same inputs (start, end) and produces a route. You can switch strategies at any time without rebuilding the map. The app simply picks the right routing engine for your current need.
