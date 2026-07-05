# 08-Kinesis

Amazon Kinesis is a family of services for real-time streaming data. Kinesis Data Streams ingests and stores data streams for processing by multiple consumers. Kinesis Data Firehose loads streaming data into data stores (S3, Redshift, Elasticsearch). Kinesis Data Analytics processes streams with SQL or Apache Flink.

## Overview
Kinesis Data Streams is the core service. Producers (applications, IoT devices, log shippers) send data records to a stream. The stream is divided into shards, each with a write capacity of 1 MB/s or 1000 records/s and read capacity of 2 MB/s. Records within a shard are ordered and stored for up to 365 days (retention period). Consumers (Lambda, KCL applications, Firehose, Analytics) read records in order from the shards. Multiple consumers can read the same stream independently, each with their own cursor position (enhanced fan-out).

## Key Characteristics
- **Ordered records per shard**: Within each shard, records are strictly ordered by sequence number. This enables exactly-once processing per shard and ordered event logs.
- **Replay capability**: Streams persist data for 24 hours (default) up to 365 days. Consumers can rewind and reprocess from any point — critical for bug fixes and data reprocessing.
- **Shard-based scaling**: Throughput is determined by shard count. Scaling requires splitting or merging shards (resharding), which takes time and has limits (only double or halve shard count). Provisioned capacity means you pay for peak shard count.
- **Multiple consumer patterns**: Shared throughput (2 MB/s per shard across all consumers) vs. enhanced fan-out (2 MB/s per shard per consumer, at additional cost). Enhanced fan-out is used for real-time dashboards or ML inference.
- **Kinesis Client Library (KCL)**: Coordinates consumer applications, manages shard leases, handles failover. KCL tracks cursor positions in DynamoDB.
- **Integration with Lambda**: Lambda can poll Kinesis streams as an event source. It processes records in batches, retries on failure, and can send failed records to a DLQ.

## Why It Matters
Kinesis is the backbone for real-time data in AWS microservices. Use cases: application log aggregation, clickstream analytics, IoT data ingestion, real-time metrics, event sourcing, and CDC (Change Data Capture) from DynamoDB Streams. Its ordered, replayable, multi-consumer design makes it ideal for event-driven architectures that need stronger guarantees than SNS fan-out.

## Related Concepts
- [DynamoDB Streams](09-DynamoDB.md) — DynamoDB's change-data-capture stream, similar to Kinesis but per-table
- [Lambda](04-Lambda.md) — Kinesis event source mapping enables serverless stream processing
- [SQS](06-SQS.md) — Pull-based queue for async messaging vs. Kinesis push/pull for streaming

---

## Mental Model
A factory conveyor belt (Kinesis shard) carrying products past inspection stations. Each station (consumer) checks for different defects — one checks weight, another checks packaging, a third scans labels. The belt is split into multiple lanes (shards), each carrying a different product category. If an inspector needs to recheck yesterday's batch, they can rewind the belt (replay) to any point within the retention period.
