# Columnar Storage Formats

## Row vs Columnar Storage

### Row-Oriented Storage

In row-oriented storage, all columns of a row are stored together:

```
Row Store Layout:
+------------------------------------------------+
| Row 1: id=1, name=Alice, age=30, city=NYC      |
| Row 2: id=2, name=Bob,   age=25, city=LA       |
| Row 3: id=3, name=Carol, age=35, city=CHI      |
| Row 4: id=4, name=Dave,  age=28, city=SF       |
+------------------------------------------------+

On Disk:
[1][Alice][30][NYC][2][Bob][25][LA][3][Carol][35][CHI][4][Dave][28][SF]
```

**Pros**:
- Efficient for row-level operations (OLTP: point lookups, updates, inserts)
- Single row can be read/written atomically
- Ideal for full-row scans

**Cons**:
- Reads unnecessary columns for analytical queries (I/O amplification)
- Poor compression ratio (mixed data types in same block)
- Cache-inefficient when accessing few columns from many rows

### Column-Oriented Storage

Columns are stored separately:

```
Column Store Layout:
+------------------------------------------+
| Column "id":      [1][2][3][4]           |
| Column "name":    [Alice][Bob][Carol][Dave] |
| Column "age":     [30][25][35][28]        |
| Column "city":    [NYC][LA][CHI][SF]      |
+------------------------------------------+

On Disk (separate column regions):
id.col:    [1][2][3][4]
name.col:  [Alice][Bob][Carol][Dave]
age.col:   [30][25][35][28]
city.col:  [NYC][LA][CHI][SF]
```

**Pros**:
- Read only required columns (I/O reduction: 10-100x for narrow projections)
- Excellent compression (same data type per column, high value locality)
- Better CPU cache utilization
- Enables vectorized processing (SIMD)
- Efficient encoding (RLE, dictionary, delta bit-packing)

**Cons**:
- Slow for full-row retrieval (requires reassembly)
- Expensive writes (must write to multiple column regions)
- Poor for point updates/inserts

### When to Use Which

| Workload | Pattern | Format | Example |
|----------|---------|--------|---------|
| OLTP | Many small reads/writes, point lookups | Row | Postgres row heap |
| Analytics | Scan billions of rows, few columns | Columnar | Parquet, ORC |
| Mixed | Both reads and writes to large tables | Hybrid | Delta Lake (Parquet + log) |
| Streaming append | Continuous writes | Row (in buffer) | Avro for Kafka |

## Parquet

### Overview

Apache Parquet is a columnar storage format designed for efficient data storage and retrieval. It originated from Cloudera and Twitter (based on Google's Dremel paper). Parquet is a binary format with rich metadata, compression, and encoding, supporting nested data structures via the striped/assembly algorithm from Dremel.

### File Structure

```
Parquet File:
+--------------------------------------------+
| Magic Number (4 bytes: "PAR1")             |
+--------------------------------------------+
| Row Group 0                                |
| +--------------------------------------+   |
| | Column Chunk "id"                    |   |
| | +----------+----------+----------+   |   |
| | | Page 0   | Page 1   | ...      |   |   |
| | | (dict)   | (data)   |          |   |   |
| | +----------+----------+----------+   |   |
| | Column Chunk "name"                  |   |
| | +----------+----------+----------+   |   |
| | | Page 0   | Page 1   | ...      |   |   |
| | | (RLE)    | (data)   |          |   |   |
| | +----------+----------+----------+   |   |
| | Column Chunk "age"                   |   |
| | +----------+----------+----------+   |   |
| | | Data     | Data     | ...      |   |   |
| | | Page A   | Page B   |          |   |   |
| | +----------+----------+----------+   |   |
| +--------------------------------------+   |
+--------------------------------------------+
| Row Group 1                                |
| ...                                        |
+--------------------------------------------+
| Metadata                                   |
| +--------------------------------------+   |
| | Schema (Thrift compact protocol)     |   |
| | Row group 0 metadata:                |   |
| |   - Num rows: 1,000,000              |   |
| |   - Column chunks for id, name, age  |   |
| |   - Column stats (min, max, nulls)   |   |
| | Row group 1 metadata: ...            |   |
| | Key-value metadata (app-specific)    |   |
| +--------------------------------------+   |
| Footer Metadata Length (4 bytes)           |
| Magic Number (4 bytes: "PAR1")             |
+--------------------------------------------+
```

### Row Groups

Row groups are horizontal partitions of the data:

- **Default size**: 128MB (config via `parquet.block.size`)
- **Why**: Enables parallel reading — each row group can be processed independently by different cores/nodes
- **Trade-off**: Larger row groups = better compression ratio, but more memory required for reads

```python
spark.conf.set("parquet.block.size", 268435456)  # 256MB row groups
spark.conf.set("parquet.page.size", 1048576)     # 1MB page size
spark.conf.set("parquet.dictionary.page.size", 1048576)
```

### Column Chunks

Each column chunk contains all pages for one column within a row group:

```
Column Chunk "age" (INT32):
+------------+------------+------------+------------+
| Page 0     | Page 1     | Page 2     | Page 3     |
| Data       | Data       | Data       | Dictionary |
| 8KB        | 12KB       | 10KB       | 2KB        |
+------------+------------+------------+------------+
Total: 32KB on disk
```

### Pages

The smallest storage unit in Parquet:

1. **Data Page (V1/V2)**: Stores actual column values
2. **Dictionary Page**: Stores the dictionary for dictionary encoding
3. **Data Page Header**: Metadata for the page (encoding type, num values, compression)

### Encoding Methods

#### RLE (Run-Length Encoding)

```
Input:    [1, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 3, 4]
RLE:      [(5, 1), (3, 2), (4, 3), (1, 4)]

Bit-packed hybrid (used in Parquet):
  - Run mode: (run_length << 1 | 1) + value  (when runs > 8)
  - Literal mode: bit-packed values           (when runs <= 8)
```

#### Dictionary Encoding

```
Input column "city": [NYC, LA, NYC, SF, LA, NYC, CHI, SF, NYC, LA, ...]

Dictionary:
  idx | value
   0  | NYC
   1  | LA
   2  | SF
   3  | CHI

Encoded indices: [0, 1, 0, 2, 1, 0, 3, 2, 0, 1, ...]

Storage comparison:
  1,000,000 rows x 6 bytes = 6 MB raw
  Dictionary: 4 x 6 bytes = 24 bytes
  Indices: 1,000,000 x 2 bits = 250 KB
  Total: ~250 KB vs 6 MB = 24x compression
```

Automatic fallback: if dictionary grows too large, Parquet switches to plain encoding.

#### Delta Encoding

```
Input timestamps:  1700000000, 1700000060, 1700000120, 1700000180, ...
Delta values:      +60, +60, +60, +60, ...

Min: 1700000000
Deltas: [60, 60, 60, 60] -> RLE: (4, 60)

Use case: sequential IDs, timestamps, monotonic counters
```

#### Delta-Length Byte Array (strings)

```
Input strings: ["apple", "banana", "carrot", "date", ...]

Lengths array: [5, 6, 6, 4, ...]
Content: "applebananacarrotdate..."

Delta-encode lengths, concatenate content. Excellent for text columns.
```

### Compression Codecs

| Codec | Speed | Ratio | CPU | Best For |
|-------|-------|-------|-----|----------|
| Snappy | Very fast | 1.5-2.0x | Low | General purpose, hot data |
| gzip | Moderate | 3.0-5.0x | High | Cold storage, archival |
| LZ4 | Fastest | 1.5-1.8x | Very low | Hot data, streaming |
| Zstandard (zstd) | Fast | 3.0-4.0x | Low-Medium | Best overall |
| Brotli | Slow | 4.0-6.0x | High | Maximum compression |
| LZ4_RAW | Fastest | 1.5-1.8x | Very low | Without checksum overhead |

```python
spark.conf.set("spark.sql.parquet.compression.codec", "snappy")
spark.conf.set("spark.sql.parquet.compression.codec", "zstd")
```

### Statistics and Predicate Pushdown

Parquet stores min/max/null counts per column chunk and per page:

```
Row Group 0 "age" column:
  Page 0: min=18, max=45, null_count=2, num_values=10000
  Page 1: min=20, max=65, null_count=0, num_values=12000
  Page 2: min=19, max=38, null_count=1, num_values=9500

Row Group Summary: min=18, max=65, null_count=3, total_values=31500

Query: SELECT * FROM data WHERE age > 60

Optimization:
  Page 0 max=45 --> skip (45 < 60)
  Page 1 max=65 --> must read
  Page 2 max=38 --> skip (38 < 60)
```

```python
spark.conf.set("spark.sql.parquet.filterPushdown", "true")
spark.conf.set("parquet.filter.statistics.enabled", "true")
```

### Schema

Parquet stores schema using Thrift Compact Protocol:

```
message schema {
  required int64 id;
  optional binary name (STRING);
  repeated group events {
    required binary event_type (STRING);
    required int64 timestamp;
    optional map<string, string> properties;
  }
}
```

**Schema evolution**:
- Adding nullable columns: backward/forward compatible
- Removing columns: forward compatible only
- Changing type: not allowed
- Renaming: not allowed (use column alias)

### Projection Pushdown

```python
df = spark.read.parquet("s3://data/events/").select("user_id", "event_type")
# Only reads user_id and event_type column chunks -- skips all others
```

## ORC (Optimized Row Columnar)

### Overview

ORC is a columnar storage format from Apache Hive, designed specifically for Hive workloads. It provides ACID support and richer indexes than Parquet.

### File Structure

```
ORC File:
+--------------------------------------------+
| Postscript (512 bytes)                     |
| - Footer length, compression type          |
+--------------------------------------------+
| Footer                                     |
| - Schema, stripe statistics, row index     |
| - Column encoding info                     |
+--------------------------------------------+
| Stripe 1 (default 64MB)                   |
| +--------------------------------------+   |
| | Index Data:                          |   |
| | - Row index entries (every 10K rows) |   |
| | - Bloom filter per column (optional) |   |
| | Row Data:                            |   |
| | - Present bit stream (null flags)    |   |
| | - Data stream (actual values)        |   |
| | - Dictionary stream (strings)        |   |
| | Stripe Footer:                       |   |
| | - Stream descriptors & encoding info |   |
| +--------------------------------------+   |
+--------------------------------------------+
| Stripe 2                                   |
| ...                                        |
+--------------------------------------------+
| Tail: Metadata + Footer + Postscript + ORC |
+--------------------------------------------+
```

### Key Features

**Three-level index**:
1. File-level: statistics per column across entire file
2. Stripe-level: statistics per column per stripe
3. Row-level (Row Group Index): statistics every 10,000 rows

```sql
SET hive.optimize.index.filter=true;
CREATE TABLE events STORED AS ORC TBLPROPERTIES (
    "orc.row.index.stride" = "10000",
    "orc.create.index" = "true"
);

SELECT * FROM events WHERE event_date = '2024-03-15';
-- Stripe index -> row group index -> only matching rows
```

### Bloom Filters

Bloom filters provide fast "definitely not in set" checks:

```
Bloom Filter for "user_id":
  Bit array: [1,0,0,1,1,0,1,0,1,1,...]  (2^16 bits = 8KB)

  Add "alice": hash1("alice")->pos=3, hash2("alice")->pos=7
  Check "charlie": pos 3=1, pos 10=0 -> NOT in stripe, skip!
```

```sql
CREATE TABLE events STORED AS ORC TBLPROPERTIES (
    "orc.bloom.filter.columns" = "user_id,event_type",
    "orc.bloom.filter.fpp" = "0.05"
);
```

### ACID via Hive

```sql
CREATE TABLE transactional_table (
    id INT, value STRING
)
CLUSTERED BY (id) INTO 10 BUCKETS
STORED AS ORC
TBLPROPERTIES (
    "transactional" = "true",
    "transactional_properties" = "insert_only",
    "orc.compress" = "zlib"
);

INSERT INTO transactional_table VALUES (1, 'hello');
UPDATE transactional_table SET value = 'world' WHERE id = 1;
DELETE FROM transactional_table WHERE id = 2;
```

**ACID mechanics**:
- Base files: original ORC files (immutable)
- Delta files: small ORC files for changes
- Compactor merges base + delta into new base
- Readers merge base + delta at read time

## Avro

### Overview

Apache Avro is a row-oriented serialization framework with rich schema support, designed for data exchange between systems, especially Kafka streams.

### Schema (JSON)

```json
{
  "type": "record",
  "namespace": "com.example",
  "name": "User",
  "fields": [
    {"name": "name", "type": "string"},
    {"name": "age", "type": "int"},
    {"name": "email", "type": ["null", "string"], "default": null},
    {"name": "address", "type": {
      "type": "record",
      "name": "Address",
      "fields": [
        {"name": "street", "type": "string"},
        {"name": "city", "type": "string"},
        {"name": "zip", "type": "string"}
      ]
    }},
    {"name": "tags", "type": {"type": "array", "items": "string"}},
    {"name": "metadata", "type": {"type": "map", "values": "string"}}
  ]
}
```

### Schema Evolution

```json
// v1 schema
{"name": "User", "fields": [
  {"name": "name", "type": "string"},
  {"name": "age", "type": "int"}
]}

// v2 (backward compatible -- added field with default)
{"name": "User", "fields": [
  {"name": "name", "type": "string"},
  {"name": "age", "type": "int"},
  {"name": "email", "type": ["null", "string"], "default": null}
]}

// v3 (forward compatible -- removed field)
{"name": "User", "fields": [
  {"name": "name", "type": "string"}
]}
```

**Compatibility modes**: Backward, Forward, Full, None

### Binary Encoding

```
Record: {"name": "Alice", "age": 30}

Encoded bytes:
  0A                     (length 10, varint)
  41 6C 69 63 65         ("Alice" UTF-8)
  3C                     (int 30, zigzag varint)

Total: 12 bytes vs ~20 bytes JSON
```

| Type | Encoding |
|------|----------|
| null | 0 bytes |
| boolean | 1 byte |
| int | Variable-length zigzag (1-5 bytes) |
| long | Variable-length zigzag (1-10 bytes) |
| float | 4 bytes LE |
| double | 8 bytes LE |
| string | Length (varint) + UTF-8 |

### Container File Format

```
Avro Container File:
+--------------------------------------------+
| Header:                                    |
| - Magic bytes (4 bytes: "Obj1")            |
| - Schema JSON (length + UTF-8)             |
| - Sync marker (16 random bytes)            |
+--------------------------------------------+
| Block 0:                                   |
| - Block count (long: num records)          |
| - Block size (long: compressed size)       |
| - Serialized records (binary + compression)|
| - Sync marker                              |
+--------------------------------------------+
| Block 1:                                   |
| ...                                        |
+--------------------------------------------+

Key features:
- Splittable (sync markers every block)
- Compressible per-block (snappy, deflate, zstd)
- Schema stored once in header, not per record
```

## Arrow

### Overview

Apache Arrow is a cross-language, in-memory columnar data format. Unlike Parquet/ORC (storage formats), Arrow is designed for zero-copy data sharing and high-performance analytics.

### Columnar Format in Memory

```
Arrow Columnar Layout (fixed-width types):
+--------------------------------------------------+
| Int64 Array:                                      |
| +--------+--------+--------+--------+--------+   |
| | Val 0  | Val 1  | Val 2  | Val 3  | Val 4  |   |
| | 8 bytes| 8 bytes| 8 bytes| 8 bytes| 8 bytes|   |
| +--------+--------+--------+--------+--------+   |
| Validity bitmap (1 bit per value):                |
| [1, 1, 0, 1, 1, ...]                              |
+--------------------------------------------------+

Variable-length (strings):
+--------------------------------------------------+
| Offsets (int32 array):                            |
| [0, 5, 11, 17, 21, ...]                           |
| Data: "applebananacarrotdate..."                   |
+--------------------------------------------------+

Nested types (Lists):
+--------------------------------------------------+
| Offsets: [0, 3, 7, 9, ...]                        |
| Child array (int32): [1, 2, 3, 4, 5, 6, 7, ...]  |
+--------------------------------------------------+
```

### Key Features

1. **Zero-copy reads**: Data can be shared between processes without serialization
2. **SIMD-friendly**: Columnar layout enables vectorized processing
3. **Language interop**: C, C++, Python, Java, Rust, Go, JavaScript
4. **IPC format**: Standard for transferring data between processes

### Zero-Copy

```
Process A (Python)                     Process B (Java)
+-----------------------+             +-----------------------+
| PyArrow DataFrame     |             | Arrow Dataset         |
| +-------------------+ |   mmap     | +-------------------+ |
| | Arrow RecordBatch | | ---------> | | Arrow RecordBatch | |
| | (shared memory)   | | zero-copy  | | (same memory)     | |
| +-------------------+ |             | +-------------------+ |
+-----------------------+             +-----------------------+

No serialization! Same bytes in memory, different language bindings.
```

### IPC Format

```
Arrow IPC Stream Format:
+----------------------------------+
| Continuation Indicator (4 bytes) |
| Message Size (4 bytes)           |
| Message (flatbuffer serialized): |
|   - Schema                       |
|   - RecordBatch (dictionary +    |
|     body lengths)                |
+----------------------------------+
| Message Body:                    |
| - Buffer 0: validity bitmap      |
| - Buffer 1: data (offsets)       |
| - Buffer 2: data (values)        |
| - Buffer N: ...                  |
+----------------------------------+
| EOS (continuation indicator = 0) |
+----------------------------------+
```

### Flight SQL

Arrow Flight SQL is a protocol for high-performance database access:

```
Client                     Flight SQL Server
  |                               |
  |-- GetFlightInfo(sql) -------->|
  |<-- FlightInfo (endpoints) ----|
  |                               |
  |-- DoGet(ticket) ------------->|
  |<-- FlightData stream ---------|
  |   (Arrow RecordBatches)       |
  |<-- (more FlightData)          |
  |<-- FINISHED                   |
  |                               |

Benefits:
  - 10-100x faster than JDBC/ODBC (no per-row serialization)
  - Parallel data access (multiple endpoints per query)
  - Encryption + auth built in (mTLS, OAuth)
```

### Arrow vs Other Formats

| Feature | Arrow | Parquet | Avro |
|---------|-------|---------|------|
| Primary use | In-memory processing | Disk storage | Data exchange |
| Access | Random access | Scan-heavy | Sequential |
| Compression | Minimal (encoding) | Heavy (compression + encoding) | Per-block |
| Schema | Fixed at read time | Schema evolution limited | Full evolution |
| Zero-copy | Yes | No | No |
| Language support | 15+ | 10+ | 10+ |
| Nested data | Yes (offset-based) | Yes (repetition/definition) | Yes (nested records) |

## Comparison: Parquet vs ORC vs Avro vs Arrow

### Feature Matrix

| Feature | Parquet | ORC | Avro | Arrow |
|---------|---------|-----|------|-------|
| Orientation | Columnar | Columnar | Row | Columnar |
| Storage | Disk (persistent) | Disk (persistent) | Disk (persistent) | Memory |
| Compression | Excellent | Excellent | Good | Minimal |
| Schema evolution | Limited | Limited | Full | Fixed |
| Predicate pushdown | Page-level | Row-group + Bloom | None | N/A |
| ACID | Via Delta/Iceberg | Native (Hive) | No | No |
| Encodings | RLE, Dict, Delta | RLE, Dict, Delta | None (binary) | Fixed-width |
| Splittable | Yes (row groups) | Yes (stripes) | Yes (blocks) | Yes (batches) |
| Nested data | Dremel (Rep/Def) | Similar to Parquet | Nested records | Offset-based |
| Vectorized reads | Yes (Spark, Arrow) | Yes (Hive, Spark) | No | Native |
| Write speed | Moderate | Moderate | Fast | Fastest |
| Read speed (few cols) | Excellent | Excellent | Poor | Excellent |
| Read speed (all cols) | Good | Good | Excellent | Excellent |

### Decision Guide

```
Use Parquet when:
  - Analytical workloads with column projection
  - You need broad query engine support (Spark, Trino, Hive, Athena)
  - Predicate pushdown is important
  - You're building a lakehouse (Delta Lake / Iceberg)

Use ORC when:
  - You're in a Hive-heavy ecosystem
  - You need ACID transactions natively
  - Bloom filter-based filtering helps your queries
  - You want the best ORC-specific optimizations (Hive LLAP)

Use Avro when:
  - Streaming/buffering data (Kafka topics, Flume)
  - Schema evolution is a primary concern
  - Row-level access is common
  - You need fast serialization/deserialization

Use Arrow when:
  - In-memory analytics (Pandas, NumPy integration)
  - Zero-copy inter-process communication
  - High-performance database access (Flight SQL)
  - SIMD-optimized computation pipelines

Trade-offs table:
| You need...                | Choose... |
|---------------------------|-----------|
| Best storage compression  | ORC       |
| Broadest engine support   | Parquet   |
| Best schema evolution     | Avro      |
| Fastest columnar scans    | Arrow     |
| ACID updates/deletes      | Delta/Iceberg over Parquet |
| Streaming ingestion       | Avro      |
| In-memory analytics       | Arrow     |
```

### Hybrid Patterns

Modern systems combine formats:

```
Streaming Pipeline:
  Kafka (Avro) --> Flink/Spark --> S3 (Parquet) --> Trino/Analytics

Lakehouse:
  Parquet + Delta Transaction Log --> ACID + Time Travel

Real-time Analytics:
  Arrow Flight --> GPU (cuDF/RAPIDS) --> Arrow --> Dashboard

Data Lake:
  Landing: Avro (fast writes)
  Staging: Parquet (optimized for Spark ETL)
  Curated: Parquet with Z-order (optimized for analytics queries)
```
