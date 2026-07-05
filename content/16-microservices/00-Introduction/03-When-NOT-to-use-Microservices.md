# 03-When-NOT-to-use-Microservices

Microservices are not always the right answer. Adopting microservices prematurely or unnecessarily adds complexity, cost, and operational burden that can destroy team velocity.

## Overview

Every distributed system tradeoff applies to microservices: network latency, data consistency, debugging complexity, and operational overhead. These costs are worth paying only when the benefits outweigh them.

## Red Flags

- **Small team (<15 engineers)** — A monolith lets a small team move faster than coordinating across microservices
- **Simple CRUD application** — Microservices add operational complexity with minimal benefit for basic data entry apps
- **No clear bounded contexts** — Without DDD-based service boundaries, you'll create a distributed monolith with all the costs and none of the benefits
- **Single scaling dimension** — If all parts of the system scale together, a monolith with horizontal scaling is simpler
- **Weak DevOps culture** — Without CI/CD, containerization, and monitoring maturity, microservices operations become unmanageable
- **Startup in discovery phase** — Premature decomposition slows iteration; monoliths let you pivot faster

## Why It Matters

Conway's Law works both ways: microservices force organizational structure that may not fit your team. The most successful microservices migrations (Amazon, Netflix, Spotify) started as monoliths and decomposed only when the monolith demonstrably constrained growth.

## Related Concepts

- [Monolith vs Microservices](/16-microservices/00-Introduction/01-Monolith-vs-Microservices.md)
- [Microservice Principles](/16-microservices/00-Introduction/05-Microservice-Principles.md)
- [Service Granularity](/16-microservices/02-Service-Design/02-Service-Granularity.md)

---

## Mental Model

Microservices are like having a dedicated team of specialists for every task. For building a backyard shed, you don't need an architect, structural engineer, electrician, plumber, and interior designer. You need one good carpenter. Microservices are for building skyscrapers, not sheds. Know which project you're on.
