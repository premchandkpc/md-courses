# Performance Testing

Performance testing measures a system's speed, throughput, scalability, and stability under various load conditions. It identifies bottlenecks, validates SLAs, and ensures the system can handle expected traffic.

## Overview
Performance testing encompasses several sub-disciplines: load testing (expected traffic), stress testing (beyond expected traffic), endurance testing (sustained traffic over time), and spike testing (sudden traffic surges). In microservices, performance testing is particularly important because a bottleneck in one service (slow database query, overloaded message queue, CPU-bound computation) can cascade and degrade the entire system. Tools like k6, Locust, Gatling, and wrk generate synthetic traffic and measure latency distributions, error rates, and resource utilization.

## Key Characteristics
- **Latency Measurement**: Records percentiles (p50, p95, p99, p99.9) to understand the distribution, not just the average.
- **Throughput Tracking**: Measures requests per second (RPS) or transactions per second (TPS) under varying concurrency.
- **Resource Monitoring**: Correlates performance metrics with CPU, memory, disk I/O, and network utilization.
- **Gradual Load Ramp**: Tests start with low load and increase gradually to observe when and how the system degrades.
- **SLA Validation**: Tests verify that the system meets defined Service Level Agreements (e.g., p99 < 500ms under 1000 RPS).

## Why It Matters
A microservice that works beautifully for a single user can collapse under production traffic. Performance testing exposes capacity limits, inefficient algorithms, connection pool exhaustion, garbage collection pauses, and contention on shared resources. It answers critical questions: How many instances do we need? What's our breaking point? Will we survive Black Friday? Without performance testing, teams deploy blind.

## Related Concepts
- [Chaos Engineering](06-Chaos-Engineering.md) — tests resilience under failure; Performance tests under load.
- [End-to-End Testing](05-End-to-End.md) — verifies functional correctness; Performance tests verify non-functional requirements.
- [Proxy](11-Patterns/02-Proxy.md) — caching proxies can dramatically improve performance; performance tests reveal caching effectiveness.

---

## Mental Model
Stress-testing a bridge before opening it to traffic. Engineers don't just drive a single car across and declare it safe. They load the bridge with progressively heavier trucks, measure how much it sways in the wind (concurrent load), and leave weight on for days to check for material fatigue (endurance). They need to know: at what weight does the bridge start to crack? Performance testing does the same for software — find the cracking point before customers arrive.
