# Server-Side Service Discovery

A discovery pattern where the client sends requests to a single well-known address (a load balancer or proxy), which queries the service registry and forwards the request to a healthy instance behind the scenes.

## Overview

In server-side discovery, the client is unaware of service instances — it only knows the load balancer's address. The load balancer (hardware like F5, software like NGINX/HAProxy, or cloud-native like AWS ALB) consults the registry to find healthy instances and distributes traffic among them. Kubernetes ClusterIP Services are a canonical example: kube-proxy watches the API server and programs iptables/IPVS rules so the ClusterIP load-balances across Pods.

## Key Characteristics

- **Simpler Clients**: Clients only need to know the load balancer hostname — no registry client library, no instance selection logic. Standard HTTP libraries work unchanged.
- **Centralized Control**: Load-balancing policies (round-robin, least connections, sticky sessions), health checks, and TLS termination are managed in one place.
- **Single Point of Failure Risk**: The load balancer must be highly available (multiple replicas, VIP with failover), or it becomes a bottleneck and outage risk.

## Why It Matters

Server-side discovery is the default choice for most teams because it keeps clients dumb — any service can call any other service with a simple URL, regardless of language or framework. Centralized routing also simplifies operations: traffic shifting, canary deployments, and blue/green rollouts are configured on the load balancer without touching services. The trade-off is the extra network hop and the operational cost of running highly available proxies.

## Related Concepts

- [Client-Side Discovery](05-Client-Side.md) — The alternative where clients do the routing themselves.
- [Kubernetes DNS](04-Kubernetes-DNS.md) — K8s's built-in server-side discovery via ClusterIP Services.
- [Load Balancing](07-Load-Balancing.md) — The core function of the server-side proxy.
- [API Gateway](../05-API-Gateway/01-API-Gateway.md) — A specialized server-side proxy that also handles cross-cutting concerns.

## Mental Model

Server-side discovery is like calling a taxi dispatch number. You (the client) call the one known number (load balancer). The dispatcher (load balancer) looks at which taxis are available (registry), picks the nearest one, and sends it to you. You never know the taxi driver's direct number, and you don't care — you just need a ride.
