# 02-SOA-vs-Microservices

Service-Oriented Architecture (SOA) and Microservices share the goal of decomposing systems into services, but differ fundamentally in scope, granularity, and communication philosophy.

## Overview

SOA emerged in the 1990s-2000s with enterprise service buses (ESB), SOAP, and WS-* standards. Microservices evolved from SOA lessons, rejecting heavy middleware in favor of lightweight, decentralized patterns.

| Dimension | SOA | Microservices |
|-----------|-----|---------------|
| Service size | Coarse-grained (large) | Fine-grained (small) |
| Communication | SOAP, WS-*, ESB | REST, gRPC, async messaging |
| Data sharing | Shared database, canonical model | Database-per-service |
| Governance | Centralized (standards body) | Decentralized (team autonomy) |
| Infrastructure | Heavy (ESB, BPEL engine) | Light (API gateway, service mesh) |
| Deployment | Few large deployments | Many small deployments |
| Integration | ESB with routing/transformation | API gateway + events |

## Why Microservices Won

Microservices succeeded where SOA struggled because they applied SOA's lessons: no shared database, no centralized ESB, lightweight protocols (HTTP/gRPC instead of SOAP), and alignment with DevOps and containerization (Docker, Kubernetes).

## Why It Matters

Understanding SOA vs Microservices helps avoid repeating SOA's mistakes — especially the "distributed monolith" anti-pattern where microservices share databases or use heavy orchestration middleware.

## Related Concepts

- [What is a Microservice](/16-microservices/00-Introduction/00-What-is-Microservice.md)
- [Monolith vs Microservices](/16-microservices/00-Introduction/01-Monolith-vs-Microservices.md)
- [Microservice Principles](/16-microservices/00-Introduction/05-Microservice-Principles.md)

---

## Mental Model

SOA = A corporate HQ with a central mailroom (ESB) that routes all inter-department communication. Every department must format their mail the same way (canonical model). Microservices = A startup with direct messaging. Each team texts each other directly (REST/gRPC) or posts in Slack channels (events). Each team uses their own language and tools. Faster, less bureaucracy, but needs clear conventions to avoid chaos.
