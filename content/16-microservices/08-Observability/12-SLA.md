# 12-SLA

A Service Level Agreement (SLA) is a contractual commitment between a service provider and a consumer that specifies the level of reliability the provider guarantees. SLAs are backed by SLOs, measured by SLIs, and typically include financial or service credits as consequences for violation.

## Overview

SLAs are business-facing documents, not engineering targets. They define what the customer is promised: "99.9% uptime for the API service, measured over a calendar month." If availability falls below 99.9%, the provider owes the customer a service credit (e.g. 10% of monthly fees). Internal teams set their SLOs tighter than the SLA to ensure they have room to miss internal targets without violating customer commitments.

## Key Characteristics

- **Contractual Guarantee**: An SLA is a legally binding commitment (or at minimum a written promise in a service contract). Violations have real consequences.
- **Measurement Exclusions**: SLAs specify what does not count against the commitment — planned maintenance windows, customer-caused outages, force majeure, and specific exclusions documented in the agreement.
- **Credit Structure**: Consequences for SLA violation are typically service credits (discount on future invoices), not cash penalties. Credits scale with the severity and duration of the violation.
- **SLA vs SLO Gap**: Internal SLOs are set 2–5× tighter than the external SLA to create a buffer. If the SLA promises 99.9%, the internal SLO is 99.95% — ensuring engineering catches problems before customers are affected.
- **Composite SLA**: For multi-service systems, the composite SLA is the product of each service's SLA. If Service A is 99.9% and Service B is 99.9%, the composite is 99.8% (99.9 × 99.9).
- **Reporting**: SLA compliance is reported to customers on dashboards or in regular business reviews. Transparent reporting builds trust and simplifies dispute resolution.
- **Business vs Operational**: Customer-facing SLAs are business documents. Internal SLAs between teams (e.g. "platform team guarantees 99.99% uptime for the deployment pipeline") are operational agreements without legal weight.

## Why It Matters

SLAs translate technical reliability into business terms. They give customers a clear expectation of service quality and recourse if that expectation is not met. For the engineering team, the SLA defines the minimum acceptable reliability floor — the level below which the business suffers penalties — and justifies investment in resilience and observability to stay above it.

## Related Concepts

- [SLO](11-SLO.md) — The SLO is the internal reliability target that backs the SLA commitment.
- [SLI](10-SLI.md) — SLIs are the specific measurements (latency, error rate) that determine SLA compliance.
- [Metrics](03-Metrics.md) — Real-time Prometheus metrics feed the SLA compliance dashboard that internal teams and customers monitor.

---

## Mental Model

An SLA is a delivery guarantee from a shipping company. "If your package doesn't arrive by 10 AM next day, you get a full refund." The shipping company's internal target is "99% of packages delivered by 9 AM" (SLO) — tighter than the guarantee. They track on-time delivery rate daily (SLI). If enough packages miss the 9 AM internal target but still hit 10 AM, the customer's SLA is met. The buffer between 9 AM and 10 AM is the company's safety margin.
