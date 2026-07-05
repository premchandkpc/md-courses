# Caching

Storing copies of frequently requested responses at the gateway or API layer so subsequent identical requests can be served without hitting the backend. This reduces latency, backend load, and network bandwidth.

## Overview

A caching layer sits between the client and microservices, typically at the API Gateway or a dedicated reverse proxy (Varnish, NGINX, CDN). When a request arrives, the cache checks for a fresh entry matching the request key (URL + headers). On a hit, it returns the cached response immediately. On a miss, it forwards the request to the backend, caches the response with a TTL, and returns it. Key concerns are cache invalidation, staleness tolerance, and cache key design.

## Key Characteristics

- **TTL-Based Expiration**: Responses are stored with a time-to-live; after expiry the next request re-fetches from the origin. Short TTLs for dynamic data, longer for static assets.
- **Cache-Control Headers**: Backend services declare cacheability via Cache-Control (public, private, max-age, s-maxage, stale-while-revalidate) — the gateway respects these directives.
- **Stale-While-Revalidate**: Serves a stale cached response immediately while asynchronously fetching a fresh copy in the background, hiding latency spikes from the client.

## Why It Matters

Many microservice responses change infrequently — product catalogs, configuration data, reference tables — yet serving each request from the database is expensive. Caching at the gateway can absorb 60-90% of read traffic, dramatically reducing load on backend services and database tiers. It also improves user-perceived latency, especially for geographically distributed clients using a CDN.

## Related Concepts

- [API Gateway](01-API-Gateway.md) — The gateway is the natural place to insert response caching.
- [Throttling](05-Throttling.md) — During throttling, cached responses can be served as a degraded fallback.
- [Rate Limiting](04-Rate-Limiting.md) — Works alongside caching to protect backend capacity.

## Mental Model

Caching is like a library's "popular books" shelf. Instead of going into the stacks and searching for a popular title every time someone asks (expensive), the librarian keeps copies of the most-requested books right at the front desk. They refresh the shelf every hour (TTL). If someone asks for a book that was on the shelf a few minutes ago but was just returned, the librarian hands them the slightly worn copy while another librarian gets a fresh one (stale-while-revalidate).
