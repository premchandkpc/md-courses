# HTTP/HTTPS Deep Dive - L5 Networking

> **[🎨 View Interactive Diagram](http-architecture.html)** | [🎨 Caching Headers Simulator](../../../html/02-http-caching-headers-viz.html) | [← Back to Index](../../systems-index.html)

*"GET request takes 500ms. Why? What can you optimize?"*

---

## 1. Problem Statement

**Core Question:** How does a browser fetch web content efficiently and securely?

Performance targets:
- First byte: <100ms
- Full page: <1s
- Secure by default (HTTPS)

Challenges:
- Multiple round-trips (handshake, request, response)
- Latency-sensitive user experience
- Security overhead (encryption)

---

## 2. Real World Analogy

**Restaurant Ordering:**

HTTP/1.1 (serial):
- Customer: orders 1 item
- Waiter: walks to kitchen
- Kitchen: prepares 1 item
- Waiter: walks back
- Customer: eats
- Repeat for each item (multiple round-trips)

HTTP/2 (multiplexed):
- Customer: orders multiple items
- Waiter: walks to kitchen once (batched)
- Kitchen: prepares all items in parallel
- Waiter: walks back with all items
- Customer: eats all (one round-trip)

---

## 3. Why Problem Exists

### Multiple Roundtrips

```
HTTP/1.1: 1 request per connection (serial)
  Request 1: 50ms network + 50ms processing
  Request 2: 50ms network + 50ms processing
  Total: 200ms for 2 requests

Parallelism: 2 connections
  Connection 1 & 2: 50ms network + 50ms processing
  Total: 100ms for 2 requests (2x faster!)
```

### TLS Handshake Overhead

```
HTTP: plaintext, no handshake
HTTPS: 
  TLS handshake: 1-3 round-trips (~100-300ms)
  Encryption/decryption: CPU cost
  Certificate validation: CPU cost

Trade: security (HTTPS) vs latency (overhead)
```

### Head-of-Line Blocking

```
HTTP/1.1 over single connection:
  Request 1 sent
  Response 1 arrives (large, 100MB download)
  Request 2 blocked (waiting for response 1)
  
Result: slow (head-of-line blocking)

HTTP/2 multiplexing:
  Request 1 sent
  Request 2 sent (without waiting)
  Response 1 receives (streamed in frames)
  Response 2 receives (interleaved)
  
Result: fast (parallel streams)
```

---

## 4. Naive Approach

**"HTTP/1.1 for all"**

Problems:
- Multiple connections (resource overhead)
- No multiplexing (slow large files)
- No server push (client has to request each asset)
- No compression support (bloated responses)

---

## 5. Why Naive Fails

### Connection Overhead

```
6 resources per page (JS, CSS, images)
HTTP/1.1: 1 request per connection
  Need: 6 connections
  Each: TCP handshake (1 RTT) + TLS (1-2 RTT)
  
Total overhead: 6 connections × 3 RTT = 18 RTT per page load
Cost: ~1.8 seconds (100ms per RTT)
```

### Large File Latency

```
Downloading 10MB file
HTTP/1.1 over single connection:
  - Request: 50ms
  - Response: 2000ms (10MB at 5Mbps)
  - Other requests: BLOCKED for 2 seconds!
```

---

## 6. Evolution / Progression

### Stage 1: HTTP/0.9
- Single request per connection
- No headers (implicit content-type)
- No caching

### Stage 2: HTTP/1.0
- Multiple requests per connection
- Headers (request & response)
- Basic caching (Expires header)

### Stage 3: HTTP/1.1
- Persistent connections (keep-alive)
- Pipelining (queue requests, wait for responses in order)
- Chunked transfer encoding
- Gzip compression (Content-Encoding)

### Stage 4: HTTP/2
- Multiplexing (streams over single connection)
- Server push (proactive delivery)
- Header compression (HPACK)
- Binary framing (more efficient)

### Stage 5: HTTP/3
- QUIC transport (UDP-based, 0-RTT)
- Connection migration (survives network change)
- Improved congestion control

---

## 7. Production Architecture

```
[Browser] → 
  
[CDN / Cache Layer]
  ├─ If cache hit: respond (instant)
  └─ If cache miss: query origin
  
[Origin Server]
  ├─ Generate response
  ├─ Compress (gzip)
  ├─ Add headers (cache headers, security headers)
  └─ Send response

[Return path]
  ├─ CDN caches response
  ├─ Browser caches response
  └─ User sees content
```

---

## 8. Components

### HTTP Methods

```
GET: retrieve resource (safe, idempotent)
POST: create resource (not idempotent, use idempotency key)
PUT: replace resource (idempotent)
DELETE: delete resource (idempotent)
PATCH: partial update (may not be idempotent)
HEAD: like GET but no response body
OPTIONS: query allowed methods
```

### Status Codes

```
1xx: Informational (100 Continue)
2xx: Success (200 OK, 201 Created, 204 No Content)
3xx: Redirect (301 Moved, 302 Found, 304 Not Modified)
4xx: Client error (400 Bad Request, 404 Not Found, 429 Too Many Requests)
5xx: Server error (500 Internal, 503 Service Unavailable)
```

### HTTP/2 Multiplexing

```
Single connection: 1 TCP + 1 TLS handshake
Multiple streams: 100+ streams over same connection

Stream = virtual request/response pair
No head-of-line blocking (streams independent)

Example:
  Stream 1: GET /large-file (100MB, slow)
  Stream 2: GET /css (1KB, fast)
  
  Stream 2: completes immediately
  Stream 1: continues (not blocked)
```

### TLS (Transport Layer Security)

```
TLS 1.2: requires 1-3 RTT for handshake
TLS 1.3: requires 1 RTT (optimization)

Versions:
  SSL 3.0: deprecated (insecure)
  TLS 1.0, 1.1: deprecated (insecure)
  TLS 1.2: widely supported
  TLS 1.3: modern (faster, more secure)
```

---

## 9. Internal Working

### HTTP Request Lifecycle

```
t=0ms:     Browser: initiated request
t=50ms:    DNS: resolved IP
t=100ms:   TCP: handshake complete
t=200ms:   TLS: handshake complete
t=201ms:   HTTP: send GET request
t=251ms:   Server: receives request
t=300ms:   Server: process (50ms)
t=350ms:   Server: send response
t=400ms:   Browser: receives response
t=400ms:   Browser: parse HTML (1ms)
t=401ms:   Browser: identify resources (JS, CSS, images)
t=401ms:   Browser: request resources (parallel via HTTP/2)
           ...
t=2000ms:  All resources loaded
t=2050ms:  JavaScript: parsed & executed
t=2100ms:   Page: rendered to user

Key insight: latency is cumulative
- DNS: 50ms
- TCP: 100ms (TCP slow start)
- TLS: 100ms
- Request: 50ms
- Response: 50ms
- Total: 350ms before page starts rendering
```

### HTTP/2 Stream Multiplexing

```
Connection established (1 TLS + 1 TCP handshake)
  ↓
Open stream 1: GET /index.html
Open stream 2: GET /style.css (without waiting for stream 1)
Open stream 3: GET /script.js (without waiting)
Open stream 4: GET /image.png (without waiting)
  ↓
Server: responds to all 4 in parallel
  Stream 1: [frame 1], [frame 2], [frame 3]...
  Stream 2: [frame 1], [frame 2]...
  Stream 3: [frame 1]...
  Stream 4: [frame 1]...
  ↓
Browser: reassembles streams
  Stream 1: complete (200KB HTML)
  Stream 2: complete (10KB CSS)
  Stream 3: complete (50KB JS)
  Stream 4: complete (200KB image)

Total time: ~100ms (not 4 × 100ms like HTTP/1.1 with single connection)
```

---

## 10. Request Lifecycle

```
Navigation timing (Performance API):

navigationStart: 0ms (user clicks link)
fetchStart: 5ms (browser starts request)
  DNS lookup: 5-50ms
dnsLookupStart: 5ms
dnsLookupEnd: 20ms
  TCP connect: 20-100ms
connectStart: 20ms
connectEnd: 100ms
  TLS: 100-200ms
secureConnectionStart: 100ms
tlsHandshakeEnd: 200ms
  Request: 200-250ms
requestStart: 200ms
responseStart: 250ms (first byte)
  Response: 250-350ms
responseEnd: 350ms
  DOM parse: 350-500ms
domLoading: 350ms
domInteractive: 500ms
domContentLoaded: 700ms
  Resource load: 700-2000ms
loadEventStart: 2000ms
loadEventEnd: 2100ms

Byte: 250ms (Time to First Byte)
Interactive: 500ms (page responds to input)
Complete: 2100ms (fully loaded)
```

---

## 11. Data Flow

### Request Headers to Response

```
Request:
  GET /api/users HTTP/1.1
  Host: api.example.com
  Connection: keep-alive
  Accept: application/json
  Accept-Encoding: gzip, deflate
  User-Agent: Mozilla/5.0...
  
Response:
  HTTP/1.1 200 OK
  Content-Type: application/json; charset=utf-8
  Content-Encoding: gzip (compressed)
  Content-Length: 5234
  Cache-Control: max-age=3600 (cache 1 hour)
  ETag: "abc123" (for 304 Not Modified)
  Set-Cookie: session=xyz (set session)
  
  [compressed body: 5234 bytes]
```

---

## 12. Key Strategy

### 1. Use HTTP/2 or HTTP/3

```
Multiplexing over single connection
  No head-of-line blocking
  Fewer handshakes
  Better compression (HPACK)
```

### 2. Optimize HTTPS

```
TLS 1.3: faster handshake (1 RTT vs 3)
Certificate: valid for domain (no warnings)
OCSP stapling: don't block on cert validation
Session resumption: reuse TLS session (saves 1 RTT)
```

### 3. Compression

```
Enable gzip: default on most servers
Reduce: JSON by 70%, HTML by 80%

Example:
  Uncompressed: 100KB
  Gzipped: 30KB
  Savings: 70KB (less bandwidth, faster download)
```

### 4. Caching

```
Static assets: Cache-Control: max-age=31536000 (1 year)
Dynamic: Cache-Control: max-age=0, must-revalidate

Browser cache: don't re-download (instant)
CDN cache: serve from edge (50-100ms)
Origin: only serve cache misses
```

---

## 13. Failure Scenarios

### Scenario 1: Slow First Byte

```
Time to First Byte: 5 seconds (target: <100ms)

Root cause investigation:
  DNS: 50ms (OK)
  TCP: 100ms (OK)
  TLS: 100ms (OK)
  Request: 50ms (OK)
  Server response: 4700ms (SLOW!)
  
Issue: server processing slow
  Database query slow?
  Cache miss + expensive computation?
  
Fix: optimize server, add caching
```

### Scenario 2: Connection Reset During Large Download

```
Downloading 100MB file over HTTP/1.1
Connection resets after 10MB
  
Retry:
  Without range: restart from 0 (waste 10MB + time)
  With range: resume from byte 10000001 (efficient)

HTTP header: Range: bytes=10000001-
Response: HTTP 206 Partial Content
```

### Scenario 3: HTTP/2 Frame Loss

```
Loss during multiplexed request
  
TCP: retransmits lost frame (automatic)
HTTP/2: streams resume transparently
User: doesn't notice (robust)

vs HTTP/1.1:
  Connection might be lost
  User: has to reload
```

---

## 14. Bottlenecks Table

| Issue | Impact | Symptoms | Fix |
|---|---|---|---|
| HTTP/1.1 serial | High latency | Slow page load | Use HTTP/2 |
| No caching | High origin load | Repeated requests | Add cache headers |
| Large responses | Slow download | Bandwidth-limited | Compress (gzip) |
| No multiplexing | Head-of-line block | Slow with large files | HTTP/2 |
| Slow TTFB | Slow start | User perception | Optimize server |

---

## 15. Monitoring

### Key Metrics (Web Vitals)

```
LCP (Largest Contentful Paint): <2.5s
FID (First Input Delay): <100ms
CLS (Cumulative Layout Shift): <0.1
TTFB (Time to First Byte): <100ms

Monitor via:
  Real User Monitoring (RUM): actual user data
  Synthetic: controlled testing
  CDN metrics: edge performance
```

### HTTP Status Codes

```
Track:
  ✓ 2xx success rate (target: >99%)
  ✓ 3xx redirect rate (should be minimal)
  ✓ 4xx client error rate (indicate bugs)
  ✓ 5xx server error rate (indicate outages)
```

---

## 16. Optimizations

### 1. Server Push (HTTP/2)

```
Browser requests: index.html
Server knows: CSS & JS needed
Server pushes: CSS & JS without waiting for browser request
  
Result: browser gets resources earlier (faster)
Cost: may push unused resources
```

### 2. Resource Hints

```
<link rel="preconnect" href="https://cdn.example.com">
  Establishes connection early (saves ~100ms)
  
<link rel="dns-prefetch" href="https://api.example.com">
  Resolves DNS early (saves ~50ms)
  
<link rel="prefetch" href="/next-page">
  Loads for next page (background)
```

### 3. Early Hints (103 Status)

```
Server sends: 103 Early Hints (with Link headers)
Before: full response

Benefit: browser starts preconnect/prefetch before response
Latency: saved 100-200ms
```

---

## 17. Security

### 1. HTTPS Enforcement

```
Default to HTTPS: all traffic encrypted
HSTS: tell browser to always use HTTPS
Prevent: downgrade attacks
```

### 2. Security Headers

```
Content-Security-Policy: restrict XSS
X-Frame-Options: prevent clickjacking
Strict-Transport-Security: enforce HTTPS
X-Content-Type-Options: prevent sniffing
```

---

## 18. Tradeoffs Table

| Version | Latency | Complexity | Browser Support |
|---|---|---|---|
| HTTP/1.1 | High | Low | All |
| HTTP/2 | Medium | Medium | Most |
| HTTP/3 | Low | High | Modern |

---

## 19. Alternatives

### WebSocket

```
HTTP: request-response (client initiates)
WebSocket: bidirectional (server can push)

Use: real-time updates (chat, notifications)
Not: static content (HTTP better)
```

---

## 20. When NOT to Use

### Don't Use HTTP/2 When:

1. **Old browser support required**
   - HTTP/1.1 + gzip: better compatibility

---

## 21. Interview Questions

1. **Optimize page load (<1s target)**
   - What's bottleneck?
   - HTTP version?
   - Caching strategy?

2. **First Byte Timing (TTFB) is 2 seconds**
   - Root cause?
   - Solutions?

3. **HTTP/1.1 vs HTTP/2 comparison**
   - When use each?
   - Performance implications?

---

## 22. Common Mistakes

1. **Not using HTTPS**
   - Performance: ~100ms overhead (worth it)
   - Security: essential
   - SEO: HTTPS ranked higher

2. **Disabling caching headers**
   - Force: reload on every visit
   - Users: slow, high origin load

3. **Large responses without compression**
   - 100KB uncompressed
   - 30KB gzipped
   - 70% smaller (3x faster)

4. **HTTP/1.1 with many resources**
   - 6 resources: need 6 connections
   - Head-of-line blocking
   - Use HTTP/2 (1 connection, multiplexed)

5. **Not implementing ETag / 304 Not Modified**
   - Full response sent even if unchanged
   - With ETag: 304 (no body, instant)
   - Bandwidth & latency improvement

---

## 23. Debugging Guide

### Step 1: Check Network Waterfall

```
Browser DevTools → Network tab
Shows: timing for each request

Waterfall analysis:
  DNS (green): 50ms (OK)
  Connect (orange): 100ms (OK)
  Request (purple): 50ms (OK)
  Response (blue): 500ms (SLOW!)
  
Issue: server response slow
```

### Step 2: Check Compression

```
DevTools → Network → Response Headers
Content-Encoding: gzip (good)
Content-Encoding: not present (bad, add gzip)
```

### Step 3: Check Cache

```
Response Headers:
Cache-Control: max-age=3600 (cache 1 hour)
ETag: "abc123" (for validation)

No cache headers: add them
```

---

## 24. Code Examples

### Go: HTTP Server with Caching

```go
func handleAPI(w http.ResponseWriter, r *http.Request) {
    // Set cache headers
    w.Header().Set("Cache-Control", "max-age=3600")
    w.Header().Set("ETag", "\"abc123\"")
    
    // Check If-None-Match (client has cached)
    if r.Header.Get("If-None-Match") == "\"abc123\"" {
        w.WriteHeader(http.StatusNotModified)
        return
    }
    
    // Compression (automatic if Content-Encoding set)
    w.Header().Set("Content-Encoding", "gzip")
    
    // Security headers
    w.Header().Set("Strict-Transport-Security", "max-age=31536000")
    w.Header().Set("Content-Security-Policy", "default-src 'self'")
    
    // Response
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

// Enable HTTP/2
// go run server.go (uses HTTP/2 if available)
// Or: http.ListenAndServeTLS(":443", "cert.pem", "key.pem", mux)
```

---

## 25. Visual Diagrams

### HTTP/1.1 vs HTTP/2

```
HTTP/1.1:
  Request 1 ──→ Response 1
    Request 2 ──→ Response 2
      Request 3 ──→ Response 3
      Time: ~300ms (serial)

HTTP/2:
  Request 1, 2, 3 ──→ (multiplexed)
  ←─ Response 1, 2, 3 (interleaved)
  Time: ~100ms (parallel)
```

---

## 26. Simulation Ideas

1. **Page Load Optimizer**
   - Vary: compression, caching, HTTP version
   - Show: impact on load time

2. **Multiplexing Impact**
   - Compare HTTP/1.1 vs HTTP/2
   - Show: speed improvement

---

## 27. Case Studies

### Case 1: Google's PageSpeed Insights
Focus: optimize TTFB, remove render-blocking, lazy-load
Result: better rankings, user experience

### Case 2: YouTube HTTP/2 Migration
Result: 25% faster page load, reduced bandwidth 15%

---

## 28. Related Topics

- **Web Caching**
- **TLS Security**
- **Performance Optimization**

---

## 29. Advanced Topics

### HTTP Trailers

```
Send data after response body
Useful for: checksums, trailers

Request:
  Transfer-Encoding: chunked, trailers
  [body chunks]
  
Trailers:
  X-Checksum: abc123
```

---

## 30. Production Checklist

- [ ] Use HTTPS (TLS 1.3 preferred)
- [ ] Use HTTP/2 or HTTP/3
- [ ] Enable gzip compression
- [ ] Set Cache-Control headers
- [ ] Implement ETag for 304 Not Modified
- [ ] Reduce Time to First Byte (<100ms)
- [ ] Optimize largest image/resource
- [ ] Lazy-load below-the-fold content
- [ ] Monitor Web Vitals (LCP, FID, CLS, TTFB)
- [ ] Monitor 5xx error rate
- [ ] Security headers (CSP, HSTS, X-Frame-Options)
- [ ] Test with slow network (DevTools throttling)
- [ ] Test with packet loss (5%, 10%)
- [ ] Load test under peak traffic
- [ ] CDN caching strategy defined

---

*Last Updated: 2026-05-28*
