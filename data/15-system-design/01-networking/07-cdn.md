# CDN (Content Delivery Networks) Deep Dive - L5 Networking

> **[🎨 View Interactive Diagram](cdn-architecture.html)** | [← Back to Index](../../systems-index.html)

*"How does Netflix stream to 100M users globally? How do we serve videos fast from anywhere?"*

---

## 1. Problem Statement

**Core Question:** How minimize latency for geographically distributed users? How replicate content globally?

Challenge: Internet has limited capacity
Distance = latency (speed of light: 200km ≈ 1ms)
Bandwidth = precious (expensive to replicate all data)

Need: edge servers near users, smart routing, cache invalidation

---

## 2. Real World Analogy

**Pizza Delivery:**

Centralized (origin server):
- One kitchen in San Francisco
- Orders from New York: 2500 miles away
- Delivery: cold pizza, slow

CDN (distributed kitchens):
- Kitchen in every city
- Order locally: hot pizza, fast
- Sync recipes (content updates)

Result: users happy (fast), kitchens coordinated

---

## 3. Why Problem Exists

### Distance & Latency

```
User in Tokyo, data in San Francisco:
  Distance: 8000 km
  Speed of light: 300,000 km/s
  Minimum latency: 26ms one-way (52ms round trip)
  
Congested routes: add 100-500ms
  Total: 200ms+ for single asset
  
User loads 50 assets: 50 × 200ms = 10 seconds (slow!)

CDN: server in Tokyo
  Distance: 10 km
  Latency: 1ms
  User: 50 assets × 1ms = 50ms (200x faster!)
```

### Bandwidth Cost

```
Stream 1 Mbps video to 1M users:
  Without CDN: 1M × 1Mbps = 1Pbps (impossible)
  Cost: $1000/Mbps = $1B/month
  
With CDN: replicate to edge servers
  Origin: serves edge servers only
  Edge: serves users locally
  Cost: $100M/month (10x cheaper)
```

---

## 4. Naive Approach

**"Just replicate everything everywhere"**

Problems:
- Storage cost (duplicate all data)
- Synchronization complexity (keep in sync)
- Invalidation headache (update all copies)
- Waste (some content unused)

---

## 5. Why Naive Fails

### Update Propagation

```
Static content: fast to propagate
Video: slow (100GB file)

Push update to 200 edge locations:
  Time: 200 × (upload time) = hours
  
Better: lazy pull (on-demand fetch)
  Edge: requests origin on cache miss
  Fill: cache, serve next request
  Delay: only first user sees latency
```

### Cache Invalidation

```
Video published: cache invalid
  Stale: user watches old content
  Invalidate all: expensive
  TTL approach: wait (stale period)
  
Smart: versioned URLs
  video.mp4 (generic)
  video-v123.mp4 (versioned)
  
New version: new URL → no invalidation
Old URL: expires on TTL
```

---

## 6. Evolution / Progression

### Stage 1: Origin Server Only
- High latency globally
- Bandwidth expensive

### Stage 2: Simple CDN
- Few edge locations (10-20)
- Manual content placement
- Basic TTL caching

### Stage 3: Smart CDN (Akamai, Cloudflare)
- 200+ edge locations globally
- Intelligent routing (anycast)
- Automatic cache invalidation
- Analytics & DDoS protection

### Stage 4: Multi-CDN
- Primary + backup CDN
- Failover if primary slow
- Cost optimization (pick cheapest)

---

## 7. Production Architecture

```
[User in Tokyo]
    ↓ (anycast DNS → nearest edge)
[Edge: Tokyo CDN Server]
    ├─ Cache hit: serve (1ms)
    ├─ Cache miss: fetch from origin
    └─ Origin: San Francisco
              ├─ Fetch from origin
              ├─ Return to edge
              ├─ Cache at edge
              └─ Serve user (50ms first, 1ms rest)

[Monitor]
    ├─ Cache hit ratio (target: >95%)
    ├─ Edge latency
    └─ Origin load
```

---

## 8. Components

### Anycast DNS

```
User queries: "cdn.example.com"
DNS returns: nearest edge IP (anycast)

Routing protocol (BGP):
  All edges advertise same IP
  Router: picks nearest (by hop count)
  User: queries nearest edge automatically
```

### Cache Headers

```
Origin sends:
  Cache-Control: max-age=86400 (1 day)
  Surrogate-Control: max-age=604800 (1 week)
  
Edge interprets:
  Surrogate-Control: respected by CDN (not browser)
  max-age: how long to cache
  
Smart: stale-while-revalidate
  Cache expired: serve stale
  Background: fetch fresh
  User: gets instant response
```

### Origin Shield

```
Many edge locations → origin overload

Solution: origin shield (extra cache layer)
  
  [Edge 1] \
  [Edge 2]  → [Origin Shield] → [Origin]
  [Edge 3] /
  
Consolidate: many edges → 1 shield → origin
Benefit: origin sees 1/100 traffic
```

---

## 9. Internal Working

### Cache Hierarchy

```
User request:

1. Browser cache (1ms if hit)
2. ISP cache (10ms if hit)
3. CDN edge (50ms if hit)
4. Origin (200ms+)

Result: typical cache hit ratio 95%
  Only 5% reach origin
```

### Purge Strategy

```
Video updated:

Option 1: TTL-based (lazy)
  TTL: 24 hours
  New version: wait 24h (stale period acceptable)

Option 2: Explicit purge
  API call: /api/purge
  CDN: remove from all edges
  Cost: expensive, propagation delay

Option 3: Versioned URLs
  old-video.mp4 (old cache)
  new-video-v2.mp4 (new URL, no collision)
  Clean: on TTL expiry
```

---

## 10. Request Lifecycle

```
t=0ms:      User clicks video link (Tokyo)
t=0-5ms:    Browser queries DNS
t=5-10ms:   Anycast: returns Tokyo edge IP
t=10-15ms:  TCP handshake to edge (1ms latency)
t=15-50ms:  HTTP GET for video

Edge checks cache:
  Cache hit (95% case):
    t=50-51ms: Serve from cache
    t=51ms:    User gets video (51ms total)

Cache miss (5% case):
    t=50-55ms: Query origin
    t=55-155ms: Origin transmits (100ms network)
    t=155-160ms: Edge receives, caches
    t=160-161ms: Edge serves user
    t=161ms:   User gets video (161ms total)

Result: P95 latency ~50ms (vs 200ms without CDN)
```

---

## 11. Data Flow

### Video Streaming Example

```
Step 1: Upload
  Creator: uploads video to origin
  Origin: stores, makes accessible

Step 2: User request
  User: clicks play (Tokyo)
  DNS: returns nearest edge (Tokyo)
  User: connects to Tokyo edge

Step 3: First view (cache miss)
  Tokyo edge: no cache
  Edge: queries origin (slow, 100ms network)
  Origin: sends video chunks
  Edge: buffers, caches
  User: plays (from edge buffer)

Step 4: Second view (cache hit)
  Different user: same video (Tokyo)
  Edge: cache hit (1-2ms)
  User: plays instantly

Step 5: Global scale
  Video: cached on 200 edges
  1M users: each gets nearby edge (<50ms)
  Origin: handles 1% requests (5% miss × 20% different)
```

---

## 12. Key Strategy

### 1. Cache Hit Optimization

```
Target: >95% hit ratio

Techniques:
  Versioned URLs (no invalidation collision)
  Smart TTLs (content-aware)
  Surrogate-Key headers (purge by tag)
  Stale-while-revalidate (serve expired)
```

### 2. Origin Protection

```
Prevent: origin overload

Techniques:
  Origin shield (consolidate requests)
  Rate limiting (max requests/sec)
  Circuit breaker (stop sending if slow)
  Failover (use backup if origin down)
```

### 3. Geographic Routing

```
User → nearest edge (lowest latency)

Anycast: automatic via routing
Geo-IP: lookup → serve nearest
Performance-based: measure, pick best
```

---

## 13. Failure Scenarios

### Scenario 1: CDN Edge Down

```
Tokyo edge server crashes
  Users in Tokyo: fallback to next nearest (Osaka)
  Latency: increases 20ms
  
Mitigation:
  Multiple edges per region
  Auto-failover (transparent)
  Health checks every 10s
```

### Scenario 2: Origin Unreachable

```
Origin network partition
  Edges: use stale-while-revalidate
  Serve: expired content (hours old)
  
After recovery:
  Refresh: fetch fresh
  Cache: update
```

### Scenario 3: Cache Stampede

```
Popular video cached, TTL expires:
  100K requests arrive simultaneously
  Cache miss: all hit origin
  Origin: overwhelmed (request spike)

Solution: stale-while-revalidate
  Serve: stale copy
  Background: 1 request refreshes
  Result: origin sees 1 request, not 100K
```

---

## 14. Bottlenecks Table

| Issue | Impact | Fix |
|---|---|---|
| Low cache hit ratio | Origin overload | Better TTL strategy |
| Single edge per region | Single point of failure | Multiple edges |
| Slow origin | P95 latency high | Origin shield |
| Stale content | User sees old data | Explicit purge API |
| Limited bandwidth | Video buffering | Origin scaling |

---

## 15. Monitoring

### Key Metrics

```
✓ Cache hit ratio (target: >95%)
✓ Edge latency (P95, P99)
✓ Origin latency (must be <500ms)
✓ Bandwidth usage (cost optimization)
✓ Origin request rate (overload detection)
✓ Error rate (4xx, 5xx)
```

---

## 16. Optimizations

### 1. Compression

```
Before: 1MB video chunk
Gzip: 200KB (80% reduction)
Brotli: 150KB (85% reduction)

Trade: CPU (edge) vs bandwidth (user)
Result: faster download
```

### 2. Image Optimization

```
User's device: mobile (small screen)
Full HD image: 2MB
Serve: 400x400 JPEG (50KB)

Technique: responsive images (srcset)
Edge: detect device type
Serve: right size (no browser waste)
```

### 3. Video Bitrate Adaptation

```
User: slow connection (2Mbps)
Stream: 5Mbps bitrate (buffering)

Solution: ABR (Adaptive Bitrate)
  Edge: detects client bandwidth
  Serve: 2Mbps stream (smooth)
  
Result: no buffering
```

---

## 17. Security

### 1. DDoS Protection

```
Attack: flood edge server
CDN: absorbs (massive capacity)
  Origin: protected (behind CDN)
  
Techniques:
  Rate limiting (edge)
  Geo-blocking (suspicious regions)
  Pattern detection (bots)
```

### 2. Access Control

```
Private content: require authentication
  Token: signed, time-limited
  Edge: validates before serving
  
Prevent: direct URL sharing (token expires)
```

---

## 18. Tradeoffs Table

| Feature | Cache Hit | Freshness | Cost |
|---|---|---|---|
| Long TTL (1 week) | High | Stale | Low |
| Short TTL (1 hour) | Medium | Fresh | Medium |
| Explicit purge | Variable | Fresh | High |
| Versioned URLs | High | Fresh | Medium |

---

## 19. Alternatives

### Self-Hosted CDN

```
Own edge servers globally
Cost: expensive (capital + operations)
Control: full
Benefit: no vendor lock-in
```

---

## 20. When NOT to Use

### Don't Use CDN When:

1. **Private, dynamic content**
   - Database queries
   - Personalized (hard to cache)

2. **Small geographic audience**
   - Single region sufficient
   - CDN cost not justified

---

## 21. Interview Questions

1. **Design video streaming (1M users globally)**
   - CDN strategy?
   - Cache invalidation?
   - Cost optimization?

2. **Cache hit ratio 50%**
   - Root cause?
   - How improve?

3. **What happens on edge failure?**
   - Fallback?
   - User impact?

---

## 22. Common Mistakes

1. **Long TTL, no purge API**
   - Stale content served for hours
   - Add: explicit purge endpoint

2. **Single edge per region**
   - One failure = region down
   - Add: multiple edges

3. **No origin protection**
   - Cache stampede kills origin
   - Add: stale-while-revalidate

4. **No monitoring**
   - Hit ratio drops, unnoticed
   - Add: dashboards

---

## 23. Debugging Guide

### Step 1: Check Cache Hit

```
curl -I https://example.com/video.mp4 | grep X-Cache
X-Cache: HIT (good)
X-Cache: MISS (investigate)
```

### Step 2: Check Edge

```
traceroute example.com
Shows: which edge server
Latency: time per hop
```

---

## 24. Code Examples

### Go: Cache Control Headers

```go
func serveVideo(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Cache-Control", "public, max-age=86400")
    w.Header().Set("Surrogate-Control", "max-age=604800")
    w.Header().Set("X-Content-Type-Options", "nosniff")
    
    // Serve video bytes
    data, _ := ioutil.ReadFile("video.mp4")
    w.Write(data)
}

func purgeCache(w http.ResponseWriter, r *http.Request) {
    // API: purge cache by surrogate-key
    key := r.URL.Query().Get("key")
    
    // Send purge request to CDN
    http.Post("https://cdn-api/purge", "application/json", 
        bytes.NewReader([]byte(fmt.Sprintf(`{"key":"%s"}`, key))))
    
    w.WriteHeader(200)
}
```

---

## 25. Visual Diagrams

### CDN vs No-CDN Latency

```
No CDN:          User (Tokyo) → Origin (SF) → 200ms round trip
CDN:             User (Tokyo) → Edge (Tokyo) → 50ms round trip

Speedup: 4x faster
```

---

## 26. Simulation Ideas

1. **Cache Invalidation Impact**
   - Vary: TTL, purge frequency
   - Show: hit ratio, origin load

---

## 27. Case Studies

### Netflix: 200+ edges globally
Result: <100ms latency, 95%+ hit ratio, 50% bandwidth savings

---

## 28. Related Topics

- **Caching Strategies**
- **DDoS Mitigation**

---

## 29. Advanced Topics

### Intelligent Routing

```
Route based on:
  Network latency (measure continuously)
  Available capacity (load-aware)
  Cost (pick cheaper)
```

---

## 30. Production Checklist

- [ ] Multiple edges per region (failover)
- [ ] Cache-Control headers set correctly
- [ ] TTL strategy (content-aware)
- [ ] Purge API for emergency invalidation
- [ ] Origin shield (if high traffic)
- [ ] Monitoring: cache hit ratio
- [ ] Monitoring: edge latency (P95, P99)
- [ ] Origin rate limiting (surge protection)
- [ ] DDoS mitigation enabled
- [ ] Graceful fallback (origin if CDN down)

---

*Last Updated: 2026-05-28*
