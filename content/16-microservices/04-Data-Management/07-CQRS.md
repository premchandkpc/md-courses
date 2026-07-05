# 07-CQRS

Command Query Responsibility Segregation (CQRS) separates the data mutation path (commands) from the data reading path (queries), allowing each to use different models, databases, and optimization strategies. This is a natural fit for microservices where read and write workloads diverge.

## Overview
- Traditional CRUD uses a single model for reads and writes. CQRS splits them into commands (write operations that change state) and queries (read operations that return data).
- Commands are typically modeled as imperatives (e.g., "PlaceOrder", "UpdateInventory") and may return no data — only success/failure.
- Queries return data without side effects. The query model can be denormalized, cached, or projected from event streams.
- CQRS is often paired with Event Sourcing, where commands produce events that are projected into read-optimized views.

## Key Characteristics
- **Separate Read/Write Models**: The write model uses domain-optimized structures (normalized tables, aggregates). The read model uses query-optimized structures (materialized views, denormalized collections, search indexes).
- **Independent Scaling**: Read and write workloads can scale independently. High-traffic reads don't contend with writes, and vice versa.
- **Eventual Consistency**: The write model and read model are often eventually consistent. A command may update the write model, but the read model takes time to reflect the change.
- **Complexity**: CQRS introduces more moving parts — at least two models, a synchronization mechanism, and potentially two databases. It should not be used unless the read/write divergence justifies the cost.
- **Query Performance**: Read models can be purpose-built for specific queries: full-text search, aggregation, graph traversal, etc.

## Why It Matters
In microservices, CQRS solves a common problem: the same data is needed for transactional writes and analytical or UI reads. Without CQRS, teams either optimize for one at the expense of the other, or build complex query layers against the write model. CQRS allows the write model to enforce domain invariants while the read model is optimized for user experience, reporting, or machine learning.

## Related Concepts
- [08-Event-Sourcing](08-Event-Sourcing.md) — CQRS and Event Sourcing are commonly paired; events feed read-optimized projections.
- [11-Data-Consistency](11-Data-Consistency.md) — CQRS introduces eventual consistency between models.

---

## Mental Model
CQRS is like a library with two desks. The check-in/check-out desk (commands) handles book updates: scanning barcodes, updating inventory, charging fines. The research desk (queries) has a separate, indexed catalog system optimized for finding books by topic, author, or publication date. Changes at the check-in desk appear in the research catalog after a short delay.
