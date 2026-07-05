# JSON Web Token (JWT)

JWT is a compact, URL-safe token format for representing claims between two parties. The token consists of three base64url-encoded segments (header, payload, signature) separated by dots. JWTs are self-contained — all claims and metadata are embedded in the payload, eliminating the need for database lookups on every request.

## Overview

JWTs are the most widely used token format in microservices security. They encode a set of claims as a JSON object that is digitally signed or MACed. When a service receives a JWT, it can verify the signature using a public key (RS256, ES256) or shared secret (HS256), then extract the claims without contacting any other service. For inter-service communication, JWTs can carry service identity and permissions, enabling decentralized authorization.

## Key Characteristics

- **Header**: Contains the token type (`typ: "JWT"`) and the signing algorithm (`alg: "RS256"`). The algorithm determines how the signature is verified. Never accept tokens with `alg: "none"` in production — this is a common JWT security vulnerability.
- **Payload**: Contains claims — statements about an entity (typically the user or service) and additional metadata. Standard claims include `iss` (issuer), `sub` (subject), `aud` (audience), `exp` (expiration), `nbf` (not before), and `iat` (issued at). Custom claims carry application-specific data like roles or permissions.
- **Signature**: Produced by signing the base64url-encoded header and payload with the chosen algorithm. For asymmetric algorithms (RS256, ES256), the signature is verified with a public key distributed via JWKS (JSON Web Key Set). For symmetric algorithms (HS256), both signer and verifier share a secret.
- **RS256 (RSA with SHA-256)**: Asymmetric signing — private key signs, public key verifies. Allows multiple services to verify tokens without sharing secrets. The public keys are published at a JWKS endpoint for automated rotation.
- **HS256 (HMAC with SHA-256)**: Symmetric signing — same secret used for signing and verification. Simpler but requires every verifying service to know the secret, making key rotation harder and increasing the blast radius if compromised.
- **Expiration**: The `exp` claim defines when the token expires. Services must reject expired tokens. Short expiration times (5-15 minutes for access tokens) limit the damage window for leaked tokens. Refresh tokens enable obtaining new access tokens without re-authentication.

## Why It Matters

JWTs are essential in microservices for stateless authentication and authorization. Because tokens are self-contained, any service can validate them locally without calling a central authority — critical for low-latency, high-throughput systems. JWTs also enable transitive trust: if service A validates a JWT and passes it to service B, service B can independently verify it. This eliminates the "trust chain" problem where services must blindly trust their upstream neighbors.

## Related Concepts

- [OAuth 2.0](01-OAuth2.md) — OAuth 2.0 uses JWTs as access tokens
- [OIDC](02-OIDC.md) — OIDC ID Tokens are always JWTs with standard identity claims
- [API Security](07-API-Security.md) — API gateways validate JWTs at the ingress and propagate claims
- [Zero Trust](08-Zero-Trust.md) — JWT validation is a core enforcement point in zero trust architectures

---

## Mental Model

A JWT is like a tamper-proof convention badge. Your name, role, and access level are printed on the badge itself (payload). The holographic seal (signature) ensures nobody can alter the badge details. Any door guard can verify the hologram using a public guide (public key) — they don't need to call HQ to check if you're authorized. When the badge expires (exp), it simply stops working.
