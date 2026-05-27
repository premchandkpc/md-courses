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

## Simplest Mental Model

> **ElastiCache = whiteboard for notes to avoid library (DB) trips.**
>
> Cluster mode = multiple whiteboards (shards). Replication = copy notes to another room. RDB = photo of whiteboard. AOF = every pen stroke recorded. Eviction = which notes to erase when full. Streams = ticker tape of events. Pub/Sub = shout to everyone listening. Sorted sets = ranking board with scores.
>
> **Key rule**: caching helps only with high hit rate. Monitor CacheHits vs CacheMisses. Set TTLs. Choose right eviction policy. High miss rate = paying for a slow misdirection.
