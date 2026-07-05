# 09-Health-Checks

Health checks are endpoints or probes that report a service's ability to handle requests. They enable load balancers, orchestrators, and service meshes to automate failover, scheduling, and traffic routing decisions based on real-time service state.

## Overview

Three distinct health check types exist in production deployments. Liveness probes answer "is the process alive?" — if not, the orchestrator restarts the container. Readiness probes answer "can this instance accept traffic?" — if not, the load balancer removes it from rotation. Startup probes answer "has initialization completed?" — used to delay liveness and readiness checks during slow starts. Deep health checks additionally verify that critical dependencies (database, cache, downstream services) are reachable.

## Key Characteristics

- **Liveness**: Lightweight — checks that the process is running (e.g. `GET /healthz`). Failure triggers a container restart by the orchestrator (Kubernetes, Nomad).
- **Readiness**: Medium-weight — confirms the service can accept traffic. Typically checks that the HTTP listener is up, connection pools are initialized, and the service isn't overloaded. Failure removes the instance from the load balancer without restarting.
- **Startup**: One-time probe for slow-starting services. Delays liveness and readiness checks until initialization is complete. Failure restarts the container.
- **Deep Health**: Heavy-weight — checks database connectivity, cache reachability, and downstream service health. Not suitable for high-frequency probes; run on a separate, longer interval.
- **Cache Invalidation**: Health check results are often cached for a few seconds to prevent probe storms from overwhelming the service.
- **Grace Period**: New instances are given a startup grace period before health checks begin, preventing premature restarts.

## Why It Matters

Without health checks, load balancers route traffic to dead or degraded instances, causing user-facing errors. Orchestrators restart healthy containers that are temporarily slow due to GC pauses or traffic spikes. Proper health checks ensure that traffic flows only to instances that can actually serve it, and that only truly dead processes are killed and rescheduled.

## Related Concepts

- [Graceful Shutdown](10-Graceful-Shutdown.md) — On shutdown, the readiness probe should report "not ready" before the process stops, allowing the load balancer to drain traffic.
- [Circuit Breaker](01-Circuit-Breaker.md) — Health checks and circuit breakers both detect failures; health checks are proactive (probes), circuit breakers are reactive (call observation).
- [Service Discovery](../02-Service-Interaction/02-Service-Discovery.md) — Health check status feeds into the service registry to update the list of healthy endpoints.

---

## Mental Model

Health checks are like a hotel's room status board. Liveness: is the room's power on? Readiness: is the room clean and ready for a guest? Startup: is the new room finished being painted? The front desk (load balancer) only assigns guests to rooms marked "ready." A room with no power (liveness fail) needs maintenance, not new guests.
