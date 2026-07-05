# 06-Trade-Offs

Microservices involve continuous tradeoff analysis. Every architectural decision exchanges one set of benefits for another set of costs. This file catalogs the most common tradeoffs and frameworks for reasoning about them.

## Complexity vs Autonomy
- **The tradeoff**: Monoliths are simpler (single process, single DB, single deploy) but create coupling. Microservices add complexity (network calls, distributed data, eventual consistency) but enable independent deployability and team autonomy.
- **Decision framework**: Start monolithic. Extract services only when you need independent deployability (different teams) or independent scaling (different resource profiles). Don't extract for extract's sake — each service boundary is a bet against future coupling.
- **Cost of wrong choice**: Premature microservices create accidental complexity (service choreography, debugging, orchestration). Staying monolith too long creates deploy bottlenecks and slow iteration cycles.

## Consistency vs Availability (CAP Theorem)
- **The tradeoff**: Strong consistency (CP) means all nodes see the same data at the same time, but the system may be unavailable during partitions. High availability (AP) means the system stays available during partitions, but data may be stale.
- **Decision framework**: Financial transactions → CP (strong consistency, use distributed transactions or sagas). Content feeds → AP (eventual consistency is fine). User profiles → CP within a region, AP across regions.
- **Cost of wrong choice**: CP for a social feed creates unacceptable latency and availability issues. AP for payment processing creates reconciliation nightmares and financial loss.

## Synchronous vs Asynchronous Communication
- **The tradeoff**: Sync (HTTP/gRPC) is simple, provides immediate feedback, and is easy to debug. Async (queues, events) decouples services, provides resilience through buffering, but adds latency, complexity, and eventual consistency.
- **Decision framework**: Queries (need an immediate answer) → sync. Commands (fire and forget) → async. Workflows spanning multiple services → async with sagas. Time-sensitive → sync. Failure-tolerant → async.
- **Cost of wrong choice**: Sync for cross-service workflows creates cascading failures and tight coupling. Async for simple CRUD creates unnecessary complexity and debugging difficulty.

## Database-per-Service vs Shared Database
- **The tradeoff**: Database-per-service gives clean boundaries, independent schema evolution, and no resource contention. Shared databases give simpler queries (joins across services), atomic transactions, and lower operational overhead.
- **Decision framework**: Core business data → database-per-service. Reporting/analytics → read replica that aggregates across services. High-cohesion services that always change together → consider merging into one service.
- **Cost of wrong choice**: Shared database services eventually merge into a distributed monolith. Database-per-service creates distributed transaction complexity for naturally coupled data.

## Event-Driven vs Request-Driven
- **The tradeoff**: Event-driven systems are decoupled, scalable, and support complex workflows through event chains. Request-driven systems are simpler, traceable, and easier to reason about — but create coupling between caller and callee.
- **Decision framework**: Process that needs auditing (order lifecycle) → event-driven. Simple CRUD with immediate response → request-driven. Fan-out to multiple consumers (notification sends) → event-driven.
- **Cost of wrong choice**: Event-driven for simple CRUD adds "event spam" and debugging overhead. Request-driven for complex workflows creates orchestration spaghetti.

## Orchestration vs Choreography (Sagas)
- **The tradeoff**: Orchestrated sagas (central coordinator) are easier to understand, monitor, and manage failure. Choreographed sagas (each service reacts to events) are more decoupled and scalable but harder to reason about overall system state.
- **Decision framework**: Few services (2-3), well-defined workflow → orchestration. Many services, flexible workflow → choreography. High compliance requirements → orchestration (easier to audit).
- **Cost of wrong choice**: Orchestration for highly dynamic workflows creates a fragile coordinator. Choreography for simple workflows makes the flow hard to trace.

## Related Concepts
- [01-Interview-Questions](01-Interview-Questions.md) — Interview questions exploring these tradeoffs
- [03-Architecture-Questions](03-Architecture-Questions.md) — Architectural reasoning based on tradeoff analysis
- [See also Tradeoffs in...]

---

## Mental Model
Tradeoff analysis is like deciding the number of doors in a house. One big room (monolith) is simple but everyone enters through the same door (deployment coupling). Adding more doors (services) lets people enter independently, but now you need more locks (security), more keys (service discovery), and people in different rooms can't easily share things (data sharing). There's no universally correct number of doors — it depends on how many people live there and what they do.
