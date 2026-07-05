# Chaos Engineering

Chaos Engineering is the practice of intentionally injecting failures into a production or staging system to test its resilience. It builds confidence that the system can withstand unexpected disruptions.

## Overview
Chaos Engineering moves beyond testing for expected scenarios and instead probes the system's behavior under realistic failure conditions: a service crashes, a network link slows to 500ms latency, a disk fills up, a DNS resolution fails, or a dependency returns 500 errors. Netflix's Chaos Monkey (which randomly kills production instances) popularized the approach. Modern chaos engineering tools like Gremlin, Litmus, and Chaos Mesh enable controlled experiments with a blast radius, automated rollback, and steady-state hypothesis validation.

## Key Characteristics
- **Steady State Hypothesis**: Before injecting chaos, define what "normal" looks like (e.g., p99 latency < 200ms, error rate < 0.1%).
- **Blast Radius Control**: Experiments start in staging or limited production scope before expanding.
- **Failure Injection**: Experiments simulate real-world failures — instance termination, network partition, CPU pressure, memory exhaustion, disk I/O spikes, dependency latency.
- **Automated Rollback**: If the steady state degrades beyond the defined threshold, the experiment is automatically rolled back.
- **Continuous Practice**: Chaos is not a one-time activity — it's run continuously to verify resilience as the system evolves.

## Why It Matters
Systems fail in production regardless of how much testing is done pre-deployment. A load balancer can misbehave, a cloud region can go down, a certificate can expire. Chaos Engineering proactively validates that the system's resilience mechanisms (circuit breakers, retries, fallbacks, timeouts) actually work when needed. Teams that practice chaos engineering find weaknesses before they cause customer-impacting incidents.

## Related Concepts
- [Performance Testing](08-Performance-Testing.md) — tests system behavior under load; Chaos Engineering tests under failure.
- [End-to-End Testing](05-End-to-End.md) — verifies correct behavior; Chaos Engineering verifies graceful degradation.
- [Decorator](11-Patterns/04-Decorator.md) — resilience decorators (retry, circuit breaker, timeout) are the mechanisms that chaos engineering validates.

---

## Mental Model
Fire drills in a school building. You don't wait for a real fire to see if the evacuation plan works. You pull the alarm intentionally, observe how students and teachers react, measure how long it takes to clear the building, and identify blocked exits. Then you fix the problems. A real fire is the production incident; the drill is chaos engineering.
