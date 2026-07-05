# 08-CDN

A Content Delivery Network is a geographically distributed network of proxy servers that delivers content from locations closest to the user. CDNs reduce latency by serving cached static assets — and sometimes dynamic content — from edge locations rather than the origin server.

## Overview
A CDN consists of hundreds or thousands of edge nodes (PoPs) worldwide. When a user requests content, the CDN routes the request to the nearest edge. If the edge has the content cached, it serves it immediately (cache hit). If not, it fetches from the origin server (cache fill) and stores a copy for subsequent requests. Origin pull is the standard pattern — the CDN pulls content from the origin on demand. Origin push proactively uploads content to edge nodes, useful for pre-warming caches for expected traffic spikes.

## Key Characteristics
- **Latency reduction**: Content travels shorter physical distances. A user in Tokyo gets served from a Tokyo edge, not a Virginia origin. This cuts latency from ~150ms to ~10ms.
- **Origin offload**: Edge nodes handle the vast majority of requests. The origin server sees only cache misses, drastically reducing load.
- **Cache invalidation**: Content changes require purging stale versions from all edges. Most CDNs support wildcard purging and API-triggered invalidation, but propagation can take seconds to minutes.
- **Static and dynamic delivery**: CDNs excel at images, CSS, JS, and video. Modern CDNs (CloudFront, Fastly, Cloudflare) also support dynamic content, API acceleration, and serverless edge compute.
- **DDoS absorption**: CDNs absorb large-scale attacks by distributing traffic across their global network. The origin sees only scrubbed, legitimate traffic.

## Why It Matters
CDNs are essential for global microservices serving web traffic. Static assets (HTML, JS, CSS, images) should always be CDN-served. Many architectures also use CDNs for API responses, streaming, and even as a caching layer in front of microservices (lambdas@edge, Cloudflare Workers). Without a CDN, every user request hits the origin, increasing latency and infrastructure cost.

## Related Concepts
- [Caching](06-Caching.md) — CDNs are a specialized form of distributed caching
- [Horizontal Scaling](01-Horizontal-Scaling.md) — CDNs effectively give you unlimited "edge replicas" for serving cached content
- [Caching Strategies](06-Caching.md) — Cache-aside and write-through patterns apply at the CDN level too

---

## Mental Model
A global news publisher prints newspapers at regional plants instead of flying them from a single central location. A reader in London gets papers printed in London, not shipped from New York. When a story changes (cache invalidation), the publisher sends an update to all regional plants — it takes time for every plant to receive and reprint.
