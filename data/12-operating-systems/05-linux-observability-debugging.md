# 🔍 Linux Observability & Debugging — Complete Deep Dive

## Table of Contents
- [strace](#strace)
- [ltrace](#ltrace)
- [gdb](#gdb)
- [perf](#perf)
- [ftrace](#ftrace)
- [BPF Tools (bpftrace & BCC)](#bpf-tools-bpftrace--bcc)
- [eBPF Observability Internals](#ebpf-observability-internals)
- [/proc Filesystem Deep Dive](#proc-filesystem-deep-dive)
- [/sys Filesystem](#sys-filesystem)
- [sar/sysstat](#sarsysstat)
- [top/htop/atop/btm](#tophtop atopbtm)
- [lsof](#lsof)
- [valgrind](#valgrind)
- [Heap Analysis](#heap-analysis)
- [Hugepage & OOM Analysis](#hugepage--oom-analysis)
- [Coredump Analysis](#coredump-analysis)
- [Simplest Mental Model](#simplest-mental-model)

---

## strace

**Syscall tracer** — intercepts and records all system calls made by a process.

```bash
strace -p 1234                # attach to running PID
strace -f -o output.txt ls    # trace child forks, write to file
strace -e trace=open,read,write  # filter specific syscalls
strace -c ls                  # count/tally syscalls (summary)
strace -t -T ls               # timestamp (-t), syscall duration (-T)
strace -e trace=network       # network syscalls only
strace -e trace=process       # fork/exec/exit family
strace -e trace=desc          # file descriptor ops
strace -e trace=signal        # signal-related
strace -e trace=ipc           # IPC syscalls
strace -e trace=all           # all (default)
strace -y                     # show FD paths
strace -x                     # show non-ASCII strings in hex
strace -z                     # successful calls only
strace -Z                     # failed calls only
```

**Filter expressions**: `-e trace=!write` (all except write). `-e read=3` (show read data for fd 3). `-e write=all` (show write data for all fds).

**Common analysis**:
- Startup time: what files are opened during exec?
- Performance: which syscall takes longest? (`-T`)
- Failures: which syscalls return -1? (`-Z`)
- Hidden reads: why is the process reading from a file?

**Limitations**: ~10-100x slowdown (syscall overhead). Each syscall needs ptrace stop. Use `seccomp`-based filtering in newer strace (in-kernel filter, faster).

**`strace -k`**: Show stack trace at each syscall (expensive, requires DWARF).

**Output format**: `[pid]  syscall(args...)  =  return_value  (comment)  <duration>`

```
[pid 1234] write(1, "hello\n", 6) = 6 <0.000010>
```

---

## ltrace

**Library call tracer** — intercepts dynamic library calls (uses `LD_PRELOAD` or `ptrace`).

```bash
ltrace ls                    # trace library calls of ls
ltrace -e 'strlen*' ls       # filter: only strlen family
ltrace -e '!libc*' ls        # exclude libc calls
ltrace -S -p 1234            # trace both library and syscalls
ltrace -c ls                 # count library calls
ltrace -b ls                 # show signal arrival
```

**Use cases**: Find what `malloc()`/`free()` patterns a program uses. Find library functions called most often.

**Limitations**: Static binaries (musl) not supported. Inlined functions invisible. `-S` shows syscalls too (combines with strace output).

---

## gdb

**GNU Debugger** — full process introspection and control.

**Startup**:

```bash
gdb ./a.out                  # start program in debugger
gdb --args ./a.out --flag    # with arguments
gdb -p 1234                  # attach to PID
gdb ./core.1234              # analyze coredump
```

**Breakpoints**:

```gdb
break main                   # function breakpoint
break file.c:42              # line number
break *0x4004a0              # address breakpoint
break func if x == 5         # conditional
catch syscall write          # syscall catchpoint
catch signal SIGSEGV         # signal catchpoint
tbreak main                  # temporary (one-shot)
rbreak regex                 # regex match function names
```

**Watchpoints**:

```gdb
watch x                      # write watch (break on write to x)
rwatch x                     # read watch (break on read of x)
awatch x                     # access watch (read or write)
watch -l *0x7fff0000         # watch by address
```

**Navigation**:

```gdb
stepi / si                   # one instruction
nexti / ni                   # one instruction (skip calls)
step / s                     # step into function
next / n                     # step over function
finish / fin                 # run until current function returns
continue / c                 # continue execution
until line                   # run until line
reverse-stepi                # step backward (rr required)
```

**Inspection**:

```gdb
info registers               # all registers
info frame                   # current stack frame
info locals                  # local variables
info args                    # function arguments
info threads                 # all threads
info inferiors               # all processes
backtrace / bt               # stack trace
frame N                      # switch to frame N
list                         # source around current line
disassemble $pc              # disassemble around PC
x/10gx $rsp                  # examine memory (10 8-byte hex)
p/x $rax                     # print rax in hex
p *(struct foo *)0x7fff      # print struct at address
call func(42)                # call a function in inferior
```

**Reverse Debugging** (Mozilla rr): Record execution, replay backwards. `rr record ./a.out`, `rr replay`. Reverse-continue, reverse-step.

**Conditional breakpoint optimization**: `break foo if hits > 100` — hardware-assisted. But avoid expensive conditions in hot paths.

**Thread debugging**: `set scheduler-locking on` – only current thread runs during step.

---

## perf

**Linux Performance Events** — uses hardware PMU counters and kernel tracepoints.

```bash
# Counting
perf stat ls                      # count events for command
perf stat -e cycles,instructions,cache-misses,branches ls
perf stat -d ls                   # default + cache events
perf stat -I 1000 -e cycles -a    # per-second sampling (system-wide)

# Sampling
perf record ./a.out               # profile with default sampling
perf record -F 99 -g ./a.out      # 99 Hz, with callgraphs
perf record -e cache-misses -c 1000 -g ./a.out  # every 1000 misses
perf record -p 1234 --sleep 10    # attach to PID, 10 seconds

# Report
perf report                       # interactive TUI
perf report --stdio               # text output
perf report -g graph --sort=dso   # call graph, sorted by shared obj

# Top
perf top -p 1234                  # live profiling of PID
perf top -e cache-misses          # top by cache misses

# Probe
perf probe -x /lib/libc.so.6 --add 'malloc size'  # dynamic probe
perf record -e probe_libc:malloc -a               # record malloc calls

# Annotate
perf annotate --stdio             # annotated assembly with samples

# Trace
perf trace ls                     # strace-like but uses tracepoints (much faster)

# Script
perf script                       # dump raw sample data
```

**perf c2c**: False sharing detection. `perf c2c record ./a.out`, `perf c2c report`. Finds cacheline contention across CPUs.

**perf mem**: Memory access profiling. `perf mem record -a`, `perf mem report`. Shows loads/stores, latency, TLB misses.

**perf sched**: Scheduler profiling. `perf sched record`, `perf sched latency`, `perf sched timehist`. Shows wakeup latency, migration, runtime.

**perf kmem**: Kernel memory allocator profiling. `perf kmem record`, `perf kmem stat`. Slab allocation hot spots.

**perf lock**: Lock contention. `perf lock record`, `perf lock report`. Shows contended locks and hold times.

**perf ftrace**: Frontend to ftrace. `perf ftrace trace -T <function>`. Live function tracer output.

**PMU Counters**:

| Event | Meaning |
|-------|---------|
| `cycles` | CPU cycles (unhalted) |
| `instructions` | Retired instructions |
| `cache-references` | Last-level cache lookups |
| `cache-misses` | Last-level cache misses |
| `branches` | Retired branches |
| `branch-misses` | Mispredicted branches |
| `L1-dcache-load-misses` | L1 data cache misses |
| `stalled-cycles-frontend` | Frontend stalls (fetch/decode) |
| `stalled-cycles-backend` | Backend stalls (execution) |

**Sampling frequency**: `-F 99` avoids lockstep sampling (if workload is periodic at 100Hz). `-c 10000` samples every 10000 events.

**Call graph methods**: `-g fp` (frame pointer, needs `-fomit-frame-pointer`), `-g dwarf` (DWARF unwinding, slower), `-g lbr` (LBR, Intel Haswell+).

---

## ftrace

**Function tracer** — built into the kernel (`/sys/kernel/debug/tracing/`).

```bash
# Setup
mount -t tracefs none /sys/kernel/tracing   # or debugfs

# Enable function tracer
echo function > /sys/kernel/tracing/current_tracer
echo do_sys_open > /sys/kernel/tracing/set_ftrace_filter
cat /sys/kernel/tracing/trace               # read output

# function_graph tracer (shows calls + durations)
echo function_graph > /sys/kernel/tracing/current_tracer
echo funcgraph-proc > /sys/kernel/tracing/trace_options
echo 10 > /sys/kernel/tracing/max_graph_depth

# Trace specific PID only
echo 1234 > /sys/kernel/tracing/set_ftrace_pid

# Dynamic tracing with kprobe
echo 'p:myprobe do_sys_open dfd=%di filename=%si flags=%dx mode=cx' > /sys/kernel/tracing/kprobe_events
echo 'r:myretprobe do_sys_open $retval' > /sys/kernel/tracing/kprobe_events
echo 1 > /sys/kernel/tracing/events/kprobes/myprobe/enable

# trace_printk (kernel developer)
# printk(KERN_INFO "trace: %d\n", var) → read from trace buffer
```

**trace-cmd**: User-friendly wrapper:

```bash
trace-cmd record -p function -l do_sys_open ls
trace-cmd report
trace-cmd record -e sched:* -e irq:*    # tracepoints
trace-cmd stream -p function_graph      # live streaming
```

**trace_marker**: Userspace can write to `/sys/kernel/tracing/trace_marker` to add custom marks in trace output.

**set_ftrace_filter**: Glob patterns: `do_sys*`, `*open*`, `!*lock*`. Can also filter by module: `:*modname`.

**set_graph_function**: Only trace this function's call graph.

---

## BPF Tools (bpftrace & BCC)

### bpftrace

**One-liners**:

```bpftrace
# New processes
bpftrace -e 'tracepoint:syscalls:sys_enter_execve { printf("%s exec'd\n", comm); }'

# Files opened
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%s %s\n", comm, str(args->filename)); }'

# Block I/O latency
bpftrace -e 'kprobe:blk_account_io_start { @start[arg0] = nsecs; }
             kretprobe:blk_account_io_complete { $s = @start[arg0]; delete(@start[arg0]); @m = hist((nsecs - $s)/1000000); }'

# TCP connections
bpftrace -e 'kprobe:tcp_connect { printf("%s → %s:%d\n", comm, ntop2(args->sk->__sk_common.skc_daddr), args->sk->__sk_common.skc_dport); }'

# Page faults by process
bpftrace -e 'tracepoint:exceptions:page_fault_user { @[comm] = count(); }'

# OOM kills
bpftrace -e 'tracepoint:oom:mark_victim { printf("OOM killed %s (%d)\n", comm, pid); }'

# Stack trace on malloc > 1MB
bpftrace -e 'uprobe:/lib/x86_64-linux-gnu/libc.so.6:malloc /arg0 > 1000000/ { printf("%d %d bytes\n", pid, arg0); print(ustack()); }'
```

**Probes**:

| Probe Type | Syntax | Use |
|------------|--------|-----|
| `kprobe` | `kprobe:func_name` | Kernel function entry |
| `kretprobe` | `kretprobe:func_name` | Kernel function return |
| `tracepoint` | `tracepoint:system:event` | Static tracepoints |
| `uprobe` | `uprobe:/path/lib:func` | Userspace function entry |
| `uretprobe` | `uretprobe:/path/lib:func` | Userspace function return |
| `usdt` | `usdt:/path/bin:provider:probe` | USDT probes (DTrace-style) |
| `profile` | `profile:hz:99` | Timer-based sampling |
| `interval` | `interval:s:1` | Periodic output |

**Built-in variables**: `pid`, `tid`, `uid`, `comm`, `nsecs`, `kstack`, `ustack`, `args`, `arg0..argN`, `retval`, `curtask`.

**Maps**: `@name[key] = value`, `@name = count()`, `@name = hist(v)`, `@name = lhist(v, min, max, step)`. `delete(@name)`, `clear(@name)`, `print(@name)`.

### BCC (BPF Compiler Collection)

**Tools**:

| Tool | Function | Source |
|------|----------|--------|
| `execsnoop` | Trace new process creation | tracepoint/sys_enter_execve |
| `opensnoop` | Trace file opens | tracepoint/sys_enter_openat |
| `biolatency` | Block I/O latency distribution | tracepoint/block:block_rq_issue + block_rq_complete |
| `biotop` | Top block I/O processes | CPUN stack traces |
| `tcptop` | Top TCP connections by throughput | kprobe/tcp_sendmsg + tcp_cleanup_rbuf |
| `runqlat` | Run queue latency (scheduler delay) | tracepoint/sched:sched_wakeup + sched_switch |
| `offcputime` | Time spent off-CPU by stack trace | kprobe/finish_task_switch |
| `stackcount` | Count stack trace occurrences | kprobe/kretprobe/tracepoint |
| `criticalstat` | Atomic/preempt off time | tracepoint/preemptirq |
| `trace` | Custom trace (function arguments) | kprobe + printf |
| `argdist` | Argument value distribution | kprobe statistics |
| `profile` | CPU sampling profiler (like perf) | timer-based + stack trace |
| `cpudist` | CPU time distribution by process | sched_switch |
| `dcstat` | Directory cache hit rate | tracepoint/sys_enter_* |
| `xfsslower` | XFS operations > 1ms | kprobe/xfs_file_read + xfs_file_write |

### bpftrace vs BCC vs perf

| Tool | Language | Ease | Granularity | Overhead |
|------|----------|------|-------------|----------|
| bpftrace | awk-like | Easy | Tracepoint/kprobe/uprobe | Low |
| BCC | Python+C | Medium | Full BPF programs | Low |
| perf | CLI | Medium | PMU + tracepoints | Low-Medium |

---

## eBPF Observability Internals

**bpf_trace_printk()**: Simple debug output. Writes to `/sys/kernel/debug/tracing/trace_pipe`. Max 3 args. Signed for early development.

**Perf Event Output**: `bpf_perf_event_output()` writes to perf ring buffer. Userspace reads via `perf_event_open()`. Legacy method.

**BPF Ring Buffer** (`BPF_MAP_TYPE_RINGBUF`, since 5.8): Shared ring buffer between BPF and userspace. Reserved/commit protocol. No lock contention compared to perf event array. `bpf_ringbuf_reserve()`, `bpf_ringbuf_submit()`, `bpf_ringbuf_discard()`.

**Map Batch Ops** (since 5.6): `bpf_map_lookup_batch()`, `bpf_map_delete_batch()`. Bulk dump/delete of map entries. Reduces BPF syscall overhead for monitoring.

**BPF Iterators** (since 5.8): Iterate over kernel data structures from BPF. E.g., `BPF_SK_STORAGE_GET` for socket-local storage. Task iterator, netlink iterator.

**BPF skeletons**: Generated `*.skel.h` from `bpftool gen skeleton`. Load BPF program into kernel with one call. `skel->bss->variable`, `skel->maps.variable`.

---

## /proc Filesystem Deep Dive

**CPU**:

| Entry | Content |
|-------|---------|
| `/proc/cpuinfo` | Per-core: model, MHz, cache, flags, cores, siblings |
| `/proc/loadavg` | 1/5/15 min load, running/total, last PID |
| `/proc/stat` | Aggregate: user, nice, system, idle, iowait, irq, softirq, steal, guest |

**Memory**:

| Entry | Content |
|-------|---------|
| `/proc/meminfo` | Total, free, available, buffers, cached, swap, slab, hugepages |
| `/proc/vmstat` | Page faults (pgfault, pgmajfault), swap (pswpin, pswpout), compaction |
| `/proc/zoneinfo` | Per-zone: managed, free, present, watermark, pagesets, fragmentation |
| `/proc/buddyinfo` | Free pages by order per node/zone |
| `/proc/pagetypeinfo` | Page type (Unmovable, Movable, Reclaimable, HWPoison, Reserve) by zone/order |
| `/proc/slabinfo` | Per-cache: active objs, total objs, size, pages |

**Networking**:

| Entry | Content |
|-------|---------|
| `/proc/net/tcp` | TCP connections (sl, local addr, rem addr, st, tx/rx queue, uid, inode) |
| `/proc/net/udp` | UDP sockets |
| `/proc/net/dev` | Interface bytes/packets/errs/drop |
| `/proc/net/snmp` | SNMP counters (Ip, Icmp, Tcp, Udp) |
| `/proc/net/netstat` | Extended netstat (ListenOverflows, TCPLoss, TCPFastRetrans) |
| `/proc/net/sockstat` | Socket usage by type |
| `/proc/net/route` | IPv4 routing table |

**Block/IO**:

| Entry | Content |
|-------|---------|
| `/proc/diskstats` | Per-disk: reads/writes completed, merged, sectors, ms |
| `/proc/mounts` | Mounted filesystems |
| `/proc/filesystems` | Supported filesystem types |
| `/proc/ioports` | I/O port regions in use |
| `/proc/interrupts` | IRQ per CPU per device |
| `/proc/locks` | Active file locks (POSIX, FLOCK, OFDLCK) |

---

## /sys Filesystem

**Block**: `/sys/block/<dev>/` — `queue/` (scheduler, nr_requests, rotational, read_ahead_kb), `device/` (model, vendor, rev).

**Class**: `/sys/class/` — `net/<iface>/` (speed, duplex, address, operstate, mtu), `drm/`, `i2c/`, `spi_master/`, `tty/`.

**Devices**: `/sys/devices/` — Full device tree. `pci0000:00/0000:00:01.0/`, `platform/coretemp.0/`.

**Kernel**: `/sys/kernel/` — `mm/transparent_hugepage/`, `fscaps/`, `notes/`, `iommu_groups/`, `uevent_helper/`.

**Power**: `/sys/power/` — `state` (mem/standby/disk), `disk` (platform/shutdown/reboot), `pm_async`, `wakeup_count`.

**FS**: `/sys/fs/` — `cgroup/` (controllers), `ext4/<dev>/` (mb_groups, mb_stats), `btrfs/`, `xfs/`.

---

## sar/sysstat

**System Activity Report** — `sar`, `mpstat`, `iostat`, `pidstat`.

```bash
sar -u 1 5                 # CPU every 1s, 5 times
sar -r 1 5                 # Memory
sar -b 1 5                 # Block I/O
sar -B 1 5                 # Page faults
sar -S 1 5                 # Swap
sar -n DEV 1 5             # Network device stats
sar -n TCP 1 5             # TCP stats
sar -n SOCK 1 5            # Socket stats
sar -W 1 5                 # Swapping stats
sar -F 1 5                 # Mount/filesystem stats

# Historical data (from /var/log/sysstat/)
sar -f /var/log/sysstat/sa12

mpstat -P ALL 1 5          # Per-CPU stats
iostat -x 1 5              # Extended disk stats (await, svctm, %util)
pidstat 1 5                # Per-process: CPU, memory, I/O
pidstat -d 1 5             # Per-process I/O
pidstat -r 1 5             # Per-process memory (minflt, majflt, RSS, VSZ)
pidstat -w 1 5             # Context switches
pidstat -t 1 5             # Per-thread
```

**Key metrics**:
- `sar -u`: `%user`, `%nice`, `%system`, `%iowait`, `%steal`, `%idle`
- `sar -r`: `kbmemfree`, `kbmemused`, `%memused`, `kbbuffers`, `kbcached`, `kbcommit`, `%commit`
- `sar -b`: `tps`, `rtps`, `wtps`, `bread/s`, `bwrtn/s`
- `sar -n DEV`: `rxpck/s`, `txpck/s`, `rxkB/s`, `txkB/s`, `%ifutil`

---

## top/htop/atop/btm

| Tool | Key Features |
|------|-------------|
| **top** | Classic. `M` (sort by mem), `P` (sort by CPU), `1` (per-CPU), `H` (threads), `u` (user filter) |
| **htop** | Color-coded, mouse support, tree view (F5), vertical/horizontal scroll, search (F3), filter (F4) |
| **atop** | Cumulative resource usage. `d` (disk), `n` (net), `s` (scheduling), `c` (command). Logs to `/var/log/atop/` |
| **btm** (bottom) | Rust-based, modern. GPU temps, disk temps, process grouping, mouse |

**atop specifics**:

```
ATOP - myhost               2024/01/15  14:30:01              ------ 10s elapsed
PRC | sys    1.23s  |  user   0.45s  | #proc   156  | #zombie    0  | #exit   12  |
CPU | sys     12%  |  user    5%  | irq      1%  | idle    81%  | wait    1%  |
CPU | cpu000   6%  |  cpu001  8%  | cpu002  12%  | cpu003   5%  |            |
CPL | avg1    2.3  |  avg5   2.1  | avg15   1.9  | csw    3412  | intr   1523  |
MEM | tot    15.8G |  free    1.2G | cache   4.5G | buff  122.3M | slab  456.6M |
SWP | tot     2.0G |  free    1.5G | vmcom   6.2G | vmlim   7.9G |
DSK | sda     busy  67%  |  read     456  |  write   1234  | avio 0.33 ms |
NET | eth0    10 Gbps |  pcki   12345  |  pcko   23456  | sp   12 Mbps |
```

---

## lsof

**List Open Files** — everything is a file:

```bash
lsof -p 1234                   # all open files for PID
lsof -i :8080                  # listening and connections on port
lsof -i TCP                    # all TCP connections
lsof -i @192.168.1.1           # connections to/from IP
lsof -P -n                    # no port name resolution, no hostname
lsof -u root                   # files opened by user
lsof +D /var/log               # all open files in directory
lsof -c nginx                  # processes starting with "nginx"
lsof -F                        # machine-readable output (for scripts)
```

**Output columns**:
```
COMMAND   PID  USER   FD   TYPE   DEVICE  SIZE/NODE   NAME
nginx    1245  root  cwd    DIR    8,1      4096      /etc/nginx
nginx    1245  root  txt    REG    8,1    1181024     /usr/sbin/nginx
nginx    1245  root  mem    REG    8,1    2156072     /lib/x86_64-linux-gnu/libc.so.6
nginx    1245  root    0r   CHR    1,3                /dev/null
nginx    1245  root    3u   IPv4  12345               TCP *:80 (LISTEN)
nginx    1246  www    5u   IPv4  12346               TCP 10.0.0.1:80->10.0.0.2:54321 (ESTABLISHED)
```

**FD column**: `cwd` (current dir), `rtd` (root dir), `txt` (text seg), `mem` (mmap), `0u` (fd 0, u=read+write), `N` (unknown), `DEL` (deleted but still open).

**TYPE column**: `REG` (file), `DIR`, `CHR` (char dev), `BLK`, `IPv4`, `IPv6`, `unix`, `FIFO`, `PIPE`, `sock`.

---

## valgrind

| Tool | Purpose | Command |
|------|---------|---------|
| **memcheck** | Memory errors (leaks, UAF, OOB) | `valgrind --tool=memcheck ./a.out` |
| **cachegrind** | Cache profiling (L1/L2/LL) | `valgrind --tool=cachegrind ./a.out` |
| **callgrind** | Call graph + cache simulation | `valgrind --tool=callgrind ./a.out` |
| **helgrind** | Thread data races | `valgrind --tool=helgrind ./a.out` |
| **drd** | Thread data races (lighter) | `valgrind --tool=drd ./a.out` |
| **massif** | Heap profiler (snapshots) | `valgrind --tool=massif ./a.out` |
| **DHAT** | Heap access patterns | `valgrind --tool=dhat ./a.out` |
| **BBV** | Basic block vector (SimPoint) | `valgrind --tool=bbv ./a.out` |

**memcheck errors**:

```
==1234== Invalid write of size 4      # write to freed memory
==1234==    at 0x4004A0: main (test.c:10)
==1234==  Address 0x5203040 is 0 bytes inside a block of size 10 free'd

==1234== Conditional jump depends on uninitialized value(s)

==1234== HEAP SUMMARY:
==1234==     in use at exit: 40 bytes in 1 blocks
==1234==   total heap usage: 1 allocs, 0 frees, 40 bytes allocated
==1234==   40 (40 direct, 0 indirect) bytes in 1 blocks are definitely lost
```

**massif**: Output visualizable with `ms_print massif.out.1234`. Shows heap usage over time with stack traces at peaks.

**cachegrind**: Output analyzable with `cg_annotate cachegrind.out.1234`. Shows L1/L2/LL misses per function.

**callgrind**: Use `callgrind_annotate` or KCachegrind (GUI) for call graph visualization.

**Limitations**: ~10-50x slowdown. Memory usage grows (memcheck tracks every byte's state). `--undef-value-errors=no` speeds up.

---

## Heap Analysis

**heaptrack** (KDE): Low-overhead heap profiler.

```bash
heaptrack ./a.out
heaptrack -p 1234                    # attach
heaptrack_print heaptrack.1234.gz    # analyze
heaptrack_gui heaptrack.1234.gz      # GUI
```

**massif-visualizer**: GUI for Massif output. Shows peak memory points. Click on peak to see stack trace of allocations.

**`/proc/pid/status`**: `VmPeak`, `VmSize`, `VmRSS`, `VmData`, `VmStk`, `VmExe`, `VmLib`.

**`/proc/pid/smaps`**: Per-mapping RSS/PSS. Shows dirty/clean private/shared breakdown.

**`/proc/pid/smaps_rollup`**: Aggregated smaps (since 4.14).

**jemalloc heap profiling**:

```bash
MALLOC_CONF=prof:true,prof_prefix:jeprof.out ./a.out
jeprof --text ./a.out jeprof.out.0001.heap
jeprof --svg ./a.out jeprof.out.0001.heap > heap.svg
```

**glibc malloc tracing**: `mtrace()` / `muntrace()` with `MALLOC_TRACE` env var. `mtrace` perl script analyzes output.

---

## Hugepage & OOM Analysis

**Hugepage analysis**:

```bash
cat /proc/meminfo | grep Huge        # HugePages_Total, Free, Rsvd
cat /proc/pid/smaps | grep -i huge   # shows which VMAs use huge pages
cat /sys/kernel/mm/transparent_hugepage/enabled
cat /sys/kernel/mm/transparent_hugepage/defrag
grep -i thp /proc/vmstat             # thp_fault_alloc, thp_collapse_alloc, thp_split
perf stat -e page-faults ./a.out     # compare with/without THP
```

**OOM Analysis**:

```bash
dmesg | grep -i "oom\|out of memory"     # OOM killer messages
journalctl -k | grep -i oom              # via systemd journal
cat /proc/pid/oom_score                   # current OOM score (0-1000)
cat /proc/pid/oom_score_adj               # adjustment (-1000 to 1000)
cat /proc/pid/oom_adj                     # legacy adjustment (-17 to 15)
find /proc -maxdepth 2 -name oom_score -exec grep -l . {} \;  # all OOM scores
```

**OOM killer message**:

```
Out of memory: Killed process 12345 (mysqld) total-vm:12345678kB, anon-rss:4567890kB, file-rss:1234kB, shmem-rss:0kB, UID:999 pgtables:12345kB oom_score_adj:0
```

---

## Coredump Analysis

**Setup**:

```bash
ulimit -c unlimited                   # enable coredumps for shell
echo "/tmp/core.%p.%e.%t" > /proc/sys/kernel/core_pattern
systemctl start systemd-coredump      # systemd's coredump collector
coredumpctl list                      # list stored coredumps
coredumpctl info 1234                 # info about PID 1234's coredump
coredumpctl gdb 1234                  # launch gdb with coredump
```

**abrt** (Automatic Bug Reporting Tool): `abrt-cli list`, `abrt-cli report`.

**gdb coredump analysis**:

```gdb
gdb /path/to/binary /path/to/core
bt full                  # full backtrace (local variables, args)
frame 3                  # switch to frame 3
info locals              # locals at crash point
info registers           # CPU state at crash
list                     # source at crash point
print *variable          # inspect value at crash
p/x $rax                 # register value
x/20i $rip-40            # disassembly around crash
up/down                  # walk stack
thread apply all bt      # backtrace for all threads
```

**Common coredump analysis patterns**:
- SIGSEGV at address 0 → null pointer dereference
- SIGSEGV at address 0x7fff... → stack overflow
- SIGABRT with backtrace in malloc → heap corruption
- SIGFPE → division by zero
- `__stack_chk_fail` → buffer overflow (stack smashing detected)
- `_int_malloc` in backtrace → heap corruption detected by malloc

---

## Simplest Mental Model

> **Linux observability is like having cameras, counters, and inspectors throughout a factory.**
>
> - **strace** = recording every time a worker picks up the phone (syscall). You see who they call, what they say, how long the call lasts. Expensive because you record everything.
> - **perf** = a dashboard of electric meters. You know how much power (cycles), how many widgets (instructions), and how often the assembly line stalls (cache misses). Sampling gives you snapshots without full recording.
> - **ftrace** = a CCTV focused on one specific machine inside the factory. You see every function called inside that machine, with timestamps.
> - **bpftrace/BCC** = micro-inspectors you can place anywhere — inside a pipe, on a gear, on a conveyor belt. They count things, measure times, and barely slow down the factory.
> - **gdb** = a pause button for a single worker. You freeze them, examine their hands (registers), see what's in their pockets (stack), and step through their actions one by one.
> - **top/htop** = a wall display showing how busy each department is right now.
> - **lsof** = a list of every drawer, cabinet, and door that's currently open across the whole factory.
> - **valgrind** = a quality inspector who shadows one worker, tracking every piece of paper they pick up (malloc) and put down (free), flagging if they forget to return anything or write in someone else's drawer.
> - **coredump** = a photograph of the accident scene — exactly what each worker was doing, what they were holding, and where they were standing when the crash happened.
> - **sar/iostat** = the factory's daily logbook. Every 10 minutes it records temperature, output, queue lengths. You look back to find when things started going wrong.
