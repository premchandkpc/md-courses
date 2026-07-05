# 06-SQS

Amazon Simple Queue Service is a fully managed message queue for decoupling microservices. SQS allows services to communicate asynchronously: a producer sends a message to a queue, a consumer polls and processes it. No direct connection between producer and consumer is required.

## Overview
SQS supports two queue types. Standard queues offer high throughput (virtually unlimited messages per second) and at-least-once delivery — messages may be delivered more than once. FIFO queues (First-In-First-Out) guarantee exactly-once processing and strict message ordering within a message group. FIFO throughput is capped at 3000 messages per second (batch) or 300 (non-batch), but can be increased with batching. Messages can be retained for 1 minute to 14 days (default 4 days). SQS is pull-based: consumers poll for messages, process them, and delete them from the queue.

## Key Characteristics
- **At-least-once delivery (Standard)**: Consumers must be idempotent — processing the same message twice must produce the same result. Standard queues can deliver duplicates.
- **Exactly-once (FIFO)**: FIFO queues deduplicate messages using a deduplication ID (or content-based dedup). Perfect for financial transactions where duplicates are unacceptable.
- **Visibility timeout**: When a consumer receives a message, it becomes invisible to other consumers for the visibility timeout period (30s default, adjustable 0s–12hr). The consumer must delete the message within this window. If the consumer fails (no delete), the message becomes visible again for reprocessing.
- **Dead-letter queue (DLQ)**: Messages that fail processing repeatedly (exceed maxReceiveCount) are moved to a DLQ for analysis. Prevents poisoned messages from blocking the queue.
- **Long polling**: Consumers can wait up to 20 seconds for a message to arrive (reducing empty responses). Compared to short polling (immediate return), long polling is more efficient and cost-effective.
- **Cost**: Pay per request (SQS API calls). The first 1 million requests per month are free. Batch operations (up to 10 messages per request) reduce costs by 10x.

## Why It Matters
SQS is the backbone of asynchronous communication in AWS microservices. It decouples producers and consumers so they can scale independently, fail independently, and be deployed on different schedules. Common patterns: API Gateway → SQS → Lambda (buffering sudden traffic spikes), SQS between order and shipping services, and SQS as a work queue for background job processing.

## Related Concepts
- [SNS](07-SNS.md) — Pub/sub messaging that can fan out to SQS queues
- [Lambda](04-Lambda.md) — Can poll SQS queues natively; batch processing with no polling code needed
- [Horizontal Scaling](13-Scalability/01-Horizontal-Scaling.md) — More consumers can be added to process messages faster

---

## Mental Model
A restaurant kitchen uses a ticket printer (SQS). Waiters (producers) place orders into the printer. Cooks (consumers) grab tickets and prepare dishes. Multiple cooks can grab from the same ticket bin, working in parallel. If a cook gets sick while preparing a dish (consumer failure), the ticket goes back on the rail (visibility timeout), and another cook picks it up.
