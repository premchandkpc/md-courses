# 02-Scenario-Questions

Real-world scenario questions that test practical decision-making under constraints — incident response, migration planning, scaling decisions, and architectural tradeoffs in ambiguous situations.

## Scenario 1: Black Friday Traffic Spike
**Situation**: Your e-commerce platform expects 10x normal traffic for Black Friday. The monolith backend has never been load-tested past 3x. You have 6 weeks.
**Questions**: How do you prepare? What do you prioritize? When do you scale vertically vs horizontally?
**Expected approach**: Load test to identify bottlenecks first. Add read replicas, scale horizontally with a load balancer. Aggressively cache product pages and catalog data. Rate-limit aggressive crawlers. Feature-flag non-critical functionality (recommendations, reviews). Be ready to shed load with a fallback page. Plan for database connection pool exhaustion — increase max connections and add PgBouncer/pgpool.

## Scenario 2: Service Degradation Without Total Failure
**Situation**: A core service is returning 2-second latencies (up from 20ms). The P95 is normal but P99 is 5s. Dashboards don't show errors.
**Questions**: How do you diagnose? Where do you look first?
**Expected approach**: P99/P50 gap suggests a small percentage of requests are slow. Check for slow database queries (missing index, sequential scan), GC pauses (JVM/Node event loop lag), hot partitions in Kafka/DB, or a downstream service that's intermittently slow. Use distributed tracing to find the slowest span. Add detailed metrics on the slow path. Correlate with recent deploys.

## Scenario 3: Migration from Monolith to Microservices
**Situation**: A 5-year-old Rails monolith with 200K LOC. Team of 30 engineers stepping on each other's toes. Deploy once a week with high failure rate.
**Questions**: Where do you start? What's the first service you extract?
**Expected approach**: Strangler fig pattern — identify bounded contexts with clear boundaries (auth, payments, notifications). Extract the service with the most independent logic and clearest API surface (auth is often good). Run both monolith and new service in parallel with a feature flag. Monitor for regressions. Extract one service at a time, not all at once.

## Scenario 4: Database Query Explosion from Microservices
**Situation**: After moving to microservices, a feature that previously used one DB query now makes 12 API calls. Latency went from 20ms to 200ms.
**Questions**: How do you fix this?
**Expected approach**: API composition pattern with a backend-for-frontend (BFF) that parallelizes independent calls. Consider CQRS with a read model tailored to the feature. Evaluate if the service boundaries are correct — maybe these belong in the same service. Use GraphQL for flexible client-driven queries. Cache frequently used data (user profile, product details) client-side.

## Scenario 5: Queue Backlog During Peak
**Situation**: Your order processing queue backs up to 500K messages during a flash sale. New orders take 20 minutes to process. Messages are idempotent.
**Questions**: What do you do right now? How do you prevent recurrence?
**Expected approach**: Immediately: scale up consumers (auto-scaling group or increase concurrency). If processing speed is bottlenecked by a database, increase DB capacity or move to batch writes. Prevention: capacity planning for known peak events, pre-warm consumer pools, implement priority queues (flash sale orders get higher priority), and set up alerting at 50% of expected capacity.

## Related Concepts
- [01-Interview-Questions](01-Interview-Questions.md) — General microservices interview questions
- [05-Production-Issues](05-Production-Issues.md) — Common production failure patterns
- [04-Debugging](04-Debugging.md) — Distributed debugging approaches

---

## Mental Model
Scenario questions are fire drills for your brain. The interviewer presents smoke, ambiguous sounds, and panicked voices — and wants to see if you can calmly identify the fire, its source, and the best extinguisher without burning the building down in the process.
