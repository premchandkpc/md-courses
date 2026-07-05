# 09-DynamoDB

Amazon DynamoDB is a fully managed NoSQL key-value and document database that delivers single-digit millisecond latency at any scale. It is serverless, auto-scaling, and designed for microservices that need predictable performance without database administration.

## Overview
DynamoDB stores data in tables, each with a primary key (partition key or partition+sort key). Data is automatically replicated across three Availability Zones in an AWS Region. Tables support on-demand or provisioned capacity modes. The item size limit is 400 KB. DynamoDB offers two read/write consistency models: eventually consistent (default, lower cost) and strongly consistent (reads the latest write). It also provides DynamoDB Accelerator (DAX) — an in-memory cache that reduces read latency from single-digit ms to microseconds.

## Key Characteristics
- **Auto-scaling capacity**: On-demand mode scales instantly to handle traffic spikes with no capacity planning. Provisioned mode uses auto-scaling policies to adjust read/write capacity based on utilization. Both are fully serverless.
- **Query and scan patterns**: Query is fast and efficient (accesses items by primary key). Scan reads the entire table — expensive at scale. Tables must be designed for query efficiency, not ad-hoc queries.
- **Secondary indexes**: Local Secondary Index (LSI) — same partition key, different sort key — must be created at table creation. Global Secondary Index (GSI) — different partition key — can be created anytime. GSIs have their own throughput and can be queried independently.
- **DynamoDB Streams**: Time-ordered sequence of item-level changes (insert, update, delete). Used for change data capture (CDC), materialized views, cross-region replication, and event-driven workflows. Streams are Kinesis-compatible.
- **TTL (Time to Live)**: Automatically expires items after a specified timestamp. No cost, no write operations. Ideal for session data, event logs, and time-series data with automatic cleanup.
- **Transactions**: DynamoDB Transactions provide ACID across up to 25 items or 4 MB of data within a single table or across tables. Enables financial operations and inventory management.
- **Consistency model**: Eventually consistent reads (up to 2x cheaper, sub-10ms) and strongly consistent reads (reflect latest write). Strong consistency may have higher latency during replication delays.

## Why It Matters
DynamoDB is the default database for many serverless microservices on AWS. It eliminates nearly all database operations: no schema migrations, no connection pooling, no read replica management, no manual sharding. Combined with Lambda, API Gateway, and SQS, DynamoDB enables fully serverless architectures. However, its query model is restrictive — access patterns must be designed in advance, and complex joins/aggregations require application-level handling.

## Related Concepts
- [Lambda](04-Lambda.md) — Lambda functions commonly read/write DynamoDB for serverless data access
- [RDS](10-RDS.md) — Relational alternative when DynamoDB's query limitations become problematic
- [CAP Theorem](13-Scalability/10-CAP-Theorem.md) — DynamoDB is CP (strong consistency) or AP (eventual consistency) per request

---

## Mental Model
A giant filing cabinet with millions of labeled folders. Each folder has a unique label (partition key). To find something, you go directly to the label — no searching, no sorting. You can also add sub-labels (sort key) to organize items within a folder. If you need to find everything by a different label, you build a separate index (GSI). The cabinet automatically expands, shrinks, and keeps backup copies.
