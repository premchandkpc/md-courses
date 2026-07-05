# 07-Redis

An in-memory data structure store used as a cache, message broker, and database. Redis supports strings, hashes, lists, sets, sorted sets, streams, and more, all with sub-millisecond latency. It is the most widely used caching and session store in microservices.

## Overview
Redis keeps data in RAM, which makes reads and writes extremely fast (measured in microseconds). It persists data to disk via snapshots (RDB) or append-only files (AOF) for durability, but is primarily valued for speed over persistence. Redis supports atomic operations on data structures (INCR, LPUSH, SADD), Lua scripting for server-side logic, and built-in replication with Redis Sentinel for automatic failover. For larger deployments, Redis Cluster shards data across nodes with automatic failover.

## Key Characteristics
- **Data structures as primitives**: Strings (caching), Lists (queues), Sets (tags, dedup), Sorted Sets (leaderboards, rate limiting), Hashes (objects), Streams (event logs). Each supports atomic operations.
- **Pub/Sub and streams**: Redis Pub/Sub provides fire-and-forget messaging. Redis Streams offer persistent, consumer-group-based message consumption similar to Kafka.
- **TTL and eviction**: Keys can have time-to-live for automatic expiration. Eviction policies (allkeys-lru, volatile-lru, allkeys-lfu) manage memory.
- **Sentinel for HA**: Redis Sentinel monitors the primary, performs automatic failover, and provides service discovery to clients.
- **Redis Cluster**: Data is sharded across nodes (16384 hash slots). Clients connect to any node, which proxies to the correct shard.
- **Not a primary database**: Redis is an in-memory system — data loss is possible if not properly configured. It complements rather than replaces relational databases.

## Why It Matters
Redis is the Swiss Army knife of microservices infrastructure. It handles caching (the most common use), session storage for stateless services, rate-limit counters, distributed locks (Redlock algorithm), real-time leaderboards, and simple message queuing. Nearly every production microservices deployment includes at least one Redis instance.

## Related Concepts
- [Caching](06-Caching.md) — Redis's primary use case; cache-aside and write-through patterns
- [Replication](05-Replication.md) — Redis replication with Sentinel ensures high availability
- [Sharding](03-Sharding.md) — Redis Cluster uses hash-slot-based sharding for horizontal scaling

---

## Mental Model
A whiteboard in the office that everyone can read and write to instantly. Notes appear in milliseconds. The whiteboard has limited space (RAM) — when full, old notes get erased (eviction). Someone takes a photo (RDB snapshot) every hour for recovery, but the current state is always what's on the whiteboard.
