# Decorator

A Decorator dynamically adds behavior to a service call by wrapping it in an enclosing layer. Common microservice decorations include retry logic, caching, logging, metrics collection, and timeout enforcement.

## Overview
The Decorator pattern attaches additional responsibilities to an object or function call without modifying its code. In microservices, decorators are typically implemented as middleware layers or wrapper functions that intercept requests and responses. Multiple decorators can be stacked to compose rich behavior from simple building blocks — for example, wrapping a service client with logging → retry → circuit breaker → metrics in sequence.

## Key Characteristics
- **Composable Stacking**: Multiple decorators can be layered; each one wraps the previous and adds its own behavior.
- **Same Interface**: Each decorator implements the same interface as the underlying service call, making it transparent.
- **Open/Closed Principle**: New cross-cutting behavior is added via decorators without modifying existing service code.
- **Single Responsibility per Decorator**: Each decorator handles exactly one concern (e.g., only retry, only logging).
- **Order Sensitivity**: The sequence of decorators matters — a retry decorator should wrap the transport, not the metric counter.

## Why It Matters
Microservice clients need standardized cross-cutting behavior: retry failed calls, cache idempotent responses, log every request, track latency distributions. Without decorators, each service client must implement these inline, leading to duplication and inconsistency. Decorators let teams assemble a "chain of concerns" declaratively — often defined in configuration or DI setup rather than in business code.

## Related Concepts
- [Proxy](02-Proxy.md) — controls access; Decorator adds behavior while preserving the interface.
- [Chain of Responsibility](09-Chain-of-Responsibility.md) — each handler decides whether to process or pass; Decorator always passes and adds behavior on both sides.
- [Middleware](10-Pipeline.md) — often implemented as decorators around HTTP handlers in frameworks like Express, Gin, or Spring.

---

## Mental Model
Wrapping a gift. The gift itself is the core service call. You add wrapping paper (logging), then a ribbon (retry), then a bow (metrics). The recipient receives the same gift but with additional layers. Each layer can be added or removed independently without changing the gift inside.
