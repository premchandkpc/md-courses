# Rate Limiting

A mechanism that controls how many requests a client can make to an API within a given time window. It protects backend services from abuse, ensures fair resource distribution, and maintains system stability under load.

## Overview

Rate limiting enforces quotas on API consumers — per user, per IP, per API key, or globally. When a client exceeds its quota, the gateway returns HTTP 429 (Too Many Requests) with a Retry-After header. Common algorithms include token bucket (burst-tolerant, refills at a fixed rate), sliding window (smooth boundaries, tracks timestamps within a rolling interval), and fixed window (simple counter reset at interval boundaries, prone to thundering herd at reset).

## Key Characteristics

- **Configurable Windows**: Limits can be applied per second, minute, hour, or day depending on the use case and sensitivity of the endpoint.
- **Distributed Enforcement**: In multi-instance deployments, Redis-backed counters ensure a consistent rate limit across all gateway replicas.
- **Graceful Feedback**: Well-implemented rate limiting returns informative error payloads and headers (X-RateLimit-Limit, X-RateLimit-Remaining, Retry-After) so clients can self-throttle.

## Why It Matters

Unbounded API traffic can overwhelm downstream services, cause cascading failures, and inflate cloud costs. Rate limiting provides a first line of defense against runaway clients, buggy retry loops, and malicious actors (DDoS, credential stuffing). It also enables tiered API plans — free tier gets 100 req/hr, pro tier gets 10,000 req/hr — directly monetizing access.

## Related Concepts

- [Throttling](05-Throttling.md) — Server-side rejection when system capacity is exceeded, complementary to client-side rate limiting.
- [API Security](09-API-Security.md) — Rate limiting is a core security control in the gateway.
- [API Gateway](01-API-Gateway.md) — The natural enforcement point for rate limit policies.

## Mental Model

Rate limiting is like a subway turnstile. The turnstile lets one person through per card swipe (one request per token). If you try to push through without swiping (no token), the turnstile locks and you must wait. The token bucket algorithm is like a bucket of coins — you can use a burst of coins at once, but the bucket refills at a steady rate.
