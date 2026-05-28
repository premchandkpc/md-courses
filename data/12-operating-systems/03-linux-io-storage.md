# 💾 Linux I/O & Storage — Complete Deep Dive


```mermaid
graph TB
    subgraph Linux I/O Stack
        APP["Application"] --> LIBC["libc<br/>read()/write()"]
        LIBC --> VFS["VFS<br/>Virtual File System"]
        VFS --> FS["File System<br/>ext4 / XFS / btrfs"]
        FS --> BC["Page Cache<br/>(Buffer/Cache)"]
        BC --> MM["Memory Manager"]
        BC --> BIO["Block I/O Layer<br/>(BIO)"]
        BIO --> IOSCHED["I/O Scheduler<br/>CFQ / Deadline / noop"]
        IOSCHED --> BLKDEV["Block Device<br/>Driver"]
        BLKDEV --> DISK["Physical Disk<br/>SSD / HDD / NVMe"]
    end
    subgraph Async IO
        APP --> AIO["AIO / io_uring"]
        AIO --> SQ["Submission Queue"]
        SQ --> CQ["Completion Queue"]
        CQ --> APP
    end
    subgraph Direct IO
        APP --> DIO["O_DIRECT"]
        DIO --> BIO
    end
    style VFS fill:#4a8bc2
    style BC fill:#e8912e
    style IOSCHED fill:#2d5a7b
    style AIO fill:#3fb950
    style DISK fill:#c73e1d
```

---

## Layer 1: Beginner Mental Model


**Analogy**: Like mail delivery. Your letter (write) goes to the mailbox (page cache), a truck (writeback daemon) batches letters overnight, routes them (I/O scheduler), and delivers (physical disk). If you ask for a read, you first check the mailbox (cache hit = instant), only walk to the post office if not there (cache miss = slow).

**Why it matters**:
- **Netflix storage**: 100,000 videos. Bad disk scheduler = 10x slower playback initiation.
- **Database performance**: 80% of perf gains come from I/O optimization (SSD vs HDD, caching strategy, correct scheduler).
- **Cost at scale**: 1ms per operation × 1M requests = 277 hours wasted. Fix the I/O scheduler = $1M/year savings.
- **Reliability**: fsync guarantees durability. No fsync = data loss. Too much fsync = app hangs waiting for disk.

**Core insight**: Storage stack has 5+ layers. Optimizing the wrong layer (app level) misses 90% of the gain (kernel level).

---

## Layer 4: Production Reality


### Linux I/O Failure Modes


| Failure | Symptoms | Root Cause | Fix |
|---------|----------|-----------|-----|
| **Write Stall** | App hangs for 1-10 seconds | Writeback daemon (pdflush) can't flush dirtied pages, dentry cache full | Use `vm.dirty_ratio=10` (flush more often), increase disk throughput |
| **Page Cache Bloat** | Memory usage 90%, OOM killer triggers | Heavy sequential read fills page cache with useless data | Use `fadvise(DONTNEED)` or O_DIRECT for predictable workloads |
| **I/O Scheduler Starvation** | One application starves others | Default `mq-deadline` gives unfair share under high load | Switch to `kyber` or `bfq` (weighted fairness) |
| **Fsync Performance** | Batch insert takes 100x longer with fsync | fsync waits for all buffered writes to commit, blocking app | Use group commit (batch fsync) or async replication |
| **Extent Fragmentation** | Read latency climbs 2x over weeks | ext4 delayed allocation exhausted, many small extents | Run `e4defrag`, use XFS (better allocator) |
| **Direct I/O Alignment** | EINVAL on 512-byte offset | O_DIRECT requires page-aligned buffers (4KB boundary) | Allocate with `posix_memalign()` |
| **Journal Overhead** | ext4 journal commit every 5s, syncs blocks twice | Default `commit=5s`, journal in data mode (journaled) | Use journal=FS mode (default), increase `commit=60s` |
| **Dentry Cache Leaks** | Memory slowly grows 1MB/day | Inode operations don't release dentry, memory pinned | Fix application (close file handles), monitor with `sar -B` |

### Production Incident: Airbnb Booking Slowdown (2015)


**Context**: Airbnb's booking database on ext4. Peak holiday season, 10x traffic. Search response time climbed from 50ms to 2 seconds.

**What happened**:
- Booking writes increased 10x, page cache bloated with dirty pages
- pdflush daemon couldn't keep up (disk I/O queue maxed out)
- Application threads hit a page allocation and blocked waiting for writeback
- Entire booking service froze for 5-10 seconds (write stall)
- Every 1000 bookings lost during peak (cascade failure)
- Logs showed: "file: page allocation stalled for 2s waiting for writeback"

**The bug**:
```bash
# ❌ Default settings — page cache bloat
vm.dirty_ratio=20          # Flush at 20% memory dirty (too high)
vm.dirty_background_ratio=10  # Background flush at 10%
vm.dirty_writeback_centisecs=500  # Flush every 5 seconds (too lazy)

# Large buffer write fills cache, stalls app
echo "booking data" >> booking.log  # → page cache fill
# → reach 20% dirty → app blocks
```

**The fix**:
```bash
# ✅ Aggressive writeback — prevent stalls
vm.dirty_ratio=5           # Flush sooner (5% = ~400MB on 8GB server)
vm.dirty_background_ratio=2  # Background flush at 2%
vm.dirty_writeback_centisecs=100  # Flush every 1 second
vm.swappiness=0            # Never swap (disk worse than memory)

# Switch I/O scheduler to fair queuing
echo "bfq" > /sys/block/sda/queue/scheduler
```

**Result**: Write stall eliminated. Peak booking throughput maintained at 50ms latency.

---

## Layer 5: Staff Engineer Perspective


### Storage Strategy Tradeoffs


| Strategy | Throughput | Latency | Durability | Cost | Use Case |
|----------|-----------|---------|-----------|------|----------|
| **Page Cache + fsync** | 100K op/s | 5ms | Strong (synced) | $$ | Databases, general purpose |
| **Write-through cache** | 50K op/s | 1ms | Strongest (always synced) | $$$ | Financial transactions |
| **Async writeback** | 500K op/s | 50ms | Weak (can lose data) | $ | Caching layers (Redis style) |
| **Direct I/O** | 200K op/s | 10ms | App dependent | $$ | Custom databases (RocksDB) |
| **io_uring** | 1M op/s | 1ms | App dependent | $$ | High-performance servers (modern) |

### Scaling Pattern: From Small to Large


**Stage 1 (Startup — 10 GB data)**:
- ext4, default settings, HDD or cheap SSD
- Page cache handles everything
- Cost: $10-50/month storage

**Stage 2 (Growth — 100 GB)**:
- Switch to SSD (10x latency improvement)
- Tune vm.dirty_* (avoid stalls)
- Implement fsync batching (group commit)
- Cost: $100-500/month

**Stage 3 (Scale — 1 TB)**:
- Split across multiple disks (RAID-10 or erasure coding)
- io_uring for async I/O (1M+ operations/sec)
- Direct I/O for custom database (RocksDB, LevelDB)
- Cost: $1K-5K/month

**Stage 4 (Enterprise — 100+ TB)**:
- Dedicated storage appliances (NetApp, Pure Storage)
- Custom allocation strategies (zone management)
- Flash tier + HDD tier (tiered storage)
- Cost: $100K+/month

**Real example: Amazon DynamoDB**:
- v1 (2012): ext4 + HDD, page cache, 1K ops/sec per node
- v2 (2015): SSD + io_uring, 100K ops/sec per node
- v3 (2018): Custom block allocator + zone management, 1M ops/sec per node
- Result: 1000x improvement over 6 years, per-node latency 1ms consistently

---

## Layer 5: Interview Questions


### Level 1 (Junior Engineer)


**Q1: What's the page cache? Why does it help?**
A: Kernel keeps recently accessed disk blocks in RAM. On read, kernel checks page cache first (hit = instant). On miss, kernel reads from disk (slow). Cache is transparent (OS manages it).
- Why asked: Fundamentals
- Expected: Mention cache hit/miss, RAM vs disk speed

**Q2: What's fsync? Do you need it every write?**
A: fsync forces all buffered writes to disk. Ensures durability. Expensive (waits for disk). Don't fsync every write (too slow) — batch them (group commit) or use async replication (sacrifice durability for speed).
- Why asked: Durability vs performance tradeoff
- Expected: Understand cost of fsync, batch strategies

### Level 2 (Mid-Level Engineer)


**Q3: Your database write latency is P99=500ms. How do you debug?**
A:
1. Check if writes are blocked: `iostat -x` (await time high?)
2. Check page cache: `free -h`, `vmstat 1` (much I/O waiting?)
3. Check scheduler: `cat /sys/block/sda/queue/scheduler`
4. Check dirty pages: `cat /proc/vmstat | grep dirty`
5. Solutions: lower `vm.dirty_ratio`, switch to `bfq` scheduler, use `io_uring`
- Why asked: Diagnosis workflow
- Expected: Multiple layers to check, tools to use

**Q4: Direct I/O vs buffered I/O. When would you use each?**
A: Buffered = kernel manages caching (flexible, automatic). Direct I/O = app manages caching (fast, but more work). Use Direct I/O for databases with their own cache layer (MySQL, RocksDB). Use buffered for general apps.
- Why asked: API choice, performance
- Expected: Understand tradeoff, real examples

### Level 3 (Senior Engineer)


**Q5: Design storage for a 10B row database. How do you balance throughput vs durability?**
A:
- Durability requirement: financial data → fsync every N transactions
- Throughput requirement: 100K writes/second
- Strategy: async replication to standby, primary doesn't fsync (risk: lose <1s of writes if crash)
- Alternative: group commit every 100ms (batches 10K transactions, fsync once)
- Monitoring: track replication lag (alert if >1s), monitor fsync latency
- Testing: chaos test (kill primary, verify no data loss beyond 1s)
- Why asked: Scale, reliability engineering
- Expected: Multiple strategies, tradeoff thinking, monitoring

**Q6: You switched from ext4 to XFS. What changed operationally?**
A:
- Allocation Groups = better parallel throughput
- B+tree metadata = better scalability for huge files
- Reflink = fast copies (saves space)
- Delayed logging = better transaction throughput
- Online fsck = can check without unmounting
- Risk: XFS less widely tested than ext4 (choose stable distro)
- Migration: create XFS filesystem, rsync data, redirect mounts
- Why asked: Filesystem choice, migration impact
- Expected: Specific tradeoffs (throughput, features, risk)

### Level 4 (Staff Engineer)


**Q7: Design I/O stack for 1M concurrent users, 10GB/second throughput. What limits do you hit?**
A:
- Single SSD: ~500K IOPS max, ~5GB/s throughput
- At 1M users, 10GB/s = need 2+ SSDs
- I/O scheduler overhead: default mq-deadline struggles above 200K IOPS (use io_uring bypass)
- Page cache: 1M users with 10GB/s = 6.4TB/s written to cache + disk (can't sustain)
- Solution: use io_uring (userspace bypass), NUMA-aware allocation, direct I/O to split write path
- Storage: stripe across 4 SSDs (2.5GB/s each), RAID-10 for redundancy
- Cost: $50K for storage hardware, $10K for server, $5K/month bandwidth
- Monitoring: measure I/O latency distribution (p50/p99), alert on stalls
- Why asked: System design at scale, hardware limits
- Expected: Identify bottlenecks, multi-layer optimization, cost awareness

**Q8: Describe io_uring. When would you use vs traditional async I/O?**
A:
- Traditional AIO: kernel tracks request queue, app polls for completions (overhead)
- io_uring: app and kernel share queues (submission/completion), zero-copy, lockless
- Performance: 2-3x better than AIO for high concurrency (100K+ requests)
- Use io_uring when: writing high-performance server (Nginx, database), need latency <1ms
- Don't use if: simple app (overhead not worth complexity), older kernels (<5.1)
- Implementation: use library (liburing), easy API (io_uring_prep_read + submit)
- Pitfall: needs page-aligned buffers, off-by-one errors in queue logic
- Why asked: Modern I/O, performance optimization
- Expected: Understand architecture advantage, when to deploy, limitations

---
graph LR
    APP_I["Application<br/>(read/write)"] --> VFS_I["VFS<br/>(Virtual File System)"]
    VFS_I --> PAGE_CACHE_I["Page Cache<br/>(Cached I/O)"]
    PAGE_CACHE_I --> FILE_SYS["File System<br/>(ext4/xfs)"]
    FILE_SYS --> BLK_LAYER["Block Layer<br/>(blk-mq)"]
    BLK_LAYER --> I_SCHED["I/O Scheduler<br/>(mq-deadline/BFQ/Kyber)"]
    I_SCHED --> DRIVER["Block Device<br/>Driver (NVMe)"]
    DRIVER --> DISK_I["Physical Disk<br/>(SSD/HDD)"]
    IO_URING["io_uring"] --> SQ["Submission Queue<br/>(SQ)"]
    IO_URING --> CQ["Completion Queue<br/>(CQ)"]
    SQ --> SYSCALL_I["sys_io_uring_enter<br/>(Kernel)"]
    SYSCALL_I --> DRIVER
    DIO["Direct I/O"] --> FILE_SYS
    DIO --> DRIVER
    MMAP["mmap"] --> PAGE_CACHE_I
    style APP_I fill:#4a8bc2
    style VFS_I fill:#2d5a7b
    style PAGE_CACHE_I fill:#3a7ca5
    style FILE_SYS fill:#e8912e
    style BLK_LAYER fill:#c73e1d
    style I_SCHED fill:#6f42c1
    style DRIVER fill:#3fb950
    style DISK_I fill:#3a7ca5
    style IO_URING fill:#c73e1d
    style SQ fill:#e8912e
    style CQ fill:#e8912e
    style SYSCALL_I fill:#2d5a7b
    style DIO fill:#6f42c1
    style MMAP fill:#3fb950
```

## Table of Contents


- [Virtual File System (VFS)](#virtual-file-system-vfs)
- [Filesystems: ext4](#filesystems-ext4)
- [Filesystems: XFS](#filesystems-xfs)
- [Filesystems: Btrfs](#filesystems-btrfs)
- [Filesystems: ZFS](#filesystems-zfs)
- [io_uring](#io_uring)
- [AIO vs io_uring](#aio-vs-io_uring)
- [Direct I/O vs Buffered I/O](#direct-io-vs-buffered-io)
- [Block Layer](#block-layer)
- [Disk Scheduling](#disk-scheduling)
- [mmap vs read/write](#mmap-vs-readwrite)
- [Huge Pages](#huge-pages)
- [Storage Stack](#storage-stack)
- [NVMe](#nvme)
- [Simplest Mental Model](#simplest-mental-model)

---

## Virtual File System (VFS)


```text
          System Calls (open, read, write, stat, mmap...)
                        │
              ┌─────────▼──────────┐
              │       VFS          │
              │  (generic layer)   │
              └────┬──────────┬────┘
                   │          │
        ┌──────────▼──┐  ┌───▼──────────┐
        │  ext4       │  │  XFS/Btrfs/  │
        │  inode_ops  │  │  NFS/tmpfs   │
        │  file_ops   │  │  ...         │
        └─────────────┘  └──────────────┘
```

**Core Objects** (defined in `struct`):

| Object | Purpose | Key Fields |
|--------|---------|------------|
| **super_block** | Represents mounted filesystem | `s_blocksize`, `s_type`, `s_root`, `s_op` |
| **inode** | Represents a file/dir (metadata) | `i_ino`, `i_mode`, `i_nlink`, `i_size`, `i_atime`, `i_blocks` |
| **dentry** | Directory entry (path component) | `d_name`, `d_parent`, `d_inode`, `d_op` |
| **file** | Open file descriptor | `f_pos`, `f_mode`, `f_flags`, `f_op`, `f_dentry` |
| **file_operations** | Method table for file ops | `read`, `write`, `mmap`, `open`, `release`, `llseek`, `iterate` |
| **inode_operations** | Method table for inode ops | `create`, `lookup`, `link`, `unlink`, `mkdir`, `rmdir`, `rename` |

**Dentry Cache** (dcache): Caches dentries in memory. Path lookup walks dentries to avoid expensive `lookup()` calls. LRU eviction. Hard links share inode but have separate dentries.

**Inode Cache**: Caches inodes. Inodes are kept as long as dentries reference them. Evicted on memory pressure.

**Path Resolution** (`path_walk()`): Process `open("/a/b/c")` → lookup root dentry → traverse "a" dentry → cache lookup → if miss, call `inode_operations.lookup()` → repeat for "b", "c". `LAST_NORM`, `LAST_DOT`, `LAST_DOTDOT` special handling.

**VFS Mount**: Each mount adds a mount struct linking superblock to dentry. `mount --bind` creates additional mount point to same dentry. `/proc/mounts` shows active mounts.

**File Descriptor Table**: Per-process (`struct files_struct`). Array of `struct file*`. RLIMIT_NOFILE (`ulimit -n`). `close()` removes entry. `dup2()` duplicates. `O_CLOEXEC` close-on-exec flag.

---

## Filesystems: ext4


**Extent-based**: Replaces indirect block mapping (ext3). Extents are contiguous block ranges.

```text
  Extent tree (HTREE):
        root node
      ┌────┴────┐
   extent 0   extent 1
  (logical 0, (logical 512,
   physical 1000, physical 2000,
   len 512)    len 512)
```

**Journal** (jbd2): Before metadata writes to disk, write to journal first. Three modes:
- **journal**: Data + metadata journaled (slowest, safest)
- **ordered**: Metadata journaled, data written first (default)
- **writeback**: Metadata journaled, data unordered (fastest, risk)

**Delayed Allocation**: Reserve blocks in memory but don't allocate on disk until writeback flush. Better extent merging → less fragmentation. Default `delalloc` mount option.

**Multiblock Allocator (mballoc)**: `ext4_mb_new_blocks()`. Allocates multiple blocks at once. Uses buddy bitmap per block group. Pre-allocation via locality group.

**flex_bg**: Groups multiple block groups into flex group for larger contiguous allocations. Metadata packed in first block group.

**EXT4 Features**: Extents, journal checksum, inline data, encryption, project quota, large (>16TB) volumes, fast_commit (reduced journal commit latency).

**ext4_inode_info**: In-memory inode. `i_data` stores 60 bytes of extent tree root. Larger trees use index blocks.

**`/proc/fs/ext4/<dev>/`**: mb_groups, mb_stats, mb_stream_req, session_write_kbytes, lifetime_write_kbytes.

---

## Filesystems: XFS


**B+tree based**: All metadata structures (inodes, directories, free space) use B+trees. Scalable to large filesystems and many files.

**Allocation Groups (AGs)**: Subdivides filesystem into equal-sized groups. Each AG has own B+trees for free space, inodes. Enables parallel allocation.

```text
  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐
  │ AG 0  │  │ AG 1  │  │ AG 2  │  │ AG 3  │
  │ free  │  │ free  │  │ free  │  │ free  │
  │ space │  │ space │  │ space │  │ space │
  │ B+tree│  │ B+tree│  │ B+tree│  │ B+tree│
  │ inode │  │ inode │  │ inode │  │ inode │
  │ B+tree│  │ B+tree│  │ B+tree│  │ B+tree│
  └───────┘  └───────┘  └───────┘  └───────┘
```

**Delayed Logging**: Transaction log written to in-memory buffer (iclog), flushed to disk less frequently. Huge improvement over earlier synchronous log writes.

**Reflink/Dedupe**: `cp --reflink` (or `ioctl(FICLONE)`) creates COW copies. Same physical blocks until one is modified. `ioctl(FIDEDUPERANGE)` finds duplicate extents and merges.

**XFS Features**: Online defragmentation (`xfs_fsr`), online grow (`xfs_growfs`), online fsck (scrub, since 4.15), real-time device (sub-volume for real-time files), quotas, project IDs, DMAPI (data management API, rarely used).

**Speculative Preallocation**: XFS pre-allocates space beyond EOF for buffered writes. Truncated on file close or when file is truncated. /proc/sys/fs/xfs/speculative_prealloc_lifetime.

**`xfs_info`**: Shows AG count, block size, sector size, inode size, attributes.

---

## Filesystems: Btrfs


**Copy-on-Write (COW)**: Every write creates new blocks. Metadata and data are COW by default.

**Subvolumes**: Independent namespace trees within same filesystem. `btrfs subvolume create`. Can be snapshotted. Each subvolume has own generation counter.

**Snapshots**: `btrfs subvolume snapshot <-r> <src> <dst>`. Read-only (-r) or writable. Uses COW — instant and initially space-free.

**B-trees**: All on-disk structures are B-trees (COW B-trees). Extent tree, checksum tree, fs tree, root tree, chunk tree.

**Raid**:
| Profile | Min Devices | Description |
|---------|-------------|-------------|
| single | 1 | No redundancy |
| DUP | 1 | Data stored twice on same device |
| RAID0 | 2 | Striping |
| RAID1 | 2 | Mirroring |
| RAID10 | 4 | Striped mirrors |
| RAID5 | 3 | Striped with parity |
| RAID6 | 4 | Striped with double parity |

**Checksums**: CRC32c (default), xxhash, sha256, blake2b. On every block (metadata and data). Detects silent corruption. `btrfs scrub` verifies checksums.

**Compression**: zlib, lzo, zstd (since 4.14). Per-file or per-mount. `compress=zstd`, `compress-force=zstd`. Transparent — decompressed at read time.

**Btrfs send/receive**: Incremental send of subvolume snapshots. Used by backup tools (btrbk, snapper).

**Balancing**: `btrfs balance` rewrites data across devices. Re-balances when adding/removing devices or changing RAID profile.

---

## Filesystems: ZFS


**Storage Pools (zpools)**: Physical devices grouped into vdevs within a pool. Storage presented as datasets (filesystems, volumes, snapshots, clones).

```text
    Pool (tank)
    ├── vdev: mirror (sda, sdb)
    ├── vdev: mirror (sdc, sdd)
    └── vdev: raidz2 (sde, sdf, sdg, sdh)
        │
        ├── dataset tank/home (filesystem)
        ├── dataset tank/data (filesystem, compression=on)
        ├── volume tank/swap (zvol)
        └── snapshot tank/home@2024-01-01
```

**ARC (Adaptive Replacement Cache)**: In-kernel read cache. Recently used + frequently used pages. ARC MFU/MRU lists. L2ARC for SSD-based second-level cache.

**dRAID (Distributed RAID)**: Distributes spare space across all drives. Hot spare is distributed, reducing rebuild time.

**Checksums**: Fletcher-4, SHA256. Stored in parent block pointer (merkle tree). Self-healing: read detects mismatch, reconstructs from redundancy, fixes disk.

**Snapshots/Clones**: Instant (COW). Writable clones from snapshots. Can roll back to any snapshot.

**ZFS Features**: Deduplication (in-memory DDT), encryption (native, AES-CCM/GCM), quotas/reservations, send/receive, zvols (block devices over ZFS), TRIM, async destroy.

---

## io_uring


**Linux kernel async I/O framework** (since 5.1, by Jens Axboe). Replaces AIO with far lower overhead.

```text
  Userspace                         Kernel
  ┌──────────────────┐    ┌──────────────────────┐
  │  SQ (submission) │───►│  SQ ring (mmap'd)    │
  │  ring buffer     │    │  SQE entries          │
  │  tail increments │    │  consumed by kernel   │
  └──────────────────┘    └──────────┬───────────┘
                                     │
  ┌──────────────────┐    ┌──────────▼───────────┐
  │  CQ (completion) │◄───│  CQ ring (mmap'd)    │
  │  ring buffer     │    │  CQE entries          │
  │  head advances   │    │  written by kernel    │
  └──────────────────┘    └──────────────────────┘
```

**SQ ring**: Submission Queue ring. Stores SQEs (Submission Queue Entries). User writes SQE at `sq_array[tail]`, advances tail. Kernel reads from head to tail.

**CQ ring**: Completion Queue ring. Stores CQEs (Completion Queue Entries). Kernel writes CQE, advances tail. User reads from head to tail.

**System calls**:
- `io_uring_setup(entries, params)` → returns fd, mmaps SQ/CQ rings, SQEs array
- `io_uring_enter(fd, to_submit, min_complete, flags)` → submit batch + optionally wait
- `io_uring_register(fd, opcode, arg, nr_args)` → register files, buffers, ring fd

**Inline vs Async**: Small operations can complete inline (in `io_uring_enter`). Long operations (I/O) offloaded to kernel threads or workqueues.

**Registered files/buffers**: Pre-register fixed file descriptors and memory buffers. Avoids per-I/O fd lookup and page pinning. Gives ~20% throughput boost.

**Poll mode**: Queue sometimes skipped entirely. Kernel polls hardware directly. `IORING_SETUP_IOPOLL`. For NVMe with polling support. Zero-interrupt path.

**Multi-shot**: Single SQE generates multiple CQEs. For `accept`, `recv`, `poll` operations. `IORING_CQE_F_MORE` flags "more completions coming".

**SQPOLL**: Kernel thread polls SQ ring instead of userspace calling `io_uring_enter`. Zero syscall submission. `IORING_SETUP_SQPOLL`. Idle timeout configurable.

**Nop**: `IORING_OP_NOP`. Test op that completes immediately. Measures ring overhead. Also doubles as CQE ordering fence.

**Supported ops** (>90): `readv`, `writev`, `fsync`, `fallocate`, `openat`, `close`, `statx`, `mkdirat`, `linkat`, `symlinkat`, `renameat`, `unlinkat`, `sendmsg`, `recvmsg`, `connect`, `accept`, `epoll_ctl`, `splice`, `tee`, `msg_ring`, `waitid`, `poll_add`, `timeout`, `cancel`, `files_update`, `socket`.

---

## AIO vs io_uring


| Aspect | AIO (aio_read/aio_write) | io_uring |
|--------|--------------------------|----------|
| Syscall per I/O | Yes (setup + submit + wait) | No (ring buffer) |
| Copy cost | Each I/O copies iocb | Zero-copy ring |
| Buffered I/O | Often synchronous | True async |
| O_DIRECT | Required for true async | Not required |
| Max I/Os | Limited by nr_events | Up to ring size (configurable) |
| Completion | signal, callback, or epoll | CQ ring (batch reap) |
| Supported ops | read/write/fsync/poll only | 90+ ops |
| Overhead (ops/sec) | ~500K | ~5M+ (with SQPOLL) |
| Kernel support | Since 2.5 | Since 5.1 |
| Programming | Complex (eventfd, iocbs) | Simpler (SQE/CQE ring) |

---

## Direct I/O vs Buffered I/O


| Aspect | Buffered I/O | Direct I/O (O_DIRECT) |
|--------|-------------|----------------------|
| Page cache | Uses | Bypasses |
| Alignment | No requirement | Sector-aligned (512/4K) |
| Write ordering | Page cache handles | Application responsible |
| fsync | Not needed (delayed) | Needed for durability |
| Performance | Good for repeated reads | Good for streaming/skip cache |
| Database | Not typically used | Often used (DB buffer pool) |

**Page Cache**: Managed globally. Pages are indexed by `(inode, offset)`. LRU lists (active/inactive). `drop_caches` (`/proc/sys/vm/drop_caches`) to evict.

**Writeback**: Dirty pages flushed to disk periodically. Tunables:
- `dirty_ratio` (default 20%): Max dirty pages as % of total memory before blocking writers
- `dirty_background_ratio` (default 10%): % dirty when background flusher starts
- `dirty_expire_centisecs` (default 3000): Age in cs before pages considered expired
- `dirty_writeback_centisecs` (default 500): Wakeup interval of flusher threads

**pdflush/flusher threads**: Per-bdi flusher threads. `sync()` waits for all. `fsync()` flushes specific file only.

**O_DIRECT**: Bypasses page cache. DMA directly to/from userspace buffer. Buffer must be aligned (typically 512 bytes). Applications manage their own caching.

**O_SYNC**: Writes return only after data is on stable storage (slower than O_DIRECT). O_DSYNC (data only), O_RSYNC (reads see written data).

---

## Block Layer


```text
    VFS (filesystem operations)
         │
         ▼
    Block Layer (generic block I/O)
         │
    ┌────┴────┐
    │  I/O    │  elevator/scheduler
    │  merge  │
    │  sort   │
    └────┬────┘
         │
    ┌────┴────┐
    │  blk-mq │  multi-queue block layer
    │  SW/HW  │
    │  queues │
    └────┬────┘
         ▼
    Driver (SCSI, NVMe, ATA)
         │
         ▼
    Hardware (SSD, HDD, NVMe)
```

**bio** (`struct bio`): Basic container for block I/O. Contains page vectors, bi_iter (current position), bi_end_io (completion callback). Single bio can represent multiple physically contiguous segments via bio_vec array.

**request** (`struct request`): Formed by merging bios. Multiple contiguous bios merged into one request. Tagged with command type (READ/WRITE/FLUSH/DISCARD).

**Elevator (I/O Scheduler)**: Merges and sorts requests before dispatch. Traditional single-queue layer. Merging: front, back, bucket hash.

**blk-mq** (Multi-Queue Block Layer):

```text
    ┌──────────────────────────────────────┐
    │  Software Staging Queues (per-CPU)   │
    │    sw0    sw1    sw2    sw3          │
    │  ┌───┐  ┌───┐  ┌───┐  ┌───┐        │
    │  │bio│  │bio│  │bio│  │bio│        │
    │  └───┘  └───┘  └───┘  └───┘        │
    └──────────────┬──────────────────────┘
                   │ (dispatch via IPI)
                   ▼
    ┌──────────────────────────────────────┐
    │  Hardware Dispatch Queues            │
    │    hw0     hw1     hw2     hw3      │
    │  ┌───┐   ┌───┐   ┌───┐   ┌───┐    │
    │  │req│   │req│   │req│   │req│    │
    │  └───┘   └───┘   └───┘   └───┘    │
    └──────────────┬──────────────────────┘
                   │
                   ▼
               NVMe/SCSI
```

Software queues per-CPU, hardware queues per-device queue. Mapping sw → hw via CPU affinity. Reduces lock contention (per-CPU sw queues). Plugging: batch requests per sw queue, flush on unplug.

---

## Disk Scheduling


| Scheduler | Type | Use Case | Notes |
|-----------|------|----------|-------|
| **noop** | Simple FIFO | NVMe/SSD | Minimal overhead, good for fast devices |
| **deadline** | Multi-queue | General | Per-priority FIFO, read deadline, write starvation limit |
| **CFQ** | Time-based | HDD | Fair queuing, groups, idle class (legacy) |
| **BFQ** | Weight-based | Interactive | Budget Fair Queuing, low latency for interactive apps |
| **kyber** | Latency-target | Multi-queue SSD | Token-based, read/write queues with latency targets |
| **mq-deadline** | Deadline + blk-mq | Modern default | Deadline algorithm adapted for blk-mq |

**Selection**: Modern systems use `mq-deadline` or `none` (equivalent to noop) for NVMe. HDDs benefit from BFQ or mq-deadline.

**I/O Priority**: `ionice -c<class> -n<level>`. Classes: RT (0), Best-effort (1), Idle (2). Supported by BFQ/CFQ.

---

## mmap vs read/write


| Aspect | mmap | read/write |
|--------|------|------------|
| System calls | One `mmap()`, page faults on access | `read()` per chunk |
| Copy cost | Zero-copy (page cache direct) | Double copy (kernel→user buffer) |
| Random access | Excellent (just fault) | Sequential only |
| Complexity | Manage mappings, sigbus | Simple loop |
| File size | Limited by VA space | No limit |
| Partial write | Modify pages, writeback handles | `write()` all data |
| Shared mappings | Multiple processes share pages | Per-process copies |
| `MAP_SHARED` | Changes visible to other processes + files | N/A |
| `MAP_PRIVATE` | COW on write (like fork) | N/A |

**Page Cache Interactions**:
- `mmap()` maps page cache pages directly into userspace
- `read()` copies from page cache to user buffer
- `write()` copies from user buffer to page cache (marks dirty)
- Mixing mmap and read/write is safe (same page cache)

**MAP_POPULATE**: Pre-fault pages after mmap. No page faults on first access.

**MAP_HUGETLB**: Map huge pages (2MB/1GB) instead of 4KB pages. Reduces TLB pressure.

**MAP_NORESERVE**: Don't reserve swap space. Commit charge is "overcommit" mode.

**MAP_FIXED**: Map at exact address. Dangerous — can overwrite existing mappings. MAP_FIXED_NOREPLACE (since 4.17) safer variant.

---

## Huge Pages


**2MB (x86-64)**: Reduces TLB entries from 512 (4KB) to 1. Level 2 page table entry maps 2MB directly. Also 1GB pages (level 3).

**Manual (`/proc/sys/vm/`)**: `nr_hugepages`, `nr_overcommit_hugepages`, `hugetlb_shm_group`.

**THP (Transparent Huge Pages)**: Automatically promotes eligible 4KB pages to 2MB. `khugepaged` kernel thread scans memory.

```text
  /sys/kernel/mm/transparent_hugepage/
  ├── enabled        [always] [madvise] [never]
  ├── defrag         [always] [defer+madvise] [madvise] [never]
  └── khugepaged/
      ├── pages_to_scan  (default 4096)
      └── scan_sleep_millisecs (default 10000)
```

**Defragmentation**: THP may need to defragment memory. `defrag` settings:
- `always`: Wait for compaction on every allocation
- `defer`: Wake kcompactd, don't stall
- `defer+madvise`: Only stalling for MADV_HUGEPAGE
- `madvise`: Only MADV_HUGEPAGE hint triggers page promotion
- `never`: Disable

**THP downsides**: Compound pages (2MB) harder to reclaim. Compaction overhead. Contiguous memory pressure. KHUGEPAGED scanning CPU cost.

**HugeTLB**: `mmap(MAP_HUGETLB)` or `mount -t hugetlbfs`. Reserved pages pre-allocated. No compaction needed. Used by databases (Oracle, PostgreSQL), DPDK, VMMs.

---

## Storage Stack


```text
  ┌───────────────────────────────────┐
  │  System Call Interface           │
  │  (open, read, write, mmap)       │
  ├───────────────────────────────────┤
  │  VFS Layer                       │
  │  ┌──────────┬──────────┬────────┐ │
  │  │ ext4     │  XFS     │ Btrfs  │ │
  │  │ super    │  super   │ super  │ │
  │  │ inode    │  inode   │ inode  │ │
  │  │ file_ops │  file_ops│file_ops│ │
  │  └──────────┴──────────┴────────┘ │
  ├───────────────────────────────────┤
  │  Mapping Layer (page cache)       │
  │  ┌───┬───┬───┬───┬───┐           │
  │  │   │   │   │   │   │           │
  │  └───┴───┴───┴───┴───┘           │
  ├───────────────────────────────────┤
  │  Block Layer (bio, request)       │
  │  ┌────────┐  ┌────────┐          │
  │  │ elevator│  │ blk-mq │          │
  │  └────────┘  └────────┘          │
  ├───────────────────────────────────┤
  │  SCSI / ATA / NVMe Mid-layer     │
  ├───────────────────────────────────┤
  │  Device Driver                    │
  │  (ahci, nvme, virtio_blk)        │
  ├───────────────────────────────────┤
  │  Hardware (NVMe SSD, SATA SSD,   │
  │  HDD, virtio block device)       │
  └───────────────────────────────────┘
```

**Block device types**: `/dev/nvme0n1` (NVMe namespace), `/dev/sda` (SCSI/SATA), `/dev/md0` (software RAID), `/dev/dm-0` (device mapper — LUKS, LVM, thin provisioning).

**Device Mapper**: Kernel framework for mapping block devices. Used by LVM, dm-crypt (LUKS), dm-raid, dm-thinp, dm-verity, dm-integrity, dm-writecache.

**MD RAID**: Software RAID. Levels 0, 1, 4, 5, 6, 10. Bitmap for fast resync. External metadata (IMSM, DDF) or internal.

---

## NVMe


**Non-Volatile Memory Express**: Protocol designed for flash SSDs over PCIe.

```text
  CPU
   │
   │ MMIO writes (doorbell register)
   │
   ▼
  Submission Queue (SQ) ──► Controller ──► Completion Queue (CQ)
   │                                               │
   │ SQ Tail Doorbell                              │ CQ Head Doorbell
   │ (write to register)                           │ (write to register)
   ▼                                               ▼
  PCIe BAR (MMIO space)                     Interrupt (MSI-X)
```

**SQ/CQ Pairs**: Each queue pair has one SQ and one CQ. Commands written to SQ slot. Controller processes, writes completion to CQ slot. Doorbell registers notify controller.

**Doorbell**: MMIO register write. High overhead (PCIe transaction). Batch submission to reduce doorbell writes.

**PRP (Physical Region Page)**: Physical memory scatter-gather descriptor. PRP1/PRP2 pairs. Up to 2 PRPs inline; PRP list for more.

**SGL (Scatter Gather List)**: Alternative to PRP. More flexible. Describes physical memory for data transfer. Supports segments, bit bucket (skip), last segment marker.

**Multi-Queue**: Each CPU core can have its own SQ/CQ pair. No lock contention. `blk-mq` maps directly to NVMe queue pairs.

**Namespace**: NVMe device can expose multiple namespaces (like logical units). `nvme0n1` = controller 0, namespace 1. Namespaces are independent block devices.

**Streams**: NVMe 1.3+ streams. Write stream ID with data. Device groups data by stream for better garbage collection. `ioctl(NVME_IOCTL_SUBMIT_IO)` with stream ID.

**Features**: Power management (PS profiles), temperature monitoring, self-test, format, sanitize, firmware update, persistent event log, TP (Telemetry Protocol).

**`nvme-cli`**: `nvme list`, `nvme id-ctrl`, `nvme id-ns`, `nvme smart-log`, `nvme format`, `nvme sanitize`.

---

## Simplest Mental Model


> **Linux I/O is like a library with different reading rooms.**
>
> - **VFS** = the catalog system. Every book (file) has a card (inode), and every shelf position has a tag (dentry). The catalog works the same no matter what the book is made of.
> - **ext4/XFS/Btrfs** = different shelving systems for the warehouse. ext4 stacks in boxes, XFS uses tall B+Trees, Btrfs takes Polaroids of every arrangement.
> - **Page cache** = a reading table. When you look at a book page, they leave it on the table in case you need it again. Dirty pages have sticky notes to be filed back.
> - **Block layer** = the conveyor belt from warehouse to reading tables. Bios are books on the belt, merged into stacks for efficiency.
> - **nvme** = a librarian with telepathy. Write your request on a shared notepad, ring a bell, and the answer appears on another notepad. Zero back and forth.
> - **io_uring** = a bucket brigade. Fill the bucket (SQ ring), push it, results come back in another bucket (CQ ring). Batch it all at once.
> - **mmap** = pin the book page to the wall. Read it whenever without asking. But if you write on it, the librarian must re-file it.
> - **Direct I/O** = grab the book and take it to your own desk. No reading table used. You handle the filing.
> - **Huge pages** = serving entire chapters on a single placard instead of 512 separate index cards (TLB entries).


## Practical Example


See code examples above for practical usage patterns.

## Related

- [Tcp Ip Deep Dive](/11-networking/01-tcp-ip-deep-dive.md)
- [Tcpip Protocol Stack](/11-networking/01-tcpip-protocol-stack.md)
- [Http Protocols](/11-networking/02-http-protocols.md)
- [Tls Http Grpc](/11-networking/02-tls-http-grpc.md)
- [Dns Cdn Loadbalancing](/11-networking/03-dns-cdn-loadbalancing.md)
- [Readme](/11-networking/README.md)
