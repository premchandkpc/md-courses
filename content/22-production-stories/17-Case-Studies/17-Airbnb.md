# 17-Airbnb

Airbnb's service decomposition journey — from a Ruby on Rails monolith to a service-oriented architecture — is notable for its pragmatic approach to migration, monorepo management, and the company's emphasis on data infrastructure and open-source contributions.

## Problem
Airbnb's platform launched in 2008 as a Ruby on Rails monolith. By 2015, the monolith had grown to millions of lines of code, hundreds of database tables, and was being modified by dozens of engineering teams. Key challenges: merge conflicts on every deploy, slow CI pipelines (hours), scaling issues during peak travel seasons, and difficulty adding new product lines (Experiences, Luxe, China platform).

## Architecture
- **Monorepo with Service-oriented architecture**: Unlike most companies that decompose into a multi-repo structure, Airbnb maintained a monorepo while transitioning to SOA. Services are packages within the monorepo that are independently deployable. This gives Google-like code sharing with service-level independence.
- **SOA decomposition approach**: Airbnb extracted services using the "domain" pattern — booking service, payment service, pricing service, messaging service, search service, and trust/safety service. Each service owns its data. The migration used the strangler fig pattern: new features built as services, old features gradually rewritten.
- **SmartStack (service discovery)**: Airbnb built SmartStack for service discovery — running a Nerve (health check agent) on each host to register services with a Zookeeper-backed registry, and Synapse (client-side load balancer) on each host to route requests to healthy backends.
- **Spindle (thrift-based RPC)**: For internal service communication, Airbnb used Thrift with Spindle — a Ruby RPC wrapper. Thrift provides typed schemas, efficient serialization, and multi-language support. Services are defined in .thrift files and code is generated for both server and client.
- **Aerosolve (ML infrastructure)**: Airbnb built Aerosolve (open-sourced 2015) as a machine learning platform for ranking search results, pricing recommendations, and fraud detection. It focused on interpretability — understanding why a specific recommendation was made.
- **Data Infrastructure (Airflow, Superset, Amundsen)**: Airbnb created and open-sourced several data tools: Apache Airflow (workflow orchestration), Apache Superset (data exploration/visualization), and Amundsen (data discovery/metadata search). These reflect Airbnb's investment in making data accessible and actionable across the company.

## Lessons Learned
- **Monorepo + SOA is viable**: Airbnb showed that a monorepo doesn't prevent service-oriented architecture. The key is having clear ownership boundaries within the monorepo and deployment pipelines that can deploy individual services independently.
- **Data infrastructure is a force multiplier**: Airbnb's investment in data tools (Airflow for pipelines, Superset for visualization, Amundsen for discovery) paid off by making data-driven decisions accessible to every team. Open-sourcing these tools built community and attracted talent.
- **Pragmatic migration over perfect decomposition**: Airbnb didn't aim for perfect service boundaries from the start. They migrated incrementally, accepting that services might be "not-quite-right" and iterating. The goal was to unblock teams, not to achieve architectural purity.
- **Service extraction reveals hidden coupling**: When extracting a service (e.g., payments from the monolith), Airbnb discovered many implicit dependencies (shared models, callbacks, database queries) that had to be refactored. Each extraction is an opportunity to clean up the architecture, not just move code around.

## Related Concepts
- [17-Amazon](17-Amazon.md) — Amazon's API mandate and service ownership philosophy
- [01-Ecommerce](../15-System-Design/01-Ecommerce.md) — E-commerce patterns used in booking and marketplace platforms
- [09-Banking](../15-System-Design/09-Banking.md) — Payment and trust/safety system design for marketplace platforms

---

## Mental Model
Airbnb's monorepo-with-services is like a large apartment building where each unit (service) is owned by a different tenant who can renovate their unit independently (independent deployability) — but they share the same address (monorepo), maintenance crew (CI/CD), and building regulations (standards). Tenants can borrow a cup of sugar from neighbors (shared code) without needing to move buildings, but they can't knock down walls without talking to the neighbors first (coordination on shared interfaces).
