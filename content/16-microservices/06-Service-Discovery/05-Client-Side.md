# Client-Side Service Discovery

A discovery pattern where the client (or its sidecar) queries the service registry directly, selects an available instance, and sends the request to that instance — no intermediate load balancer.

## Overview

In client-side discovery, each consumer service knows how to talk to the registry (Eureka, Consul, ZooKeeper). It fetches the list of available instances for the target service, applies a load-balancing algorithm (round-robin, weighted random, least outstanding requests), and sends the HTTP or gRPC call directly to the chosen instance. Popular implementations include Netflix Ribbon (now Spring Cloud LoadBalancer) and client-side Consul DNS lookups.

## Key Characteristics

- **No Extra Hop**: The client communicates directly with the service instance, avoiding the latency and bottleneck of an intermediate load balancer.
- **Client Library Required**: Each service must include a discovery-aware HTTP client or sidecar that understands the registry protocol and load-balancing strategy.
- **Rich Load-Balancing**: The client can implement sophisticated strategies — zone-aware routing (prefer same availability zone), weighted response time, circuit breakers — that would be harder in a centralized LB.

## Why It Matters

Client-side discovery excels in high-throughput environments where every millisecond counts — the eliminated network hop can reduce P99 latency by 10-30%. It also scales horizontally: adding more clients adds more discovery capacity, unlike a centralized load balancer that becomes a bottleneck. The trade-off is operational complexity — every service must bundle and configure the right client library, and rolling out a new strategy requires updating every service.

## Related Concepts

- [Server-Side Discovery](06-Server-Side.md) — The alternative pattern where a load balancer proxies requests.
- [Service Registry](01-Service-Registry.md) — The registry that client-side discovery queries.
- [Eureka](03-Eureka.md) — Commonly used with client-side discovery in Netflix OSS / Spring Cloud.
- [Load Balancing](07-Load-Balancing.md) — The selection strategy applied by the client.

## Mental Model

Client-side discovery is like having a personal assistant who knows every restaurant in town. When you want Thai food, the assistant checks their directory, picks a restaurant (maybe the one closest to you), and drives you directly there. No central dispatcher needed — your assistant handles everything.
