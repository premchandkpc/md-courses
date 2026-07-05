# 11-SLO

A Service Level Objective (SLO) is a target value for a Service Level Indicator — the reliability goal a service aims to meet. SLOs define the threshold between "good enough" and "needs improvement," and they drive the error budget that governs the balance between reliability and feature velocity.

## Overview

An SLO is expressed as a percentage over a time window: "99.9% of requests complete in under 500ms over a rolling 30-day window." The difference between 100% and the SLO target is the error budget — the amount of unreliability the team can tolerate. If the service consumes its entire error budget, the team typically halts feature releases and focuses on reliability until the budget is replenished.

## Key Characteristics

- **Target Percentage**: Typical targets range from 99% (two nines — ~7h downtime/month) to 99.999% (five nines — ~26s downtime/month). Choose the target that meets user expectations, not the highest possible number.
- **Time Window**: SLOs are evaluated over rolling windows (28 days, 30 days, quarter). A longer window smooths out short bursts but delays feedback. Multiple windows (30d + 7d) give both trend and recency views.
- **Error Budget**: `error_budget = 1 - SLO = maximum allowed failure rate`. Consumed by each SLI violation. When error budget is exhausted, deployment velocity is reduced.
- **Burn Rate**: How fast the error budget is being consumed. Burn rate > 1 means budget will be exhausted before the window closes; burn rate alerts trigger incident response.
- **Implementation SLO vs User-Facing SLO**: Internal SLOs (e.g. database query latency) support user-facing SLOs (e.g. API response time). User-facing SLOs are the ones that matter.
- **Multi-Window, Multi-Burn-Rate Alerts**: Advanced alerting uses short windows (1h, 5m) to detect fast burns and long windows (6h, 30d) to detect slow burns, with severity scaling by burn rate.

## Why It Matters

SLOs force teams to decide explicitly how reliable a service needs to be. Without SLOs, reliability is an unbounded discussion — "it should be fast" vs "it's fast enough." With SLOs, the team has a numeric target to aim for, a budget that quantifies how much failure is acceptable, and a governance mechanism that pauses features when reliability slips.

## Related Concepts

- [SLI](10-SLI.md) — The SLI is the measured metric; the SLO is the target for that metric.
- [SLA](12-SLA.md) — An SLA is a contractual SLO with consequences; internal SLOs often have tighter targets than external SLAs.
- [Metrics](03-Metrics.md) — SLIs and SLOs are derived from metrics; PromQL queries evaluate SLO compliance in real-time.

---

## Mental Model

An SLO is a New Year's fitness goal. "I will run 100 miles this month" — that's the target. Each missed run consumes your "run budget." If you skip too many days and burn through the budget by mid-month, you know you're off track and need to adjust — either run more or revise the goal. The budget tells you when to stop making excuses and start running. It also tells you when you have room to skip a day without guilt.
