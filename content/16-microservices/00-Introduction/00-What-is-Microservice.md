# 00-What-is-Microservice

A microservice is an independently deployable, loosely coupled service that owns a specific business capability. Each microservice runs as its own process, communicates via lightweight protocols (HTTP/gRPC/async messaging), and can be developed, deployed, and scaled independently.

## Overview

Microservices architecture decomposes a large application into smaller, focused services. Each service:
- Owns its domain data (database-per-service)
- Has a well-defined API contract
- Can use its own tech stack (polyglot)
- Is deployed independently via CI/CD
- Is developed by a small, focused team

## Key Characteristics

- **Single Responsibility**: One business capability per service
- **Loose Coupling**: Services can change independently — changing one doesn't require changing others
- **High Cohesion**: Related behavior stays together within the same service boundary
- **Independent Deployability**: Each service has its own CI/CD pipeline and deployment cadence
- **Bounded Context**: Clear domain boundaries defined via Domain-Driven Design
- **Owned Data**: Each service owns its database exclusively

## Why It Matters

Microservices enable organizations to scale development velocity by aligning teams with service boundaries (Conway's Law). They allow independent scaling of hot services, reduce deployment risk through isolation, and enable technology diversity where each service uses the best tool for its job.

## Related Concepts

- [Monolith vs Microservices](/16-microservices/00-Introduction/01-Monolith-vs-Microservices.md)
- [Microservice Principles](/16-microservices/00-Introduction/05-Microservice-Principles.md)
- [Bounded Context](/17-software-architecture/01-Domain-Driven-Design/03-Bounded-Context.md)

---

## Mental Model

Microservices = A hospital with specialized departments. Each department (cardiology, radiology, pharmacy) has its own staff, equipment, and procedures. They communicate through standardized channels (referrals, charts). If the X-ray machine breaks, only radiology is affected — the pharmacy doesn't stop working. Just like microservices, departments can upgrade equipment independently without shutting down the whole hospital.
