# MongoDB Sharding: Design, Pitfalls & Production Scaling

## Shard Key Selection: The Most Important Decision

### What Makes a Good Shard Key?

A shard key determines:
1. **Data distribution** across shards
2. **Query routing** (which shards to scan)
3. **Scalability** (can you scale horizontally?)
4. **Write performance** (hot shards = bottleneck)

### Bad Shard Keys (Common Mistakes)

**Example 1: Ascending Timestamp (Sequential)**
```javascript
db.orders.createIndex({created_at: 1});
db.orders.enableSharding("ecommerce", {key: {created_at: 1}});

// Problem: All new writes go to SAME shard (latest timestamp)
// Shard 1: timestamp 2024-01-01 (cold, unused)
// Shard 2: timestamp 2025-01-01 (HOT, gets 100% of writes)
// Shard 3: timestamp 2025-02-01 (cold, empty)

// Write distribution: 1% / 1% / 98% (TERRIBLE!)
// Peak: one shard maxes out at 40KB/sec, entire cluster underutilized
// Expected: 100K writes/sec with 3 shards → Actual: 40K writes/sec (60% waste)
```

**Example 2: Low-Cardinality Field (Status)**
```javascript
db.orders.enableSharding("ecommerce", {key: {status: 1}});

// Problem: Only 4 possible values (pending, processing, shipped, cancelled)
// Shard 1: status = 'pending' (90% of data, HOT)
// Shard 2: status = 'processing' (5% of data)
// Shard 3: status = 'shipped' (5% of data)

// Data distribution: 90% / 5% / 5% (Jumbo chunk on shard 1)
// Can't auto-split (chunk > 16GB on status='pending')
// Write hotspot: all pending order writes hit shard 1
```

### Good Shard Keys (Production Examples)

**Example 1: Hashed Fields**
```javascript
db.users.enableSharding("app", {key: {user_id: "hashed"}});

// Data distribution: even (hashing distributes uniformly)
// Benefits:
// - No hot shards (each shard gets ~25% writes)
// - Scales linearly (add shard = 20% more throughput)
// - Data balanced automatically

// Downside: Range queries on user_id are scattered
SELECT * FROM users WHERE user_id BETWEEN 100 AND 200;
// Must query all 4 shards (slower than targeted query)
```

**Example 2: Compound Key (Locality + Distribution)**
```javascript
db.orders.enableSharding("ecommerce", {key: {customer_id: 1, created_at: -1}});

// Data distribution: by customer (hash-like)
// Benefits:
// - customer_id distributes evenly (each customer's orders on 1 shard usually)
// - created_at ranges efficiently within shard
// - Query "all orders for customer 100" = single shard (fast)

// Query pattern analysis:
// 80%: "Find customer's recent orders" → routed to 1 shard (5ms)
// 15%: "Orders by date range" → broadcast to all shards (100ms)
// 5%: "Popular customer (1B orders)" → shard overflow, needs sub-sharding

// Recommendation: Best for customer-centric data (orders, transactions)
```

---

## Query Routing & Targeting

### Targeted vs Broadcast Queries

```javascript
// Collection sharded by {customer_id: 1, created_at: -1}

// TARGETED (knows shard, routed to 1 shard):
db.orders.find({customer_id: 100, created_at: {$gt: ISODate("2025-01-01")}});
// Router: "customer_id 100 is on shard 2"
// Latency: 5-10ms (1 shard scanned)
// Efficiency: 100% (only necessary shard queried)

// BROADCAST (unknown shard, sent to all):
db.orders.find({status: "pending", created_at: {$gt: ISODate("2025-01-01")}});
// Router: "status not in shard key, unknown which shard"
// Latency: 50-200ms (all shards scanned, results merged)
// Efficiency: 25% (queried 4 shards, needed 1 average)

// PARTIAL BROADCAST (router optimizes):
db.orders.find({customer_id: 100, status: "pending"});
// Router: "customer_id determines shard 2, filter status on that shard"
// Latency: 10-20ms (1 shard + filter)
// Efficiency: 95% (single shard after routing)
```

### Query Router Performance

```javascript
// Slow query due to broadcast:
db.orders.find({status: "pending"}).limit(100);
// Must scan all shards, wait for slowest
// If one shard slow (network spike), entire query slow

// Better: Add customer context (if possible)
db.orders.find({customer_id: 100, status: "pending"}).limit(100);
// Targets single shard → fast even if other shards slow

// Lesson: App should pass shard key in queries when possible
```

---

## Rebalancing & Chunk Management

### Automatic Chunk Splitting

```
Initial state (1 shard, 5GB data):
[Shard1: Chunk A (5GB)]

Add shard:
[Shard1: Chunk A (5GB)] → [Shard2: waiting]

Auto-rebalance triggers:
1. Chunk > 16GB OR
2. Shard imbalance > 2 chunks

Split happens:
[Shard1: Chunk A (2.5GB)] → [Shard2: Chunk A' (2.5GB)]
[Shard1: Chunk B (2.5GB)] → migrate to Shard2

Performance during rebalance:
- Migration time: ~10-30s per 100MB chunk
- Latency spike: 50-100ms during migration window
- Cluster available: yes (migration in background)
- Client impact: slight latency increase, no errors
```

### Monitoring Rebalancing

```javascript
// Check shard sizes
db.adminCommand({balancer: {}});
// Returns: balancer state, chunk count per shard

// Find jumbo chunks (can't split):
db.getSiblingDB("config").chunks.find({jumbo: true});

// Example output:
// {_id: "app.orders-customer_id_1", min: {customer_id: ObjectId(...)}, jumbo: true}

// Fix: May need to re-shard with different key
// Lesson: Avoid shard keys that create jumbo chunks
```

---

## Hot Shard Problem & Solutions

### Detecting Hot Shards

```javascript
// Check write distribution
db.adminCommand({shardConnPoolStats: {}});
// Returns: connection count per shard
// Uneven connections = some shards receiving more traffic

// Example of hot shard:
// Shard1: 100 connections (hot)
// Shard2: 30 connections
// Shard3: 25 connections
// Total: 100 write capacity wasted, bottleneck at 40KB/sec

// Check operation distribution
db.adminCommand({top: 1});
// Shows ops per shard
```

### Solution 1: Sub-Sharding (App-Level)

```javascript
// Problem: One customer (leaderboard game) gets 100K updates/sec
// Shard key: {game_id: 1, tier: 1} still creates hot shard

// Solution: Distribute within app
function getShardKeyForGame(gameId, tierId) {
  const subShard = Math.floor(Math.random() * 10);  // 0-9
  return {game_id: gameId, tier: tierId, shard_id: subShard};
}

// Instead of 1 document per game/tier, create 10 (one per sub-shard)
// Game "id=1, tier=gold" → 10 documents (sub_0 to sub_9)
// Updates: spread across 10 docs, distribute write load 10x

// Read: sum across 10 documents
db.leaderboard.aggregate([
  {$match: {game_id: 1, tier: "gold"}},
  {$group: {_id: "$game_id", total_score: {$sum: "$score"}}}
]);
```

### Solution 2: Write Caching + Async Batch

```javascript
// For frequent updates to same document:
// Instead of: 100K/sec direct MongoDB writes
// Use: Local cache + batch update every 1 second

// In-app cache:
const scoreCache = {};  // {userId: score}

// Update (fast, in-memory):
scoreCache[userId] += points;

// Batch to MongoDB every second:
setInterval(() => {
  const updates = Object.entries(scoreCache);
  scoreCache = {};  // Reset cache
  
  // Batch write (much fewer DB writes):
  updates.forEach(([userId, score]) => {
    db.leaderboard.updateOne(
      {_id: userId},
      {$inc: {score: score}}
    );
  });
}, 1000);

// Result: 100K ops/sec → 10-20 batch writes/sec to MongoDB
// Throughput: limited by batch size, not shard capacity
```

---

## Real-World Scenarios

### Scenario 1: E-Commerce 500M Orders

```javascript
// Requirements:
// - 50K new orders/sec peak
// - Queries: "customer's orders", "orders by date"
// - Retention: keep 2 years (1B total)

// Shard key choice:
db.orders.enableSharding("shop", {key: {customer_id: 1, created_at: -1}});

// Why this key:
// - customer_id: evenly distributed, no hot shards
// - created_at: range queries efficient within shard
// - Together: "customer's recent orders" = single shard (fast)

// Capacity planning:
// 50K orders/sec / 10 shards = 5K orders/sec per shard
// Per shard capacity: 40KB/sec per MongoDB instance
// Estimated size per order: 500 bytes
// 5K ops/sec × 500 bytes = 2.5MB/sec ✓ (within capacity)

// Storage planning:
// 500M orders × 500 bytes = 250GB total
// With replication factor 3: 750GB across cluster
// 10 shards × 3 replicas = 30 nodes needed
// 750GB / 30 nodes = 25GB per node ✓

// Index strategy:
db.orders.createIndex({customer_id: 1, created_at: -1});
// This is your shard key index

db.orders.createIndex({status: 1, created_at: -1});
// For "pending orders in date range" (broadcast query)

// Query examples:
// Fast (targeted):
db.orders.find({customer_id: 100}).sort({created_at: -1}).limit(20);
// Latency: 5-10ms

// Slower (broadcast):
db.orders.find({status: "shipped", created_at: {$gt: ISODate("2025-01-01")}});
// Latency: 100-200ms (all shards)
```

### Scenario 2: Gaming Leaderboard 1B Scores

```javascript
// Requirements:
// - 500K score updates/sec (very high write volume)
// - Queries: "top 100", "player rank", "friends ranks"
// - Retention: current season only (3 months)

// Challenge: Some games popular (100M scores/hour), others niche (1K scores/hour)
// Uneven distribution!

// Shard key strategy:
db.scores.enableSharding("game", {key: {game_id: 1, tier: "hashed"}});

// Why:
// - game_id: popular games might be hot, tier distributes within game
// - hashed tier: prevents jumbo chunks on specific tier

// Sub-sharding for hot games:
function getScoreKey(gameId, tier, playerId) {
  const isHotGame = ["game_A", "game_B"].includes(gameId);
  if (isHotGame) {
    const subShard = playerId % 10;  // Distribute 10 ways
    return {game_id: gameId, tier: tier, shard_num: subShard, player_id: playerId};
  }
  return {game_id: gameId, tier: tier, player_id: playerId};
}

// Storage:
// 1B scores × 100 bytes = 100GB
// With replication 3: 300GB
// 5 shards × 3 replicas = 15 nodes
// 300GB / 15 = 20GB per node ✓

// Write distribution:
// Hot game (100K scores/sec): distributed to 5 shards × 10 sub-shards = 50 shards
// 100K / 50 = 2K writes/sec per effective shard ✓

// Monitoring:
// Alert if: shard imbalance > 10GB
// Alert if: chunk count on one shard > 100
```

---

## Troubleshooting Guide

### Problem: One Shard Much Larger than Others

```javascript
// Check shard sizes
db.adminCommand({shardConnPoolStats: {}});

// Likely cause: bad shard key (hot shard)
// Solution: re-shard with better key (expensive operation)

// Temporary fix: Add more replicas to hot shard
db.adminCommand({addShard: "shard1_replica:27018"});
// Distributes reads to replicas, not writes
```

### Problem: Queries Suddenly Slow

```javascript
// Possible cause: broadcast queries (no shard key)
// Check slow log:
db.adminCommand({getLog: "global"});
// Look for: queries scanning multiple shards

// Fix: Refactor queries to include shard key
// Before: find({status: "pending"})  // Broadcast
// After: find({customer_id: X, status: "pending"})  // Targeted
```

### Problem: Chunk Rebalancing Won't Stop

```javascript
// Check for jumbo chunks:
db.getSiblingDB("config").chunks.count({jumbo: true});

// If many jumbo chunks:
// Root cause: shard key creates uneven chunks
// Solution: Re-shard collection (backup, shard key change, restore)
// This is expensive but necessary
```

---

## Performance Checklist

- ✓ Choose shard key carefully (evenly distributes, supports queries)
- ✓ Test query patterns before sharding (make sure key works)
- ✓ Monitor shard sizes (alert if imbalance > 10%)
- ✓ Monitor hot shards (connection count per shard)
- ✓ For hot data, use sub-sharding or write caching
- ✓ For broadcast queries, accept 100ms+ latency or refactor
- ✓ Create covering indexes on common query patterns
- ✓ Plan for growth (estimate peak writes, bytes/doc, retention)
- ✓ Use hashed sharding for even distribution (if range queries ok)
- ✓ Avoid sequential/timestamp shard keys (creates hot shards)

---

**Summary:**
- **Shard key = everything**: determines performance, scalability, query efficiency
- **Good keys**: distributed uniformly, support query patterns, no hotspots
- **Bad keys**: sequential (timestamp), low-cardinality (status), uneven (some customers huge)
- **Query routing**: Targeted (shard key in query) = 5-10ms, Broadcast (no shard key) = 50-200ms
- **Scaling**: Add shard → auto-rebalance, chunks split, load distributed
- **Hot shards**: Sub-shard (10x distribution), or write caching + async batch
