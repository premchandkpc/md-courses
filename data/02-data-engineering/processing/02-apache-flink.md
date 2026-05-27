# Apache Flink

## Overview

Apache Flink is a distributed stream processing framework designed for stateful computations over unbounded and bounded data streams. It provides high throughput, low latency (real-time), and exactly-once semantics. Flink originated from the Stratosphere research project at TU Berlin and became a top-level Apache project in 2015.

## Architecture

### Flink Cluster Components

```
+-------------------------------------------------------------------+
|                         Flink Cluster                              |
|                                                                   |
|  +----------------------------+  +----------------------------+   |
|  |      JobManager (Master)   |  |  ResourceManager           |   |
|  |  +----------------------+  |  |  - Task slot allocation    |   |
|  |  | JobGraph → Execution |  |  |  - Resource scaling        |   |
|  |  | Graph → Scheduling   |  |  +----------------------------+   |
|  |  +----------------------+  |                                     |
|  |  +----------------------+  |  +----------------------------+   |
|  |  | CheckpointCoordinator|  |  |  Dispatcher               |   |
|  |  | - Trigger ckpt      |  |  |  - Job submission          |   |
|  |  | - Align barriers    |  |  |  - REST endpoint           |   |
|  |  | - Store metadata    |  |  +----------------------------+   |
|  |  +----------------------+  |                                     |
|  +----------------------------+                                     |
|                                                                   |
|  +---------+  +---------+  +---------+  +---------+              |
|  | TM 1   |  | TM 2   |  | TM 3   |  | TM 4   |              |
|  | Slot 0  |  | Slot 0  |  | Slot 0  |  | Slot 0  |              |
|  | Slot 1  |  | Slot 1  |  | Slot 1  |  | Slot 1  |              |
|  +---------+  +---------+  +---------+  +---------+              |
+-------------------------------------------------------------------+
```

#### JobManager

The JobManager is the master process controlling the application. It contains three main components:

1. **ResourceManager**: Manages task slot resources across TaskManagers
   - Requests/releases slots from cluster managers (YARN, K8s, Standalone)
   - Handles TaskManager failures (re-requests slots)

2. **Dispatcher**: REST API endpoint for submitting jobs
   - Maintains a web dashboard (Flink UI at port 8081)
   - Receives job JARs and DataStream programs

3. **JobMaster**: One per job, responsible for:
   - Taking the JobGraph (logical dataflow)
   - Converting to ExecutionGraph (parallel physical dataflow)
   - Scheduling execution on TaskManagers
   - Coordinating checkpoints and recovery

#### TaskManager

TaskManagers are worker processes that execute dataflow operators. Key concepts:

- **Task Slot**: A fixed unit of resource (CPU/memory) in a TaskManager
- **Task**: The parallel instance of an operator running in a slot
- **Subtask**: A specific parallel instance of an operator

```
TaskManager (4 slots, 32GB, 8 cores)
+--------------------------------------------------+
|  Slot 0          |  Slot 1       |  Slot 2  |  Slot 3 |
|  Source[1]       |  Source[2]    |  Map[1]  |  Map[2] |
|  Sink[1]         |  Sink[2]      |          |          |
+--------------------------------------------------+
```

**Slot sharing**: By default, multiple operators can share the same slot (pipeline chaining). This reduces resource consumption:
```
JobGraph: source → map → keyBy → window → sink
                                       
Slot 0: [source[1], map[1], window[1], sink[1]]
Slot 1: [source[2], map[2], window[2], sink[2]]
Slot 2: [source[3], map[3], window[3], sink[3]]
```

#### Checkpoint Coordinator

The Checkpoint Coordinator is a JobManager component that:
1. Sends checkpoint barriers through data sources
2. Collects acknowledgments from operators
3. Stores checkpoint metadata in external storage (HDFS, S3)
4. Manages checkpoint lifecycle (pending, in-progress, completed)

### High Availability

```yaml
# HA configuration (ZooKeeper-based)
high-availability: zookeeper
high-availability.zookeeper.quorum: "zk1:2181,zk2:2181,zk3:2181"
high-availability.storageDir: "hdfs:///flink/ha/"
high-availability.zookeeper.path.root: "/flink"
```

## Stream Processing Model

### Dataflow Graph

A Flink application is a **Dataflow Graph**:

```
Logical Dataflow (JobGraph):
  Source(Kafka) → FlatMap(parse) → KeyBy(user) → Window(1h) → Sink(DB)

Physical Dataflow (ExecutionGraph) with parallelism=3:
  Source[1] ----> FlatMap[1] ----> KeyBy[1] --> Window[1] --> Sink[1]
  Source[2] ----> FlatMap[2] ----> KeyBy[2] --> Window[2] --> Sink[2]
  Source[3] ----> FlatMap[3] ----> KeyBy[3] --> Window[3] --> Sink[3]
```

### Basic Program Structure

```java
// Flink Streaming Job in Java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

DataStream<String> source = env
    .addSource(new FlinkKafkaConsumer<>("input-topic", new SimpleStringSchema(), props));

DataStream<Event> parsed = source
    .flatMap(new Tokenizer())
    .returns(Types.POJO(Event.class));

DataStream<Event> keyed = parsed
    .keyBy(Event::getUserId);

DataStream<WindowResult> windowed = keyed
    .window(TumblingEventTimeWindows.of(Time.hours(1)))
    .aggregate(new CountAggregate());

windowed.addSink(new FlinkKafkaProducer<>("output-topic", new SimpleStringSchema(), props));

env.execute("Flink Streaming Job");
```

### PyFlink (Python API)

```python
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors import FlinkKafkaConsumer
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.typeinfo import Types

env = StreamExecutionEnvironment.get_execution_environment()

kafka_props = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'flink-consumer'
}

ds = env.add_source(
    FlinkKafkaConsumer("input", SimpleStringSchema(), kafka_props)
)

ds = ds \
    .flat_map(lambda x: [(w, 1) for w in x.split()]) \
    .key_by(lambda x: x[0]) \
    .sum(1) \
    .print()

env.execute("PyFlink WordCount")
```

### Operators

```python
# Core operators in PyFlink
from pyflink.datastream.functions import MapFunction, FilterFunction, FlatMapFunction

class ParseFunction(MapFunction):
    def map(self, value):
        parts = value.split(",")
        return {"user": parts[0], "action": parts[1], "ts": int(parts[2])}

class ErrorFilter(FilterFunction):
    def filter(self, value):
        return value["action"] == "ERROR"

ds = env.from_collection(["alice,LOGIN,1000", "bob,ERROR,1001"])

# Map: one-to-one
parsed = ds.map(ParseFunction(), Types.MAP(Types.STRING(), Types.STRING()))

# Filter: subset
errors = parsed.filter(ErrorFilter())

# FlatMap: one-to-many
ds.flat_map(lambda s: s.value.split(","))

# KeyBy: partition by key
keyed = parsed.key_by(lambda r: r["user"])

# Reduce: stateful aggregation on keyed stream
keyed.reduce(lambda a, b: {"user": a["user"], "action": b["action"], "ts": max(a["ts"], b["ts"])})

# ProcessFunction: low-level access to state, timers, output
class MyProcessFunction(ProcessFunction):
    def process_element(self, value, ctx):
        # Access state
        count = self.count_state.value()
        self.count_state.update(count + 1)
        # Register event-time timer
        ctx.timer_service().register_event_time_timer(watermark + 5000)
        # Side output
        ctx.output(OutputTag("side-output"), value)
```

### Parallelism and Chaining

```python
env = StreamExecutionEnvironment.get_execution_environment()

# Set global parallelism
env.set_parallelism(10)

# Control chaining explicitly
ds = env.from_collection(data)

ds1 = ds.map(lambda x: x * 2).name("map1").disable_chaining()  # Force boundary
ds2 = ds1.map(lambda x: x * 3).name("map2")                     # New chain
ds3 = ds2.key_by(lambda x: x).sum(0).name("sum").slot_sharing_group("default")

# Chain comparison:
# Without disable_chaining:
#   [source → map1 → map2 → sum]  ← all in same task (single thread)

# With disable_chaining:
#   [source → map1]  [map2 → sum] ← two tasks (two threads)
```

**Chaining conditions** (all must be true):
1. Same parallelism
2. One-to-one data partitioning (forward, not keyBy)
3. Slot sharing group compatibility
4. Chainable operator type (not Sink)

## State Management

State in Flink is what makes it stateful stream processing — intermediate data stored across events.

### State Types

```python
from pyflink.datastream.state import (
    ValueStateDescriptor, ListStateDescriptor, MapStateDescriptor,
    ReducingStateDescriptor, AggregatingStateDescriptor
)

# 1. ValueState: single value per key
class CountFunction(KeyedProcessFunction):
    def __init__(self):
        self.count_state = None

    def open(self, runtime_context):
        descriptor = ValueStateDescriptor("count", Types.LONG())
        descriptor.set_queryable("queryable-count")  # Enable interactive queries
        self.count_state = runtime_context.get_state(descriptor)

    def process_element(self, value, ctx):
        current = self.count_state.value() or 0
        self.count_state.update(current + 1)

# 2. ListState: list of values per key
class ListStateFunction(KeyedProcessFunction):
    def open(self, ctx):
        self.list_state = ctx.get_list_state(
            ListStateDescriptor("events", Types.STRING())
        )

    def process_element(self, value, ctx):
        self.list_state.add(value["event_type"])

# 3. MapState: key-value map per key
class MapStateFunction(KeyedProcessFunction):
    def open(self, ctx):
        self.map_state = ctx.get_map_state(
            MapStateDescriptor("sessions", Types.STRING(), Types.LONG())
        )

    def process_element(self, value, ctx):
        self.map_state.put(value["session_id"], value["timestamp"])
        # Iterate over entries
        for k, v in self.map_state.entries():
            print(k, v)

# 4. ReducingState: incremental reduce per key
class ReducingStateFunction(KeyedProcessFunction):
    def open(self, ctx):
        self.reducing_state = ctx.get_reducing_state(
            ReducingStateDescriptor("sum", lambda a, b: a + b, Types.LONG())
        )
```

### Operator State

Operator state is state that is *not* partitioned by key. Useful for sources/sinks:

```python
class BufferingSink(SinkFunction):
    """Sink that buffers and flushes in batches using operator state."""
    class BufferState(CheckpointedFunction):
        def __init__(self):
            self.buffer = []
            self.checkpointed_state = None

        def initialize_state(self, context):
            # Restore state from checkpoint
            self.checkpointed_state = context.get_operator_state(
                ListStateDescriptor("buffer", Types.STRING())
            )
            self.buffer = list(self.checkpointed_state.get())

        def snapshot_state(self, context):
            # Store state for checkpoint
            self.checkpointed_state.clear()
            for elem in self.buffer:
                self.checkpointed_state.add(elem)

        def invoke(self, value, context):
            self.buffer.append(value)
            if len(self.buffer) >= 1000:
                self._flush()
```

### State Backends

Backends determine how state is stored and checkpoints are managed.

```python
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.state_backend import (
    HashMapStateBackend, EmbeddedRocksDBStateBuffer, RocksDBStateBackend
)

env = StreamExecutionEnvironment.get_execution_environment()

# 1. HashMapStateBackend (default for heap)
# State stored in JVM heap as Java objects
# Fast access, but limited by heap size and GC overhead
state_backend = HashMapStateBackend()
env.set_state_backend(state_backend)

# 2. RocksDBStateBackend
# State stored in embedded RocksDB instances (LMS-tree on disk)
# More memory (disk-backed), less affected by GC, slower access
state_backend = RocksDBStateBackend(
    "file:///tmp/flink-state",  # Checkpoint storage
    incremental=True            # Incremental checkpoints
)
state_backend.set_number_of_transfer_threads(4)
state_backend.set_predefined_options(
    RocksDBStateBackend.PredefinedOptions.SPINNING_DISK_OPTIMIZED
)
env.set_state_backend(state_backend)
```

**Trade-offs**:

| Feature | HashMap | RocksDB |
|---------|---------|---------|
| Access speed | Microseconds | Milliseconds |
| Memory | JVM heap | Off-heap (direct memory) |
| Checkpoint | Synchronous full snapshot | Asynchronous incremental |
| State size limit | Heap size | Disk size (TB+) |
| GC impact | High | Low |
| Cross-operator sharing | Direct reference | Serialization/deserialization |
| Best for | Small state (<10GB) | Large state (>10GB) |

**RocksDB tuning**:
```yaml
# $FLINK_HOME/conf/flink-conf.yaml
state.backend.rocksdb.memory.managed: true
state.backend.rocksdb.write-buffer-size: 64 MB
state.backend.rocksdb.max-write-buffer-number: 4
state.backend.rocksdb.min-write-buffer-number-to-merge: 2
state.backend.rocksdb.block.cache-size: 256 MB
state.backend.rocksdb.compaction.level.max-size-level-base: 256 MB
state.backend.rocksdb.thread.num: 4
state.backend.rocksdb.log.level: WARN
```

### State TTL

```python
from pyflink.api.common.state import StateTtlConfig
from pyflink.api.common.time import Time

# TTL configuration
ttl_config = StateTtlConfig \
    .new_builder(Time.hours(24)) \
    .set_update_type(StateTtlConfig.UpdateType.OnCreateAndWrite) \
    .set_state_visibility(StateTtlConfig.StateVisibility.NeverReturnExpired) \
    .set_ttl_time_characteristic(StateTtlConfig.TtlTimeCharacteristic.ProcessingTime) \
    .cleanup_full_snapshot() \           # Clean on checkpoint
    .cleanup_incrementally(1000, True) \ # Incremental cleanup
    .cleanup_rocksdb_compact_filter() \  # RocksDB filter during compaction
    .build()

# Apply to state descriptor
descriptor = ValueStateDescriptor("my-state", Types.LONG())
descriptor.enable_time_to_live(ttl_config)
```

**Cleanup strategies**:
- `cleanup_full_snapshot()`: Removes expired during full checkpoint (slowest, most thorough)
- `cleanup_incrementally(n, cleanupEmptyState)`: Incremental GC per state access
- `cleanup_rocksdb_compact_filter()`: RocksDB compaction filters (only with RocksDB backend)

## Checkpointing

### Checkpoint Mechanism

Flink's checkpointing implements the **Chandy-Lamport distributed snapshot** algorithm with barriers:

```
Phase 1: Source injects checkpoint barrier
Source:                   Operator A:              Operator B: (Sink)
  [1,2,3,BARRIER,4,5] → [1,2,BARRIER,3,4,5]   [1,2,3,4,BARRIER,5]
                            ↓                      ↓
                         Snapshot A:            Snapshot B:
                         {state_A at barrier}   {state_B at barrier}
                            ↓                      ↓
                         ACK to                    ACK to
                         JobManager               JobManager
                                 ↓
                        Checkpoint COMPLETED (Barrier 0)
```

**Alignment** (exactly-once):
```
Input 1: [1, 2, BARRIER(t=1), 3, 4, 5, ...]
Input 2: [1, BARRIER(t=1), 2, 3, 4, ...]

Operator receives:
  1. Process (1, 1) from both
  2. Receives BARRIER from Input 2 → buffers Input 1 data
  3. Receives BARRIER from Input 1 → state snapshot, release buffer
  4. Process buffered data (2, 3, 4 from Input 1) + new data
```

```python
# Enable checkpointing in job
env = StreamExecutionEnvironment.get_execution_environment()

env.enable_checkpointing(60000)  # Checkpoint every 60 seconds
env.get_checkpoint_config().set_checkpointing_mode(
    CheckpointingMode.EXACTLY_ONCE   # or AT_LEAST_ONCE (faster, weaker guarantees)
)
env.get_checkpoint_config().set_checkpoint_storage_dir("hdfs:///flink/checkpoints/")
env.get_checkpoint_config().set_max_concurrent_checkpoints(1)
env.get_checkpoint_config().set_min_pause_between_checkpoints(30000)
env.get_checkpoint_config().set_checkpoint_timeout(600000)  # 10 min
env.get_checkpoint_config().set_tolerable_checkpoint_failure_number(3)
env.get_checkpoint_config().enable_unaligned_checkpoints()
env.get_checkpoint_config().set_aligned_checkpoint_timeout(5000)  # Fall back to unaligned
```

### Checkpoint Storage

```python
# File-system based (default)
env.get_checkpoint_config().set_checkpoint_storage_dir("s3a://flink-checkpoints/job-123/")

# JobManager heap (for small state, testing)
env.get_checkpoint_config().set_checkpoint_storage("jobmanager")
```

### Incremental Checkpoints

Only available with RocksDB backend. Instead of storing full state each time:

```
Checkpoint 1: Full RocksDB SST files (1 GB)
Checkpoint 2: Only changed SST files (100 MB)
Checkpoint 3: Another delta (50 MB)
Checkpoint N: Chain of deltas → periodically compact to full
```

```python
RocksDBStateBackend("hdfs:///flink/ckpt", incremental=True)
```

### Savepoints

Savepoints are manually triggered, fully stopped checkpoints used for:

- Job upgrades with state changes
- Version upgrades (Flink, dependencies)
- Scaling parallelism
- Replaying/reprocessing

```bash
# Trigger savepoint
./bin/flink savepoint <job-id> [s3://savepoints/]

# Cancel with savepoint
./bin/flink cancel -s [s3://savepoints/] <job-id>

# Restart from savepoint
./bin/flink run -s [s3://savepoints/savepoint-xxx] job.jar

# Stop and drain all remaining data (stop with savepoint)
./bin/flink stop --savepointPath [s3://savepoints/] <job-id>
```

**Allow non-restored state** (when operator topology changes):
```bash
./bin/flink run -s s3://savepoints/sp-xxx \
  --allowSkippedState \
  job.jar
```

## Time Semantics

### Time Domains

```
+--------------------------------------------------------------+
|                        Time Hierarchy                         |
|                                                              |
|  Event Time: When the event actually happened                |
|  (embedded in event payload, may be out of order)            |
|                                                              |
|  Ingestion Time: When the event entered Flink source         |
|  (assigned by source at read time)                           |
|                                                              |
|  Processing Time: When the event is processed by an operator |
|  (system time of the machine processing it)                  |
+--------------------------------------------------------------+

Timeline:
  Event 1: eventTime=10:00:00,  ingestionTime=10:00:05,  processingTime=10:00:07
  Event 2: eventTime=10:00:01,  ingestionTime=10:00:03,  processingTime=10:00:06
  Event 3: eventTime=10:00:02,  ingestionTime=10:00:06,  processingTime=10:00:08
```

```python
# Configuration in PyFlink
from pyflink.common import TimeCharacteristic

env.set_stream_time_characteristic(TimeCharacteristic.EventTime)

# Default: ProcessingTime (lowest overhead, non-deterministic)
# EventTime:  Correct, handles out-of-order, needs watermarks
# IngestionTime: Like event time but assigned at source
```

### Watermarks

Watermarks track the progress of event time and handle late data:

```
Timeline:
  10:00  10:01  10:02  10:03  10:04  10:05  10:06  ...
    |       |      |      |     |       |      |
  Event A  Event B       Event C        Watermark: 10:03
  (10:00)  (10:01)  ...  (10:03)        (no events < 10:03 expected)
                                        ↓
                                  Window [10:00-10:05)
                                  can now be evaluated!
```

```python
from pyflink.datastream.watermark import WatermarkStrategy
from pyflink.common.time import Duration
from pyflink.common.types import Types

# Configure watermark strategy
watermark_strategy = WatermarkStrategy \
    .for_bounded_out_of_orderness(Duration.of_seconds(30)) \
    .with_timestamp_assigner(lambda event, _: event["timestamp"]) \
    .with_idleness(Duration.of_seconds(60))  # Mark as idle if no data

# Apply to stream
stream = env.from_collection(data)
stream = stream.assign_timestamps_and_watermarks(watermark_strategy)

# Custom WatermarkGenerator
class LaggingWatermarkGenerator(WatermarkGenerator):
    def __init__(self, max_lag):
        self.max_lag = max_lag
        self.max_ts = 0

    def on_event(self, event, ts, output):
        self.max_ts = max(self.max_ts, ts)
        output.emit_watermark(Watermark(self.max_ts - self.max_lag - 1))

    def on_periodic_emit(self, output):
        output.emit_watermark(Watermark(self.max_ts - self.max_lag - 1))
```

### Idle Sources

When a source stops sending data, watermarks won't advance, blocking downstream operations:

```python
# Mark source as idle after 60 seconds of no data
watermark_strategy = WatermarkStrategy \
    .for_bounded_out_of_orderness(Duration.of_seconds(10)) \
    .with_idleness(Duration.of_seconds(60))
```

## Windowing

### Window Types

```python
from pyflink.datastream.window import (
    TumblingEventTimeWindows, SlidingEventTimeWindows,
    EventTimeSessionWindows, GlobalWindows
)

# 1. Tumbling Window (fixed, non-overlapping)
keyed.window(TumblingEventTimeWindows.of(Time.minutes(5)))
# [00:00-00:05) [00:05-00:10) [00:10-00:15)

# 2. Sliding Window (fixed, overlapping)
keyed.window(SlidingEventTimeWindows.of(Time.hours(1), Time.minutes(15)))
# [00:00-01:00) [00:15-01:15) [00:30-01:30) [00:45-01:45)

# 3. Session Window (gap-based)
keyed.window(EventTimeSessionWindows.with_gap(Time.minutes(30)))
# [---session 1---]  [---session 2---]  [---session 3---]
# Events separated by <30min are in same window

# 4. Global Window (all events, needs custom trigger)
keyed.window(GlobalWindows.create())
```

### Window Function Types

```python
# ReduceFunction: incremental aggregation (most efficient)
class SumReducer(ReduceFunction):
    def reduce(self, a, b):
        return a + b

windowed.reduce(SumReducer())

# AggregateFunction: more flexible (incremental)
class AvgAggregate(AggregateFunction):
    def create_accumulator(self):
        return (0, 0)  # (sum, count)

    def add(self, value, acc):
        return (acc[0] + value, acc[1] + 1)

    def get_result(self, acc):
        return acc[0] / acc[1]

    def merge(self, a, b):
        return (a[0] + b[0], a[1] + b[1])

windowed.aggregate(AvgAggregate())

# ProcessWindowFunction: full access to window state & metadata (non-incremental)
class MyProcessWindow(ProcessWindowFunction):
    def process(self, key, context, elements, out):
        count = len(elements)
        window_start = context.window().start
        window_end = context.window().end
        out.collect(WindowResult(key, count, window_start, window_end))

windowed.process(MyProcessWindow(), Types.SOMETHING())
```

### Trigger API

```python
from pyflink.datastream.window.triggers import (
    EventTimeTrigger, ProcessingTimeTrigger, CountTrigger,
    PurgingTrigger, ContinuousEventTimeTrigger
)

# Custom trigger: fire every 1000 events OR every minute
class CustomTrigger(Trigger):
    def on_element(self, element, timestamp, window, ctx):
        # Register processing time timer for 1 minute
        ctx.register_processing_time_timer(
            ctx.get_current_processing_time() + 60000
        )
        # Fire if count reaches 1000
        count = ctx.get_timer_service().get_partition_state(
            ValueStateDescriptor("count", Types.LONG())
        ).value()
        if count >= 1000:
            return TriggerResult.FIRE
        return TriggerResult.CONTINUE

    def on_processing_time(self, time, window, ctx):
        return TriggerResult.FIRE  # Fire on timer

    def on_event_time(self, time, window, ctx):
        return TriggerResult.CONTINUE

    def on_merge(self, window, ctx):
        # Merge state when windows merge (session windows)
        pass

    def clear(self, window, ctx):
        # Clean up state
        pass

windowed.trigger(CustomTrigger())
```

**TriggerResults**:
- `CONTINUE`: Do nothing
- `FIRE`: Emit window result, keep window state
- `PURGE`: Clear window state, don't emit
- `FIRE_AND_PURGE`: Emit and clear

**Allowed lateness**:
```python
# Allow late events up to 1 hour
windowed.allowed_lateness(Time.hours(1))

# Side-output for dropped late events
late_output_tag = OutputTag("late-events", Types.INT())
windowed.side_output_late_data(late_output_tag)
```

## Joins

### Window Join

```python
stream1 = env.from_collection(...).assign_timestamps_and_watermarks(ws1)
stream2 = env.from_collection(...).assign_timestamps_and_watermarks(ws2)

# Join within same window
stream1.join(stream2) \
    .where(lambda e: e.user_id) \
    .equal_to(lambda e: e.user_id) \
    .window(TumblingEventTimeWindows.of(Time.minutes(5))) \
    .apply(lambda e1, e2: JoinedResult(e1, e2))
```

### Interval Join

Join stream1 events with stream2 events that fall in a time interval *around* the stream1 event:

```python
stream1.key_by(lambda e: e.key) \
    .interval_join(stream2.key_by(lambda e: e.key)) \
    .between(Time.minutes(-10), Time.minutes(5)) \
    .process(new ProcessJoinFunction() {
        def process_element(self, left, right, ctx, out):
            out.collect(Joined(left, right))
    })
```

### Regular Join (Table API)

```python
# Table API join (full SQL-like, with state)
from pyflink.table import TableEnvironment, EnvironmentSettings

t_env = TableEnvironment.create(EnvironmentSettings.in_streaming_mode())

orders = t_env.from_data_stream(order_stream, Schema.new_builder()
    .column("order_id", "BIGINT")
    .column("user_id", "STRING")
    .column("amount", "DOUBLE")
    .build()
)

users = t_env.from_data_stream(user_stream, Schema.new_builder()
    .column("user_id", "STRING")
    .column("name", "STRING")
    .build()
)

# Regular join (stateful, can handle updates)
result = orders.join(users).where(orders.user_id == users.user_id)
result.execute().print()
```

### Temporal Join

Joins a stream against a versioned table (changelog):

```python
# Temporal join: join against the version of users at order time
orders = t_env.from_data_stream(order_stream, ...)
users = t_env.from_data_stream(user_stream, ...)

# Create versioned view
t_env.create_temporary_view("users_versioned", users)

result = t_env.sql_query("""
    SELECT o.order_id, o.amount, u.name
    FROM orders AS o
    JOIN users_versioned FOR SYSTEM_TIME AS OF o.order_time AS u
    ON o.user_id = u.user_id
""")
```

## Fault Tolerance

### Restart Strategies

```python
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.restart_strategy import (
    FixedDelayRestartStrategy, FailureRateRestartStrategy,
    FallbackRestartStrategy
)

# 1. Fixed delay restart (default)
# Restart 3 times with 10-second delay
env.set_restart_strategy(
    FixedDelayRestartStrategy(3, 10000)
)

# 2. Failure rate restart
# Max 5 failures in 5 minutes, 30-second delay
env.set_restart_strategy(
    FailureRateRestartStrategy(5, Time.minutes(5), Time.seconds(30))
)

# 3. No restart
env.set_restart_strategy(RestartStrategies.no_restart())

# 4. Exponential backoff (1.5 base, 1min initial, 30min max)
env.set_restart_strategy(
    RestartStrategies.exponential_delay(
        Time.seconds(60), Time.minutes(30), 1.5
    )
)
```

### Exactly-Once Sinks

Exactly-once sinks require a **two-phase commit** protocol:

```
JobManager: Checkpoint Coordinator
      |
      | Trigger checkpoint barrier
      v
Operator (Kafka Sink):
  Phase 1 (Pre-commit): Write records to Kafka, open transaction
     → "I'm ready to commit, state is at checkpoint N"
  Phase 2 (Commit): Checkpoint completes, commit Kafka transactions
     → "Transaction for checkpoint N is committed"
  
If failure between pre-commit and commit:
  → Kafka transactions are aborted on recovery
  → Data is consistent - exactly once
```

```python
# Kafka exactly-once sink
from pyflink.datastream.connectors.kafka import FlinkKafkaProducer
from pyflink.common.serialization import SimpleStringSchema

# Requires: transaction.timeout.ms > checkpoint interval
kafka_props = {
    'bootstrap.servers': 'localhost:9092',
    'transaction.timeout.ms': '600000',
}

exactly_once_sink = FlinkKafkaProducer(
    "output-topic",
    SimpleStringSchema(),
    kafka_props,
    semantic=Semantic.EXACTLY_ONCE
)

stream.add_sink(exactly_once_sink)
```

**Supported exactly-once sinks**:
| Sink | Mechanism |
|------|-----------|
| Kafka | Two-phase commit with transactions |
| JDBC (Postgres/MySQL) | XA transactions |
| Streaming File Sink | Rolling files + commit on checkpoint |
| Elasticsearch (with X-Pack) | Bulk processor with transaction ID |
| Pulsar | Transactional producer |

### Job Failure Handling

When a TaskManager fails:

```
1. Failure detected by JobManager (heartbeat timeout: 50s)
2. JobManager cancels all running tasks in the job
3. JobManager restarts all tasks (based on restart strategy)
4. All operators load state from last successful checkpoint
5. Sources resume from checkpointed offsets
6. Downstream operators process state, but no output until all states restored
7. Normal processing resumes
```

**Failure flow diagram**:
```
TM fails → JM detects → Cancel all tasks → Determine restart strategy
                                                     ↓
                                               Delay (if configured)
                                                     ↓
                                  Re-deploy tasks with checkpointed state
                                                     ↓
                                  Sources seek to checkpointed offsets
                                                     ↓
                                  Operators restore state from checkpoint
                                                     ↓
                                  [Processing Resumes]
```

### End-to-End Exactly-Once

For true end-to-end exactly-once, all components must support it:

```
Source              Flink           Sink
(Kafka)             (Process)       (Kafka)
  ↓                   ↓               ↓
Offset tracking    Checkpoint     Two-phase commit
committed to       state at       (Kafka transactions
Zookeeper/Kafka    barriers       with pre-commit
                                 and commit phases)
  ↓                   ↓               ↓
Exactly-once      Exactly-once    Exactly-once
source semantics   state          sink semantics
  ↓                   ↓               ↓
            END-TO-END EXACTLY-ONCE
```

**Prerequisites**:
1. Source: Kafka 0.10+ with consumer offset tracking
2. Flink: Exactly-once checkpointing with alignment
3. Sink: Transactional sink (Kafka producer with `idempotence=true`)
4. Idempotent writes at target system (if transactional sink not available)

## Optimizations

### Operator Chaining

Chaining reduces serialization and network overhead:

```python
# Default: maximal chaining
env.disable_operator_chaining()  # DISABLE all chaining for debugging

# Selective: start new chain
stream.map(lambda x: x * 2).start_new_chain()
```

### Task Slot Configuration

```yaml
# flink-conf.yaml
taskmanager.numberOfTaskSlots: 8
taskmanager.memory.process.size: 32768m
taskmanager.memory.task.heap.size: 16384m
taskmanager.memory.managed.size: 8192m
taskmanager.memory.network.max: 1024m

# Job parallelism
parallelism.default: 20
```

### Buffer and Network Tuning

```yaml
# Network buffer tuning for high throughput
taskmanager.memory.network.fraction: 0.15
taskmanager.memory.network.min: 64mb
taskmanager.memory.network.max: 1gb
taskmanager.network.memory.buffers-per-channel: 2
taskmanager.network.memory.floating-buffers-per-gate: 16
taskmanager.network.request-backoff.initial: 100
taskmanager.network.request-backoff.max: 10000
taskmanager.network.netty.transport: epoll  # Linux only
```

### Async I/O

Async I/O allows overlapping I/O operations (database lookups):

```python
from pyflink.datastream.functions import AsyncFunction
import asyncio
import aiohttp

class AsyncEnrichment(AsyncFunction):
    async def async_invoke(self, value):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://api/user/{value.user_id}") as resp:
                user = await resp.json()
                value.name = user["name"]
                return value

stream = AsyncDataStream.ordered_wait(
    stream, AsyncEnrichment(), 1000,  # Max 1000 concurrent requests
    TimeUnit.MILLISECONDS
)
# ordered_wait: preserves record order
# unordered_wait: higher throughput, may reorder
# unordered_no_wait: even higher throughput, no backpressure
```

## Monitoring

### Flink Web UI

Accessible at `http://jobmanager:8081`:

```
Dashboard:
  - Running/Failed jobs
  - Checkpoint stats (completed, failed, in-progress)
  - Task slot utilization

Job Page:
  - Full execution graph with operator metrics
  - Per-subtask metrics:
    - Records received/sent
    - Bytes received/sent
    - Current/low/high watermarks
    - Backpressure ratio (low/ok/high)
  - Checkpoint history with sizes and durations

Backpressure Monitoring:
  - Color-coded: OK (green) < 0.1, LOW < 0.5, HIGH (red) > 0.5
  - Indicates if operator is processing slower than receiving
```

### Metrics

```yaml
# flink-conf.yaml metrics
metrics.reporter.prom.class: org.apache.flink.metrics.prometheus.PrometheusReporter
metrics.reporter.prom.port: 9250

# Custom metrics in code
class MyRichMap(RichMapFunction):
    def open(self, params):
        self.counter = self.get_runtime_context()
            .get_metric_group()
            .counter("my-counter")

        self.gauge = self.get_runtime_context()
            .get_metric_group()
            .gauge("my-gauge", lambda: self.state.value())

    def map(self, value):
        self.counter.inc()
        return process(value)
```

**Key metrics**:
```
numRecordsIn / numRecordsOut       - Throughput
currentInputWatermark              - Event time progress
lastCheckpointSize                 - Checkpoint overhead
numberOfBuffersInLocalChannels    - Network buffer pressure
numBytesInLocal / numBytesInRemote - Local vs remote data transfer
```

### Logging

```xml
<!-- log4j.properties -->
log4j.rootLogger=WARN, file
log4j.logger.org.apache.flink=INFO
log4j.logger.org.apache.flink.runtime.checkpoint=DEBUG
log4j.logger.org.apache.flink.streaming.runtime.tasks=DEBUG
log4j.logger.org.apache.flink.runtime.state=DEBUG
```

---

## Related

- [Databases](../../08-databases/) — Data storage and querying
- [Messaging](../../10-messaging/) — Event streaming (Kafka)
- [Cloud Platforms](../../05-cloud/) — Data warehousing (Redshift, BigQuery)
- [Backend](../../03-backend/) — Data service APIs
- [Distributed Systems](../../09-distributed-systems/) — Scale and consistency
