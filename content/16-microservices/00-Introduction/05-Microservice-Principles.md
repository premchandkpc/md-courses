# 05-Microservice-Principles

Core design principles that guide the creation and evolution of microservices architectures. These principles help teams make consistent architectural decisions.

## Overview

Microservice principles derive from years of distributed systems experience. They provide a north star for design decisions, helping teams avoid common pitfalls while maintaining velocity.

## Core Principles

- **Bounded Context**: Each service maps to one domain boundary. The same "Customer" concept may differ between Sales and Support contexts.
- **Database per Service**: Each service exclusively owns its data store. No other service accesses its database directly — only via the service's API.
- **Design for Failure**: Assume network failures, latency spikes, and process crashes. Use circuit breakers, retries, timeouts, and bulkheads.
- **Automate Everything**: CI/CD, infrastructure-as-code, automated testing, and canary deployments are required, not optional.
- **Hide Internal Implementation**: Services communicate via well-defined APIs, never exposing internal data models or technology choices.
- **Decentralize Governance**: Each team chooses its own tech stack and evolution pace, within agreed API contracts.
- **Observability by Default**: Every service exposes metrics, structured logs, and distributed tracing from day one.

## Why It Matters

Principles compensate for the complexity that microservices introduce. Without them, microservices degrade into a "distributed monolith" — all the operational cost of microservices with none of the autonomy benefits.

## Related Concepts

- [What is a Microservice](/16-microservices/00-Introduction/00-What-is-Microservice.md)
- [Twelve-Factor App](/16-microservices/00-Introduction/04-Twelve-Factor-App.md)
- [Bounded Context](/17-software-architecture/01-Domain-Driven-Design/03-Bounded-Context.md)
- [Database per Service](/16-microservices/02-Service-Design/04-Database-Per-Service.md)

---

## Mental Model

Microservice principles = House-building codes. You could build a house without following building codes, and it might even stand for a while. But when the first storm hits (outage, traffic spike, team change), the house that followed codes survives while the one that didn't collapses. The codes feel like bureaucracy until they save your building.
