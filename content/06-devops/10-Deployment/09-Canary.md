# Canary Deployment

Canary deployment is a progressive delivery strategy that gradually shifts traffic from an old version to a new version, starting with a small percentage and increasing as confidence grows. Traffic is monitored for errors, latency, and business metrics. If the canary shows signs of regression, the rollout is automatically rolled back. If it succeeds, traffic is gradually increased to 100%.

## Overview

The name comes from the "canary in a coal mine" — miners brought canaries into mines to detect toxic gases before humans were affected. Similarly, a canary deployment exposes a small subset of users to the new version first, validating behavior under real production conditions before exposing all users. Unlike blue-green (instant switch) or rolling update (incremental but blind), canary deployments are metric-driven: the rollout progresses or stops based on observed behavior.

## Key Characteristics

- **Gradual Traffic Shift**: Traffic starts at a small percentage (5%) and increases through defined stages (5% → 25% → 50% → 75% → 100%). Each stage lasts a minimum observation period (minutes to hours). Istio VirtualService weight-based routing, service mesh traffic splitting, or load balancer weights implement the shift. The pace is configurable and can be automated or gated by manual approval.
- **Metrics Comparison**: The canary's success rate, latency (p50, p95, p99), error rate, and business metrics are compared against the baseline (current version). Automated analysis detects statistically significant regressions. If error rate increases by >1%, latency degrades by >10%, or business metrics (conversion rate, signups) decline, the canary is halted or rolled back.
- **Automatic Rollback**: When metrics breach defined thresholds, the canary automatically rolls back. Traffic is shifted back to 100% stable version. The failed version remains in place for debugging but receives no traffic. Rollback should be fast (seconds, not minutes) to limit user impact.
- **User Segmentation**: Canaries can target specific user segments: internal users first (dogfooding), users in a specific region, users with specific account types, or random sampling. Cookie-based or header-based routing ensures consistent user experience (a user doesn't flip-flop between versions). This enables testing with real users while controlling blast radius.
- **Observability Requirements**: Effective canary deployments require real-time monitoring: request metrics with version labels, distributed tracing to identify issues across service boundaries, error tracking with stack traces, and business metrics that correlate with the deployment. Without this observability, the canary provides no useful signal.
- **Analysis Tools**: Flagger (automated canary operator for Istio/Linkerd/App Mesh), Argo Rollouts (Kubernetes progressive delivery controller), and AWS CodeDeploy provide automated canary analysis. They compare canary vs baseline metrics, implement promotion/rollback logic, and integrate with monitoring systems (Prometheus, Datadog, CloudWatch).

## Why It Matters

Canary deployments reduce the risk of releasing buggy code to all users. They validate the new version under real production traffic — catching issues that staging environments cannot replicate (scale, data diversity, user behavior patterns). The automated rollback on metric regression means that most canary failures never impact the full user base. Canary deployments enable teams to release more frequently with higher confidence.

## Related Concepts

- [Blue-Green](08-BlueGreen.md) — Canary is more gradual than blue-green's instant switch; canary can transition into blue-green
- [Rolling Update](10-Rolling-Update.md) — Rolling updates are infrastructure-oriented; canaries are metrics-oriented
- [Istio](05-Istio.md) — VirtualService weight-based routing for canary traffic splitting
- [Service Mesh](04-Service-Mesh.md) — Mesh provides the traffic splitting and metrics for canary analysis

---

## Mental Model

Canary deployment is like testing a new bridge design with a single lane first. Instead of opening all lanes to traffic at once (blue-green), you open one lane (5% traffic) and watch for vibrations, stress cracks, and structural issues (metrics). If the lane holds, you open two more lanes (25%), then half the bridge (50%), always monitoring. At the first sign of structural weakness, you close the new lanes and revert to the original bridge. The majority of traffic never experiences the risk.
