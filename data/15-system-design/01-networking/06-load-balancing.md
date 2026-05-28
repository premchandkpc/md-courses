# Load Balancing Deep Dive - L5 Networking

> **[🎨 View Interactive Diagram](load-balancing-architecture.html)** | [← Back to Index](../../systems-index.html)

*"10 backend servers. How distribute 100K requests/sec fairly?"*

---

## 1. Problem Statement

**Core Question:** Single server can't handle all traffic. How distribute across many servers?

Challenge:
- Uneven distribution → some overloaded, some idle
- Server failures → need failover
- Geographic dispersion → need smart routing

---

## 2. Real World Analogy

**Restaurant Queue:**

No load balancing: all customers to Waiter A
- Waiter A: overloaded
- Waiters B,C: idle
- Service slow

With load balancing: distribute equally
- All waiters: balanced load
- Service fast

---

## 3. Why Problem Exists

### Uneven Capability
```
Server A: 10K req/sec
Server B: 5K req/sec (older hardware)

If split 50-50:
  A: 50K overloaded
  B: 25K overloaded
  Total: bottleneck

With weighted:
  A: 2/3 traffic (65K requests)
  B: 1/3 traffic (35K requests)
  Balanced load
```

---

## 4. Naive Approach

**"Round-robin (even split)"**

Problems:
- Ignores uneven server capacity
- Doesn't account for request complexity
- No failover on server failure

---

## 5. Why Naive Fails

### Capacity Mismatch
```
3 servers, but one is half-speed
Equal split: fast servers underutilized, slow overloaded
Result: system bottleneck at slowest

Need: weighted distribution
```

---

## 6. Evolution / Progression

### Stage 1: No Load Balancing
- Single server
- Bottleneck

### Stage 2: Round-Robin
- Basic distribution
- Doesn't account for capacity

### Stage 3: Weighted Load Balancing
- Account for server capacity
- Health checks for failover

### Stage 4: Intelligent Routing
- Layer 7 aware (request type aware)
- Dynamic capacity adjustment
- Geographic routing

---

## 7. Production Architecture

```
[Clients 100K req/sec]
    ↓
[Load Balancer]
  ├─ Algorithm: least connections, weighted, layer 7
  ├─ Health checks: every 5 seconds
  ├─ Failover: remove dead servers
  └─ Sticky: route same user to same server (if needed)
    
    ├─ Server A (weight 3): 60K req/sec
    ├─ Server B (weight 2): 40K req/sec
    └─ Server C (weight 1): offline (failed)
```

---

## 8. Components

### Load Balancing Algorithms

```
Round-Robin: 1→A, 2→B, 3→C, 4→A... (simple, ineffective)
Least Connections: route to server with fewest active connections
Weighted: A gets 2x requests (account for capacity)
IP Hash: same IP always to same server (sticky)
Random: pick random server
Least Response Time: route to fastest
Resource Aware: CPU, memory based
```

### Health Checks

```
Active: load balancer pings server
  Interval: 5-10 seconds
  On failure: remove from rotation
  Recovery: add back if healthy

Passive: monitor response errors
  5xx rate high: likely unhealthy
  Reduce traffic: before full removal
```

### Session Persistence (Sticky Sessions)

```
Without: user A request 1 → Server A, request 2 → Server B
  Problems: session lost (different server)

With sticky:
  User A: always → Server A (for all requests)
  Benefit: session continuity
  Cost: uneven load (some users heavy)
```

---

## 9. Internal Working

### Least Connections Algorithm

```
Server A: 100 active connections
Server B: 50 active connections
Server C: 75 active connections

New request:
  → Route to B (fewest connections)
  Load balanced dynamically
```

---

## 10. Request Lifecycle

```
t=0ms:      Client sends request to LB IP
t=1-5ms:    LB selects backend server
t=5-10ms:   Network to selected server
t=10-100ms: Server processes
t=100-110ms: Network back to client
Total: ~110ms
```

---

## 11. Data Flow

### Server Failure Scenario

```
Servers: A (healthy), B (healthy), C (healthy)

t=0-100ms: Traffic distributed 1/3 each

t=100ms:   Server C fails (power loss)

t=100-105ms: Health check detects failure
t=105ms:    C removed from rotation

t=105-200ms: Traffic redistributed
  A: 50% (1/3 → 1/2)
  B: 50% (1/3 → 1/2)
  C: 0% (offline)

Users: transparent failover (~5ms delay)
```

---

## 12. Key Strategy

### 1. Distribute Evenly

```
Monitor: connection count, response time per server
Rebalance: if variance > 20%
Adjust: weights or algorithm
```

### 2. Health Checks

```
Frequent checks: detect failures quickly
Graceful removal: don't drop mid-request
Readiness probes: ensure server is truly ready
```

### 3. Geographic Distribution

```
Users in US: route to US servers (low latency)
Users in EU: route to EU servers
Global: use GeoDNS or intelligent LB
```

---

## 13. Failure Scenarios

### Scenario: Cascading Overload

```
Server C becomes slow (high latency)
LB still routes to it (waiting for health check)
Requests: queue up, timeout
Other servers: get excess traffic
Cascade: entire system slow
```

**Fix:** Adaptive algorithm (detect response time increase)

---

## 14. Bottlenecks Table

| Issue | Fix |
|---|---|
| Uneven load | Weighted algorithm |
| Server failure | Health checks, failover |
| Session loss | Sticky sessions |
| LB single point of failure | Multiple LBs, failover |

---

## 15. Monitoring

```
✓ Server load distribution (variance < 20%)
✓ Health check success rate (>99%)
✓ Failover latency (< 10 seconds)
✓ Connection distribution
```

---

## 16. Optimizations

### Connection Pooling

```
Reuse connections to backend servers
Reduce: handshake overhead
Increase: throughput
```

### Caching at LB

```
Cache: frequently accessed responses
Return: instantly (no backend query)
Reduce: backend load
```

---

## 17. Security

### DDoS Mitigation

```
Rate limit: per IP, per endpoint
Detect: unusual patterns
Block: malicious traffic
```

---

## 18. Tradeoffs Table

| Algorithm | Fairness | Complexity | Stickiness |
|---|---|---|---|
| Round-robin | Equal | Low | No |
| Weighted | Proportional | Low | No |
| Least conn | Fair | Medium | No |
| IP hash | Unknown | Low | Yes |

---

## 19. Alternatives

### Client-Side Load Balancing

```
Client: choose backend directly (from list)
Pro: no central LB bottleneck
Con: client logic complex

Use: microservices within datacenter
```

---

## 20. When NOT to Use

### Don't Load Balance When:

1. **Single server sufficient**
   - Overhead not worth it

---

## 21. Interview Questions

1. **Design LB for 1M req/sec**
   - Algorithm?
   - Failover?
   - Stickiness?

2. **Server C slow, LB still sends traffic**
   - Why?
   - How detect?
   - Solutions?

---

## 22. Common Mistakes

1. **Ignoring server capacity differences**
   - Equal split → bottleneck at slowest
   - Use: weighted distribution

2. **No health checks**
   - Dead server still gets traffic
   - Add: frequent health checks

3. **Sticky sessions for everything**
   - Uneven load
   - Use: only when necessary

---

## 23. Debugging Guide

### Step 1: Check Distribution

```
Monitor backend load:
  Server A: 35% (target: 33%)
  Server B: 33%
  Server C: 32%

Balanced: ✓
```

### Step 2: Check Health

```
Health check: passes? (200 OK)
Latency: under threshold?
Error rate: acceptable?
```

---

## 24. Code Examples

### Go: Weighted Round-Robin

```go
type LB struct {
    servers []*Server
    weights []int
    index   int
}

func (lb *LB) NextServer() *Server {
    // Weighted round-robin
    totalWeight := 0
    for _, w := range lb.weights {
        totalWeight += w
    }
    
    count := 0
    for {
        lb.index = (lb.index + 1) % len(lb.servers)
        count++
        if count >= lb.weights[lb.index] {
            return lb.servers[lb.index]
        }
    }
}
```

---

## 25. Visual Diagrams

### Load Distribution

```
Equal Split:      Server A (50%)
                  Server B (50%)

Weighted (2:1):   Server A (66%)
                  Server B (33%)

Least Conn:       Dynamic based on connections
```

---

## 26. Simulation Ideas

1. **Distribution Fairness**
   - Vary: algorithm, server capacity
   - Show: load balance

---

## 27. Case Studies

### Netflix: Layer 7 LB
Result: route by request type, 99.99% availability

---

## 28. Related Topics

- **Health Checking**
- **Failover Strategies**
- **Geographic Routing**

---

## 29. Advanced Topics

### Consistent Hashing

```
Instead of: mod-based (loses all on server failure)
Use: ring hash (lose 1/N on failure)
Benefit: minimal rehashing on scale
```

---

## 30. Production Checklist

- [ ] Choose appropriate algorithm (weighted)
- [ ] Implement health checks (every 5s)
- [ ] Failover strategy (remove dead)
- [ ] Multiple LBs (HA)
- [ ] Monitor distribution (< 20% variance)
- [ ] Test failure scenarios
- [ ] Document weights/settings
- [ ] Rate limiting at LB
- [ ] Graceful shutdown (drain connections)
- [ ] Sticky sessions (if needed)

---

*Last Updated: 2026-05-28*

<!-- html-live -->
<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>
    .topology-title {color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:12px;letter-spacing:1px}
    .topology-svg {width:100%;max-width:600px;height:300px;background:#1a2332;border:1px solid #1e3a5f;border-radius:4px}
    .topo-edge {stroke:#1e3a5f;stroke-width:2}
    .topo-legend {display:flex;gap:16px;margin-top:12px;font-size:12px;color:#e3eaf0;font-family:monospace;flex-wrap:wrap}
    .legend-item {display:flex;align-items:center;gap:6px}
  </style>
  <div class="topology-title">Load Balancer Topology</div>
  <svg class="topology-svg" viewBox="0 0 600 300">
    <defs><marker id="arrow1" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><polygon points="0 0, 10 3, 0 6" fill="#1e3a5f"/></marker></defs>
    <g><rect x="250" y="20" width="100" height="50" rx="4" fill="#1e3a5f" stroke="#00d4ff" stroke-width="1"/><text x="300" y="50" text-anchor="middle" fill="#e3eaf0" font-size="12" font-family="monospace">Load Balancer</text></g>
    <g><rect x="80" y="140" width="80" height="50" rx="4" fill="#1e3a5f" stroke="#00d4ff" stroke-width="1"/><text x="120" y="170" text-anchor="middle" fill="#e3eaf0" font-size="12" font-family="monospace">Server-1</text></g>
    <g><rect x="260" y="140" width="80" height="50" rx="4" fill="#1e3a5f" stroke="#00d4ff" stroke-width="1"/><text x="300" y="170" text-anchor="middle" fill="#e3eaf0" font-size="12" font-family="monospace">Server-2</text></g>
    <g><rect x="440" y="140" width="80" height="50" rx="4" fill="#1e3a5f" stroke="#00d4ff" stroke-width="1"/><text x="480" y="170" text-anchor="middle" fill="#e3eaf0" font-size="12" font-family="monospace">Server-3</text></g>
    <line class="topo-edge" x1="300" y1="70" x2="120" y2="140" marker-end="url(#arrow1)"/>
    <line class="topo-edge" x1="300" y1="70" x2="300" y2="140" marker-end="url(#arrow1)"/>
    <line class="topo-edge" x1="300" y1="70" x2="480" y2="140" marker-end="url(#arrow1)"/>
  </svg>
  <div class="topo-legend">
    <div class="legend-item"><div style="width:14px;height:14px;background:#1e3a5f;border:1px solid #00d4ff"></div><span>Server</span></div>
  </div>
</div>

<!-- html-live -->
<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>
    .obs-title {color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px;letter-spacing:1px}
    .obs-grid {display:grid;grid-template-columns:repeat(auto-fit, minmax(150px, 1fr));gap:12px}
    .obs-card {padding:12px;background:#1a2332;border:1px solid #1e3a5f;border-radius:4px;display:flex;flex-direction:column;align-items:center;transition:all 0.3s}
    .obs-card:hover {border-color:#00d4ff;box-shadow:0 0 8px rgba(0, 212, 255, 0.3)}
    .obs-label {color:#a3aab8;font-family:monospace;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px}
    .obs-value {font-family:monospace;font-size:20px;font-weight:bold;margin-bottom:4px;letter-spacing:0.5px}
    .obs-unit {color:#a3aab8;font-family:monospace;font-size:10px;text-transform:uppercase}
    .metric-healthy {color:#34d399}
    .metric-warning {color:#fbbf24}
  </style>
  <div class="obs-title">Load Balancer Metrics</div>
  <div class="obs-grid">
    <div class="obs-card">
      <div class="obs-label">Throughput</div>
      <div class="obs-value metric-healthy">15K</div>
      <div class="obs-unit">req/s</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Latency</div>
      <div class="obs-value metric-healthy">2</div>
      <div class="obs-unit">ms</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Healthy Servers</div>
      <div class="obs-value metric-healthy">3</div>
      <div class="obs-unit">of 3</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Connection Pool</div>
      <div class="obs-value metric-healthy">94</div>
      <div class="obs-unit">%</div>
    </div>
  </div>
</div>
