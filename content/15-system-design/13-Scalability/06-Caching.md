# 06-Caching

Storing frequently accessed data in a fast-access layer so that subsequent requests can be served without hitting the primary data store. Caching reduces latency, decreases load on backend systems, and improves throughput.

## Overview
A cache sits between the client and the authoritative data source. When a request arrives, the cache is checked first. If the data is present (cache hit), it's returned immediately. If not (cache miss), the request goes to the source, and the response is stored in the cache for future use. Caches operate at multiple levels: in-memory (Redis, Memcached), at the application layer (in-process LRU cache), at the CDN edge (CloudFront, Cloudflare), and in the browser (HTTP cache headers). Each level trades off speed against capacity and staleness risk.

## Key Characteristics
- **Cache hit ratio determines effectiveness**: A 90% hit ratio means 10% of requests hit the backend. Optimizing the ratio depends on cache size, eviction policy (LRU, LFU, TTL), and access patterns.
- **Staleness is inevitable**: Cached data is always potentially outdated. Applications must decide acceptable staleness (TTL) and whether to allow stale reads during backend failures.
- **Cache-aside (lazy loading)**: Application checks cache, falls back to DB, writes to cache. Simple and common but has a cold-start penalty.
- **Write-through**: Data is written to cache and DB simultaneously. Ensures cache is always fresh but adds write latency.
- **Write-behind (write-back)**: Data is written to cache first and asynchronously flushed to DB. Fast writes but risk of loss if cache fails.
- **Cache invalidation is hard**: Removing stale data at the right moment is notoriously difficult. Time-based expiration is the simplest; event-driven invalidation (publish cache-busting events) is more precise.

## Why It Matters
Caching is the highest-leverage performance optimization in microservices. A well-placed cache can reduce database load by 90%+ and cut p99 latency from 100ms to 1ms. Every service should consider caching for read-heavy endpoints, reference data, and expensive computations. However, caching also introduces complexity: cache consistency, invalidation, and cold-start scenarios must be handled carefully.

## Related Concepts
- [Redis](07-Redis.md) — The most popular distributed cache for microservices
- [CDN](08-CDN.md) — Edge caching for static and dynamic web content
- [Horizontal Scaling](01-Horizontal-Scaling.md) — Caching reduces per-instance load, letting fewer instances handle more traffic

---

## Mental Model
A chef keeps the most commonly used spices in a small rack next to the stove (cache) instead of walking to the pantry (database) for every dish. The spice rack can only hold 20 jars — when a new spice is added, the least-used one goes back to the pantry (eviction policy).
