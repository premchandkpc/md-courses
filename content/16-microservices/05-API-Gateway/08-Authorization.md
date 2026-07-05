# Authorization

Determining what an authenticated client is allowed to do — which resources they can access and which operations they can perform. Authorization is enforced at the gateway alongside or after authentication.

## Overview

Once a client's identity is established via authentication, authorization checks whether that identity has permission to perform the requested action. Common models include Role-Based Access Control (RBAC), where roles map to permissions; Attribute-Based Access Control (ABAC), where policies evaluate attributes of the user, resource, and environment; and Scope-Based Access Control (OAuth2 scopes), where tokens carry scoped permissions like "read:orders" or "write:users". The gateway inspects the request, extracts the user's claims (roles, scopes, permissions), and either allows or rejects it.

## Key Characteristics

- **Policy Enforcement Point (PEP)**: The gateway makes allow/deny decisions based on policies, often by consulting a central policy engine (OPA, Casbin, custom service).
- **Claim-Based Decisions**: JWT claims (roles, permissions, tenant ID) are extracted and evaluated against route-specific rules — e.g., only users with role "admin" can call DELETE /users/:id.
- **Fine-Grained or Coarse**: Authorization can be as simple as route-level guards or as detailed as resource-level checks that require downstream service involvement.

## Why It Matters

Authorization is the second half of access control — authentication proves identity, but without authorization any authenticated user can access any resource. Centralizing authorization at the gateway provides a consistent enforcement layer and simplifies auditing. However, fine-grained authorization (row-level, field-level) often needs to be delegated to individual services because the gateway lacks domain-specific context.

## Related Concepts

- [Authentication](07-Authentication.md) — Prerequisite: the user must be authenticated before authorization can be evaluated.
- [API Security](09-API-Security.md) — Authorization is a core security function.
- [API Gateway](01-API-Gateway.md) — The gateway hosts the policy enforcement point.

## Mental Model

If authentication is the building security desk checking your ID, authorization is the keycard that only opens certain doors. A contractor might be authenticated (they passed the security check) but their keycard only opens the lobby and the third-floor conference room, not the server room. The door lock (authorization) checks their permissions before every access attempt.
