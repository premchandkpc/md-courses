---
title: Topic 08: Connection Pooling & Resource Management
topic: 08-databases
difficulty: intermediate
time: 45
paths:
  - backend-junior
  - data
  - backend-senior
---

# Topic 08: Connection Pooling & Resource Management

[🎨 Interactive Visualization](../../html/08-connection-pooling-viz.html)

mins | **Production Critical:** ⭐⭐⭐

---

## Overview

Every database connection is expensive: TCP handshake (50-100ms), authentication, memory allocation. Opening a new connection per query = 🔥 disaster. Connection pooling reuses connections, reducing latency 10-100x and increasing throughput 5-20x.

**Why this matters:**
- A 1000-RPS API without pooling = 1000 concurrent DB connections (💥 crash)
- Same API with pooling = 20-50 connections (sustainable)
- Interview question: **"How do you scale database connections?"**

---

## The Problem: Naive Connection Management

### Without Connection Pooling

```
┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Request │→ │ New conn │→ │  Query   │→ │  Close   │
└─────────┘  │ (50ms)   │  │ (5ms)    │  │ (10ms)   │
             └──────────┘  └──────────┘  └──────────┘
             
Total: 65ms per request (80% overhead)
At 1000 RPS: 1000 concurrent connections needed
DB max connections: 100 → 90% rejected ❌
```

### With Connection Pooling

```
┌─────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐
│ Request │→ │Reuse conn│→ │  Query   │→ │Return pool │
└─────────┘  │(1-3ms)   │  │(5ms)     │  │(instant)   │
             └──────────┘  └──────────┘  └────────────┘
             
Total: 6-8ms per request (90% faster)
At 1000 RPS: 20-50 connections needed (all served)
DB max connections: 100 → 0% rejected ✅
```

---

## How Connection Pooling Works

### Architecture: Pool Lifecycle

```
1. INITIALIZATION
   ┌─────────────────┐
   │ Create pool     │
   │ (min=5 conns)   │
   └─────────────────┘
         ↓
2. WAITING (idle connections ready)
   ┌──────┐  ┌──────┐  ┌──────┐
   │Conn1 │  │Conn2 │  │Conn3 │
   │(idle)│  │(idle)│  │(idle)│
   └──────┘  └──────┘  └──────┘
   
   Request arrives ↓
   
3. ALLOCATION
   ┌──────┐  ┌──────┐  ┌──────┐
   │Conn1*│  │Conn2 │  │Conn3 │ *in use
   │      │  │(idle)│  │(idle)│
   └──────┘  └──────┘  └──────┘
   
4. EXECUTION
   Query runs on Conn1
   
5. RETURN
   ┌──────┐  ┌──────┐  ┌──────┐
   │Conn1 │  │Conn2 │  │Conn3 │
   │(idle)│  │(idle)│  │(idle)│
   └──────┘  └──────┘  └──────┘
   
6. SCALING (demand > available)
   ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
   │Conn1*│  │Conn2*│  │Conn3*│  │Conn4 │ Create new
   └──────┘  └──────┘  └──────┘  └──────┘
```

### Key Concepts

**1. Pool Size Parameters**

```
min_size=10        (always maintain 10 idle connections)
max_size=50        (create up to 50 total connections)
queue_timeout=5s   (wait max 5s for available connection)
idle_timeout=10m   (close idle connections after 10 mins)
```

**2. Connection States**

| State | Duration | Cost |
|-------|----------|------|
| Creation | 50-100ms | High (TCP + auth) |
| Idle (in pool) | 0ms | Free (reuse) |
| Active (in use) | 5-100ms | Paid (running query) |
| Closing | 5-10ms | Low |

**3. Pool Metrics (Monitor These)**

```
Active connections:      15/50 (30% utilization) ✅
Idle connections:        10/50 (20% available)
Waiting requests:        0 (no queue)
Avg wait time:           0.5ms (instant)
Connections/sec created: 0.1 (stable)
```

---

## Core Pooling Strategies

### Strategy 1: Resource-Based Pooling (Most Common)

Each application server maintains its own pool.

```
┌─────────────────────────────────────────┐
│ Web Application (4 servers)             │
├─────────┬─────────┬─────────┬─────────┤
│Server 1 │Server 2 │Server 3 │Server 4 │
│Pool 10  │Pool 10  │Pool 10  │Pool 10  │
│conns    │conns    │conns    │conns    │
└─────────┴─────────┴─────────┴─────────┘
              ↓ TCP connections
         ┌──────────────┐
         │ Database     │
         │(sees 40 max) │
         └──────────────┘

Pros: Simple, no bottleneck
Cons: Each server maintains own pool (wasteful if 1 server slow)
```

**Example Configuration:**

```yaml
# PostgreSQL pooling config
pool:
  min_size: 10
  max_size: 50
  queue_timeout: 5s
  idle_timeout: 10m
  connection_timeout: 3s
  
# Typical deployment:
# 4 web servers × 50 conns = 200 connections to DB
# Database max: 500 connections
# Reserve: 300 for batch jobs, maintenance
```

### Strategy 2: PgBouncer / ProxySQL (Pooling Middleware)

Central pool server between app + database.

```
┌─────────────────────────────────┐
│ Web Servers (10 instances)      │
│ (each with 5 conns to pgbouncer)│
└─────────────────────────────────┘
         10 × 5 = 50 connections
              ↓
       ┌──────────────────┐
       │ PgBouncer Pool   │
       │ (session mode)   │
       │ ~50 idle conns   │
       │ 1-2 conns/user   │
       └──────────────────┘
              ↓ 10-20 TCP connections
         ┌──────────────┐
         │ Database     │
         │ (sees 20)    │
         └──────────────┘

Pros: Centralized, reduces DB connections 5-10x
Cons: Extra hop (1-2ms latency), single point of failure
```

**When to use:**
- Many app servers (>5) connecting to one DB
- Database hitting max connection limits
- Need to rebalance connections across replicas

---

## Connection Pool Implementation Patterns

### Pattern 1: SDK Built-in Pool (Node.js/JavaScript)

```javascript
// pg library (PostgreSQL)
const { Pool } = require('pg');

const pool = new Pool({
  user: 'user',
  password: 'password',
  host: 'localhost',
  port: 5432,
  database: 'mydb',
  max: 50,           // max pool size
  min: 10,           // min pool size
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Query uses pool internally
pool.query('SELECT * FROM users WHERE id = $1', [userId])
  .then(result => console.log(result.rows))
  .catch(err => console.error('Query failed', err));

// After 30 seconds idle, unused connections close
// If all 50 in use + new request: queue until one available
```

### Pattern 2: ORM Pool (Django/SQLAlchemy)

```python
from sqlalchemy import create_engine

# Create engine with pooling
engine = create_engine(
    'postgresql://user:password@localhost/mydb',
    pool_size=20,              # connections to keep open
    max_overflow=30,           # additional connections if needed
    pool_recycle=3600,         # recycle connections every 1 hour
    pool_pre_ping=True,        # check connection health before use
)

# ORM uses pool automatically
with engine.connect() as conn:
    result = conn.execute(text('SELECT * FROM users'))
    
# Connection returned to pool after with block exits
```

### Pattern 3: Manual Pool Management (Go)

```go
package main

import (
    "database/sql"
    _ "github.com/lib/pq"
)

func main() {
    db, _ := sql.Open("postgres", "postgres://user:pass@localhost/mydb")
    
    // Configure pool
    db.SetMaxOpenConns(50)    // max connections
    db.SetMaxIdleConns(10)    // idle connections to keep
    db.SetConnMaxLifetime(time.Hour) // recycle after 1 hour
    
    // Query uses pool
    row := db.QueryRow("SELECT name FROM users WHERE id = $1", userId)
}
```

---

## Real Production Example: Handling Traffic Spikes

### Scenario: 10x Traffic Spike

**Before (no pooling):**
```
Baseline: 100 RPS
├─ Connections/request: 1
├─ Active connections: 100
├─ Avg response: 65ms (50ms pool creation + 15ms query)

Spike: 1000 RPS
├─ Need: 1000 new connections/sec
├─ Database max: 500 connections
├─ Result: 500 rejected (ERR_TOO_MANY_CONNECTIONS) ❌
├─ Users see: "Service unavailable"
└─ Lost revenue: All requests during spike
```

**After (with pooling, pool_size=50, 10 servers):**
```
Baseline: 100 RPS
├─ Connections: 50 (reused)
├─ Avg response: 8ms (2ms pool lookup + 6ms query)
├─ Success rate: 100%

Spike: 1000 RPS
├─ Queue length: 0 (immediate dequeue)
├─ Database sees: 50 connections (unchanged)
├─ Avg response: 8-15ms (queue wait + query)
├─ Success rate: 99.9% ✅
└─ Revenue impact: Zero
```

**Metrics comparison:**

| Metric | No Pool | With Pool |
|--------|---------|-----------|
| Latency (p95) | 150ms | 12ms |
| Throughput | 500 RPS | 5000 RPS |
| DB connections | 500 | 50 |
| Success rate | 50% | 99.9% |

---

## Tuning Connection Pool Size

### Formula (Rough)

```
pool_size = (core_count × 2) + effective_spindle_count

For web servers:
pool_size = (4 cores × 2) + 0 = 8 (conservative)
pool_size = (4 cores × 2) + 4 = 12 (typical)

For high-concurrency services:
pool_size = (8 cores × 2) + 8 = 24
```

### Practical Approach: Load Testing

```bash
# Test with incrementally larger pools
# Measure throughput, latency, DB connection count

# Pool size: 5
┌──────────────────────────────┐
│ Throughput: 800 RPS          │
│ P95 latency: 250ms           │
│ DB connections: 5 (maxed out)│
└──────────────────────────────┘

# Pool size: 10
┌──────────────────────────────┐
│ Throughput: 1500 RPS (↑88%)  │
│ P95 latency: 50ms            │
│ DB connections: 10           │
└──────────────────────────────┘

# Pool size: 20
┌──────────────────────────────┐
│ Throughput: 1600 RPS (↑7%)   │
│ P95 latency: 45ms            │
│ DB connections: 20           │
└──────────────────────────────┘
→ Sweet spot: size=10-15 (diminishing returns after)
```

---

## Common Pooling Issues & Solutions

### Issue 1: Exhausted Pool (All connections in use, no idle)

**Symptom:** "Unable to acquire connection" errors, p99 latency spikes

**Cause:**
- Slow queries holding connections
- Connection leak (not returning to pool)
- Blocking code in transaction

**Solution:**
```javascript
// ❌ Bad: Holds connection during sleep
app.get('/slow', async (req, res) => {
  const conn = pool.connect();
  await sleep(5000); // 5 second wait
  const result = await conn.query('SELECT 1');
  res.json(result);
});
// If 50 RPS, all 50 pool connections exhausted waiting

// ✅ Good: Release connection, wait outside
app.get('/slow', async (req, res) => {
  const result = await pool.query('SELECT 1');
  await sleep(5000); // Wait after query, connection released
  res.json(result);
});
```

### Issue 2: Connection Leak

**Symptom:** Connections climb to max, never decrease. Eventually all leak away.

**Cause:** Forgetting to close/return connections

**Solution:**
```go
// ❌ Bad: Connection leak
func handleRequest() {
  conn := pool.Acquire()
  result := conn.Query("SELECT ...")
  // Forgot to release!
}

// ✅ Good: Always release
func handleRequest() {
  conn := pool.Acquire()
  defer conn.Release() // Guaranteed return
  result := conn.Query("SELECT ...")
}

// ✅ Better: Use context manager
func handleRequest() {
  with pool.acquire() as conn:
    result = conn.query("SELECT ...")
  # Automatic release on exit
```

### Issue 3: Stale Connections

**Symptom:** Random "connection lost" errors after idle period

**Cause:** Database closes idle connections; app doesn't know

**Solution:**
```python
# Recycle connections periodically
engine = create_engine(
    'postgresql://...',
    pool_pre_ping=True,      # Test connection before use
    pool_recycle=3600,       # Recycle after 1 hour
)
```

---

## Monitoring Connection Pools

### Essential Metrics

```
1. ACTIVE CONNECTIONS
   Gauge: 15/50 (30% usage)
   Alert: > 90% → increase pool size
   
2. IDLE CONNECTIONS
   Gauge: 10/50 (queued up)
   Alert: 0 → requests queuing
   
3. WAITING REQUESTS
   Counter: 0 currently waiting
   Alert: > 10 → pool exhausted
   
4. POOL WAIT TIME
   Histogram: p50=0.1ms, p95=2ms, p99=50ms
   Alert: p99 > 100ms → pool too small
   
5. CONNECTIONS CREATED/SEC
   Counter: 0.5/sec (stable, not spiking)
   Alert: > 10/sec → pool too small, thrashing
   
6. CONNECTION LIFETIME
   Histogram: avg 15 mins (connections living ~15 mins)
   Low lifetime = too many being recycled
```

### Prometheus Metrics (Example)

```
# HELP db_pool_size_gauge Current pool size
# TYPE db_pool_size_gauge gauge
db_pool_size_gauge{pool="default"} 50

# HELP db_pool_active Current active connections
# TYPE db_pool_active gauge
db_pool_active{pool="default"} 15

# HELP db_pool_idle Current idle connections
# TYPE db_pool_idle gauge
db_pool_idle{pool="default"} 35

# HELP db_pool_wait_time_seconds Connection wait time
# TYPE db_pool_wait_time_seconds histogram
db_pool_wait_time_seconds_bucket{le="0.01", pool="default"} 1000
db_pool_wait_time_seconds_bucket{le="0.1", pool="default"} 1200
db_pool_wait_time_seconds_bucket{le="1"} 1250
```

### Grafana Dashboard Panels

1. **Pool utilization %** — (active / max) × 100
2. **Active connections timeline** — Shows traffic patterns
3. **Wait time p50/p95/p99** — Latency impact
4. **Connections created/sec** — Churn indicator
5. **Failed connection attempts** — Exhaustion events

---

## Database-Specific Pooling

### PostgreSQL: Built-in Limits

```sql
-- Check current connections
SELECT count(*) FROM pg_stat_activity;

-- Max connections setting
SHOW max_connections;  -- typically 100

-- Reserve connections for admin
SHOW superuser_reserved_connections;  -- typically 3
```

**Recommendation:** Set `max_connections = (pool_size × num_servers) + 10`

### MySQL: Max Connection Handling

```sql
-- Check current connections
SHOW PROCESSLIST;
SHOW STATUS LIKE 'Threads_connected';

-- Max connections setting
SHOW VARIABLES LIKE 'max_connections';  -- typically 151

-- Monitor connection saturation
SELECT VARIABLE_VALUE FROM INFORMATION_SCHEMA.GLOBAL_STATUS
WHERE VARIABLE_NAME = 'Threads_connected';
```

### MongoDB: Connection Pool Internals

```javascript
const client = new MongoClient(uri, {
  maxPoolSize: 50,         // max connections
  minPoolSize: 10,         // min connections
  maxIdleTimeMS: 30000,    // close idle after 30s
  waitQueueTimeoutMS: 5000 // timeout if no connection within 5s
});
```

---

## Best Practices Checklist

- [ ] Set `max_pool_size` based on load test (not guesswork)
- [ ] Set `min_pool_size` to ~20% of max (keeps connections warm)
- [ ] Enable `pool_pre_ping` (test connection health)
- [ ] Set `connection_timeout` (fail fast on DB down)
- [ ] Set `idle_timeout` (recycle stale connections)
- [ ] Monitor active/idle/waiting metrics (alert on exhaustion)
- [ ] Test failure modes: what happens if pool exhausted?
- [ ] Load test with 2-3x expected peak traffic
- [ ] Log slow queries (those holding connections)
- [ ] Document pool size rationale (why that number?)

---

## See Also

### Phase 7.1 Related Topics

- [Database Replication](./10-database-replication.md) — Pooling replicates across servers
- [Database Sharding](./11-database-sharding.md) — Pool size considerations with shards
- [Disaster Recovery](./09-disaster-recovery.md) — Pool reconnection after failover

### Additional Resources

- **Topic 09:** Disaster Recovery & Backups
- **Topic 10:** Multi-Region Architecture
- **Per-engine guides:**
  - PostgreSQL pooling (PgBouncer)
  - MySQL pooling (ProxySQL)
  - MongoDB connection management
  - DynamoDB SDK pooling
  - Redis pipelining
