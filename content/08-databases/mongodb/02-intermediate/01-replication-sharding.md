# MongoDB Replication, Sharding & Scaling

## Replica Sets (High Availability)

Multiple servers with automatic failover.

### Architecture

```
Primary (writes)
   ↓ (replication)
   ├→ Secondary 1 (reads)
   └→ Secondary 2 (reads)
   
   If primary fails:
   → Automatic election
   → One secondary becomes primary
   → No manual intervention
```

### Setup

```javascript
// Start 3 servers
mongod --replSet rs0 --port 27017

// Initialize replica set
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "server1:27017", priority: 2 },
    { _id: 1, host: "server2:27017", priority: 1 },
    { _id: 2, host: "server3:27017", priority: 1 }
  ]
})

// Check status
rs.status()
// Shows: primary, secondary, secondary status
```

### Write Concern

```javascript
// Acknowledge level for writes
db.collection.insertOne(
  { name: "Alice" },
  { writeConcern: { w: 1 } }  // Wait for primary
)

db.collection.insertOne(
  { name: "Alice" },
  { writeConcern: { w: 3 } }  // Wait for 3 servers (slower)
)

db.collection.insertOne(
  { name: "Alice" },
  { writeConcern: { w: "majority" } }  // Majority of replicas
)
```

### Read Preference

```javascript
// Read from secondary (avoid overloading primary)
db.collection.find()
  .readPreference("secondary")

// Read from nearest (lowest latency)
db.collection.find()
  .readPreference("nearest")

// Read from primary only (for consistent reads)
db.collection.find()
  .readPreference("primary")  // Default
```

---

## Sharding (Horizontal Scaling)

Distribute data across multiple servers.

### Shard Key Selection

```javascript
// Shard key: determines which shard holds data

// ❌ Bad: Low cardinality (few distinct values)
// Shard key: gender (M, F, unknown)
// Result: All males go to shard1, all females to shard2
// Imbalanced!

// ❌ Bad: Monotonically increasing
// Shard key: timestamp
// Result: Old data idle on shard1, new data hotspotted on shard2
// Sequential writes to same shard

// ✓ Good: High cardinality, well-distributed
// Shard key: userId (millions of distinct values)
// Result: Evenly distributed across shards

// ✓ Good: Compound key
// Shard key: customerId, orderId
// Result: All customer orders together, distributed globally
```

### Setup

```javascript
// 1. Enable sharding on database
sh.enableSharding("ecommerce")

// 2. Shard collection
sh.shardCollection("ecommerce.orders", { customerId: 1 })

// 3. Create index on shard key
db.orders.createIndex({ customerId: 1 })

// Data automatically distributed:
// Shard1: customerId 0-1M
// Shard2: customerId 1M-2M
// Shard3: customerId 2M-3M
```

### Monitoring Sharding

```javascript
// Check shard status
sh.status()

// Shows:
// - Shard servers
// - Databases and collections
// - Chunk distribution
// - Balancer status

// Check chunk count per shard (should be balanced)
db.adminCommand({ getShardVersion: "ecommerce.orders" })

// Manual balancing
sh.startBalancer()
sh.stopBalancer()
```

---

## Replication + Sharding Combined

```
Sharded Cluster:
├─ Shard 1 (Replica set)
│  ├─ Primary
│  ├─ Secondary
│  └─ Secondary
├─ Shard 2 (Replica set)
│  ├─ Primary
│  ├─ Secondary
│  └─ Secondary
└─ Shard 3 (Replica set)
   ├─ Primary
   ├─ Secondary
   └─ Secondary

Plus:
- Config servers (metadata)
- Mongos routers (query routing)
```

---

## Real-World Scaling Scenario

### Problem: Database at Capacity

```
Single server:
- 500GB data
- 100K ops/second
- 80% CPU
- Disk full soon

Solution: Shard
```

### Migration Steps

```javascript
// 1. Plan: Choose shard key
// customerId - good cardinality, often queried

// 2. Enable sharding
sh.enableSharding("app")
sh.shardCollection("app.orders", { customerId: 1 })

// 3. Pre-split chunks (avoid initial imbalance)
for (let i = 1; i <= 1000; i++) {
  sh.splitFind("app.orders", { customerId: i })
}

// 4. Monitor migration
while (true) {
  let status = sh.status()
  console.log(status)
  // Watch chunks move to other shards
}

// 5. Rebalance complete when balanced
```

### Performance After Sharding

```
Before:
- Single server: 100K ops/sec
- CPU: 80% (bottleneck)
- Disk: 500GB

After (3 shards):
- Combined: 300K+ ops/sec (3x capacity)
- Each shard ~33% CPU
- Data: ~167GB per shard
```

---

## Backup & Recovery

### Snapshot Backup (All Shards)

```bash
# Backup all shards simultaneously
for shard in shard1 shard2 shard3; do
  mongodump --host=$shard --out=backup_$(date +%s)/$shard &
done
wait

# Aggregate all shards
tar czf backup.tar.gz backup_*/
```

### Point-in-Time Recovery

```bash
# If replica sets have oplog:
mongorestore --host rs0 backup/
```

---

## Transaction Support

### Multi-Shard Transactions (4.2+)

```javascript
const session = db.getMongo().startSession()

try {
  session.startTransaction()
  
  // Write to orders (shard1)
  db.orders.updateOne(
    { _id: 1 },
    { $set: { status: "paid" } },
    { session }
  )
  
  // Write to payments (shard2)
  db.payments.insertOne(
    { orderId: 1, amount: 100 },
    { session }
  )
  
  session.commitTransaction()
} catch (error) {
  session.abortTransaction()
  throw error
} finally {
  session.endSession()
}
```

**Important:** Slower than single-shard (coordination overhead)

---

## Common Sharding Issues

### Hotspot Shard

```javascript
// Problem: One shard gets 90% traffic

// Check chunk distribution
db.chunks.aggregate([
  { $group: { _id: "$shard", count: { $sum: 1 } } }
])

// If imbalanced: Bad shard key choice
// Solution: Reshard with different key
```

### Uneven Distribution

```javascript
// Example: Shard key = region (4 values)
// Shard1: North America (50M docs)
// Shard2: Europe (40M docs)
// Shard3: Asia (45M docs)
// Shard4: Other (2M docs)

// Solution: Compound key
// Shard key: region, customerId
// Much more balanced distribution
```

---

## Cost Analysis

```
Single server (non-sharded):
- 1 MongoDB instance: $300/month (Atlas)
- Storage: 500GB
- High availability: Add secondary = $600/month

Sharded cluster:
- 3 shards × $300 = $900/month
- 3 replicas per shard = $900/month
- Config servers = $100/month
- Total: ~$1900/month

But:
- 3x capacity (300K ops/sec)
- Automatic failover
- Can add shards later

ROI: Worth for 200K+ ops/sec, 200GB+
```

---

## Migration from Single Server

```javascript
// Gradual migration

// Phase 1: Add secondary
rs.addArb("server2:27017")  // Replica set

// Phase 2: Enable sharding
sh.enableSharding("app")
sh.shardCollection("app.orders", { customerId: 1 })

// Phase 3: Add shards (one at a time)
sh.addShard("server3:27017")
sh.addShard("server4:27017")

// Phase 4: Monitor balancing
sh.status()

// Phase 5: Decommission old server
// Shard has been emptied automatically
// Safe to remove
```

---

## Monitoring Sharded Clusters

```javascript
// Shard status
sh.status()

// Chunk distribution
db.chunks.find({ ns: "app.orders" }).count()

// Balancer status
sh.getBalancerState()
sh.isBalancerRunning()

// Config server status
db.adminCommand({ getCmdLineOpts: 1 })

// Performance
db.getProfilingLevel()
db.setProfilingLevel(1)  // Log slow queries
```

---

## Best Practices

1. **Choose shard key carefully** - Cannot change later without resharding
2. **High cardinality** - Millions of distinct values
3. **Distributed** - Avoid monotonic sequences
4. **Query patterns** - If always by userId, use userId
5. **Monitor balance** - Keep chunks evenly distributed
6. **Replica sets** - Always use for HA within shard
7. **Backup early** - Plan backup strategy before sharding
8. **Test capacity** - Know limits before hitting them

---

## Summary

- **Replica Sets**: High availability, automatic failover
- **Sharding**: Horizontal scaling, data distribution
- **Write Concern**: Control write acknowledgment level
- **Read Preference**: Route reads to secondaries
- **Shard Key**: Critical choice, high cardinality needed
- **Monitoring**: Track chunk distribution, balancer
- **Transactions**: Multi-shard supported but slower
- **Migration**: Gradual from single to sharded

Next: [[02-advanced-patterns.md|Advanced Patterns & Optimization]]

---

**See Also:**
- [[01-overview.md|MongoDB Overview]]
- [[02-aggregation-advanced.md|Aggregation Pipeline]]
- [[../../mysql/02-intermediate/02-replication-ha.md|MySQL Replication]]
- [[../../dynamodb/06-scaling/01-global-tables.md|DynamoDB Global Tables]]
