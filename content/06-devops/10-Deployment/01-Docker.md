# Docker

Docker is a containerization platform that packages applications and their dependencies into lightweight, portable containers. Containers share the host OS kernel but run in isolated user-space environments, providing consistency across development, staging, and production. Docker is the foundational building block for deploying microservices.

## Overview

Each microservice is packaged as a Docker image containing the application binary, runtime, libraries, and configuration defaults. Images are built from Dockerfiles, stored in registries (Docker Hub, ECR, GCR, ACR), and pulled by orchestration platforms (Kubernetes, ECS, Nomad) to run containers. Docker's layered filesystem enables efficient builds, caching, and distribution — only changed layers are rebuilt or transferred.

## Key Characteristics

- **Dockerfile Best Practices**: Start with an official base image pinned to a specific version (not `latest`). Combine `RUN` commands to minimize layers. Use `.dockerignore` to exclude unnecessary files. Sort multi-line arguments alphabetically. Use `COPY --chown` for permission management. Prefer `COPY` over `ADD` unless extracting archives or fetching remote URLs.
- **Multi-Stage Builds**: Use multiple `FROM` statements in a single Dockerfile. The first stages compile the application with build tools (Go compiler, Node.js, Maven). The final stage copies only the compiled artifacts into a minimal runtime image. This produces small production images (often under 100MB) without build dependencies or source code.
- **Distroless Images**: Minimal container images containing only the application and its runtime dependencies — no shell, package manager, or utilities. Distroless images reduce the attack surface dramatically (no `curl`, `wget`, `bash` for an attacker to use) and produce smaller images. Google's distroless project provides base images for Go, Python, Java, and Node.js.
- **Layer Caching**: Docker caches each layer after building. The order of instructions in the Dockerfile significantly impacts build performance. Place frequently changing instructions (code copy, dependency install) near the end. Place infrequently changing instructions (base image, system packages) at the beginning. This maximizes cache reuse during development CI.
- **Health Checks**: The `HEALTHCHECK` instruction tells Docker how to test if the container is functioning. Combined with Kubernetes liveness/readiness probes, health checks enable automatic recovery from application failures. A simple HTTP health endpoint (`/healthz`) is preferred over process-based checks.
- **Resource Constraints**: Docker can limit CPU, memory, and block I/O per container. Set `--memory` and `--cpus` limits in production to prevent one service from starving others. These map to Kubernetes resource requests and limits.

## Why It Matters

Docker provides the packaging and isolation that makes microservices practical. Each service runs in its own container with its own dependencies, eliminating the "it works on my machine" problem. Containers start in seconds, enabling rapid scaling and deployment. The image registry pattern enables immutable, versioned artifacts that flow through CI/CD pipelines without rebuilding between environments.

## Related Concepts

- [Kubernetes](02-Kubernetes.md) — Orchestrates Docker containers at scale
- [Helm](03-Helm.md) — Packages Kubernetes configurations for Docker-based services
- [Blue-Green](08-BlueGreen.md) — Deployment strategy using Docker images as immutable artifacts
- [Sidecar](07-Sidecar.md) — Co-located container pattern (e.g., Envoy proxy alongside app container)

---

## Mental Model

Docker is like a shipping container for software. Just as a shipping container standardizes cargo transport across ships, trains, and trucks (developer laptops, test environments, production servers), Docker standardizes how applications are packaged, shipped, and run. The container's contents (application + dependencies) are sealed and consistent regardless of where the container is opened. Multi-stage builds are like having a factory assemble the product, then packaging only the finished goods for shipment — leaving the assembly line behind.
