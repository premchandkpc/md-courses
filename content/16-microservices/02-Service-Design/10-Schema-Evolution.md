# 10-Schema-Evolution

Schema evolution defines the rules for changing data schemas over time in a way that maintains wire compatibility between producers and consumers operating at different schema versions.

## Overview

In microservices, services communicate over the network using serialized messages. Whether using JSON over HTTP, Protobuf over gRPC, or Avro over Kafka, the structure of those messages will change over time. Schema evolution rules — established by systems like Protocol Buffers, Apache Avro, and Apache Thrift — define which changes are safe (backward-compatible, forward-compatible, or both) and which break the wire contract.

## Key Characteristics

- **Protobuf Rules**: Field numbers must never be reused. Fields can be added as `optional` (safe) or removed by number reservation. Changing field types is a breaking change. Unknown fields are preserved during serialization/deserialization by default.
- **Avro Rules**: Readers and writers can be at different schemas. Adding a field with a default value is backward-compatible. Removing a field the reader expects is not. Avro's resolution algorithm reconciles reader and writer schemas at read time.
- **Forward vs Backward Compatibility**: Forward compatibility means a new consumer can read old messages. Backward compatibility means an old consumer can read new messages. Ideally, schemas support both.
- **Schema Registry**: A central service (Confluent Schema Registry, Apicurio) stores all schema versions, validates changes against compatibility rules, and ensures producers write schemas that consumers can read.

## Why It Matters

In an event-driven microservices system, messages may live in queues or logs for days. A consumer may process a message written by a version of the producer that was deployed weeks ago. Schema evolution rules ensure those messages are still readable. Without them, you risk deserialization failures that cause data loss, retry storms, and hard-to-diagnose production incidents.

## Related Concepts

- [08-Backward-Compatibility](08-Backward-Compatibility.md) — schema evolution is the data-level expression of this principle
- [07-Service-Versioning](07-Service-Versioning.md) — versioning at the API level vs evolution at the schema level
- [03-gRPC](../03-Communication/03-gRPC.md) — Protobuf schema evolution in practice
- [08-Kafka](../03-Communication/08-Kafka.md) — Avro schema evolution with Schema Registry

---

## Mental Model

Schema evolution is like a hotel room assignment system. The hotel (producer) may have room 201 booked as a single (v1 schema), then renovate it to a double (v2 schema). A guest (consumer) who booked a single will still find a usable room — the bed count changes but the room exists. But if the hotel removes room 201 entirely (deletes a field), the guest has nowhere to stay. Schema evolution is the rulebook for these renovations.
