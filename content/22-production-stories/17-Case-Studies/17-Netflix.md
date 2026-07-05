# 17-Netflix

Netflix's migration from a monolithic on-premise DVD-by-mail operation to a cloud-native streaming platform is one of the most influential microservices case studies. Their work on chaos engineering (Chaos Monkey), circuit breakers (Hystrix), and API gateways (Zuul) shaped the industry.

## Problem
In 2008, a major database corruption event halted DVD shipments for three days. Netflix realized the relational database model and monolithic architecture could not scale to their streaming ambitions. They needed a system that could survive component failures without customer impact and scale globally on demand.

## Architecture
- **Cloud migration (2008-2016)**: Netflix moved from on-premise data centers to AWS. All infrastructure was rebuilt as stateless services running on cloud instances. The migration used the "strangler fig" pattern — gradually routing traffic from on-prem to cloud, feature by feature.
- **Microservices decomposition**: The streaming platform was decomposed into hundreds of services — user profiles, content catalog, recommendations, search, playback, billing, notifications, device registration, and more. Each service owns its data store (Cassandra, EVCache, S3, or relational DB).
- **Zuul API Gateway**: All client requests route through Zuul, a JVM-based edge service that handles authentication, rate limiting, routing, request/response transformation, and A/B testing. Zuul can handle 100K+ requests/second per instance.
- **Hystrix Circuit Breaker**: Netflix built Hystrix to prevent cascading failures — when a downstream service fails, the circuit breaker opens and subsequent calls fail fast (or serve fallback data). This was foundational for building resilient microservices.
- **Chaos Engineering**: Chaos Monkey randomly terminates production instances during business hours. Chaos Kong simulates entire AWS Region failures. Latency Monkey, Conformity Monkey, and others create a "Simian Army" that continuously tests resilience.
- **Content Delivery (Open Connect)**: Netflix built its own CDN (Open Connect) — custom caching appliances deployed in ISP data centers. Serves ~95% of traffic from within the ISP network, reducing transit costs and improving quality.

## Lessons Learned
- **Build resilience through continuous failure**: Don't wait for failure to happen — deliberately inject it. Chaos engineering is not about breaking things for fun; it's about proving the system can survive failures. If Chaos Monkey finds a weakness, fix it before real traffic triggers it.
- **Services must be independently deployable**: Each microservice has its own deployment pipeline. Changes roll out progressively via canary deployments. A bad deployment affects only one service, not the entire platform.
- **Data ownership per service**: Each service owns its data store. There is no shared database. Services communicate through APIs only. This enables independent scaling and schema evolution but requires careful API versioning.
- **Know when to build vs buy**: Netflix built Open Connect (CDN) because no existing CDN could handle their scale and cost requirements. They built Hystrix and Zuul because no off-the-shelf solutions existed for their resilience needs. They chose AWS for cloud because building their own data centers would be slower.

## Related Concepts
- [03-Netflix](../15-System-Design/03-Netflix.md) — Netflix streaming system design
- [17-Amazon](17-Amazon.md) — API mandate and service ownership culture that influenced Netflix

---

## Mental Model
Netflix's architecture is like a cruise ship designed to stay afloat even if several compartments flood. Chaos engineering is the crew periodically opening a compartment to water, checking the flood doors close properly, and patching any leaks they find. This is done not once but continuously, so when a real storm hits, the ship handles it without drama.
