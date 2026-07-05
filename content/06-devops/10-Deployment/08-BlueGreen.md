# Blue-Green Deployment

Blue-green deployment is a release strategy that maintains two identical production environments: blue (the current live version) and green (the new version). Traffic is switched from blue to green instantaneously once the green environment is fully deployed and tested. This enables zero-downtime deployments, instant rollback by switching back to blue, and the ability to validate the new version under production-like conditions before serving live traffic.

## Overview

In a blue-green deployment, both environments run simultaneously. The blue environment serves all production traffic. The green environment is deployed with the new version of the service and undergoes validation (smoke tests, integration tests, load tests). Once green is verified, the router, load balancer, or DNS is switched to send all traffic to green. Blue remains running and ready to receive traffic if a rollback is needed. The key requirement is that both environments are fully provisioned and capable of handling production load.

## Key Characteristics

- **Instant Traffic Switch**: Traffic is cut over at the routing layer (load balancer, Kubernetes Service selector update, DNS change, or Istio VirtualService weight update). The switch is atomic from the user's perspective — requests in flight during the switch complete against the old environment, while new requests go to the new environment. Proper connection draining ensures zero-dropped requests.
- **Full Capacity at All Times**: Both environments must be able to handle 100% of production traffic. This means double infrastructure costs during the deployment window. For cost-optimized setups, the idle environment can be scaled down after verification, but the tradeoff is slower rollback (requiring scale-up before switching traffic).
- **Rollback by Traffic Switch**: Rolling back is as simple as switching traffic back to the previous environment. This is an O(1) operation — no redeployment, no rebuilding. The idle environment retains the previous version, so rollback is instantaneous. This dramatically reduces the risk of a bad deployment causing extended downtime.
- **Database Compatibility**: The most complex aspect of blue-green deployments. The database schema must be compatible with both versions (backward-compatible migrations) because both environments read/write to the same database during the transition. Schema changes must be additive (add columns, not remove or rename) and deployed in phases: migrate schema first, deploy green, switch traffic, then clean up old schema.
- **Testing Before Cutover**: The green environment can be fully tested before receiving production traffic. This includes automated smoke tests, manual QA, load testing, and integration tests against real production dependencies (queues, caches, databases). The green environment can also be staged to receive a subset of traffic for validation (essentially becoming a canary deployment).
- **Environment Management**: Both environments must be kept in sync in terms of configuration, infrastructure, and dependencies. Configuration drift between blue and green is a common failure mode. Infrastructure-as-code (Terraform, Helm, Pulumi) and immutable infrastructure ensure both environments are identical.

## Why It Matters

Blue-green deployment eliminates the riskiest moment in a deployment: the transition from old to new version. If the new version has a critical bug, traffic is switched back in seconds — not minutes or hours spent redeploying the old version. This makes deployments a low-stress operation that can be performed frequently. The tradeoff is infrastructure cost and database compatibility complexity.

## Related Concepts

- [Canary](09-Canary.md) — Gradual traffic migration vs instant switch; canary precedes blue-green in progressive delivery
- [Rolling Update](10-Rolling-Update.md) — Incremental pod replacement vs full environment parallel deployment
- [Istio](05-Istio.md) — VirtualService traffic switching enables blue-green without infrastructure changes
- [Kubernetes](02-Kubernetes.md) — Services and Deployments can implement blue-green with label selectors

---

## Mental Model

Blue-green deployment is like a theater with a revolving stage. The current act (version) plays on the visible stage (blue). The next act's set is built on the back half of the stage (green) while the current act performs. When the green set is ready and verified, the stage rotates — the new act is now in front of the audience, and the previous set moves to the back. If the new act is a flop, the stage rotates back immediately. The audience never sees a curtain drop or experiences an intermission during the change.
