# Scaling Microservices

Scaling is the ability of a system to handle increased load by adding resources. In microservices, scaling can be horizontal (adding more instances), vertical (adding more power to existing instances), or a combination of both. Effective scaling strategies ensure that services maintain performance and availability as demand grows without over-provisioning resources during low demand.

## Overview

Microservices architectures are designed for elastic scaling — each service can scale independently based on its own demand patterns. A video-encoding service scales during upload peaks while the user-profile service remains at baseline. This granular scaling is a primary advantage of microservices over monoliths, where everything must scale together. Modern scaling combines automated policies (HPA, KEDA), capacity planning, and infrastructure automation to right-size resources continuously.

## Key Characteristics

- **Horizontal Scaling**: Adding more instances of a service behind a load balancer. This is the preferred scaling method for cloud-native microservices because it provides both capacity and redundancy. If one instance fails, others continue serving. Kubernetes HPA automates horizontal scaling based on CPU, memory, or custom metrics. Horizontal scaling is limited by service statefulness — stateless services scale trivially, while stateful services require data partitioning.
- **Vertical Scaling**: Increasing resources (CPU, memory) to existing instances. Useful when the workload cannot be distributed (e.g., single-threaded processing, large in-memory datasets). Vertical scaling has hard limits (maximum instance size in the cloud) and typically requires restarts. It is often combined with horizontal scaling for a "scale up then scale out" strategy — scale vertically to a point, then add more instances.
- **Auto-Scaling Policies**: Rules that define when and how to scale. Key parameters: scale-up threshold (e.g., CPU > 75% for 2 minutes), scale-down threshold (CPU < 30% for 5 minutes), minimum replicas (availability floor), maximum replicas (cost ceiling), and cooldown periods (prevent thrashing). Policies should be service-specific — a batch processor scales differently than a real-time API.
- **Scale-to-Zero**: Reducing replica count to zero during periods of no demand. Used for event-driven workloads (background processors, queue consumers) that only need to run when work is available. KEDA (Kubernetes Event-Driven Autoscaling) enables scale-to-zero by watching external event sources (Kafka lag, SQS queue depth, cron schedule). Scale-to-zero saves significant cost for low-utilization services.
- **Predictive Scaling**: Using historical patterns to scale before load arrives. Machine learning models predict traffic based on time-of-day, day-of-week, seasonal patterns, and known events (marketing campaigns, product launches). Predictive scaling solves the lag problem in reactive autoscaling (it takes 2-5 minutes for new instances to become ready). AWS Auto Scaling Predictive Scaling, GCP Autoscaler, and custom solutions implement this.
- **Scaling Thresholds**: The metric values that trigger scaling actions. Choosing correct thresholds requires understanding service behavior: CPU may spike briefly without needing more replicas (transient), or sustained moderate CPU may indicate capacity shortage. Metrics should be smoothed (e.g., 1-5 minute averages) to avoid reacting to noise. Target utilization (e.g., 70% CPU target) leaves headroom for traffic spikes.
- **Scheduling-Based Scaling**: Scaling on a schedule for predictable patterns. Scale up at 8 AM for business hours, scale down at 6 PM. Cron-based HPA or scheduled KEDA scalers implement this. Useful when traffic patterns are known and predictable, reducing reliance on reactive scaling.
- **Database and Stateful Scaling**: The hardest scaling challenge. Read replicas scale horizontally for read-heavy workloads. Write scaling requires sharding (partitioning data across databases) or distributed databases (CockroachDB, YugabyteDB, Cassandra). Cache scaling uses consistent hashing (Redis Cluster, Memcached). Stateful scaling often requires manual planning and data rebalancing.

## Why It Matters

Scaling is not just about handling peak traffic — it's about cost optimization. Over-provisioning wastes resources; under-provisioning causes outages. Effective scaling aligns resource consumption with actual demand, minimizing waste while maintaining SLOs. In microservices, independent scaling per service enables fine-grained cost allocation and optimization. Services with stable demand can be right-sized manually, while variable-demand services benefit from autoscaling.

## Related Concepts

- [HPA](11-HPA.md) — Kubernetes-native horizontal pod autoscaler
- [Kubernetes](02-Kubernetes.md) — Cluster autoscaling and pod-level scaling
- [Docker](01-Docker.md) — Container resource limits and requests for scaling
- [Canary](09-Canary.md) — Canary deployments scale the new version gradually
- [Rolling Update](10-Rolling-Update.md) — Rolling updates interact with autoscaler during upgrades
- [Service Mesh](04-Service-Mesh.md) — Mesh provides the metrics that drive scaling decisions

---

## Mental Model

Scaling microservices is like managing a fleet of food trucks at a festival. Horizontal scaling: when one truck has a long line, you open another truck of the same type (add instances). Vertical scaling: you add more cooks to the existing truck (increase resources). Predictive scaling: you know the lunch rush happens at noon, so you have extra trucks ready by 11:30. Scale-to-zero: the vegan taco truck goes home between meals when there's no demand. Each truck type scales independently — the burger truck might need 5x capacity while the smoothie truck stays at 1x.
