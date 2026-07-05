# Linkerd

Linkerd is a lightweight, ultra-fast service mesh for Kubernetes. It uses a Rust-based proxy (`linkerd2-proxy`) instead of Envoy, resulting in significantly lower resource consumption (memory and CPU) and startup latency. Linkerd prioritizes simplicity, security, and operational ease over the extensive feature set of Istio. It is the CNCF-graduated service mesh with the lowest barrier to adoption.

## Overview

Linkerd consists of a control plane (destination, identity, proxy-injector, and tap components) and a data plane of Rust sidecar proxies. The control plane is minimal — just a few deployments with low resource requirements. The sidecar proxy is implemented in Rust for memory safety and performance, using approximately 10MB RAM per proxy instance (compared to 50-100MB for Envoy). Linkerd provides automatic mTLS, HTTP/gRPC load balancing, observability, and service profiles for per-route metrics.

## Key Characteristics

- **Rust Proxy**: The `linkerd2-proxy` is a micro-proxy written in Rust. It uses less than 10MB RSS per instance and starts in milliseconds. Rust's memory safety eliminates entire classes of security vulnerabilities (buffer overflows, use-after-free). The proxy's small codebase reduces the attack surface compared to Envoy's large C++ codebase.
- **Automatic mTLS**: Linkerd enables mTLS between all meshed pods by default. Identities are tied to Kubernetes service accounts using SPIFFE-compatible certificates. The identity controller issues certificates valid for 24 hours, automatically rotated. Linkerd's mTLS is "on by default" — no configuration required.
- **Service Profiles**: Linkerd-specific CRDs that define per-route metrics, retry budgets, and timeouts. A service profile describes the routes a service exposes (gRPC methods or HTTP routes). Once defined, Linkerd provides success rates, latency distributions, and request volumes per route. Service profiles enable fine-grained reliability configuration without application changes.
- **Tap**: The `linkerd viz tap` command streams live requests and responses for any meshed pod. It shows the source, destination, HTTP method, path, status code, latency, and headers for each request. Tap is invaluable for debugging traffic flows and verifying mTLS is working. In production, tap is typically used with authorization and sampling to avoid performance impact.
- **Low Resource Footprint**: The Linkerd control plane uses approximately 100MB total across all components. The proxy uses ~10MB per instance. This makes Linkerd suitable for resource-constrained environments (small clusters, edge devices) and cost-effective at scale. Linkerd can run alongside applications without requiring cluster autoscaling just for the mesh.
- **Simplicity**: Linkerd has fewer components, fewer CRDs, and fewer configuration options than Istio. There is no separate ingress gateway (use any Ingress controller). The proxy injection is label-based (`linkerd.io/inject: enabled` on a namespace). Linkerd's philosophy is "do the common things perfectly" rather than "support every edge case."

## Why It Matters

Linkerd is ideal for teams that want the benefits of a service mesh — automatic mTLS, observability, and reliability — without the operational complexity and resource overhead of Istio. Its Rust proxy provides a security and performance advantage. Linkerd's "on by default" mTLS means teams get encryption without configuration. The tradeoff is fewer features for complex traffic management, but for most microservices deployments, Linkerd's feature set is sufficient.

## Related Concepts

- [Service Mesh](04-Service-Mesh.md) — Linkerd is a lightweight service mesh implementation
- [Sidecar](07-Sidecar.md) — Rust proxy implements the sidecar pattern
- [mTLS](04-mTLS.md) — Automatic mTLS is Linkerd's primary security feature
- [Istio](05-Istio.md) — Feature-rich alternative; Envoy-based vs Rust proxy
- [Observability](04-Service-Mesh.md) — Linkerd provides metrics, tap, and tracing

---

## Mental Model

Linkerd is like a bicycle courier service for microservices. The Rust proxy is a lightweight messenger bike — nimble, cheap to maintain, and gets the job done with minimal fuel (10MB RAM). Istio, by contrast, is a fleet of armored trucks: more powerful, more secure against threats, but far more expensive and resource-intensive. For most city deliveries (microservices), the bike is sufficient, faster to deploy, and costs a fraction of the truck fleet. When you need to split traffic across routes or inject faults, the bike can handle it too — just with fewer bells and whistles.
