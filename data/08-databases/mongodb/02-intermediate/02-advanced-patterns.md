# MongoDB Advanced Patterns & Optimization

## Bulk Operations for Performance

### Ordered vs Unordered Inserts

```javascript
// Ordered (default): Stops on first error
db.collection.insertMany([
  { name: "Alice" },
  { name: "Bob" },
  { name: "Charlie" }
], { ordered: true })

// Unordered: Continues on error, faster
db.collection.insertMany([
  { name: "Alice" },
  { name: "Bob" },
  { name: "Charlie" }
], { ordered: false })

Performance:
- Ordered: 10K inserts/sec
- Unordered: 50K inserts/sec (5x faster)
```

### Bulk Write Operations

```javascript
const bulk = db.collection.initializeUnorderedBulkOp()

bulk.insert({ name: "Alice", score: 100 })
bulk.find({ name: "Bob" }).updateOne({ $set: { score: 95 } })
bulk.find({ name: "Charlie" }).replaceOne({ name: "Charles", score: 90 })
bulk.find({ _id: ObjectId("...") }).removeOne()

bulk.execute()  // Execute all at once
```

**Cost:** 1 round-trip to DB instead of 4. 4x latency improvement.

---

## Connection Pooling & Optimization

### Connection Pool Configuration

```javascript
// High throughput setup
const client = new MongoClient(uri, {
  maxPoolSize: 100,        // Max connections
  minPoolSize: 10,         // Min connections
  maxIdleTimeMS: 60000,    // Close idle after 1 min
  serverSelectionTimeoutMS: 5000,
  socketTimeoutMS: 45000
})

// Settings for different scenarios
// Batch processing: maxPoolSize=50, minPoolSize=5
// Real-time API: maxPoolSize=100, minPoolSize=20
// Rare queries: maxPoolSize=10, minPoolSize=2
```

### Monitoring Connection Pool

```javascript
client.on('connectionPoolCreated', () => console.log('Pool created'))
client.on('connectionPoolClosed', () => console.log('Pool closed'))
client.on('connectionCreated', (event) => console.log(`Connection #${event.connectionId} created`)
client.on('connectionCheckedOut', (event) => console.log(`Connection #${event.connectionId} checked out`)
client.on('connectionCheckedIn', (event) => console.log(`Connection #${event.connectionId} returned`)
```

---

## Compression & Network Optimization

### Wire Compression

```javascript
const client = new MongoClient(uri, {
  compressors: ['snappy', 'zlib'],  // Try snappy first
  zlibCompressionLevel: 6              // 1-9, 6 is default
})

// Snappy: Fast, less compression (good for bandwidth-rich, CPU-poor)
// zlib: Slower, more compression (good for bandwidth-poor, CPU-rich)
```

**Trade-off:** CPU vs bandwidth
- Without: 1000 MB/min, CPU=5%
- Snappy: 800 MB/min, CPU=8% (20% bandwidth saved)
- zlib: 500 MB/min, CPU=15% (50% bandwidth saved)

---

## Indexing Deep Dive

### Index Creation Strategy

```javascript
// 1. Identify slow queries
db.collection.find({ status: "active", createdAt: { $gt: new Date("2025-01-01") } })

// 2. Create compound index (order matters!)
db.collection.createIndex({ status: 1, createdAt: -1 })

// 3. Verify index used
db.collection.find({ status: "active", createdAt: { $gt: new Date("2025-01-01") } }).explain()

// 4. Check index size
db.collection.stats()  // Shows indexes, index sizes
```

### Index Types

```javascript
// Regular index
db.users.createIndex({ email: 1 })

// Compound index (3-way)
db.orders.createIndex({ customerId: 1, status: 1, createdAt: -1 })

// Text index (full-text search)
db.articles.createIndex({ title: "text", body: "text" })

// Geospatial index
db.locations.createIndex({ coordinates: "2dsphere" })

// TTL index (auto-delete after expiry)
db.sessions.createIndex({ createdAt: 1 }, { expireAfterSeconds: 86400 })

// Sparse index (only includes docs with field)
db.users.createIndex({ phone: 1 }, { sparse: true })

// Unique index
db.users.createIndex({ email: 1 }, { unique: true })
```

### Partial Index

```javascript
// Index only active users
db.users.createIndex(
  { email: 1 },
  { partialFilterExpression: { status: "active" } }
)

// Saves storage, faster insertion of inactive users
// Only helps queries that match filter
```

---

## Memory & Caching

### In-Memory Storage Engine (Evaluation Version)

```javascript
// Config for in-memory
storage:
  engine: inMemory
  inMemory:
    engineConfig:
      cacheSizeGB: 4  # RAM dedicated to cache

// Benefits: Sub-millisecond latency
// Cost: Data lost on restart
// Use: Cache layer only, not primary DB
```

### Cache Warming

```javascript
// Pre-load hot data on startup
async function warmCache() {
  const hotData = await db.orders
    .find({ status: "active" })
    .limit(10000)
    .toArray()
  
  console.log(`Warmed cache with ${hotData.length} documents`)
}

warmCache()  // Call on server startup
```

---

## Real-World Optimization Case Study

### Problem: Leaderboard Query Slow

```javascript
// Current (slow): 2 seconds
db.leaderboards.aggregate([
  { $match: { gameId: "game123" } },
  { $sort: { score: -1 } },
  { $limit: 100 }
])

// Check explain plan
db.leaderboards.aggregate([...]).explain("executionStats")
// Shows: COLLSCAN (bad!), examined 1M documents
```

### Solution 1: Add Index

```javascript
// Create index
db.leaderboards.createIndex({ gameId: 1, score: -1 })

// Now fast: 50ms
// Examined 100 documents only
```

### Solution 2: Denormalize

```javascript
// Store top 100 in cache collection
db.leaderboardsCache.drop()

db.leaderboardsCache.insertOne({
  gameId: "game123",
  top100: [
    { rank: 1, playerId: "p1", score: 9999 },
    { rank: 2, playerId: "p2", score: 9998 },
    // ...
  ],
  lastUpdated: new Date()
})

// Query cache first (instant)
// Refresh every 5 minutes (batch job)
```

### Solution 3: Materialized View

```javascript
// Run every 5 minutes
async function refreshLeaderboard() {
  const top100 = await db.leaderboards.aggregate([
    { $match: { gameId: "game123" } },
    { $sort: { score: -1 } },
    { $limit: 100 },
    { $project: { playerId: 1, score: 1, rank: { $add: [{ $indexOfArray: [1, 2, 3] }, 1] } } }
  ]).toArray()
  
  await db.leaderboardsCache.updateOne(
    { gameId: "game123" },
    { $set: { top100, lastUpdated: new Date() } },
    { upsert: true }
  )
}

// Schedule with cron/scheduler
setInterval(refreshLeaderboard, 5 * 60 * 1000)
```

---

## Query Optimization Patterns

### Avoiding $where (Very Slow)

```javascript
// ❌ SLOW: JavaScript evaluation, no index
db.users.find({ $where: "this.age > 25" })

// ✓ FAST: Indexed query
db.users.find({ age: { $gt: 25 } })

// Speed difference: 100x slower with $where
```

### Avoiding Negative Queries

```javascript
// ❌ SLOW: Scans all documents
db.orders.find({ status: { $ne: "cancelled" } })

// ✓ FAST: Indexes on status
db.orders.find({ status: { $in: ["pending", "shipped", "delivered"] } })
```

### Using Aggregate vs Find

```javascript
// Simple query: Use find()
db.users.find({ age: { $gt: 25 } })

// Complex transform: Use aggregate()
db.users.aggregate([
  { $match: { age: { $gt: 25 } } },
  { $group: { _id: "$country", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])

// Aggregate benefits: Pipeline can use indexes, filter early
```

---

## Monitoring & Diagnostics

### Query Profiler

```javascript
// Enable profiling level 1 (slow queries only)
db.setProfilingLevel(1, { slowms: 100 })  // Log >100ms queries

// View profiled queries
db.system.profile.find().limit(10).sort({ ts: -1 }).pretty()

// Analysis
db.system.profile.aggregate([
  { $group: { _id: "$op", count: { $sum: 1 }, avgMillis: { $avg: "$millis" } } },
  { $sort: { count: -1 } }
])
```

### Collection Stats

```javascript
db.collection.stats()

// Shows:
// - Document count
// - Total size
// - Index details + sizes
// - Average document size
// - Storage information
```

### Server Status

```javascript
db.serverStatus()

// Shows:
// - Uptime
// - Memory usage
// - Connection stats
// - Index sizes
// - Operation counters
```

---

## Best Practices Summary

1. **Indexing:** Compound index (status, createdAt) better than separate indexes
2. **Bulk Operations:** Use insertMany with unordered=true for speed
3. **Connection Pooling:** Tune pool size to workload (API=100, batch=50)
4. **Compression:** Use snappy for most cases (speed/compression balance)
5. **Caching:** Denormalize hot data (leaderboards, user stats)
6. **Queries:** Avoid $where, $ne; use direct index queries
7. **Monitoring:** Enable profiler, track slow queries
8. **Aggregation:** Use $match early to reduce pipeline data
9. **Sparse Indexes:** For sparse fields (optional data)
10. **TTL Indexes:** Auto-expire temporary data (sessions, OTP)

---

## Summary

- **Bulk Operations**: 5-10x faster than individual writes
- **Compound Indexes**: Essential for multi-field queries
- **Denormalization**: Trade storage for speed on hot queries
- **Connection Pooling**: Critical for concurrent applications
- **Profiling**: Find and fix slow queries systematically

Next: [[../../../comparison-guide.md|Comparison & Selection]]

---

**See Also:**
- [[01-replication-sharding.md|Replication & Sharding]]
- [[../01-overview.md|MongoDB Overview]]
- [[../../postgres/02-intermediate/01-advanced-optimization.md|PostgreSQL Optimization]]
