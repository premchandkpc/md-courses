# Database Interview Preparation Guide

## Common Database Questions

### MySQL Questions

**Q1: What are ACID properties?**
```
Atomicity: All or nothing
Consistency: Valid before and after
Isolation: Concurrent independence
Durability: Survives failures

Example: Bank transfer
- Debit account A
- Credit account B
- Both succeed or both fail (atomic)
```

**Q2: Explain indexes and when to use**
```
Index: Sorted data structure for fast lookup
Use: WHERE, JOIN, ORDER BY columns

B-tree: Default, most common
Hash: Equality only
BRIN: Large tables, sequential data

Cost: Storage + write overhead
Benefit: Read speedup (10-100x)

Create: High cardinality columns
Skip: Low cardinality (gender, status)
```

**Q3: What's the difference between INNER and LEFT JOIN?**
```
INNER: Rows matching both tables
LEFT: All left table, matching right
RIGHT: All right table, matching left

Example:
Users LEFT JOIN Posts
- All users (even without posts)
- Posts where user exists

Use: When you need unmatched rows
```

**Q4: How to optimize slow query?**
```
Steps:
1. EXPLAIN to see plan
2. Look for: Seq Scan (bad), Index Scan (good)
3. Add indexes on WHERE/JOIN columns
4. Avoid functions in WHERE
5. Use LIMIT for top-N
6. Check table statistics (ANALYZE)
7. Consider denormalization

Example:
SELECT * FROM users WHERE UPPER(email) = 'JOHN@EXAMPLE.COM'
↓ Bad (no index on UPPER)
↓ Create index on UPPER(email) OR query differently
```

**Q5: Transactions and locks**
```
Isolation levels:
- READ UNCOMMITTED: Dirty reads (bad)
- READ COMMITTED: Only committed data
- REPEATABLE READ: Same data in transaction
- SERIALIZABLE: Sequential (slow)

Locks:
- Shared: Multiple readers
- Exclusive: Single writer

Deadlock: When txns wait for each other
- Prevention: Lock in consistent order
```

---

### PostgreSQL Questions

**Q1: JSON vs JSONB**
```
JSON: Text, re-parsed each query (slow)
JSONB: Binary, pre-parsed (fast, indexed)

Use: JSONB always

Operators:
-> : JSON extraction
->> : Text extraction
@> : Contains
? : Has key
```

**Q2: Window functions vs GROUP BY**
```
GROUP BY: Collapses rows, returns groups
Window: Keeps all rows, adds aggregate

Use window when: Need original + aggregate

Example:
SELECT user, score,
  ROW_NUMBER() OVER (ORDER BY score DESC) as rank
FROM leaderboard

- Keeps all users
- Adds rank without collapsing
```

**Q3: CTEs (Common Table Expressions)**
```
WITH statement: Named subquery
Use: Readable, reusable, recursive

Example:
WITH active AS (
  SELECT * FROM users WHERE status='active'
)
SELECT * FROM active WHERE age > 25

Recursive: For hierarchies (categories, org charts)
```

**Q4: Full-text search**
```
tsvector: Searchable text representation
@@ : Match operator
to_tsvector: Convert to searchable

Example:
SELECT title FROM articles
WHERE tsvector_col @@ plainto_tsquery('postgresql database')

Better than: LIKE (slow), regex (complex)
```

---

### MongoDB Questions

**Q1: Document vs relational**
```
Relational: 3+ collections, JOINs
Document: All data in one doc, nested

Relational (orders, items, products):
SELECT o.id, i.quantity, p.name
FROM orders o JOIN items i JOIN products p

Document (order with embedded items):
db.orders.findOne({_id: 1})
// Returns: {items: [{product: {name: "..."}, qty: 2}]}
```

**Q2: Aggregation pipeline**
```
Stages (order matters):
$match → Filter (like WHERE)
$group → Aggregate
$sort → Order
$limit → Top N
$project → Reshape
$lookup → JOIN

Example: Top 10 users by post count
db.posts.aggregate([
  {$group: {_id: "$userId", count: {$sum: 1}}},
  {$sort: {count: -1}},
  {$limit: 10}
])
```

**Q3: Sharding**
```
Shard key: Determines which server

Good: High cardinality (userId, email)
Bad: Low cardinality (gender, status)
Bad: Monotonic (timestamp, sequence)

Problem: Hot shard (one gets all traffic)
Solution: Compound shard key + prefix

Cost: Per-shard storage + ops
```

**Q4: Replica sets**
```
Primary: Writes
Secondary: Reads (stale data)

Write concern: How many servers acknowledge
- w: 1 = Primary only
- w: "majority" = Half + 1 servers
- w: 3 = All 3 replicas

Failover: Auto if primary fails
```

---

### DynamoDB Questions

**Q1: Partition key design**
```
Partition key: Distributes data

Good: High cardinality (userId, email)
Bad: Sequential (1,2,3 → hot)
Bad: Timestamp (today's writes hotspot)

Hot partition: One server gets 90% traffic
Solution: Add random prefix, composite key

Cost: Provisioned per partition
```

**Q2: RCU/WCU**
```
RCU: 1 unit = 1 × 4KB strongly consistent read
WCU: 1 unit = 1 × 1KB write

Example:
Read 5KB item = 2 RCU (rounds up to 4KB)
Write 2.5KB item = 3 WCU (rounds up to 3×1KB)

Billing:
On-demand: $1.25 per million reads
Provisioned: $0.00013 per RCU-hour
```

**Q3: Query vs Scan**
```
Query: Fast, uses key
- Partition key mandatory
- Optional sort key conditions
- Cost: Items scanned / 4KB

Scan: Slow, reads all
- No key required
- FilterExpression (post-scan)
- Cost: All items / 4KB (expensive!)

Use Query 99% of time
```

**Q4: Global tables**
```
Multi-region replication
- Write any region, replicate others
- Eventually consistent (<1s)
- Auto-failover if region down
- 3x cost (per region)

Read: Local (1-2ms)
Write: Async replicate (100ms-1s)
```

---

### Oracle Questions

**Q1: Partitioning**
```
Range: By date ranges
List: By category
Hash: Automatic distribution

Benefits:
- Parallel query
- Faster pruning
- Easier maintenance

Example: Sales by year
```

**Q2: Indexing**
```
B-tree: Standard
Bitmap: Low cardinality (status, gender)
Function-based: UPPER(email)
Partitioned: Per partition

Cost: Storage + write overhead
```

---

## Design Questions

### "Design a leaderboard"

**Solution with DynamoDB:**
```
Table: Leaderboards
PK: GameId, SK: Score#PlayerId

Atomic update:
UPDATE leaderboards
SET score = score + points
WHERE gameId = 'game123'

Distributed counter (sharding):
LeaderboardId#0, LeaderboardId#1...
Reduces hot partition

Query top 10:
Query with ScanIndexForward=False, Limit=10
```

### "Design social feed"

**Solution with PostgreSQL:**
```
Tables:
- users (id, name)
- posts (id, userId, content, createdAt)
- comments (id, postId, userId, content)
- likes (id, postId, userId)

Indexes:
- posts(userId, createdAt DESC)
- comments(postId)
- likes(postId, userId UNIQUE)

Query user's feed:
SELECT p.*, COUNT(l.id) as likes
FROM posts p
WHERE userId IN (SELECT friendId FROM friendships WHERE userId=5)
ORDER BY p.createdAt DESC
LIMIT 50
```

### "Design inventory system"

**Key concerns:**
```
Race condition: Stock undercount
Solution: Atomic decrement

UPDATE inventory 
SET quantity = quantity - 1
WHERE productId = 5 AND quantity > 0

Transaction: Prevent oversell
START TRANSACTION
SELECT quantity FROM inventory WHERE productId=5 FOR UPDATE
IF quantity >= requested:
  UPDATE inventory SET quantity = quantity - requested
```

---

## Performance Q&A

**Q: Why is my query slow?**
```
Checklist:
1. Run EXPLAIN ANALYZE
2. Check for Seq Scan (bad) vs Index Scan
3. Add missing indexes
4. Remove functions from WHERE
5. Update statistics (ANALYZE)
6. Check table size (SELECT COUNT)
7. Try LIMIT if large result set
8. Consider denormalization
```

**Q: How many indexes should I have?**
```
Rule of thumb:
- PK: Always
- Foreign keys: Usually
- WHERE columns: Often
- JOIN columns: Often
- ORDER BY: Sometimes
- Don't over-index

Monitor:
- Unused indexes (remove)
- Index bloat (rebuild)
- Write overhead (too many)
```

**Q: When to use materialized view?**
```
Materialized view: Computed table (cached)

Use:
- Expensive aggregations (compute once)
- Historical data (slowly changing)
- Reports (pre-compute)

Refresh: Periodic (daily, hourly)

Cost: Storage, refresh time
Benefit: Query speed (10-100x)
```

---

## Behavioral Questions

**Q: Tell me about a database issue you fixed**
```
Good answer structure:
1. Problem: [Specific issue]
2. Discovery: [How you found it - EXPLAIN, monitoring]
3. Root cause: [Why it happened]
4. Solution: [What you did]
5. Result: [Metrics improvement - latency, throughput]
6. Learning: [What you learned]

Example:
"E-commerce checkout slow (5s response). 
Used EXPLAIN, saw 3 full table scans. 
Added 2 indexes on order lookup. 
Latency dropped to 50ms (100x improvement). 
Learned: Always index WHERE/JOIN columns."
```

**Q: How do you approach database design?**
```
1. Understand access patterns
   - What queries run most?
   - Read vs write ratio?
   - Concurrency needs?

2. Choose database
   - Relational for complex queries
   - Document for flexibility
   - Key-value for scale

3. Design schema
   - Normalize or denormalize
   - Indexes for hot queries
   - Partitioning for scale

4. Plan capacity
   - Growth estimate
   - Peak traffic
   - Cost

5. Monitor & optimize
   - Slow logs
   - Metrics (latency, throughput)
   - Ongoing tuning
```

---

## Technical Deep Dives

### Transactions: ACID vs BASE

```
ACID (Relational):
- Atomicity: All or nothing
- Consistency: Valid state
- Isolation: No interference
- Durability: Persisted

BASE (NoSQL):
- Basic Availability
- Soft state
- Eventually consistent

Trade-off: Consistency vs Availability
```

### Consistency Models

```
Strong: Latest data guaranteed (slower)
Eventual: Latest data eventually (faster)
Causal: Related writes consistent
Read-your-write: See own writes

DynamoDB: Eventually consistent default
PostgreSQL: Strong consistent
MongoDB: Configurable
```

### CAP Theorem

```
Pick 2 of 3:
- Consistency: All nodes same
- Availability: Always responsive
- Partition tolerance: Survives network split

Relational: Consistency + Availability (single region)
Distributed: Availability + Partition (sacrifices consistency)
```

---

## Red Flags in Interviews

✗ "We don't use indexes"
✗ "SELECT * FROM large_table every request"
✗ "No transactions needed"
✗ "Database will never grow"
✗ "We'll optimize later"

✓ "We profiled and found bottleneck"
✓ "We chose DB based on access patterns"
✓ "We have monitoring in place"
✓ "We test with production-like load"

---

## Resources to Study

**Per Database:**
- Official docs (best source)
- Performance tuning guides
- Best practices from companies
- GitHub projects (how they use it)

**General:**
- Database Internals (book)
- Designing Data-Intensive Applications
- System Design Interview (website)

---

## Practice Problems

**Easy:**
1. Explain 3 ways to optimize slow query
2. When would you denormalize?
3. What's better: 1 index or 5 indexes?

**Medium:**
1. Design user/post/comment schema
2. How to handle 1M writes/second?
3. Partition strategy for time-series data?

**Hard:**
1. Design global DB with multi-region
2. How to do transactions across shards?
3. Prevent race conditions in inventory?

---

**See Also:**
- [[README.md|Main Guide]]
- [[COMPARISON_GUIDE.md|Database Comparison]]
- Individual database guides
