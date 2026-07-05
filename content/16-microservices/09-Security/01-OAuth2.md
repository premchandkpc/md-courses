# OAuth 2.0

OAuth 2.0 is an authorization framework that enables applications to obtain limited access to user accounts on an HTTP service. It decouples authentication from authorization by issuing access tokens rather than sharing credentials. The framework defines four grant types optimized for different client scenarios (web apps, mobile apps, server-to-server).

## Overview

OAuth 2.0 introduces an authorization layer that separates the role of the client from the resource owner. The authorization server issues tokens to clients after obtaining authorization from the resource owner. Clients present these tokens to resource servers to access protected resources. In microservices, API gateways and service meshes commonly validate OAuth 2.0 tokens at the edge, while internal services rely on mTLS or short-lived tokens for inter-service calls.

## Key Characteristics

- **Authorization Code Grant**: The most secure flow for web apps; the client receives a code via redirect, then exchanges it for tokens using a client secret. The authorization code is returned via frontchannel, while the token exchange happens via backchannel — preventing token exposure to the browser.
- **PKCE Extension**: Required for mobile and native apps where client secrets cannot be stored securely. The client generates a cryptographically random code verifier and transmits its SHA-256 hash (code challenge) in the initial authorization request. During token exchange, the actual verifier must match the challenge, preventing interception attacks.
- **Client Credentials Grant**: For server-to-server communication where no user is involved. The client authenticates directly with the authorization server using its client ID and secret, receiving an access token scoped to the service's own capabilities rather than any user's permissions.
- **Access & Refresh Tokens**: Access tokens are short-lived (minutes to hours) and represent authorization; refresh tokens are long-lived credentials used to obtain new access tokens without requiring the user to re-authenticate. Refresh tokens can be rotated and revoked independently.
- **Scopes**: Granular permission boundaries that limit what a token can access (e.g., `read:orders`, `write:profile`). Scopes are requested at authorization time and asserted on every API call, enabling fine-grained access control.

## Why It Matters

OAuth 2.0 is the foundation for API security in microservices. It centralizes authorization policy in an authorization server rather than scattering credential validation across every service. Service meshes and API gateways validate tokens at ingress, passing validated claims via sidecar proxies or HTTP headers to downstream services. Using OAuth 2.0 avoids the anti-pattern of each service maintaining its own authentication logic or shared secret database.

## Related Concepts

- [OIDC](02-OIDC.md) — Authentication layer built on top of OAuth 2.0; adds ID tokens for user identity
- [JWT](03-JWT.md) — Common token format used by OAuth 2.0 to encode access tokens
- [API Security](07-API-Security.md) — Rate limiting, input validation, and gateway-level token inspection
- [Service Identity](09-Service-Identity.md) — Server-to-server auth with client credentials grant and SPIFFE

---

## Mental Model

OAuth 2.0 is like a hotel key card system. The front desk (authorization server) issues your key card (access token) after verifying your identity. The card works only for specific floors and rooms (scopes) for a limited time (expiration). When your card expires, you return to the front desk — not to the room doors — to get a new one. The refresh token is your receipt; you present it at the desk to get a fresh card without showing your ID again.
