# 09-CDC

Change Data Capture (CDC) is a technique for capturing database changes (inserts, updates, deletes) from the database's transaction log (WAL — Write-Ahead Log) and streaming them as events. Tools like Debezium, Maxwell, and AWS DMS implement CDC to feed events into message brokers without application code changes.

## Overview
- Every modern database writes all modifications to a transaction log or WAL before applying them to the actual data pages.
- CDC reads this log in real-time, parses each change record, and emits it as an event to a broker (Kafka, Pulsar) or webhook.
- The application is unaware of CDC — it writes to the database normally, and changes appear in the event stream automatically.
- CDC provides a zero-code way to implement the Outbox pattern, feed data into other systems, or populate CQRS read models.

## Key Characteristics
- **Non-Invasive**: No application code changes needed. The existing CRUD operations produce events naturally through the database log.
- **Low Latency**: CDC captures changes within milliseconds of the database commit — faster than polling-based approaches.
- **Snapshot Capability**: Most CDC tools can take an initial snapshot of the entire table before streaming incremental changes.
- **Schema Changes**: CDC tools must handle schema evolution (column adds, drops, renames) gracefully. Debezium uses Confluent Schema Registry for this.
- **Full Change History**: CDC streams include before-and-after images (if configured), enabling complete data replication and auditing.

## Why It Matters
CDC is the most practical way to introduce event-driven architecture into an existing system without rewriting application code. It powers data replication, cache invalidation, search index updates, and analytics pipelines. However, CDC is a read-only capture mechanism — it cannot enforce business rules or prevent invalid writes. It also adds operational overhead: log retention, CDC connector management, and schema compatibility.

## Related Concepts
- [05-Outbox-Pattern](05-Outbox-Pattern.md) — CDC is an alternative to the explicit Outbox table for reliable event publishing.
- [07-CQRS](07-CQRS.md) — CDC can populate CQRS read models from the write database log.
- [08-Event-Sourcing](08-Event-Sourcing.md) — Both capture state changes as an event stream, but CDC works on existing state-based databases.

---

## Mental Model
CDC is like a stenographer sitting next to a judge, transcribing every word spoken in court. The judge (application) does their job without thinking about the transcription. The stenographer's log (CDC event stream) is a complete, accurate record that others can read later — journalists, lawyers, or the appeals court — without disturbing the proceedings.
