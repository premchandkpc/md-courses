# 09-Contract-Driven-Development

Contract-Driven Development (CDD) uses consumer-driven contracts — tests written by the consumer that define what they expect from the provider — to ensure APIs meet consumer needs without breaking existing integrations.

## Overview

Unlike API-first (which focuses on the provider publishing a spec), CDD reverses the flow: consumers write contracts describing how they intend to use the API. The provider then runs these contracts as part of its CI pipeline, ensuring it never releases a change that breaks a consumer. Pact is the leading tool for this pattern, supporting HTTP and message-based contracts.

## Key Characteristics

- **Consumer-Written Contracts**: The service consumer writes a Pact test specifying the request it will make and the response it expects. This is checked into the consumer's repo.
- **Provider Verification**: The provider runs the consumer's Pact tests against its actual implementation. If any contract fails, the provider's CI pipeline fails — the breaking change is caught before deployment.
- **Broker/Registry**: Pact Broker stores contracts, tracks which versions of which services are compatible, and can prevent deployment of incompatible provider versions.
- **Can-I-Deploy**: A verification step that checks whether a given provider version is compatible with all consumers in production. This enables safe, independent deployments.

## Why It Matters

CDD solves the "provider doesn't know what consumers depend on" problem. Without it, providers make breaking changes unintentionally because they don't know which field or endpoint a consumer relies on. CDD also shifts the power dynamic — consumers have a formal voice in the API design, leading to more usable APIs and fewer integration surprises.

## Related Concepts

- [06-API-First](06-API-First.md) — CDD builds on API-first by adding consumer verification
- [08-Backward-Compatibility](08-Backward-Compatibility.md) — contracts encode what backward compatibility means in practice
- [10-Schema-Evolution](10-Schema-Evolution.md) — contracts must evolve with schemas

---

## Mental Model

Think of CDD as a lease agreement. The tenant (consumer) specifies what they need (number of rooms, pet policy, parking). The landlord (provider) agrees to meet those needs. Before any "renovation" (API change), the landlord checks the lease to ensure the change doesn't violate the tenant's terms. The Pact Broker is the notary that holds the signed agreements.
