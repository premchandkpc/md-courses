# Load Balancing

Distributing incoming traffic across multiple service instances to ensure no single instance is overwhelmed, improve responsiveness, and provide fault tolerance by routing around failed nodes.

## Overview

Load balancing operates at multiple levels in a microservices architecture: at the edge (external traffic → gateway), at the platform layer (gateway → services via ClusterIP or proxy), and at the client layer (in client-side discovery). Algorithms include round-robin (simple rotation), least connections (send to the instance with fewest active requests), consistent hashing (same client/request always goes to the same instance, useful for caching), and weighted distribution (allocate traffic proportional to instance capacity).

## Key Characteristics

- **Health-Aware Routing**: The load balancer monitors instance health via passive checks (timeouts, 5xx counts) or active probes (periodic health endpoint pings) and removes unhealthy instances from the pool.
- **Session Affinity**: When needed, the LB ensures requests from the same client go to the same instance (sticky sessions), typically via a cookie or hashing the client IP.
- **Algorithms Vary by Use Case**: Round-robin for uniform workloads, least connections for variable-length requests, consistent hashing for cache-friendly routing, and weighted for heterogeneous instance sizes.

## Why It Matters

Without load balancing, traffic concentrates on a few instances, creating hot spots that degrade latency and trigger cascading failures. A good load balancer smooths out traffic variations, absorbs instance failures transparently, and enables horizontal scaling: add instances, and traffic automatically redistributes. In cloud environments, load balancers also enable zone-aware routing (keeping traffic within an availability zone) to reduce cross-zone costs and latency.

## Related Concepts

- [Client-Side Discovery](05-Client-Side.md) — Load balancing logic lives in the client library.
- [Server-Side Discovery](06-Server-Side.md) — Load balancing is handled by a centralized proxy.
- [API Gateway](../05-API-Gateway/01-API-Gateway.md) — The gateway often includes a load balancer for routing to downstream services.
- [Service Registry](01-Service-Registry.md) — Provides the list of healthy instances that the load balancer distributes traffic across.

## Mental Model

Load balancing is like a restaurant host seating guests. When a party arrives (request), the host looks at which tables are free and occupied (instance health), picks a table that balances the workload — not seating too many parties with one server — and guides the party there. If a server calls in sick (instance failure), the host stops seating guests in that section and distributes them to the remaining servers.
