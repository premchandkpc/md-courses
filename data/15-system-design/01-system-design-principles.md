# 🏛️ System Design Principles — Complete Deep Dive



```mermaid
graph LR
    A["Input<br/>Layer"] --> B["Hidden<br/>Layers"]
    B --> C["Hidden<br/>Layers"]
    C --> D["Output<br/>Layer"]
    B --> E["Activation<br/>Functions"]
    E --> B
    style A fill:#4a8bc2
    style B fill:#2d5a7b
    style C fill:#2d5a7b
    style D fill:#c73e1d
```

## 📋 Table of Contents
- [Scalability](#scalability)
- [Availability](#availability)
- [Performance](#performance)
- [Reliability](#reliability)
- [Consistency Models](#consistency-models)
- [Caching Strategies](#caching-strategies)
- [Database Patterns](#database-patterns)
- [Simplest Mental Model](#simplest-mental-model)

---

## Scalability

### Vertical vs Horizontal

```text
Vertical Scaling (Scale Up):     Horizontal Scaling (Scale Out):
+---------------------+          +---------------------+
|  Big Server         |          |  Server A | Server B|
|  CPU: 128 cores     |          |  (small)  | (small) |
|  RAM: 2TB           |          +----------+----------+
|  Disk: 100TB SSD    |                 |        |
+---------------------+          +-------+-+  +-+-------+
                                 |  Load Balancer |       |
  Limits: single machine ceiling +----------------+       |
  Cost: exponential $$$/perf             |                |
  SPOF: yes                              v                |
                                     [Users]             ...

  Limits: theoretically infinite, but adds complexity
  Cost: linear $/perf (usually)
  SPOF: no (with proper replication)
```

### Stateless Design for Horizontal Scaling

```python
# BAD: Stateful server — session stuck to this process
class BadSession:
    def __init__(self):
        self.sessions = {}  # local dict

    def handle_request(self, user_id, data):
        session = self.sessions.get(user_id)
        # ... process ...
        self.sessions[user_id] = session

# GOOD: Stateless — session stored externally
class GoodSession:
    def handle_request(self, user_id, data):
        session = redis.get(f"session:{user_id}")
        # ... process ...
        redis.set(f"session:{user_id}", updated_session)
```

### Data Partitioning Strategies

```text
Hash-Based Partitioning:
  server = hash(key) % N
  Problem: N changes → most keys remap (massive migration)

Consistent Hashing:
  Keys and servers placed on a unit ring [0, 2^256 - 1]
  Key assigned to next server clockwise.
  On server add/remove: only neighbor keys remap.

  +------+    +------+     +------+
  |  S1  |    |  S2  |     |  S3  |
  | K-A  |    | K-B  |     | K-C  |
  +------+    +------+     +------+
     |            |            |
  S4 added: K-A moves to S4 (only S1's keys affected)

Range-Based Partitioning:
  Shard 1: users A-F
  Shard 2: users G-L
  Shard 3: users M-R
  Shard 4: users S-Z
  Problem: hotspots on skewed distribution (e.g., many "S" names)

Directory-Based Partitioning:
  Lookup table: key → shard
  Flexible but: SPOF (lookup service), extra hop
```

- **Sharding**: Horizontal partitioning across databases
- **Federation**: Split databases by function (user DB, orders DB, products DB)
- **Partition Tolerance**: System continues despite network partition (CAP theorem)

---

## Availability

### HA Configurations

```text
Active-Passive:                       Active-Active:
+--------+      +--------+            +--------+      +--------+
| Active |----->|Passive |            |Active A|<---->|Active B|
| (live) |      |(standby)|           |(writes)|      |(writes)|
+--------+      +--------+            +--------+      +--------+
     |                |                     |               |
     |<----health------                     |<--- replicate->
     |     check       |                    |               |
     |                 |                   \/              \/
Failover: promote passive to active
RTO: seconds (warm) - minutes (cold)

Multi-AZ (Availability Zone) = physically separate datacenter in same region
Multi-Region = geographically separate, active-passive or active-active
```

- **N+1 Redundancy**: N nodes required + 1 spare. Single node failure tolerated.
- **2N Redundancy**: Double capacity — full traffic handled even with N failures.
- **N+M Redundancy**: N required + M spares. Middle ground.
- **SPOF Elimination**: Redundant network links, power supplies, load balancers, database replicas.
- **Failover**: Automatic (health check → DNS swap/load balancer reconfig) vs Manual (human triggered).
- **Leader Election**: Raft, Paxos, Zab (ZooKeeper). Nodes vote for leader. Majority required.
- **Graceful Degradation**: Return limited functionality instead of crash (e.g., show cached data when DB is down).

### Health Checks

- **TCP Health**: SYN → SYN/ACK? → port open
- **HTTP Health**: `GET /health` → 200 OK? Application-level check (DB connection, queue reachable)
- **gRPC Health**: Health/Check RPC → SERVING status
- **Passive**: Monitor request failures (Envoy outlier detection)
- **Active**: Periodic probe from load balancer

---

## Performance

### Latency vs Throughput

```text
Latency = time for one request (ms)
Throughput = requests per second (RPS)

The relationship:
  concurrency = latency × throughput (Little's Law)

Fixed concurrency: high latency → low throughput
Parallel requests can hide latency but increase resource usage

Typical Latency Numbers (2025 hardware):
  L1 cache:      ~1ns
  L2 cache:      ~4ns
  L3 cache:      ~10ns
  DRAM:          ~100ns
  SSD (NVMe):    ~10-50µs
  Network (DC):  ~500µs
  Cross-region:  ~30-100ms
  HDD:           ~5-10ms
  TLS handshake: ~20-50ms (full)
```

### Tail Latency

```text
P50 = median latency (50th percentile)
P95 = 95% of requests faster than this
P99 = 99% of requests faster than this
P999 = 99.9% of requests faster than this

Importance: In large systems, the slowest few requests affect many users
  - 1000 servers, each serving 1000 requests: P999 affects 1M requests
  - Long tail = fan-in aggregation (many parallel services)
```

- **HOL Blocking**: One slow request blocks others in queue (HTTP/1.1 pipelining, TCP)
- **Timeouts**: Deadlines for external calls. Fast fail vs crash-in-progress
- **Retry Budget**: Limit total retries per window. Prevent retry storms (exponential backoff + jitter)
- **Load Shedding**: Drop excess requests gracefully (503 Service Unavailable with Retry-After)
- **Throttling**: Limit per-user/per-IP request rates
- **Backpressure**: Receiver signals sender to slow down (gRPC flow control, TCP receive window, queue limits)

---

## Reliability

### Fault Tolerance

```
Fault types:
  Physical:   Server crash, power loss, network cable cut
  Logical:    Bug, corrupted data, race condition
  Timeout:    Slow dependency, GC pause, deadlock
  Byzantine:  Arbitrary behavior (malicious node, bit flip)

Strategy:
  Tolerate = detect + isolate + recover
           = redundancy + health checks + circuit breakers + graceful degradation
```

### SLA / SLO / SLI

- **SLI** (Service Level Indicator): Measured metric. E.g., request latency, error rate, uptime.
- **SLO** (Service Level Objective): Target threshold. E.g., P99 latency < 200ms, 99.9% availability.
- **SLA** (Service Level Agreement): Contract with consequences (credits, penalties). Usually looser than SLO.
- **Error Budget**: 100% - SLO. E.g., 99.9% SLO = 0.1% error budget = ~8.76 hours downtime/year. Team can deploy during error budget surplus. Must stop deploying when budget exhausted.
- **Reliability Ladder**: Monitoring → Alerting → Incident Response → Postmortem → Preventative → Reliability Culture.
- **Chaos Engineering**: Netflix Chaos Monkey, Simian Army. Deliberately inject failures to test resilience.

---

## Consistency Models

### Consistency Spectrum

```text
Weaker Consistency ←─────────────────────────→ Stronger Consistency
     |                        |                        |
     v                        v                        v
Eventual  Causal   Read-Your-    Session   Monotonic  Strong/Linearizable
                    Own-Writes

                 Bounded Staleness (between eventual and strong)
                   - Time bound: e.g., < 30s lag
                   - Version bound: e.g., < N versions behind

Tradeoff: Strong consistency = higher latency, lower availability (CAP)
          Eventual consistency = higher availability, lower latency
```

- **Strong**: After write completes, all subsequent reads see it. Single-node DB reads, Paxos/Raft commit.
- **Eventual**: Given enough time without updates, all replicas converge. DNS propagation.
- **Causal**: Causally related writes seen in order. Concurrent writes can be seen in any order. Vector clocks.
- **Read-Your-Writes**: Client always sees its own writes. Session tokens, sticky sessions.
- **Session**: Within same session, read-your-writes + monotonic reads.
- **Monotonic Read**: Successive reads never see older version. If you read value v, all future reads return ≥ v.
- **Monotonic Write**: Writes by same client are applied in order. Prevents "lost updates."
- **Bounded Staleness**: Reads are guaranteed to be within K versions or T seconds of latest write.

---

## Caching Strategies

```python
# Cache-Aside (lazy loading) — most common
def get_user(user_id: str) -> User:
    user = redis.get(f"user:{user_id}")
    if user is not None:
        return deserialize(user)

    user = db.query(User).filter_by(id=user_id).first()
    redis.set(f"user:{user_id}", serialize(user), ex=3600)
    return user

# Write-Through
def write_user(user_id: str, data: dict):
    user = db.query(User).filter_by(id=user_id).update(data)
    redis.set(f"user:{user_id}", serialize(user), ex=3600)
    db.commit()

# Write-Around
def write_user(user_id: str, data: dict):
    db.query(User).filter_by(id=user_id).update(data)
    db.commit()
    # Write directly to DB, invalidate cache
    redis.delete(f"user:{user_id}")

# Write-Back (write-behind)
def write_user(user_id: str, data: dict):
    redis.set(f"user:{user_id}_pending", serialize(data))
    # Async: batch + flush to DB periodically

# Refresh-Ahead
def get_user(user_id: str) -> User:
    # Before TTL expires, proactively refresh from DB
    cached = redis.get(f"user:{user_id}")
    if cached.ttl < 60:  # refresh if expiring soon
        asyncio.create_task(refresh_user_cache(user_id))
    return deserialize(cached)
```

### Cache Eviction Policies

| Policy | Strategy | Best For |
|--------|----------|----------|
| LRU | Evict least recently used | General purpose, temporal locality |
| LFU | Evict least frequently used | Stable access patterns, popularity skew |
| FIFO | Evict oldest first | Simple, short-lived items |
| TTL | Evict after fixed time | Predictable staleness |
| 2Q | Two LRU queues (hot/warm) | Better than LRU for scans |
| ARC | Adaptive — balances LRU/LFU | Dynamic workloads |
| Clock | Approximate LRU (reference bits) | Memory-limited, scalable |

### Caching Challenges

- **Cache Stampede (Thundering Herd)**: Many requests miss simultaneously when cache expires → all hit DB. Use mutex (lock), request coalescing, early expiration + background refresh.
- **Hot Key**: Single key receives disproportionate traffic. Solution: hot key replication (multiple cache nodes hold copy), local cache (in-process), read replicas.
- **Stale Cache Serving**: Serve stale data while async-fetching fresh version (`stale-while-revalidate`). Tolerable for many workloads.
- **Cache Warming**: Pre-populate cache before traffic arrives (deployment, launch event).

---

## Database Patterns

### CQRS — Command Query Responsibility Segregation

```text
                   +--------------+
                   |  Client      |
                   +---+------+---+
                       |      |
                  Write|      |Read
                       v      v
              +-------------+----------------+
              | Command Bus |   Query Bus     |
              | (commands)  |   (queries)     |
              +------+------+-------+--------+
                     |               |
                     v               v
              +-----------+  +----------------+
              | Write DB  |  | Read Database  |
              | (normal-  |  | (denormalized, |
              |  ized)    |  |  indexed,      |
              +-----+-----+  |  cached)       |
                    |        +----------------+
                    |                ^
                    +----sync--------+
                    (eventual consistency)
```

### Event Sourcing

```python
# Event Store: append-only log of domain events
class AccountEventStore:
    def save_events(self, account_id: str, events: list[Event]):
        for event in events:
            sql = "INSERT INTO event_store (stream_id, version, event_type, data)"
            sql += " VALUES (?, ?, ?, ?)"
            db.execute(sql, [account_id, event.version, type(event).__name__, serialize(event)])

    def get_events(self, account_id: str) -> list[Event]:
        rows = db.query("SELECT * FROM event_store WHERE stream_id = ? ORDER BY version", [account_id])
        return [deserialize(r.event_type, r.data) for r in rows]

# Aggregate: rebuild state from events
class Account:
    def __init__(self):
        self.balance = 0
        self.version = 0

    def apply(self, event: Event):
        match event:
            case Deposited(amount=amount): self.balance += amount
            case Withdrawn(amount=amount): self.balance -= amount
        self.version += 1

# Projection: read model built from events
class AccountBalanceProjection:
    def on_deposited(self, event):
        sql = "UPDATE account_balances SET balance = balance + ? WHERE id = ?"
        db.execute(sql, [event.amount, event.account_id])

    def on_withdrawn(self, event):
        sql = "UPDATE account_balances SET balance = balance - ? WHERE id = ?"
        db.execute(sql, [event.amount, event.account_id])
```

- **Snapshot**: Periodically save aggregate state. Rebuild from snapshot + events after it.
- **Event Versioning**: New event fields over time. Use upcasting (migrate old events on read).
- **SAGA**: Distributed transaction pattern. Each step publishes event that triggers next step. Compensating transactions on failure.
- **Outbox Pattern**: Write to event outbox table in same DB transaction as business data. Reliable publisher reads outbox → message broker.
- **Database-per-service**: Each microservice owns its DB. No sharing.
- **Shared Database**: Multiple services share same DB. Simpler but couples schema changes.

---

## Simplest Mental Model

> **System design is building a restaurant empire.**
>
> - **Vertical Scaling** = Bigger kitchen with more stoves. Hits ceiling when you can't fit more equipment.
> - **Horizontal Scaling** = More restaurant locations. Each location handles its own customers. Requires coordination between kitchens.
> - **Load Balancer** = The host at the door who knows which tables are free (round-robin), which waiters have fewer customers (least connections), or who served you last time (sticky sessions).
> - **Caching** = Your go-to menu items that are pre-made (CDN = pre-made at every location, Redis = ingredients ready in the back, database = full inventory in the warehouse).
> - **Cache Eviction** = Running out of prep space — must decide: discard oldest (LRU), least popular (LFU), or about-to-expire (TTL).
> - **Consistency Models** = How quickly the menu prices update across all locations after a price change. Strong = all menus updated before anyone sees them (slow but accurate). Eventual = some customers might see old prices for a bit (fast but temporarily inconsistent).
> - **CAP Theorem** = You can have a perfectly up-to-date menu (consistency), keep serving during a phone outage (partition tolerance), or stay open continuously (availability) — pick two.
> - **CQRS** = Separate order-taking (writes) from menu display (reads). Different systems optimized for each.
> - **Event Sourcing** = Keep the complete receipt tape. Any state can be reconstructed by replaying all transactions from day one.
> - **SAGA** = A multi-step order with compensating actions: if dessert fails, the main course order is automatically refunded.