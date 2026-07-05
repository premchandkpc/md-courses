# 04-Twelve-Factor-App

The Twelve-Factor App is a methodology for building software-as-a-service applications that are portable, resilient, and deployable to cloud platforms. These principles are the foundation of modern microservices design.

## Overview

Published by Heroku engineers in 2011, the twelve factors codify patterns for cloud-native applications. Each factor addresses a specific concern in distributed application development.

## The 12 Factors

1. **Codebase** — One codebase per service, tracked in revision control; many deployments (staging, prod)
2. **Dependencies** — Explicitly declare and isolate dependencies (package manager, containers)
3. **Config** — Store config in environment variables, never in code
4. **Backing Services** — Treat databases, message queues, caches as attached resources (swap via URL)
5. **Build, Release, Run** — Strict separation between build, release, and run stages
6. **Processes** — Execute the app as one or more stateless processes (no sticky sessions)
7. **Port Binding** — Export services via port binding (self-contained HTTP server)
8. **Concurrency** — Scale out via the process model (horizontal scaling)
9. **Disposability** — Fast startup and graceful shutdown for robustness
10. **Dev/Prod Parity** — Keep dev, staging, and production as similar as possible
11. **Logs** — Treat logs as event streams (write to stdout, not files)
12. **Admin Processes** — Run admin/management tasks as one-off processes

## Why It Matters

The twelve factors directly enable microservices best practices: stateless processes (scale-out), config injection (environment-specific deploys), disposability (Kubernetes pod lifecycle), and logging as event streams (ELK stack). Every microservice should follow these principles.

## Related Concepts

- [Microservice Principles](/16-microservices/00-Introduction/05-Microservice-Principles.md)
- [Externalized Configuration](/06-devops/10-Deployment/03-Helm.md)
- [Graceful Shutdown](/16-microservices/07-Resilience/10-Graceful-Shutdown.md)

---

## Mental Model

Twelve-Factor App = A well-organized kitchen. Ingredients (dependencies) are clearly labeled and stored. Recipes (config) are on a board, not hidden in a drawer. Dishes are cooked in portion-sized batches (processes) and plated immediately (port binding). If a burner breaks, you can swap to another without resetting everything (disposability). The kitchen is set up the same whether you're cooking at home (dev) or in a restaurant (prod).
