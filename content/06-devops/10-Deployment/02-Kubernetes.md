# Kubernetes

Kubernetes is an open-source container orchestration platform that automates deployment, scaling, and management of containerized applications. It abstracts the underlying infrastructure as a cluster of nodes and provides primitives for scheduling, service discovery, load balancing, and self-healing. Kubernetes is the standard platform for running microservices in production.

## Overview

A Kubernetes cluster consists of control plane components (API server, scheduler, controller manager, etcd) that manage the cluster state, and worker nodes that run containerized workloads. Users declare desired state through YAML manifests (deployments, services, configmaps), and Kubernetes reconciles actual state to match. For microservices, Kubernetes provides the scheduling, networking, and scaling substrate that services run on top of.

## Key Characteristics

- **Pods**: The smallest deployable unit — one or more containers that share a network namespace and storage volumes. Each pod gets a unique IP address. For microservices, typically one container per pod (the service), with optional sidecar containers (Envoy, log shippers, metrics collectors) in the same pod.
- **Deployments**: Declarative management of ReplicaSets and pods. A deployment defines the desired number of replicas, update strategy (rolling, recreate), and pod template. Deployments handle rollouts, rollbacks, and self-healing (recreating failed pods). Never create pods directly — always use deployments.
- **Services**: Stable network endpoints that abstract over dynamic pod IP addresses. Services select pods by labels and provide load-balanced access. Types include ClusterIP (internal), NodePort (external on node port), LoadBalancer (cloud LB), and Headless (direct pod DNS). Service discovery uses DNS: `service-name.namespace.svc.cluster.local`.
- **ConfigMaps and Secrets**: Decouple configuration from container images. ConfigMaps store non-sensitive configuration (environment variables, config files). Secrets store sensitive data (base64-encoded at rest, with encryption at rest optional). Both can be mounted as volumes or environment variables. Changes trigger pod redeployment patterns for live updates.
- **Namespaces**: Virtual clusters within a physical cluster. Namespaces isolate environments (dev, staging, prod), teams, or projects within a single cluster. Resource quotas, network policies, and RBAC are enforced per namespace. Namespace-scoped resources (pods, services, configmaps) are contained, while cluster-scoped resources (nodes, namespaces themselves) span the entire cluster.
- **Resource Limits and Requests**: Every pod specifies CPU and memory requests (guaranteed minimum) and limits (maximum allowed). The scheduler uses requests to place pods on nodes. Limits prevent resource starvation. Quality of Service (QoS) classes — Guaranteed, Burstable, BestEffort — determine eviction priority under resource pressure.
- **Self-Healing**: Kubernetes restarts failed containers, reschedules pods from failed nodes, kills unresponsive pods (based on liveness probes), and routes traffic only to healthy pods (based on readiness probes). This is the foundation for the "cattle not pets" operations model.

## Why It Matters

Kubernetes provides the operational substrate that makes running dozens or hundreds of microservices feasible. It handles the mechanical complexities of deployment, networking, and scaling with a consistent API. Services are declared as YAML, version-controlled, and applied through CI/CD pipelines. Kubernetes' self-healing and scaling capabilities reduce operational burden and increase reliability compared to managing services on VMs directly.

## Related Concepts

- [Docker](01-Docker.md) — Containers are the runtime unit Kubernetes orchestrates
- [Helm](03-Helm.md) — Package manager for Kubernetes manifests
- [HPA](11-HPA.md) — Horizontal scaling mechanism in Kubernetes
- [Service Mesh](04-Service-Mesh.md) — Adds advanced networking features to Kubernetes services
- [Rolling Update](10-Rolling-Update.md) — Default deployment strategy for zero-downtime updates

---

## Mental Model

Kubernetes is like an automated hotel manager for microservices. Pods are guests (each with their own room), deployments ensure the right number of guests are checked in, services are the front desk (directing visitors to the right room), and ConfigMaps/Secrets are room key instructions. If a guest gets sick (pod failure), the manager checks in a replacement automatically (self-healing). If more guests arrive (traffic spike), the manager opens more rooms (scaling).
