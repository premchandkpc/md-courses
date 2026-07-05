# Pact

Pact is a consumer-driven contract testing framework. Consumers define their API expectations in a Pact file, and providers verify that their actual API satisfies those expectations. Pact enables safe, independent service deployment.

## Overview
Pact flips the traditional testing relationship: instead of the provider defining the API spec and consumers conforming to it, the consumer defines what it needs and the provider must satisfy those needs. The consumer writes tests that record HTTP interactions (request → expected response) into a Pact file. This file is shared with the provider team, who runs Pact verification tests to confirm their service matches the recorded expectations. If all contracts pass, both sides can deploy independently.

## Key Characteristics
- **Consumer-Driven Contracts**: The consumer writes the contract by recording actual test interactions.
- **Pact File Format**: A JSON file containing the consumer's name, provider's name, interactions, and matchers.
- **Pact Broker**: Central repository for publishing and retrieving Pact files, with webhook-based verification triggers.
- **Provider Verification**: The provider replays each consumer interaction against its real API and checks the response.
- **Flexible Matching**: Pact supports exact matching, type matching, regex matching, and body structure matching.
- **Provider States**: Allows consumers to specify preconditions (e.g., "user exists") that the provider sets up before verification.

## Why It Matters
In a microservices ecosystem with many consumers, the provider team can't track every downstream API usage by reading code. Pact provides an automated way to discover what consumers expect. When the provider changes an API, Pact verification immediately shows which consumer contracts would break. This shifts the coordination burden from human communication (emails, meetings) to automated verification in CI.

## Related Concepts
- [Contract Testing](03-Contract-Testing.md) — the broader methodology; Pact is the most widely adopted implementation.
- [Integration Testing](02-Integration-Testing.md) — Pact replaces some integration tests by verifying contracts without running both services.
- [End-to-End Testing](05-End-to-End.md) — Pact contracts complement E2E tests; Pact catches API mismatches earlier and faster.

---

## Mental Model
A restaurant menu (provider) and a regular customer (consumer). The customer visits frequently and has specific expectations: the house salad always has vinaigrette dressing (Pact contract). The kitchen changes the menu — now salads come with ranch by default. The Pact verification alerts: "Your regular customer expects vinaigrette on the house salad." The kitchen adds a note to the menu or offers to switch dressing. The customer doesn't have to visit to discover the change.
