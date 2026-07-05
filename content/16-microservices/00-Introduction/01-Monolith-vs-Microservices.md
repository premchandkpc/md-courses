# 01-Monolith-vs-Microservices

Choosing between monolithic and microservices architectures is one of the most consequential decisions in software design. The right choice depends on team size, organizational maturity, domain complexity, and scale requirements.

## Overview

A monolith is a single deployable unit where all functionality runs in one process. Microservices decompose this into multiple independently deployable services. Each approach has distinct tradeoffs.

| Aspect | Monolith | Microservices |
|--------|----------|---------------|
| Deployment | One artifact | N independent services |
| Scaling | Scale entire app | Scale per component |
| Team autonomy | Low (merge conflicts) | High (own service) |
| Tech stack | Single language | Polyglot |
| Latency | Low (in-process) | Network overhead |
| Data consistency | Strong (single DB) | Eventual (distributed) |
| Debugging | Simple stack trace | Distributed tracing needed |
| Testing | Simple integration | Complex contract tests |

## When to Choose Each

**Choose monolith when:**
- Small team (<10 engineers)
- Simple domain with clear boundaries
- Early-stage product (move fast, iterate)
- No clear service boundaries yet
- Operational overhead must stay low

**Choose microservices when:**
- Multiple teams need autonomy
- Services scale at different rates
- Domain has clear bounded contexts
- Need polyglot technology choices
- Team can invest in infrastructure

## Why It Matters

Starting with a monolith is often the right call — many successful systems (Amazon, Netflix, Uber) began as monoliths and decomposed only when the monolith became the bottleneck. Premature microservices add complexity without benefit.

## Related Concepts

- [What is a Microservice](/16-microservices/00-Introduction/00-What-is-Microservice.md)
- [SOA vs Microservices](/16-microservices/00-Introduction/02-SOA-vs-Microservices.md)
- [When NOT to use Microservices](/16-microservices/00-Introduction/03-When-NOT-to-use-Microservices.md)

---

## Mental Model

Monolith = A food truck. One cook does everything — taking orders, cooking, serving, handling payments. Simple, fast for small crowds. Microservices = A restaurant kitchen with specialized stations. Grill station, salad station, pastry station, expediter. When the dinner rush hits, you can add more grill cooks without retraining everyone. But you need more space, more coordination, and a lot more equipment.
