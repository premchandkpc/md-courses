# 🗄️ Relational Database Internals — Complete Deep Dive

## Table of Contents
1. [Storage Engines](#storage-engines)
2. [B+tree Internals](#btree-internals)
3. [LSM-tree Internals](#lsm-tree-internals)
4. [Indexing](#indexing)
5. [Transaction Management](#transaction-management)
6. [MVCC](#mvcc)
7. [Concurrency Control](#concurrency-control)
8. [Simplest Mental Model](#simplest-mental-model)

---

## Storage Engines

```text
┌────────────────────────────────────────────────────────────┐
│              Storage Engine Landscape                       │
├──────────┬───────────┬──────────────┬──────────────────────┤
│  B-tree  │  B+tree   │  LSM-tree    │  Heap + Hash         │
│  InnoDB  │  PG, MySQL│  RocksDB,    │  MySQL MEMORY        │
│  SQLite  │  Oracle   │  Cassandra   │  Heap tables         │
└──────────┴───────────┴──────────────┴──────────────────────┘
```

| Property | B+tree | LSM-tree | Hash |
|----------|--------|----------|------|
| Point read | O(log N) | O(K log N) | O(1) |
| Write | O(log N) | O(log N) amortized | O(1) |
| Write amplification | Low (1-3x) | High (10-40x) | None |

---

## B+tree Internals

### Page Structure (PostgreSQL 8KB pages)

```text
┌──────────────────────────────────┐
│  PageHeaderData (24B)           │
│  ItemIdData[] (4B each) ← down  │
│  ↓ free space ↑                 │
│  Items (tuples/index) → up      │
└──────────────────────────────────┘
```

### Internal vs Leaf Nodes

```text
            ┌──────────┐
            │  Root    │
            │ [5,20,50]│
            └────┬─────┘
         ┌───────┼───────┐
         ▼       ▼       ▼
    ┌────────┐ ┌────────┐ ┌────────┐
    │ Internal │ ......   │ internal│
    └────┬────┘           └────┬────┘
     ┌───┼───┐            ┌───┼───┐
     ▼   ▼   ▼            ▼   ▼   ▼
    ┌─┐ ┌─┐ ┌─┐          ┌─┐ ┌─┐ ┌─┐
    │L│ │L│ │L│  ...      │L│ │L│ │L│ ← leaf (data + sibling ptr)
    └─┘ └─┘ └─┘          └─┘ └─┘ └─┘
```

- Internal: key + child pointer, no data
- Leaf: key + TID, sibling links for range scan
- Fanout ~300-500 for 8KB with 20B keys
- Height = 1 + ceil(log_fanout(N)) → 5 levels for 1B rows

### Split/Merge

```python
def btree_insert(tree, key, value):
    leaf = find_leaf(tree.root, key)
    leaf.insert(key, value)
    if leaf.is_overflow():
        mid = len(leaf.keys) // 2
        new_leaf = LeafNode(keys=leaf.keys[mid:], values=leaf.values[mid:])
        leaf.keys, leaf.values = leaf.keys[:mid], leaf.values[:mid]
        tree.insert_into_parent(leaf, new_leaf.keys[0], new_leaf)

def btree_delete(tree, key):
    leaf = find_leaf(tree.root, key)
    leaf.delete(key)
    if leaf.is_underflow():
        if leaf.can_borrow_from(leaf.sibling):
            leaf.borrow_from(leaf.sibling)
        else:
            tree.merge_nodes(leaf, leaf.sibling)
```

### Buffer Pool

```python
class BufferPool:
    def __init__(self, pool_size=1000):
        self.pages = {}
        self.replacer = ClockReplacer(pool_size)

    def fetch_page(self, page_id):
        if page_id in self.pages:
            return self.pages[page_id]
        frame = self.evict_frame()
        page = self.read_from_disk(page_id)
        self.pages[page_id] = page
        return page
```

| Algorithm | Strategy | Used By |
|-----------|----------|---------|
| LRU | Evict least recently used | Simple (fails under scans) |
| CLOCK | Circular scan w/ reference bit | PostgreSQL |
| 2Q | Two queues: hot/warm | PG (archived) |
| ARC | Adaptive recency/frequency | ZFS, InnoDB |

---

## LSM-tree Internals

```text
Write Buffer → flush → L0 SST (overlapping keys)
                        │ compaction
                        ▼
                    L1 SST (sorted, non-overlapping)
                        │ compaction
                        ▼
                    L2 SST (10x larger)
```

- **Memtable**: In-memory sorted tree (Red-Black/SkipList)
- **SSTable**: Immutable on-disk sorted file + index + bloom filter
- **WAL**: Crash recovery for memtable
- **Compaction**: Background merge to bound reads

### Compaction Strategies

**Size-tiered (Cassandra):** N SSTables → compact → larger SST → next level. Triggers at file count threshold.

**Leveled (LevelDB/RocksDB):** L0 overlapping, L1+ non-overlapping, 10x size ratio per level. Write amp ~10-40x, better space amp.

### Bloom Filter

```python
class BloomFilter:
    def __init__(self, n, fpr=0.01):
        m = -n * math.log(fpr) / (math.log(2)**2)
        self.bits = bytearray(int(m))
        self.k = int(m / n * math.log(2))

    def add(self, key):
        for h in self.hashes:
            self.bits[h(key) % len(self.bits)] = 1

    def might_contain(self, key):
        return all(self.bits[h(key) % len(self.bits)] for h in self.hashes)
```

No false negatives, configurable false positive rate (~0.1-5%).

---

## Indexing

### Primary vs Secondary

- **Clustered** (InnoDB): Data stored in index order (table = index)
- **Heap** (PostgreSQL): Data stored separately, index points to TID

```sql
CREATE INDEX idx_multi ON users (last_name, first_name, dob);
-- Column order: equality cols first, then range, then sort

-- Partial: only index relevant subset
CREATE INDEX idx_active ON users (email) WHERE status = 'active';

-- Covering: avoid heap lookup
CREATE INDEX idx_cov ON orders (user_id) INCLUDE (total, status);

-- Functional
CREATE INDEX idx_lower ON users (LOWER(email));
```

| Index | Use Case |
|-------|----------|
| B-tree | Default: =, <, >, BETWEEN, IN, LIKE |
| GiST | Geometry, full-text, fuzzy |
| GIN | JSONB, arrays, full-text (contains) |
| BRIN | Correlated data, time-series (100-1000x smaller) |
| Hash | Equality only (O(1)) |

---

## Transaction Management

### ACID

- **Atomicity**: All-or-nothing via WAL + UNDO
- **Consistency**: Constraints + triggers
- **Isolation**: MVCC/locking prevent interference
- **Durability**: Committed data survives crashes

### Isolation Levels

```text
                    Dirty Read  Non-Repeatable  Phantom
READ UNCOMMITTED   Possible    Possible        Possible
READ COMMITTED     Safe        Possible        Possible
REPEATABLE READ    Safe        Safe            Possible (PG: Safe)
SERIALIZABLE       Safe        Safe            Safe
```

---

## MVCC

Each transaction sees the database as of its snapshot time. PostgreSQL tracks via XMIN/XMAX in tuple header:

```python
def is_visible(tuple, snapshot):
    if is_aborted(tuple.xmin): return False
    if tuple.xmin > snapshot.xmax: return False
    if tuple.xmin in snapshot.xip: return False
    if tuple.xmax == 0 or is_aborted(tuple.xmax): return True
    if tuple.xmax > snapshot.xmax: return True
    if tuple.xmax in snapshot.xip: return True
    if is_committed(tuple.xmax): return False
    return True
```

| Feature | PostgreSQL | MySQL (InnoDB) |
|---------|-----------|----------------|
| Old versions | In-page dead tuples | Undo logs |
| Cleanup | VACUUM | Purge thread |

---

## Concurrency Control

**2PL (Two-Phase Locking):** Growing phase (acquire locks) → shrinking phase (release). SS2PL: hold all locks until commit.

**OCC (Optimistic):** Read → Validate → Write. Abort on conflict.

**SSI (Serializable Snapshot Isolation):** Detects rw-conflict cycles between concurrent transactions, aborts one.

**Deadlock Detection:** Build wait-for graph, find cycles, abort youngest/lowest-cost transaction.

---

## Simplest Mental Model

```
A database is a fancy key-value store that:
1. ORGANIZES data in pages on disk (B+tree, LSM)
2. CACHES hot pages in memory (buffer pool)
3. FINDS rows fast (indexes)
4. PROTECTS writes (WAL)
5. GIVES each tx its own view (MVCC)
6. PREVENTS chaos w/ concurrent writes (locks/OCC)

B+tree = phone book sorted for lookup
MVCC   = git branches for each transaction
WAL    = black box recorder for writes
```
