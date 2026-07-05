# Sidecar Proxy

The sidecar pattern deploys an auxiliary container alongside the primary application container in the same pod. The sidecar intercepts all network traffic to and from the application, handling cross-cutting concerns like security, observability, and traffic management. Sidecars are the foundation of service mesh architectures and are commonly used for logging, monitoring, and proxy functionality.

## Overview

In Kubernetes, a sidecar is a container that runs in the same pod as the application container, sharing the same network namespace and volumes. All traffic to and from the application flows through the sidecar, which can enforce policies, collect telemetry, and handle encryption. The application is completely unaware of the sidecar — it communicates over localhost as if no intermediary exists. This separation of concerns allows infrastructure teams to add networking capabilities without involving application developers.

## Key Characteristics

- **Traffic Interception**: The sidecar intercepts all inbound and outbound traffic using iptables rules (Istio's `istio-init` init container configures these) or transparent proxy (Linkerd's proxy redirects traffic). Inbound traffic destined for the application port is redirected through the sidecar, which applies policies before forwarding to the application. Outbound traffic also passes through the sidecar for routing and mTLS.
- **Shared Network Namespace**: The sidecar and application share the same network namespace (they can communicate via localhost). The application binds to a specific port (e.g., 8080), and the sidecar listens on a well-known port (e.g., 15001 for Istio Envoy). Iptables rules redirect port 8080 traffic to the sidecar transparently.
- **Zero Application Changes**: This is the key benefit. The application runs as it always has — listening on its port, calling other services by hostname. The sidecar handles encryption, retries, load balancing, and telemetry without the application knowing. This enables retrofitting a service mesh onto existing deployments without code changes.
- **Resource Overhead**: Each sidecar consumes CPU and memory resources. Envoy sidecars (Istio) use 50-100MB RAM and moderate CPU. Linkerd's Rust proxy uses ~10MB RAM. In clusters with hundreds of services, sidecar overhead must be factored into capacity planning. Sidecar resource limits and requests should be configured to prevent interference with the application.
- **Startup Ordering**: The sidecar must be ready before the application starts — if the application sends requests before the sidecar is configured, traffic bypasses the mesh. Istio uses `holdApplicationUntilProxyStarts` (configured via `values.global.proxy.holdApplicationUntilProxyStarts`). Linkerd injects an init container that configures the proxy network before the application starts.
- **Lifecycle Management**: Sidecars are updated by restarting pods (rolling restart). The service mesh control plane pushes new proxy configuration dynamically (Envoy hot reload, Linkerd proxy update). Sidecar upgrades require coordination to avoid breaking the application's network connectivity during the transition.

## Why It Matters

The sidecar pattern is the enabling technology for service meshes. It decouples networking infrastructure from application logic, allowing platform teams to add mTLS, distributed tracing, circuit breakers, and advanced routing to existing microservices without developer involvement. Without sidecars, each service would need to implement these capabilities using language-specific libraries — a maintenance nightmare in polyglot environments.

## Related Concepts

- [Service Mesh](04-Service-Mesh.md) — Sidecars are the data plane of a service mesh
- [Istio](05-Istio.md) — Uses Envoy sidecar proxies
- [Linkerd](06-Linkerd.md) — Uses Rust-based sidecar proxies
- [mTLS](04-mTLS.md) — Sidecars handle mutual TLS termination
- [Container](01-Docker.md) — Sidecars are co-located containers in the same pod

---

## Mental Model

A sidecar proxy is like a personal security detail for a diplomat. The diplomat (application) goes about their business meeting people, unaware of the security checks happening around them. The security detail (sidecar) intercepts everyone who approaches (inbound traffic), verifies credentials (mTLS), records interactions (telemetry), and escorts them to the diplomat at the right time (routing). When the diplomat needs to visit another building, the detail secures the route (outbound traffic). The diplomat never needs to know about the security protocols — they just walk through doors.
