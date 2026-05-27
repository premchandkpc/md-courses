# 🐘 PostgreSQL Internals — Complete Deep Dive

> **Scope**: PostgreSQL process architecture, shared memory, connection lifecycle, shared buffers and buffer manager, MVCC, WAL, query processing (parser/planner/executor), vacuum/autovacuum, indexing (B-tree/GiST/GIN/BRIN/Bloom), replication (streaming/logical), backup/PITR — complete internal architecture of the world's most advanced open-source database.

> **Related**: [01-linux-kernel-architecture.md](../os/01-linux-kernel-architecture.md), [03-memory-management.md](../os/03-memory-management.md), [04-io-models.md](../os/04-io-models.md)

---



```mermaid
graph LR
    CONN["Client<br/>Connection"] --> POST["Postmaster<br/>(Fork Backend)"]
    POST --> BG_WORKER["Backend Process<br/>(Backend)"]
    BG_WORKER --> SH_MEM["Shared Memory<br/>(Shared Buffers / WAL)"]
    BG_WORKER --> QUERY["Query<br/>Executor"]
    QUERY --> PARSER["Parser<br/>(Parse Tree)"]
    PARSER --> PLANNER["Planner<br/>(Query Plan)"]
    PLANNER --> EXEC["Executor<br/>(Run Plan)"]
    EXEC --> BUF_MGR["Buffer Manager<br/>(Shared Buffers)"]
    EXEC --> MVCC["MVCC<br/>(xmin/xmax)"]
    MVCC --> WAL["WAL<br/>(Write-Ahead Log)"]
    WAL --> ARCHIVE["WAL Archive<br/>(Continuous Archival)"]
    style CONN fill:#4a8bc2
    style POST fill:#2d5a7b
    style BG_WORKER fill:#3a7ca5
    style SH_MEM fill:#e8912e
    style QUERY fill:#c73e1d
    style PARSER fill:#6f42c1
    style PLANNER fill:#3fb950
    style EXEC fill:#c73e1d
    style BUF_MGR fill:#e8912e
    style MVCC fill:#3a7ca5
    style WAL fill:#2d5a7b
    style ARCHIVE fill:#e8912e
```

## Table of Contents

1. [Process Architecture](#1-process-architecture)
2. [Shared Memory](#2-shared-memory)
3. [Connection Lifecycle](#3-connection-lifecycle)
4. [Shared Buffers & Buffer Manager](#4-shared-buffers--buffer-manager)
5. [MVCC](#5-mvcc)
6. [Transaction Manager & CLOG](#6-transaction-manager--clog)
7. [WAL — Write-Ahead Log](#7-wal--write-ahead-log)
8. [Query Processing](#8-query-processing)
9. [Vacuum & Autovacuum](#9-vacuum--autovacuum)
10. [Indexing](#10-indexing)
11. [Replication](#11-replication)
12. [Backup & PITR](#12-backup--pitr)
13. [Internals](#13-internals)
14. [Failure Analysis](#14-failure-analysis)
15. [Edge Cases](#15-edge-cases)
16. [Performance](#16-performance)
17. [Simplest Mental Model](#17-simplest-mental-model)

---

## 1. Process Architecture

```
┌────────────────────────────────────────────────────────────┐
│                 PostgreSQL Process Model                    │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐               │
│  │Postmaster│──►│ Backend  │──►│ Backend  │  ...          │
│  │(parent)  │   │(child 1) │   │(child 2) │               │
│  └─────┬────┘   └──────────┘   └──────────┘               │
│        │                                                    │
│        ├──► WAL Writer     ├──► Autovacuum Launcher        │
│        ├──► Checkpointer   ├──► Archiver                   │
│        ├──► Stats Collector├──► WAL Sender                 │
│        └──► Logical Replication Launcher                   │
│                                                             │
│  On connection: postmaster fork() → backend for each conn  │
│  Children share System V shared memory                     │
└────────────────────────────────────────────────────────────┘
```

- **postmaster**: Parent — listens on TCP port 5432, forks for each connection, restarts dead children
- **backend** (child): One per client connection, owns transaction state, per-backend memory (work_mem)
- **wal_writer**: Flushes WAL buffer every WAL_WRITER_FLUSH_MS (default 200ms)
- **checkpointer**: Writes dirty buffers to disk, updates REDO point, writes pg_control
- **bgwriter**: Writes dirty buffers between checkpoints, spreads I/O
- **autovacuum launcher**: Schedules workers based on table stats
- **stats collector**: Collects pg_stat_* via UDP messages from backends
- **wal_sender**: Sends WAL to standbys
- **wal_receiver** (standby): Receives WAL from primary

---

## 2. Shared Memory

```
┌───────────────────────────────────────────────────────────┐
│                PostgreSQL Shared Memory                    │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ shared_buffers (default 128MB, recommended 25% RAM) │   │
│  │ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ │   │
│  │ │buf0│ │buf1│ │buf2│ │... │ │... │ │... │ │bufN│ │   │
│  │ └────┘ └────┘ └────┘ └────┘ └────┘ └────┘ └────┘ │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌─────────────┐ ┌──────┐ ┌──────────┐ ┌───────────────┐ │
│  │ WAL Buffers │ │CLOG  │ │ Lock Mgr │ │  ProcArray   │ │
│  │ (16MB)      │ │      │ │(LWLocks+ │ │ (PGPROC[])   │ │
│  │             │ │      │ │ HWT locks)│ │              │ │
│  └─────────────┘ └──────┘ └──────────┘ └───────────────┘ │
└───────────────────────────────────────────────────────────┘
```

Key shared memory regions:
- **shared_buffers**: Buffer pool (8KB blocks), clock-sweep eviction
- **WAL buffers**: WAL write cache before flush (wal_buffers)
- **CLOG**: Commit log — transaction status bits (2 bits per xid)
- **Lock Manager**: LWLock hash table + heavyweight lock hash table
- **ProcArray**: Array of PGPROC — tracks xmin, xid per backend for snapshot building

---

## 3. Connection Lifecycle

```
Client                   Postmaster                Backend
  │                           │                       │
  │  TCP connect (5432)       │                       │
  │──────────────────────────►│                       │
  │                    fork()│────► backend process   │
  │ StartupMessage           │                       │
  │──────────────────────────────────────────────────►│
  │ Authentication (SCRAM-SHA-256)                    │
  │◄──────────────────────────────────────────────────│
  │ ReadyForQuery ('Z')       │                       │
  │◄──────────────────────────────────────────────────│
  │ Query: SELECT ...                                 │
  │──────────────────────────────────────────────────►│
  │ Result rows                                       │
  │◄──────────────────────────────────────────────────│
  │ Disconnect (EOF)          │                       │
  │──────────────────────────────────────────────────►│
  │                           │◄──── exit ───────────│
```

- pg_hba.conf controls authentication: `host all all 0.0.0.0/0 scram-sha-256`
- StartupMessage: user, database, application_name, protocol version
- SCRAM-SHA-256: Salted Challenge Response — stores salted password hash
- Postmaster receives SIGCHLD on backend exit, cleans up

---

## 4. Shared Buffers & Buffer Manager

```
Buffer Descriptor:
  ┌──────────────────────────────┐
  │ buf_id: 42                   │
  │ tag: {db=12345, rel=67890,  │
  │       fork=MAIN, block=100} │
  │ state: BM_DIRTY | BM_VALID  │
  │ refcount: 2     (pins)      │
  │ usage_count: 3  (clock-swp) │
  │ io_in_progress: false       │
  └──────────────────────────────┘
```

### Buffer Access

```
ReadBuffer(rel, block):
  1. Hash lookup buffer tag → hit → pin, return
  2. Miss → clock-sweep victim → find unpinned buffer
  3. If victim dirty → flush to disk
  4. Read block from disk into victim buffer
  5. Pin, set usage_count=1, return

Clock sweep:
  pointer→ buf0(uc=3) → buf1(uc=0) → buf2(uc=1) → ...
            skip        evict!        decrement→0
```

### Checkpoint Phases

```
1. Checkpoint Begin: WAL record, update REDO point
2. Write: flush ALL dirty buffers to disk
3. Sync: fsync all files
4. Checkpoint End: WAL record, update pg_control

Parameters:
  checkpoint_timeout (default 5min)
  max_wal_size (default 1GB) — triggers checkpoint before hitting this
  checkpoint_completion_target (0.9) — spread I/O over 90% of interval
```

---

## 5. MVCC

### Tuple Header

```
HeapPage:
  ┌────────────────────────────────┐
  │ PageHeaderData (24 bytes)      │
  │ pd_lsn, pd_checksum,           │
  │ pd_lower, pd_upper, pd_special │
  ├────────────────────────────────┤
  │ ItemIdData[] (line pointers):  │
  │ lp_off, lp_flags, lp_len       │  ← 4 bytes each
  ├────────────────────────────────┤
  │ Free space                     │
  ├────────────────────────────────┤
  │ HeapTupleHeaderData[]:          │
  │ ┌────────────────────────────┐ │
  │ │ t_xmin (creating xid)      │ │
  │ │ t_xmax (deleting xid)      │ │
  │ │ t_cid (command id)         │ │
  │ │ t_ctid (next version tid) │ │
  │ │ t_infomask (hint bits)     │ │
  │ │ t_hoff (header offset)     │ │
  │ │ NULL bitmap / OID          │ │
  │ │ Data (aligned)             │ │
  │ └────────────────────────────┘ │
  └────────────────────────────────┘
```

### Snapshot & Visibility

```
Snapshot { xmin, xmax, xip[] }

Visible if:
  1. t_xmin committed (CLOG says COMMITTED) OR
     t_xmin < xmin (old) → visible
  2. t_xmin in xip[] → INVISIBLE (transaction in progress)
  3. t_xmin aborted → INVISIBLE
  4. t_xmax == 0 → never deleted → VISIBLE
  5. t_xmax committed → DEAD

Hint bits (t_infomask):
  HEAP_XMIN_COMMITTED — skip CLOG lookup (set by first accessor after commit)
  HEAP_XMIN_INVALID   — skip CLOG (aborted)
  HEAP_XMAX_COMMITTED — delete is committed
```

### UPDATE = DELETE + INSERT

```
UPDATE person SET name='Bob' WHERE id=1;

Before:  Tuple1: name='Alice', t_xmin=100, t_xmax=0
During:  Tuple1: t_xmax=105 (deleted)
         Tuple2: name='Bob', t_xmin=105, t_xmax=0
         Tuple1.t_ctid → Tuple2 (version chain)

After commit:
  Snapshot < 105: sees Alice
  Snapshot >= 105: sees Bob
  Tuple1 is dead → needs vacuum
```

### HOT (Heap-Only Tuple)

When update doesn't change indexed columns: chain via t_ctid, no new index entry. Saves index maintenance, improves UPDATE performance for non-indexed column changes.

---

## 6. Transaction Manager & CLOG

### CLOG

```
2 bits per transaction:
  0x00 = IN_PROGRESS
  0x01 = COMMITTED
  0x02 = ABORTED
  0x03 = SUB_COMMITTED

Storage: pg_xact/
  8KB page covers 32,768 transactions
  Checkpoint: truncates old CLOG pages
```

### Transaction ID Wraparound

```
xid is 32-bit — wraps at 4 billion

Old tuples with xmin near 4 billion look "future" after wrap.
Fix: FREEZE — set xmin to FrozenTransactionId (2).

autovacuum_freeze_max_age = 200 million (default)
  → Forces autovacuum to freeze old tuples
  → Prevents wraparound shutdown
```

---

## 7. WAL — Write-Ahead Log

### Principle

```
Write log BEFORE data:
  1. Every change: write to WAL first
  2. Data file written lazily
  3. Crash recovery: replay WAL from last checkpoint

WAL Segment: 16MB each
  /pg_wal/000000010000000000000001
  (timeline + LSN high + LSN low)
```

### LSN (Log Sequence Number)

```
LSN = segment + offset (e.g., 1/ABCD1234)

Stored in page header (pd_lsn)
On recovery: if pd_lsn >= WAL LSN → page already updated, skip
Used for: hot standby conflict detection, replication progress
```

### WAL Record

```
XLogRecord (28 bytes header):
  xl_tot_len | xl_xid | xl_prev | xl_info | xl_rmid
  + block references (relfilenode, block number)
  + main data (tuple changes)
  + backup block (full page image — 8KB)

Full Page Image (FPI):
  First modification after checkpoint → write full page to WAL
  Protects against torn pages
  Config: full_page_writes = on (DO NOT disable)
```

### WAL Config

```
wal_level = replica (default), logical, minimal
synchronous_commit: off (fast, unsafe), local (safe), remote_write, remote_apply, on
wal_buffers = 16MB
wal_sync_method = open_datasync | fdatasync | fsync
```

---

## 8. Query Processing

```
SQL ──► Parser ──► Analyzer ──► Rewriter ──► Planner ──► Executor
        (gram.y)   (catalog)    (rules,views) (cost-based)  (volcano)
```

### Planner

```
Cost parameters:
  seq_page_cost = 1.0
  random_page_cost = 4.0 (set to 1.1 for SSD!)
  cpu_tuple_cost = 0.01
  cpu_operator_cost = 0.0025

Join strategies:
  Nested Loop:   O(|R| * |S|) — small inner, good index
  Hash Join:     O(|R| + |S|) — large join
  Merge Join:    O(|R| + |S|) — sorted inputs
```

### Executor (Volcano Model)

```
Plan: Sort ← IndexScan (age > 25)
  ExecSort() pulls all tuples from child, sorts, returns
  ExecIndexScan() iterates index, checks visibility, returns matching
  Each node has: ExecInit, ExecProcNode (next), ExecEnd
```

---

## 9. Vacuum & Autovacuum

### VACUUM Steps

```
VACUUM table:
  1. Scan pages, find dead tuples (t_xmax committed, not visible)
  2. Remove dead index entries
  3. Compact page, update FSM
  4. Update visibility map (all-visible flag)
  5. Update pg_class stats
  6. Truncate trailing empty pages
```

### FSM (Free Space Map)

```
pg_freespacemap (fork #1): tree structure
  Internal nodes: max free space in subtree
  Leaf nodes: longest free chunk per 8KB page
  Used by: INSERT to find page with enough space

Visibility Map (fork #2):
  1 bit all-visible, 1 bit all-frozen per page
  Speeds: VACUUM skips all-visible pages, index-only scans skip heap
```

### Autovacuum Trigger

```
Trigger: n_dead_tup > threshold + scale_factor * n_live_tup
  default: 50 + 0.2 * n_live_tup

Cost-based delay:
  Each read/write page has cost (default 1 per page)
  When cost > autovacuum_vacuum_cost_limit (200)
  Sleep autovacuum_vacuum_cost_delay (2ms)
```

### TOAST

```
When row > ~2KB: large fields moved to pg_toast_<relfilenode>
  EXTENDED: compress then TOAST (default for text/bytea)
  EXTERNAL: TOAST without compression
  MAIN: prefer inline, TOAST if necessary
  PLAIN: never TOAST
```

---

## 10. Indexing

### B-tree (Lehman & Yao)

```
Page: Items sorted by key | Special: btpo_prev/next/level/flags

Structure:
  Metapage → Root (internal) → Internal pages → Leaf pages (tid, key)

Index deduplication (PostgreSQL 13+):
  Multiple identical keys stored once with tid list
  Suffix truncation: internal keys shortened (saves space, faster compare)

Page splits: L&Y algorithm — half of items move to new right sibling,
  parent updated with new high key. Concurrent access via "right link" pointers.
```

### GiST (Generalized Search Tree)

```
Balanced tree for: R-tree (spatial), full-text ranking, tsvector
  Extensible: implement consistent(), union(), compress(), decompress()
  Used by: PostGIS (geometry), pg_trgm, btree_gist (exclusion constraints)
```

### GIN (Generalized Inverted Index)

```
Inverted index for: arrays, full-text search (tsvector), JSONB
  Posting tree: TIDs sorted by item pointer
  Posting list: compressed TID list for small sets
  Fast: GIN_FAST_UPDATE = on → pending list (delayed merge)
```

### BRIN (Block Range Index)

```
For large tables with natural ordering (time-series, log data)
  Stores min/max per block range (default 128 pages per range)
  Very small index (0.1% of table size)
  Lossy: may return false positives → seq scan within range only

Bloom:
  Bloom filter index for arbitrary multi-column equality queries
  False-positive allowed; space-efficient
```

---

## 11. Replication

### Streaming Replication

```
Primary (WAL sender)                   Standby (WAL receiver)
  │                                          │
  │  WalSnd: sends WAL as generated          │
  │─────────────────────────────────────────►│  WalRcv: writes to pg_wal/
  │                                          │  Startup: replays WAL (continuous)
  │                                          │
  │  Synchronous replicate: wait for ACK     │
  │  synchronous_standby_names: '1' (any)    │
  │                         'FIRST 2' (priority)                  │
  │                         'ANY 2'  (quorum)                    │
  │                                          │
  │  Cascading: standby → another standby    │
  │  hot_standby = on → read-only queries    │
  └──────────────────────────────────────────┘
```

### Logical Replication

```
Publication (primary)                 Subscription (standby)
  ├── Logical decoding of WAL           ├── Apply changes (INSERT/UPDATE/DELETE)
  ├── Replication slot tracks position  ├── Different table structure allowed
  ├── Per-table granularity             ├── Bi-directional possible
  └── Origin tracking avoids loops      └── Conflict resolution

Use cases:
  - Upgrade PostgreSQL version (logical — no binary compat needed)
  - Selective replication (specific tables)
  - Data integration / CDC (Change Data Capture)
  - Multi-master (via bidirectional)

Tools:
  pgoutput: built-in logical decoding plugin
  wal2json: output as JSON (for external consumers like Kafka)
  decoderbufs: protobuf output
  pglogical: third-party (from 2ndQuadrant)
  Debezium: CDC via Kafka Connect + pgoutput
```

---

## 12. Backup & PITR

### pg_basebackup

```bash
pg_basebackup -h primary -D /backup/base -X stream -P
  --wal-method=stream  # WAL fetched during backup
  --progress           # show progress
  --format=tar         # tar output (default)

Creates: base backup + WAL from start to finish
Used for: replica setup, base for PITR
```

### Continuous Archiving & PITR

```
WAL segments continuously copied to archive:
  archive_mode = on
  archive_command = 'cp %p /archive/%f'

PITR recovery:
  restore_command = 'cp /archive/%f %p'
  recovery_target_time = '2024-01-15 10:30:00'
  (or: recovery_target_xid, recovery_target_lsn)

  Steps:
    1. Restore base backup
    2. Set restore_command + recovery_target
    3. Start PostgreSQL → enters recovery mode
    4. Startup process replays WAL until target
    5. Database consistent → ready for queries (target_recovery)
```

---

## 13. Internals

### ProcArray

```c
// Simulated PGPROC — backend process descriptor
typedef struct PGPROC {
    int pid;                    // Backend PID
    PGXACT *pgxact;             // Transaction state
    Latch procLatch;            // For signaling (kill, cancel)
    int backendId;              // Shared memory slot
    LWLock *myLock;             // Lock for this process
    bool isBackgroundWorker;    // Or regular backend
} PGPROC;

// pgxact tracks:
//   xid — current transaction ID
//   xmin — oldest transaction this backend cares about (for snapshots)
//   vacuumFlags
```

### Lock Manager

```
Two-level locking:
  1. LWLock (Lightweight Lock): spinlock + sleep backing
     Used for: shared buffers (individual buffer locks), WAL insert
     Modes: Exclusive (write), Shared (read)

  2. Heavyweight Lock: table-level, row-level
     Modes: AccessShare (SELECT), RowShare, RowExclusive (UPDATE/DELETE),
            ShareUpdateExclusive (VACUUM), Share, ShareRowExclusive, Exclusive,
            AccessExclusive (ALTER TABLE, DROP)
     Deadlock detection: directed graph, timeout-based
```

### WAL Insert Lock

```c
// WAL insert is protected by WALInsertLocks (per-ring buffer segment)
// Each backend reserves space in WAL buffer via atomic increment
// Then copies WAL data, advances shared pointer
// wal_writer flushes WAL buffer to disk

ReserveWALInsert():
  - Reserve space (WALInsertLock on current segment)
  - Copy data to WAL buffer
  - Release lock, advance insert position

FlushWAL():
  - Wait until WAL flushed to LSN (XLogFlush)
  - fsync or open_datasync
```

---

## 14. Failure Analysis

### Database Crash and Recovery

```
Crash → postmaster restarts → recovery mode:
  1. Read pg_control → find REDO point
  2. Startup process replays WAL from REDO point to end
  3. WAL with full page images ensures page-level consistency
  4. When all WAL applied → database consistent → ready

If pg_control corrupt: pg_resetwal (emergency, loses transactions)
```

### Transaction ID Wraparound Shutdown

```
When oldest unfrozen xid is approaching 2^31-1:
  - WARNING: "database is approaching transaction wraparound"
  - Then: ERROR — database shuts down
  - Emergency: start in single-user mode, VACUUM (FREEZE) all tables

Prevention:
  - autovacuum_freeze_max_age = 200M (default)
  - Monitor pg_database.datfrozenxid
  - Schedule aggressive VACUUM FREEZE during maintenance
```

### Replication Lag

```
Causes:
  - Network latency
  - Standby underpowered (can't replay WAL fast enough)
  - Long-running queries on standby blocking WAL replay (conflict)
  - WAL archiving slow (archive_command blocks WAL recycling)

Detection:
  pg_stat_replication: replay_lag, write_lag, flush_lag
  pg_stat_wal_receiver: last_msg_send_time, last_msg_receipt_time

Standby query conflicts:
  Vacuum on primary → removes tuples visible to standby query
  → Conflict: query cancelled after max_standby_streaming_delay (30s)
```

### OOM in PostgreSQL

```
Causes:
  - work_mem too large with many concurrent sort/hash operations
    (work_mem * max_connections * concurrent_operations = OOM)
  - shared_buffers too large + other system processes
  - Connection storm (backend per connection)

Mitigation:
  - work_mem = 4-64MB (not GB)
  - hash_mem_multiplier = 1.5 (PostgreSQL 15+)
  - max_connections = 100-500 (not 5000)
  - Use connection pooler (PgBouncer, Pgpool-II)
```

---

## 15. Edge Cases

- **Concurrent VACUUM + queries**: VACUUM skips pages visible to any active snapshot; long-running queries delay dead tuple cleanup
- **HOT update failure**: Not enough space on same page for new tuple → fallback to non-HOT update (index maintenance needed)
- **GIN pending list large**: GIN_FAST_UPDATE = on → pending list grows → query slowdown → periodic cleanup needed
- **BRIN page range skew**: Data inserted not in natural order → BRIN ranges overlap → poor selectivity
- **pg_upgrade + replication**: Streaming replication incompatible across major versions → use logical replication for upgrade
- **checkpoint I/O spike**: checkpoint_completion_target too low → all I/O at checkpoint start → I/O spike
- **full_page_writes WAL storm**: After crash/restart, every page gets FPI → checkpoint burst
- **Replication slot disk fill**: Logical slot not consumed → pg_wal can't recycle → disk full
- **Standby query conflict**: Primary vacuum, standby query blocked → max_standby_streaming_delay exceeded → query cancelled
- **TOAST + UPDATE**: Large TOAST values rewritten on every UPDATE even if unchanged (pg_reuse_toast = off in older versions)
- **Sequence exhaustion**: BIGSERIAL (int8) wraps only after 9 quintillion; but SERIAL (int4) wraps at 2 billion
- **pg_stat_statements reset**: Resets all query stats → loss of query performance history
- **Autovacuum not running**: Disabled or max workers reached → bloat accumulates → table bloat and index bloat

---

## 16. Performance

### Key Tuning Parameters

```
# Memory
shared_buffers = RAM * 0.25       # (but not > 8-16GB without huge pages)
effective_cache_size = RAM * 0.75 # helps planner estimate index scans
work_mem = 4-64MB                 # per sort/hash operation
maintenance_work_mem = 256MB-1GB  # VACUUM, CREATE INDEX
wal_buffers = 64MB                # WAL write cache

# Checkpoint
checkpoint_timeout = 15min
max_wal_size = 4GB
checkpoint_completion_target = 0.9  # spread I/O

# Planner
random_page_cost = 1.1        # SSD (default 4.0 is for HDD)
effective_io_concurrency = 200  # SSD can handle concurrent I/O

# Autovacuum
autovacuum_vacuum_scale_factor = 0.01  # aggressive (default 0.2)
autovacuum_vacuum_threshold = 100
autovacuum_max_workers = 4
```

### Buffer Cache Sizing

```
shared_buffers hit rate:
  pg_buffercache: SELECT count(*) FILTER (WHERE isdirty) ...
  pg_statio_all_tables: heap_blks_hit / (heap_blks_hit + heap_blks_read)
  Target: > 99% hit rate for OLTP

If hit rate < 99%:
  - Increase shared_buffers
  - Check for seq scans flushing buffer pool
  - Consider pg_prewarm (warm cache after restart)
```

### WAL Generation Rate

```
WAL rate depends on:
  - Frequency of data modifications
  - full_page_writes (FPI after checkpoint)
  - wal_compression = on (saves ~50% WAL on FPI)

High WAL generation:
  - Monitor: pg_wal/ directory growth
  - Monitor: pg_stat_bgwriter (checkpoints_timed vs checkpoints_req)
  - If checkpoints_req > checkpoints_timed: increase max_wal_size
```

### Vacuum Bloat

```
Table bloat detection:
  pgstattuple: SELECT * FROM pgstattuple('table');
  pg_freespacemap: check free space per page
  pg_stat_all_tables: n_dead_tup trending up

Index bloat:
  pgstatindex: avg_leaf_density < 75% → index needs REINDEX
  pg_indexes_size: index size vs table size (index > table = bloat)
```

---

## 17. Simplest Mental Model

> **PostgreSQL is a giant ledger book. Multiple scribes (backend processes) write entries simultaneously, each with their own inkwell (memory). The buffer pool is the open book on the desk — frequently read pages stay on the desk, old pages go back to the shelf (disk). MVCC means nobody crosses out entries — they write a new line and mark the old one as outdated, so a scribe who started reading sees the old entry while a new one writing sees the new one. WAL is a diary: before making any change, a scribe writes in the diary first. If the book is destroyed (crash), you reconstruct from the diary. Vacuum is a clerk who periodically comes by, tears out outdated pages, and compacts the remaining ones. Autovacuum is the same clerk but on a timer — cleaning before the book overflows. Indexes are the tabbed dividers: B-tree is alphabetical tabs, GiST is spatial dividers for maps, GIN is the index at the back of a textbook. Every design choice in PostgreSQL prioritizes data safety and correctness first, then performance — because a mistake in a database loses facts, not just time.**



## Query Execution Flow: Step-by-Step

```
1. Parser: "SELECT * FROM users WHERE id=1"
   ↓
2. Semantic Analyzer: Validate tables/columns exist
   ↓
3. Optimizer: Generate execution plans
   - Plan A: Full table scan (cost: 1000)
   - Plan B: Index on id (cost: 10) ← CHOSEN
   ↓
4. Planner: Build execution tree
   - IndexScan(users, id=1)
   └─ Filter(WHERE condition)
   ↓
5. Executor: Run physical operations
   - Fetch row from index
   - Apply filter
   - Return result
```

### Real Bottleneck Examples

**Missing Index** (1000ms)
```sql
-- Slow: full table scan
SELECT * FROM orders WHERE customer_id = 5;
-- Fix: CREATE INDEX idx_orders_cust ON orders(customer_id);
```

**Bad Join Order** (30s)
```sql
-- Slow: joins small × large
SELECT * FROM items i
JOIN orders o ON i.id = o.item_id
WHERE o.created > '2024-01-01';

-- Better: filter first, then join
SELECT * FROM orders o
WHERE o.created > '2024-01-01'
JOIN items i ON o.item_id = i.id;
```

