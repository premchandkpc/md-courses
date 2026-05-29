# Network Performance & Optimization Deep Dive - L5 Networking

> **[🎨 View Interactive Diagram](network-performance-architecture.html)** | [🎨 Rate Limiting Simulator](../../../html/01-rate-limiting-token-bucket-viz.html) | [← Back to Index](../../systems-index.html)

*"Why is my app slow? How do I identify network bottlenecks?"*

---

## 1. Problem Statement

**Core Question:** How measure network performance? How optimize latency, bandwidth, loss?

Challenges:
- Latency has many sources (routing, queueing, processing)
- Bandwidth: utilization vs capacity
- Packet loss: cascading impact
- Network invisible: hard to debug from application

Need: measurement, identification, optimization

---

## 2. Real World Analogy

**Highway Congestion:**

No monitoring:
- Drivers don't know where delays are
- Take random routes (worsen congestion)
- Traffic info: useless

With monitoring:
- Know: where slow (accidents, construction)
- Reroute: avoid congestion
- Capacity: add lanes when needed

Result: informed decisions, better flow

---

## 3. Why Problem Exists

### Latency Complexity

```
Total latency: sum of many sources

Source 1: Network propagation (fixed by distance)
  Tokyo → SF: 26ms minimum (speed of light)
  
Source 2: Router processing (varies by load)
  Empty queue: 1ms
  Congested: 50ms+
  
Source 3: TCP/IP stack (varies by tuning)
  Good: 10ms
  Bad: 100ms
  
Source 4: Application processing (in our control)
  Fast: 10ms
  Slow: 1000ms
  
Total: can be 26ms (fast) to 1100ms (slow)
Need: identify which source slowing
```

### Bandwidth vs Latency

```
Bandwidth: throughput (how much data per second)
  100 Mbps: can send 100M bits per second
  
Utilization: how much being used
  Ideal: ~80% (headroom for spikes)
  >95%: congestion, queueing, latency
  
Latency: time to send one packet
  Low bandwidth + high utilization = high latency
```

---

## 4. Naive Approach

**"Just watch response times"**

Problems:
- Application slow ≠ network slow
- Network problem: hides in P99
- Root cause: invisible from app metrics alone

---

## 5. Why Naive Fails

### Latency Hiding

```
Measurement: response time 100ms
Breakdown:
  Database: 50ms (slow query)
  Network: 40ms (router congestion)
  Processing: 10ms
  
"Fix database" → response time 60ms
  Network still congested (problem remains)
  
Must measure: each layer separately
```

### Bandwidth Saturation

```
Link: 1 Gbps capacity
Usage: 950 Mbps (95%)
  Result: new packets queue

Customer: "why slow?"
  Reason: bandwidth near limit
  Solution: bigger pipe

But: upgrading to 10 Gbps:
  Cost: 100x
  Solve: temporary (usage grows)
  
Better: optimize first
  Compress: reduce 950 → 200 Mbps
  Result: same service, 1/5 cost
```

---

## 6. Evolution / Progression

### Stage 1: Black Box
- Only response time visible
- No networking insight

### Stage 2: Basic Metrics
- Ping latency
- Packet loss % (yes/no)

### Stage 3: Detailed Metrics
- Per-hop latency (traceroute)
- Jitter (latency variance)
- Bandwidth utilization

### Stage 4: Network Telemetry
- Flow-level analytics
- Per-connection loss/reordering
- Real-time optimization

---

## 7. Production Architecture

```
[Application]
    ↓ (instrument: request start/end times)
[Network Monitoring]
    ├─ Ping: latency
    ├─ MTR: per-hop latency
    ├─ Iperf: bandwidth test
    ├─ Tcpdump: packet analysis
    └─ Flow export (Netflow/sFlow)
    
[Analytics]
    ├─ Identify: bottlenecks
    ├─ Correlate: latency with congestion
    └─ Alert: on degradation
    
[Optimization]
    ├─ Compress: data
    ├─ Batch: requests
    ├─ Upgrade: capacity
    └─ Reroute: traffic
```

---

## 8. Components

### Latency Measurement

```
Ping: measures round-trip latency
  Send: ICMP echo
  Receive: echo reply
  Time: delta

Result: typical 1-100ms

Limitation: doesn't measure congestion (queue depth)
  Ping: lightweight (not affected by other traffic)
  TCP: affected by congestion (more realistic)
```

### Bandwidth Test (Iperf)

```
Throughput test: send max data for duration

Iperf: results
  Bandwidth: 850 Mbps achieved
  Capacity: 1 Gbps available
  Utilization: 85% (good)

Limitation: test must reach full capacity
  If congestion elsewhere: doesn't show
```

### Packet Loss

```
Send: 100 packets
Receive: 98 packets
Loss: 2% (bad)

Impact: TCP retransmit
  Retransmit: adds 100-500ms latency
  Degradation: if loss >0.1%, latency increases

Correlation: loss correlates with latency
```

---

## 9. Internal Working

### Latency Breakdown

```
User request → response timeline:

t=0ms:       Client initiates connection (DNS)
t=0-10ms:    DNS resolution (network + recursive)
t=10-20ms:   TCP 3-way handshake (1 RTT)
t=20-25ms:   TLS handshake (2 RTT)
t=25-30ms:   HTTP request (1 RTT)
t=30-40ms:   Application processing (server)
t=40-45ms:   HTTP response (1 RTT)
t=45-50ms:   Browser render

Total: 50ms ideal
Actual: 200ms (congestion, slow processing, etc)

Identify: which hops slow?
  Traceroute: per-hop time
  Packet capture: protocol timing
```

### Queueing Theory

```
Arrivals: M (Poisson: random)
Service: M (exponential: random)
Queue: 1 (single server)

Latency: L = lambda / (mu - lambda)
  lambda: arrival rate
  mu: service rate
  
Example: 100K req/s, server handles 150K
  Latency: 100,000 / (150,000 - 100,000) = 2ms

If: 100K arrivals, server only 110K capacity
  Latency: 100,000 / (110,000 - 100,000) = 10ms (5x!)
  
Insight: near capacity → latency explodes
```

---

## 10. Request Lifecycle

```
Video streaming measurement:

t=0ms:       User initiates video request
t=0-50ms:    DNS + TCP (network setup)
t=50-100ms:  First chunk request
t=100-200ms: CDN response (latency + processing)
t=200ms+:    Buffering (filling buffer)

Monitor:
  Per-hop latency: identify slow segment
  Packet loss: detect congestion
  Jitter: detect queueing

Example finding:
  Hop 5 (ISP router): 50ms (high)
  Issue: ISP congestion
  Action: notify, escalate to ISP
```

---

## 11. Data Flow

### Network Optimization

```
Scenario: user reports slow experience

Step 1: Measure
  Ping: 50ms (OK)
  Video latency: 500ms (bad)
  Packet loss: 5% (very bad)
  
Step 2: Diagnose
  TCP retransmit: 5% loss → 100ms extra per loss
  Queue depth: router buffer full
  
Step 3: Fix
  Optimize: compress video 50% (less congestion)
  Upgrade: ISP link from 1G → 10G
  Route: use different ISP (avoid congestion)
  
Result: latency → 100ms (5x better)
```

---

## 12. Key Strategy

### 1. Measure Continuous

```
Monitor: in production (always)
Baseline: normal latency (establish)
Alert: deviation (2x normal → investigate)

Types:
  Synthetic: send test traffic (always same)
  Real: actual user traffic (varied)
  
Both: needed for complete picture
```

### 2. Identify Bottleneck

```
Latency high: which layer?

Layer 1: DNS (bottleneck)
  Solution: DNS caching, GeoDNS

Layer 2: Network (bottleneck)
  Solution: upgrade, reroute, CDN

Layer 3: Application (bottleneck)
  Solution: optimize code, scale

Find: using detailed metrics
  Not: guessing
```

### 3. Optimize

```
Identify: network saturated

Solutions:
  Immediate: compress, batch (reduce data)
  Short-term: traffic shape, reroute
  Long-term: upgrade capacity, CDN
```

---

## 13. Failure Scenarios

### Scenario 1: Congestion Collapse

```
Network: 95%+ utilization
  Packet loss: >1% (acceptable TCP breaks)
  Queueing: increased
  
Cascade: bad
  Traffic: increases (UDP retry)
  Loss: increases (packets drop)
  Traffic: increases (app retry)
  
Result: network unusable (Ethernet ~10%, TCP ~1% loss)

Solution:
  Rate limiting: cap traffic
  Backoff: exponential (reduce)
  Failover: different route
```

### Scenario 2: Path Changes

```
Routing: changes (ISP optimization)
  New path: goes through congested link
  Latency: increases (user complaints)

Detection: hard (path invisible)
Solution:
  Continuous measurement (detect)
  BGP monitoring (learn path change)
  Alert: on latency increase
```

### Scenario 3: MTU Fragmentation

```
Frame size: 1500 bytes (standard)
Request: 2000 bytes
  Fragmented: into 2 packets
  
Reassembly: if one lost, entire lost
  Loss rate: increases

Solution:
  Optimize: send data within MTU
  PMTUD: discover correct MTU
  
Example: 1500 bytes might be 1460 (headers)
Send: 1450 (safe)
```

---

## 14. Bottlenecks Table

| Issue | Impact | Detection | Fix |
|---|---|---|---|
| Congestion | High latency | Latency/loss monitoring | Rate limit, upgrade |
| Packet loss | Retransmit, slow | Loss counter | Reroute, diagnosis |
| DNS slow | Initial delay | DNS timing | Caching, GeoDNS |
| MTU issues | Fragmentation | Packet analysis | Reduce payload size |

---

## 15. Monitoring

### Key Metrics

```
✓ Latency: P50, P95, P99 (percentiles important)
✓ Packet loss: % (target: <0.01%)
✓ Jitter: variance in latency
✓ Bandwidth utilization: %
✓ Error rate: 4xx, 5xx
✓ Per-hop latency: via traceroute/MTR
```

---

## 16. Optimizations

### 1. Compression

```
Request: 1MB JSON
Gzip: 200KB (80% reduction)
Brotli: 150KB (85% reduction)

Tradeoff: CPU (compression) vs bandwidth
Result: faster transfer, less network stress
```

### 2. Connection Pooling

```
Without: new TCP for each request
  Handshake: 1 RTT per connection
  100 requests: 100 RTT

With: reuse connections
  1 connection: shared
  100 requests: 1 RTT (connection setup)
  
Result: 100x faster (handshake amortized)
```

### 3. Protocol Optimization

```
HTTP/1.1: 1 request per connection (slow)
HTTP/2: multiplexing (many requests per connection)
  Result: 2-3x faster

QUIC: 0-RTT (resume previous connection)
  Result: instant (no handshake)
```

---

## 17. Security

### 1. Encryption Overhead

```
TLS: adds CPU cost (handshake + stream cipher)
  Cost: 5-10% latency overhead

Modern (TLS 1.3): optimized
  Cost: 2-3% latency overhead

Trade: security (encryption) vs latency
  Usually: acceptable (security > performance)
```

---

## 18. Tradeoffs Table

| Approach | Latency | Complexity | Cost |
|---|---|---|---|
| Measure only | No improvement | Low | Low |
| Compress | Better | Low | Medium |
| Upgrade link | Better | Low | High |
| CDN | Better | Medium | Medium |
| Optimize app | Better | High | Low |

---

## 19. Alternatives

### SD-WAN

```
Software-defined: dynamic routing
Per-flow: optimization
  Cost: expensive
  Benefit: performance + failover
```

---

## 20. When NOT to Use

### Don't Over-Optimize When:

1. **Already fast (<50ms)**
   - Cost-benefit poor
   - Diminishing returns

---

## 21. Interview Questions

1. **Design performance monitoring**
   - Metrics?
   - Dashboards?
   - Alerts?

2. **Latency spike investigation**
   - Diagnose approach?
   - Tools?

3. **Optimize for 1M users**
   - Identify bottleneck?
   - Solutions?

---

## 22. Common Mistakes

1. **No baseline**
   - Can't detect degradation
   - Establish: normal latency

2. **Only average latency**
   - Outliers: hidden (P99 matters)
   - Track: percentiles

3. **No per-hop measurement**
   - Blame: wrong layer
   - Use: traceroute to identify

4. **Optimize without measuring**
   - Changes: no effect
   - Measure: before/after

---

## 23. Debugging Guide

### Step 1: Check Latency

```
ping -c 100 example.com
Shows: min/avg/max/stddev
  stddev high: jitter (queueing)
```

### Step 2: Check Per-Hop

```
mtr example.com
Shows: latency per hop, packet loss
  Hop 5: 50ms (identify slow segment)
```

### Step 3: Check Bandwidth

```
iperf -c server
Shows: achievable bandwidth
  Low: saturation or congestion
```

---

## 24. Code Examples

### Go: Latency Measurement

```go
func measureLatency(url string) time.Duration {
    start := time.Now()
    
    client := &http.Client{
        Timeout: 10 * time.Second,
    }
    
    resp, _ := client.Get(url)
    defer resp.Body.Close()
    
    latency := time.Since(start)
    return latency
}

func measurePercentile(measurements []time.Duration) {
    sort.Slice(measurements, func(i, j int) bool {
        return measurements[i] < measurements[j]
    })
    
    p50 := measurements[len(measurements)*50/100]
    p95 := measurements[len(measurements)*95/100]
    p99 := measurements[len(measurements)*99/100]
    
    fmt.Printf("P50: %v, P95: %v, P99: %v\n", p50, p95, p99)
}
```

---

## 25. Visual Diagrams

### Latency Breakdown

```
Total: ────────────────── 200ms

DNS:          ██ 10ms
Network:      ████████ 60ms
TLS:          ████ 30ms
Processing:   ███████ 60ms
Response:     ████ 30ms
Render:       ██ 10ms
```

---

## 26. Simulation Ideas

1. **Congestion Impact**
   - Vary: utilization
   - Show: latency curve

---

## 27. Case Studies

### Google: measurement infrastructure
Result: every request measured, real-time dashboards

---

## 28. Related Topics

- **Distributed Tracing**
- **Observability**

---

## 29. Advanced Topics

### ECMP (Equal Cost Multipath)

```
Multiple paths: same cost
Router: splits traffic evenly
  Flow-based: consistent per-connection
  
Benefit: load distribution, redundancy
```

---

## 30. Production Checklist

- [ ] Baseline latency established
- [ ] Continuous measurement (synthetic)
- [ ] Real user measurement (RUM)
- [ ] Per-hop latency monitoring
- [ ] Packet loss monitoring
- [ ] Bandwidth utilization tracking
- [ ] Alerts on degradation (2x normal)
- [ ] Dashboard: latency percentiles
- [ ] Diagnostic tools: ping, MTR, iperf
- [ ] Compression enabled (gzip minimum)
- [ ] Connection pooling implemented
- [ ] Protocol optimized (HTTP/2 minimum)

---

*Last Updated: 2026-05-28*
