# PostgreSQL Tuning Cheat Sheet

PostgreSQL performance tuning for slow queries, high concurrency, and production incidents. Covers config knobs, indexing, vacuum, and monitoring.

**Cross-refs**: `08-databases/01-relational-database-internals.md`, `08-databases/02-postgresql-architecture.md`, `08-databases/03-postgresql-troubleshooting-tuning.md`, `08-databases/internals/indexes.md`

## Quick Diagnostic Commands

```bash
# Slow query log
SELECT * FROM pg_stat_activity WHERE state != 'idle' ORDER BY query_start;
SELECT query, calls, total_exec_time, rows FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;
SELECT relname, seq_scan, seq_tup_read, idx_scan FROM pg_stat_all_tables ORDER BY seq_scan DESC;

# Bloat & dead tuples
SELECT relname, n_dead_tup, n_live_tup, round(n_dead_tup * 100.0 / GREATEST(n_live_tup, 1), 2) AS dead_pct
FROM pg_stat_user_tables WHERE n_dead_tup > 10000 ORDER BY n_dead_tup DESC;

# Locks
SELECT pid, mode, granted, wait_event, query FROM pg_locks l JOIN pg_stat_activity a USING(pid) WHERE NOT granted;

# Connections
SELECT count(*), state, wait_event FROM pg_stat_activity GROUP BY state, wait_event;
```

## Configuration Parameters

| Parameter | Default | Tuning | Effect |
|-----------|---------|--------|--------|
| `shared_buffers` | 128MB | 25% RAM | Cache hot data in shared memory |
| `effective_cache_size` | 4GB | 75% RAM | Planner estimate for OS cache |
| `work_mem` | 4MB | 4-64MB | Sort/hash per operation; too high = OOM |
| `maintenance_work_mem` | 64MB | 10% RAM | VACUUM, CREATE INDEX |
| `random_page_cost` | 4.0 | 1.1 (SSD) | Index scan cost vs seq scan |
| `max_connections` | 100 | 20-200 | Each conn needs ~2MB; prefer pgbouncer |
| `wal_buffers` | 16MB | 64MB-1GB | Write-ahead log buffer |
| `checkpoint_completion_target` | 0.5 | 0.9 | Spread checkpoint I/O |

## Query Tuning

```sql
-- EXPLAIN plans
EXPLAIN (ANALYZE, BUFFERS, TIMING) SELECT * FROM orders WHERE status = 'pending';
-- Look for: Seq Scan on large tables, high loops, large rows= estimates

-- Common fixes
CREATE INDEX CONCURRENTLY idx_orders_status_created ON orders(status, created_at);
VACUUM ANALYZE orders;
SET enable_seqscan = off;  -- Force index use (debug only, not permanent)
```

## Indexing

| Index Type | Use Case | Caveat |
|-----------|----------|--------|
| B-tree | Equality, range, sort | Default; good for most |
| Hash | Equality only | 2-3x smaller than B-tree |
| GiST | Full-text, geometry | Larger, slower to build |
| GIN | Array, JSONB, tsvector | Fast search, slow writes |
| BRIN | Large tables, correlated | Very small, great for time-series |
| Partial | `WHERE status = 'active'` | Only for filtered queries |
| Covering | `INCLUDE (col)` | Index-only scans |

```sql
-- Find unused indexes
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes WHERE idx_scan = 0 AND indexrelid NOT IN (SELECT indexrelid FROM pg_constraint);

-- Duplicate indexes
SELECT pg_size_pretty(SUM(pg_relation_size(idx))) AS total_size
FROM pg_indexes i1 WHERE EXISTS (SELECT 1 FROM pg_indexes i2 WHERE i2.indexdef = i1.indexdef AND i2.indexname != i1.indexname);
```

## Vacuum & Bloat

```sql
-- Table-level vacuum
VACUUM (VERBOSE, ANALYZE) orders;
VACUUM FULL orders;             -- Exclusive lock, last resort
REINDEX TABLE CONCURRENTLY orders;

-- Monitor vacuum progress
SELECT datname, phase, heap_blks_total, heap_blks_scanned, heap_blks_vacuumed
FROM pg_stat_progress_vacuum;

-- Auto-vacuum tuning (in postgresql.conf)
-- autovacuum_vacuum_scale_factor = 0.01   (trigger after 1% dead tuples)
-- autovacuum_vacuum_threshold = 50         (min dead tuples before trigger)
-- autovacuum_analyze_scale_factor = 0.05
```

## Memory Tuning Profile

```ini
# Server with 32GB RAM, SSD, 16 cores
shared_buffers = 8GB              # 25% of RAM
effective_cache_size = 24GB       # 75% of RAM
maintenance_work_mem = 2GB
work_mem = 32MB
wal_buffers = 64MB
random_page_cost = 1.1            # SSD
effective_io_concurrency = 200    # SSD
max_worker_processes = 16
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
```

## Production Debugging Workflow

```bash
# 1. Find what's slow
SELECT pid, now() - query_start AS duration, state, query
FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC;

# 2. Cancel or terminate
SELECT pg_cancel_backend(pid);     -- Cancel query
SELECT pg_terminate_backend(pid);  -- Kill connection

# 3. Check locks
SELECT blocked.pid AS blocked_pid, blocking.pid AS blocking_pid, blocked.query AS blocked_query
FROM pg_locks blocked
JOIN pg_locks blocking ON blocking.locktype = blocked.locktype AND blocking.database = blocked.database
  AND blocking.relation = blocked.relation AND blocking.mode = blocked.mode
WHERE NOT blocked.granted;

# 4. Analyze wait events
SELECT wait_event_type, wait_event, count(*) FROM pg_stat_activity
WHERE state != 'idle' AND wait_event IS NOT NULL GROUP BY 1, 2 ORDER BY 3 DESC;
```

## Anti-Patterns

| Anti-Pattern | Why It Hurts | Fix |
|-------------|-------------|-----|
| `SELECT *` in production | I/O waste, index-only scan kills | Name columns explicitly |
| No `LIMIT` on queries | Memory blowup on large tables | Always set `LIMIT` |
| Indexing every column | Write slowdown, disk bloat | Monitor `idx_scan`; drop unused |
| Huge `work_mem` | OOM from parallel sorts | Start low, increase incrementally |
| `VACUUM FULL` on busy tables | Long exclusive lock | Use `pg_repack` instead |
| No `pg_stat_statements` | Tuning blind | `shared_preload_libraries = 'pg_stat_statements'` |

## Common Troubleshooting Sequences

```bash
# Slow query
EXPLAIN (ANALYZE, BUFFERS) → check seq_scan → add index → ANALYZE → re-check

# High CPU
pg_stat_activity → top CPU queries → pg_stat_statements → add index / tune work_mem

# Connection spikes
SELECT count(*) FROM pg_stat_activity → check state → add pgbouncer → tune max_connections

# Disk growing fast
pg_stat_user_tables.n_dead_tup → tune autovacuum → VACUUM → check WAL archive retention

# Lock contention
pg_locks with NOT granted → find blocking pid → cancel or tune query → add index
```
