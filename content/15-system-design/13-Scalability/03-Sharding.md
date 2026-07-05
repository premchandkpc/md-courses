# 03-Sharding

Splitting a large dataset across multiple database instances by a shard key so that each shard holds a subset of the data. Sharding distributes read and write load horizontally, enabling databases to scale beyond what a single node can handle.

## Overview
Sharding divides data into independent subsets, each hosted on a separate database server (shard). A routing layer — the application, a proxy (e.g., ProxySQL, pgpool), or a database-native feature (e.g., MongoDB sharding, Citus for Postgres) — directs queries to the correct shard based on the shard key. Hash-based sharding assigns data to shards via a hash of the key for uniform distribution. Range-based sharding splits data by value ranges (e.g., user IDs 1–10000 on shard A, 10001–20000 on shard B), which supports range queries but risks hot spots.

## Key Characteristics
- **Shard key selection is critical**: A poor key causes uneven data distribution and hot partitions. High-cardinality keys that evenly spread queries are ideal.
- **Cross-shard operations are expensive**: JOINs, transactions, and aggregations across shards require scatter-gather patterns, coordination, and often application-level workarounds.
- **Rebalancing is painful**: Adding or removing shards requires moving large volumes of data. Consistent hashing reduces the amount of data that must move during rebalancing.
- **No single point of failure**: Each shard can have its own replication. Losing one shard affects only its subset of users.
- **Operational complexity**: You manage N database clusters instead of one. Backups, monitoring, schema migrations — all must handle N shards.

## Why It Matters
Sharding is how the largest systems handle data at scale. Every major platform (Uber, Airbnb, Twitter) shards its core databases. Microservices often shard per-service: the order service shards its orders table, the user service shards its users table. Without sharding, the database becomes the hard bottleneck that no amount of stateless service replicas can fix.

## Related Concepts
- [Partitioning](04-Partitioning.md) — Sharding is a form of partitioning, but partitioning also covers non-database data splits (Kafka partitions, file partitions)
- [Vertical Scaling](02-Vertical-Scaling.md) — The simpler alternative before sharding is needed
- [Hot Partition](09-Hot-Partition.md) — A common failure mode when shard key choice is poor

---

## Mental Model
A single library has aisles organized by the first letter of the author's last name. A–C in one aisle, D–F in another, etc. Each aisle is a shard. Finding a book is fast — you know the shard key (author's last name). But searching across all aisles for "books published in 2023" requires checking every shard (scatter-gather).
