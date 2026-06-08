---
title: PostgreSQL Advanced Optimization & Performance Tuning
topic: 08-databases
difficulty: intermediate
time: 30m
paths:
  - backend-junior
  - data
  - backend-senior
---

# PostgreSQL Advanced Optimization & Performance Tuning

## Query Execution Plans

### EXPLAIN

```sql
-- Show query plan
EXPLAIN SELECT * FROM users WHERE age > 25;

-- Output:
-- Seq Scan on users (cost=0.00..35.50 rows=100 width=200)
-- Filter: (age > 25)

-- GOOD: Uses index
EXPLAIN SELECT * FROM users WHERE id = 1;
-- Index Scan using users_pkey on users

-- BAD: Full scan (seq scan)
EXPLAIN SELECT * FROM users WHERE age > 25;
-- Seq Scan on users
```

### EXPLAIN ANALYZE (Actual Execution)

```sql
-- Show actual execution with stats
EXPLAIN ANALYZE SELECT * FROM posts WHERE userId = 5;

-- Output includes:
-- Seq Scan on posts (cost=0.00..1000.00 rows=100)
-- (actual time=0.100..0.500 rows=87 loops=1)

-- Compare planned vs actual rows
-- Mismatch indicates stats need updating
ANALYZE users;  -- Update table statistics
```

### Costs Explained

```
Cost format: (startup_cost..total_cost)

Seq Scan: cost=0.00..1000.00
  - Start: 0 (immediate)
  - Total: 1000 cost units
  - Means: ~1000 random page accesses

Index Scan: cost=0.15..10.50
  - Much cheaper (index seek)
  - If index accessed sequentially

Most expensive: Nested Loop Join with subquery
Cheapest: Single-index lookup
```

---

## Index Tuning

### Identifying Missing Indexes

```sql
-- Find slow queries
SELECT query, mean_time, calls
FROM pg_stat_statements
WHERE mean_time > 100  -- > 100ms
ORDER BY mean_time DESC;

-- Check which columns filtered/joined frequently
SELECT schemaname, tablename, attname
FROM pg_stat_user_tables t
JOIN pg_stat_user_col_defs c ON t.tableid = c.tableid
WHERE seq_scan > index_scan * 10;  -- Heavy sequential scans
```

### Index Strategy

```sql
-- Index by cardinality
-- High cardinality: Good for index (email, id)
-- Low cardinality: Bad (status, gender, country)

-- Bad: Index on gender (M, F, unknown = 3 values)
CREATE INDEX idx_gender ON users(gender);

-- Good: Composite index for frequent query
CREATE INDEX idx_user_created ON posts(userId, createdAt DESC);

-- Conditional index for subset
CREATE INDEX idx_active_users ON users(email)
WHERE status = 'active';  -- Only index active rows

-- Partial index for large data
CREATE INDEX idx_recent_posts ON posts(userId, createdAt)
WHERE createdAt > NOW() - INTERVAL '1 year';
```

### Index Types

```sql
-- B-tree (default, most common)
CREATE INDEX idx_standard ON users(email);

-- Hash (equality only)
CREATE INDEX idx_hash ON users USING HASH(email);

-- BRIN (Block Range Index, huge tables)
-- Scans 1 billion rows of log data
CREATE INDEX idx_logs_time ON logs USING BRIN(timestamp);

-- GiST (Generalized Search Tree)
-- Full-text search, geometric
CREATE INDEX idx_fts ON documents USING GiST(tsvector);

-- GIN (Inverted Index)
-- Best for JSON, arrays, text
CREATE INDEX idx_jsonb ON metadata USING GIN(data);

-- SPGIST (Space-partitioned GiST)
-- IP addresses, ranges
CREATE INDEX idx_ip ON networks USING SPGIST(ip_range);
```

---

## Query Optimization Techniques

### Avoid Functions in WHERE

```sql
-- ❌ Index not used
SELECT * FROM users WHERE LOWER(email) = 'john@example.com';

-- ✓ Store lowercase or use expression index
CREATE INDEX idx_email_lower ON users(LOWER(email));
SELECT * FROM users WHERE LOWER(email) = 'john@example.com';

-- Or: Store field in lowercase
ALTER TABLE users ADD email_lower VARCHAR(255);
CREATE INDEX idx_email_lower ON users(email_lower);
```

### Use Window Functions

```sql
-- ❌ Subquery for each row
SELECT u.*, (SELECT COUNT(*) FROM posts WHERE userId = u.userId)
FROM users u;

-- ✓ Window function (much faster)
SELECT u.*, COUNT(*) OVER (PARTITION BY userId)
FROM users u
LEFT JOIN posts p ON u.userId = p.userId;
```

### Batch Processing

```sql
-- ❌ Individual inserts
INSERT INTO logs VALUES (1, 'error');
INSERT INTO logs VALUES (2, 'warning');
INSERT INTO logs VALUES (3, 'info');

-- ✓ Batch insert
INSERT INTO logs (id, level) VALUES
  (1, 'error'),
  (2, 'warning'),
  (3, 'info');

-- ✓ COPY for bulk
COPY logs (id, level) FROM STDIN;
1	error
2	warning
3	info
\.
```

---

## Configuration Tuning

### Memory Settings

```ini
# postgresql.conf

# Shared buffer (cache for pages)
shared_buffers = 4GB  # 25% of RAM for most systems

# Effective cache (includes OS cache)
effective_cache_size = 12GB  # 75% of RAM

# Work memory per operation
work_mem = 100MB  # Per sort/hash operation

# Maintenance memory
maintenance_work_mem = 1GB  # For REINDEX, VACUUM
```

### Query Planning

```ini
# Parallel query execution
max_parallel_workers_per_gather = 4
max_parallel_workers = 4

# Random page access cost
random_page_cost = 1.1  # For SSD (default 4.0 for HDD)

# Enable features
enable_seqscan = on
enable_indexscan = on
enable_hashjoin = on
enable_nestloop = on
```

---

## Maintenance

### VACUUM

```sql
-- Reclaim space from deleted rows
VACUUM users;

-- With analysis (updates stats)
VACUUM ANALYZE users;

-- Aggressive (locks table longer, frees more space)
VACUUM FULL users;
```

### ANALYZE

```sql
-- Update statistics for query planner
ANALYZE users;

-- Check stats age
SELECT schemaname, tablename, last_vacuum, last_analyze
FROM pg_stat_user_tables
ORDER BY last_analyze DESC;
```

### Autovacuum

```sql
-- Enable automatic maintenance
ALTER TABLE users SET (
  autovacuum_vacuum_scale_factor = 0.05,
  autovacuum_analyze_scale_factor = 0.02
);

-- Monitor
SELECT datname, last_autovacuum, last_autoanalyze
FROM pg_stat_user_tables;
```

---

## Real-World Tuning Example

### Slow Query: User Post Count

```sql
-- Problem: Slow
SELECT u.id, u.email, COUNT(p.id) as post_count
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.id
ORDER BY post_count DESC;

-- Analysis
EXPLAIN ANALYZE ...
-- Shows: Seq Scan on users, Seq Scan on posts, Hash Aggregate
-- Problem: No indexes, full table scans

-- Solution 1: Add indexes
CREATE INDEX idx_posts_user ON posts(user_id);
CREATE INDEX idx_users_id ON users(id);

-- Solution 2: Denormalization
ALTER TABLE users ADD post_count INT DEFAULT 0;
CREATE TRIGGER update_post_count ...

-- Solution 3: Materialized view (pre-computed)
CREATE MATERIALIZED VIEW user_stats AS
  SELECT u.id, u.email, COUNT(p.id) as post_count
  FROM users u
  LEFT JOIN posts p ON u.id = p.user_id
  GROUP BY u.id;

CREATE INDEX idx_user_stats_count ON user_stats(post_count DESC);

-- Query becomes much faster
SELECT * FROM user_stats ORDER BY post_count DESC;

-- Refresh periodically
REFRESH MATERIALIZED VIEW user_stats;
```

---

## Monitoring Tools

### Built-in Views

```sql
-- Slow queries
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;

-- Missing indexes
SELECT * FROM pg_stat_user_tables
WHERE seq_scan > index_scan * 10;
```

### External Tools

```
pgAdmin - GUI management
PgBadger - Log analysis
pg_stat_kcache - Cache misses
Prometheus + pg_exporter - Metrics
```

---

## Common Performance Issues

### N+1 Queries

```sql
-- ❌ Bad: 1 + N queries
SELECT * FROM users;
-- Then in app: for each user, SELECT posts WHERE user_id = ?

-- ✓ Good: Single query
SELECT u.*, p.*
FROM users u
LEFT JOIN posts p ON u.id = p.user_id;

-- Or: Fetch separately with batch
SELECT * FROM posts WHERE user_id IN (SELECT id FROM users);
```

### Missing Statistics

```sql
-- Stale stats cause bad plans
SELECT last_analyze FROM pg_stat_user_tables;

-- Update
ANALYZE;

-- Auto-analyze should handle, but manual helps
```

### Index Bloat

```sql
-- Deleted rows not reclaimed
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Clean up
VACUUM FULL users;
REINDEX TABLE users;
```

---

## Summary

- **EXPLAIN ANALYZE**: Understand actual execution
- **Indexes**: B-tree default, BRIN for huge, GIN for JSON/arrays
- **Window Functions**: Better than subqueries
- **Batch Operations**: Faster than row-by-row
- **Configuration**: Tune memory, costs, parallelism
- **Maintenance**: VACUUM, ANALYZE, autovacuum
- **Monitoring**: pg_stat views, pgAdmin, PgBadger
- **Denormalization**: Trade storage for speed when needed

Next: [[02-replication-scaling.md|Replication & Scaling]]

---

**See Also:**
- [[02-json-arrays-advanced.md|JSON & Advanced Features]]
- [[../../mysql/02-intermediate/02-replication-ha.md|MySQL Replication]]
- [[../../dynamodb/05-optimization/01-performance-tuning.md|DynamoDB Optimization]]
