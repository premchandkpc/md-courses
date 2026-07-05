# 17-Amazon

Amazon's journey from a monolith (late 1990s) to service-oriented architecture (early 2000s) to today's microservices ecosystem is the foundational case study for modern distributed systems. The infamous "API mandate" and "two-pizza team" concepts originated here.

## Problem
In the late 1990s, Amazon's e-commerce platform was a single monolithic application (code-named "Obidos"). As the company grew rapidly, the monolith became a bottleneck: teams stepped on each other's code, deployments were slow and risky, and scaling required scaling the entire application rather than individual components. A single deploy could take weeks of coordination.

## Architecture
- **API Mandate (2002)**: CEO Jeff Bezos mandated that all teams must communicate through service interfaces (APIs). No direct database access, no shared code, no point-to-point connections. All services must be designed to be externally consumable. Teams that didn't comply were fired.
- **Service-Oriented Architecture**: The monolith was decomposed into services like catalog, cart, checkout, payment, recommendations, inventory, and fulfillment. Each service owned its data and exposed APIs. The decomposition was driven by business capabilities, not technical layers.
- **Two-Pizza Teams**: Teams were kept small (6-10 people, the size that two pizzas could feed). Each team owned a service end-to-end — design, development, testing, deployment, and operations. This ownership model forced operational excellence and reduced coordination overhead.
- **DynamoDB (2007)**: Facing database scalability challenges, Amazon built DynamoDB as a key-value and document database designed for high scale with predictable performance. It pioneered the Dynamo paper's consistent hashing and eventual consistency model.
- **AWS (2006-present)**: The internal infrastructure developed to run Amazon's services — compute, storage, networking, databases — was productized as Amazon Web Services, creating a $100B+ business.

## Lessons Learned
- **APIs are the contract**: When services communicate only through well-defined APIs, teams can evolve independently. The API contract is more important than the implementation. Breaking changes must be carefully versioned and communicated.
- **Ownership drives quality**: Teams that own their services in production (on-call, monitoring, debugging) build better software. The pain of operating a poorly-designed service provides direct feedback to the developers. This is "you build it, you run it."
- **Start monolith, extract with discipline**: Amazon didn't start with microservices. They started monolithic, felt the pain, and methodically extracted services. The extraction was driven by clear business needs, not architectural trends.
- **Infrastructure as a product**: Building internal infrastructure with the same rigor as external products (APIs, documentation, SLAs, pricing) creates reusable platforms. AWS was the natural outcome of this philosophy.

## Related Concepts
- [01-Ecommerce](01-Ecommerce.md) — E-commerce system design patterns derived from Amazon's architecture
- [17-Airbnb](17-Airbnb.md) — Another monolith-to-services migration story

---

## Mental Model
Amazon's API mandate was like a city requiring every building to have a standard front door with a mail slot, regardless of what happens inside. Neighboring buildings don't need to know your internal plumbing — they just drop letters through the slot. This let each building renovate its interior independently, as long as the slot remained functional.
