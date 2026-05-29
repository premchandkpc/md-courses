# PostgreSQL Replication, Scaling & High Availability

## Streaming Replication (Read Replicas)

### Setup Master-Replica

```sql
-- On Master:
-- 1. Set replication user
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'password';

-- 2. Configure postgresql.conf
max_wal_senders = 3         # Max concurrent replicas
wal_level = replica          # Enable WAL for replication
wal_keep_size = 1GB          # Keep WAL for replay

-- 3. Configure pg_hba.conf
host  replication  replicator  replica_ip/32  md5
```

```bash
# On Replica:
# 1. Get base backup
pg_basebackup -h master_ip -D /var/lib/postgresql/data -U replicator -v -P

# 2. Create standby.signal (tells PostgreSQL to be replica)
touch /var/lib/postgresql/data/standby.signal

# 3. Configure recovery.conf
primary_conninfo = 'host=master_ip user=replicator password=password'
recovery_target_timeline = 'latest'

# 4. Start PostgreSQL
pg_ctl start -D /var/lib/postgresql/data
```

### Monitoring Replication

```sql
-- On Master: Check connected replicas
SELECT client_addr, client_hostname, usename, state, sent_lsn, write_lsn
FROM pg_stat_replication;

-- Check replication lag
SELECT now() - pg_last_xact_replay_time() AS replication_lag;

-- On Replica: Confirm replication status
SELECT pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn();
```

---

## Logical Replication (Version 10+)

### Publication-Subscription Model

```sql
-- On Master (Publisher):
CREATE PUBLICATION all_tables FOR ALL TABLES;

-- Publish specific table
CREATE PUBLICATION orders_pub FOR TABLE orders;

-- On Replica (Subscriber):
CREATE SUBSCRIPTION orders_sub CONNECTION 'host=master_ip user=replicator password=pwd database=mydb'
PUBLICATION orders_pub;

-- Monitor subscription
SELECT * FROM pg_stat_subscription;
```

**Advantage over streaming replication:**
- Logical changes only (DML), not physical WAL
- Can replicate to older PostgreSQL versions
- Row filtering possible
- Column subsetting supported

---

## Failover Strategies

### Manual Failover

```sql
-- On Replica when Master fails:
SELECT pg_promote();  -- Promote to master

-- Or on standby:
pg_ctl promote -D /var/lib/postgresql/data
```

### Automated Failover with Patroni

```yaml
# patroni.yml
scope: postgres_cluster
name: replica1

etcd:
  hosts:
    - 127.0.0.1:2379

postgresql:
  data_dir: /var/lib/postgresql/data
  parameters:
    max_connections: 1000
    
# With Patroni:
# - Automatic failover <30 seconds
# - Member discovery via etcd
# - Health checks
```

### pg_auto_failover

```bash
# Setup monitor server
pg_autoctl create monitor --pgctl /usr/bin/pg_ctl

# Setup master
pg_autoctl create postgres --pgctl /usr/bin/pg_ctl --auth trust

# Setup replica
pg_autoctl create postgres --pgctl /usr/bin/pg_ctl --auth trust --monitor <monitor_url>

# Automatic failover on master failure
```

---

## Horizontal Scaling Patterns

### Read Replicas for Load Balancing

```javascript
// Application level routing
const pool = require('pg').Pool;
const readPool = new Pool({ host: 'replica1', user: 'app' });
const writePool = new Pool({ host: 'master', user: 'app' });

// Write to master
writePool.query('UPDATE users SET last_login=NOW() WHERE id=$1', [userId]);

// Read from replica (eventual consistent)
readPool.query('SELECT * FROM users WHERE id=$1', [userId]);
```

**Configuration:** 1 Master + 2-5 Replicas typical

### Connection Pooling (pgBouncer)

```ini
# pgbouncer.ini
[databases]
mydb = host=master port=5432 dbname=mydb user=app

[pgbouncer]
pool_mode = transaction  # Per-transaction pooling
max_client_conn = 1000
default_pool_size = 25
```

**Pooling modes:**
- `session`: Connection per user (high overhead)
- `transaction`: Connection per transaction (balanced)
- `statement`: Connection per query (low overhead, careful with transactions)

---

## Sharding & Partitioning

### Declarative Partitioning (9.6+)

```sql
-- Range partition by date
CREATE TABLE events (
  id BIGSERIAL,
  event_date DATE,
  event_data JSONB
) PARTITION BY RANGE (event_date);

CREATE TABLE events_2025_01 PARTITION OF events
  FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE events_2025_02 PARTITION OF events
  FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Query all partitions transparently
SELECT COUNT(*) FROM events;  -- Scans all partitions

-- Maintenance (drop old partition, not truncate)
DROP TABLE events_2024_01;  -- Fast!
```

**Benefits:**
- Query pruning (ignore old partitions)
- Parallel queries
- Maintenance windows per partition
- Archive via detaching partition

### Application-Level Sharding

```sql
-- Shard by user_id (application determines shard)
-- Shard1: user_id % 3 = 0
-- Shard2: user_id % 3 = 1
-- Shard3: user_id % 3 = 2

-- Application code
function getShardForUser(userId) {
  return 'shard' + (userId % 3 + 1);
}

// Query specific shard
const shard = getShardForUser(userId);
const conn = connections[shard];  // Get connection to shard
const result = await conn.query('SELECT * FROM orders WHERE user_id=$1', [userId]);
```

---

## Backup & Disaster Recovery

### PITR (Point-In-Time Recovery)

```bash
# Continuous WAL archiving
archive_command = 'test ! -f /wal_archive/%f && cp %p /wal_archive/%f'
archive_mode = on

# Backup database
pg_basebackup -h localhost -D /backups/postgres_base -Ft -z -P

# WAL files accumulate in /wal_archive/
# Recovery: Restore base backup + apply WAL up to timestamp
```

### Recovery Steps

```bash
# 1. Stop PostgreSQL
pg_ctl stop

# 2. Restore base backup
cd /var/lib/postgresql/data
rm -rf *
tar xzf /backups/postgres_base.tar.gz

# 3. Create recovery.conf
cat > recovery.conf <<EOF
restore_command = 'cp /wal_archive/%f %p'
recovery_target_timeline = 'latest'
recovery_target_time = '2025-05-29 14:30:00'
EOF

# 4. Start PostgreSQL (replays WAL to target time)
pg_ctl start
```

---

## Advanced Tuning for Scale

### Vacuum & Autovacuum Tuning

```sql
-- Check dead rows
SELECT n_live_tup, n_dead_tup, last_vacuum, last_autovacuum
FROM pg_stat_user_tables
WHERE relname = 'orders';

-- Aggressive vacuum for high-update tables
ALTER TABLE orders SET (
  autovacuum_vacuum_scale_factor = 0.01,  # 1% trigger
  autovacuum_vacuum_cost_delay = 10,      # Faster
  autovacuum_vacuum_cost_limit = 1000     # Higher limit
);
```

### Work Memory for Sorts

```sql
-- Per operation memory
SET work_mem = '256MB';  # Per sort operation

-- Large aggregation
SELECT user_id, COUNT(*) OVER (ORDER BY created_at)
FROM orders
ORDER BY created_at;  # Needs work_mem

-- Monitor memory usage
SELECT query, mean_exec_time, mean_memory
FROM pg_stat_statements
ORDER BY mean_memory DESC;
```

### Parallel Query Execution

```sql
-- Enable parallelism
SET max_parallel_workers_per_gather = 4;
SET max_parallel_workers = 4;

-- Large aggregate on huge table (will parallelize)
SELECT COUNT(*), AVG(amount)
FROM orders
WHERE created_at > '2025-01-01';

-- Check if parallel used
EXPLAIN SELECT COUNT(*), AVG(amount)
FROM orders
WHERE created_at > '2025-01-01';
-- Look for "Gather" nodes in plan
```

---

## Multi-Region Deployment

### Cross-Region Replication

```
Region 1 (US-East)
├─ Master
└─ Local Replica

    ↓ Streaming WAL

Region 2 (Europe)
└─ Cross-region Replica (async)

Replication lag: 100-500ms typical
```

### Implementation

```sql
-- Region 1 Master (sends WAL)
max_wal_senders = 5

-- Region 2 Replica (receives WAL)
primary_conninfo = 'host=us_east_master.example.com user=replicator'

-- Monitor cross-region lag
SELECT now() - pg_last_xact_replay_time() AS lag;
```

**Trade-offs:**
- Write latency: Replicated after primary commit
- Read consistency: Eventually consistent (lag)
- Cost: Double bandwidth consumption
- Failover: Manual (network isolation risk)

---

## Cost Analysis: Scaling to 1TB

```
Single Master (RDS Large):
- $2,000/month
- 500GB database
- 50K connections max

Master + 2 Read Replicas (RDS Large):
- $6,000/month (3 × $2K)
- Load balanced reads
- 150K concurrent connections

Multi-region (Master + Regional Replicas):
- $8,000/month
- Cross-region PITR
- Disaster recovery

Auto-scaling (Managed):
- $10,000+/month
- Automatic failover
- Monitoring included
```

---

## Best Practices for Scale

1. **Replication lag:** Monitor <100ms. Increase wal_senders if lagging.
2. **Read routing:** Direct reads to replica, writes to master.
3. **Partitioning:** By time (daily), by user (app-level), or by range.
4. **Pooling:** Use pgBouncer for 100+ connections.
5. **Vacuum:** Aggressive for high-update tables (orders, sessions).
6. **Backups:** 24-hour PITR minimum, test recovery monthly.
7. **Monitoring:** Track replica lag, connections, slow queries.
8. **Failover:** Automate with Patroni for <30s recovery.

---

## Summary

- **Streaming Replication**: Master-replica for reads scaling
- **Logical Replication**: Selective, version-tolerant replication
- **Failover**: Patroni/pg_auto_failover for automatic recovery
- **Partitioning**: Range partitions for time-series, app-level shards for user data
- **Backup**: PITR with base backup + WAL archiving
- **Multi-region**: Cross-region async replica for DR, higher latency

Next: [[../COMPARISON_GUIDE.md|Database Comparison & Selection]]

---

**See Also:**
- [[01-advanced-optimization.md|Query Optimization]]
- [[../01-overview.md|PostgreSQL Features]]
- [[../../dynamodb/06-scaling/01-global-tables.md|DynamoDB Multi-region]]
