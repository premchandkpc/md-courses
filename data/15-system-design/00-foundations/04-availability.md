# Availability Deep Dive - L5 Fundamentals

> **[🎨 View Interactive Diagram](availability-architecture.html)** | [← Back to Index](../../systems-index.html)

*"99.9% availability sounds great. That's 43 minutes of downtime per month. What's the catch?"*

---

## 1. Problem Statement

**Core Question:** How much downtime can you actually tolerate?

System A: "We aim for 99.9% uptime"
System B: "We guarantee 99.99% uptime"

What's the difference? 
System A: 8.76 hours downtime/year
System B: 52.56 minutes downtime/year

How do you design differently?

---

## 2. Real World Analogy

**Restaurant Availability:**
- 99% available: Open every day, close 1 day per month (full day)
- 99.9% available: Close 2.4 hours per month (scattered outages)
- 99.99% available: Close 14 minutes per month
- 99.999% available: Close 86 seconds per month

At 99.999%, you need:
- Multiple backup ovens (if one fails, others cover)
- Backup generators (if power fails)
- Backup water (if supply fails)
- Trained replacement staff (if key people unavailable)

Cost? 10-100x of 99% system.

---

## 3. Why Problem Exists

### Sources of Downtime

**A. Hardware Failures**
- Server fails: 1-5 times per 1000 servers per year
- Drive fails: 2-5% failure rate per year
- NIC fails: 0.5% per year
- Power supply fails: 1-2% per year

Single server → expect failure ~once per 5 years
But at scale (1000 servers) → failure every single day

**B. Software Bugs**
- Deploy introduces bug
- Cascades to production
- Takes 30 minutes to detect and roll back
- Service unavailable during

**C. Network Issues**
- Fiber cut (BGP route failure)
- Switch misconfiguration
- DDoS attack
- Network congestion

**D. Human Error**
- Wrong deployment
- Wrong database migration
- Incorrect config
- Accidental deletion

**E. Dependency Failures**
- Third-party API down
- Database unavailable
- Load balancer broken

---

## 4. Naive Approach

**"Build a robust system"**

- Write careful code
- Test thoroughly
- Monitor closely

Problems:
- Doesn't handle hardware failures (code quality can't fix dead disk)
- Doesn't handle human error (deployment mistakes)
- Single point of failure (one bad thing breaks everything)

---

## 5. Why Naive Fails

### SPOF (Single Point of Failure)

```
Architecture:
  [Clients] → [Load Balancer] → [Database]

If load balancer fails:
  All traffic drops
  Availability: 0% (not 99%)

Probability: LB fails once every 5 years
  Annual availability: 99.99%
  But when it fails, ALL users affected (cascading impact)
```

### Cascading Failures

```
Service A depends on Service B

Service B goes down (maintenance, bug)
Service A can't process requests → queues build up
Clients timeout → retry → more load
Service A crashes from overload
Service C depends on A → now C fails too

Result: 3 services down from 1 initial failure
```

### Lack of Failover

```
Database primary fails
Application still tries to connect
Connection timeouts
Application hangs
Until operator manually fails over

Downtime: 30 minutes (detection + failover)
RTO (Recovery Time Objective): 30 minutes
RPO (Recovery Point Objective): some data loss
```

---

## 6. Evolution / Progression

### Stage 1: Single Instance (0% availability)
- One server, one database
- Failure = total outage
- Availability: dependent on hardware reliability (99%)

### Stage 2: Redundancy + Manual Failover (99% availability)
- Primary + standby database
- When primary fails, operator manually fails over to standby
- Downtime: 30 minutes (detection + manual process)

### Stage 3: Automatic Failover (99.9% availability)
- Primary + standby (replication)
- Automatic detection (heartbeat)
- Automatic failover (no human needed)
- Downtime: 2-5 minutes (detection + failover script)

### Stage 4: Multi-Region Redundancy (99.99% availability)
- Multiple data centers
- Automatic routing to healthy region
- No single point of failure
- Downtime: seconds (healthcheck + route change)

### Stage 5: Global Distributed (99.999% availability)
- Multiple independent systems
- Can lose entire data center
- Service continues
- Downtime: < 1 second (local failover)

---

## 7. Production Architecture

```
[Client Requests]
    │
    ├─→ [DNS (Route 53)] ← Multiple DNS servers
    │
    ├─→ [CDN / Edge] ← Global distribution
    │
    ├─→ [Load Balancer A] (Region 1)
    │   ├─ Health check: active
    │   ├─ If unhealthy: DNS reroutes
    │   │
    │   ├─→ [API Servers] (3 instances, running)
    │   │   ├─ Instance 1
    │   │   ├─ Instance 2
    │   │   └─ Instance 3 (can lose one, still works)
    │   │
    │   ├─→ [Database Primary] (Region 1)
    │   │   ├─ Replication to Standby (Region 2)
    │   │   ├─ Replication to Standby (Region 3)
    │   │   └─ Automatic failover (if primary unhealthy)
    │   │
    │   ├─→ [Redis Cache]
    │   │   ├─ Replication to backup instance
    │   │   └─ Automatic promotion on failure
    │   │
    │   └─→ [Distributed Queue]
    │       ├─ Replicated (Kafka multiple brokers)
    │       └─ Tolerates broker failure
    │
    ├─→ [Load Balancer B] (Region 2)
    │   └─ [API Servers, Database Standby, etc.]
    │
    └─→ [Load Balancer C] (Region 3)
        └─ [API Servers, Database Standby, etc.]
```

---

## 8. Components

### Health Checks
**Purpose:** Detect failures automatically

```
Liveness check: Is service running?
  curl http://server:8000/health
  Status: 200 → healthy, else → unhealthy

Readiness check: Is service ready for traffic?
  Check: database connection, cache accessible, queues available
  Status: 200 → ready, else → not ready

Frequency: every 5 seconds
Action on failure: remove from load balancer, trigger failover
```

### Replication
**Purpose:** Keep copy of data on standby

```
Primary DB (active):
  Writes: 100% of writes
  Reads: 50% of reads
  
Standby DB (replicas):
  Writes: 0% (async replication from primary)
  Reads: 50% of reads (eventual consistency)
  
On primary failure:
  Standby promoted to primary
  Failover time: 1-5 minutes (automatic)
  Data loss: 0 if fully replicated, else last few seconds
```

### Circuit Breaker
**Purpose:** Prevent cascading failures

```
Service A calls Service B

Circuit states:
  CLOSED (normal): requests flow
  OPEN (service B broken): requests fail fast (don't wait)
  HALF_OPEN (testing): send limited requests to test recovery

Flow:
  [Service B fails]
  → After 5 failures → Circuit opens
  → Requests immediately fail (fast)
  → Application uses fallback
  → After 1 minute → try 1 request (HALF_OPEN)
  → If succeeds → close circuit (resume normal)
```

### Bulkhead Pattern
**Purpose:** Isolate failures

```
Single queue:
  Service A requests: 100 req/s
  Service B requests: 50 req/s
  Queue size: 100
  
If Service A slow:
  Queue fills with A requests
  Service B requests timeout (no queue space)
  Both fail

Bulkhead (separate queues):
  Service A queue: 80 size (80% of capacity)
  Service B queue: 20 size (20% of capacity)
  
If Service A slow:
  A queue fills, A requests rejected
  B queue available, B continues → doesn't cascade
```

---

## 9. Internal Working

### Failure Detection Timeline

```
t=0ms: Primary database becomes unhealthy (network partition)
  → Still accepting connections, but slow

t=100ms: First health check succeeds (was in flight before failure)
  → Still marked healthy

t=100-5000ms: Health checks start failing
  → Retry with exponential backoff

t=5000ms: Mark as unhealthy (after 5 consecutive failures)
  → Load balancer stops sending requests

t=5100-10000ms: Promote standby to primary
  → Reconfigure DNS/routing
  → Application reconnects

t=10000ms: System recovered, requests resume

Total downtime: 10 seconds
```

### Replication Lag

```
Write committed on primary: t=0ms
Write reaches replica: t=10ms (network delay)

If primary fails at t=5ms:
  Write not replicated yet
  Failover to replica
  Data loss: 5ms worth of transactions

RTO: Recovery Time Objective (30 minutes acceptable? 5 seconds?)
RPO: Recovery Point Objective (5ms data loss acceptable? 0?)

Trade: Tight RPO requires synchronous replication (slows writes)
```

---

## 10. Request Lifecycle

```
Normal path:
  [Client] → [DNS] → [Load Balancer] → [Healthy Server] → Response

Failure path:
  [Client] → [DNS] (primary region unhealthy)
            → [Health check fails]
            → [DNS reroutes to secondary region]
            → [Load Balancer B] → [Healthy Server] → Response

Perceived downtime: Network time (10-50ms to reroute)
Actual downtime: 0 (failover automatic)
```

---

## 11. Data Flow

### Replication at Scale

```
Primary DB: 10K writes/sec
Replication lag tolerance: 1 second
Replicas: 3 (distributed geographically)

Write replication flow:
  Primary writes to log: 1ms
  Primary applies: 2ms
  Send to Replica A: 20ms (network)
  Replica A applies: 1ms
  Ack to primary: 20ms
  Commit confirmed: ~44ms per write (async, acceptable)

During network split (Replica A isolated):
  Replica B, C get updates in real-time (20ms)
  Replica A lags (no network)
  If primary fails: failover to B or C (minimal data loss)
  Replica A resynchronizes when network heals
```

---

## 12. Key Strategy

### 1. Define Availability Target
```
Nines: 99%, 99.9%, 99.99%, 99.999%

Cost increases exponentially:
  99%:     $100K/year
  99.9%:   $200K/year (2x)
  99.99%:  $500K/year (5x)
  99.999%: $2M/year (20x)

Pick based on: business impact of downtime, user tolerance
```

### 2. Identify Single Points of Failure
```
Architecture:
  Load Balancer → Database
  
SPOF: Load Balancer
  If LB fails → entire system down
  
Fix: Active-Active LBs (both process traffic)
     or Automatic failover (DNS reroutes)
```

### 3. Replicate Everything Critical
```
Critical components:
  ✓ Database (replication, multiple replicas)
  ✓ Cache (failover, multiple instances)
  ✓ Load Balancer (active-active)
  ✓ DNS (multiple providers)
  
Non-critical: can have single instance (logs, monitoring, internal tools)
```

### 4. Automatic Detection & Failover
```
Automatic:
  Health checks run continuously
  On failure: automatic removal/failover
  Downtime: 2-5 seconds (detection + action)

Manual:
  Alert operator
  Operator investigates
  Operator initiates failover
  Downtime: 30+ minutes
```

### 5. Test Failure Scenarios
```
Regular chaos engineering:
  - Kill random servers (weekly)
  - Simulate network partition (quarterly)
  - Simulate datacenter failure (monthly)
  
Validate: system recovers automatically, no data loss
```

---

## 13. Failure Scenarios

### Scenario 1: Cascading Timeout
```
Service A calls Service B (timeout: 5s)
Service B calls Service C (timeout: 5s)

Service C becomes slow (GC pause, 10s)
Service B times out → retries
Retries stack up in queue
Service B becomes slow
Service A times out → retries
Cascading timeout propagates upstream

Result: entire system feels slow
```

**Fix:** Circuit breaker (fail fast), timeout propagation (fail immediately if upstream will timeout)

### Scenario 2: Data Corruption
```
Primary DB bugs out: corrupts table during migration
Replication copies corruption to standbys
Failover: switchover to standby (now also corrupted)

Entire system: corrupted data
Recovery: restore from backup (hours)

Data loss: all changes since last backup
```

**Fix:** 
- Backup to separate cloud provider (Glacier, independent replica)
- Point-in-time recovery (can roll back)
- Change data capture (CDC) with validation

### Scenario 3: Network Partition
```
Datacenter A (primary): 5 servers
Datacenter B (standby): 5 servers

Network between A & B fails (fiber cut)
A still has quorum (5 servers, 3 needed)
B loses quorum (5 servers, but can't reach A, network says A failed)

Scenario 1: B assumes A is dead, promotes self to primary
  → Both A and B think they're primary (split brain)
  → Conflicting writes, data corruption

Scenario 2: B detects network partition, stops processing
  → System continues in A (preferred)
  → B serves no traffic (correct)
```

**Fix:** Consensus algorithm (Raft, Paxos) that prevents split-brain

---

## 14. Bottlenecks Table

| Bottleneck | Availability Impact | Symptoms | Quick Fix |
|---|---|---|---|
| Single LB | 99% (LB fails = down) | All traffic drops | Active-active LBs |
| Single DB | 99.9% (downtime on failure) | Data unavailable | Replication, standby |
| No health checks | 99% (slow to detect) | Users timeout, manual recovery | Automated health checks |
| No circuit breaker | Cascading failures | Chain reaction of timeouts | Add circuit breakers |
| Weak replication | 99.9% + data loss | Lose recent writes on failover | Synchronous replication |
| No backup | Data loss risk | Total loss if corruption | Distributed backups |
| Manual failover | 30+ minutes downtime | Operator delay | Automatic failover |
| Cascading timeouts | Chain failures | System-wide slowness | Deadline propagation, fast-fail |

---

## 15. Monitoring

### Key Metrics

```
Uptime tracking:
  ✓ Overall uptime: 99.99%
  ✓ Uptime per service: API 99.99%, DB 99.999%
  ✓ Downtime incidents: count, duration, root cause

Health indicators:
  ✓ Number of healthy instances (target: >2 per service)
  ✓ Replication lag (target: <100ms)
  ✓ Failover success rate (target: 100%)
  ✓ Error rate (target: <0.1%)
```

### Dashboards

```
Real-time status:
  Service A: ✓ healthy (99.99% uptime)
             ✓ 3 instances running (capacity for 1 failure)
             ✓ Replication lag: 50ms
             
  Service B: ✗ WARNING (99.8% uptime)
             ✓ 2 instances running (one unhealthy)
             ⚠ Replication lag: 500ms (high)
             
  Database:  ✓ healthy (99.999% uptime)
             ✓ Primary + 2 standbys
             ✓ Backup: 1 hour old
```

### Red Flags

- Replication lag growing unbounded (standbys falling behind)
- Only 1 healthy instance (can't tolerate failure)
- No recent backup (data loss risk)
- Failover disabled (manual recovery only)
- High error rate (system degraded)

---

## 16. Optimizations

### 1. Active-Active Configuration
```
Passive (standby):
  Primary handles 100% traffic
  Standby idle (wasted capacity)
  On failure: cold start (slow)

Active-Active:
  Primary handles 50% traffic
  Standby handles 50% traffic (live)
  On failure: other continues at 100% (degraded but available)
```

### 2. Distributed Consensus (Raft)
```
No leader elected (single point of failure)
vs.
Leader elected via consensus (multiple servers vote)
  → Any server can take over
  → Prevents split-brain
  → Stronger availability guarantee
```

### 3. Synchronous Replication
```
Asynchronous:
  Write committed immediately on primary
  Async sent to replicas
  Fast (high throughput), but data loss risk on primary failure

Synchronous:
  Write must be replicated to majority before commit
  Slow (lower throughput), but zero data loss

Trade: choose based on RPO requirements
```

### 4. Bulkhead Pattern
```
Without: shared resource pool
  Heavy workload fills pool
  Light workload starved

With: separate pools per workload
  Heavy workload isolated
  Light workload continues
```

---

## 17. Security

### 1. DDoS Impact on Availability
```
Attack: 1M requests per second
System capacity: 100K req/s

Without mitigation:
  Drop 90% of traffic
  System overloaded
  Legitimate users: 10% success rate

Mitigation:
  Rate limiting per IP: 100 req/s
  Drop obvious bot traffic: 50% filtered
  Early filtering at edge: 30% filtered
  
Result: keep system responsive for legitimate users
```

### 2. Blast Radius Limitation
```
Vulnerability in payment service:
  If all traffic flows through one service
  → Entire system compromised

With isolation:
  Payment service isolated (separate auth, separate DB)
  Even if compromised → can't reach other services
  → Loss contained
```

---

## 18. Tradeoffs Table

| Approach | Availability Gain | Cost | Complexity |
|---|---|---|---|
| Replication | 99% → 99.9% | 2x infrastructure | Medium |
| 3-way replication | 99.9% → 99.99% | 3x infrastructure | High |
| Multi-region | 99.99% → 99.999% | 3x+ infrastructure | Very High |
| Synchronous replication | Zero data loss | Write latency +50% | Medium |
| Automated failover | 30min → 5sec recovery | Operational complexity | High |
| Active-active | Better resource utilization | Complex consistency | Very High |
| Circuit breakers | Prevent cascades | Additional latency (fallbacks) | Medium |

---

## 19. Alternatives

### Strong Consistency vs High Availability

CAP Theorem: Can't have all 3 (Consistency, Availability, Partition tolerance)
- Choose: Consistency + Tolerance (CP) → sacrifices Availability
- Choose: Availability + Tolerance (AP) → sacrifices Consistency

```
CP system (strong consistency):
  - Majority partition continues
  - Minority partition stops (prevents split-brain)
  - Availability: 99.9% (down during partition)

AP system (high availability):
  - Both partitions continue (diverge)
  - Requires merge/reconciliation
  - Availability: 99.999% (always available)
  - Trade: eventual consistency
```

---

## 20. When NOT to Use

### Don't Optimize for 99.999% When:

1. **Business doesn't justify cost**
   - 99.99% costs 20x more than 99%
   - Downtime impact not worth it

2. **Operational complexity too high**
   - 99.999% requires expert ops team
   - Cost of maintenance > cost of downtime

3. **Dependencies aren't as available**
   - Your system 99.999% reliable
   - But dependent on external API that's 99%
   - Overall limited by weakest link

4. **Don't have critical data needs**
   - Blog can tolerate 1 hour downtime
   - Don't need distributed backup
   - Don't need multi-region

---

## 21. Interview Questions

1. **Design system with 99.99% availability**
   - What would you replicate?
   - How handle failures?
   - What's the critical path?

2. **System A: 99.99% for $500K/year. System B: 99.999% for $2M/year. How decide?**
   - What's business impact of downtime?
   - What's user tolerance?
   - What are alternatives?

3. **Your replicated database has 1-second replication lag**
   - Is it acceptable?
   - What happens if primary fails?
   - How minimize RPO?

4. **Compare active-standby vs active-active**
   - Pros/cons of each?
   - When use each?
   - Data consistency implications?

5. **How prevent cascading failure?**
   - Design pattern?
   - Monitoring?
   - Testing approach?

---

## 22. Common Mistakes

1. **SPOFs overlooked**
   - Design: "we have replication"
   - Reality: only one load balancer (SPOF)
   - Every component must be redundant

2. **Replication lag ignored**
   - Assume replication instant
   - Primary fails, lose recent writes
   - RPO: 0 requires synchronous replication (slow)

3. **Manual failover too slow**
   - 30+ minute recovery
   - Cost of downtime: 10x faster failover
   - Automate failover process

4. **Testing failures never**
   - "Replication works in dev"
   - "Failover tested in staging"
   - Production is different (real timing, real data)
   - Chaos engineering: kill servers in production (carefully)

5. **Monitoring too late**
   - Health checks every 5 minutes
   - Failure not detected until 5+ min
   - Check every second, react immediately

6. **Data corruption unchecked**
   - No backup validation
   - Corruption propagates to all replicas
   - Restore from week-old backup (data loss)
   - Validate backups regularly

---

## 23. Debugging Guide

### Step 1: Detect Failure
```
Alert: Service A availability dropped to 95%

Current state:
  Health check: 5 instances, 1 failing
  Error rate: 20% (vs normal 0.1%)
  Latency: 5s (vs normal 100ms)
  
Investigation: Why is instance failing?
```

### Step 2: Understand Impact
```
Failed instance:
  Traffic: 20% of requests (from load balancer)
  Other instances: each took 20% additional (now 70% load)
  Queue: filled up (requests waited 4s)
  P99 latency: spike (7s vs 1s normal)
  
Data: if instance handled writes, any data loss?
  Write replication: was it replicated before failure?
  Check replication lag at time of failure
```

### Step 3: Failover
```
Option 1: Restart instance
  Time: 2 minutes
  Risk: if bug, will fail again

Option 2: Remove from rotation, investigate
  Time: immediate
  Risk: operating at 80% capacity

Choose: Option 2 (safety over capacity)
```

### Step 4: Root Cause Analysis
```
Instance logs:
  t=10:00: Memory usage: 2GB (normal)
  t=10:15: Memory usage: 3GB (increasing)
  t=10:25: Memory usage: 4GB (out of memory)
  t=10:26: Process killed (OOM killer)
  
Root cause: Memory leak in recent deployment
  → Revert deployment
  → Reduce memory footprint
  → Monitor memory usage
```

---

## 24. Code Examples

### Go: Health Check Endpoint
```go
func healthCheck(w http.ResponseWriter, r *http.Request) {
    // Check dependencies
    var checks struct {
        Status string `json:"status"`
        Checks struct {
            Database bool `json:"database"`
            Cache    bool `json:"cache"`
            Queue    bool `json:"queue"`
        } `json:"checks"`
    }
    
    // Database check
    ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
    defer cancel()
    err := db.PingContext(ctx)
    checks.Checks.Database = (err == nil)
    
    // Cache check
    err = cache.Ping()
    checks.Checks.Cache = (err == nil)
    
    // Queue check
    err = queue.Ping()
    checks.Checks.Queue = (err == nil)
    
    // Overall status
    if checks.Checks.Database && checks.Checks.Cache && checks.Checks.Queue {
        checks.Status = "healthy"
        w.WriteHeader(http.StatusOK)
    } else {
        checks.Status = "unhealthy"
        w.WriteHeader(http.StatusServiceUnavailable)
    }
    
    json.NewEncoder(w).Encode(checks)
}

// Usage: health check every 5 seconds
// If status != 200 for 3 consecutive checks, remove from LB
```

### Go: Circuit Breaker
```go
type CircuitBreaker struct {
    state       string // "closed", "open", "half-open"
    failures    int
    lastFailure time.Time
    threshold   int
    timeout     time.Duration
    mu          sync.RWMutex
}

func (cb *CircuitBreaker) Call(fn func() error) error {
    cb.mu.Lock()
    defer cb.mu.Unlock()
    
    // If open, check if timeout elapsed
    if cb.state == "open" {
        if time.Since(cb.lastFailure) > cb.timeout {
            cb.state = "half-open"
            cb.failures = 0
        } else {
            return fmt.Errorf("circuit breaker open")
        }
    }
    
    // Try the call
    err := fn()
    
    if err != nil {
        cb.failures++
        cb.lastFailure = time.Now()
        
        if cb.failures >= cb.threshold {
            cb.state = "open"
        }
        
        return err
    }
    
    // Success: reset
    if cb.state == "half-open" {
        cb.state = "closed"
    }
    cb.failures = 0
    return nil
}

// Usage:
cb := &CircuitBreaker{
    state:     "closed",
    threshold: 5,        // open after 5 failures
    timeout:   1 * time.Minute,  // try again after 1 min
}

err := cb.Call(func() error {
    return callSlowService()
})
if err != nil {
    // Service unavailable, use fallback
    return fallback()
}
```

### Go: Replication Lag Monitor
```go
func monitorReplicationLag(primary *sql.DB, replica *sql.DB) {
    ticker := time.NewTicker(5 * time.Second)
    defer ticker.Stop()
    
    for range ticker.C {
        // Get primary's binlog position
        var primaryPos string
        primary.QueryRow("SHOW MASTER STATUS").Scan(&primaryPos)
        
        // Get replica's replicated position
        var replicaPos string
        replica.QueryRow("SHOW SLAVE STATUS").Scan(&replicaPos)
        
        // Compare (simplified)
        if primaryPos != replicaPos {
            lag := calculateLag(primaryPos, replicaPos)
            
            if lag > 5*time.Second {
                log.Printf("HIGH REPLICATION LAG: %v", lag)
                alert("replication_lag_high", lag)
            }
        }
    }
}

// Alert monitoring:
// - lag > 1s: warning
// - lag > 5s: critical
// - lag > 60s: trigger manual failover alert
```

---

## 25. Visual Diagrams

### Availability vs Downtime
```
Availability   Annual Downtime   Monthly Downtime   MTTR Tolerance
99%            3.65 days         7.2 hours          1 day
99.9%          8.76 hours        43 minutes         30 minutes
99.99%         52.56 minutes     2.6 minutes        5 minutes
99.999%        5.26 minutes      15 seconds         <1 minute
```

### Failure Recovery Timeline
```
Time (sec)   Event
0            Primary database failure
1-5          Health checks fail (exponential backoff)
5            Mark as unhealthy, remove from LB
5-10         Promote standby to primary
10-15        Application reconnects
15           System recovered

↑ Automated: <15 seconds
↑ Without automation: >30 minutes
```

### Replication Consistency
```
Primary DB                    Replica DB
Write: 100                    (async replication)
Write: 101                    ← lag: 50ms
Write: 102                    Write: 100 ← behind
                              Write: 101

If primary fails now:
  → Failover to replica
  → Loses write 102 (not replicated)
  → RPO: 50ms (acceptable?)
```

---

## 26. Simulation Ideas

1. **MTTR Calculator**
   - Input: detection time, failover time
   - Output: total downtime
   - Show: automation value

2. **Availability Calculator**
   - Input: number of nines desired
   - Output: downtime budget, MTTR requirements
   - Show: component dependencies

3. **Cascade Failure Simulator**
   - Service A → Service B → Service C
   - Introduce failure to A
   - Show: without circuit breakers, cascades
   - Show: with circuit breakers, contained

4. **Replication Lag Simulator**
   - Network latency: variable
   - Data change rate: variable
   - Show: impact on RPO

5. **Failover Time Simulator**
   - Detection algorithm: health check frequency
   - Failover process: automated vs manual
   - Show: time to recovery

---

## 27. Case Studies

### Case 1: AWS DynamoDB (99.99% available)
**Problem:** Single region DynamoDB unavailable (30 minutes)

**Root Cause:** Network partition within region, not enough replicas to maintain quorum

**Solution:**
1. Multi-region replication (global tables)
2. Automatic failover to another region
3. Improved quorum algorithm (consensus-based)

**Result:** 99.999% availability (down from 99.99%)

### Case 2: Facebook Global Outage (2019)
**Problem:** Entire platform down (12 hours)

**Root Cause:** BGP routing configuration error. Traffic routed incorrectly. Cascaded to entire infrastructure.

**Solution:**
1. Independent DNS providers (reduce routing dependency)
2. Out-of-band network for recovery (separate from main)
3. Faster rollback process (automated)

**Result:** Prevented recurrence, improved recovery time

### Case 3: Stripe Payment Processing
**Problem:** Payments failing during surge (P99 latency 10s, should be <100ms)

**Root Cause:** Database connection pool exhausted. Cascading queue delays.

**Solution:**
1. Connection pooling improvements (PgBouncer)
2. Request shedding (fail fast if queue too deep)
3. Multi-region redundancy (automatic failover)

**Result:** 99.999% availability, <100ms latency maintained during peak

---

## 28. Related Topics

- **MTTR/MTTF:** Mean time to repair/failure
- **SLI/SLO/SLA:** Service level indicators/objectives/agreements
- **RTO/RPO:** Recovery time/point objectives
- **CAP Theorem:** Consistency-Availability-Partition tradeoff
- **Fault Tolerance:** System design patterns

---

## 29. Advanced Topics

### Byzantine Fault Tolerance
```
Standard quorum (Raft): tolerates F failures with 2F+1 servers
  → F can be crashed servers
  → Assumes: servers don't lie (Byzantine honest)

Byzantine: servers can be compromised (lie, corrupt data)
  → Tolerates F failures with 3F+1 servers (PBFT)
  → Validator consensus: must agree on transactions
  → Used: blockchain (Bitcoin, Ethereum)
```

### Hot-Standby vs Cold-Standby
```
Hot-standby:
  - Actively processes traffic (load balanced)
  - On failure: other takes over (no capacity loss)
  - Cost: 2x infrastructure always

Cold-standby:
  - Idle, no traffic
  - On failure: cold start (boot, load data)
  - Cost: 1.5x infrastructure + startup delay
```

### Leaderless Replication
```
Leader-based (Raft, MySQL):
  - One leader, multiple followers
  - Writes go to leader
  - Failure: elect new leader

Leaderless (Cassandra, DynamoDB):
  - All nodes equal
  - Write to any node
  - Nodes replicate to all others
  - Failure: any node can serve reads/writes
  - Trade: eventual consistency, conflict resolution
```

---

## 30. Production Checklist

- [ ] Define availability target (99%? 99.9%? 99.99%?)
- [ ] Calculate downtime budget (hours/year)
- [ ] Map all components (identify SPOFs)
- [ ] Add redundancy to all critical paths
- [ ] Implement health checks (every 1-5 seconds)
- [ ] Test failover (automated, <5 min RTO)
- [ ] Set replication strategy (RPO tolerance?)
- [ ] Implement circuit breakers (prevent cascades)
- [ ] Set timeout budgets (deadline propagation)
- [ ] Enable distributed tracing (identify failures)
- [ ] Set up alerting (detect issues early)
- [ ] Plan for multi-region (if 99.99%+ required)
- [ ] Implement automated backups (independent location)
- [ ] Test disaster recovery (quarterly, full outage sim)
- [ ] Document runbooks (ops procedures)
- [ ] Chaos engineering (weekly failure simulation)
- [ ] Monitor replication lag (alert if > threshold)
- [ ] Track incident metrics (MTTR, frequency)
- [ ] Review architecture (quarterly, identify weaknesses)
- [ ] Load test failure scenarios (before launch)

---

*Last Updated: 2026-05-28*

<!-- html-live -->
<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>
    .cascade-title {color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px;letter-spacing:1px}
    .cascade-stages {display:flex;flex-direction:column;gap:12px;margin-bottom:16px}
    .cascade-stage {display:flex;align-items:center;gap:12px}
    .cascade-label {color:#e3eaf0;font-family:monospace;font-size:12px;min-width:120px}
    .cascade-indicator {width:24px;height:24px;border-radius:4px;background:#34d399;border:2px solid #22c55e;transition:all 0.3s}
    .cascade-indicator.failing {background:#ef4444;border-color:#dc2626;box-shadow:0 0 12px #ef4444;animation:cascade-fail 0.6s ease-out}
    @keyframes cascade-fail {0%{transform:scale(1);opacity:1}100%{transform:scale(1.2);opacity:0.8}}
    .cascade-controls {display:flex;gap:8px;flex-wrap:wrap}
    .cascade-button {padding:8px 16px;border:1px solid #00d4ff;background:#1e3a5f;color:#00d4ff;border-radius:4px;cursor:pointer;font-family:monospace;font-size:12px;transition:all 0.2s}
    .cascade-button:hover {background:#2a5a8f;box-shadow:0 0 8px #00d4ff}
  </style>
  <div class="cascade-title">Outage Propagation Cascade</div>
  <div class="cascade-stages" id="cascade-stages">
    <div class="cascade-stage"><span class="cascade-label">Primary DB</span><div class="cascade-indicator" data-stage="stage0"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Connection Pool</span><div class="cascade-indicator" data-stage="stage1"></div></div>
    <div class="cascade-stage"><span class="cascade-label">API Server</span><div class="cascade-indicator" data-stage="stage2"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Load Balancer</span><div class="cascade-indicator" data-stage="stage3"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Client Errors</span><div class="cascade-indicator" data-stage="stage4"></div></div>
  </div>
  <div class="cascade-controls">
    <button class="cascade-button" onclick="startCascade()">Trigger Outage</button>
    <button class="cascade-button" onclick="resetCascade()">Recover</button>
  </div>
  <script>
    function startCascade() {const stages = document.querySelectorAll('[data-stage]'); let delay = 0; stages.forEach((stage) => {setTimeout(() => {stage.classList.add('failing');}, delay); delay += 300;});}
    function resetCascade() {document.querySelectorAll('[data-stage]').forEach((stage) => {stage.classList.remove('failing');});}
  </script>
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
    .metric-critical {color:#ef4444}
  </style>
  <div class="obs-title">Availability & Reliability Metrics</div>
  <div class="obs-grid">
    <div class="obs-card">
      <div class="obs-label">Uptime</div>
      <div class="obs-value metric-healthy">99.99</div>
      <div class="obs-unit">%</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">MTTR</div>
      <div class="obs-value metric-healthy">12</div>
      <div class="obs-unit">min</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Incidents/Mo</div>
      <div class="obs-value metric-warning">2</div>
      <div class="obs-unit">incidents</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">RTO Target</div>
      <div class="obs-value metric-healthy">5</div>
      <div class="obs-unit">min</div>
    </div>
  </div>
</div>
