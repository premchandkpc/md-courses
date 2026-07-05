# 10-SLI

A Service Level Indicator (SLI) is a carefully chosen metric that measures a specific aspect of service reliability — latency, error rate, availability, throughput, or durability. SLIs define what to measure, forming the foundation of the service level framework.

## Overview

An SLI is a ratio of good events to total events over a measurement window. For availability, the SLI might be `successful requests / total requests` over a 1-minute window. For latency, it might be the proportion of requests served faster than a threshold (e.g. `count(requests < 200ms) / total requests`). SLIs are derived from raw metrics (e.g. Prometheus counters) but represent a specific, well-defined reliability dimension.

## Key Characteristics

- **Good Event / Total Event Ratio**: The standard SLI form is `good / total` (e.g. successful HTTP responses / all HTTP responses). This produces a value between 0 and 1, typically expressed as a percentage.
- **Measurement Window**: SLIs are computed over rolling windows (1 minute, 5 minutes, 30 days) to smooth out transient spikes while still detecting sustained degradation.
- **Latency SLI**: Proportion of requests below a threshold (e.g. `p99 latency < 500ms`). Multiple thresholds may be defined (fast: <200ms, acceptable: <1s).
- **Availability SLI**: Uptime or success rate. For request-driven services: `HTTP 2xx or 3xx / total requests`. For storage: successful reads/writes / total operations.
- **Freshness SLI**: For batch or data pipeline services: age of the most recent data compared to the expected update interval.
- **Durability SLI**: Probability that stored data survives a given period (e.g. 99.9999999% annual durability for object storage).
- **Error Budget Derivation**: The SLI value is subtracted from 100% to compute error budget consumption: `error_budget_consumed = (1 - SLI) × total_events`.

## Why It Matters

Without SLIs, teams argue about what "reliable" means. An SLI makes reliability measurable and objective. It answers "what does good look like?" in a numeric, queryable form. Every meaningful SLO and SLA depends on well-defined SLIs that capture the user's actual experience of the system.

## Related Concepts

- [SLO](11-SLO.md) — The SLO sets the target value for an SLI (e.g. "SLI ≥ 99.9%").
- [SLA](12-SLA.md) — The SLA is a contractual commitment backed by an SLO, which is in turn measured by an SLI.
- [Metrics](03-Metrics.md) — SLIs are derived from raw metrics via queries (e.g. PromQL expressions).

---

## Mental Model

An SLI is a car's fuel efficiency gauge — specifically "miles per gallon over the last 50 miles." It's a concrete measurement that tells you exactly how the car is performing on that dimension. You decide whether 30 MPG is good or bad separately (that's the SLO). The gauge just reports the number. Different drivers (services) might care about different gauges: fuel efficiency, engine temperature, tire pressure.
