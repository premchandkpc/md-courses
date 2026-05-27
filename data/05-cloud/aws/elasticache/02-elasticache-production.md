# 🚀 ElastiCache Production Patterns — Complete Deep Dive

## Table of Contents
- [Redis Cluster Mode](#redis-cluster-mode)
- [Replication & Persistence](#replication--persistence)
- [Eviction Policies](#eviction-policies)
- [Redis Pub/Sub & Streams](#redis-pubsub--streams)
- [Sorted Sets (Leaderboards, Rate Limiting)](#sorted-sets-leaderboards-rate-limiting)
- [Memcached vs Redis](#memcached-vs-redis)
- [Auto-Failover Multi-AZ & Backup/Restore](#auto-failover-multi-az--backuprestore)
- [Encryption (At Rest & In Transit)](#encryption-at-rest--in-transit)
- [Security Groups & Parameter Groups](#security-groups--parameter-groups)
- [CloudWatch Metrics](#cloudwatch-metrics)
- [Global Datastore & ElastiCache Serverless](#global-datastore--elasticache-serverless)
- [Cost Optimization & Caching Patterns](#cost-optimization--caching-patterns)
- [Redis Transactions](#redis-transactions)
- [Simplest Mental Model](#simplest-mental-model)

---

## Redis Cluster Mode

Distributed Redis sharding across 16384 hash slots. `CRC16(key) % 16384 -> assigned shard`.

```text
No Cluster: 1 shard (primary + replicas). Max 161 GB. No horizontal scaling.
Cluster Enabled: Up to 500 shards. Reshard online with zero downtime.

```

**Resharding**: Slots moved from source to target shard. Source marks IMPORTING, target marks MIGRATING. Keys migrated incrementally. Clients retry MOVED/ASK redirects during migration.

**Client requirement**: redis-py-cluster, ioredis, Lettuce. Non-cluster clients get MOVED errors.

**Scaling**: Add shards for throughput (more CPU cores parallelizing). Add replicas for read throughput. Scale during low traffic.

## Replication & Persistence

**Replication**: Async via PSYNC2 (Redis 4.0+). Primary buffers writes in backlog (16 MB circular). Replica requests partial sync (ID + offset). Full sync if outside backlog. PSYNC2 supports partial resync after failover.

**Backlog sizing**: `repl-backlog-size = (reconnect time in sec) * (write rate/sec)`. Monitor `ReplicationLag`.

**Persistence**:

| Feature | RDB (snapshot) | AOF (append-only) |
|---------|---------------|-------------------|
| Recovery | Fast (load dump) | Slow (replay commands) |
| Data loss | Last snapshot | ~1s (everysec) or 0 (always) |
| File size | Smaller | Larger |
| Performance | Fork + write (spiky) | Constant append |

**Best practice**: RDB + AOF combined. Redis loads AOF on restart for most complete data.

## Eviction Policies

When `maxmemory` reached:

| Policy | Description | Use case |
|--------|-------------|----------|
| `allkeys-lru` | LRU on all keys | General cache (default) |
| `allkeys-lfu` | LFU on all keys | Hot/cold data patterns |
| `volatile-lru` | LRU on keys with TTL | Mixed cache + persistent |
| `volatile-ttl` | Shortest TTL first | Time-sensitive data |
| `noeviction` | Return write errors | Must keep all data |

**Choosing**: allkeys-lfu for clear hot keys (frequently accessed stay longer). allkeys-lru for uniform patterns. Avoid noeviction for caches (write failures). Monitor `Evictions` - low (< 100/min) acceptable, high (> 1000/min) = scale.

## Redis Pub/Sub & Streams

**Pub/Sub**: Publisher -> Channel -> Subscribers. No persistence. Offline = lost messages. For real-time notifications, WebSocket broadcast, chat.

**Streams**: Persistent append-only log with consumer groups. `XADD`, `XREADGROUP`, `XACK`. Load-balanced processing with acknowledgment tracking. Can re-read messages.

**vs Pub/Sub**: Streams persist, support consumer groups, ACK tracking, re-reading. Use for job queues, event sourcing, reliable messaging.

## Sorted Sets (Leaderboards, Rate Limiting)

```bash
ZINCRBY leaderboard 100 alice     # add/increment score
ZRANGE leaderboard 0 9 REV        # top 10
ZRANK leaderboard alice           # get rank
ZREM leaderboard bob              # remove member

```

**Sliding window rate limiting**:

```bash
ZREMRANGEBYSCORE ratelimit:user1 0 <now - 60s>
ZCARD ratelimit:user1             # current count in window
ZADD ratelimit:user1 <now> <uuid> # record new request

```

## Memcached vs Redis

| Feature | Redis | Memcached |
|---------|-------|-----------|
| Data structures | Rich (strings, lists, sets, sorted sets, hashes, streams) | Strings only |
| Persistence | RDB + AOF | None (ephemeral) |
| Replication | Yes (Multi-AZ) | No |
| Cluster mode | Native sharding | Client-side only |
| Advanced | Lua, transactions, pub/sub, streams | None |
| Max key size | 512 MB | 1 MB |

**Redis** for almost everything. **Memcached** for pure key-value with minimal overhead.

## Auto-Failover Multi-AZ & Backup/Restore

**Multi-AZ**: Primary in AZ-1, replica in AZ-2. 30-60s detection + promotion. Primary endpoint auto-updates after failover. Reader endpoint round-robins across replicas.

**Backup**: RDB snapshots (auto/manual) stored in S3. Retention: 0-35 days (auto), indefinite (manual). Restore new cluster from snapshot (no point-in-time recovery). GRT for fast S3 restore of large clusters.

## Encryption (At Rest & In Transit)

**At rest**: KMS AES-256 encryption. Enable at cluster creation (cannot add later). Encrypts data, backups, snapshots. Required for PCI/HIPAA/SOC.

**In transit**: TLS enforcement. Clients connect via rediss:// or TLS port 6380. All node-to-node traffic encrypted. Combined with AUTH token for defense in depth.

## Security Groups & Parameter Groups

**Subnet groups**: Subnets per AZ for HA. Include 2+ AZs. Security groups: allow 6379 (Redis) / 11211 (Memcached) from app SGs only. Never 0.0.0.0/0.

**Parameter groups**: Clone default -> modify -> associate (reboot may be required). Key params: `maxmemory-policy`, `timeout`, `tcp-keepalive` (300), `active-defrag`, `appendonly`, `auto-aof-rewrite-percentage`.

## CloudWatch Metrics

**Hit rate**: `CacheHits / (CacheHits + CacheMisses)`. Low = inefficient cache. **Evictions**: > 0 = maxmemory reached. **CPUUtilization**: > 80% sustained = scale. **DatabaseMemoryUsagePercentage**: > 80% = add memory. **CurrConnections**: anomaly detection. **ReplicationLag**: monitor sync issues. **FreeableMemory**: OS memory pressure. **NetworkBytesIn/Out**: approaching limits.

## Global Datastore & ElastiCache Serverless

**Global Datastore**: Active-passive cross-region replication. Primary -> up to 2 secondary regions. RPO < 1s. Promote secondary for DR. Local reads from replicas.

**Serverless**: Auto-scaling, no capacity planning. Pay per ECPU + storage. Min 1 GB. Best for variable/unpredictable workloads. Provisioned clusters cheaper for steady, predictable loads.

## Cost Optimization & Caching Patterns

**Cost**: Reserved nodes (30-60%), RDB-only (less IOPs), right-sizing, cluster + smaller nodes (cheaper per GB), longer backup intervals, replicas for reads.

**Cache-Aside**: Check cache -> miss -> query DB -> write cache (TTL) -> return. Most common. Cache miss penalty.
**Write-Through**: Write DB + write cache simultaneously. Data always fresh. Higher write latency.
**Write-Behind**: Write cache only, async flush to DB. Lowest write latency. Risk of data loss.

## Redis Transactions

`MULTI` (queue commands) -> `EXEC` (atomic execution). `WATCH` for optimistic locking (CAS). If watched key changes before EXEC, transaction aborts. No rollback on errors within EXEC (Redis rolls forward through successful commands).

## Redis Lua Scripting

`EVAL` / `EVALSHA` for atomic server-side scripts. `script load` caches script. `script exists` checks cache. Return KEYS[1], ARGV[1] as arrays. All Redis commands within script are atomic.

**Use cases**: Rate limiting, distributed locking (SET NX EX + Lua for safe unlock), batch compare-and-swap, complex data transformations.

**Best practice**: Scripts are replicated. Keep idempotent (use `redis.replicate_commands()` for non-deterministic). Timeout 5s default. Use `EVALSHA` to minimize bandwidth.

**Danger**: Scripts block all other operations. Never do slow loops. Keep < 10ms execution.

## ElastiCache Scaling

**Horizontal**: Add shards (Redis Cluster). Add replicas. No downtime in Cluster mode - slot migration online.

**Vertical**: Modify node type (reboot required). Must have replicas to avoid downtime (failover -> modify -> failback).

**Memory optimization**: Use Redis Hashes (ziplist encoding for small hashes). `hash-max-ziplist-entries 512`, `hash-max-ziplist-value 64`. Use integer IDs. Avoid large keys. Use pipelining for bulk operations.

**Performance tuning**: `tcp-keepalive 300` for healthy connections. `maxclients 65000` for high concurrency. `hz 10` for background tasks. `lazyfree-lazy-eviction yes` for non-blocking deletes. `activedefrag yes` for memory fragmentation.

## Common Failure Modes

**Memory pressure**: Evictions spike, latency increases -> scale up or improve eviction policy.

**Network bandwidth**: Throttled at instance level -> spread across more shards.

**Failover storms**: Multiple replicas failing at once -> stagger replacement. Increase repl-backlog to reduce full syncs.

**Hot key**: Single key accessed disproportionately -> application-level sharding (prefix-based) on hot key.

**Hot shard**: One shard saturated while others idle -> rebalance hash slots.

**OOM on replica**: Replica runs out of memory applying replication buffer -> increase replica memory or reduce write load.

## Memcached Auto-Discovery

Memcached has no native clustering. ElastiCache provides auto-discovery via AWS API. `telnet my-cluster.cache.amazonaws.com 11211`. App gets all node endpoints. Client libs (spymemcached, ElastiCache Cluster Client) detect node changes. Memcached ASCII protocol: `config get cluster`. Use consistent hashing on client side for distributing keys.

## Client Retry & Failure Handling

**Retry**: Exponential backoff on MOVED, ASK, TRYAGAIN. Timeout per node with pool of connections. Circuit breaker for node-level failures.

**Connection pooling**: Lettuce, jedis-pool. Typical pool: 50 connections. Monitor `CurrConnections` and `NewConnections`.

**TLS overhead**: ~1ms per connection handshake. Pool keeps connections alive. Redis 6 ACL prevents auth bypass.

**Read-from-replica client pattern**: Redis Cluster mode - MOVED redirect handles this. Standalone - use Reader Endpoint which round-robins across replicas. Client sets `READONLY` mode (Redis >= 3.2). No stale data tolerance for reads.

---

## Code Examples

### Java Client (Lettuce — Redis)

```java
import io.lettuce.core.*;
import io.lettuce.core.api.sync.RedisCommands;

// Connection
RedisClient client = RedisClient.create("rediss://auth-token@endpoint:6380");
StatefulRedisConnection<String, String> connection = client.connect();
RedisCommands<String, String> commands = connection.sync();

// Cache-Aside Pattern
String getCacheKey(String userId) {
  String cached = commands.get("user:" + userId);
  if (cached != null) return cached;
  
  // Fetch from DB
  String user = fetchFromDB(userId);
  commands.setex("user:" + userId, Duration.ofMinutes(30), user);
  return user;
}

// Sorted Set (Leaderboard)
commands.zadd("leaderboard", 1000.0, "alice");
commands.zadd("leaderboard", 950.0, "bob");
List<ScoredValue<String>> top10 = 
  commands.zrevrangeWithScores("leaderboard", 0, 9);

// Pipeline (batch operations)
List<Object> results = connection.sync().multi(
  RedisCommand.zadd(...),
  RedisCommand.zadd(...),
  RedisCommand.zrange(...)
);

```

### Python (redis-py)

```python
import redis
from datetime import timedelta

# Connection with pooling
r = redis.Redis(
  host='endpoint.cache.amazonaws.com',
  port=6380,
  ssl=True,
  decode_responses=True,
  socket_pool_kwargs={'max_connections': 50}
)

# Cache-Aside
def get_user(user_id):
  key = f"user:{user_id}"
  cached = r.get(key)
  if cached:
    return json.loads(cached)
  
  user = fetch_from_db(user_id)
  r.setex(key, timedelta(minutes=30), json.dumps(user))
  return user

# Rate limiting with sorted sets
def check_rate_limit(user_id, max_requests=100, window=60):
  key = f"ratelimit:{user_id}"
  now = time.time()
  r.zremrangebyscore(key, 0, now - window)
  
  count = r.zcard(key)
  if count >= max_requests:
    return False
  
  r.zadd(key, {str(uuid.uuid4()): now})
  r.expire(key, window)
  return True

# Streams (event log)
r.xadd("events", {"user": "alice", "action": "login"})
messages = r.xread({"events": "0-0"}, count=10)

```

### Node.js (ioredis)

```javascript
const Redis = require('ioredis');
const redis = new Redis({
  host: 'endpoint.cache.amazonaws.com',
  port: 6380,
  tls: {},
  maxRetriesPerRequest: 3,
  retryStrategy: (times) => Math.min(times * 50, 2000)
});

// Cache-Aside with promises
async function getUser(userId) {
  const cached = await redis.get(`user:${userId}`);
  if (cached) return JSON.parse(cached);
  
  const user = await fetchFromDB(userId);
  await redis.setex(`user:${userId}`, 1800, JSON.stringify(user));
  return user;
}

// Pub/Sub for notifications
redis.on('message', (channel, message) => {
  console.log(`${channel}: ${message}`);
});
redis.subscribe('notifications');

// Publish
redis.publish('notifications', 'User alice logged in');

// Redis Streams
await redis.xadd('orders', '*', 'user_id', 'alice', 'amount', '99.99');
const messages = await redis.xrange('orders', '-', '+', 'COUNT', 10);

```

---

## Common Failure Modes & Solutions

### 1. Cache Stampede (Thundering Herd)

**Problem**: Multiple requests miss cache simultaneously → all query DB → DB overload.

```

Time:    T0              T1              T2
         └─ User 1 → DB  └─ User 2 → DB  └─ User 3 → DB
         └─ User 4 → DB  └─ User 5 → DB  └─ ... (1000s)
         
Result: DB spike, timeouts, cascading failures

```

**Solution 1: Probabilistic early expiration**

```python
def smart_ttl(base_ttl=1800):
  return base_ttl * random.uniform(0.7, 1.0)  # Stagger expiration

redis.setex(key, smart_ttl(), value)

```

**Solution 2: Lease pattern**

```python
def get_with_lease(key):
  val = redis.get(key)
  if val:
    lease_time = redis.ttl(key)
    if lease_time < 300:  # < 5 minutes left
      trigger_background_refresh(key)  # Async refresh
    return val
  
  # Cache miss: fetch and set
  val = fetch_from_db()
  redis.setex(key, 1800, val)
  return val

```

### 2. Hot Partition (Single Shard Overload)

**Problem**: Uneven key distribution → one shard saturated, others idle.

```

Shard 1: User profiles (heavily accessed)
  CPU: 95%, Network: Saturated
  
Shard 2: Analytics (infrequently accessed)
  CPU: 5%, Network: 10%

```

**Root cause**: Hash slot allocation based on key.

**Solution 1: Add prefix to key**

```python
# Before (all same shard):
r.set("alice:profile", ...)
r.set("alice:history", ...)
r.set("alice:settings", ...)

# After (distributed across shards):
r.set(f"user:{random.randint(0,99):02d}:alice:profile", ...)

```

**Solution 2: Rebalance slots**

```bash
redis-cli --cluster rebalance endpoint:6379 --auto-weights

```

### 3. Memory Leak / OOM

**Problem**: Evictions spike, latency increases, replicas run OOM.

**Root causes**:
- Keys without TTL accumulating
- Unreleased connections holding memory
- Large values pushing exceeding maxmemory

**Debugging**:

```bash
redis-cli --latency           # Measure latency spikes
redis-cli memory doctor       # Analyze memory
redis-cli --bigkeys           # Find large keys
SLOWLOG GET 10               # Slow operations

```

**Fix**:

```python
# Set TTL on all keys
for key in redis.scan_iter():
  if redis.ttl(key) == -1:  # No TTL
    redis.expire(key, 86400)  # 24 hours

# Monitor evictions
if redis.info()['evicted_keys'] > 1000:
  scale_cluster()

```

### 4. Replication Lag During High Write Load

**Problem**: Replica falls behind primary → stale reads.

```

Primary: Receives 10,000 writes/sec
Replica: Falls 2-3 seconds behind
Clients reading from replica see stale data

```

**Solution**: Increase replication backlog

```bash
CONFIG SET repl-backlog-size 67108864  # 64 MB (default 1 MB)

```

### 5. Connection Pool Exhaustion

**Problem**: Clients hold all pool connections → others timeout.

**Solution**: Monitor and tune

```python
pool = redis.ConnectionPool(
  host='endpoint',
  max_connections=100,  # Increase from default 50
  socket_keepalive=True,
  socket_keepalive_options={
    1: (1, 3)  # (TCP_KEEPIDLE, TCP_KEEPINTVL)
  }
)

```

---

## Interview Questions

### 1. Design a rate limiter using Redis.

**Answer**: Use sorted sets with sliding window:
- Key: `ratelimit:{user_id}`
- Score: timestamp of each request
- Value: request UUID
- Remove expired entries: `ZREMRANGEBYSCORE key 0 (now - window)`
- Count current: `ZCARD key`
- Reject if count >= limit

Trade-off: Sorted set operations O(log N) per request. Alternative: Leaky bucket with `DECRBY` + `EXPIRE` (O(1) but less accurate).

### 2. Explain cache invalidation strategies. Which is hardest?

**Strategies**:
- **TTL**: Automatic expiration. Simple but risks stale data.
- **Event-based**: DB writes invalidate cache. Complex but accurate.
- **Conditional**: Check version/ETag. Balances both.

**Hardest**: Distributed event-based invalidation across multiple services. Requires event bus (Kafka), idempotent handlers, retry logic.

### 3. Your Redis cluster experiences sudden evictions. Diagnose.

**Investigation steps**:
1. Check memory usage: `INFO memory` → is `used_memory` near `maxmemory`?
2. Check evictions: `INFO stats` → compare `evicted_keys` trend.
3. Check hot keys: `redis-cli --hotkeys` or XREAD from `__keyevent__:evicted__` stream.
4. Check slow log: identify expensive operations.
5. Check network: `INFO stats` → `total_net_input_bytes`, `total_net_output_bytes`.

**Fix**:
- Increase `maxmemory` (vertical scale).
- Add shards (horizontal scale).
- Improve eviction policy from `allkeys-lru` to `allkeys-lfu` if hot/cold distribution.
- Add TTLs to transient keys.
- Reduce request rate (application level).

### 4. What's the difference between `WATCH` and Lua transactions?

**WATCH**: Optimistic locking. Aborts if watched key changed. Application must retry.

```redis
WATCH user:123
value = GET user:123
value = value + 1
MULTI
SET user:123 value
EXEC

```

**Lua**: Atomic server-side script. No conflicts. Must be idempotent.

```redis
EVAL "redis.call('INCR', KEYS[1])" 1 user:123

```

**Choose**:
- WATCH: When conflict expected to be rare.
- Lua: When conflicts common or operation complex.

---

## Simplest Mental Model

> **ElastiCache = whiteboard for notes to avoid library (DB) trips.**
>
> Cluster mode = multiple whiteboards (shards). Replication = copy notes to another room. RDB = photo of whiteboard. AOF = every pen stroke recorded. Eviction = which notes to erase when full. Streams = ticker tape of events. Pub/Sub = shout to everyone listening. Sorted sets = ranking board with scores.
>
> **Key rule**: caching helps only with high hit rate. Monitor CacheHits vs CacheMisses. Set TTLs. Choose right eviction policy. High miss rate = paying for a slow misdirection.
