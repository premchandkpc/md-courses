# Service Registry

A dynamic phone book for microservices that maps service names to their network locations (IP:port). Services register themselves on startup and deregister on shutdown; clients query the registry to find available instances.

## Overview

In a microservices environment, instances come and go — scaled up, scaled down, crashed, replaced. Hard-coding addresses is impossible. The service registry maintains a real-time directory of all healthy service instances. Each instance sends heartbeats to signal liveness; the registry removes entries that fail to heartbeats. Clients or load balancers query the registry to discover instance addresses, typically using a round-robin or random strategy to select one.

## Key Characteristics

- **Registration and Deregistration**: Instances register their address, health endpoint, and metadata on startup, and deregister on graceful shutdown or heartbeat timeout.
- **Health Checking**: The registry actively pings health endpoints or relies on heartbeats to mark instances as healthy or unhealthy.
- **TTL-Based Eviction**: If an instance fails to renew its lease within a time window, the registry evicts it, preventing clients from routing to dead instances.

## Why It Matters

Without a registry, service locations must be configured statically or managed through DNS with long TTLs, both of which break under dynamic orchestration. The registry enables elastic scaling (new instances join and are immediately discoverable), fault tolerance (failed instances are removed), and zero-downtime deployments (old instances drain while new ones register).

## Related Concepts

- [Consul](02-Consul.md) — A popular CP service registry with KV store and health checking.
- [Eureka](03-Eureka.md) — Netflix's AP service registry, designed for availability over consistency.
- [Kubernetes DNS](04-Kubernetes-DNS.md) — K8s's built-in registry via DNS SRV records.
- [Client-Side Discovery](05-Client-Side.md) — Clients query the registry directly.
- [Server-Side Discovery](06-Server-Side.md) — A load balancer queries the registry on behalf of clients.

## Mental Model

A service registry is like the host at a busy restaurant. Walk-in customers (service instances) tell the host their name and party size (register). When a guest (client) asks "is my party here?", the host checks the list and points to the right table. If a customer leaves without telling the host, the host eventually notices the empty table and crosses them off the list (TTL eviction).
