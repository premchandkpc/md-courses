---
title: PostgreSQL Index Types, Selection & Performance Deep Dive
topic: 08-databases
difficulty: intermediate
time: 30m
paths:
  - backend-junior
  - data
  - backend-senior
---

# PostgreSQL Index Types, Selection & Performance Deep Dive

## Index Fundamentals

### What Indexes Do
- **Speed reads**: O(log N) instead of O(N) full table scan
- **Slow writes**: every INSERT/UPDATE/DELETE updates all indexes on table
- **Trade-off**: read speed vs write speed vs storage cost

```sql
-- Without index: scans all 1M rows
SELECT * FROM orders WHERE customer_id = 100;
-- Execution time: 500-1000ms

-- With index on customer_id: finds via B-tree
CREATE INDEX idx_customer ON orders(customer_id);
-- Same query: 1-5ms (100-1000x faster)
```

---

## Index Types: Decision Matrix

### B-tree (Default, Most Common)
**When:** equality, range, sorting
**Performance:** 1-10ms for 1M rows
**Storage:** ~10% of table size
**Write overhead:** 5-10%

```sql
-- Good for B-tree
CREATE INDEX idx_orders_date ON orders(created_at);
SELECT * FROM orders WHERE created_at >= '2025-01-01' AND created_at < '2025-02-01';
-- B-tree scans range efficiently

-- Also good: sorting
SELECT * FROM orders ORDER BY created_at LIMIT 10;
-- Uses B-tree index, no SORT operation
```

### BRIN (Block Range Index)
**When:** time-series, large tables, sequential writes
**Performance:** 50-100ms for 10B rows (slower but acceptable)
**Storage:** 0.1% of table size (TINY!)
**Write overhead:** <1%

```sql
-- Good for BRIN on time-series
CREATE INDEX idx_events_time USING BRIN ON events(timestamp);
-- Table: 10B events, event_date = today (mostly recent queries)

-- Query: last 24 hours events
SELECT * FROM events WHERE timestamp >= NOW() - INTERVAL '1 day';
-- BRIN: scans ~100 blocks, reads relevant rows
-- B-tree: would need ~500MB index, BRIN uses ~5MB

-- Cost trade-off: 10-20% slower queries, 99% less storage
```

### GIN (Generalized Inverted Index)
**When:** JSONB, arrays, full-text search
**Performance:** 1-50ms for 100M rows
**Storage:** ~30% of table size
**Write overhead:** 20-40%

```sql
-- GIN for JSONB
CREATE INDEX idx_data_gin ON products USING GIN(attributes);

-- Fast: JSONB contains search
SELECT * FROM products WHERE attributes @> '{"color": "red"}'::jsonb;
-- Without index: scans all 1M rows
-- With GIN: finds via inverted index (~5ms)

-- GIN for arrays
CREATE INDEX idx_tags_gin ON articles USING GIN(tags);
SELECT * FROM articles WHERE tags @> ARRAY['postgresql'];
```

### Hash Index
**When:** equality only, rarely used
**Performance:** 1-5ms
**Storage:** ~15% of table size
**Write overhead:** 5%

```sql
-- Hash for exact match (but B-tree usually better)
CREATE INDEX idx_uuid USING HASH ON users(uuid);
SELECT * FROM users WHERE uuid = 'abc123';
-- Works but B-tree typically faster (hash collision overhead)
```

### GiST (Generalized Search Tree)
**When:** geometric, spatial queries
**Performance:** 5-20ms for geographic data
**Storage:** ~25% of table size
**Write overhead:** 10%

```sql
-- GiST for geographic distance
CREATE INDEX idx_location_gist ON restaurants USING GIST(location);

-- Find restaurants within 5km radius
SELECT * FROM restaurants 
WHERE ST_DWithin(location, ST_GeomFromText('POINT(0 0)', 4326), 5000);
-- GiST efficiently prunes far-away points
```

### SPGIST (Space-Partitioned GiST)
**When:** IP addresses, ranges, hierarchical
**Performance:** 5-20ms
**Storage:** ~15% of table size
**Write overhead:** 8%

```sql
-- SPGIST for IP ranges
CREATE INDEX idx_ip_spgist ON access_logs USING SPGIST(ip_address);

-- Find access from subnet
SELECT * FROM access_logs WHERE ip_address << '192.168.0.0/16'::inet;
-- SPGIST efficiently partitions IP space
```

---

## Composite Indexes: Column Order Matters

### Rule: Equality First, Then Range, Then Sorting

```sql
-- Schema: orders(customer_id, created_at, status, amount)
-- Query pattern:
-- 1. Find by customer_id (equality) - filter 99%
-- 2. Within date range (range) - filter 90%
-- 3. Sort by amount (sorting) - for display

-- GOOD: customer_id first (equality), then created_at (range)
CREATE INDEX idx_orders_good ON orders(customer_id, created_at, amount);

-- Query uses full index:
SELECT amount FROM orders 
WHERE customer_id = 100 
  AND created_at >= '2025-01-01' 
ORDER BY amount;
-- Execution: 1-2ms (index scan + sort from index)

-- BAD: different order
CREATE INDEX idx_orders_bad ON orders(created_at, customer_id, amount);

-- Same query now:
-- - Can't use index for customer_id equality efficiently
-- - Must scan all dates for all customers
-- Execution: 100-200ms (slower)
```

### Multi-column Index Strategy

```sql
-- Table: user_orders (user_id, order_id, created_at, status, amount)
-- Common queries:
-- Q1: SELECT * FROM user_orders WHERE user_id = 1 AND status = 'pending'
-- Q2: SELECT * FROM user_orders WHERE user_id = 1 AND created_at > '2025-01-01'
-- Q3: SELECT * FROM user_orders WHERE user_id = 1 ORDER BY created_at

-- Single index covers all three:
CREATE INDEX idx_user_orders_opt ON user_orders(user_id, created_at DESC);
-- Q1: Uses index, filters by user_id, checks status in-index
-- Q2: Uses index, scans range for user_id + date
-- Q3: Uses index for sorting (created_at already sorted)

-- Covering index (includes non-indexed columns):
CREATE INDEX idx_user_orders_cover ON user_orders(user_id, created_at) INCLUDE (status, amount);
-- Index stores: user_id, created_at, status, amount (all in index)
-- Queries can fetch all data from index without touching table
-- Benefit: 10-100x faster (no table lookup)
```

---

## Index Bloat & Maintenance

### Identifying Bloat

```sql
-- Check index bloat
SELECT 
  schemaname, tablename, indexname,
  idx_blks_read, idx_blks_hit,
  ROUND(100 * idx_blks_hit / (idx_blks_hit + idx_blks_read), 2) hit_ratio
FROM pg_statio_user_indexes
ORDER BY idx_blks_read DESC;

-- Example output:
-- orders_customer_idx: hit_ratio = 95% (good)
-- orders_date_idx: hit_ratio = 40% (bloated, many unused blocks)
```

### Reindexing Strategy

```sql
-- Reindex online (no locks, PostgreSQL 12+):
REINDEX INDEX CONCURRENTLY idx_orders_customer;
-- Rebuilds index in background, allows reads/writes

-- Without CONCURRENTLY (locks table, old way):
REINDEX INDEX idx_orders_customer;
-- Table locked, users blocked, don't do this on production

-- Reindex all indexes on table:
REINDEX TABLE CONCURRENTLY orders;

-- Automatic reindex with maintenance window:
-- Schedule during low-traffic hours (midnight)
```

### VACUUM & Autovacuum Tuning

```sql
-- Check dead rows
SELECT 
  schemaname, tablename,
  n_live_tup, n_dead_tup,
  ROUND(100 * n_dead_tup / (n_live_tup + n_dead_tup), 2) dead_percent
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;

-- Example: orders table
-- live: 1M rows, dead: 100K rows (9% dead)
-- Without vacuum: indexes growing, searches slower

-- Aggressive vacuum for high-update tables:
ALTER TABLE orders SET (
  autovacuum_vacuum_scale_factor = 0.01,    -- vacuum at 1% dead rows
  autovacuum_vacuum_cost_delay = 10,        -- faster vacuum (lower delay)
  autovacuum_vacuum_cost_limit = 1000       -- higher throughput
);

-- Vacuum manually if urgent:
VACUUM ANALYZE orders;
-- ANALYZE: updates table statistics for query planner
```

---

## Query Planner & Statistics

### Understanding EXPLAIN

```sql
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM orders WHERE customer_id = 100 AND amount > 1000;

-- Output:
-- Index Scan using idx_orders_customer on orders
--   Index Cond: (customer_id = 100)
--   Filter: (amount > 1000)
--   Rows: 50 (estimated 52)
--   Buffers: hits=100 reads=5

-- Interpretation:
-- - "Index Scan": using index (good!)
-- - "Index Cond": customer_id filtered at index level
-- - "Filter": amount filtered after index (acceptable if few rows)
-- - "Rows: 50 (estimated 52)": estimate was accurate
-- - "Buffers: hits=100 reads=5": most data from cache
```

### Bad Plans (Red Flags)

```sql
EXPLAIN SELECT * FROM orders WHERE amount > 1000 ORDER BY created_at LIMIT 10;

-- Bad plan (without index on amount):
-- Seq Scan on orders
--   Filter: (amount > 1000)
--   Rows: 500K (scanned 1M, filtered 500K)
--   Sort: on 500K rows
-- This is slow! (100-200ms)

-- Solution: Create index
CREATE INDEX idx_amount ON orders(amount, created_at);

-- Now:
-- Index Scan using idx_amount
--   Index Cond: (amount > 1000)
--   Rows: 500K (still many, but in order)
--   LIMIT applied: returns 10
-- Fast! (1-2ms)
```

---

## Real-World Performance Scenarios

### Scenario 1: E-Commerce Orders (100M rows)

```sql
-- Common queries:
-- Q1: Recent orders by customer (99% of traffic)
-- Q2: Search by date range (1% of traffic)

-- Optimization:
CREATE INDEX idx_customer_date ON orders(customer_id, created_at DESC);
-- Covers Q1 (customer lookup) + sorting by date

CREATE INDEX idx_date_range ON orders(created_at) WHERE status IN ('pending', 'processing');
-- Partial index for Q2 (only active orders)
-- Size: 5% of full index, faster

-- Query Q1:
SELECT * FROM orders WHERE customer_id = 100 ORDER BY created_at DESC LIMIT 20;
-- Time: 1-2ms (index scan + limit)

-- Query Q2:
SELECT COUNT(*) FROM orders WHERE created_at >= '2025-01-01' AND created_at < '2025-02-01';
-- Time: 10-20ms (index range scan)
```

### Scenario 2: Time-Series Data (1B events/day)

```sql
-- Data: events(timestamp, user_id, event_type, data)
-- Challenge: 1B rows/day = 30B rows/month = storage huge

-- Index strategy:
-- Option 1: BRIN on timestamp (smallest)
CREATE INDEX idx_events_timestamp USING BRIN ON events(timestamp);
-- Size: 100MB (tiny!)
-- Query "last 24h": 50-100ms (acceptable for reports)

-- Option 2: B-tree on timestamp (faster but bigger)
CREATE INDEX idx_events_timestamp_btree ON events(timestamp);
-- Size: 500GB (huge!)
-- Query "last 24h": 5-10ms (faster)

-- Trade-off: BRIN for storage, B-tree for speed
-- Recommendation: BRIN for archival, B-tree for hot data

-- Rolling partitions to manage size:
CREATE TABLE events_2025_01 PARTITION OF events
  FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- Drop old partition (fast, no index scan):
DROP TABLE events_2024_01;
```

---

## Monitoring & Alerting

### Key Metrics to Watch

```sql
-- 1. Index usage
SELECT 
  schemaname, tablename, indexname,
  idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Red flag: High idx_tup_read, low idx_tup_fetch
-- Indicates index returning many rows (not selective)
-- Solution: Add filter column to index

-- 2. Unused indexes (safe to drop)
SELECT 
  schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;

-- 3. Bloated indexes
SELECT 
  current_database(), schemaname, tablename, indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) size,
  ROUND(100 * pg_relation_size(indexrelid) / pg_relation_size(tablename), 2) percent
FROM pg_indexes
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_relation_size(indexrelid) DESC;

-- 4. Slow queries (requires pg_stat_statements extension)
SELECT 
  query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE mean_time > 100
ORDER BY total_time DESC;
```

---

## Best Practices Checklist

- ✓ Index columns used in WHERE, JOIN, ORDER BY
- ✓ Composite index: equality columns first, range second, sorting last
- ✓ Avoid over-indexing (write overhead kills performance)
- ✓ Monitor index bloat, reindex monthly
- ✓ Use partial indexes for filtered queries (saves space)
- ✓ Use INCLUDE for covering index queries (10-100x faster)
- ✓ ANALYZE after bulk changes (keeps statistics fresh)
- ✓ Test with EXPLAIN ANALYZE (actual vs estimated rows)
- ✓ Drop unused indexes (wastes space, slows writes)
- ✓ Monitor index hit ratio (should be >90% for hot tables)

---

**Summary:**
- **B-tree**: Default, best for most queries (equality, range, sorting)
- **BRIN**: Time-series, huge tables, tiny storage cost
- **GIN**: JSONB/arrays, inverted searches
- **Column order**: Equality → Range → Sorting
- **Maintenance**: REINDEX CONCURRENTLY, aggressive VACUUM, monitor bloat
- **Monitoring**: Hit ratio, unused indexes, slow queries
