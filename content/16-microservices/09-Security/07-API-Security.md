# API Security

API security encompasses the practices, tools, and policies that protect HTTP APIs from unauthorized access, abuse, and attacks. In microservices, the API surface area expands dramatically — every service exposes an API, multiplying attack vectors. A layered defense at the API gateway and individual service level is essential for protecting both external-facing and internal APIs.

## Overview

API security in microsystems spans multiple layers: transport security (TLS/mTLS), authentication (OAuth2, OIDC, API keys), authorization (RBAC, ABAC, claims-based), input validation, rate limiting, and attack prevention (SQL injection, XSS, CSRF). The API gateway acts as the first line of defense, enforcing authentication, rate limiting, and input validation before requests reach internal services. Internal services add a second layer of defense with service-specific validation and authorization.

## Key Characteristics

- **Rate Limiting**: Prevents abuse by limiting the number of requests a client can make within a time window. Common algorithms include token bucket (burst allowance), leaky bucket (smooth rate), and sliding window (accurate time boundaries). Rate limits are configured per-client, per-endpoint, or per-scope. Responses include `X-RateLimit-*` headers so clients can self-regulate. In microservices, rate limiting is enforced at the API gateway to protect downstream services from overload.
- **Input Validation and Sanitization**: Every API endpoint must validate that inputs conform to expected types, formats, and ranges. Never trust client-supplied data — validate schema, length, encoding, and allowed values. Parameterized queries prevent SQL injection. Content-type verification prevents MIME confusion. Input validation at the gateway catches broad attacks, while service-level validation handles domain-specific constraints.
- **CORS (Cross-Origin Resource Sharing)**: Controls which web origins can access the API from browser-based clients. Configured via headers (`Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`). In microservices, the gateway sets CORS policies centrally rather than each service managing its own, ensuring consistent policies.
- **CSRF Protection**: Prevents cross-site request forgery attacks where an authenticated user unknowingly executes actions on another site. For browser-facing APIs, CSRF tokens or SameSite cookie attributes (Strict/Lax) prevent unauthorized state-changing requests. Modern SPAs using JWT-based auth with proper CORS are generally immune to CSRF.
- **SQL Injection Prevention**: Never concatenate user input into SQL queries. Use parameterized queries (prepared statements) or ORMs that handle escaping automatically. Even at the API layer, input validation can detect and reject suspicious patterns. SQL injection remains one of the most common and damaging API vulnerabilities.
- **API Key Management**: For programmatic access, API keys authenticate clients without user context. Keys should be opaque, high-entropy strings, stored as hashes, and never logged. API key rotation, revocation, and scoping limit the impact of key compromise. The gateway validates API keys before requests reach internal services.
- **OWASP API Security Top 10**: Industry-standard threat model covering broken object-level authorization, broken authentication, excessive data exposure, lack of rate limiting, mass assignment, security misconfiguration, injection, improper asset management, and logging/monitoring gaps. Regular audits against this framework are best practice.

## Why It Matters

Microservices dramatically increase the API attack surface compared to monolithic applications. Each service is a potential entry point. Consistent API security practices enforced at the gateway level provide defense-in-depth while service-level checks handle domain-specific threats. Without these layers, a single vulnerable endpoint can compromise the entire system.

## Related Concepts

- [OAuth 2.0](01-OAuth2.md) — Authorization framework for API access control
- [JWT](03-JWT.md) — Token format for propagating authentication and authorization claims
- [Zero Trust](08-Zero-Trust.md) — Every API call is verified regardless of source network
- [Service Mesh](04-Service-Mesh.md) — Mesh provides transport-layer security for internal API calls

---

## Mental Model

API security is like airport security with multiple checkpoints. The API gateway is the main entrance (TSA checkpoint) — it checks ID (auth), verifies the ticket (token), limits how many people can enter (rate limiting), and screens for prohibited items (input validation). Individual services are like specific gates — they perform additional checks (boarding pass scan) relevant to their specific jurisdiction. Multiple layers ensure that no single failure point compromises the entire system.
