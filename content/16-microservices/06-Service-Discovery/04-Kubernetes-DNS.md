# Kubernetes DNS

Kubernetes's built-in service discovery mechanism that uses DNS records (A/AAAA and SRV) to map Service names to Pod IP addresses. Every K8s cluster runs a DNS service (CoreDNS) that is automatically configured as pods are created and destroyed.

## Overview

When a Service is created in Kubernetes, the DNS controller creates corresponding DNS records. A regular ClusterIP Service gets an A record resolving to the cluster IP (a virtual IP that load balances across Pods). A Headless Service (clusterIP: None) gets A records for each individual Pod IP, plus SRV records with port mappings. Pods discover services simply by using the service name as a hostname (e.g., `http://my-service:8080`), and DNS handles routing.

## Key Characteristics

- **Zero-Configuration Discovery**: Pods don't need to register or query any external registry — DNS resolution works automatically for any Service within the same namespace or cluster.
- **SRV Record Support**: Headless services expose individual Pod addresses via SRV records, enabling client-side load balancing and stateful application discovery (e.g., Cassandra seed nodes).
- **Namespace Scoping**: Fully qualified names follow the pattern `<service>.<namespace>.svc.cluster.local`, enabling cross-namespace discovery and network policy enforcement.

## Why It Matters

K8s DNS is the simplest discovery mechanism: it requires no separate infrastructure, no client libraries, and no registration code. Every language and framework supports DNS resolution. For most Kubernetes-native applications, DNS-based discovery is sufficient, and its simplicity reduces operational burden. The trade-off is limited control — DNS caching (TTLs) makes changes slow to propagate, and any sophisticated routing requires additional tooling.

## Related Concepts

- [Service Registry](01-Service-Registry.md) — DNS is one implementation of the registry pattern.
- [Server-Side Discovery](06-Server-Side.md) — ClusterIP Services implement server-side discovery via kube-proxy.
- [Consul](02-Consul.md) — External registries can supplement K8s DNS for advanced features.

## Mental Model

Kubernetes DNS is like a phone system in a large office where every employee has a direct extension. When someone joins, the phone book automatically gets an entry (A record). When someone moves desks, the entry updates. To reach "billing," you just dial "billing" — you don't need to know which desk they're at or whether there are multiple billing reps handling calls.
