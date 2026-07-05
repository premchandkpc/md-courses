# 17-Uber

Uber's microservices evolution tracks a company growing from a single-city monolith to a global multi-product platform with thousands of microservices. Their work on domain-oriented architecture, geospatial matching, and distributed payment systems provides valuable architecture lessons.

## Problem
Uber's initial architecture was a monolithic Python/Tornado backend (2009-2014). As the company expanded to hundreds of cities and added products (UberX, UberPool, UberEats, UberFreight), the monolith couldn't keep up — deployments were slow, teams had merge conflicts, and scaling was inefficient. A single deploy affected all products.

## Architecture
- **Domain-Oriented Microservices**: Uber decomposed services around business domains — trip service, dispatch, payment, pricing, driver management, rider management, notifications, maps/ETA, and surge. Each domain is owned by a dedicated team with full ownership.
- **Dispatch Service**: The core matching engine receives rider requests, queries nearby drivers via geospatial index (geohash-based), scores matches (distance, driver rating, surge multiplier, direction compatibility), and dispatches the best match. Uses a publish-subscribe model for real-time location updates.
- **Schemaless DB (Cassandra-based)**: Uber built Schemaless on top of Cassandra to get the scalability of NoSQL with the flexibility of schemas. It stores driver location history, trip records, and other high-write-volume data as JSON blobs indexed by metadata keys.
- **Ribbon-based Load Balancing**: For service discovery, Uber used a load balancer per service (Ribbon-style). Each client maintains a list of healthy servers and picks one using a configurable strategy (round-robin, weighted, zone-aware).
- **Ringpop (consistent hashing)**: For stateful services like dispatch, Uber used Ringpop — a consistent hashing ring with membership management. This allows dispatching to be sharded by the geohash region, keeping related data on the same node.
- **M3 (metrics engine)**: Uber built M3, a distributed time-series database for storing and querying metrics at scale (millions of metrics per second across the fleet). It's the backbone of their monitoring and alerting.

## Lessons Learned
- **Domain boundaries over technical layers**: Uber's early architecture had teams organized by technology (mobile API team, database team). The shift to domain-oriented teams (dispatch team, payment team) dramatically improved velocity and ownership.
- **Geospatial indexing is hard**: Simple distance-based queries don't scale. Use hierarchical grids (geohash, Google S2) with dynamic precision. For dispatch, use batched optimization (consider multiple requests simultaneously) rather than greedy nearest-driver matching.
- **Schemaless design for flexibility**: In fast-moving domains, schemas change constantly. Schemaless/Cassandra provided the flexibility to iterate quickly while maintaining the scalability needed for global operations.
- **Invest in observability early**: Uber's M3 platform was born from the need to understand a rapidly-growing fleet. Observability at scale requires dedicated investment — off-the-shelf solutions don't handle millions of metrics per second.

## Related Concepts
- [02-Uber](../15-System-Design/02-Uber.md) — Ride-hailing system design patterns
- [17-Amazon](17-Amazon.md) — API mandate and service ownership comparison

---

## Mental Model
Uber's dispatch system is like an air-traffic controller managing thousands of planes in real-time. The controller doesn't just match the nearest plane to a landing request — they consider all planes in the airspace, their fuel levels (driver availability), wind patterns (surge pricing), and runway capacity (demand), optimizing the global match, not just each individual request.
