# Contract Testing

Contract testing verifies that the API contract between a consumer and a provider is correctly implemented on both sides. It ensures services can be deployed independently without breaking their consumers.

## Overview
In microservices, each service is owned by a different team and deployed independently. A consumer service depends on a provider service's API — but how can the consumer team safely deploy without knowing whether the provider's latest changes broke their expected contract? Contract testing solves this by encoding the consumer's expectations into a formal contract (e.g., Pact file) and verifying that the provider satisfies it. Both sides are tested against the same contract, enabling independent deployment with confidence.

## Key Characteristics
- **Consumer-Driven**: The consumer defines its expectations of the provider's API (endpoint, request, response).
- **Published Contract**: The consumer's expectations are published as a contract file that the provider must verify against.
- **Broker-Mediated**: A contract broker (e.g., Pact Broker) stores contracts, verifies them, and reports results.
- **Independent Verification**: Both sides are tested independently using the same contract — no end-to-end test needed.
- **Deployment Gating**: Provider deployments are blocked if they fail contract verification against all consumer contracts.

## Why It Matters
Integration tests require both consumer and provider to be running simultaneously, creating tight coupling between test environments. Contract testing decouples the verification: the consumer team writes expectations, and the provider team runs the verification in their own CI pipeline. This enables parallel development and independent deployment. If the provider changes an API and breaks a contract, the provider team knows before they deploy — not after consumers break in production.

## Related Concepts
- [Pact](04-Pact.md) — the most popular consumer-driven contract testing framework.
- [Integration Testing](02-Integration-Testing.md) — tests real interactions; contract tests focus specifically on API agreements.
- [End-to-End Testing](05-End-to-End.md) — tests complete flows; contract tests provide faster feedback at a granular level.

---

## Mental Model
A signed shipping contract between a supplier and a retailer. The contract specifies: deliver 100 units every Monday, standard pallets, dock 4 receiving. The supplier verifies they can meet these terms before each shipment. The retailer verifies they receive what was contracted. Both parties follow the same contract independently — no need to call each other every Monday to confirm the details.
