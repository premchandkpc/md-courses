# Chain of Responsibility

The Chain of Responsibility pattern passes a request through a sequence of handlers, where each handler decides whether to process the request or forward it to the next handler. It is the backbone of middleware pipelines in web frameworks.

## Overview
In a chain, each handler implements two operations: process the request if applicable, and pass it to the next handler. Handlers are linked in a ordered sequence. In microservices, this pattern structures request processing pipelines — incoming requests pass through authentication, authorization, input validation, rate limiting, request logging, and finally the business logic handler. Any handler can short-circuit the chain by returning a response without forwarding.

## Key Characteristics
- **Sequential Processing**: Handlers execute in a defined order; each handler sees the request after the previous handler.
- **Handler Independence**: Each handler knows only its successor; it doesn't know about other handlers in the chain.
- **Short-Circuiting**: Any handler can terminate the chain by returning a response directly (e.g., auth failure).
- **Dynamic Composition**: Handlers can be added, removed, or reordered without modifying existing handlers.
- **Single Responsibility**: Each handler handles exactly one concern (e.g., only authentication, only rate limiting).

## Why It Matters
Without chain-based middleware, every service endpoint would need to manually call auth, validation, logging, and rate-limiting logic. This creates duplication and makes it easy to forget a step. The chain ensures consistent processing across all endpoints. Changing the order of processing (validate before auth vs auth before validate) is a configuration change, not a code change.

## Related Concepts
- [Decorator](04-Decorator.md) — both wrap behavior; Decorator wraps around a single target, Chain links multiple handlers linearly.
- [Pipeline](10-Pipeline.md) — transforms data through stages; Chain of Responsibility decides to process or pass.
- [Proxy](02-Proxy.md) — controls access to a single target; Chain of Responsibility applies multiple concerns in sequence.

---

## Mental Model
A customer support escalation line. Level 1 support (handler 1) handles basic issues. If they can't resolve it, they escalate to Level 2 (handler 2). Level 2 tries a deeper fix or escalates to Level 3 (engineer). Each level decides independently whether to resolve or pass along. The customer only knows someone is handling their issue — they don't know which level is current or how many levels exist.
