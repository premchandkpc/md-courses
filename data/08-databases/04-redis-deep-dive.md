# 🚀 Redis — Complete Deep Dive

## Table of Contents
1. [Data Structures Overview](#data-structures-overview)
2. [Data Structure Internals](#data-structure-internals)
3. [Memory Optimization](#memory-optimization)
4. [Persistence](#persistence)
5. [Replication](#replication)
6. [Redis Cluster](#redis-cluster)
7. [Sentinel](#sentinel)
8. [Transactions & Lua](#transactions--lua)
9. [Modules](#modules)
10. [Simplest Mental Model](#simplest-mental-model)

---

## Data Structures Overview

```text
String      → SDS (512MB max)
List        → quicklist
Set         → intset / dict
Sorted Set  → skiplist + dict
Hash        → listpack / dict
Stream      → radix tree
Bitmap      → string as bits
HyperLogLog → probabilistic (~12KB, 2^64 count)
Geospatial  → geohash + sorted set
Bloom/Cuckoo/T-Digest/CMS → modules
```

---

## Data Structure Internals

### SDS (Simple Dynamic String)

```text
┌──────┬──────┬──────┬──────────────────────┐
│ len  │ alloc│flags │  buf[]               │
│ (4B) │ (4B) │ (1B) │ (flexible, null-term)│
└──────┴──────┴──────┴──────────────────────┘
```

O(1) length, binary safe, preallocation to next power of 2.

### Encoding

```python
EMBSTR_LIMIT = 44  # 64 - header(19) - null(1)
if len(value) <= EMBSTR_LIMIT:
    encoding = "embstr"  # single alloc
elif value.isdigit() and within_int64:
    encoding = "int"     # stored as C long
else:
    encoding = "raw"     # separate allocs
```

### SkipList (Sorted Set)

```text
Level 4:  ──────► 45 ──────────────────────────► NULL
Level 3:  ──────► 45 ─────────────► 78 ────────► NULL
Level 2:  ──────► 45 ───► 62 ─────► 78 ───► 99 ─► NULL
Level 1:  ─────► 12 ──► 45 ──► 62 ──► 78 ──► 99 ─► NULL
             HEAD

Search 78: HEAD→45(L4)→drop→45(L3)→78→FOUND
```

```python
def random_level():
    level = 1
    while random() < 0.25 and level < MAX_LEVEL:
        level += 1
    return level
```

### Dict (Hash Table)

```python
class RedisDict:
    def __init__(self):
        self.ht = [HashTable(4), HashTable(0)]
        self.rehashidx = -1

    def insert(self, key, val):
        if self.ht[0].used >= self.ht[0].size * 5:  # load factor
            self._start_rehash(self.ht[0].size * 2)
        if self.rehashidx >= 0:
            self._rehash_step()

    def _rehash_step(self):
        # Incremental: move 10 buckets per operation
        for _ in range(10):
            if self.rehashidx < 0:
                break
            # Move bucket from ht[0] → ht[1]
            self.rehashidx += 1
```

### Stream (Radix Tree)

Compressed trie with listpack leaf nodes. Each entry ID = `timestamp-sequence`.

---

## Memory Optimization

### Key Naming & Expiration

```redis
# Bad: long prefixes
SET "user:12345:profile:email:verified" "true"
# Good: short
SET "u:12345:eml_vrf" "true"
SETEX "session:abc123" 3600 "data"
```

Expiration: **Lazy** (check on access) + **Active** (sample 20 keys every 100ms, if >25% expired, repeat).

### Eviction Policies

```redis
maxmemory 4gb
maxmemory-policy allkeys-lru   # General purpose
```

```text
allkeys-lru      → LRU among all keys       [general]
allkeys-lfu      → LFU among all keys       [repeated patterns]
volatile-lru     → LRU among keys with TTL  [if you set TTLs]
noeviction       → return errors on writes  [safety]
allkeys-random   → random eviction          [uniform access]
```

### Memory Fragmentation

```bash
INFO memory | grep mem_fragmentation_ratio
# >1.5 → fragmentation (check jemalloc)
# <1.0 → swapping (BAD)

CONFIG SET activedefrag yes
```

**jemalloc:** Size classes (8, 16, 32, 48, 64, ...) — each has own arena, reduces cross-size fragmentation.

---

## Persistence

### RDB (Snapshot)

```redis
save 900 1    # 15min if ≥1 change
save 300 10   # 5min if ≥10
save 60 10000 # 1min if ≥10K
BGSAVE         # background fork + COW
```

### AOF (Append-Only File)

```redis
appendfsync everysec  # default (good balance)
appendfsync always    # safest, slowest
appendfsync no        # let OS decide
```

**AOF Rewrite:** Fork child → build new AOF from memory → parent appends buffered commands → atomic rename.

### Hybrid (Redis 4+)

```text
appendonly.aof = [RDB snapshot | AOF incremental commands]
Fast restart: load RDB, replay only incremental AOF.
```

---

## Replication (PSYNC2)

```text
REPLICAOF host port
  → PSYNC replid offset
    ├── Partial: CONTINUE (backlog has data) → send buffered cmds
    └── Full: FULLRESYNC new_replid offset
        → BGSAVE → send RDB → buffer writes → replica loads + catch up
```

**Backlog:** Circular buffer (`repl-backlog-size 64mb`). If replica offset in backlog → partial sync.

---

## Redis Cluster

```text
Nodes: A(0-5461), B(5462-10922), C(10923-16383)
         └── each has replica ──┘
         Gossip protocol (PING/PONG every 1s)
```

```python
def slot_for_key(key):
    if '{' in key and '}' in key:
        key = key[key.index('{')+1:key.index('}')]
    return crc16(key) & 16383  # 16384 slots
```

**Resharding:** MIGRATE keys → CLUSTER SETSLOT NODE. Client gets MOVED (cache permanently) or ASK (temporary redirect).

**Consistency:** No strong consistency. Async replication. Minority partition stops accepting writes.

---

## Sentinel

```text
Sentinels (3+) monitor master/replicas.
S1 marks master SDOWN (no PONG) → asks others → ODOWN → leader elected
→ picks replica with highest offset → REPLICAOF NO ONE → others follow

Config epoch prevents split-brain.
```

---

## Transactions & Lua

### MULTI/EXEC/WATCH

```redis
WATCH balance                        -- optimistic lock
MULTI                                -- queue commands
DECR balance 100
INCR other_account 100
EXEC                                 -- nil if WATCHed key changed
```

### Lua Scripting

```lua
-- Atomic transfer (runs on server, no network roundtrips)
local bal = redis.call('GET', KEYS[1])
if tonumber(bal) < tonumber(ARGV[1]) then
    return redis.error_reply('Insufficient funds')
end
redis.call('DECRBY', KEYS[1], ARGV[1])
redis.call('INCRBY', KEYS[2], ARGV[1])
```

```redis
EVAL "script" 2 from to amount
EVALSHA <sha1> 2 from to amount   -- cached script (SCRIPT FLUSH to clear)
```

---

## Modules

```redis
# RediSearch: full-text search
FT.CREATE idx ON HASH PREFIX 1 "product:" SCHEMA name TEXT
FT.SEARCH idx "@name:laptop @price:[500 1500]"

# RedisJSON: native JSON ops
JSON.SET doc $ '{"name":"Alice"}'
JSON.ARRAPPEND doc $.tags '"premium"'

# RedisBloom: probabilistic data structures
BF.ADD bloom "user:42"
BF.EXISTS bloom "user:42"

# RedisTimeSeries: time-series with downsampling
TS.CREATE sensor:temp RETENTION 86400000
TS.RANGE sensor:temp 1614556800 1614643200
```

---

## Simplest Mental Model

```
Redis is a toolbox where everything is a key:

1. STRING = sticky note (text, numbers, bits)
2. LIST = linked chain (queue, stack)
3. SET = bouncer's list (unique, fast membership)
4. SORTED SET = leaderboard (ordered by score)
5. HASH = mini filing cabinet (fields within a key)
6. STREAM = conveyor belt (event log, message queue)
7. All data lives in RAM (that's why it's fast)
8. Persistence = photo (RDB) + diary (AOF)
9. Cluster = multiple toolboxes sharing the work
10. Sentinel = friend watching the toolbox

"If you need to go to disk, you've already lost"
```


---

## Code Examples

```python
# Example implementation
# [Add language-specific code demonstrating core concept]
pass
```

---

## Common Failure Modes

**Problem**: [Key issue in production]

**Root cause**: [Why it happens]

**Solution**: [How to fix]

---

## Interview Questions

### Q1: [Core concept question]

**Answer**: [Detailed explanation with trade-offs]

### Q2: [Design/architecture question]

**Answer**: [Best practices and reasoning]
