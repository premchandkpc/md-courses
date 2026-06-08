---
title: Network Security Deep Dive - L5 Networking
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# Network Security Deep Dive - L5 Networking

> **[🎨 View Interactive Diagram](network-security-architecture.html)** | [← Back to Index](../../systems-index.html)

*"How do we protect networks from attacks? How filter malicious traffic?"*

---

## 1. Problem Statement

**Core Question:** How defend network against unauthorized access? How mitigate attacks?

Threats:
- DDoS: flood with traffic (unavoidable in network)
- Intrusion: hack into systems
- Eavesdropping: sniff unencrypted data
- Spoofing: fake source IP

Need: perimeter defense, encryption, rate limiting

---

## 2. Real World Analogy

**Airport Security:**

No security:
- Anyone enters, anyone leaves
- Terrorists board planes
- Chaos

Security:
- Check: passport (authentication)
- Scan: luggage (intrusion detection)
- Monitor: suspicious behavior (anomaly detection)
- Restrict: certain items (rate limiting)

Result: safer, but not perfect (tradeoff with speed)

---

## 3. Why Problem Exists

### Attack Scale

```
DDoS attack: 1 Tbps traffic
Origin server: handles 1 Gbps
Ratio: 1000x overload

Can't filter at origin (already flooded)
Must filter at network edge (ISP level)
```

### Encryption Necessity

```
Send: password over network
Attacker: sniffs (plaintext)
User: compromised

Encrypt: password → ciphertext
Sniff: meaningless
Result: confidentiality

HTTPS: standard for all web
```

---

## 4. Naive Approach

**"Block obvious attacks"**

Problems:
- Attacks: constantly evolving
- Signatures: outdated quickly
- False positives: block legitimate traffic
- Computationally expensive

---

## 5. Why Naive Fails

### Signature Evasion

```
Attack: SYN flood
Signature: block SYN packets
Attacker: morphs (use TCP fragments)
Bypass: detection

New attack emerges: old signatures useless
```

### Traffic Explosion

```
Filter every packet: expensive
  1M packets/sec: filter each
  CPU: 100% (can't do deep inspection)
  
Must choose:
  Depth: inspect every bit (slow)
  Breadth: light inspection (fast)
```

---

## 6. Evolution / Progression

### Stage 1: Firewalls Only
- Allow/deny by IP/port
- Stateless (no connection awareness)

### Stage 2: Stateful Firewalls
- Track connections
- Allow responses only
- Simple protocol inspection

### Stage 3: Next-Gen Firewalls (NGFW)
- Deep packet inspection
- IDS/IPS (intrusion detection/prevention)
- Application-layer filtering

### Stage 4: Cloud-Native Security
- DDoS mitigation via ISP
- WAF (web application firewall)
- Zero-trust (never trust, always verify)

---

## 7. Production Architecture

```
[Internet]
    ↓ (attacks, spam)
[ISP DDoS Mitigation] (drop obvious attacks)
    ↓ (cleaner traffic)
[Perimeter Firewall]
    ├─ Stateful inspection
    ├─ Port filtering
    └─ Rate limiting
    ↓
[WAF (Web Application Firewall)]
    ├─ HTTP inspection
    ├─ SQL injection detection
    └─ Bot detection
    ↓
[Internal Network]
    ├─ Encrypted (TLS)
    ├─ Segmentation (zones)
    └─ Monitoring (logging)
```

---

## 8. Components

### DDoS Mitigation

```
Attack: 1 Tbps SYN flood
ISP upstream: detects surge
Strategy: scrubbing (filter attack traffic)
  - Anycast: traffic to scrubbing center
  - Filter: drop spoofed IPs
  - Rate limit: per-source
  - Result: clean traffic to origin (~1 Gbps instead of 1 Tbps)

Cost: $10-100K/month per ISP depending on scale
```

### WAF Rules

```
SQL injection: detect SQL patterns
  Pattern: "' OR '1'='1"
  Block: request
  Log: for investigation

XSS (cross-site scripting):
  Pattern: "<script>alert('xss')</script>"
  Block: request
  Sanitize: output

Geo-blocking:
  Country: not allowed
  Block: all traffic from country
```

### VPN / Encrypted Tunnels

```
Plaintext: user → ISP → destination
Attacker: sniffs (plaintext visible)

VPN: user → ISP (encrypted) → destination
Attacker: sniffs (encrypted, useless)

Trade: encryption cost (CPU) vs security
```

---

## 9. Internal Working

### Firewall Packet Flow

```
Packet arrives: check stateful connection table
  New (SYN): connection not tracked
    Rule: allow SSH from 10.0.0.0/8?
    Action: allow, track connection
    
  Established: connection in table
    Rule: exists, allowing
    Action: forward
    
  Invalid: unexpected state
    Rule: no matching rule
    Action: drop

Result: only expected traffic passes
```

### DDoS Detection

```
Normal traffic: 1M packets/sec
DDoS: 100M packets/sec (100x surge)

Detector: threshold exceeded
  Action: activate scrubbing
  
Scrubber: filter rules
  - Drop SYN from same source (>1K/sec)
  - Drop DNS to non-existent servers
  - Drop fragmented packets
  
Result: 99% attack filtered, 1% legit passthrough
```

---

## 10. Request Lifecycle

```
Attack scenario: SYN flood

t=0ms:      Attacker sends SYN packets (100K/sec)
t=0-10ms:   ISP edge: detects anomaly (surge)
t=10-20ms:  DDoS scrubber: activated
t=20-100ms: Scrubber: learns attack pattern
t=100-200ms: Scrubber: filters 99% of SYN packets
t=200ms+:   Origin server: receives clean traffic (~1K/sec)

Result: attack mitigated in 200ms
Legitimate users: delayed slightly, but accessible
```

---

## 11. Data Flow

### Intrusion Prevention

```
Request: POST /login (SQL injection attempt)
  Payload: "username=admin' OR '1'='1'"
  
WAF: inspect
  Rule: SQL injection pattern detected
  Action: drop, log IP
  Attacker: IP blocked for 1 hour
  
Next 100 attempts: from same IP
  Firewall: drop (IP in block list)
  
Result: attack prevented
```

---

## 12. Key Strategy

### 1. Defense in Depth

```
Layer 1: ISP DDoS mitigation (stop floods)
Layer 2: Firewall (allow/deny by rule)
Layer 3: WAF (inspect application layer)
Layer 4: Encryption (TLS, protect data)
Layer 5: Monitoring (detect anomalies)

Breach one layer: others defend
```

### 2. Rate Limiting

```
Per-user: max 10 requests/sec
Per-IP: max 100 requests/sec
Per-endpoint: max 1000 requests/sec

Attacker: rate limited (effective, not destructive)
Users: rate limit → retry (backoff)
```

### 3. Anomaly Detection

```
Baseline: normal traffic pattern (day, time)
Alert: deviation (2x surge → investigate)

Machine learning:
  Train: on normal traffic
  Detect: unusual patterns (new attack)
  Alert: before blacklist updated
```

---

## 13. Failure Scenarios

### Scenario 1: Firewall Bypass

```
Attacker: uses sophisticated evasion
  Fragment packets: bypass inspection
  Tunnel: in DNS (exfiltrate data)
  
Result: malware enters network

Mitigation:
  Egress filtering: inspect outbound
  Segment: internal zones
  Endpoint security: detect on host
```

### Scenario 2: DDoS Overwhelm

```
Attack: 100 Tbps (exceeds ISP capacity)
  ISP: can scrub 50 Tbps max
  Result: service unavailable

Mitigation:
  Geographically distributed: CDN
  Multiple uplinks: from different ISPs
  Fallback: degraded service (500 errors)
```

### Scenario 3: Zero-Day

```
New vulnerability: no patch
Attacker: exploits
  Signature: not in WAF
  Result: breach

Mitigation:
  Principle of least privilege: limit impact
  Monitoring: detect anomalous behavior
  Incident response: contain, eradicate
```

---

## 14. Bottlenecks Table

| Issue | Impact | Fix |
|---|---|---|
| Firewall CPU maxed | Packet drop | More capacity |
| False positives high | Legit users blocked | Tune rules |
| Slow anomaly detection | Breach undetected | Automation |
| No egress filtering | Data exfiltration | Monitor outbound |

---

## 15. Monitoring

### Key Metrics

```
✓ Attack traffic detected (DDoS)
✓ Firewall rule hits (unusual patterns)
✓ WAF rule hits (injection attempts)
✓ Latency (security should not slow)
✓ False positive rate (tune balance)
✓ Response time (alert to action)
```

---

## 16. Optimizations

### 1. Stateless Filtering

```
Check: only headers (fast)
Drop: obvious bad (spoofed IPs)
Result: quick triage (99% legitimate pass)

Trade: some attacks bypass
```

### 2. Hardware Acceleration

```
Crypto operations: expensive (CPU-bound)
Hardware: dedicated crypto chips (ASIC)
Result: TLS handshake 10x faster
```

---

## 17. Security

### 1. DNSSEC

```
Sign: DNS responses cryptographically
Verify: on client side
  Valid: trusted source
  Invalid: forged (block)

Prevent: DNS hijack attacks
```

### 2. BGP Hijack Prevention

```
RPKI: sign route announcements
Validate: on edge router
  Valid: accept
  Invalid: reject

Prevent: traffic redirection attacks
```

---

## 18. Tradeoffs Table

| Feature | Protection | Latency | Cost |
|---|---|---|---|
| ISP DDoS | Massive | Low | High |
| Firewall | Good | Low | Low |
| WAF | Application-layer | Medium | Medium |
| VPN | Encryption | High | Medium |

---

## 19. Alternatives

### Cloudflare (DDoS as Service)

```
Outsource: DDoS mitigation
Benefits: cheaper, larger scale
Cost: vendor lock-in, privacy
```

---

## 20. When NOT to Use

### Don't Over-Engineer When:

1. **Low-risk target**
   - Basic firewall sufficient
   - Cost-benefit poor

---

## 21. Interview Questions

1. **Design DDoS defense for e-commerce**
   - ISP layer?
   - WAF?
   - Monitoring?

2. **SQL injection attack**
   - Prevent?
   - Detect?
   - Contain?

3. **Network segmentation**
   - How design?
   - Benefits?

---

## 22. Common Mistakes

1. **No egress filtering**
   - Malware exfiltrates data
   - Add: inspect outbound

2. **Too many false positives**
   - Legitimate users blocked
   - Tune: thresholds

3. **No monitoring**
   - Breach undetected
   - Add: logging, alerts

4. **Single ISP**
   - DDoS attack = down
   - Add: multiple uplinks

---

## 23. Debugging Guide

### Step 1: Check Firewall Logs

```
tail -f /var/log/firewall
Shows: blocked packets, rule matches
```

### Step 2: Check DDoS Status

```
DDoS scrubber: active?
Attack traffic: 99% blocked?
Latency: acceptable?
```

---

## 24. Code Examples

### Go: Rate Limiter

```go
type RateLimiter struct {
    tokens  int
    maxRate int
    mu      sync.Mutex
    ticker  *time.Ticker
}

func (r *RateLimiter) Allow() bool {
    r.mu.Lock()
    defer r.mu.Unlock()
    
    if r.tokens > 0 {
        r.tokens--
        return true
    }
    return false
}

func (r *RateLimiter) refill() {
    ticker := time.NewTicker(time.Second)
    for range ticker.C {
        r.mu.Lock()
        if r.tokens < r.maxRate {
            r.tokens++
        }
        r.mu.Unlock()
    }
}
```

---

## 25. Visual Diagrams

### Network Security Layers

```
Attacker → ISP DDoS → Firewall → WAF → Application
           (filter)   (IP/port)  (HTTP)
```

---

## 26. Simulation Ideas

1. **DDoS Attack Response**
   - Vary: attack size
   - Show: mitigation time

---

## 27. Case Studies

### GitHub DDoS (2015): 620 Gbps
Result: cloudflare mitigated, service continued

---

## 28. Related Topics

- **Cryptography & Encryption**
- **Authentication & Authorization**

---

## 29. Advanced Topics

### Zero-Trust Security

```
Principle: never trust, always verify
  Even internal traffic: authenticate
  Every request: check permissions
  
Trade: more overhead, but safer
```

---

## 30. Production Checklist

- [ ] ISP DDoS mitigation contracted
- [ ] Stateful firewall configured
- [ ] WAF rules updated regularly
- [ ] TLS/HTTPS enforced everywhere
- [ ] VPN for sensitive data
- [ ] Rate limiting per user/IP
- [ ] Anomaly detection enabled
- [ ] Egress filtering (data loss prevention)
- [ ] Security monitoring 24/7
- [ ] Incident response plan

---

*Last Updated: 2026-05-28*
