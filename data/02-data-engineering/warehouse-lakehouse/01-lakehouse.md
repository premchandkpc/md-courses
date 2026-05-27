# Lakehouse Architecture

## Data Lake vs Warehouse vs Lakehouse

### Evolution

```
2000s: Data Warehouse
  +------------------+
  |   BI / Reports   |
  +------------------+
  |    SQL Engine     |
  +------------------+
  |  Proprietary      |
  |  Storage (Teradata|
  |  Oracle, Vertica) |
  |  Expensive $      |
  +------------------+

2010s: Data Lake
  +------------------+
  |   BI / ML / DS   |
  +------------------+
  |  Spark / Hive    |
  +------------------+
  |  Cheap Storage   |
  |  (S3, HDFS)      |
  |  Raw files       |
  |  (JSON, CSV,     |
  |   Parquet, Avro) |
  +------------------+

2020s: Lakehouse
  +------------------+
  |  BI / ML / DS    |
  |  + SQL + Stream  |
  +------------------+
  |  Delta / Iceberg |
  |  / Hudi          |
  |  (ACID, Time     |
  |   Travel, Schema |
  |   Enforcement)   |
  +------------------+
  |  Cheap Storage   |
  |  (S3, ADLS, GCS) |
  +------------------+
```

### Comparison Matrix

| Feature | Data Lake | Data Warehouse | Lakehouse |
|---------|-----------|---------------|-----------|
| ACID transactions | No | Yes | Yes |
| Schema enforcement | Read-time | Write-time | Write-time |
| BI tool support | Poor | Excellent | Excellent |
| ML/AI support | Excellent | Poor | Excellent |
| Storage cost | Low | High | Low |
| Compute/storage coupling | Decoupled | Tight | Decoupled |
| Time travel | No | Limited | Yes |
| Streaming | Complex | Batch only | Yes |
| Data types | Any (raw) | Structured | Any |
| Open format | Yes | No | Yes |
| Governance | Manual | Built-in | Transaction log |

### Key Insight

The lakehouse brings warehouse-grade reliability and ACID to cheap object storage by adding a **transaction log** on top of open file formats (Parquet). This gives you:

- Reliable concurrent writes (multiple writers, readers)
- Snapshot isolation (readers see consistent state)
- Time travel (query data as of any previous version)
- Schema enforcement (reject bad data at write time)

## Delta Lake

### Architecture

Delta Lake by Databricks is an open-source storage layer that brings ACID transactions to Apache Spark. It uses a **transaction log** (`_delta_log`) directory alongside Parquet data files.

```
Table Directory:
  s3://data/warehouse/events/
  |
  +-- _delta_log/
  |   +-- 00000000000000000000.json    (initial commit)
  |   +-- 00000000000000000001.json    (1st add/remove)
  |   +-- 00000000000000000002.json    (2nd commit)
  |   +-- ...                          (one per transaction)
  |   +-- _last_checkpoint            (optimization for reads)
  |
  +-- part-00000-xxx.snappy.parquet    (data file v1)
  +-- part-00001-xxx.snappy.parquet
  +-- part-00002-xxx.snappy.parquet
  |
  (After OPTIMIZE, new files replace old ones:
  +-- part-00000-yyy.snappy.parquet    (compacted file)
  ...)
```

### Transaction Log

Each JSON file in the `_delta_log` directory is an **atomic commit**:

```json
// 00000000000000000001.json
{
  "commitInfo": {
    "timestamp": 1700000000000,
    "operation": "WRITE",
    "operationParameters": {"mode": "Append"},
    "isolationLevel": "Serializable"
  },
  // Files to add
  "add": {
    "path": "part-00000-xxx.snappy.parquet",
    "partitionValues": {"date": "2024-03-15"},
    "size": 268435456,
    "modificationTime": 1700000000000,
    "dataChange": true,
    "stats": "{\"numRecords\":1000000,\"minValues\":{\"id\":1},\"maxValues\":{\"id\":1000000},\"nullCount\":{\"email\":0}}"
  },
  // Files to remove (none for first write)
  "remove": {}
}
```

**Transaction log guarantees**:
- Atomic: All-or-nothing via atomic rename on object store
- Consistent: Each version is a complete snapshot of the table
- Durable: Stored on durable object storage
- Serializable: Two concurrent writers use optimistic concurrency

### ACID Properties

```
Atomicity:
  Write begins -> Write files to temp dir -> Check conditions
  -> Atomic rename _delta_log/XXXX.json
  -> Write committed (or retry on conflict)

Consistency:
  Schema enforced at write time (reject mismatched data)
  Invariants checked (NOT NULL, CHECK constraints)

Isolation:
  Read: Snapshot isolation (reader sees version N at open time)
  Write: Serializable isolation (optimistic concurrency)
  Conflicting writes: one succeeds, others retry

Durability:
  Data in S3 (11 9's durability)
  Log in S3 (same durability)
```

```python
from delta import DeltaTable, DeltaMergeBuilder

# ACID upsert (merge)
delta_table = DeltaTable.forPath(spark, "s3://data/events")

delta_table.alias("target") \
    .merge(
        updates_df.alias("source"),
        "target.event_id = source.event_id"
    ) \
    .whenMatchedUpdateAll() \
    .whenNotMatchedInsertAll() \
    .execute()
```

### Time Travel

```python
# Read latest version
df = spark.read.format("delta").load("s3://data/events")

# Read version 50
df_v50 = spark.read.format("delta") \
    .option("versionAsOf", 50) \
    .load("s3://data/events")

# Read as of timestamp
df_ts = spark.read.format("delta") \
    .option("timestampAsOf", "2024-03-15 10:00:00") \
    .load("s3://data/events")

# Restore table to version 50 (creates new commit)
delta_table.restoreToVersion(50)

# Check history
delta_table.history().show(truncate=False)
# +-------+--------+------+------------------+
# |version|operation|user  |timestamp         |
# +-------+--------+------+------------------+
# |52     |RESTORE |admin |2024-04-01 12:00  |
# |51     |WRITE   |bot   |2024-03-20 08:00  |
# |50     |WRITE   |alice |2024-03-15 10:00  |
# +-------+--------+------+------------------+
```

### Schema Enforcement

```python
# Schema on write: only allows compatible schema changes
from delta.tables import DeltaTable

df_invalid = spark.createDataFrame([
    (1, "event_a", 100.0, "extra_col"),
], schema="event_id INT, event_type STRING, value DOUBLE, extra STRING")

# This FAILS -- schema mismatch (extra column not in table)
df_invalid.write.format("delta").mode("append").save("s3://data/events")

# Schema evolution (opt-in)
df_invalid.write.format("delta") \
    .option("mergeSchema", "true") \
    .mode("append") \
    .save("s3://data/events")

# Schema validation
delta_table = DeltaTable.forPath(spark, "s3://data/events")
delta_table.schema().printTreeString()
```

### OPTIMIZE and Z-order

```python
# Compaction: merge small files into larger ones
spark.sql("OPTIMIZE delta.`s3://data/events`")

# With file size target
spark.sql("OPTIMIZE delta.`s3://data/events` WHERE date >= '2024-03-01'")

# Z-order clustering: colocate related data on disk
spark.sql("OPTIMIZE delta.`s3://data/events` ZORDER BY (user_id, event_type)")

# Auto-optimize (continuous)
spark.conf.set("spark.databricks.delta.autoCompact.enabled", "true")
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")
```

**Z-order effect**:
```
Without Z-order:
  File 1: user_0..100, event_type = random
  File 2: user_101..200, event_type = random
  File 3: user_201..300, event_type = random
  Query: WHERE user_id = 42 -> scans all files

With Z-order (clustered by user_id):
  File 1: user_0..50
  File 2: user_51..100
  File 3: user_101..150
  Query: WHERE user_id = 42 -> scans only File 1

With Z-order (clustered by user_id, event_type):
  Data is reorganized so similar values are in same files
  Query on user_id or event_type reduces scan significantly
```

### Vacuum

```python
# Remove old files no longer referenced by any version
# Default retention: 7 days (must be > 168h for safety)
delta_table.vacuum(retentionHours=168)

# Dry run to see what would be deleted
delta_table.vacuum(retentionHours=168, dryRun=True)
```

**Vacuum considerations**:
- Only removes files older than `retentionHours`
- Cannot time travel past vacuum-retained versions
- Default 7 days protects against long-running queries
- Vacuum is NOT transactional with concurrent reads

## Apache Iceberg

### Architecture

Apache Iceberg is a table format designed for large analytic datasets. It introduces a **three-level metadata hierarchy**:

```
Catalog (Hive Metastore / AWS Glue / Nessie)
  |
  +-- Table: my_db.events
       |
       +-- Metadata Layer
       |   |
       |   +-- v1.metadata.json
       |   |    (current version pointer)
       |   |    +-- Schema, partition spec, sort order
       |   |    +-- Snapshot list (0, 1, 2, ...)
       |   |    +-- Location: root path
       |   |
       |   +-- snap-00000001-xxx.avro
       |   |    (Snapshot: list of manifest files)
       |   |
       |   +-- snap-00000002-yyy.avro
       |        (Snapshot: list of manifest files)
       |
       +-- Manifest Layer
       |   |
       |   +-- manifest-aaa.avro
       |   |    (List of data files + column stats)
       |   |    +-- part-00000.parquet, min_id=1, max_id=1000
       |   |    +-- part-00001.parquet, min_id=1001, max_id=2000
       |   |
       |   +-- manifest-bbb.avro (newer version)
       |
       +-- Data Layer (Parquet / Avro / ORC)
           |
           +-- data/date=2024-03-15/
           |   +-- part-00000.parquet
           |   +-- part-00001.parquet
           |
           +-- data/date=2024-03-16/
               +-- part-00000.parquet
```

### Table Format

```sql
-- Create Iceberg table
CREATE TABLE events (
    event_id BIGINT,
    user_id STRING,
    event_type STRING,
    amount DOUBLE,
    ts TIMESTAMP
)
USING iceberg
PARTITIONED BY (days(ts))  -- Hidden partitioning
LOCATION 's3://data/iceberg/events';

-- Write data
INSERT INTO events VALUES (1, 'alice', 'purchase', 29.99, TIMESTAMP '2024-03-15 10:00:00');

-- Snapshot isolation query
SELECT count(*) FROM events FOR SYSTEM_VERSION AS OF 1;
SELECT count(*) FROM events FOR SYSTEM_TIME AS OF '2024-03-15 12:00:00';
```

### Manifest Files

Manifests are Avro files listing data files with column statistics:

```
Manifest Entry:
  - File path: s3://data/warehouse/events/part-00000.parquet
  - File format: PARQUET
  - Partition data: days(ts)=2024-03-15
  - Record count: 1,000,000
  - File size: 256 MB
  - Column statistics:
    event_id: min=1, max=1000000, null_count=0
    user_id: min_size=4, max_size=20, null_count=5
    amount: min=0.99, max=999.99, null_count=50
    ts: min=2024-01-01, max=2024-03-15, null_count=0
```

### Partitioning Evolution

Iceberg supports **partition evolution** — changing the partition scheme without rewriting data:

```sql
-- Table initially partitioned by days(ts)
ALTER TABLE events SET PARTITION SPEC (
    days(ts), bucket(16, user_id)
);
-- Old data: only days(ts) partitions
-- New data: days(ts) + bucket(user_id) partitions
-- Queries: read both partition specs transparently
```

### Hidden Partitioning

Iceberg automatically computes partition values from data:

```sql
-- No need to specify partition column in WHERE clause
-- Iceberg knows that ts = '2024-03-15' maps to partition days(ts)=2024-03-15

SELECT * FROM events WHERE ts >= '2024-03-15' AND ts < '2024-03-16'
-- Automatically prunes to partition days(ts)=2024-03-15

-- Vs traditional Hive partitioning (user must specify partition column):
SELECT * FROM hive_events WHERE event_date = '2024-03-15'  -- Must know partition column
```

### Snapshot Isolation

Iceberg uses **serializable snapshot isolation**:

```
Writer 1: Start transaction (snapshot N)
  -> Write new data files
  -> Create manifest listing new files
  -> Create snapshot N+1 pointing to new manifests
  -> Commit: atomic swap of current snapshot pointer

Writer 2: Start transaction (snapshot N, concurrent with Writer 1)
  -> Same process
  -> Commit attempt fails (snapshot pointer changed)
  -> Retry: read new snapshot N+1, re-apply conflict detection
```

**Concurrency model**:
- Optimistic concurrency (no locks)
- Retry on conflict (max 4 retries by default)
- Catalog-level atomic compare-and-swap (HMS notification, DynamoDB lock)

### Iceberg in Practice

```python
# Spark SQL with Iceberg
spark.sql("""
    MERGE INTO events AS t
    USING updates AS s
    ON t.event_id = s.event_id
    WHEN MATCHED THEN UPDATE SET *
    WHEN NOT MATCHED THEN INSERT *
""")

# Compaction via Spark
spark.sql("CALL spark_catalog.system.rewrite_data_files('db.events')")

# Expire old snapshots
spark.sql("CALL spark_catalog.system.expire_snapshots('db.events', TIMESTAMP '2024-01-01')")

# Remove orphan files
spark.sql("CALL spark_catalog.system.remove_orphan_files('db.events')")
```

## Apache Hudi

### Architecture

Apache Hudi (Hadoop Upserts Deletes and Incrementals) is designed for incremental data processing and streaming ingestion.

### Copy-on-Write (COW)

```
Write: Merge input with existing file group
  Input: rows to update/insert

  File Group:
    v1 (base): part-00000.parquet (id range 1-1000)

  Step 1: Read v1 file
  Step 2: Merge input records into file
  Step 3: Write new v2 base file (v1 + changes)
  Step 4: Mark v1 as deleted, v2 as active

Reads: Read v2 directly (single file) -- fast reads
Writes: Full file rewrite -- expensive for small upserts
```

### Merge-on-Read (MOR)

```
Write: Append delta to separate log files
  File Group:
    v1 (base): part-00000.parquet (id range 1-1000)

  Insert: write to new log file
    +-- .log.1 (delta: inserts 1001-1050)

  Update: write to delta log
    +-- .log.1 (delta: updates to id 100-200)

Reads:
  Snapshot read: merge base + delta (slower, but always fresh)
  Read-optimized: read base only (fast, stale data)
  Incremental read: read only delta logs since last commit

Compaction (async):
  Merge base + delta files into new base file
  v2 (base): part-00000.parquet (merged)
  Delete log files
```

### Incremental Queries

```python
# Hudi incremental query (process only changed rows)
incremental_df = spark.read \
    .format("hudi") \
    .option("hoodie.datasource.query.type", "incremental") \
    .option("hoodie.datasource.read.begin.instanttime", "20240315000000") \
    .option("hoodie.datasource.read.end.instanttime", "20240316000000") \
    .load("s3://data/hudi/events")

# Stream from Hudi (continual processing)
streaming_df = spark.readStream \
    .format("hudi") \
    .option("hoodie.datasource.query.type", "streaming") \
    .option("hoodie.datasource.streaming.enable", "true") \
    .load("s3://data/hudi/events")
```

### Clustering

```python
# Hudi clustering reorganizes data for query efficiency
spark.sql("CALL run_clustering(table => 'hudi_events', order => 'user_id')")

# Configuration
spark.conf.set("hoodie.clustering.inline", "true")  # Inline with writes
spark.conf.set("hoodie.clustering.inline.max.commits", "4")  # Every 4 commits
spark.conf.set("hoodie.clustering.plan.strategy.target.file.max.bytes", "268435456")
spark.conf.set("hoodie.clustering.plan.strategy.sort.columns", "user_id")
```

### MOR Compaction

```python
# Inline compaction (immediate)
spark.conf.set("hoodie.compact.inline", "true")
spark.conf.set("hoodie.compact.inline.max.delta.commits", "5")  # After 5 delta commits

# Async compaction (separate Spark job)
spark-submit --class org.apache.hudi.utilities.HoodieCompactor \
    --table-type MERGE_ON_READ \
    --base-path s3://data/hudi/events

# Delta commits threshold (trigger compaction)
spark.conf.set("hoodie.compaction.delta.commits", "10")
spark.conf.set("hoodie.compaction.delta.seconds", "3600")
```

## Comparison: Delta vs Iceberg vs Hudi

### Feature Matrix

| Feature | Delta Lake | Apache Iceberg | Apache Hudi |
|---------|-----------|----------------|-------------|
| Origin | Databricks | Netflix/Expedia | Uber |
| Format | Parquet + JSON log | Parquet/Avro/ORC + Avro manifests | Parquet/Avro + HFile logs |
| Open source | Yes (Linux Foundation) | Yes (Apache) | Yes (Apache) |
| ACID isolation | Serializable | Serializable | Snapshot |
| Time travel | Yes (version/timestamp) | Yes (version/timestamp) | Yes (via commits) |
| Schema evolution | Add/drop/rename/comment | Add/drop/rename/reorder | Add/drop/rename |
| Partition evolution | No (rewrite required) | Yes | No |
| Hidden partitioning | No | Yes | No |
| Merge/Upsert | MERGE SQL | MERGE SQL | Write API + SQL |
| Incremental queries | Change Data Feed | Incremental read | Native incremental |
| Streaming ingest | Auto-compact | Rewrite data files | COW/MOR + compaction |
| Clustering/Z-order | Z-order | Sort-order + rewrite | Clustering |
| Catalog | Hive, AWS Glue, custom | Hive, Glue, Nessie, REST | Hive, Glue |
| Query engines | Spark, Trino, Flink, Presto | Spark, Trino, Flink, Presto, Dremio | Spark, Trino, Flink, Presto |
| Performance (reads) | Good | Excellent (manifest pruning) | Good |
| Performance (writes) | Good | Good | Excellent (MOR) |

### Decision Guide

```
Use Delta Lake when:
  - You're in a Databricks/Spark-centric ecosystem
  - You need simple, production-tested ACID
  - Z-order clustering fits your query patterns
  - You want auto-optimize for streaming ingestion
  - You need Unity Catalog integration

Use Apache Iceberg when:
  - You need multi-engine support (Trino, Spark, Flink, Dremio)
  - Partition evolution is important (changing partition schemes)
  - Hidden partitioning simplifies queries
  - REST catalog gives you Git-like branching (Nessie)
  - You want the best read performance via manifest pruning
  - You're building a truly open lakehouse

Use Apache Hudi when:
  - Streaming/batch ingestion with upserts is your primary pattern
  - MOR helps balance write speed with read consistency
  - You need native incremental queries (CDC pipelines)
  - Clustering for query performance
  - You're at Uber-scale with high-frequency updates

Migration paths:
  - Parquet tables -> Delta Lake (add _delta_log)
  - Hive tables -> Iceberg (migrate with spark.sql.catalog)
  - Hive tables -> Hudi (hoodie.datasource.write.operation)
```

## Query Engines

### Trino

Trino (formerly Presto SQL) is a distributed SQL query engine designed for large-scale analytics.

```sql
-- Connect to Iceberg table via Trino
SELECT COUNT(*), event_type
FROM iceberg.db.events
WHERE ts >= TIMESTAMP '2024-03-01'
GROUP BY event_type;

-- Trino connector config (etc/catalog/iceberg.properties)
-- connector.name=iceberg
-- iceberg.catalog.type=hive
-- hive.metastore.uri=thrift://metastore:9083
```

**Connector matrix**:

| Engine | Delta | Iceberg | Hudi | Hive |
|--------|-------|---------|------|------|
| Trino | Yes (delta-lake connector) | Yes (iceberg connector) | Yes (hudi connector) | Yes |
| Presto | Limited | Yes | Yes | Yes |
| Spark SQL | Native | Native | Native | Native |
| Athena | Yes (through Glue) | Yes (Glue catalog) | Limited | Yes |
| Snowflake | Yes (UniCatalog) | Yes (Iceberg tables) | No | No |
| Dremio | Yes | Yes | Yes | Yes |

### Performance Considerations

```sql
-- Trino: pushdown projections and predicates
EXPLAIN (TYPE DISTRIBUTED)
SELECT event_type, count(*)
FROM events
WHERE ts >= DATE '2024-03-01'
  AND amount > 100
GROUP BY event_type;
-- Output shows:
--   - Predicate pushdown: ts >= 2024-03-01 AND amount > 100
--   - Projection pushdown: event_type only
--   - Partition pruning: only scans date >= 2024-03-01 directories
```

## Catalog

### Hive Metastore

The traditional catalog for Hive/Spark tables:

```
Spark/Trino/Flink --> Hive Metastore (HMS)
                       |
                       +-- Database --> Table --> Partition
                       |
                       +-- Thrift API (port 9083)
                       |
                       +-- Backend (MySQL/Postgres)
                       |
                       +-- Stores: schema, partition metadata, location
```

### AWS Glue Catalog

Serverless catalog on AWS:

```
AWS Glue Catalog:
  - REST API (replace Hive Metastore)
  - Integrated with Athena, Redshift Spectrum, EMR
  - Crawlers to auto-discover schema
  - Fine-grained permissions (Lake Formation)
  - Serverless (no infrastructure to manage)

Configuration:
  spark.conf.set("spark.sql.catalog.glue", "org.apache.iceberg.spark.SparkCatalog")
  spark.conf.set("spark.sql.catalog.glue.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
  spark.conf.set("spark.sql.catalog.glue.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
```

### Nessie (Catalog with Git-like Branching)

Nessie brings Git semantics to data lakes:

```
Nessie Catalog:
  Branch: main
    |
    +-- Commit: Table events v1
    +-- Commit: Table events v2 (add column)
    +-- Commit: Table users v1 (new table)
    |
  Branch: dev (from main@v2)
    |
    +-- Commit: Rewrite events partition scheme
    |
  Branch: feature-experiment (from dev@v3)
    |
    +-- Commit: Add experimental columns
    |
  Tag: release-2024.03
    |
    +-- Points to main@v3
```

```sql
-- Trino with Nessie catalog
SELECT * FROM nessie.events.main;            -- Main branch
SELECT * FROM nessie.events.dev;             -- Dev branch
SELECT count(*) FROM nessie.events.main;     -- Current production

-- Nessie operations
CREATE BRANCH dev IN nessie FROM main;
MERGE dev INTO main IN nessie;
```

**Nessie benefits**:
- Isolated experimentation (branch before schema changes)
- Reproducible queries (query by commit hash)
- Zero-copy branching (metadata only, not data)
- CI/CD for data (PR → merge to main)

---

## Related

- [Databases](../../08-databases/) — Data storage and querying
- [Messaging](../../10-messaging/) — Event streaming (Kafka)
- [Cloud Platforms](../../05-cloud/) — Data warehousing (Redshift, BigQuery)
- [Backend](../../03-backend/) — Data service APIs
- [Distributed Systems](../../09-distributed-systems/) — Scale and consistency
