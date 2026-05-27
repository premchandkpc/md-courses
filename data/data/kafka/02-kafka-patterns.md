# 📨 Kafka Production Patterns — Complete Deep Dive

**Related**: [Kafka Basics](01-kafka-basics.md) · [Distributed Transactions & Saga](../microservices/06-distributed-transactions-saga.md) · [CQRS & Event Sourcing](../microservices/07-cqrs-event-sourcing.md)

---

## Table of Contents

- [Event Sourcing](#-event-sourcing-with-kafka) · [1. CQRS](#1-cqrs-with-kafka) · [2. Outbox](#2-outbox-pattern) · [3. Transactional Messaging](#3-transactional-messaging) · [4. Idempotent Consumers](#4-idempotent-consumers) · [5. DLQ & Retry](#5-dead-letter-queues--retry-topics) · [6. Compacted Topics](#6-compacted-topics-for-state) · [7. Streaming Joins](#7-streaming-joins) · [8. Windowed Aggregations](#8-windowed-aggregations) · [9. Global KTables](#9-global-ktables) · [10. Interactive Queries](#10-interactive-queries) · [11. Exactly-Once](#11-exactly-once-end-to-end) · [12. MirrorMaker](#12-kafka-mirrormaker-for-dr) · [Simplest Mental Model](#-simplest-mental-model)

---

## 🧭 Event Sourcing with Kafka

```text
Stores state changes as an immutable event log.

  Traditional: DB Row (status:SHIPPED) — history lost
  Event Sourcing: [OrderPlaced, PaymentRecvd, OrderShipped] — full audit trail
```

| Aspect | Traditional | Event Sourcing |
|--------|-------------|----------------|
| Audit trail | Manual logs | Built-in |
| Temporal query | Impossible | Replay any point |
| Schema changes | Migrations | New event types |

---

## 1. CQRS with Kafka

```text
Separates commands (writes) from queries (reads):

  Command → Handler + Write DB → Event (Kafka) → Projector → Read DB
  Query → Read DB (denormalized for reads)
```

```javascript
consumer.run({
    eachMessage: async ({ message }) => {
        const ev = JSON.parse(message.value.toString());
        if (ev.eventType === "OrderPlaced") {
            await db.query(`INSERT INTO order_summary (order_id, user_id, total, status)
                VALUES ($1, $2, $3, 'PLACED')`, [ev.aggregateId, ev.data.userId, ev.data.total]);
        }
    },
});
```

---

## 2. Outbox Pattern

```text
BEGIN TX: INSERT INTO orders + INSERT INTO outbox → COMMIT
Poller → read outbox → send to Kafka → mark sent

Alternative: Debezium CDC reads WAL in real-time (no polling lag).
```

```sql
CREATE TABLE outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending'
);
```

---

## 3. Transactional Messaging

```text
Atomic writes across topics:

  BEGIN TX → produce enriched ✓ → produce audit ✓ → sendOffsets → COMMIT
  → all written OR none (auto-abort on failure)
```

```java
producer.initTransactions();
while (true) {
    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
    producer.beginTransaction();
    try {
        for (ConsumerRecord<String, String> record : records) {
            producer.send(new ProducerRecord<>("enriched-orders", enrich(record)));
            producer.send(new ProducerRecord<>("audit-log", audit(record)));
        }
        producer.sendOffsetsToTransaction(currentOffsets(consumer), consumer.groupMetadata());
        producer.commitTransaction();
    } catch (Exception e) { producer.abortTransaction(); }
}
```

---

## 4. Idempotent Consumers

```text
Handle duplicates: process → INSERT; same event again → dedup → SKIP.
```

```sql
CREATE TABLE processed_events (
    event_id VARCHAR(255) PRIMARY KEY,
    processed_at TIMESTAMP DEFAULT NOW()
);
INSERT INTO processed_events (event_id) VALUES ($1) ON CONFLICT (event_id) DO NOTHING;
```

| Condition | Action |
|-----------|--------|
| Already processed | Skip |
| Incomplete prior | Re-apply |
| Stale | Reject |

---

## 5. Dead Letter Queues & Retry Topics

```text
  Consumer → process → success (done)
              ↓ failure, retries < 3
         Retry Topic (backoff)
              ↓ retries exhausted
         DLQ Topic (manual analysis)

Kafka has no native delay. Workarounds: timestamp-filtered retry topics,
separate topics per delay (orders-retry-10s, orders-retry-1m).
```

```javascript
try { await processMessage(message); }
catch (err) {
    const r = (message.headers["retry-count"] || 0);
    const topic = r < 3 ? "orders-retry" : "orders-dlq";
    await producer.send({ topic, messages: [{
        key: message.key, value: r < 3 ? message.value : JSON.stringify({ err: err.message }),
        headers: { ...message.headers, "retry-count": (r+1).toString() },
    }]});
}
```

---

## 6. Compacted Topics for State

```text
Only latest value per key survives: u1=v1, u2=v1, u1=v2, u3=v1, u1=v3, u2=v2
→ u3=v1, u1=v3, u2=v2 → ideal for KTables
```

```java
KTable<String, UserProfile> profiles = builder.table("user-profiles",
    Consumed.with(Serdes.String(), profileSerde));

KStream<String, EnrichedOrder> enriched = builder
    .stream("orders", Consumed.with(Serdes.String(), orderSerde))
    .leftJoin(profiles, (order, profile) -> new EnrichedOrder(order, profile));
```

Use cases: user profiles, product catalog, configuration.

---

## 7. Streaming Joins

**Stream-Table** (enrichment):
```java
KStream<String, EnrichedOrder> enriched = orders.join(users,
    (order, user) -> new EnrichedOrder(order, user),
    Joined.with(Serdes.String(), orderSerde, userSerde));
```

**Stream-Stream** (time-bounded within window):
```java
KStream<String, MatchedOrder> matched = orders.join(payments,
    (order, payment) -> new MatchedOrder(order, payment),
    JoinWindows.ofTimeDifferenceWithNoGrace(Duration.ofHours(1)));
```

**Table-Table**: merge two KTables.

---

## 8. Windowed Aggregations

| Window | Behavior | Use Case |
|--------|----------|----------|
| Tumbling | Non-overlapping | Per-minute counts |
| Hopping | Overlapping | Rolling averages |
| Sliding | Per-pair | Event correlation |
| Session | Activity-triggered | User sessions |

```java
KTable<Windowed<String>, Long> perMinute = orders
    .groupByKey(Grouped.with(Serdes.String(), orderSerde))
    .windowedBy(TimeWindows.ofSizeWithNoGrace(Duration.ofMinutes(1)))
    .count();

KTable<Windowed<String>, Long> sessions = orders
    .groupByKey(Grouped.with(Serdes.String(), orderSerde))
    .windowedBy(SessionWindows.ofInactivityGapWithNoGrace(Duration.ofMinutes(30)))
    .count();
```

---

## 9. Global KTables

```text
KTable: partitioned (subset per instance) — needs co-partitioning
GlobalKTable: ALL data on EVERY instance — no co-partitioning needed
```

```java
GlobalKTable<String, Product> products = builder.globalTable("products",
    Consumed.with(Serdes.String(), productSerde));

KStream<String, Order> enriched = orders.join(products,
    (orderKey, order) -> order.getProductId(),
    (order, product) -> { order.setPrice(product.getPrice()); return order; });
```

For small reference data (<1GB).

---

## 10. Interactive Queries

```text
HTTP query of state stores. Local key → return. Remote key → route to owner.
```

```java
ReadOnlyKeyValueStore<String, Long> store = streams
    .store(StoreQueryParameters.fromNameAndType("order-count-store",
        QueryableStoreTypes.keyValueStore()));
Long count = store.get(userId);
if (count != null) return count;
HostInfo host = streams.metadataForKey("order-count-store", userId, ...);
return remoteQuery(host, "/api/orders/count/" + userId);
```

---

## 11. Exactly-Once End-to-End

| Stage | Mechanism |
|-------|-----------|
| Source → Kafka | Idempotent producer + outbox |
| Kafka internal | Transactions + read_committed |
| Kafka Streams | `processing.guarantee=exactly_once_v2` |
| Consumer → Sink DB | Dedup + `ON CONFLICT DO NOTHING` |

---

## 12. Kafka MirrorMaker for DR

```text
  Primary (active R+W) ──MM2──> Replica (standby, read-only)
                                          │ failover
                                          ▼
                                  Producers/consumers switch
```

```yaml
clusters: primary, backup
primary->backup.enabled: true
primary->backup.topics: .*
sync.group.offsets.enabled: true
```

| Strategy | RPO | RTO | Complexity |
|----------|-----|-----|------------|
| Active-Passive (MM2) | Sec-min | Minutes | Medium |
| Active-Active | ~0 | Seconds | High |

---

## 🧭 Simplest Mental Model

```text
  Event Sourcing  = Store EVERYTHING, never delete
  CQRS            = Separate pen (write) from map (read)
  Outbox          = Write message WITH data (same DB txn)
  DLQ             = Dead letter office for failures
  Retry           = Give it another chance (backoff)
  Compacted       = Latest snapshot per key
  Transaction     = All-or-nothing across topics
  MirrorMaker     = Offsite backup for Kafka

  Golden rule: Kafka is a LOG, not a queue.
  Consumer groups → queue semantics.
  Compacted topics → key-value storage.
  Transactions → atomic multi-topic writes.
```
