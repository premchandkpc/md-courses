# Topic 11: Sharding & Distributed Databases

[🎨 Interactive Visualization](../../html/11-database-sharding-viz.html)

**Level:** Advanced | **Time:** 60 mins | **Production Critical:** ⭐⭐⭐⭐

---

## Overview

Sharding = splitting a large dataset across multiple databases (shards) to scale horizontally. Problem: A single database can only scale vertically (bigger server). Solution: Shard data so each database holds a subset, distributing load. This guide covers sharding strategies, hash-based vs range-based sharding, hot-spot handling, and cross-shard joins.

**Why this matters:**
- Twitter: 100B+ tweets, sharded by user_id (can't fit on 1 server)
- Uber: Sharded by city_id (geographically local)
- Interview prep: "How would you shard a 10TB table across 100 databases?"
- Common pitfall: Poor shard key choice leads to unbalanced distribution

**Key metrics:**
- **Data skew:** Uneven distribution across shards (goal: < 10% variance)
- **Shard hotspot:** One shard handles 90% of traffic (bad)
- **Cross-shard queries:** Queries hitting multiple shards (slow, complex)

---

## 1. Sharding Strategies

### Strategy 1: Hash-Based Sharding (Most Common)

Hash the shard key, modulo number of shards.

```
Shard key: user_id
Number of shards: 4

hash(user_id) % 4 = shard_number

user_id=123   → hash(123) % 4 = 0 → Shard 0
user_id=456   → hash(456) % 4 = 2 → Shard 2
user_id=789   → hash(789) % 4 = 1 → Shard 1
user_id=1000  → hash(1000) % 4 = 3 → Shard 3

Result: Uniform distribution across shards
```

**Pros:**
- Uniform distribution (balanced load)
- Deterministic (same user_id always on same shard)
- Easy to implement

**Cons:**
- Adding/removing shards requires reshuffling (expensive)
- Can't query range (e.g., users created between date1-date2)

**Implementation**
```javascript
// Shard router
class ShardRouter {
  constructor(numShards) {
    this.numShards = numShards;
    this.shards = Array(numShards)
      .fill(null)
      .map((_, i) => new Database(`shard-${i}.example.com`));
  }

  getShardId(userId) {
    return hashCode(userId) % this.numShards;
  }

  getShard(userId) {
    const shardId = this.getShardId(userId);
    return this.shards[shardId];
  }

  async query(sql, params, userId) {
    const shard = this.getShard(userId);
    return shard.query(sql, params);
  }
}

// Usage
const router = new ShardRouter(4);

// Insert user on correct shard
await router.query(
  'INSERT INTO users VALUES ($1, $2)',
  [userId, name],
  userId
);

// Query on correct shard (fast, single-shard query)
const user = await router.query(
  'SELECT * FROM users WHERE id = $1',
  [userId],
  userId
);
```

---

### Strategy 2: Range-Based Sharding

Divide key range into ranges, each shard handles a range.

```
Shard key: user_id
Shard ranges:

Shard 0: user_id 1-1M
Shard 1: user_id 1M-2M
Shard 2: user_id 2M-3M
Shard 3: user_id 3M-4M

user_id=500K    → Shard 0
user_id=1.5M    → Shard 1
user_id=2.5M    → Shard 2
user_id=3.5M    → Shard 3
```

**Pros:**
- Range queries work (users 1M-2M live on Shard 1)
- Easy to add shards (just extend range)
- Can read multiple shards for range query (slower but works)

**Cons:**
- Unbalanced distribution (if user_ids not evenly distributed)
- Hot spot: If all active users in range 1M-2M, Shard 1 overloaded

**Example: Time-Based Sharding (High Volume Data)**
```
Shard key: timestamp
Shard 0: Jan 2026
Shard 1: Feb 2026
Shard 2: Mar 2026

logs table (1TB/month):
  Jan logs → Shard 0 (400GB)
  Feb logs → Shard 1 (300GB)
  Mar logs → Shard 2 (350GB)

Query: "Get logs from Feb"
  → Only hit Shard 1 (fast)

Query: "Get logs from entire Q1"
  → Hit all 3 shards (multi-shard query, slower)
```

---

### Strategy 3: Directory-Based Sharding

Maintain lookup table: shard_key → shard_id.

```
Shard key: user_id
Lookup table (ShardDirectory):

user_id  | shard_id
---------|----------
123      | 0
456      | 2
789      | 1
1000     | 3

To find shard: SELECT shard_id FROM shard_directory WHERE user_id = 123;
Result: Shard 0
```

**Pros:**
- Flexible (can rebalance without reshuffling)
- Easy to move data (just update directory)
- No hash function needed

**Cons:**
- Additional lookup (1 extra query per request)
- Directory becomes bottleneck (must cache)
- Maintenance burden

**Implementation**
```javascript
class ShardDirectory {
  constructor(dbConnection) {
    this.db = dbConnection;
    this.cache = new Map(); // Local cache
  }

  async getShardId(userId) {
    // Check cache first
    if (this.cache.has(userId)) {
      return this.cache.get(userId);
    }

    // Query directory
    const result = await this.db.query(
      'SELECT shard_id FROM shard_directory WHERE user_id = $1',
      [userId]
    );

    if (!result.rows.length) {
      // New user, assign to balanced shard
      const shardId = await this.findBalancedShard();
      await this.db.query(
        'INSERT INTO shard_directory (user_id, shard_id) VALUES ($1, $2)',
        [userId, shardId]
      );
      this.cache.set(userId, shardId);
      return shardId;
    }

    const shardId = result.rows[0].shard_id;
    this.cache.set(userId, shardId);
    return shardId;
  }

  async findBalancedShard() {
    // Find shard with lowest user count
    const result = await this.db.query(
      'SELECT shard_id, COUNT(*) as user_count FROM shard_directory GROUP BY shard_id ORDER BY user_count ASC LIMIT 1'
    );
    return result.rows[0].shard_id;
  }
}
```

---

## 2. Shard Key Selection (Critical)

Bad shard key = disaster. Good shard key = uniform distribution + queryability.

### Bad Shard Keys

```javascript
// ❌ BAD: customer_country
// Problem: USA 80% of traffic, other countries 20%
// Result: USA shard overloaded

// ❌ BAD: timestamp
// Problem: Current month shard gets all writes
// Result: Hot shard, older shards cold/wasted

// ❌ BAD: status (active/inactive)
// Problem: 70% active, 30% inactive
// Result: Active shard 70% of data, inactive 30%

// ✅ GOOD: user_id (uniform, deterministic)
// Problem: None (hash distributes evenly)
// Result: All shards balanced
```

### Choosing Shard Key

```
Criteria:
1. High cardinality: Many unique values (user_id >> status)
2. Uniform distribution: Even spread (not skewed)
3. Queryable: Can find data by key
4. Immutable: Don't change after insert
5. Non-temporal: Don't cluster time (hot-shard problem)

Examples:
✅ user_id (high cardinality, uniform, immutable)
✅ tenant_id (multi-tenant app, uniform)
✅ organization_id (consistent access pattern)
❌ is_active (low cardinality, skewed)
❌ created_at (temporal, causes hot-shard)
```

---

## 3. Cross-Shard Operations (The Problem)

Most operations need single-shard access (fast). Some need multiple shards (slow).

```
Single-shard query (FAST):
  SELECT * FROM users WHERE user_id = 123;
  → Shard 0 only

Cross-shard query (SLOW):
  SELECT * FROM users WHERE country = 'USA';
  → Need to query all 4 shards, merge results, network latency 4x

Worst case (very slow):
  SELECT COUNT(*) FROM users;
  → Query all shards, sum results (4 network requests)
```

### Handling Cross-Shard Queries

**Option 1: Avoid (Best)**
```javascript
// ❌ ANTI-PATTERN: "Get count of all users"
SELECT COUNT(*) FROM users;
// This requires hitting all shards

// ✅ SOLUTION: Track count separately
class UserStats {
  async getCount() {
    // Maintain user_count in central store
    return await cache.get('user_count');
  }

  async increment() {
    await cache.increment('user_count');
  }
}
```

**Option 2: Broadcast (Parallel)**
```javascript
// ❌ SLOW: Sequential (4 shards × 100ms = 400ms)
let results = [];
for (let shardId = 0; shardId < 4; shardId++) {
  const result = await shards[shardId].query(
    'SELECT * FROM users WHERE country = $1',
    ['USA']
  );
  results.push(...result);
}

// ✅ FAST: Parallel (max(4 shards × 100ms) = 100ms)
const results = await Promise.all(
  shards.map(shard =>
    shard.query('SELECT * FROM users WHERE country = $1', ['USA'])
  )
);
const merged = results.flat();
```

**Option 3: Secondary Index (Complex)**
```
Create reverse index:
  country → [user_ids on all shards]

Query: "Users from USA"
1. Lookup: country_index.get('USA') → [user_ids]
2. For each user_id: route to correct shard (single-shard)
3. Fetch in parallel

Complexity: Maintain index + handle consistency
```

---

## 4. Hot-Shard Problem & Solutions

One shard gets 90% of traffic (overloaded). Others underutilized.

### Cause 1: Bad Shard Key

```
Shard key: user_type (premium/free)

Premium users: 10% of users, 90% of queries
Free users: 90% of users, 10% of queries

Result:
  Premium shard: 90% load
  Free shard: 10% load
```

**Fix: Better shard key**
```javascript
// ✅ Shard by user_id (not user_type)
// Distribute premium/free evenly across shards
```

### Cause 2: Time-Based Access Pattern

```
Shard key: timestamp
Shard: Jan, Feb, Mar, Apr, ...

All queries hit recent months (Feb, Mar)
Old months (Jan) rarely accessed

Result:
  Current shard: Hot (90% load)
  Old shards: Cold (5% load)
```

**Fix 1: Sub-shard Recent Data**
```
Shard 0 (Jan): 1M documents, 1 server
Shard 1 (Feb): 1M documents, 5 servers ← more capacity
Shard 2 (Mar): 1M documents, 10 servers ← even more
Shard 3 (Apr): 1M documents, 15 servers ← hottest
```

**Fix 2: Cache Hot Data**
```javascript
// Cache recent data in Redis
// On query for Feb data: check cache first
// Cache hit rate: 95% → database hit rate: 5%
// → Reduces load on hot shard
```

---

## 5. Real Production Example: User Sharding (Twitter-style)

```javascript
// 100B users, 4 shards, 25B users per shard

class UserShardRouter {
  constructor() {
    this.shards = [
      new Database('shard0.example.com'),
      new Database('shard1.example.com'),
      new Database('shard2.example.com'),
      new Database('shard3.example.com')
    ];
    this.directoryCache = new Map();
  }

  getShardId(userId) {
    // Hash-based (deterministic)
    return hashCode(userId) % 4;
  }

  async createUser(userId, name) {
    const shardId = this.getShardId(userId);
    const shard = this.shards[shardId];

    await shard.query(
      'INSERT INTO users (id, name) VALUES ($1, $2)',
      [userId, name]
    );

    this.directoryCache.set(userId, shardId);
  }

  async getUser(userId) {
    const shardId = this.getShardId(userId);
    const shard = this.shards[shardId];

    const result = await shard.query(
      'SELECT * FROM users WHERE id = $1',
      [userId]
    );

    return result.rows[0];
  }

  async getUsersByCountry(country) {
    // Cross-shard query: broadcast to all shards
    const results = await Promise.all(
      this.shards.map(shard =>
        shard.query('SELECT * FROM users WHERE country = $1', [country])
      )
    );

    // Merge results from all shards
    return results.flatMap(r => r.rows);
  }

  async getTotalUsers() {
    // Cross-shard aggregation: parallel sum
    const counts = await Promise.all(
      this.shards.map(async shard => {
        const result = await shard.query('SELECT COUNT(*) FROM users');
        return parseInt(result.rows[0].count);
      })
    );

    return counts.reduce((a, b) => a + b, 0);
  }
}

// Usage
const router = new UserShardRouter();

await router.createUser(123, 'Alice');
const user = await router.getUser(123); // Shard 3
const usaUsers = await router.getUsersByCountry('USA'); // All shards (slow)
const totalUsers = await router.getTotalUsers(); // All shards (slow)
```

---

## 6. Adding/Removing Shards (Reshuffling)

Going from 4 to 5 shards requires reshuffling data (expensive).

```
Old: hash(user_id) % 4
New: hash(user_id) % 5

user_id=123:
  Old: hash(123) % 4 = 3
  New: hash(123) % 5 = 3 (happens to match, lucky)

user_id=456:
  Old: hash(456) % 4 = 2
  New: hash(456) % 5 = 1 (doesn't match, must move)

Reshuffling: 60% of data needs to move
```

### Consistent Hashing (Solves This)

Instead of hash % num_shards, use consistent hashing (limits reshuffling).

```
Consistent hashing ring (0-360):

Users distributed on ring by hash(user_id)
Shards assigned positions on ring

When adding shard:
  - Only users between old shard and new shard move
  - ~25% of data moves (vs 60% with modulo hashing)
```

**Libraries:** Python hashlib with consistent_hash, Java Ketama, Redis Cluster

---

## 7. Sharding Checklist

- [ ] Shard key chosen (high cardinality, uniform, immutable)
- [ ] Hashing strategy decided (hash vs range vs directory)
- [ ] Number of shards calculated (growth projection 5 years)
- [ ] Hotspot analysis done (simulate uneven distribution)
- [ ] Cross-shard query handling planned (broadcast, cache, etc.)
- [ ] Reshuffling strategy documented (consistent hashing preferred)
- [ ] Data migration tool built (move data between shards)
- [ ] Replication configured (each shard has replicas)
- [ ] Monitoring setup (uneven load, cross-shard latency)
- [ ] Failover plan (if one shard dies, others survive)
- [ ] Testing: Can add/remove shard without downtime?

---

## Interview Prep Questions

1. **"How would you shard a 10TB users table?"**
   - Answer: Shard by user_id (hash-based). Distribute evenly across 100 shards (100GB each). Each shard has 2 replicas for HA.

2. **"What's a bad shard key? Why?"**
   - Answer: Status (active/inactive). 70% data on active shard, 30% on inactive. Creates hot-shard (one shard overloaded, others underutilized).

3. **"How do you count total rows across shards?"**
   - Answer: Broadcast COUNT(*) to all shards in parallel. Sum results. Slow (network to all shards), but works.

4. **"Can you change shard key after going live?"**
   - Answer: Difficult. Would require full reshuffling. Plan shard key carefully upfront.

5. **"What's consistent hashing? Why is it useful?"**
   - Answer: Ring-based sharding. When adding shard, only ~K/n data moves (vs K/(n+1) with modulo hashing). Reduces reshuffling cost.

---

## See Also

### Phase 7.1 Related Topics

- [Database Replication](./10-database-replication.md) — Replication topology with shards
- [Disaster Recovery](./09-disaster-recovery.md) — Backup strategy per shard
- [Connection Pooling](./08-connection-pooling.md) — Pool size calculation with shards

### Additional Resources

- Vitess: MySQL sharding proxy (open source)
- Amazon DynamoDB: Sharded NoSQL
- Google Spanner: Geo-distributed sharding
- Citus: PostgreSQL sharding extension
- Cassandra: Distributed with automatic sharding
