# 🌊 Stream Processing — Complete Deep Dive

> **Scope**: Processing semantics (at-most-once, at-least-once, exactly-once), Kafka Streams (topology, KStream/KTable, state stores, exactly-once, DSL operators, Processor API), Apache Flink (DataStream API, event time, watermarks, windowing, state management, checkpointing, fault tolerance), stream-batch unification.

## Table of Contents

1. Stream Processing Semantics
2. Stream vs Batch Unification
3. Kafka Streams: Topology & Core Abstractions
4. Kafka Streams: KStream, KTable, GlobalKTable
5. Kafka Streams: State Stores
6. Kafka Streams: Exactly-Once Semantics
7. Kafka Streams: DSL Operators & Windowing
8. Kafka Streams: Processor API
9. Flink: Architecture & DataStream API
10. Flink: Event Time & Watermarks
11. Flink: Windowing
12. Flink: State Management & Checkpointing
13. Flink: Fault Tolerance

---

## 1. Stream Processing Semantics

```text
+------------------+------------------+------------------+
|  At-Most-Once    |  At-Least-Once   |  Exactly-Once    |
+------------------+------------------+------------------+
| Fire and forget  | Retry on fail    | Idempotent writes|
| May lose data    | May duplicate    | Transactional    |
| Fastest          | Medium           | Costliest        |
+------------------+------------------+------------------+
```

**At-Most-Once:** Process, don't retry. Crash → data loss.
**At-Least-Once:** Process then commit offset. Crash before commit → duplicate.
**Exactly-Once Approaches:**
1. **Idempotent writes:** Same result every time (e.g., `UPDATE x=5 WHERE id=y`).
2. **Transactional consume-process-produce:** Commit offsets + produce in one atomic tx.
3. **Deduplication:** Track processed IDs, skip duplicates.

---

## 2. Stream vs Batch Unification

**Stream** = unbounded, event-triggered, incremental. **Batch** = bounded, scheduled, full recompute.

**Stream-Table Duality:** A stream is a changelog of updates to a table. A table is a snapshot of a stream. `KTable` = compacted stream (latest per key). `KStream` = full history.

**Unified APIs (Flink, Kafka Streams):** Same code processes batch and stream. Batch = bounded stream.

---

## 3. Kafka Streams: Topology & Core Abstractions

```text
Source Topic → SourceProcessor → StreamTask → Processor → SinkProcessor → Output Topic
                 (topology DAG)
```

**Processor Types:**
- **Source:** Reads from Kafka topic.
- **Stream:** Transforms (map, filter, join).
- **Sink:** Writes to Kafka topic.

**StreamTask:** Unit of parallelism. One task per topic partition. Each task runs its own processor topology instance.

---

## 4. Kafka Streams: KStream, KTable, GlobalKTable

```python
builder = StreamBuilder()

# KStream — all records (append-only event stream)
orders: KStream = builder.stream("orders")
orders.filter(lambda k, v: v["amount"] > 100) \
      .map(lambda k, v: (v["user_id"], v)) \
      .to("high-value-orders")

# KTable — latest per key (upsert from compacted topic)
users: KTable = builder.table("user-profiles")

# KStream-KTable join
enriched = orders.join(users,
    join_key=lambda o: o["user_id"],
    value_mapper=lambda o, u: {**o, "email": u["email"]})

# GlobalKTable — full replica on every node (for broadcast data)
products: GlobalKTable = builder.global_table("product-catalog")
```

**KStream (append-only):** All records. **KTable (upsert):** Latest per key, compacted internally. **GlobalKTable (broadcast):** Entire table on all nodes for small reference data.

---

## 5. Kafka Streams: State Stores

```text
StreamTask 0          StreamTask 1          StreamTask 2
+---------------+     +---------------+     +---------------+
| RocksDB Store |     | RocksDB Store |     | InMemory Store|
| (partition 0) |     | (partition 1) |     | (partition 2) |
+---------------+     +---------------+     +---------------+
      |                      |                       |
      +----------+-----------+-----------------------+
                 | Changelog Topics (backup + recovery)
                 v
```

**Types:** RocksDB (disk-backed, handles > memory), In-Memory (fast, volatile), Persistent (RocksDB + logging).

**Changelog Topics:** Every stateful op has a changelog topic. On restart, state store rebuilds from changelog.

**Standby Replicas:** Warm state copies on other nodes for fast recovery during rebalance.

**Interactive Queries:** Query state stores externally via `streams.store("store", ...).get("key")`.

---

## 6. Kafka Streams: Exactly-Once Semantics

```text
Consume → Process → Produce (committed atomically)
    |                    |
    offset committed     batch written
    in same tx           in same tx
    v                    v
Source Topic          Sink Topic
```

**Transaction Coordinator:** Broker managing producer transactions. **Epoch (Zombie Fencing):** Each producer instance gets unique epoch. Stale epochs rejected.

**Configuration:**
```python
props = {"processing.guarantee": "exactly_once_v2"}  # Kafka 3.0+
```

**EOS v1:** Separate producer per task, many concurrent transactions. **EOS v2:** One producer per thread, single transaction per poll.

---

## 7. Kafka Streams: DSL Operators & Windowing

**Stateless operators:** `filter`, `map`, `flatMap`, `selectKey`, `peek`, `branch`, `merge`.

**Stateful operators:** `groupBy` + `count`/`aggregate`/`reduce`, `join`, `cogroup`.

```python
# Windowing
tumbling = grouped.windowed_by(TimeWindows.of(Duration.ofMinutes(5))).count()

hopping = grouped.windowed_by(
    TimeWindows.of(Duration.ofMinutes(10)).advance_by(Duration.ofMinutes(5))
).count()

sessions = grouped.windowed_by(
    SessionWindows.with(Duration.ofMinutes(5))  # inactivity gap
).count()
```

```text
Tumbling: [0-5) [5-10) [10-15)    (fixed, non-overlapping)
Hopping:  [0-10)[5-15)[10-20)     (fixed, overlapping)
Session:  |--active--|gap|--active--|gap|  (gap-based)
```

**Grace Period:** `TimeWindows.of(...).grace(Duration.ofMinutes(1))` — wait for late records.

**Suppression:** `suppress(Suppressed.untilWindowCloses(...))` — emit only at window end.

---

## 8. Kafka Streams: Processor API

```python
class MyProcessor(Processor):
    def init(self, context):
        self.store = context.getStateStore("my-store")
        context.schedule(Duration.ofSeconds(30), PunctuationType.WALL_CLOCK_TIME, self.punctuate)

    def process(self, key, value):
        count = (self.store.get(key) or 0) + 1
        self.store.put(key, count)
        self.context.forward(key, {"count": count})

    def punctuate(self, ts):
        results = list(self.store.all())
        self.context.forward("__agg__", results)
```

**ProcessorContext:** `forward()` to downstream, `schedule()` for punctuators, `commit()` for manual commit.

**Custom State Store:** `Stores.persistentKeyValueStore("my-store")` connected via `connectProcessorAndStateStores`.

---

## 9. Flink: Architecture & DataStream API

```text
JobManager — coordination, checkpoint management, scheduling
    |
TaskManager 1 (slots)     TaskManager 2 (slots)     TaskManager N
    |                          |                         |
  subtasks                  subtasks                   subtasks
```

```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

DataStream<SensorReading> readings = env
    .addSource(new FlinkKafkaConsumer<>("sensors", deserializer, props));

DataStream<Alert> alerts = readings
    .filter(r -> r.temperature > 100)
    .map(r -> new Alert(r.sensorId, "High temperature: " + r.temperature));

alerts.addSink(new FlinkKafkaProducer<>("alerts", serializer, props));
env.execute("Temperature Monitor");
```

**Flink SQL (Table API):**
```sql
SELECT sensor_id, TUMBLE_END(ts, INTERVAL '10' SECOND) AS win,
       AVG(temperature) AS avg_temp
FROM sensor_data
GROUP BY sensor_id, TUMBLE(ts, INTERVAL '10' SECOND);
```

---

## 10. Flink: Event Time & Watermarks

**Three time concepts:**
- **Event Time:** When the event happened (in the record).
- **Processing Time:** When Flink processes it.
- **Ingestion Time:** When it enters the pipeline.

**Watermark:** Signal "no more events with timestamp < watermark" will arrive. When watermark passes window end, window fires.

```java
readings.assignTimestampsAndWatermarks(
    WatermarkStrategy
        .<SensorReading>forBoundedOutOfOrderness(Duration.ofSeconds(5))
        .withTimestampAssigner((event, ts) -> event.timestamp)
);
```

```text
Events:  [E1@100] [E2@110] [E3@120] [E4@125] [E5@140]
Watermarks: 105      115       130      140      150
              E1 done   E2 ok      window @120 fires
```

**Idle Sources:** `withIdleness(Duration.ofSeconds(60))` — mark source idle after 60s so watermarks can proceed.

---

## 11. Flink: Windowing

```java
// Tumbling window
readings.keyBy(r -> r.sensorId)
    .window(TumblingEventTimeWindows.of(Time.minutes(5)))
    .aggregate(new AverageAggregate());

// Sliding window (size=10, slide=5)
readings.keyBy(r -> r.sensorId)
    .window(SlidingEventTimeWindows.of(Time.minutes(10), Time.minutes(5)))
    .apply(new MyWindowFunction());

// Session window (gap=5 min)
readings.keyBy(r -> r.sensorId)
    .window(EventTimeSessionWindows.withGap(Time.minutes(5)))
    .process(new MyProcessWindowFunction());
```

**Trigger:** Controls when window evaluates (count, time, custom). **Evictor:** Removes elements before evaluation.

**Functions:** `ReduceFunction` (incremental), `AggregateFunction` (accumulator different from output), `ProcessWindowFunction` (full window content).

```java
// AggregateFunction — incremental aggregation
window.aggregate(new AggregateFunction<SensorReading, AvgAccum, Double>() {
    public AvgAccum createAccumulator() { return new AvgAccum(); }
    public AvgAccum add(SensorReading r, AvgAccum a) { a.sum += r.temp; a.count++; return a; }
    public Double getResult(AvgAccum a) { return a.sum / a.count; }
    public AvgAccum merge(AvgAccum a, AvgAccum b) { ... }
});
```

---

## 12. Flink: State Management & Checkpointing

**Keyed State (per-key):**
```java
public class CountAverage extends RichFlatMapFunction<SensorReading, Double> {
    private ValueState<Tuple2<Long, Double>> state;

    public void open(Configuration c) {
        state = getRuntimeContext().getState(
            new ValueStateDescriptor<>("average", Types.TUPLE(Types.LONG, Types.DOUBLE))
        );
    }

    public void flatMap(SensorReading r, Collector<Double> out) throws Exception {
        Tuple2<Long, Double> current = state.value();
        if (current == null) current = Tuple2.of(0L, 0.0);
        current.f0++; current.f1 += r.temp;
        state.update(current);
        if (current.f0 >= 10) {
            out.collect(current.f1 / current.f0);
            state.clear();
        }
    }
}
```

**State Types:** `ValueState`, `ListState`, `MapState`, `ReducingState`, `AggregatingState`.

**Operator State (per-task):** Non-keyed, shared across all records in subtask. **Broadcast State:** Same on all instances (for rules/config).

**State Backends:** **HashMap** (heap, fast, limited), **RocksDB** (disk, more state, slower).

**State TTL:** `StateTtlConfig.newBuilder(Time.days(1)).build()`.

**Backpressure:** Downstream can't keep up. Flink uses TCP flow control + credit-based network buffers.

---

## 13. Flink: Fault Tolerance

**Checkpointing — exactly-once via barrier alignment:**

```text
Source → |BARRIER| → Operator → |BARRIER| → Sink
   |          |          |           |        |
snapshot   align      snapshot    apply     snapshot
offset    barriers    state      to sink   completed
```

```java
env.enableCheckpointing(Duration.ofMinutes(1));
env.getCheckpointConfig().setCheckpointingMode(CheckpointingMode.EXACTLY_ONCE);
env.getCheckpointConfig().setMinPauseBetweenCheckpoints(Duration.ofSeconds(30));
env.getCheckpointConfig().setCheckpointTimeout(Duration.ofMinutes(10));
```

**Savepoint:** Manual checkpoint for planned restarts (upgrade, rescaling).

**Restart Strategies:**
```java
env.setRestartStrategy(RestartStrategies.fixedDelayRestart(
    3, Duration.ofSeconds(10)));
env.setRestartStrategy(RestartStrategies.exponentialDelayRestart(
    Duration.ofSeconds(1), Duration.ofMinutes(5), 2.0, 0.1, Duration.ofMinutes(2)));
```

**Failure Recovery Flow:**
1. Task fails, JobManager detects via heartbeat timeout.
2. JobManager cancels all tasks.
3. Restarts from latest checkpoint.
4. Sources resume from checkpointed offsets.
5. Stateful operators restore from snapshots.

---

## Simplest Mental Model

**Stream processing handles an infinite series of events without storing them all.** Kafka Streams turns Kafka topics into living tables — every message is an update to a key-value store. Flink breaks streams into tiny time-based batches (windows) with guaranteed consistency via checkpoints. **Both solve: "process data as it arrives, not later."** Use Kafka Streams when already in Kafka ecosystem; use Flink for complex event-time, large state, or batch + stream unification.
