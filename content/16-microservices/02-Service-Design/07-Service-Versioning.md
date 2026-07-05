# 07-Service-Versioning

Service versioning manages how APIs change over time without breaking existing consumers. It answers the question: "When I need to change my API, how do my clients survive the transition?"

## Overview

In a monolith, internal API changes are managed by refactoring callers and callees in the same deploy. In microservices, the provider and consumer deploy independently, so an API change on one side can break the other if not managed carefully. Versioning strategies provide a contract for change: the provider signals what changed, and the consumer decides when to adapt.

## Key Characteristics

- **URL Path Versioning** (`/v1/orders`, `/v2/orders`): Simple, explicit, easy to route. Can lead to URL bloat and encourages long-lived old versions.
- **Header Versioning** (`Accept: application/vnd.company.v1+json`): Keeps URLs clean. Version lives in the header, making it invisible in URLs but harder to test manually.
- **Content Negotiation**: Varying representation based on `Accept` header or media type parameters. Most flexible but most complex to implement and document.
- **Query Parameter Versioning** (`?version=1`): Simple but easily lost in logs and caching. Least recommended.

## Why It Matters

Without a versioning strategy, every API change forces a coordinated deploy of all consumers — the exact coordination overhead microservices are meant to eliminate. Versioning gives consumers time to migrate on their schedule. The best strategy depends on your ecosystem: URL path versioning is the most common and pragmatic default. Retire old versions aggressively to avoid maintaining a long tail of deprecated APIs.

## Related Concepts

- [08-Backward-Compatibility](08-Backward-Compatibility.md) — often better than versioning
- [10-Schema-Evolution](10-Schema-Evolution.md) — wire-compatible schema changes can avoid version bumps
- [02-REST](../03-Communication/02-REST.md) — REST API versioning patterns

---

## Mental Model

API versioning is like software version numbers for an app. Users on v1.0 keep working while users on v2.0 use new features. Eventually you stop supporting v1.0 (end-of-life), but you give users a migration window. Without versioning, every "upgrade" would force every user to update simultaneously.
