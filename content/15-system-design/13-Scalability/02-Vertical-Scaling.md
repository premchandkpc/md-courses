# 02-Vertical-Scaling

Increasing the resources (CPU, RAM, disk, network) of a single instance rather than adding more instances. Also called "scaling up." Simpler to implement than horizontal scaling but hits hard physical and cost limits.

## Overview
Vertical scaling upgrades the existing machine to handle more load — swapping a t3.medium for a t3.xlarge, adding more RAM, or moving to a higher-core processor. No code changes are needed since the same instance handles all traffic. This makes it attractive for legacy systems, stateful services, and databases that resist sharding. However, even the largest AWS instances cap out at 448 vCPUs and 24 TB RAM — a finite ceiling.

## Key Characteristics
- **No architectural changes**: Drop in a larger instance and the same code runs with better performance. No load balancers, no distributed state management.
- **Hardware ceiling**: Every instance type has a maximum size. Once you hit it, you must switch strategies (horizontal scaling or sharding).
- **Non-linear cost**: Larger instances cost more per unit of capacity. A 2x larger instance often costs more than 2x the smaller one. The price/performance curve bends against you.
- **Upgrade requires downtime**: Most vertical scaling operations require a restart or failover. Rolling upgrades can minimize but not eliminate disruption.
- **Good for stateful workloads**: Databases, caches, and legacy services benefit from vertical scaling because they avoid the complexity of distributed consistency.

## Why It Matters
Despite its limitations, vertical scaling remains essential. Stateful services (relational databases, Redis, Kafka brokers) are hard to shard and replicate. These often run on the largest instances available. Microservices architects must know when to scale up (simpler, good enough) versus scale out (elastic, unlimited).

## Related Concepts
- [Horizontal Scaling](01-Horizontal-Scaling.md) — The alternative: more instances rather than bigger ones
- [Sharding](03-Sharding.md) — Horizontal scaling for databases, often needed when vertical scaling maxes out
- [CAP Theorem](10-CAP-Theorem.md) — Vertical scaling doesn't introduce distributed tradeoffs, unlike horizontal approaches

---

## Mental Model
You own a small restaurant with one kitchen. When demand grows, you install a bigger oven and more burners (vertical scaling). Eventually the kitchen can't get any bigger — that's the hardware ceiling. At that point you open a second kitchen (horizontal scaling).
