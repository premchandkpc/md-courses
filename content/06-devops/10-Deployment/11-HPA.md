# Horizontal Pod Autoscaler (HPA)

The Horizontal Pod Autoscaler automatically scales the number of pods in a deployment, replication controller, or stateful set based on observed metrics. HPA is a Kubernetes-native resource that adjusts replica counts to match demand, increasing capacity during traffic spikes and reducing waste during low-traffic periods. It is the primary mechanism for elastic scaling in Kubernetes.

## Overview

HPA periodically queries a metrics source (metrics server for resource metrics, Prometheus adapter or custom metrics API for custom/external metrics), calculates the desired replica count based on the current metric value vs target value, and updates the deployment's replicas. The control loop runs every 15 seconds (configurable via `--horizontal-pod-autoscaler-sync-period`). Scaling is conservative by design: the algorithm prevents thrashing by requiring the target metric to cross a configurable tolerance (default 10%) and cooldown periods.

## Key Characteristics

- **CPU-Based Scaling**: The most common HPA configuration. Target average CPU utilization across all pods (e.g., `targetAverageUtilization: 75`). The autoscaler calculates: `desiredReplicas = ceil(currentUtilization / targetUtilization * currentReplicas)`. CPU-based scaling works well for CPU-bound services but doesn't capture all scaling signals (memory, request rate, queue depth).
- **Memory-Based Scaling**: Similar to CPU, using memory utilization. Less common because memory is less directly correlated with load — services may use memory at startup (JVM heap) or cache data under normal load. Memory-based scaling is useful for memory-caching services where increased traffic causes memory pressure.
- **Custom Metrics Scaling**: Scales on application-specific metrics exposed via the custom metrics API. Examples: requests per second (from Istio/Envoy metrics), queue length (from RabbitMQ Prometheus exporter), gRPC stream count, or database connection pool utilization. Custom metrics provide the most accurate scaling signals for most microservices.
- **External Metrics Scaling**: Scales based on metrics from systems outside Kubernetes. Examples: SQS queue depth (AWS), Pub/Sub subscription backlog (GCP), or CloudWatch metrics. External metrics enable scaling Kubernetes workloads based on event-driven demand signals — the foundation for event-driven autoscaling (KEDA).
- **Multiple Metrics**: HPA can evaluate multiple metrics simultaneously, using the metric that produces the highest desired replica count. For example, scale on both CPU (target: 75%) and requests-per-second (target: 1000). The HPA calculates desired replicas for each metric independently and takes the max. This prevents one metric from becoming a scaling bottleneck.
- **Scaling Behavior Configuration**: Kubernetes 1.23+ HPA supports `behavior` configuration for fine-grained control. `scaleUp` and `scaleDown` policies with `stabilizationWindowSeconds` (cooldown), `selectPolicy` (max/min/disabled), `policies` (percent/absolute), and `periodSeconds`. Example: scale up 100% in 15 seconds, scale down 10% per 5 minutes (aggressive up, conservative down).
- **Cooldown/Stabilization**: Prevents thrashing — rapid scale-up followed by immediate scale-down. The stabilization window holds the desired replica count for a configurable duration before executing. For example, if the desired count drops from 10 to 5, the HPA holds at the higher count for 5 minutes to absorb brief traffic dips.
- **Metrics Server Required**: HPA requires the Metrics Server (or equivalent) to be installed in the cluster for resource metrics. Custom and external metrics require a metrics adapter (Prometheus Adapter, Datadog Cluster Agent, KEDA).

## Why It Matters

HPA is essential for cost-efficient, reliable microservices operation. It ensures that services have enough capacity during traffic spikes without over-provisioning during quiet periods. Combined with cluster autoscaling (node-level), HPA provides end-to-end elasticity — service pods scale within the cluster, and the cluster scales nodes to fit the pods. HPA also reduces operational burden by eliminating manual capacity planning.

## Related Concepts

- [Scaling](12-Scaling.md) — Broader scaling concepts including vertical and predictive scaling
- [Kubernetes](02-Kubernetes.md) — HPA operates on Kubernetes Deployments and StatefulSets
- [Service Mesh](04-Service-Mesh.md) — Istio/Linkerd metrics feed into HPA custom metrics

---

## Mental Model

HPA is like a restaurant manager who watches the queue length (metrics) and opens more serving lines (pods) when the queue gets too long. When the lunch rush hits, the manager opens all available lines (scale up). When the rush passes, lines are closed one at a time (scale down), but the manager waits a few minutes between closing each line (stabilization) because another wave might arrive. The manager doesn't reopen a line immediately after closing it (cooldown) — that would confuse the kitchen.
