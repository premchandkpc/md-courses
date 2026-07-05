# Rolling Update

Rolling update is a deployment strategy that incrementally replaces instances of the old version with the new version. Pods are updated one by one (or in batches), with health checks ensuring that each new pod is ready before proceeding to the next. Rolling updates are the default deployment strategy in Kubernetes and provide zero-downtime updates without requiring additional infrastructure.

## Overview

In a rolling update, the deployment controller creates new pods with the updated version while gradually terminating old pods. The process is controlled by two parameters: `maxSurge` (how many extra pods can be created above the desired count) and `maxUnavailable` (how many pods can be unavailable during the update). A readiness probe on the new pods gates the progression — the update pauses if new pods fail to become healthy. Rolling updates are infrastructure-centric: they replace instances without explicit metrics-based validation.

## Key Characteristics

- **maxSurge**: Maximum number of pods that can be created above the desired replica count during the update. Default is 25% (rounded up). With 10 replicas and 25% maxSurge, up to 3 extra pods can be created during the update. Higher maxSurge speeds up the rollout but requires spare cluster capacity.
- **maxUnavailable**: Maximum number of pods that can be unavailable during the update. Default is 25% (rounded up). With 10 replicas and 25% maxUnavailable, at least 8 pods must remain serving at all times. Setting maxUnavailable to 0 ensures zero downtime but requires extra capacity (maxSurge > 0).
- **Readiness Probe Gating**: The rollout pauses if new pods fail their readiness probes. Kubernetes waits for each new pod to become ready before terminating the next old pod. If new pods remain unready beyond `progressDeadlineSeconds` (default 600 seconds), the rollout is considered failed and is paused (not rolled back automatically — that requires manual or CI/CD intervention).
- **Zero Downtime with Proper Configuration**: Achieving zero downtime requires: readiness probes correctly reflecting application startup, graceful shutdown (SIGTERM handling with `preStop` hook for connection draining), `terminationGracePeriodSeconds` allowing in-flight requests to complete, and service endpoints updated before traffic is routed. Pod Disruption Budgets prevent voluntary disruptions during the update.
- **Rollback by Reapplying Old Spec**: To roll back a rolling update, reapply the previous deployment specification. Kubernetes performs another rolling update from the current version back to the previous version. This is slower than blue-green's instant rollback but requires no additional infrastructure overhead.
- **Stateless vs Stateful**: Rolling updates work well for stateless services. For stateful services (databases, caches), StatefulSets with `PodManagementPolicy: OrderedReady` perform rolling updates one pod at a time, in reverse ordinal order, ensuring data consistency.

## Why It Matters

Rolling updates are the simplest and most resource-efficient deployment strategy for microservices. They require no additional environments (unlike blue-green) and no traffic routing infrastructure (unlike canary). They are the default in Kubernetes for good reason: they provide zero-downtime updates with minimal overhead. The tradeoff is that rollback is a multi-step process, and there is no built-in metrics-based validation (canary analysis must be added separately, e.g., with Flagger or Argo Rollouts).

## Related Concepts

- [Kubernetes](02-Kubernetes.md) — Deployments implement rolling updates by default
- [Blue-Green](08-BlueGreen.md) — Instant rollback vs rolling update's slower rollback
- [Canary](09-Canary.md) — Metrics-based validation vs rolling update's health-check-based approach
- [HPA](11-HPA.md) — Horizontal scaling interacts with rolling updates for capacity planning
- [Sidecar](07-Sidecar.md) — Sidecar readiness must be factored into application readiness probes

---

## Mental Model

Rolling update is like rotating tires on a moving car. You don't stop the car and replace all four tires at once (recreate). Instead, you lift one corner, replace the tire (update pod), lower it, and move to the next corner. The car keeps moving (serving traffic) throughout. If a new tire has a defect (pod fails readiness), you stop the process, replace that tire with the old one (rollback that pod), and investigate. The journey continues with three old tires and one new — degraded but not stopped.
