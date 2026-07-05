# Authentication

The process of verifying who a client is at the API Gateway layer before allowing access to internal services. Centralizing authentication at the gateway prevents each microservice from implementing its own auth logic.

## Overview

The gateway acts as the authentication enforcement point. It validates credentials presented by the client — JWTs, API keys, OAuth2 tokens, session cookies — and only forwards authenticated requests to backend services. Common flows include JWT validation (verify signature, check expiry, decode claims), OAuth2 token introspection (call the authorization server to validate opaque tokens), and API key lookup (match against a stored key in a database or config). The authenticated identity is typically forwarded as a header (X-User-Id, X-User-Roles).

## Key Characteristics

- **Centralized Credential Validation**: All auth logic lives in one place — signature verification, token expiry checks, revocation list lookups — rather than duplicated across every service.
- **Token Forwarding or Translation**: The gateway can pass the original token downstream, or strip it and inject a service-specific token (e.g., a short-lived JWT for inter-service RPC).
- **Pluggable Strategies**: Support multiple auth methods simultaneously — JWT for mobile clients, session cookies for browser users, API keys for machine-to-machine — and route based on the client type.

## Why It Matters

Decentralized authentication forces every microservice to fetch and verify the same public keys, maintain the same token validation logic, and handle the same edge cases (expired tokens, malformed JWTs, clock skew). This duplication breeds inconsistency and security gaps. Centralizing at the gateway ensures every request is authenticated exactly once, with uniform policies, before it reaches any internal service. It also simplifies audits — the gateway logs are the single source of truth for authentication attempts.

## Related Concepts

- [Authorization](08-Authorization.md) — What an authenticated user is allowed to do; authentication always precedes authorization.
- [API Security](09-API-Security.md) — Authentication is a cornerstone of API security.
- [API Gateway](01-API-Gateway.md) — The gateway is the authentication enforcement boundary.

## Mental Model

Authentication at the gateway is like a building security desk. Everyone entering the building shows their ID badge (JWT, API key) to the security guard. The guard verifies the badge is valid (not expired, matches the person, signed by a trusted issuer). Once cleared, the guard lets them through the turnstile. The individual offices inside don't need to check ID again — they trust the person already passed security.
