# Consul

HashiCorp Consul is a service networking solution that provides service discovery, health checking, a distributed KV store, and multi-datacenter support. It favors consistency (CP in CAP theorem) using the Raft consensus protocol.

## Overview

Consul uses a gossip protocol (Serf) for cluster membership and failure detection, and Raft for consistent data replication across the cluster. Each Consul agent runs on every node; agents forward requests to the server pool. Consul supports multiple datacenters out of the box — services in us-east-1 can discover services in eu-west-1 via the WAN gossip pool. It also includes a service mesh layer (Consul Connect) for mTLS between services.

## Key Characteristics

- **CP System (Consistency over Availability)**: Uses Raft to ensure strong consistency — all servers agree on the registry state before responding. During a network partition, the minority side stops serving writes to prevent split-brain.
- **KV Store**: A hierarchical key-value store for configuration data that any service can read/write, enabling dynamic configuration without restarts.
- **Multi-DC and Service Mesh**: Native multi-datacenter replication and built-in service mesh with automatic mTLS, L7 traffic management, and intentions (firewall rules between services).

## Why It Matters

Consul's strong consistency guarantees are critical when service topology must be authoritative — for example, during blue/green deployments where you must ensure only the new version receives traffic. Its KV store replaces ad-hoc config management (ZooKeeper, etcd). The integrated service mesh simplifies zero-trust networking, and the multi-DC support is unmatched among service registries.

## Related Concepts

- [Service Registry](01-Service-Registry.md) — The abstract pattern Consul implements.
- [Eureka](03-Eureka.md) — An AP alternative; Consul chooses consistency over availability.
- [Kubernetes DNS](04-Kubernetes-DNS.md) — DNS-based discovery, simpler but less feature-rich.

## Mental Model

Consul is like the central switchboard of a large corporation with offices worldwide. Each office has a local operator (Consul agent) who knows everyone in that building. The operators talk to each other (gossip) to share updates, and the main switchboard (Consul server cluster) keeps the authoritative company directory. If you need to reach someone in another country, the switchboard finds the right extension.
