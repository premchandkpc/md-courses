# Zero Trust Architecture

Zero Trust is a security model based on the principle "never trust, always verify." No entity — whether inside or outside the network perimeter — is implicitly trusted. Every access request is authenticated, authorized, and encrypted before being granted. In microservices, Zero Trust maps naturally to the distributed, ephemeral nature of services that cannot rely on fixed network boundaries.

## Overview

Traditional perimeter-based security ("castle and moat") assumes everything inside the corporate network is trustworthy. Zero Trust eliminates this assumption entirely. Every request, from any source to any destination, must prove its identity and earn authorization. In microservices, this means service A cannot call service B just because they share a network — service A must present valid credentials, and service B must verify them. Continuous monitoring detects anomalous behavior even after initial authentication.

## Key Characteristics

- **No Implicit Trust**: Network location (same subnet, same cluster, private IP) confers zero trust. A request from inside the perimeter receives the same scrutiny as one from the public internet. This prevents lateral movement — if an attacker compromises one service, they cannot automatically access others.
- **Continuous Verification**: Trust is not a binary state granted at login. Every request is re-verified based on signal strength: device posture, user behavior, request context, time of day, geolocation, and risk score. A user authenticated 5 minutes ago may be denied access if their behavior becomes anomalous.
- **Microsegmentation**: The network is divided into the smallest possible trust zones — ideally per-service or per-workload. Each service can only communicate directly with services it explicitly needs to reach. Network policies (Kubernetes NetworkPolicies, service mesh authorization policies) enforce these boundaries.
- **mTLS Everywhere**: All service-to-service communication uses mutual TLS. Every connection is encrypted and both sides authenticate with certificates. There is no plaintext internal traffic. Service mesh sidecars enforce this transparently.
- **Identity-Based Access**: Access decisions use identity (user, service, device), not network constructs (IP, hostname). SPIFFE IDs identify services. OIDC claims identify users. Policies reference these identities, making access control portable across environments.
- **Least Privilege**: Every entity receives the minimum permissions required to function. Services access only the specific databases, queues, and APIs they need. Users access only the data their role requires. Permissions are scoped, time-boxed, and regularly audited.
- **Assume Breach**: Design the system assuming an attacker is already present. Encrypt data at rest, rotate credentials aggressively, log everything, and monitor for anomalous patterns. Breach containment (blast radius limitation) is a primary design goal.

## Why It Matters

Microservices cannot be secured with perimeter-based models because they have no single perimeter. Services are deployed across clusters, regions, and cloud providers. Containers are ephemeral — IPs change constantly. Zero Trust aligns with the architecture: identity-based, automated, and policy-driven. It prevents the most damaging microservices attack pattern: compromising one service and using it to attack others laterally.

## Related Concepts

- [mTLS](04-mTLS.md) — The transport mechanism for enforcing zero trust between services
- [Service Identity](09-Service-Identity.md) — Zero trust depends on strong, verifiable service identities
- [API Security](07-API-Security.md) — API gateway enforces zero trust at the ingress
- [Service Mesh](04-Service-Mesh.md) — Mesh implements zero trust policies without application changes
- [Encryption](06-Encryption.md) — Data protection when zero trust's "assume breach" is realized

---

## Mental Model

Zero Trust is like a secure office building where every employee has a badge that must be scanned at every door, not just the main entrance. The mailroom (service A) can access the mailroom, but needs separate authorization to enter accounting (service B). Even the CEO scans their badge at every door. Security guards (sidecar proxies) verify each scan and watch for unusual behavior — someone entering the server room at 3 AM triggers an alert even if their badge is valid.
