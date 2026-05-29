# Topic 10: Database Replication & Multi-Master Architectures

**Level:** Intermediate-Advanced | **Time:** 60 mins | **Production Critical:** ⭐⭐⭐⭐

---

## Overview

Replication = keeping copies of data synchronized across multiple servers. Why? Failover (if primary dies, promote replica), read scaling (queries hit replicas), geographic distribution (low latency for global users), and high availability. This guide covers single-master (primary-replica), multi-master (bidirectional), and the tradeoffs.

**Why this matters:**
- Instagram: Replication to 3+ regions = 99.99% uptime
- Netflix: Multi-master replication = no single point of failure
- Interview prep: "How would you scale reads without replicating the database?"
- Common pitfall: Replication lag causes inconsistency (user sees stale data)

**Key metrics:**
- **Replication lag:** Time between write on primary → visible on replica (goal: <100ms)
- **RTO:** If primary fails, time to promote replica (goal: <5 mins)
- **RPO:** Data loss if primary fails (goal: zero with sync replication)

---

## 1. Replication Architectures

### Architecture 1: Single-Master (Primary-Replica)

Primary accepts all writes. Replicas handle reads asynchronously.

```
                    Writes
                      ↓
    ┌─────────────────────────────┐
    │    Primary Database         │
    │    ├─ Tables                │
    │    ├─ Indexes               │
    │    └─ WAL (redo logs)       │
    └────────┬────────────────────┘
             │
        WAL Stream (async)
             │
    ┌────────▼────────┬───────────┬──────────┐
    │   Replica 1     │ Replica 2 │ Replica 3│
    │   (read-only)   │ (readonly)│ (readonly)
    └─────────────────┴───────────┴──────────┘
         ↑ Read queries (app distributes)
```

**Characteristics:**
- Writes: Always go to primary
- Reads: Can hit replicas (lower latency, less load on primary)
- Replication: Async (replication lag = 1-100ms typical)
- Failover: Manual or semi-automatic

**PostgreSQL Single-Master Example**
```bash
# Primary setup (primary.conf)
wal_level = replica
max_wal_senders = 10
hot_standby = on

# Replica setup: connects to primary, streams WAL
primary_conninfo = 'host=primary.example.com user=replication password=xxx'
recovery_target_timeline = 'latest'

# Promotion (if primary fails):
pg_ctl promote -D /var/lib/postgresql/14/main

# Now replica is new primary (read-write)
```

**Pros:**
- Simple: Clear write path (primary only)
- Consistent: No write conflicts
- Read-heavy apps: Offload reads to replicas

**Cons:**
- Single point of failure (primary dies = 5+ min recovery)
- Replication lag (replica sees stale data temporarily)
- Cascading failures (if primary and replica both fail = data loss)

---

### Architecture 2: Multi-Master (Bidirectional Replication)

Every database can accept writes. Changes replicated bidirectionally.

```
    ┌──────────────────┐         ┌──────────────────┐
    │  Primary A       │◄────────┤  Primary B       │
    │  ├─ Tables       │ Replicate│  ├─ Tables      │
    │  └─ Write-ahead  │         │  └─ Write-ahead │
    │    logs          │         │    logs          │
    └────────▲─────────┘         └────────▲─────────┘
             │                            │
          Writes                       Writes
          (local)                      (local)
             │                            │
        ┌────▼────────────────────────────▼────┐
        │  Application (any server)             │
        │  Can write to A or B                  │
        └──────────────────────────────────────┘
```

**Characteristics:**
- Writes: Can go to either A or B
- Reads: Can hit either A or B
- Replication: Bidirectional (conflicts possible)
- Failover: Automatic (no promotion needed)

**MySQL Multi-Master Example (Percona XtraDB Cluster)**
```bash
# Both nodes accept writes
# Synchronous replication (commit waits for group consensus)

# Node A config
[mysqld]
wsrep_provider = /usr/lib64/galera4/libgalera_smm.so
wsrep_cluster_name = "my-cluster"
wsrep_cluster_address = "gcomm://node-a.example.com,node-b.example.com"
wsrep_node_name = "node-a"
wsrep_node_address = "192.168.1.10:4567"

# Node B config (same, different address)
wsrep_node_address = "192.168.1.20:4567"

# Application writes to any node
INSERT INTO users VALUES (...); -- On Node A
INSERT INTO posts VALUES (...); -- On Node B
SELECT * FROM users; -- Visible on both immediately (sync replication)
```

**Pros:**
- High availability: No single point of failure
- Load distribution: Writes spread across nodes
- Disaster recovery: Any node can fail, cluster survives

**Cons:**
- Conflict handling: If both nodes write same row simultaneously → need merge logic
- Write latency: Sync replication = slower commits (wait for group consensus)
- Network split risk: If nodes lose connection, split-brain possible

---

### Architecture 3: Star Replication (Hub-Spoke)

Primary + replicas, but one replica acts as intermediate hub.

```
    Primary
        ↓ WAL
    Replica 1 (hub)
        ├─ WAL → Replica 2
        ├─ WAL → Replica 3
        └─ WAL → Replica 4
```

**Use case:** Cascading replication reduces primary load. Used when 10+ replicas needed.

---

## 2. Replication Methods

### Method 1: Statement-Based Replication

Replicate the SQL statements themselves.

```
Primary:
  UPDATE users SET status = 'active' WHERE created_at > NOW() - INTERVAL 1 DAY;

Replica receives:
  Same SQL statement → executes locally
```

**Problem: Non-deterministic functions**
```
Primary executes:
  INSERT INTO logs (timestamp) VALUES (NOW()); -- 2026-05-30 14:32:15.123

Replica executes same statement:
  INSERT INTO logs (timestamp) VALUES (NOW()); -- 2026-05-30 14:32:15.456 (different!)
```

**Used by:** MySQL binlog (with caution)

---

### Method 2: Row-Based Replication

Replicate actual changed data (before/after).

```
Primary:
  UPDATE users SET status = 'active' WHERE id = 5;

Replica receives:
  Row: id=5, old_status='inactive', new_status='active' → Apply exact change
```

**Pros:**
- Deterministic (same result on all nodes)
- Correct with non-deterministic functions
- Easy to reason about

**Cons:**
- Large replication overhead (full rows, not just statement)
- Slower for bulk operations

**Used by:** PostgreSQL WAL streaming, MySQL binlog format=ROW

---

### Method 3: Log-Based Replication (Write-Ahead Logs)

Replicate low-level log records (most common for modern DBs).

```
Primary:
  1. Write to WAL (Write-Ahead Log)
  2. Commit transaction
  3. Stream WAL to replicas

Replica:
  1. Receive WAL record
  2. Apply change
  3. Confirm receipt
```

**Best for:** PostgreSQL, Amazon Aurora, Google Cloud SQL

---

## 3. Synchronous vs Asynchronous Replication

### Asynchronous (Default)

Primary commits immediately. Replica catches up later.

```
Timeline:
t=0ms   : Write to primary, commit ✓ (return to app immediately)
t=1ms   : Async send WAL to replica
t=50ms  : Replica applies change
        → Replication lag = 50ms

Problem: If primary crashes at t=25ms:
  - App thinks data saved ✓
  - Replica never received it ✗
  - Data loss
```

**RTO:** 5-10 minutes (detect failure, promote replica)  
**RPO:** Data loss up to seconds

**Used by:** Most read-heavy systems (acceptable RPO)

---

### Synchronous (Strict Consistency)

Primary waits for replica acknowledgment before committing.

```
Timeline:
t=0ms   : Write to primary, wait for replica
t=1ms   : Async send WAL to replica
t=50ms  : Replica acknowledges receipt, commit ✓
        → Return to app (total latency: 50ms)

Benefit: Zero data loss (replica has data before commit)

Problem: Slow writes (add 50-100ms latency per write)
```

**RTO:** <1 minute (automatic, zero replication lag)  
**RPO:** Zero (no data loss)

**Used by:** Mission-critical systems (finance, healthcare)

**PostgreSQL Synchronous Replication**
```bash
# primary.conf
synchronous_commit = remote_apply
synchronous_standby_names = 'standby1, standby2'

# Write won't commit until remote_apply = replica has applied to disk
# Slow but safe
```

---

## 4. Real Production Pattern: Read Replicas for Scaling

Primary handles writes. Replicas handle reads (10x higher throughput).

```
Application:
  ├─ SELECT queries → Route to read-replicas (load balanced)
  └─ INSERT/UPDATE/DELETE → Route to primary

Typical split:
  - Writes: 5% of traffic (primary)
  - Reads: 95% of traffic (replicas)
  
Result:
  - Primary: 100 RPS (write-only)
  - Each replica: 1900 RPS (read-only)
  → Total: 100 writes + 1900 reads per replica = 2000 RPS throughput
```

**Implementation: Read/Write Splitting**

```javascript
import pg from 'pg';

// Connection pools
const primaryPool = new pg.Pool({
  host: 'primary.example.com', // Write endpoint
  max: 10 // Fewer connections needed
});

const readReplicaPools = [
  new pg.Pool({ host: 'replica1.example.com', max: 100 }),
  new pg.Pool({ host: 'replica2.example.com', max: 100 }),
  new pg.Pool({ host: 'replica3.example.com', max: 100 })
];

let replicaIndex = 0;

// Route reads to replicas (round-robin)
async function query(sql, params, isWrite = false) {
  if (isWrite) {
    return primaryPool.query(sql, params); // Always primary
  } else {
    // Load balance across replicas
    const pool = readReplicaPools[replicaIndex % readReplicaPools.length];
    replicaIndex++;
    return pool.query(sql, params);
  }
}

// Usage
await query('INSERT INTO users VALUES ($1)', [user], true); // Write to primary
const users = await query('SELECT * FROM users'); // Read from replica
```

**Replication Lag Handling**
```javascript
// If replica falls behind (lag > 100ms), read from primary
async function queryWithFallback(sql, params, isWrite = false) {
  const maxLag = 100; // ms

  if (isWrite) {
    return primaryPool.query(sql, params);
  }

  try {
    // Check replication lag on replica
    const [replicaLag] = await readReplica.query(
      'SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))::int as lag_seconds'
    );

    if (replicaLag.rows[0].lag_seconds * 1000 > maxLag) {
      // Replica too far behind, read from primary
      console.warn(`Replica lag too high (${replicaLag}s), reading from primary`);
      return primaryPool.query(sql, params);
    }

    return readReplica.query(sql, params);
  } catch (err) {
    // Replica down, fallback to primary
    console.error('Replica query failed, reading from primary', err);
    return primaryPool.query(sql, params);
  }
}
```

---

## 5. Replication Across Databases

### PostgreSQL Primary-Replica

```bash
# Streaming replication (modern, preferred)
# Primary streams WAL continuously to replica

# Setup:
# 1. Primary: pg_basebackup from replica
# 2. Replica: Start recovery process
# 3. Primary: Stream WAL to replica

# Monitor:
SELECT slot_name, restart_lsn FROM pg_replication_slots;
SELECT pid, usename, replay_time FROM pg_stat_replication;
```

---

### MySQL Semi-Synchronous Replication

```bash
# Primary waits for at least 1 replica to ACK

INSTALL PLUGIN rpl_semi_sync_master SONAME 'semisync_master.so';
SET GLOBAL rpl_semi_sync_master_enabled = ON;

# Replica
INSTALL PLUGIN rpl_semi_sync_slave SONAME 'semisync_slave.so';
SET GLOBAL rpl_semi_sync_slave_enabled = ON;

# After write on primary:
# 1. Write to primary binary log
# 2. Wait up to rpl_semi_sync_master_timeout (10 sec) for replica ACK
# 3. If ACK → commit (sync)
# 4. If timeout → commit anyway (fallback to async)
```

---

### MongoDB Replica Sets

```javascript
// 3-node replica set (Primary + 2 Secondaries)
rs.initiate({
  _id: 'rs0',
  members: [
    { _id: 0, host: 'mongo1:27017', priority: 2 }, // Primary
    { _id: 1, host: 'mongo2:27017', priority: 1 }, // Secondary
    { _id: 2, host: 'mongo3:27017', priority: 1 }  // Secondary
  ]
});

// Write concern (synchronous replication)
db.users.insertOne(
  { name: 'Alice' },
  { writeConcern: { w: 'majority', j: true } }
  // w: 'majority' = wait for majority of nodes to acknowledge
  // j: true = wait for journal write (disk durable)
);

// Read preference
db.users.find({}, { readPreference: 'secondaryPreferred' });
// Try secondary first, fallback to primary if secondary unavailable
```

---

## 6. Common Replication Issues & Fixes

### Issue 1: Replication Lag

Replica falls behind primary (queries see stale data).

```
Cause: Replica too slow to apply changes
       (large writes on primary, slow disk on replica)

Symptoms:
  - SELECT on replica returns stale data
  - User sees old information

Fix:
  - Monitor: SELECT * FROM pg_stat_replication; (lag_bytes)
  - Upgrade replica hardware (faster CPU, SSD)
  - Reduce write batch sizes on primary
  - Use read-only replicas (no heavy queries)
```

---

### Issue 2: Replication Broken

Replica falls out of sync (corruption, WAL mismatch).

```
Cause: Network failure, replica restart during replication, WAL segment removed

Symptoms:
  - Replication thread stops
  - Error: "could not write block ... beyond end of segment"

Fix:
  - Option 1: pg_basebackup (full resync from primary)
  - Option 2: Recover from backup + replay WAL to catch up
  - Option 3: Cold start replica from scratch
```

---

### Issue 3: Write Amplification in Multi-Master

Same row written on both nodes simultaneously.

```
Timeline:
t=0ms  : App writes row X on Node A
t=0ms  : App writes same row X on Node B (different value)

t=5ms  : Node A's change replicated to Node B
t=5ms  : Node B's change replicated to Node A

Result: Conflict!
        Node A has B's value, Node B has A's value (inconsistent)

Fix (depends on DB):
  - Last-write-wins: Timestamp decides winner
  - Custom merge logic: App-defined conflict resolution
  - Avoid: Use primary-replica (no conflicts)
  - Detect: Application layer handles conflicts
```

---

## 7. Replication Checklist

- [ ] Replication type chosen (primary-replica vs multi-master)
- [ ] Synchronous vs async decided (RPO requirement)
- [ ] Replication lag monitoring configured
- [ ] Read/write splitting implemented (if scaling reads)
- [ ] Failover process documented and tested
- [ ] Backup strategy includes replicas
- [ ] Replica integrity checked monthly
- [ ] Data verification (row count, checksums) on replicas
- [ ] Network: Low-latency link between primary/replica (same datacenter or region)
- [ ] Alerts: Replication lag > threshold, replication broken, replica down

---

## Interview Prep Questions

1. **"How would you scale read traffic without sharding?"**
   - Answer: Read replicas. Primary handles writes, replicas handle 95% of reads. Use connection pooling + read/write splitting.

2. **"What's the difference between async and sync replication?"**
   - Answer: Async = faster writes, RPO = data loss possible. Sync = slower writes, RPO = zero. Trade latency for consistency.

3. **"If replication lag is 5 seconds, should you read from primary or replica?"**
   - Answer: Depends on tolerance. For financial transactions (strict consistency): primary. For analytics/caching: replica OK.

4. **"How would you detect a broken replica?"**
   - Answer: Monitor replication lag (if increasing or stuck = broken). Query replica with specific value, verify on primary. Monthly integrity check (SELECT COUNT, CHECKSUM).

5. **"What causes write amplification in multi-master?"**
   - Answer: Concurrent writes to same row on different nodes. Both replicate bidirectionally → conflicts. Solved with last-write-wins or custom merge logic.

---

## See Also

### Phase 7.1 Related Topics

- [Disaster Recovery](./09-disaster-recovery.md) — Replication strategy choice
- [Database Sharding](./11-database-sharding.md) — Multi-shard replication topology
- [Connection Pooling](./08-connection-pooling.md) — Read replicas scaling

### Additional Resources

- PostgreSQL Streaming Replication: Official docs
- MySQL Replication: Binlog format, semi-sync
- MongoDB Replica Sets: Consensus-based
- Percona XtraDB Cluster: Galera synchronous replication
- Patroni: Automatic failover for PostgreSQL
- Vitess: MySQL sharding + replication
