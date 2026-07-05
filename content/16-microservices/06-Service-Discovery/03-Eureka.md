# Eureka

Netflix Eureka is a REST-based service registry designed for the AP side of CAP — availability and partition tolerance over consistency. It is a core component of the Netflix OSS stack and integrates deeply with Spring Cloud.

## Overview

Eureka favors availability: if a Eureka server fails or a network partition occurs, clients continue to operate with cached registry data rather than failing. Services register with Eureka and send periodic heartbeats (renewals); if a heartbeat is missed, Eureka does not immediately evict the instance — it enters a self-preservation mode that keeps the instance registered because the heartbeat loss might be due to a network partition, not instance death.

## Key Characteristics

- **AP System (Availability over Consistency)**: During partitions, servers on both sides continue to serve; stale data is preferred over no data. This prevents a registry outage from taking down all service discovery.
- **Self-Preservation Mode**: If fewer than 85% of heartbeats arrive in a minute, Eureka assumes a network issue and stops evicting instances. This prevents a transient network blip from wiping the registry.
- **Client-Side Caching**: Eureka clients cache the full registry locally and refresh periodically (default 30s), so a Eureka server outage doesn't prevent existing clients from discovering services.

## Why It Matters

Eureka's AP design reflects the Netflix philosophy that a service registry outage should not cause a system-wide failure. In large-scale deployments, network partitions are inevitable — Eureka's self-preservation mode and client-side caching mean services keep running with slightly stale but usable registry data. This trade-off is ideal for environments where availability of existing services matters more than instantly seeing new instances.

## Related Concepts

- [Consul](02-Consul.md) — A CP alternative; Eureka favors availability when they conflict.
- [Service Registry](01-Service-Registry.md) — The abstract pattern Eureka implements.
- [Client-Side Discovery](05-Client-Side.md) — Eureka is typically used with client-side discovery (Ribbon/Spring Cloud LoadBalancer).

## Mental Model

Eureka is like a community bulletin board where businesses pin their business cards. If someone removes a card, it stays on the board for a while before anyone notices (self-preservation). If the board falls down (server failure), people still have the cards they already collected (client cache). It's better that someone visits a business that just closed (stale data) than that no one can find any business at all (unavailability).
