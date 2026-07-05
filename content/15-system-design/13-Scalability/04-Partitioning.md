# 04-Partitioning

Dividing data or work into smaller, independent units called partitions. Partitioning enables parallel processing, improves manageability, and distributes load across resources. It applies to databases, message queues, file systems, and computation.

## Overview
Partitioning is a broader concept than sharding. In databases, partitioning splits a table into physical segments (by range, list, or hash of a partition key) that can be queried independently. In Kafka, topics are split into partitions that are distributed across brokers for parallel consumption. In distributed computing, map-reduce partitions input data for parallel mapping. Partitioning provides a natural unit for parallelism and fault isolation — one partition's failure doesn't affect others.

## Key Characteristics
- **Parallelism enabler**: Data in different partitions can be processed concurrently by different workers, threads, or nodes. Total throughput scales with partition count.
- **Partition scheme matters**: Range partitioning (by date, ID range) supports efficient scans but can create hot partitions. Hash partitioning spreads evenly but breaks range queries. List partitioning groups discrete values.
- **Partition independence**: Each partition is self-contained. Operations on one partition don't block others. This reduces contention compared to a single shared resource.
- **Manageability**: Dropping old data becomes a partition drop instead of a DELETE. Backups and maintenance can target individual partitions.
- **Rebalancing complexity**: Adding partitions requires redistributing data. Kafka handles this with partition reassignment; databases require ALTER TABLE operations or dump/reload cycles.

## Why It Matters
Partitioning appears at every level of a microservices system. Database tables are partitioned by date for time-series data. Kafka topics are partitioned for consumer group parallelism. File storage is partitioned across shards. Understanding partitioning helps architects design systems that scale linearly rather than hitting shared-resource contention.

## Related Concepts
- [Sharding](03-Sharding.md) — A specific form of partitioning where data is split across database nodes
- [Hot Partition](09-Hot-Partition.md) — When one partition receives disproportionate traffic
- [Horizontal Scaling](01-Horizontal-Scaling.md) — Partitioned data can be distributed across horizontally scaled compute

---

## Mental Model
A large warehouse is divided into numbered zones. Each zone stores a specific category of items (aisle 1–5: electronics, 6–10: clothing, etc.). When an order comes in, workers in each zone pick their items in parallel. The warehouse processes orders faster than if every worker had to search the entire building.
