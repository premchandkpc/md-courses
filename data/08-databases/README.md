# 08 — Databases


> **Run the live simulator**: [redis-eviction.html](/08-databases/redis-eviction.html) — add keys with different TTLs, fill memory, and watch eviction policies in action.> **Run the live simulator**: [btree-visualizer.html](/08-databases/btree-visualizer.html) — insert keys into an Order-4 B+Tree and watch node splits and tree growth in real-time.

The theory and practice of data storage, retrieval, and management. Covers relational databases (PostgreSQL, MySQL), NoSQL systems (MongoDB, Cassandra, DynamoDB), in-memory stores (Redis), distributed SQL (CockroachDB, TiDB, Spanner), storage engine internals (B+tree, LSM, MVCC, WAL), query optimization, performance tuning, and troubleshooting.

```mermaid
graph TB
    subgraph Clients
        C1["App / Service"]
        C2["Migration Tool"]
        C3["Analytics"]
    end
    subgraph Database
        Q["Query Layer"]
        P["Parser"]
        O["Optimizer<br/>(CBO)"]
        E["Executor"]
        I["Index<br/>B+Tree / Hash"]
        S["Storage Engine"]
        L["Logging<br/>(WAL / AOF)"]
        M["MVCC<br/>Snapshot"]
        B["Buffer Pool"]
        D["Disk"]
    end
    C1 --> Q; C2 --> Q; C3 --> Q
    Q --> P --> O --> E
    E --> I
    E --> S
    S --> L
    S --> M
    S --> B --> D
    
    style C1 fill:#4a8bc2
    style C2 fill:#2d5a7b
    style C3 fill:#3a7ca5
    style O fill:#e8912e
    style S fill:#c73e1d
    style D fill:#f85149
```

## Table of Contents

## Database Comparison

| Feature | PostgreSQL | MongoDB | Cassandra | Redis | Elasticsearch |
|---------|-----------|---------|-----------|-------|---------------|
| **Model** | Relational (SQL) | Document | Wide-Column | Key-Value | Inverted Index |
| **Consistency** | Strong | Tunable | Eventual | Strong | Near Real-Time |
| **Partitioning** | Manual | Sharding | Auto (Partitioner) | Clustering | Auto Sharding |
| **Replication** | Primary/Standby | Replica Set | Gossip + Hinted Handoff | Primary/Replica | Multi-Node |
| **Index** | B+Tree, GiST, GIN | B+Tree | SSTable/LSM | Skip List | Inverted Index |
| **Transactions** | ACID | Multi-Doc | Lightweight | MULTI/EXEC | Per Document |
| **Use Case** | OLTP, Analytics | Content, IoT | Time-Series, IoT | Cache, Session | Search, Logs |

## Query Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant P as Parser
    participant O as Optimizer
    participant E as Executor
    participant S as Storage Engine
    participant D as Disk
    
    C->>P: SQL / Query
    P->>P: Parse & Validate
    P->>O: Parse Tree
    O->>O: Generate Plans
    O->>O: CBO (Cost-Based)
    O->>E: Best Execution Plan
    E->>S: Fetch Tuples
    S->>D: Page Read
    D-->>S: Data Page
    S-->>E: Tuple
    E-->>C: Result
```

- [Relational Databases](#relational-databases)
  - [PostgreSQL](#postgresql)
  - [MySQL](#mysql)
- [NoSQL](#nosql)
  - [Document Stores](#document-stores)
  - [Wide-Column Stores](#wide-column-stores)
  - [Key-Value Stores](#key-value-stores)
  - [Search Engines](#search-engines)
  - [Graph Databases](#graph-databases)
  - [Time-Series](#time-series)
- [Redis](#redis)
  - [Data Structures](#data-structures)
  - [Persistence](#persistence)
  - [High Availability](#high-availability)
  - [Use Cases](#use-cases)
- [Distributed SQL](#distributed-sql)
  - [CockroachDB](#cockroachdb)
  - [TiDB](#tidb)
  - [Google Spanner](#google-spanner)
  - [YugabyteDB](#yugabytedb)
- [Database Internals](#database-internals)
  - [B+tree Index](#btree-index)
  - [LSM-Tree](#lsm-tree)
  - [MVCC](#mvcc)
  - [Write-Ahead Log (WAL)](#write-ahead-log-wal)
  - [Buffer Pool](#buffer-pool)
  - [Query Execution](#query-execution)
- [Troubleshooting](#troubleshooting)
  - [Slow Queries](#slow-queries)
  - [Connection Issues](#connection-issues)
  - [Replication Lag](#replication-lag)
  - [Lock Contention](#lock-contention)
  - [Resource Exhaustion](#resource-exhaustion)
- [Performance Tuning](#performance-tuning)
  - [Indexing Strategies](#indexing-strategies)
  - [Query Optimization](#query-optimization)
  - [Configuration Tuning](#configuration-tuning)
  - [Schema Design](#schema-design)
- [Learning Path](#learning-path)
- [Cross-References](#cross-references)

---

## Relational Databases

### PostgreSQL

The most advanced open-source relational database. ACID-compliant, extensibility, excellent concurrency.

- **Architecture** — process-per-connection model; shared buffers, WAL segments, checkpoint process, autovacuum launcher/workers, background writer, stats collector, logical replication walsender
- **Data Types** — numeric, text, boolean, JSON/JSONB, arrays, hstore, UUID, enum, range, interval, CIDR/inet, geometric, custom (CREATE TYPE), composite
- **Indexes** — B-tree (default), Hash (limited use), GiST (full-text, geometry), GIN (JSONB, arrays), SP-GiST (partitioned trees), BRIN (large tables, correlated ordering), Bloom (multi-column); partial, expression, unique, concurrent, covering (INCLUDE)
- **Advanced Features** — CTEs (WITH), window functions, recursive queries, DISTINCT ON, LATERAL JOIN, FOR UPDATE/SHARE, RETURNING, upsert (ON CONFLICT DO UPDATE/NOTHING), partitioning (range, list, hash, sub-partitioning)
- **Concurrency** — MVCC (snapshot isolation), transaction isolation levels (Read Uncommitted, Read Committed <default>, Repeatable Read, Serializable), row-level locking, advisory locks, SKIP LOCKED, NOWAIT
- **Extensions** — PostGIS (geospatial), pgvector (vector similarity), pg_partman (partition management), pg_stat_statements (query stats), auto_explain, pg_hint_plan, timescaledb (time-series), Citus (distributed), pg_ivm (incremental materialized views)
- **Replication** — Streaming replication (physical), synchronous/async; logical replication (publish/subscribe, selective tables, major version upgrades), pglogical, Bi-Directional
- **Backup & Restore** — pg_dump/pg_dumpall (logical), pg_basebackup (physical), WAL archiving (archive_command, restore_command), continuous archiving + PITR, pgBackRest, barman, WAL-G
- **Configuration** — shared_buffers, work_mem, maintenance_work_mem, effective_cache_size, wal_buffers, max_connections, random_page_cost, effective_io_concurrency, jit, track_io_timing

### MySQL

Most widely deployed open-source database (especially as MariaDB forks). Popular for LAMP stack, read-heavy workloads.

- **Architecture** — thread-per-connection; storage engine abstraction (MyISAM, InnoDB, Memory, CSV, Archive, Federated), InnoDB is default (ACID, MVCC, row-level locking, crash recovery)
- **InnoDB Internals** — clustered index (primary key as B+tree, rows stored in leafs), secondary indexes (pointers to PK), doublewrite buffer, change buffer (insert/update buffering for secondary indexes), adaptive hash index, redo log, undo log
- **Indexes** — B-tree (default), Hash (memory engine, NDB), Full-text, Spatial (R-tree), Descending, Functional key parts (8.0+), Generated column indexes; multi-column, prefix, INCLUDE (descending index)
- **Replication** — Async (default), semi-sync, group replication (InnoDB Cluster); binary log (statement, row, mixed); GTID-based replication, multi-source replication, delayed replication
- **Engine Comparison** — InnoDB (transactional, row locking, MVCC), MyISAM (table locking, full-text, non-transactional), Memory (heap), NDB (clustered, shared-nothing), Archive (compressed, insert-only, no indexes), TokuDB (Fractal tree, high compression)
- **Tools** — mysqldump, mysqlpump, Xtrabackup, mysqlbinlog, pt-query-digest, MySQL Shell (AdminAPI for InnoDB Cluster), ProxySQL (connection pooling, routing)

---

## NoSQL

### Document Stores

- **MongoDB** — document-oriented (BSON); collections (tables → collections, documents → rows); _id primary key (ObjectId); flexible schema, embedded documents, arrays; indexes (single, compound, multikey, text, geospatial, hashed, TTL, partial)
  - **Aggregation Pipeline** — $match, $group, $sort, $project, $lookup (join), $unwind, $facet, $bucket; optimized with indexes; vs map-reduce (deprecated)
  - **Replication** — replica set (primary + secondaries), elections (Raft-like), read preferences (primary, primaryPreferred, secondary, secondaryPreferred, nearest), write concern (w: majority, j: true)
  - **Sharding** — shard key (range, hash, zone), mongos (router), config servers; balancing, chunk migration, tag-aware sharding
  - **Storage Engines** — WiredTiger (default, document-level locking, LSM for time-series), In-memory (ephemeral)
- **Couchbase** — document + key-value; N1QL (SQL-like for JSON), FTS, analytics (via Couchbase Analytics), eventing

### Wide-Column Stores

- **Apache Cassandra** — peer-to-peer (no master), partition key → clustering columns, CQL (Cassandra Query Language); designed for write-heavy, high availability, multi-datacenter
  - **Data Model** — keyspace → table → partition key (hash determines node), clustering columns (order within partition); primary key = partition key + clustering columns; static columns, collections (list, set, map)
  - **Architecture** — gossip protocol (node discovery), snitch (topology awareness), partitioner (murmur3partitioner), virtual nodes (vnodes), hinted handoff, read repair, Merkle trees (anti-entropy)
  - **Consistency** — ANY, ONE, TWO, THREE, QUORUM, LOCAL_QUORUM, EACH_QUORUM, ALL; tunable consistency per request; consistency level + replication factor (e.g., QUORUM = RF/2 + 1)
  - **Compaction** — size-tiered (STCS), leveled (LCS), time-window (TWCS); repair (incremental vs full)
  - **DynamoDB** — (covered under cloud services) managed wide-column + document; partition key + sort key; LSI/GSI indexes; DynamoDB Streams (CDC); global tables (multi-region active-active)
- **ScyllaDB** — Cassandra-compatible, C++ rewrite; shard-per-core architecture; zero-GC pauses, lower latency

### Key-Value Stores

- **Redis** — see [Redis section](#redis) below
- **Memcached** — distributed memory cache; simple (strings only), no persistence, no replication; LRU eviction; consistent hashing for scaling
- **etcd** — distributed consistent key-value store (Raft); Kubernetes primary datastore; watch API, TTL (leases), transactions (if/then/else)
- **FoundationDB** — distributed, ACID, ordered key-value; uses deterministic simulation testing; runs multiple layers (document, relational)

### Search Engines

- **Elasticsearch** — distributed, RESTful, JSON-based search + analytics; inverted index, BM25 scoring, aggregations, percolator, cross-cluster search; Kibana for visualization
  — Cluster: nodes (master, data, ingest, coordinating), shards (primary + replicas), index lifecycle management (ILM), rollup, transforms, snapshot/restore
- **OpenSearch** — community fork of Elasticsearch (after license change); feature-compatible; OpenSearch Dashboards
- **Meilisearch** — Rust-based, developer-friendly, typo-tolerant, instant search
- **Typesense** — fast (C++), schema-optional, search and faceted filtering

### Graph Databases

- **Neo4j** — labeled property graph; Cypher query language (ASCII-art patterns); ACID; clustering (causal cluster, read replicas)
- **Amazon Neptune** — managed graph (property graph + RDF); Gremlin (Apache TinkerPop) + SPARQL

### Time-Series

- **InfluxDB** — purpose-built TSDB; measurements, tags (indexed), fields; Flux query language (now SQL in v3); TSM storage engine; continuous queries, retention policies, down-sampling
- **TimescaleDB** — PostgreSQL extension for time-series; hypertables (auto-partitioned by time); continuous aggregates, compression (native, column-level), data retention policies
- **ClickHouse** — columnar OLAP; real-time analytics; materialized views (incremental), merge tree engine; SQL-compatible (extended)

---

## Redis

In-memory data structure store—used as cache, message broker, queue, and primary database for certain workloads.

### Data Structures

- **Strings** — value up to 512MB; SET/GET, INCR/DECR, APPEND, STRLEN, GETSET, MSET/MGET
- **Lists** — linked lists; LPUSH/RPUSH, LPOP/RPOP, LRANGE, LTRIM, BLPOP/BRPOP (blocking); use cases: queues, message buffers, timeline feeds
- **Sets** — unordered, unique; SADD, SMEMBERS, SISMEMBER, SINTER/SUNION/SDIFF (set ops); SPOP, SRANDMEMBER; use cases: tags, uniqueness checks
- **Sorted Sets** — scored members; ZADD, ZRANGEBYSCORE, ZRANK, ZREVRANGE, ZINCRBY, ZINTERSTORE/ZUNIONSTORE; use cases: leaderboards, rate limiting, time-series
- **Hashes** — field-value pairs; HSET/HGET, HGETALL, HEXISTS, HINCRBY, HLEN; use cases: objects, session stores, user profiles
- **Bitmaps** — bit operations on strings; SETBIT, GETBIT, BITCOUNT, BITOP; use cases: daily active users (DAU), bloom filters
- **HyperLogLog** — approximate cardinality (~0.81% error); PFADD, PFCOUNT, PFMERGE; use cases: unique visitors, distinct elements
- **Geospatial** — GEOADD, GEODIST, GEORADIUS, GEORADIUSBYMEMBER, GEOSEARCH; use cases: location-based queries
- **Streams** — append-only log, consumer groups; XADD, XREAD, XREADGROUP, XRANGE, XDEL, XACK; use cases: message queuing, event sourcing (more flexible than Pub/Sub)
- **Pub/Sub** — channel-based messaging; PUBLISH, SUBSCRIBE, PSUBSCRIBE; fire-and-forget (no persistence)

### Persistence

- **RDB (Redis Database)** — point-in-time snapshots; configured by save intervals; compact binary; great for backups + cold starts; potential data loss (last snapshot to crash)
- **AOF (Append-Only File)** — logs every write operation; fsync policies (always, everysec <default>, no); larger than RDB, slower startup, but less data loss
- **Mixed Persistence** — use both (AOF + RDB); default since Redis 7.x (AOF rewrite creates RDB as base)
- **Redis Stack** — extends core with RediSearch, RedisJSON, RedisTimeSeries, RedisGraph, RedisBloom; all in single module package

### High Availability

- **Replication** — primary → replica (async); replicas can be chained; partial resynchronization (PSYNC), replication ID + offset
- **Sentinel** — monitoring + automatic failover; quorum (min votes for failover), majority; choose new primary from replicas; uses config rewriting
- **Redis Cluster** — sharded (16384 hash slots), automatic failover, multi-primary writes; gossip protocol; no cross-slot multi-key operations; all nodes accessible (client can connect to any)
- **Cluster Architecture** — hash slot (CRC16(key) mod 16384) → node; resharding (migrate slots), replication (primary → replica in different node), cluster bus

### Use Cases

- Cache (read-through, write-through, write-behind)
- Session store (web app sessions, TTL-based)
- Rate limiter (sliding window with sorted sets, token bucket)
- Real-time leaderboard (sorted sets)
- Message queue (list, stream + consumer groups)
- Distributed lock (SET NX EX, Redlock for consensus)
- Idempotency check (SET key NX EX TTL)

---

## Distributed SQL

### CockroachDB

- **Architecture** — shared-nothing, SQL-layer on transactional KV store; each node is equal (no master); range-based sharding (64MB ranges), range leaseholder (Raft leader)
- **Consistency** — Serializable isolation (default, strictest), also Snapshot; strongly consistent (uses Raft consensus for replication); no eventual consistency
- **Geo-distribution** — table locality, follower reads (low-latency stale reads), global tables (low-latency writes from any region via Follower + Leaseholder co-location)
- **SQL Compatibility** — PostgreSQL wire protocol, compatible with most PostgreSQL syntax; Cockroach-specific: locality-optimized search, costing differences
- **Change Data Capture** — changefeeds (Kafka, cloud storage, webhook); schema changes without blocking

### TiDB

- **Architecture** — TiDB (SQL layer, MySQL-compatible), TiKV (distributed transactional KV store, Raft), PD (placement driver, scheduling); TiFlash (columnar storage for HTAP)
- **Storage** — TiKV: RocksDB-based, LSM-tree, region-based sharding (96MB default), Raft group per region; TiFlash: columnar replicas (asynchronous replication from TiKV)
- **HTAP** — hybrid transactional + analytical; TiFlash replicas used for OLAP queries (data from TiKV in near real-time)
- **Scheduling** — PD manages region placement, balance, split/merge; labels for topology (zone, rack, host)

### Google Spanner

- **Architecture** — globally distributed SQL database; TrueTime API (GPS + atomic clocks) for external consistency; Paxos-based consensus per tablet; directory-based placement
- **Consistency** — external consistency (linearizability), serializable isolation; TrueTime enables lock-free read-only transactions, no coordinator needed
- **Storage** — tablet → split → Paxos group; interleave tables (parent-child storage co-location); F1 SQL layer (compiles queries, distributed joins, automatic query optimization)
- **Replication** — Paxos (configurable number of replicas, typically 5); atomic clocks enable global strongly consistent reads with no blocking
- **SQL** — Google-standard SQL; INTERLEAVE IN PARENT, STORED views, generated columns, change streams, sequence counters
- **Cloud Spanner** — managed service; multi-region configurations (regional, dual-region, multi-region); strong consistency across continents

### YugabyteDB

- **Architecture** — YSQL (PostgreSQL-compatible SQL), YCQL (Cassandra-compatible); DocDB distributed document store (Raft per tablet), fully replicated, sharded
- **DocDB** — LSM + B-tree hybrid; column-level compression; tablet-peers (Raft groups); automatic sharding by hash or range
- **Geo-distributed** — xCluster (asynchronous multi-region), 3-region synchronous replication; read replicas for local reads
- **PostgreSQL Compatibility** — reuses PostgreSQL query layer (same parser, planner, executor, catalogs); most PostgreSQL extensions work

---

## Database Internals

### B+tree Index

The classic database index structure. Used by MySQL InnoDB, PostgreSQL default, Oracle, SQL Server.

- **Structure** — internal nodes (keys + pointers to child nodes), leaf nodes (keys + row pointers or row data in clustered indexes); fanout (high, reduces tree height)
- **Height** — 3-4 levels for billions of rows (e.g., 4KB pages, 1000 keys per node = 1 billion rows in 3 levels)
- **Operations** — point lookup (tree traversal, O(log n)), range scan (sequential leaf node traversal), insert/split, delete/merge
- **Clustered vs Secondary** — clustered (leaf = row data, InnoDB), secondary (leaf = primary key pointer → additional lookup)
- **Page Splits** — 50/50 or 90/10 split strategies; impacts insert performance and page utilization
- **Buffer Pool & Prefetching** — sequential pages prefetched for range scans; buffer pool hit ratio critical

### LSM-Tree

Log-Structured Merge-Tree. Used by LevelDB, RocksDB, Cassandra, ScyllaDB, YugabyteDB, TiKV.

- **Structure** — in-memory memtable (sorted) → immutable memtable → level 0 SSTables (sorted string tables) → level 1 → level N; each level is larger (10x growth factor typical)
- **Writes** — append to WAL → insert into memtable; sequential writes are fast (no random seeks)
- **Reads** — check memtable → immutable → level 0 → level 1 ... ; need to merge results from multiple levels (bloom filters per SSTable to skip levels)
- **Compaction** — size-tiered (STS: merge SSTables to next level when enough files), leveled (LCS: maintain non-overlapping, merge across levels); tradeoff: write amplification vs read amplification vs space amplification
- **Bloom Filters** — per SSTable; false-negative-free, configurable false-positive rate; speeds up point queries, range queries cannot use

### MVCC

Multiversion Concurrency Control. Used by PostgreSQL, MySQL InnoDB, CockroachDB, TiDB, Oracle.

- **Snapshots** — each transaction sees a consistent snapshot of data; writers do not block readers, readers do not block writers
- **Implementation** — PostgreSQL: each row has xmin (creating transaction), xmax (deleting transaction); visibility checks compare with transaction snapshot (xmin/xmax arrays)
- **Old Versions** — dead tuples (row versions no longer visible to any transaction); need cleanup (VACUUM in PostgreSQL, purge in InnoDB)
- **Isolation Levels** — Read Committed (new snapshot per statement), Repeatable Read (single snapshot per transaction), Serializable (snapshot + conflict detection or predicate locking)
- **Conflicts** — first-committer-wins (PostgreSQL Serializable), first-updater-wins (standard locking)

### Write-Ahead Log (WAL)

Ensures durability without flushing data pages on each commit. Central to PostgreSQL, MySQL InnoDB, all ACID databases.

- **Write Path** — transaction commit → write WAL record (append) → success → data written to buffer pool (lazy) → checkpoint (flush dirty pages)
- **WAL Records** — logical (row changes, PostgreSQL) vs physical (page changes, InnoDB redo log); LSN (log sequence number) for ordering
- **Checkpoint** — sync all dirty pages to disk, write checkpoint WAL record; recovery scans from last checkpoint
- **Recovery** — redo (reapply changes from WAL after checkpoint), undo (rollback uncommitted transactions); ARIES algorithm (IBM, widely used)
- **WAL Tuning** — WAL size, checkpoint intervals, WAL buffer size, sync method (O_DIRECT)

### Buffer Pool

- **Page Replacement** — LRU,2Q, Clock, ARC (PostgreSQL used clock sweep); InnoDB uses midpoint insertion (LRU with midpoint)
- **Dirty Pages** — pages modified in memory but not yet on disk; checkpoint flushes them
- **Doublewrite Buffer** (InnoDB) — prevents partial page writes (torn pages); write to doublewrite buffer before writing to data file
- **PostgreSQL Shared Buffers** — typical 25% of RAM; effective_cache_size helps query planner (OS cache)

### Query Execution

- **Parser** — SQL → parse tree; syntax check, access check
- **Rewriter** — views, rules, subquery flattening (correlated → join), CTE inlining
- **Planner/Optimizer** — generate join orders, access paths (sequential scan, index scan, bitmap scan, index-only scan), join methods (Nested Loop, Hash Join, Merge Join)
- **Cost Model** — cost per page (seq_page_cost, random_page_cost), per tuple (cpu_tuple_cost, cpu_operator_cost, cpu_index_tuple_cost); PostgreSQL cost model is configurable; EXPLAIN (ANALYZE, BUFFERS, TIMING) essential
- **Executor** — runs the plan: sort, aggregate (hash/group), join (method from plan); hash tables, sort-merge

---

## Troubleshooting

### Slow Queries

- **EXPLAIN ANALYZE** — actual vs estimated rows, startup + total cost for each node; look for sequential scans on large tables (missing index), large row estimates vs actual (stale statistics)
- **pg_stat_statements** — top queries by total_time, mean_time, calls, rows, shared_blks_hit/read; identify problematic queries
- **Missing Indexes** — check query WHERE clause, JOIN conditions, ORDER BY; analyze index usage (pg_stat_user_indexes, sys.schema_index_statistics)
- **Index Bloat** — B-tree pages not reused after deletes; REINDEX, autovacuum (PostgreSQL), OPTIMIZE TABLE (MySQL)
- **Slow Joins** — nested loop on large tables (need hash join or index); missing join column index; wrong join order

### Connection Issues

- **Max Connections** — connection spikes → errors; connection pooler (PgBouncer, RDS Proxy, ProxySQL) essential; manage with pgbouncer, RDS Proxy, ProxySQL
- **Idle Connections** — consuming memory; set idle_in_transaction_session_timeout, statement_timeout
- **Disk Full** — partition full, binlogs accumulating, WAL not purged; monitor disk space, log retention, WAL archiving

### Replication Lag

- **Monitor** — replay lag (pg_stat_replication), seconds_behind_master (MySQL), replica lag (Mongo, Cassandra)
- **Causes** — write-heavy workload on primary, under-provisioned replica, long-running queries on replica, DDL on primary (command-logged)
- **Cascading Replica** — primary -> replica1 -> replica2; reduced primary load, increased lag at far end
- **Synchronous Replication** — no lag (primary waits for at least one sync replica), but increased write latency

### Lock Contention

- **Monitor** — pg_locks (PostgreSQL), sys.innodb_locks (MySQL), SHOW PROCESSLIST; check blocked vs blocking queries
- **Common Causes** — long transactions, missing indexes in UPDATE/DELETE (row lock → table lock escalation or many row locks), DDL locks, foreign key locks
- **Remediation** — reduce transaction length, add indexes for UPDATE/DELETE WHERE clauses, use NOWAIT/SKIP LOCKED, partition large tables

### Resource Exhaustion

- **Memory** — buffer pool / shared buffers too small (cache miss ratio high); work_mem too high per query (OLAP aggregate memory); investigate with pg_buffercache, InnoDB buffer pool metrics
- **CPU** — high query throughput, insufficient indexing, query plan changes (bad plan); missing indexes, plan regression
- **I/O** — WAL writes, checkpoints, data file reads; use faster storage (NVMe, Provisioned IOPS); adjust WAL settings, checkpoint intervals

---

## Performance Tuning

### Indexing Strategies

- **Composite Index Column Order** — most selective first, then equality columns before range columns
- **Covering Indexes** — index contains all columns needed for query; index-only scans
- **Partial Indexes** — index on subset of rows (WHERE condition); useful for active records, soft-delete, temporal tables
- **Expression Indexes** — index on function result (UPPER(name), EXTRACT(year FROM created_at))
- **Index Maintenance** — monitor bloat, REINDEX/CONCURRENTLY (non-blocking), track unused indexes

### Query Optimization

- **Avoid SELECT \*** — only fetch needed columns; benefits: less I/O, index-only scans, less network transfer
- **Use JOINs Correctly** — inner vs left vs right vs anti-join (NOT EXISTS); prefer EXISTS vs IN for subqueries
- **Limit Early** — ORDER BY ... LIMIT n (can use index for sort + stop early)
- **Window Functions vs Self-Joins** — window functions are more efficient for running totals, rankings, moving averages
- **CTEs / WITH** — optimization fences (PostgreSQL materializes CTE unless NOT MATERIALIZED); inline vs materialized performance

### Configuration Tuning

- **PostgreSQL** — shared_buffers (25% RAM), effective_cache_size (50-75% RAM), work_mem (OLTP: 4-64MB per sort), maintenance_work_mem (1GB+ for VACUUM), wal_buffers (16-64MB), random_page_cost (1.1 for SSD, 4 for HDD)
- **MySQL** — innodb_buffer_pool_size (70-80% RAM), innodb_log_file_size (256MB-4GB), innodb_flush_log_at_trx_commit (2 = better performance, 1 = full ACID), max_connections, table_open_cache, tmp_table_size / max_heap_table_size
- **MongoDB** — WiredTiger cache size (default 50% RAM, adjust), storage.wiredTiger.engineConfig.journalCompressor, net.maxIncomingConnections

### Schema Design

- **Normalization vs Denormalization** — 3NF/BCNF (OLTP), star/snowflake (OLAP); balance: too normalized = many JOINs, too denormalized = update anomalies
- **Data Types** — smallest type for data (int vs bigint, varchar vs text, timestamp vs timestamptz); avoid TEXT for short strings in MySQL (uses VARCHAR)
- **Partitioning** — range (time-series), list (region), hash (even distribution); partition pruning drastically reduces scan; manage partitions (add/drop/merge/split)
- **Constraints** — PK, FK, UNIQUE, CHECK, NOT NULL; provide data integrity + query optimizer information
- **Soft Deletes** — add deleted_at TIMESTAMP; partial index on WHERE deleted_at IS NULL for active records

---

## Code Examples

### PostgreSQL: Advanced Queries

```sql
-- Window functions for ranking
SELECT 
    user_id,
    amount,
    ROW_NUMBER() OVER (ORDER BY amount DESC) as rank,
    ROUND(100.0 * amount / SUM(amount) OVER (), 2) as pct_of_total
FROM transactions
WHERE created_at >= NOW() - INTERVAL '30 days';

-- CTE (Common Table Expression) for hierarchical data
WITH RECURSIVE org AS (
    SELECT id, name, manager_id, 1 as level
    FROM employees
    WHERE manager_id IS NULL
    
    UNION ALL
    
    SELECT e.id, e.name, e.manager_id, o.level + 1
    FROM employees e
    INNER JOIN org o ON e.manager_id = o.id
)
SELECT * FROM org ORDER BY level, name;

-- Partial index for soft deletes
CREATE INDEX active_users_idx ON users(id) 
WHERE deleted_at IS NULL;

-- Index on expression for case-insensitive search
CREATE INDEX email_lower_idx ON users(LOWER(email));

-- EXPLAIN ANALYZE to check query plan
EXPLAIN ANALYZE
SELECT * FROM orders 
WHERE customer_id = 123 AND created_at > NOW() - INTERVAL '1 year'
ORDER BY created_at DESC LIMIT 10;
```

### MongoDB: Document Queries & Aggregation

```javascript
// Create collection with schema validation
db.createCollection("orders", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["customer_id", "amount", "created_at"],
      properties: {
        customer_id: { bsonType: "objectId" },
        amount: { bsonType: "decimal" },
        created_at: { bsonType: "date" },
        status: { enum: ["pending", "shipped", "delivered"] }
      }
    }
  }
});

// Aggregation pipeline: match → group → sort
db.orders.aggregate([
  { $match: { created_at: { $gte: new Date("2024-01-01") } } },
  { $group: {
      _id: "$customer_id",
      total_amount: { $sum: "$amount" },
      order_count: { $sum: 1 },
      avg_order: { $avg: "$amount" }
  }},
  { $sort: { total_amount: -1 } },
  { $limit: 10 }
]);

// Index for query performance
db.orders.createIndex({ customer_id: 1, created_at: -1 });
db.orders.createIndex({ status: 1, created_at: -1 });
```

### Redis: Caching & Data Structures

```python
import redis
import json
import time

r = redis.Redis(host='localhost', port=6379, db=0)

# String: Simple cache
user_id = 42
user_data = {"id": 42, "name": "Alice", "email": "alice@example.com"}
r.setex(f"user:{user_id}", 3600, json.dumps(user_data))  # 1 hour TTL
cached = json.loads(r.get(f"user:{user_id}"))

# Hash: Object storage
r.hset(f"user:{user_id}:profile", mapping={
    "name": "Alice",
    "email": "alice@example.com",
    "age": 28
})
profile = r.hgetall(f"user:{user_id}:profile")

# List: Queue/Log
r.rpush("task_queue", "task1", "task2", "task3")  # Append
task = r.lpop("task_queue")  # Pop from left (FIFO)

# Set: Unique members
r.sadd("active_users", user_id, 43, 44)  # Add to set
is_active = r.sismember("active_users", user_id)  # Check membership
count = r.scard("active_users")  # Count members

# Sorted Set: Leaderboard
r.zadd("leaderboard", {"alice": 1000, "bob": 950, "charlie": 900})
top_10 = r.zrange("leaderboard", 0, 9, withscores=True)

# TTL & Expiration
r.expire("user:42", 3600)  # Set expiry in seconds
ttl = r.ttl("user:42")  # Get remaining TTL
```

### SQL Performance Tuning

```sql
-- Missing index detection
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC
LIMIT 10;  -- Unused indexes

-- Slow query analysis
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT orders.*, customers.name
FROM orders
JOIN customers ON orders.customer_id = customers.id
WHERE orders.created_at > NOW() - INTERVAL '7 days';

-- Table bloat detection
SELECT 
    schemaname,
    tablename,
    ROUND(100 * pg_relation_size(schemaname||'.'||tablename) / 
    pg_total_relation_size(schemaname||'.'||tablename), 2) as table_ratio
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Autovacuum tune per table
ALTER TABLE orders SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02,
    autovacuum_vacuum_cost_delay = 2
);
```

### Python: SQLAlchemy ORM

```python
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    orders = relationship("Order", back_populates="customer")

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    amount = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    customer = relationship("Customer", back_populates="orders")

# Create engine & session
engine = create_engine('postgresql://user:password@localhost/db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Query
customer = session.query(Customer).filter_by(email='alice@example.com').first()
orders = customer.orders  # Lazy load related orders

# Insert
new_order = Order(customer_id=customer.id, amount=1500)
session.add(new_order)
session.commit()

# Batch insert
customers = [Customer(name=f"User{i}", email=f"user{i}@example.com") for i in range(1000)]
session.add_all(customers)
session.commit()
```

---

## Learning Path

1. **Stage 1** — SQL proficiency: joins, subqueries, aggregations, window functions, CTEs
2. **Stage 2** — One relational DB in depth: PostgreSQL (recommended) or MySQL; indexing, EXPLAIN, configuration, backup/restore
3. **Stage 3** — One NoSQL DB: MongoDB (document) or Redis (caching); understand when to use NoSQL vs relational
4. **Stage 4** — Database internals: B+tree, LSM-tree, MVCC, WAL, query planning, buffer pool management
5. **Stage 5** — Distributed SQL (CockroachDB/TiDB), partitioning, replication, performance tuning, troubleshooting at scale

---

## Cross-References

| Domain | Connection |
|--------|-----------|
| [00 — Foundations](/00-foundations/) | B+tree, sorting, searching algorithms are database internals; discrete math for relational algebra |
| [01 — AI/ML](/01-ai-ml/) | Vector databases (pgvector, Milvus), feature stores, embedding storage for RAG |
| [02 — Data Engineering](/02-data-engineering/) | Warehouse (Snowflake, BigQuery), lakehouse (Delta/Iceberg), ETL from operational databases, CDC |
| [03 — Backend](/03-backend/) | Database connection management, ORM patterns, query design, data access layers |
| [05 — Cloud](/05-cloud/) | Managed databases (RDS, Cloud SQL, Azure SQL), NoSQL (DynamoDB, Firestore, Cosmos DB), ElastiCache |
| [07 — Kubernetes](/07-kubernetes/) | Running databases on K8s (stateful operators), CSI storage, database at scale on K8s |
| [09 — Distributed Systems](/09-distributed-systems/) | Consensus (Raft, Paxos) in distributed databases, CAP theorem, consistency models |
| [10 — Messaging](/10-messaging/) | CDC (Debezium, Kafka Connect), database event streaming, transactional outbox pattern |

## Related

- [Cap Consistency](/09-distributed-systems/01-cap-consistency.md)
- [Consensus Replication](/09-distributed-systems/01-consensus-replication.md)
- [Consensus Raft](/09-distributed-systems/02-consensus-raft.md)
- [Distributed Transactions](/09-distributed-systems/02-distributed-transactions.md)
- [Distributed Caching](/09-distributed-systems/03-distributed-caching.md)
- [Distributed Storage](/09-distributed-systems/03-distributed-storage.md)

---

# Database Systems Complete Guide

Comprehensive coverage of relational and NoSQL databases from fundamentals to advanced optimization, scaling, and concurrency patterns.

**Total Content:** 25+ files with code examples, real-world patterns, and visual diagrams.

---

## 📚 Quick Navigation

| Database | Overview | Schema | Operations | Advanced |
|----------|----------|--------|-----------|----------|
| **DynamoDB** | [Overview](./dynamodb/01-basics/01-overview.md) + [Visual](./dynamodb/01-basics/01-overview.html) | [Tables](./dynamodb/01-basics/02-tables.md) + [Visual](./dynamodb/01-basics/02-tables.html) | [Items](./dynamodb/01-basics/03-items.md) + [Visual](./dynamodb/01-basics/03-items.html) | [Queries](./dynamodb/02-intermediate/01-advanced-queries.md) \| [Concurrency](./dynamodb/04-concurrency/01-concurrency-control.md) \| [Optimization](./dynamodb/05-optimization/01-performance-tuning.md) |
| **MySQL** | [Overview](./mysql/01-basics/01-overview.md) + [Visual](./mysql/01-basics/01-overview.html) | [Design](./mysql/01-basics/02-schema-design.md) | [CRUD](./mysql/01-basics/01-overview.md#basic-operations) | [Optimization](./mysql/01-basics/02-schema-design.md) |
| **PostgreSQL** | [Overview](./postgres/01-basics/01-overview.md) | [Advanced SQL](./postgres/01-basics/01-overview.md) | [Queries](./postgres/01-basics/01-overview.md#ctesqueries) | JSON \| Arrays \| FTS |
| **MongoDB** | [Overview](./mongodb/01-basics/01-overview.md) | [Documents](./mongodb/01-basics/01-overview.md#documents--collections) | [CRUD](./mongodb/01-basics/01-overview.md#crud-operations) | [Aggregation](./mongodb/01-basics/01-overview.md#aggregation-pipeline) |
| **Oracle** | [Overview](./oracle/01-basics/01-overview.md) | [Tablespaces](./oracle/01-basics/01-overview.md#tablespaces--storage) | [Operations](./oracle/01-basics/01-overview.md#basic-operations) | [Partitioning](./oracle/01-basics/01-overview.md#partitioning) |

---

## 🎯 By Use Case

### Web Application Backend
**Recommended:** MySQL or PostgreSQL
- Start: [MySQL Overview](./mysql/01-basics/01-overview.md)
- Focus: Schema design, CRUD, indexing
- Key: User authentication, sessions, relationships

### Mobile App Backend  
**Recommended:** DynamoDB or MongoDB
- Start: [DynamoDB Overview](./dynamodb/01-basics/01-overview.md)
- Focus: Partition keys, scalability, TTL
- Key: Session storage, push notifications, analytics

### Real-Time Analytics
**Recommended:** DynamoDB or PostgreSQL
- Start: [DynamoDB Advanced Queries](./dynamodb/02-intermediate/01-advanced-queries.md)
- Focus: Query optimization, GSI, aggregation
- Key: Index strategies, denormalization

### Enterprise System
**Recommended:** Oracle or PostgreSQL
- Start: [Oracle Overview](./oracle/01-basics/01-overview.md) or [PostgreSQL Overview](./postgres/01-basics/01-overview.md)
- Focus: Complex queries, security, HA
- Key: Transactions, partitioning, compliance

### Content Management / Flexible Schema
**Recommended:** MongoDB
- Start: [MongoDB Overview](./mongodb/01-basics/01-overview.md)
- Focus: Collections, aggregation, flexible docs
- Key: Semi-structured data, rapid development

### Gaming / Leaderboards
**Recommended:** DynamoDB
- Start: [DynamoDB Items](./dynamodb/01-basics/03-items.md)
- Focus: Atomic operations, sharding, concurrency
- Key: Consistent leaderboards, player rankings

---

## 📖 Topics Covered

### Fundamentals (All Databases)
- Schema design principles
- Data types and constraints
- Indexing strategies  
- Query optimization
- Transactions and ACID properties

### Intermediate
- Join types and optimization
- Aggregation and grouping
- Subqueries and CTEs
- Stored procedures and functions
- Replication basics

### Advanced
- Sharding and partitioning
- Consistency models
- Distributed transactions
- Query execution plans
- Performance tuning

### Concurrency & Isolation
- Locking mechanisms (optimistic & pessimistic)
- Isolation levels
- Deadlock prevention
- Atomic operations
- Multi-version concurrency control (MVCC)

### Optimization & Scaling
- Connection pooling
- Caching strategies (DAX, Redis)
- Read replicas
- Write optimization
- Monitoring and diagnostics

### Scaling & HA
- Horizontal scaling (sharding)
- Vertical scaling
- Load balancing
- Failover strategies
- Global replication
- Multi-region setup

---

## 🗂️ File Structure

```
/08-databases/
├── README.md (This file)
├── GETTING_STARTED.md (Quick start guide)
├── CONTENT_INVENTORY.md (File listing)
│
├── dynamodb/
│   ├── 01-basics/
│   │   ├── 01-overview.md/html (Intro, features, billing)
│   │   ├── 02-tables.md/html (Keys, indexes, design)
│   │   └── 03-items.md/html (CRUD, batch, transactions)
│   ├── 02-intermediate/
│   │   └── 01-advanced-queries.md (Optimization, GSI)
│   ├── 04-concurrency/
│   │   └── 01-concurrency-control.md (Locking, atomics)
│   ├── 05-optimization/
│   │   └── 01-performance-tuning.md (Capacity, caching)
│   └── 06-scaling/ (Global tables - coming)
│
├── mysql/
│   └── 01-basics/
│       ├── 01-overview.md/html (Intro, ACID, engines)
│       └── 02-schema-design.md (Normalization, ERD)
│
├── postgres/
│   └── 01-basics/
│       └── 01-overview.md (Advanced SQL, JSON, arrays)
│
├── mongodb/
│   └── 01-basics/
│       └── 01-overview.md (Documents, CRUD, agg)
│
└── oracle/
    └── 01-basics/
        └── 01-overview.md (Enterprise, partition)
```

---

## 💡 Each Section Includes

- **Theory**: Concepts and principles with examples
- **Code Examples**: Real, runnable code in Python/SQL/JS
- **Why**: Problem-solving rationale  
- **When**: Use case scenarios and tradeoffs
- **Best Practices**: Do's and don'ts
- **Real-World Patterns**: Production scenarios
- **Visuals**: Diagrams and execution plans (HTML files)

---

## 🚀 Getting Started

**New to Databases?**
1. Read [GETTING_STARTED.md](./GETTING_STARTED.md) for learning paths
2. Choose a database from the table above
3. Start with the Basics folder (01-overview)

**Pick a Database Based On:**
- **Open Source + Reliable:** PostgreSQL or MySQL
- **Scalability + Simplicity:** DynamoDB or MongoDB
- **Enterprise + Maximum Performance:** Oracle
- **Specific Use Case:** See "By Use Case" section above

**Learning Progression:**
1. Read markdown for detailed explanations
2. View HTML for visual understanding
3. Run code examples locally
4. Study real-world patterns
5. Practice with your own data

---

## 🔗 Cross-Database Comparison

See GETTING_STARTED.md for detailed comparison tables covering:
- Cost models
- Scaling strategies
- Consistency models
- Transaction support
- Concurrency handling
- Best use cases
- Migration considerations

---

## 📊 Content Statistics

| Database | Files | Coverage | Examples | Visuals | Status |
|----------|-------|----------|----------|---------|--------|
| DynamoDB | 11 | Basics-Optimization | 40+ | 6 | ✓ Complete |
| MySQL | 2 | Basics-Schema | 15+ | 1 | ✓ In Progress |
| PostgreSQL | 1 | Basics | 20+ | - | ✓ In Progress |
| MongoDB | 1 | Basics | 25+ | - | ✓ In Progress |
| Oracle | 1 | Basics | 15+ | - | ✓ In Progress |

---

## 🎓 Recommended Learning Orders

### For Web Developers
1. MySQL or PostgreSQL basics (relational model)
2. Indexing & optimization
3. DynamoDB for scalability
4. MongoDB for flexible schema

### For Data Engineers
1. PostgreSQL advanced SQL (CTEs, window functions)
2. MongoDB aggregation pipeline
3. DynamoDB for real-time analytics
4. Scaling & partitioning strategies

### For System Architects
1. All overviews (compare all databases)
2. Scaling strategies (sharding, replication)
3. Concurrency & consistency models
4. HA/DR patterns

---

## 🔍 Search by Topic

- **Transactions**: [DynamoDB](./dynamodb/01-basics/03-items.md), [MySQL](./mysql/01-basics/01-overview.md), [PostgreSQL](./postgres/01-basics/01-overview.md), [Oracle](./oracle/01-basics/01-overview.md)
- **Indexing**: All database overviews
- **Scaling**: [DynamoDB Scaling](./dynamodb/06-scaling/), [Oracle Partitioning](./oracle/01-basics/01-overview.md#partitioning)
- **Concurrency**: [DynamoDB Concurrency](./dynamodb/04-concurrency/01-concurrency-control.md)
- **Performance**: [DynamoDB Optimization](./dynamodb/05-optimization/01-performance-tuning.md)
- **Joins**: [MySQL Schema](./mysql/01-basics/02-schema-design.md), [PostgreSQL](./postgres/01-basics/01-overview.md)
- **JSON/Flexible**: [PostgreSQL](./postgres/01-basics/01-overview.md#jsonjsonb), [MongoDB](./mongodb/01-basics/01-overview.md)

---

## 📝 How to Use These Guides

1. **Reading Code Examples**: Copy-paste to your IDE/terminal
2. **Testing Queries**: Use local databases or cloud free tiers
3. **Visual Diagrams**: Open .html files in web browser
4. **Cross-References**: Click links to related topics
5. **Exercises**: Modify examples with your own data

---

## 🎯 Next Steps

Start with [GETTING_STARTED.md](./GETTING_STARTED.md) for:
- Learning paths by experience level
- Quick start guides by use case
- Comparative analysis
- Study strategies

Then pick a database and dive into the basics!

---

**Happy Learning!** 🚀

For questions or additions, see contributing guidelines or open an issue.
