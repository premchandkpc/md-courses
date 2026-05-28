# DNS Resolution Deep Dive - L5 Networking

> **[🎨 View Interactive Diagram](dns-architecture.html)** | [← Back to Index](../../systems-index.html)

*"You type example.com. How does your computer find 93.184.216.34?"*

---

## 1. Problem Statement

**Core Question:** How does the internet map domain names to IP addresses at global scale?

Challenge:
- Billions of domains
- Millions of queries per second
- Need fast response (should be <100ms)
- Needs to survive failures

---

## 2. Real World Analogy

**Phone Directory Scenario:**

No DNS (call operator every time):
- You: "What's John's number?"
- Operator: searches phonebook
- Operator: "555-1234"
- Cost: slow, centralized

DNS (distributed directory):
- You: "What's John's number?" (ask local cache)
- Cache hit: instant
- Cache miss: ask next authority
- Keep records locally for next time
- Cost: fast, distributed

---

## 3. Why Problem Exists

### IP Addresses Hard to Remember

```
example.com: easy to remember
93.184.216.34: hard to remember

Need: mapping service (DNS)
```

### Global Scale Requires Distribution

```
Single DNS server:
  1M queries/sec
  Server capacity: 100K queries/sec
  Overloaded, slow

Solution:
  Distributed hierarchy (root → TLD → authoritative)
  Caching (reduce queries)
  Replication (fast response)
```

### Changes Must Propagate Fast

```
Server IP changes
DNS records updated
Users still see old IP (cache)

Solution:
  TTL (Time-To-Live): how long to cache
  Small TTL: fast updates, more queries
  Large TTL: fewer queries, stale records
```

---

## 4. Naive Approach

**"Single DNS server"**

Problems:
- Bottleneck (can't handle global load)
- No redundancy (single point of failure)
- Latency (queries travel globally)
- Cache misses expensive

---

## 5. Why Naive Fails

### Capacity Wall

```
Single server: 100K queries/sec
Global traffic: 1M+ queries/sec
Overloaded, users get timeouts
```

### Fault Intolerance

```
Single server fails: entire DNS down
All lookups fail
Internet breaks (can't reach any domain)
```

---

## 6. Evolution / Progression

### Stage 1: Single DNS Server
- All lookups centralized
- Doesn't scale

### Stage 2: Hierarchical DNS
- Root nameservers (13 globally distributed)
- TLD nameservers (top-level domain)
- Authoritative nameservers (per domain)
- Recursive resolvers (ISP, Google, Cloudflare)

### Stage 3: Caching & CDN
- DNS caches at multiple levels
- Reduce authoritative server load
- GeoDNS (route based on location)

### Stage 4: Modern DNS (DNSSEC, DoH, DoT)
- Security (DNSSEC signs records)
- Privacy (DNS-over-HTTPS, DNS-over-TLS)
- Performance (0-RTT)

---

## 7. Production Architecture

```
[Client: browser] wants example.com
    │
    ├─ Check: local cache (OS, browser)
    │  ├─ Hit: return IP (instant)
    │  └─ Miss: query recursive resolver
    │
    ├─ [Recursive Resolver] (ISP, Google 8.8.8.8, Cloudflare 1.1.1.1)
    │  ├─ Check: cache
    │  │  ├─ Hit: return to client
    │  │  └─ Miss: query hierarchy
    │  │
    │  ├─ Query [Root Nameserver]
    │  │  └─ "Where's example.com?" → "Ask TLD server"
    │  │
    │  ├─ Query [TLD Nameserver] (.com)
    │  │  └─ "Where's example.com?" → "Ask authoritative"
    │  │
    │  └─ Query [Authoritative Nameserver] (example.com)
    │     └─ "Where's example.com?" → "93.184.216.34"
    │
    └─ [Client] receives 93.184.216.34
       ├─ Cache locally (for TTL seconds)
       └─ Connect to IP
```

---

## 8. Components

### DNS Record Types

```
A: IPv4 address (example.com → 93.184.216.34)
AAAA: IPv6 address (example.com → 2606:2800:220:1:248:1893:25c8:1946)
CNAME: alias (www.example.com → example.com)
MX: mail server (example.com → mail.example.com)
NS: nameserver (example.com → ns1.example.com)
TXT: text record (SPF, DKIM for email)
SOA: start of authority (zone information)
SRV: service record (location of service)
```

### TTL (Time-To-Live)

```
TTL = 3600 (1 hour)
  Client caches for 1 hour
  After 1 hour: refetch from authoritative
  
Short TTL (300 = 5 minutes):
  Fast updates (IP changes within 5 min)
  Cost: more queries to authoritative
  
Long TTL (86400 = 1 day):
  Few queries
  Cost: stale records for 1 day if IP changes
```

### DNS Query Types

```
Recursive: resolver must fully resolve
  Client asks: resolver to find answer
  Resolver: may query root, TLD, authoritative
  Return: final IP address

Iterative: resolver returns hint
  Client asks: root nameserver
  Root: "Try TLD"
  Client asks: TLD
  TLD: "Try authoritative"
  Client asks: authoritative
  Get: final IP
```

---

## 9. Internal Working

### DNS Query Path

```
Client: "What's example.com?"
  ↓ (recursive resolver)
  
Resolver cache: miss
  ↓ (iterate through hierarchy)
  
Ask Root: "Where's example.com?"
  Root: "Don't know, try .com TLD"
  
Ask TLD (.com): "Where's example.com?"
  TLD: "Don't know, try ns1.example.com"
  
Ask Authoritative (example.com): "What's example.com?"
  Auth: "93.184.216.34"
  
Cache at resolver: 93.184.216.34 (TTL=3600)

Return to client: 93.184.216.34
Cache at client: 93.184.216.34 (TTL=3600)
```

### DNS Over UDP (Default)

```
Query: sent via UDP (no handshake, fast)
  Packet size: usually <512 bytes
  Timeout: 2 seconds typical
  Retry: after timeout (exponential backoff)

Reliability:
  UDP: no ack, fire-and-forget
  May lose packet: client retries
  Usually works (fast on good networks)
```

---

## 10. Request Lifecycle

```
t=0ms:      Browser: lookup example.com
t=0-1ms:    OS cache check (miss)
t=1ms:      Query recursive resolver (8.8.8.8)
t=1-2ms:    Network: query to resolver
t=2-3ms:    Resolver: cache check (miss, first time)
t=3-4ms:    Resolver: query root server
t=4-5ms:    Network to root
t=5-6ms:    Root: responds (try .com TLD)
t=6-7ms:    Resolver: query TLD
t=7-8ms:    Network to TLD
t=8-9ms:    TLD: responds (try authoritative)
t=9-10ms:   Resolver: query authoritative
t=10-11ms:  Network to authoritative
t=11-12ms:  Auth: responds 93.184.216.34
t=12-13ms:  Network back to resolver
t=13ms:     Resolver: cache result
t=13-14ms:  Network back to client
t=14ms:     Client: receives IP

Total: ~14ms first lookup (cached in resolver)
Second lookup (hot cache): <1ms

With client caching: subsequent lookups instant
```

---

## 11. Data Flow

### Recursive Resolver Performance

```
Query rate: 1M queries/sec
Cache hit rate: 95%
  Cached: 950K queries/sec (instant)
  Authoritative: 50K queries/sec

Cache effectiveness:
  Resolver can handle ~100K auth queries/sec
  With 95% cache: can handle 2M total queries/sec
  
Cascades to authoritative:
  If cache miss rate 50%: 500K auth queries (overload!)
  Need: bigger cache, better TTL strategy
```

---

## 12. Key Strategy

### 1. Use Public DNS Resolvers

```
Google Public DNS (8.8.8.8):
  Large cache, fast, reliable
  
Cloudflare (1.1.1.1):
  Focus on privacy, fast
  
Quad9 (9.9.9.9):
  Blocks malware, privacy-focused

Better than ISP DNS (often slow, unreliable)
```

### 2. Optimize TTL

```
Static records (rarely change):
  Long TTL (86400 = 1 day)
  Few queries, but stale records if change

Dynamic records (change often):
  Short TTL (300 = 5 min)
  More queries, fast updates
  
Default: 3600 (1 hour, balance)
```

### 3. GeoDNS Load Balancing

```
Client in US: route to US server
Client in EU: route to EU server

DNS query: from resolver IP (not client IP!)
  May be wrong location

Solution:
  Use GEOIP on resolver
  Or: use client IP (sent by resolver via ECS)
```

---

## 13. Failure Scenarios

### Scenario 1: Resolver Downstream

```
Google public DNS (8.8.8.8) down or slow
Your ISP's recursive resolver depends on it
All lookups slow/fail

User experience: can't reach any domain
```

**Fix:** 
- Primary: Google 8.8.8.8
- Secondary: Cloudflare 1.1.1.1
- Fallback: quad9 9.9.9.9

### Scenario 2: Authoritative Server Down

```
example.com authoritative goes down
Resolver still has cached records
Users: OK (cache hit)

After TTL expires:
  No answer from authoritative
  Resolver: return cached (if stale-cache enabled)
  Or: timeout

Delay: TTL + detection time (minutes to hours)
```

**Fix:**
- Multiple authoritative servers (NS records)
- NSEC3 white-lie (respond with cached even after TTL)
- Proper TTL strategy

### Scenario 3: DNS Cache Poisoning

```
Attacker: spoofs authoritative response
Inserts: wrong IP in cache
Users: redirected to attacker site
```

**Fix:**
- DNSSEC (cryptographic signing)
- Query ID randomization
- Source port randomization
```

---

## 14. Bottlenecks Table

| Issue | Impact | Symptoms | Fix |
|---|---|---|---|
| Slow resolver | High latency | DNS queries 500ms+ | Use fast public DNS |
| Cache miss rate | High load | Authoritative overloaded | Better TTL, bigger cache |
| Single resolver | Outage | No DNS | Secondary resolver |
| TLD timeout | Some domains fail | Intermittent failures | Retry with backoff |
| Stale cache | Wrong IP | Users routed incorrectly | Monitor, purge cache |

---

## 15. Monitoring

### Key Metrics

```
Resolver performance:
  ✓ Query latency: P50, P99 (target: <50ms)
  ✓ Cache hit rate: % (target: >90%)
  ✓ Query rate: QPS (track growth)

Reliability:
  ✓ NXDOMAIN rate: % (should be low)
  ✓ SERVFAIL rate: % (should be 0)
  ✓ Timeout rate: % (should be <0.1%)

Upstream:
  ✓ Authoritative reachability: can reach
  ✓ Response time: per TLD, per authoritative
```

### Red Flags

- Query latency > 100ms (slow resolver)
- Cache hit rate < 80% (low cache effectiveness)
- SERVFAIL rate > 0.1% (resolver issues)
- Authoritative unreachable (DNS breaking)

---

## 16. Optimizations

### 1. CNAME Flattening

```
Standard:
  www.example.com → CNAME → example.example.com → A → 93.184.216.34
  Client: 2 lookups (CNAME, then A)

Flattening:
  www.example.com → A → 93.184.216.34
  Client: 1 lookup

Result: faster (fewer round-trips)
```

### 2. Anycast Distribution

```
Root nameserver: actually 13 servers, 1 IP
Requests routed by BGP to nearest instance
User in US: routed to US root
User in EU: routed to EU root

Result: low latency, distributed load
```

### 3. DNS-over-HTTPS (DoH)

```
Standard DNS: plaintext UDP, traceable
DoH: DNS queries via HTTPS (encrypted)

Benefit: privacy (ISP can't see queries)
Cost: overhead (HTTPS handshake)
```

---

## 17. Security

### 1. DDoS Protection

```
Attack: billions of DNS queries to authoritative
Defense:
  - Rate limiting (max queries/IP)
  - Anycast distribution (spread load)
  - Reflection attack: use UDP response amplification
  
ISP: may drop DNS during attack
Users: can't lookup domains
```

### 2. DNSSEC

```
Sign DNS records with private key
Resolver verifies signature
Prevents: DNS poisoning, man-in-the-middle

Cost: validation overhead, larger responses
Benefit: trust (cryptographic proof)
```

---

## 18. Tradeoffs Table

| Approach | Latency | Cache Hit | Cost |
|---|---|---|---|
| ISP DNS | High | Low | Free |
| Google 8.8.8.8 | Low | High | Free |
| Custom resolver | Medium | Tunable | High |
| DoH | Latency + | High | Medium |

---

## 19. Alternatives

### Local DNS Caching

```
Running local resolver (systemd-resolved, dnsmasq)
Cache: locally, instant hits
Benefit: speed, reduce external queries
Cost: stale records if not updated
```

---

## 20. When NOT to Use

### Don't Use Long TTL When:

1. **IP changes frequently**
   - Load balancing scale-up/down
   - Use short TTL (5-10 min)

---

## 21. Interview Questions

1. **Design DNS system handling 1M queries/sec**
   - Caching strategy?
   - Failover?
   - Latency optimization?

2. **Resolver timeout increases to 5 seconds**
   - Root cause?
   - How diagnose?

3. **Compare public DNS providers**
   - Speed, reliability, privacy?

4. **DNS poisoning attack**
   - How defend?
   - DNSSEC?

---

## 22. Common Mistakes

1. **Using ISP DNS**
   - Often slow, unreliable
   - Use public DNS (8.8.8.8, 1.1.1.1)

2. **Long TTL for dynamic services**
   - IP changes, users hit old
   - Use short TTL (5-10 min)

3. **Single resolver**
   - Fails, all DNS down
   - Use multiple resolvers (failover)

4. **Not monitoring DNS**
   - Slow resolver undetected
   - Monitor latency, error rate

5. **Cache invalidation misunderstanding**
   - Can't invalidate globally (no mechanism)
   - Wait TTL to expire (can take hours)
   - Or: change CNAME during TTL

---

## 23. Debugging Guide

### Step 1: Check Resolution

```
nslookup example.com
dig example.com

Output:
  Query time: 50ms (normal)
  Status: NOERROR (OK)
  Answer: 93.184.216.34

Issue:
  Query time: 5000ms (slow!)
  Status: SERVFAIL (error)
```

### Step 2: Trace Query

```
dig +trace example.com

Shows: full path through hierarchy
  Root → TLD → Authoritative
  Timing for each

Identify: which is slow
```

### Step 3: Test Different Resolvers

```
nslookup example.com 8.8.8.8 (Google)
nslookup example.com 1.1.1.1 (Cloudflare)

Compare: latency
If one is slow: use other
```

---

## 24. Code Examples

### Go: DNS Lookup with Timeout

```go
func lookupDomain(domain string, timeout time.Duration) (string, error) {
    ctx, cancel := context.WithTimeout(context.Background(), timeout)
    defer cancel()
    
    // Use custom resolver (faster, more reliable than ISP)
    resolver := &net.Resolver{
        PreferGo: true,
        Dial: func(ctx context.Context, network, addr string) (net.Conn, error) {
            d := net.Dialer{
                Timeout: timeout,
            }
            // Use Google DNS
            return d.DialContext(ctx, network, "8.8.8.8:53")
        },
    }
    
    ips, err := resolver.LookupIPAddr(ctx, domain)
    if err != nil {
        return "", err
    }
    
    if len(ips) == 0 {
        return "", fmt.Errorf("no IPs found")
    }
    
    return ips[0].String(), nil
}

// Usage:
ip, _ := lookupDomain("example.com", 5*time.Second)
// Result: "93.184.216.34"
```

### Go: DNS Caching

```go
type DNSCache struct {
    cache map[string]*CacheEntry
    mu    sync.RWMutex
    ttl   time.Duration
}

type CacheEntry struct {
    IP        string
    ExpiresAt time.Time
}

func (dc *DNSCache) Lookup(domain string) (string, error) {
    dc.mu.RLock()
    entry, exists := dc.cache[domain]
    dc.mu.RUnlock()
    
    if exists && time.Now().Before(entry.ExpiresAt) {
        // Cache hit
        return entry.IP, nil
    }
    
    // Cache miss or expired: resolve
    ip, err := lookupDomain(domain, 5*time.Second)
    if err != nil {
        return "", err
    }
    
    // Store in cache
    dc.mu.Lock()
    dc.cache[domain] = &CacheEntry{
        IP:        ip,
        ExpiresAt: time.Now().Add(dc.ttl),
    }
    dc.mu.Unlock()
    
    return ip, nil
}

// Usage:
cache := &DNSCache{
    cache: make(map[string]*CacheEntry),
    ttl:   1 * time.Hour, // Cache for 1 hour
}
ip, _ := cache.Lookup("example.com")
```

---

## 25. Visual Diagrams

### DNS Hierarchy

```
[User] queries: example.com
  ↓
[Recursive Resolver] (8.8.8.8)
  ├─ Query [Root Server] (. zone)
  │ └─ Referral: .com TLD servers
  │
  ├─ Query [TLD Server] (.com zone)
  │ └─ Referral: example.com authoritative
  │
  └─ Query [Authoritative] (example.com zone)
     └─ Answer: 93.184.216.34

Caching:
  Resolver: caches 93.184.216.34 (TTL=3600)
  Client: caches 93.184.216.34 (TTL=3600)
  
Next query (within TTL): instant (cache hit)
```

---

## 26. Simulation Ideas

1. **Cache Hit Rate Simulator**
   - Vary: TTL, query distribution
   - Show: hit rate, query load

2. **Latency Impact**
   - Vary: resolver distance, packet loss
   - Show: query time, user experience

3. **Failover Scenario**
   - Primary resolver down
   - Show: fallback to secondary

---

## 27. Case Studies

### Case 1: GitHub DNS Outage (2016)
Problem: Single DNS provider, attacked
Solution: multi-provider failover, GeoDNS
Result: resilience to single-provider attacks

### Case 2: Cloudflare DNS
Performance: optimized caching, Anycast
Result: <10ms global latency

---

## 28. Related Topics

- **Load Balancing via DNS**
- **GeoDNS & Anycast**
- **DNSSEC**

---

## 29. Advanced Topics

### EDNS Client Subnet (ECS)

```
Resolver sends: client IP (or subnet)
Authoritative: responds based on client location
Not: resolver location

Benefit: GeoDNS accuracy (actual user location)
Privacy: resolver reveals client location
```

---

## 30. Production Checklist

- [ ] Use public DNS resolver (not ISP)
- [ ] Primary: 8.8.8.8, Secondary: 1.1.1.1
- [ ] Set appropriate TTL (3600 default, shorter for dynamic)
- [ ] Monitor DNS latency (P50, P99)
- [ ] Monitor query rate (growth tracking)
- [ ] Implement client-side DNS caching
- [ ] Cache negative responses (NXDOMAIN)
- [ ] Test failover to secondary resolver
- [ ] Implement timeout on lookups (5s max)
- [ ] Monitor NXDOMAIN, SERVFAIL rates
- [ ] Consider DoH for privacy (if needed)
- [ ] Document DNS records (A, CNAME, MX, etc)
- [ ] Monitor TTL expiration (no stale cache after TTL)
- [ ] Test with packet loss simulator
- [ ] Log slow DNS queries (>100ms)

---

*Last Updated: 2026-05-28*
