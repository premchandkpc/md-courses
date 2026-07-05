# 01-DDD-Basics

Domain-Driven Design is a software methodology that aligns code structure with business domain models, introduced by Eric Evans in 2003. It bridges the gap between domain experts and developers through a shared understanding of the problem space. DDD is especially powerful in microservices because it provides clear heuristics for decomposing a system into bounded contexts.

## Overview
DDD splits into two layers: **strategic design** (bounded contexts, context maps, ubiquitous language) and **tactical design** (entities, value objects, aggregates, events, services, repositories). Strategic design answers *which* boundaries to draw; tactical design answers *how* to model within each boundary. Domains are classified as **core** (competitive advantage), **supporting** (necessary but not differentiating), or **generic** (off-the-shelf solutions).

## Key Characteristics
- **Strategic vs Tactical**: Strategic DDD defines context boundaries and relationships; tactical DDD provides building blocks for the model inside each context.
- **Domain Classification**: Core domains get custom, well-crafted models. Supporting domains get simpler implementations. Generic domains often use existing software.
- **Iterative Modeling**: The model evolves continuously as the team deepens its understanding of the business.
- **Model-Driven Design**: The code is the model — every term in the code has a precise business meaning.

## Why It Matters
Without DDD, microservice boundaries tend to follow technical layers (UI → API → data) rather than business capabilities, leading to chatty, coupled services that are hard to evolve. DDD provides a language for splitting along domain boundaries, yielding services that change independently.

## Related Concepts
- [Bounded Context](03-Bounded-Context.md) — the primary strategic pattern for drawing service boundaries
- [Ubiquitous Language](02-Ubiquitous-Language.md) — the shared vocabulary that makes DDD work
- [Entities](04-Entities.md) — objects with identity, a tactical building block

---

## Mental Model
Think of DDD like mapping a city. Strategic DDD draws district boundaries (bounded contexts). Tactical DDD decides what buildings go inside each district (entities, value objects) and how they connect (services, events). The map is useless if it doesn't match how people actually navigate the city — just as the model is useless if it doesn't match how domain experts think about their work.
