# API Security

The collection of policies, controls, and best practices applied at the API Gateway to protect backend services from attacks, data leaks, and abuse. It encompasses everything from CORS to injection prevention.

## Overview

API security is a multi-layered defense built into the gateway layer. It includes transport security (TLS termination), request validation (schema checking, size limits, content-type enforcement), cross-origin protection (CORS configuration, CSRF tokens), injection prevention (SQL, NoSQL, command injection), and abuse prevention (rate limiting, IP allow/block lists). The gateway is the ideal enforcement point because it intercepts every external request before any backend service touches it.

## Key Characteristics

- **Request Validation**: Malformed payloads, oversized bodies, and unexpected content types are rejected before reaching services. JSON schema validation catches structural attacks early.
- **CORS and CSRF Protection**: CORS headers control which origins can access the API; CSRF tokens prevent cross-site request forgery for cookie-authenticated clients.
- **Injection Prevention**: The gateway can sanitize inputs and block requests containing SQL fragments, XSS payloads, or command injection patterns using regex or dedicated WAF rules.

## Why It Matters

Microservices expand the attack surface — each service is an entry point. A gateway centralizes security controls so that every service behind it benefits from the same protections without reimplementing them. A single misconfigured service with an SQL injection vulnerability is catastrophic; the gateway can block the attack before it reaches that service. Defense-in-depth at the gateway also simplifies PCI-DSS, HIPAA, and SOC2 compliance audits by providing a clear security boundary.

## Related Concepts

- [Authentication](07-Authentication.md) — Verifies identity, a first step in API security.
- [Authorization](08-Authorization.md) — Controls access, the second step.
- [Rate Limiting](04-Rate-Limiting.md) — Prevents abuse and brute-force attacks.
- [API Gateway](01-API-Gateway.md) — The enforcement point for all security policies.

## Mental Model

API security is like airport security. Before you reach the gate (microservice), you pass through multiple checkpoints: bag size check (request validation), metal detector (injection prevention), ID verification (authentication), boarding pass check (authorization), and limits on how many bags you carry (rate limiting). Each layer catches what the previous one missed, and nobody gets to the gate without passing through all of them.
