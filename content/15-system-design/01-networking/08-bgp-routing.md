---
title: BGP & Routing Deep Dive - L5 Networking
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# BGP & Routing Deep Dive - L5 Networking

> **[🎨 View Interactive Diagram](bgp-architecture.html)** | [← Back to Index](../../systems-index.html)

*"How do packets find paths across the internet? How do autonomous systems communicate?"*

---

## 1. Problem Statement

**Core Question:** How route packets between independent networks? How ensure delivery via optimal path?

Challenge: Internet fragmented (65K+ autonomous systems)
No central routing database
Dynamic: links fail, need rerouting

Need: decentralized routing protocol, fast convergence

---

## 2. Real World Analogy

**Road Networks:**

City-level (IGP: OSPF):
- Know all roads in city
- Shortest path to any destination
- Updates propagate locally (fast)

Interstate system (BGP):
- Each state: manages own roads
- State A: knows path to state B
- Phone calls: "send traffic to state C through us"
- Agreements: business relationships (peers)

Result: nationwide routing, no single authority

---

## 3. Why Problem Exists

### Network Fragmentation

```
Internet: 65K+ autonomous systems (AS)
Each AS: owned by different company
No hierarchy: Amazon, Google, Comcast are peers

Challenge: how coordinate?
  No central authority
  Each AS: want own optimization
  Result: need dynamic protocol

BGP: handles decentralized routing
```

### Link Failures

```
Route: AS1 → AS2 → AS3 → destination
Link (AS2→AS3): fails

Without BGP: traffic stuck
  Packets: can't reach destination

With BGP: convergence
  AS2: announces "can't reach destination via AS3"
  BGP: recalculates
  AS1: routes via AS4 → AS5 → destination
  Time: ~3-5 minutes (slow, but works)
```

---

## 4. Naive Approach

**"Tell everyone about all routes"**

Problems:
- Flood: every AS learns everything (|V|²)
- Scalability: 65K ASes, millions of routes
- Convergence: takes hours to settle

---

## 5. Why Naive Fails

### Route Explosion

```
Global routing: billions of routes
Flood: everyone learns everything
  Memory: terabytes per router
  CPU: constant recomputation
  Bandwidth: chat flooding network

Better: aggregate routes
  192.0.2.0/24 represents 256 IPs
  Announce once, benefit all
```

### AS-level abstraction

```
Instead: AS → AS routes (not IP-level)
  AS1: "I can reach 192.0.0.0/8"
  AS2: "I can reach 203.0.113.0/8"
  
Trade: less precise routing
Benefit: scalable (65K ASes vs billions of IPs)
```

---

## 6. Evolution / Progression

### Stage 1: IGP Only (OSPF)
- Routing within single AS
- All routers know all routes
- Doesn't scale globally

### Stage 2: BGP Early
- Announce: which ranges I reach
- No path vector (easy to loop)

### Stage 3: BGP with Path Vector
- Announce: "AS1 → AS2 → AS3 → destination"
- Reject: if own AS in path (loop prevention)

### Stage 4: Modern BGP (with policies)
- Communities (traffic engineering)
- Prepending (deprioritize routes)
- Local preference (internal ranking)

---

## 7. Production Architecture

```
[ISP A]
  Router R1: internal (OSPF)
    ↓
  Router R1: BGP speaker
    ├─ Peer with ISP B (BGP)
    ├─ Peer with ISP C (BGP)
    └─ Announce: "I reach 1.2.3.0/24"

[ISP B]
  Router R2: BGP speaker
    ├─ Learned: "A reaches 1.2.3.0/24"
    ├─ Peer with ISP C (BGP)
    └─ Re-announce: "via A, reach 1.2.3.0/24"

[ISP C]
  Router R3: BGP speaker
    ├─ Learned: "reach 1.2.3.0/24 via A"
    ├─ Learned: "reach 1.2.3.0/24 via B"
    └─ Pick: lower AS-path (fewer hops)
```

---

## 8. Components

### BGP Message

```
UPDATE message:
  Withdrawn routes: remove these prefixes
  Path attributes:
    AS-path: list of ASes (loop detect)
    Next-hop: who to send to
    Local preference: ranking (1-65535)
    MED (multi-exit discriminator): cost hint
    
Example:
  Announce: 192.0.2.0/24
  AS-path: AS1 → AS2 → AS3
  Next-hop: 203.0.113.1
  Local-pref: 100
```

### Attributes

```
AS-path: [1, 2, 3]
  AS1 sent to AS2
  AS2 sent to AS3
  AS3 sends to us
  Longest: fewer hops better (shorter is faster)

Local preference: internal policy
  Route A: local-pref 100 (preferred)
  Route B: local-pref 50
  Pick: A (if all else equal)

MED (multi-exit discriminator):
  AS1: "prefer entering via router 1 (MED=10)"
  AS1: "avoid router 2 (MED=100)"
```

---

## 9. Internal Working

### Route Selection (Best Path)

```
Receive multiple paths to 192.0.2.0/24:

Path 1: AS-path [10, 20, 30], local-pref 100
Path 2: AS-path [10, 40], local-pref 100
Path 3: AS-path [50, 60], local-pref 80

Selection:
  1. Highest local-pref: Path 1,2 (100>80)
  2. Shortest AS-path: Path 2 ([10,40] < [10,20,30])
  3. Result: Path 2 chosen
```

### Convergence Time

```
Link (AS1→AS2): fails

t=0:       Link down (detected by keepalive timeout)
t=5s:      AS1 marks route invalid
t=10s:     AS1 announces: "withdrawn 192.0.2.0/24 via AS2"
t=15s:     Neighbors receive, recalculate
t=20s:     AS1 announces: "192.0.2.0/24 via AS3" (alt path)
t=25s:     Propagates globally (25-180s for convergence)
t=180s:    Full network converged

Result: 3-5 minute global convergence (slow)
```

---

## 10. Request Lifecycle

```
Traffic: user in AS1 → destination in AS3

t=0ms:       User initiates connection
t=0-50ms:    ISP A router (R1) receives packet
t=50-100ms:  R1 BGP: route to 192.0.2.0/24?
t=100-101ms: BGP table: route via AS2 → AS3
t=101-102ms: Forward: AS2 (next hop)
t=102-130ms: AS2 network transit
t=130-131ms: AS2 router (R2) BGP: route to 192.0.2.0/24?
t=131-132ms: BGP table: route via AS3
t=132-133ms: Forward: AS3
t=133-160ms: AS3 network transit
t=160-200ms: Destination received

Latency: ~200ms (depends on AS-path length)
Longer path: more latency
```

---

## 11. Data Flow

### Traffic Engineering

```
Source: AS1
Destination: 192.0.2.0/24 (reachable via AS2 or AS3)

Default (shortest AS-path):
  AS-path: [1, 2, 3] (chosen)
  AS-path: [1, 4, 5, 3] (not chosen)

Traffic engineering (prepending):
  AS1: prepend self to one path
  AS1 → AS1 → AS2 → AS3 (longer, avoided)
  AS1 → AS4 → AS5 → AS3 (shorter, preferred)
  
Result: traffic goes via preferred path

Real use: balance traffic, avoid congestion
```

---

## 12. Key Strategy

### 1. Path Selection

```
Rank routes by policy:
  1. Local preference (internal ranking)
  2. AS-path length (fewer hops)
  3. Origin (IGP vs EGP vs incomplete)
  4. MED (exit point optimization)

Result: deterministic, predictable routing
```

### 2. Failover

```
Primary link fails:
  BGP: detects (no keepalive)
  Announce: withdraw route
  Neighbors: recalculate
  Backup: activated (longer AS-path)
  
Time: 3-5 minutes (high, use local failover for critical)
```

### 3. Load Balancing

```
Multiple paths same cost:
  Router: split traffic (usually ECMP)
  Per-flow: consistent hashing
  
Result: distribute load across paths
```

---

## 13. Failure Scenarios

### Scenario 1: BGP Hijack

```
Attacker: announces "I reach 8.8.8.0/24" (Google DNS)
  Global routing: traffic goes to attacker
  Users: redirected to attacker server
  
Impact: massive (man-in-the-middle)

Mitigation:
  RPKI: signed announcements
  Route filtering: drop invalid ASes
```

### Scenario 2: Route Flapping

```
Link: oscillates (up/down/up/down)
BGP: re-announces each time
  Cascading: all neighbors recalculate
  CPU: spike (unnecessary churn)

Solution: dampening
  Penalize: flapping route
  Suppress: temporarily
  Time: reset on stability
```

### Scenario 3: Blackhole

```
AS1: announces "I reach 192.0.2.0/24"
  But: drops traffic silently
  
Result: traffic sent to AS1, lost

Detection: tricky (monitors needed)
Solution: customer monitoring, alerting
```

---

## 14. Bottlenecks Table

| Issue | Impact | Fix |
|---|---|---|
| Slow convergence | Downtime 3-5 min | Local failover |
| BGP hijack | Traffic redirection | RPKI signing |
| Route flapping | CPU spike | Dampening |
| Too many routes | Memory overload | Aggregation |

---

## 15. Monitoring

### Key Metrics

```
✓ Route stability (flap rate)
✓ Convergence time (failover)
✓ BGP sessions (up/down)
✓ Route count (should be stable)
✓ AS-path length (suspicious if long)
```

---

## 16. Optimizations

### 1. Route Aggregation

```
Announce: 192.0.0.0/16 (covers 192.0.0.0 - 192.0.255.255)
Instead of: 192.0.0.0/24, 192.0.1.0/24, ... 192.0.255.0/24
(256 announcements → 1)

Benefit: smaller routing tables, less memory
```

### 2. AS-path Prepending

```
Make route less attractive:
  Normal: AS1 → AS2 → AS3
  Prepended: AS1 → AS1 → AS1 → AS2 → AS3
  
Result: longer path, lower priority
  Used: traffic engineering (steer away)
```

---

## 17. Security

### 1. RPKI (Resource Public Key Infrastructure)

```
Sign: route announcements cryptographically
Verify: on reception
  Valid: trusted origin
  Invalid: drop (prevent hijack)
```

### 2. BGP Monitoring

```
Anomaly detection:
  Unusual AS-path?
  Unexpected withdrawal?
  
Alert: on suspicious patterns
```

---

## 18. Tradeoffs Table

| Aspect | BGP | IGP (OSPF) |
|---|---|---|
| Scope | Global (inter-AS) | Local (intra-AS) |
| Scalability | 65K ASes | 500-1000 routers |
| Convergence | 3-5 min | <1 min |
| Optimality | Good (policy) | Optimal (shortest) |

---

## 19. Alternatives

### SD-WAN

```
Software-defined: traffic engineered per-flow
More control: bypass BGP policy
Cost: expensive, vendor lock-in
```

---

## 20. When NOT to Use

### Don't Use BGP When:

1. **Single ISP**
   - Simple routing (default route)

---

## 21. Interview Questions

1. **Design global routing for 100 ASes**
   - BGP strategy?
   - Failover?
   - Security?

2. **BGP hijack attack**
   - Prevent?
   - Detect?

3. **Route flapping**
   - Cause?
   - Impact?
   - Solution?

---

## 22. Common Mistakes

1. **No RPKI validation**
   - Vulnerable to hijack
   - Add: RPKI checks

2. **Slow failover (BGP)**
   - Use: local failover (seconds)
   - BGP: backup (minutes)

3. **No aggregation**
   - Route explosion
   - Group ranges intelligently

---

## 23. Debugging Guide

### Step 1: Check BGP Sessions

```
show bgp summary
Shows: neighbor status, routes learned/sent
```

### Step 2: Check Routes

```
show ip bgp 192.0.2.0/24
Shows: AS-path, next-hop, local-pref
```

---

## 24. Code Examples

### Go: BGP Route Selection

```go
type Route struct {
    Prefix        string
    ASPath        []int
    LocalPref     int
    MED           int
}

func selectBestRoute(routes []Route) Route {
    // 1. Highest local preference
    sort.Slice(routes, func(i, j int) bool {
        if routes[i].LocalPref != routes[j].LocalPref {
            return routes[i].LocalPref > routes[j].LocalPref
        }
        // 2. Shortest AS-path
        if len(routes[i].ASPath) != len(routes[j].ASPath) {
            return len(routes[i].ASPath) < len(routes[j].ASPath)
        }
        // 3. Lowest MED
        return routes[i].MED < routes[j].MED
    })
    return routes[0]
}
```

---

## 25. Visual Diagrams

### BGP Convergence After Link Failure

```
t=0:        Link fails
t=0-5s:     Router detects
t=5-25s:    Announcement propagates
t=25-180s:  Network converges
t=180s:     New routes active

Slowness: multiple propagation hops
```

---

## 26. Simulation Ideas

1. **Route Flapping Impact**
   - Vary: flap rate
   - Show: CPU, convergence time

---

## 27. Case Studies

### AT&T BGP Leak (2010)
Result: entire YouTube unreachable for hours (AT&T announced Google's range)

---

## 28. Related Topics

- **Network Resilience**
- **Traffic Engineering**

---

## 29. Advanced Topics

### BGP Communities

```
Tag: routes for policy handling
Community: "backup" (lower priority)
Community: "customer-only" (restricted)
  
Route: policy-driven forwarding
```

---

## 30. Production Checklist

- [ ] RPKI validation enabled
- [ ] BGP session monitoring (up/down)
- [ ] Route aggregation configured
- [ ] Prepending for traffic engineering
- [ ] Dampening for flapping
- [ ] Local failover (faster than BGP)
- [ ] Monitoring: convergence time
- [ ] Anomaly detection (unusual routes)
- [ ] Regular audits (unauthorized routes)
- [ ] Documentation (peering agreements)

---

*Last Updated: 2026-05-28*
