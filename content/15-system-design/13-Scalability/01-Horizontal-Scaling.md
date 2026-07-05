# 01-Horizontal-Scaling

Adding more service instances behind a load balancer to distribute traffic across multiple nodes. This is the primary scaling strategy for microservices because it aligns with the architecture's distributed nature and supports elastic, on-demand capacity changes.

## Overview
Horizontal scaling (scaling out) adds more machines or containers to a pool rather than making individual machines larger. Each instance runs the same service code and shares the workload. A load balancer distributes incoming requests across the pool. When demand drops, instances are removed to save cost. This approach underpins nearly all cloud-native architectures — Kubernetes horizontal pod autoscaling (HPA), AWS Auto Scaling Groups, and serverless concurrency scaling all follow this pattern.

## Key Characteristics
- **Stateless design is required**: Instances must not store session data locally. Any instance must be able to handle any request. State is offloaded to external stores (Redis, database, object storage).
- **Elastic and cost-efficient**: Match capacity to demand in near-real time. Scale to zero during off-hours. Pay only for what you use.
- **No inherent upper limit**: Unlike vertical scaling, horizontal scaling has no hardware ceiling. Add as many instances as the load balancer and backend can handle.
- **Requires infrastructure automation**: Manual scaling doesn't work at scale. Auto-scaling policies, health checks, and deployment pipelines are essential.
- **Graceful degradation**: When an instance fails, the load balancer routes around it. The system continues operating with reduced capacity.

## Why It Matters
Horizontal scaling is the backbone of microservices elasticity. It lets each service scale independently based on its own demand — the search service can have 20 replicas while the auth service has 3. Combined with container orchestration (Kubernetes, ECS), it becomes fully automated. Without horizontal scaling, microservices lose their primary operational advantage over monoliths.

## Related Concepts
- [Vertical Scaling](02-Vertical-Scaling.md) — The alternative approach of making instances larger instead of more numerous
- [Caching](06-Caching.md) — Reduces the load that each instance must handle, improving scale efficiency
- [Replication](05-Replication.md) — Horizontal scaling for data planes rather than compute

---

## Mental Model
A food truck adds more serving windows when the lunch rush hits. Each window is identical — any customer can be served at any window. When the rush ends, windows close. No single window needs to be faster; you just need enough windows for the line.
