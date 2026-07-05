# 02-Service-Granularity

Service granularity refers to the size and scope of a microservice — how many responsibilities it encompasses. The wrong granularity is one of the most common and costly mistakes in microservices adoption.

## Overview

Too fine-grained and you get orchestration hell: dozens of services must coordinate for a single user request, creating latency, debugging nightmares, and cascading failures. Too coarse-grained and you have a distributed monolith: a large service that is hard to deploy independently and still tightly coupled internally. The sweet spot is services that are independently deployable, own a coherent domain, and communicate infrequently.

## Key Characteristics

- **Cohesion**: A service should contain highly related functions. If you can describe what a service does in a sentence without using "and," the granularity is probably right.
- **Team Alignment**: Granularity should match team size and expertise. A 10-person team can own a broader service; a 2-person team needs narrower scope.
- **Deployment Independence**: If two functions must always be deployed together, they belong in the same service. If they can be released on different schedules, consider splitting.
- **Data Locality**: Services that need the same data for every operation may be too fine-grained. Consider merging if cross-service queries dominate.

## Why It Matters

Granularity directly impacts team autonomy, deployment frequency, operational complexity, and system performance. Over-splitting multiplies infrastructure costs and debugging surface area. Under-splitting negates the benefits of microservices. Evolution over time is expected — start coarser and split as you learn where boundaries should be.

## Related Concepts

- [01-Service-Boundaries](01-Service-Boundaries.md) — boundaries define granularity
- [03-Single-Responsibility](03-Single-Responsibility.md) — the principle that guides granularity decisions
- [07-Message-Brokers](../03-Communication/07-Message-Brokers.md) — fine-grained services often need async communication

---

## Mental Model

A bonsai tree must be pruned thoughtfully — cut too little and it's just a bush, cut too much and it dies. Service granularity is the same: split where there's natural separation, but keep enough tissue to stand independently. It's easier to split a healthy service later than to merge distributed ones.
