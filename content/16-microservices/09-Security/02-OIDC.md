# OpenID Connect (OIDC)

OpenID Connect is an authentication protocol built on top of OAuth 2.0 that verifies user identity. Unlike OAuth 2.0, which only provides authorization, OIDC introduces an ID Token (a signed JWT) containing verified user claims. OIDC standardizes how clients discover public keys, retrieve user profile information, and handle session management across applications.

## Overview

OIDC extends OAuth 2.0 by adding an identity layer. The key addition is the ID Token — a signed JWT issued by the authorization server that contains claims about the authenticated user (sub, name, email, etc.). Clients verify the ID Token's signature using keys published at the provider's discovery endpoint. In microservices, OIDC enables single sign-on (SSO) across services: a user authenticates once at the identity provider, and their session is recognized by all services in the mesh.

## Key Characteristics

- **ID Token**: A signed JWT (typically RS256) containing the `sub` (subject) claim that uniquely identifies the user. Standard claims include `name`, `email`, `preferred_username`, and `iss` (issuer). The ID Token is separate from the access token — it conveys identity, not authorization.
- **UserInfo Endpoint**: An authenticated OAuth 2.0 resource that returns additional user claims. Clients can fetch claims that are too large to fit in the ID Token. The endpoint is protected by the access token, and responses are typically JSON with standard OIDC claim names.
- **Discovery**: OIDC providers expose a `/.well-known/openid-configuration` endpoint returning metadata including issuer URL, authorization endpoint, token endpoint, JWKS URI, supported scopes, and response types. Clients dynamically configure themselves from this document, eliminating hardcoded provider URLs.
- **Hybrid Flow**: Combines aspects of authorization code and implicit flows. The client receives both an authorization code and an ID Token in the initial response. Used when the client needs the user's identity immediately but wants the security of a code exchange for the access token.
- **Session Management**: OIDC defines mechanisms for monitoring and managing user sessions across applications, including iframe-based session status and logout endpoints that terminate sessions at the provider and all relying parties.

## Why It Matters

OIDC is critical for microservices because it provides a standardized, federated identity layer. Services can authenticate users by validating ID Tokens without maintaining their own user databases or password stores. Combined with an identity provider (Keycloak, Auth0, Dex, ORY Hydra), OIDC enables consistent authentication across dozens of services, supports SSO, and integrates with enterprise identity systems (LDAP, SAML, social login).

## Related Concepts

- [OAuth 2.0](01-OAuth2.md) — OIDC is built on OAuth 2.0; the access token from OAuth 2.0 protects the UserInfo endpoint
- [JWT](03-JWT.md) — ID Tokens are JWTs; understanding JWT structure and signature verification is essential
- [Service Identity](09-Service-Identity.md) — While OIDC handles user identity, SPIFFE handles service identity
- [Zero Trust](08-Zero-Trust.md) — OIDC enables continuous user identity verification inside a zero trust perimeter

---

## Mental Model

OIDC is like showing your passport at airport security. The passport (ID Token) is a verified document issued by a trusted authority (identity provider) that proves who you are. Your boarding pass (access token) is separate — it proves you're authorized to board a specific flight. Security checks your passport once at the entrance, but you show your boarding pass at each gate. The discovery endpoint is like the airport's published list of accepted travel documents.
