# ⚡ Distributed Caching — Complete Deep Dive

> **Scope**: Caching strategies (cache-aside, read-through, write-through, write-behind, refresh-ahead), eviction policies (LRU, LFU, ARC, LIRS, TinyLFU, 2Q), Redis cluster internals, Memcached internals, cache invalidation patterns, caching at scale (Netflix EVCache, Twitter Twemproxy, Facebook mcrouter), consistent hashing variants, cache stampede prevention, failure modes and monitoring.
>
> **Related**: [01-cap-consistency.md](./01-cap-consistency.md) | [04-distributed-transactions.md](./04-distributed-transactions.md)

## Table of Contents

1. Caching Strategies
2. Cache Eviction Policies
3. Redis Cluster Internals
4. Memcached Internals
5. Cache Invalidation Patterns
6. Caching at Scale
7. Consistent Hashing & Variants
8. Cache Stampede / Thundering Herd
9. Strategy Comparison
10. Cache Size Estimation
11. Cache Monitoring
12. Failure Modes
13. Atomic Operations in Redis
14. Cache-DB Consistency

---

## 1. Caching Strategies

```text
Cache-Aside (Lazy Loading):
  Application                    Cache                      DB
     |                             |                        |
     |--- GET(key) --------------->|                        |
     |<-- MISS --------------------|                        |
     |--- SELECT * FROM db ------->|                        |
     |<-- result ------------------|                        |
     |--- SET(key, result) ------->|                        |
     |                             |                        |

Read-Through:
  Application                    Cache                      DB
     |                             |                        |
     |--- GET(key) --------------->|                        |
     |                             |--- MISS -> load ------->|
     |                             |<-- result -------------|
     |                             |--- store --------------|
     |<-- result ------------------|                        |

Write-Through:
  Application                    Cache                      DB
     |                             |                        |
     |--- SET(key, val) ---------->|                        |
     |                             |--- INSERT/UPDATE ----->|
     |                             |<-- OK -----------------|
     |<-- OK ----------------------|                        |

Write-Behind (Write-Back):
  Application                    Cache                      DB
     |                             |                        |
     |--- SET(key, val) ---------->|                        |
     |<-- OK ----------------------|                        |
     |                             |  (async, batched)      |
     |                             |--- INSERT/UPDATE ----->|
     |                             |<-- OK (later) ---------|

Refresh-Ahead:
  Application                    Cache
     |                             |
     |--- GET(key) --------------->|
     |<-- result (cache hit) ------|
     |                             | (TTL nearing expiry)
     |                             | (proactively refresh)
```

**Cache-Aside:** Most common. App manages cache. Cache misses are handled by app. Simple, flexible. Downside: N+1 problem, stampede risk.

**Read-Through:** Cache library handles miss. App simpler. Less flexible (cache provider dependent). Used by Memcached (with mcrouter), EVCache.

**Write-Through:** Synchronous dual write. Latency increases but consistency improves. Good for data that must be immediately consistent.

**Write-Behind:** Asynchronous. Buffered writes to DB. Fast writes but risk of data loss on cache node failure. Good for high-write workloads.

**Refresh-Ahead:** Predicts expiry. Proactively fetches fresh data before TTL expiration. Reduces latency spikes. Requires predicting access patterns.

---

## 2. Cache Eviction Policies

**LRU (Least Recently Used):**
- Data structure: doubly linked list + hashmap
- Get: move to front (O(1)). Put: evict from back (O(1)).
- Problem: scan once pattern pollutes cache (sequential scan evicts hot items).
- Variants: LRU-k (track last k accesses), segmented LRU (hot/warm/cold).

**LFU (Least Frequently Used):**
- Data structure: min-heap (frequency) + hashmap (key->frequency)
- Get: increment frequency, update heap (O(log n)).
- Problem: old hot items never evict even if no longer accessed (frequency inertia).
- Solution: frequency decay, window-based counting.

**ARC (Adaptive Replacement Cache):**

```text
+---+---+---+---+
| B1 | T1 | T2 | B2 |
+---+---+---+---+

T1 = recent (recency-focused)
T2 = frequent (frequency-focused)
B1 = ghost entries evicted from T1
B2 = ghost entries evicted from T2

Ghost entries track recently evicted items to adapt:
- Hit in B1: increase T1 size (recency matters more)
- Hit in B2: increase T2 size (frequency matters more)
Self-tuning between recency and frequency.
```

ARC maintains four LRU lists (B1, T1, T2, B2). Total size fixed. Adaptive parameter `p` partitions cache between recency (T1) and frequency (T2). Ghost entries hold metadata only (not values), track what's been evicted.

**LIRS (Low Inter-reference Recency Set):**
- HIR (High Inter-reference Recency): entries with large reuse distance
- LIR (Low Inter-reference Recency): entries with small reuse distance
- LIR entries are always in cache; HIR entries compete for remaining space
- Scan-resistant: sequential scans produce HIR entries that don't evict LIR.

**TinyLFU (Caffeine):**
- Frequency sketch: 4-bit Count-Min Sketch for approximate frequency counting
- Reset mechanism: periodically halve all counters (exponential decay)
- Admission window: new entries start in small window; on eviction, candidate compared with TinyLFU gate
- Adaptive: track hit rate of admission window, adjust if performance degrades

```text
Caffeine Architecture:
         +--------------------+
         | Admission Window   |  (small, fast, recency)
         +--------+-----------+
                  |
             hit rate? < threshold?
                  |
                  v
         +--------+-----------+
         | TinyLFU Gate       |  (frequency sketch)
         | (candidate vs victim)|
         +--------+-----------+
                  |
         +--------+-----------+
         | Main Space         |  (large, frequency-based)
         +--------------------+
```

**2Q (Two Queue):**
- A1in: FIFO for first-time access
- A1out: ghost entries (metadata only)
- Am: LRU for frequently accessed items
- Items move A1in -> Am on second access. Am evictions go to A1out.

**Performance Comparison (approximate):**
| Policy | Scan-Resist | Adaptivity | Complexity | Memory Overhead |
|--------|-------------|------------|------------|-----------------|
| LRU | Poor | None | O(1) | Low |
| LFU | Good | No decay | O(log n) | Medium |
| ARC | Excellent | Self-tuning | O(1) | High (ghost entries) |
| LIRS | Excellent | None | O(1) | Medium |
| TinyLFU | Excellent | Adaptive | O(1) | Low (sketch) |
| 2Q | Good | Fixed | O(1) | Medium |

---

## 3. Redis Cluster Internals

**Hash Slot:** 16384 slots total. Key -> CRC16(key) % 16384 -> slot.

```text
Cluster Nodes:
  +----------+     +----------+     +----------+
  | Node A   |     | Node B   |     | Node C   |
  | slots:   |     | slots:   |     | slots:   |
  | 0-5460   |     | 5461-10922|    | 10923-16383|
  | replicas |     | replicas |     | replicas |
  +----+-----+     +----+-----+     +----+-----+
       |                |                |
       +----------------+----------------+
                        |
                Cluster Bus (port +10000)
                Gossip protocol
                PING/PONG every 100ms
```

**MOVED Redirection:** Client sends command to wrong node. Node responds with `-MOVED <slot> <node_ip>:<port>`. Client redirects and updates slot cache.

**ASK Redirection:** During resharding (slot migration). Source node responds with `-ASK <slot> <target>`. Client sends `ASKING` then command. Slot not yet migrated — transient state.

**Cluster Bus:** Separate gossip port (TCP, inter-node). PING/PONG, FAILOVER, PUBLISH, REPLICATE messages. Node discovery, failure detection (PFAIL -> FAIL based on gossip + info from other nodes).

**Failover:** Replica initiates if master is PFAIL for `cluster-node-timeout`. Replica sends `FAILOVER_AUTH_REQUEST` to all masters. Majority must acknowledge. Replica becomes new master.

**Replica Migration:** Orphan replicas (no master) migrate to masters with fewer replicas.

**Resharding:**
```
redis-cli --cluster reshard <host>:<port>
1. Set source and target nodes
2. Set number of slots to move
3. For each slot:
   a. Source: migrate all keys in slot to target
   b. Source: slot migration state (MIGRATING)
   c. Target: slot import state (IMPORTING)
   d. On key move: MIGRATE command (dump key, restore, delete)
4. Cluster state -> slot assigned to target
```

---

## 4. Memcached Internals

**Slab Allocator:** Prevents memory fragmentation by allocating slabs (1MB chunks) divided into slab classes with fixed chunk sizes.

```text
Slab Class 1: chunk size = 96 bytes
Slab Class 2: chunk size = 120 bytes (growth factor 1.25)
Slab Class 3: chunk size = 152 bytes
...
Slab Class N: chunk size = 1MB (max item size)

Each slab class = N slabs (1MB) -> N * (chunk size) items per slab.
```

**Page Size:** 1MB default. Each slab class carves pages into chunks of its size.

**Slab Growth:** On slab class exhaustion, Memcached allocates new page (evicts from another slab class if needed via LRU crawler).

**LRU per Slab Class:** Each slab class has its own LRU list. Eviction happens within the same slab class, not globally. A large item slab class may have different hit rate than small.

**No Replication:** Memcached has no built-in replication. Data loss on node failure.

**Consistent Hashing:** Clients (like libketama) use consistent hashing for key mapping. Server list changes cause minimal key redistribution.

**Memcached Challenges:**
- Hot key: one key gets massive traffic, single server overloaded
- Connection overhead: many client connections
- No authentication (pre-v1.4.3)
- No persistence

---

## 5. Cache Invalidation Patterns

**Explicit Delete/Invalidate:** On write to DB, delete corresponding cache key. Next read triggers cache miss and fresh load. Simplest and most reliable.

**TTL/Expiry:** Set TTL on cache entry. Data self-invalidates after TTL. Used for time-bounded staleness. Common TTLs: 1s, 10s, 60s, 300s.

**Version Key:** Key includes version suffix (e.g., `user:profile:42:v3`). On data update, increment version. New reads use new version key; old keys expire naturally via TTL.

**Timestamp-Based:** Each cache entry has a stored timestamp. Application compares with last-known update time. On mismatch, refresh.

**Redis Keyspace Notifications:** Subscribe to `__keyspace@0__:keyname` events. Get notified on SET/DEL/EXPIRE. Useful for cascading invalidation across services.

**CDC (Change Data Capture) -> Debezium -> Cache Update:**

```text
Application                    Database              Kafka Connect
     |--- UPDATE --------------->|                        |
     |<-- OK --------------------|                        |
     |                           |--- binlog/WAL -------->|
     |                           |                        |--- Debezium ---> Cache Update Service
     |                           |                        |                        |
     |                           |                        |               cache.invalidate(key)
```

Real-time invalidation without application awareness. Used at scale for cross-service cache consistency.

**Cache Invalidation Anti-Patterns:**
- **Timeout-based only with no max staleness:** Risk of unbounded staleness
- **Global cache flush:** Unnecessary cold-start, stampede risk
- **Update cache on DB write without version check:** Race condition (old value overwrites new)
- **Complex multi-key invalidation transactions:** Atomicity challenges

---

## 6. Caching at Scale

**Netflix EVCache (memcached-based):**
- Multi-region, cross-region replication via EVCache replication
- Write-behind replication (async, eventually consistent)
- Region affinity: reads prefer local region
- Cold start mitigation: warm-up from backup region
- Consistency: TTL-based + replica sync via ZooKeeper

**Twitter Twemproxy (proxy for memcached/Redis):**
- Single-threaded event-driven proxy
- Consistent hashing (Ketama)
- Auto-ejection of unhealthy servers
- Pipeline support (reduce connection count)
- Limitations: single core bottleneck, no auto-scaling

```text
Application --> Twemproxy --> [Memcached/Redis Nodes]

Twemproxy features:
  - Consistent hashing
  - Server auto-ejection
  - Connection pooling
  - Protocol translation
  - Pipelining
```

**Facebook Mcrouter (multi-cluster router):**
- Multi-tenant, multi-cluster, pool-based
- Regional pools for geographic routing
- Stale sets: serve stale data during cache miss (if latency bound)
- Lease mechanism: prevent thundering herd (lease token for cache miss)
- Thrifty: adaptive replication for hot keys

```text
Mcrouter Routing:
Client --> mcrouter --> [pool-replicated-cache]
                  --> [pool-regional-cache]
                  --> [pool-local-cache]
```

**Facebook Stale Sets:**
When cache misses, instead of going to DB, serve a slightly stale value (within bound). Used when latency matters more than perfect freshness.

```text
Cache miss (TTL < staleness_tolerance):
  Return stale value + async refresh in background

Cache miss (TTL > staleness_tolerance):
  Return stale value + refresh from DB (blocking)
```

---

## 7. Consistent Hashing & Variants

```text
Classic Consistent Hashing Ring:
           +---0---+
           |       |
     360   |       |   30
           |       |
           +-------+
       330 |       | 60
           |       |
           |       |
     300   +-------+ 90
           |       |
           |       |
       270 |       | 120
           |       |
           +---240-+
```

**Without Consistent Hashing:**
- `hash(key) % N` servers
- Adding/removing server -> most keys remap
- Cache hit ratio drops to near 0% during scaling

**Consistent Hashing:**
- `hash(key)` maps to ring position
- Each server maps to one or more ring positions
- Key is stored at first clockwise server
- Adding/removing server remaps only adjacent keys

**Virtual Nodes:** Each physical server maps to multiple virtual nodes on ring. Improves load distribution. Default: 150 virtual nodes per server.

**Jump Consistent Hash (Google, 2014):**
- O(log n) — no ring, uses piecewise-linear function
- Minimal redistribution: adding a server remaps exactly 1/n of keys
- Cannot remove servers (fixed server list)
- Used in Google's internal systems

**Rendezvous Hashing (HRW — Highest Random Weight):**
- Each server computes `hash(key || server_id)` — key's weight for that server
- Key assigned to server with highest weight
- Deterministic, O(n) computation
- Good for small n, poor for large n
- Minimal redistribution (n remaps 1/(n+1) on new server)

**Comparison:**
| Algorithm | Complexity | Redistribution | Server Removal | Use Case |
|-----------|------------|----------------|----------------|----------|
| Mod N | O(1) | All keys | Easy | Static clusters |
| Ring (ketama) | O(log v) | 1/n keys | Easy | Memcached, Redis |
| Jump | O(log n) | 1/n keys | Not supported | Google internal |
| HRW | O(n) | 1/(n+1) keys | Easy | Small clusters |

---

## 8. Cache Stampede / Thundering Herd

**Problem:** Cache for popular key expires. Hundreds of concurrent requests all miss -> all hit DB simultaneously. DB overload, cascading failures.

**Solutions:**

**Mutex Lock per Key:**
```text
Request 1:   GET key -> MISS
             SETNX lock_key (TTL=10s)
             lock acquired -> LOAD FROM DB -> SET key -> DEL lock
             return value
Request 2-N: GET key -> MISS
             SETNX lock_key -> fail (already locked)
             WAIT (retry GET, spin)
```

**Probabilistic Early Expiration (X-Default):**
```text
Cache entry TTL = 600s
On GET:
  remaining_ttl = TTL - (now - created_at)
  if remaining_ttl < 0:
    MISS (expired)
  elif random() < (TTL - remaining_ttl) / TTL * factor:
    PROACTIVE_REFRESH (async) + return stale value
  else:
    return value immediately
```

Jitter added to TTL (e.g., 10% random) also prevents synchronized mass expiration.

**Stale-While-Revalidate:**
```text
Cache-Control: max-age=60, stale-while-revalidate=300
- 0-60s: use fresh cache value, fast
- 60-360s: serve stale value, background revalidation
- 360s+: normal cache miss (blocking fetch)
```

**Hedge Requests:** Send multiple parallel requests to DB/cache. Use first response, cancel others. Mitigates tail latency and intermittent slow responses. Used by Google, AWS.

**Redis SETNX Lock with TTL:**
```text
SET key_lock <unique_id> NX EX 10  -- acquire lock
SET key <value> EX 600             -- set cache
DEL key_lock                        -- release lock
```

Lock must be unique (prevents same-key unlocking across requests). TTL on lock prevents deadlock if lock holder crashes.

---

## 9. Strategy Comparison

| Strategy | Read Latency | Write Latency | Stale Reads | Implementation Complexity |
|----------|-------------|---------------|-------------|-------------------------|
| Cache-Aside | Low (hit) / High (miss) | Low | Possible (before write to cache) | Simple |
| Read-Through | Low (hit) / Medium (miss) | Low | Possible | Medium (cache lib) |
| Write-Through | Low (hit) | High (sync to DB) | Minimal (strongest) | Medium |
| Write-Behind | Low (hit) | Very Low (async) | Yes (write lag) | High (durability risk) |
| Refresh-Ahead | Low (always) | Low | Very Low | High (predictive load) |

---

## 10. Cache Size Estimation

**Working Set Estimation:**
- Track unique keys accessed in a sliding window (e.g., 1 hour)
- Measure access frequency distribution (Zipfian typically)
- Target: cache size = 80-90% of working set
- Tool: Redis `INFO keyspace`, `MEMORY USAGE`, `MEMORY STATS`

**Sampling vs Full Scan:**
- For large clusters, sample keyspace (cross-node)
- Estimate per-key size distribution
- Count-Min Sketch for frequency distribution

**Hit Ratio vs Cache Size (typical asymptotic):**
```text
Hit Rate
 100% |                                ___
  90% |                           _____|
  80% |                     _____|
  70% |               _____|
  60% |          _____|
  50% |     _____|
  40% |____|
       +-----------------------------------> Cache Size
        Working set                        (as % of total data)
```

Goal: operate on the "knee" of the curve (diminishing returns).

---

## 11. Cache Monitoring

**Key Metrics:**
- **Hit Ratio:** `hits / (hits + misses)`. Target > 90%.
- **Miss Ratio:** `1 - hit_ratio`.
- **Eviction Rate:** Number of keys evicted per second. High eviction -> undersized cache.
- **Memory Usage:** Current vs max memory. Monitor growth rate.
- **Network Bandwidth:** Ingress/egress throughput.
- **Command Latency:** P99/P999 of GET/SET commands.
- **Slowlog:** Redis `SLOWLOG GET 100`.

**Redis Monitoring:**
```text
redis-cli INFO stats | grep hits
redis-cli INFO memory | grep used
redis-cli INFO cpu
redis-cli SLOWLOG GET 10
```

**Eviction Rate Analysis:**
- High eviction + low hit ratio = cache too small
- High eviction + high hit ratio = working set shifted, access pattern changed
- Sudden eviction spike = popular key expired or DDOS/traffic surge

---

## 12. Failure Modes

**Cache Node Down -> Request Storm to DB:**
- All keys mapped to lost node must be re-fetched.
- DB load increases proportional to affected keyspace.
- Mitigation: connection pooling, DB read replica scaling, circuit breaker, graceful degradation.

**Connection Pool Exhaustion:**
- If cache slows (network issue), connections accumulate.
- Pool exhausts -> all requests fail to cache -> cascading to DB.
- Mitigation: pool timeout, fail-fast, circuit breaker.

**OOM from Cache Flooding:**
- Cache filled with unique keys (cache miss storm).
- Eviction rate spikes, hit ratio drops.
- Mitigation: rate limit, restrict key size, limit key TTL.

**Hot Key Amplification:**
- Single key accessed at very high rate.
- One cache node becomes bottleneck.
- Mitigation: local cache (client-side caching), hot key replication (read replicas), shard splitting.

```text
Hot Key Problem:
  All requests for "trending_video_1" -> Node A
  Node A: 100K QPS (max capacity: 20K QPS)
  Node A: overloaded, slow, timeout

Solutions:
  1. Local cache (stale tolerated): each client caches locally
  2. Hot key replication: replicate to N nodes, client picks random
  3. Adaptive sharding: split hot key into sub-keys
```

**Backup Requests:** If a request times out, app issues backup request to another cache node. Same as hedge requests at cache layer.

**Replication Lag Inconsistency:**
- Write to master, read from replica (stale).
- Session consistency required.
- Mitigation: read-your-writes via read-from-master for the session.

---

## 13. Atomic Operations in Redis

**Redis Pipeline:**
```text
Client: SET key1 val1
Client: GET key2
Client: INCR counter
All sent at once -> multipart response
Non-atomic: other commands can interleave between pipeline commands
```

**Redis Transactions (MULTI/EXEC):**
```text
MULTI
SET key1 val1
GET key2
INCR counter
EXEC
Atomic: all or none executed. But no rollback (if syntax error: none exec).
WATCH provides optimistic locking.
```

**Lua Scripting (EVAL):**
```text
EVAL "redis.call('SET', KEYS[1], ARGV[1]); return redis.call('GET', KEYS[1])" 1 key1 val1
Fully atomic. All or nothing. No interruption.
Preferred over MULTI/EXEC for complex operations.
```

**Lazy Freeing:**
- `UNLINK key`: deletes key in background thread, returns immediately
- `FLUSHDB ASYNC` / `FLUSHALL ASYNC`: async flush, non-blocking
- Prevents main event loop blocking on large key deletion

---

## 14. Cache-DB Consistency

**Dual Write Problem:** Application writes to both DB and cache. If one fails, they diverge.

**Solutions:**

**Write-through (transactional):**
```text
BEGIN TX
  UPDATE db SET x=1 WHERE id=42
  cache.set("key:42", new_value)
COMMIT
```
If cache.set fails, rollback DB. Both succeed or both fail.

**Read Repair:** On read, if cache value differs from DB, update cache. Works for eventual consistency.

**Async Repair:** Background process compares DB and cache, fixes discrepancies.

**CDC Sync (Debezium):**

```text
DB Write -> WAL/binlog -> Debezium -> Kafka -> Cache Update Service -> Redis SET
```

Zero application involvement. Cache always reflects DB changed data.

**Outbox Pattern:**
```text
BEGIN TX
  UPDATE db
  INSERT INTO outbox (event_type, payload)
COMMIT
-- CDC reads outbox -> invalidate/update cache
```

Atomic DB update + outbox write in same transaction. CDC ensures cache update eventually. Solves dual-write atomicity.

**TTL safety net:** Even with all strategies, TTL ensures cache eventually self-heals.

---

## Simplest Mental Model

**Caching is like a whiteboard next to your filing cabinet.** You write popular files' contents on the whiteboard (cache) so you don't have to open the filing cabinet (DB) every time. The challenge is keeping the whiteboard updated when the filing cabinet changes — you either update both simultaneously (write-through), or let the whiteboard expire and re-fetch (TTL), or erase the whiteboard entry when you change the file (invalidate). The hard part is doing this in a distributed system without everyone overcrowding the filing cabinet at once (cache stampede).
