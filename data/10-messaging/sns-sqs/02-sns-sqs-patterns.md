# ☁️ SNS & SQS Production Patterns — Complete Deep Dive

> Battle-tested patterns for reliable, scalable, cost-effective messaging with SNS and SQS in production.

## 📑 Table of Contents

- [1. Fan-Out Architecture](#1-fan-out-architecture)
- [2. Ordered Processing with FIFO](#2-ordered-processing-with-fifo)
- [3. Exactly-Once Processing](#3-exactly-once-processing)
- [4. SQS as Buffered Lambda Consumer](#4-sqs-as-buffered-lambda-consumer)
- [5. Batch Lambda Processing](#5-batch-lambda-processing)
- [6. SNS & CloudWatch Alarms](#6-sns--cloudwatch-alarms)
- [7. Cross-Region SNS](#7-cross-region-sns)
- [8. Transaction Outbox to SQS](#8-transaction-outbox-to-sqs)
- [9. SQS Poison Pill Handling](#9-sqs-poison-pill-handling)
- [10. Cost Optimization](#10-cost-optimization)
- [11. SQS+SNS vs Kafka Decision Guide](#11-sqssns-vs-kafka-decision-guide)
- [12. Idempotent Consumers](#12-idempotent-consumers)
- [13. SNS Message Archiving](#13-sns-message-archiving)
- [14. Simplest Mental Model](#14-simplest-mental-model)

---
## 1. Fan-Out Architecture
```text
Producer → SNS Topic ─┬─→ SQS Orders → Lambda: Process
                       ├─→ SQS Audit → S3 Archive
                       ├─→ SQS Analytics → Firehose → S3
                       └─→ Lambda: Cache update
```
Single event triggers multiple independent workflows. Each team owns their queue.
**Checklist**: Each SQS has own DLQ • Raw message delivery on • Filter policies • CloudWatch on queue depth
```python
sns.set_subscription_attributes(SubscriptionArn='...', AttributeName='RawMessageDelivery', AttributeValue='true')
```
---
## 2. Ordered Processing with FIFO
```text
Producer → SNS FIFO Topic → SQS FIFO → Lambda Processor
group=123    orders.fifo    orders.fifo
```
Ordering per MessageGroupId. Groups process in parallel.
**Limits**: SNS FIFO → SQS FIFO only • 300 TPS (3000 batch) • 5-min dedup window
```python
sns.publish(TopicArn='arn:...:orders.fifo', Message=json.dumps({'order_id': '123'}),
    MessageGroupId='123', MessageDeduplicationId=f"placed-{uuid.uuid4()}")
```
---
## 3. Exactly-Once Processing
```text
SQS FIFO → Receive → check DynamoDB idempotency key
                        ├── Exists → skip (delete)
                        └── Not exists → process + store → delete msg
```
```python
try:
    dynamodb.put_item(TableName='idempotency', Item={'pk': {'S': f'MSG#{dedup_id}'},
        'ttl': {'N': str(int(time.time()) + 86400)}}, ConditionExpression='attribute_not_exists(pk)')
except ClientError:
    return {'status': 'duplicate'}
```
**Key sources**: Webhook → pi_id + event_type • Order → order_id + version • Outbox → UUID
---
## 4. SQS as Buffered Lambda Consumer
```text
Traffic spike → SQS (buffer millions) → Lambda (auto-scale)
```
SQS absorbs spikes. Lambda scales with queue depth. Auto-retry. No data loss.
```yaml
OrderProcessor:
  Type: AWS::Serverless::Function
  Properties:
    Events:
      SQSEvent:
        Type: SQS
        Properties:
          Queue: !GetAtt OrdersQueue.Arn
          BatchSize: 10
          MaximumBatchingWindowInSeconds: 5
    ReservedConcurrentExecutions: 50
```
---
## 5. Batch Lambda Processing
```python
def lambda_handler(event, context):
    failures = []
    for record in event['Records']:
        try:
            payload = json.loads(record['body'])
            if 'Message' in payload: payload = json.loads(payload['Message'])
            process_record(payload)
        except Exception:
            failures.append({'itemIdentifier': record['messageId']})
    return {'batchItemFailures': failures}
```
Use ReportBatchItemFailures to avoid reprocessing successful items.
---
## 6. SNS & CloudWatch Alarms
```python
cloudwatch.put_metric_alarm(AlarmName='orders-queue-oldest',
    MetricName='ApproximateAgeOfOldestMessage', Namespace='AWS/SQS',
    Dimensions=[{'Name': 'QueueName', 'Value': 'orders'}],
    Statistic='Maximum', Period=300, EvaluationPeriods=2, Threshold=300,
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=['arn:aws:sns:...:ops-alerts'])
```
| Metric | Threshold | Meaning |
|--------|-----------|---------|
| ApproximateAgeOfOldestMessage | > 5 min | Consumer stuck |
| NumberOfMessagesReceived | Drop > 50% | Producer issue |
| DLQ ApproximateNumberOfMessages | > 0 | Investigate failures |
---
## 7. Cross-Region SNS
```text
us-east-1                        eu-west-1
SNS Topic ──────────────────────► SQS Queue
```
Target SQS needs policy allowing source SNS. Data transfer costs apply.
```python
sqs.set_queue_attributes(QueueUrl=eu_url, Attributes={'Policy': json.dumps({
    'Statement': [{'Effect': 'Allow', 'Principal': {'Service': 'sns.amazonaws.com'},
        'Action': 'sqs:SendMessage', 'Resource': eu_arn,
        'Condition': {'ArnEquals': {'aws:SourceArn': us_topic_arn}}}]})})
sns.subscribe(TopicArn=us_topic_arn, Protocol='sqs', Endpoint=eu_arn)
```
---
## 8. Transaction Outbox to SQS
```text
Service → DB TX ─┬─→ Business table
                  └─→ Outbox table (same TX) → Poller → SQS → Consumer
```
If DB write succeeds, message is guaranteed sent.
```sql
BEGIN;
    INSERT INTO orders (id, customer_id, total) VALUES ('123', '456', 99.99);
    INSERT INTO outbox (aggregate_type, aggregate_id, event_type, payload)
    VALUES ('order', '123', 'order_placed', '{"order_id":"123"}');
COMMIT;
```
**Poller**: Lambda reads outbox WHERE processed_at IS NULL, sends to SQS, marks processed.
---
## 9. SQS Poison Pill Handling
```text
Source → receive → consumer fails → retry × N → DLQ → fix → redrive
```
Non-retriable errors → delete immediately.
```python
def consumer(event, context):
    for record in event['Records']:
        try:
            process(record['body'])
        except ValueError:
            continue
        except Exception:
            if int(record['attributes']['ApproximateReceiveCount']) >= 5:
                log_poison(record); continue
            raise
```
**Redrive**: sqs.start_message_move_task(SourceArn=dlq_arn)
---
## 10. Cost Optimization
| Strategy | Savings | Trade-off |
|----------|---------|-----------|
| Long poll (20s) | ~70% | +20s latency |
| Batch (10 msgs) | ~90% | None |
| Raw delivery | Varies | None |
**Checklist**: Long polling • Max batch size • Lambda window • Raw delivery • Compress • Filter • Delete unused • Short retention
```python
sqs.create_queue(QueueName='optimized', Attributes={
    'ReceiveMessageWaitTimeSeconds': '20', 'VisibilityTimeout': '120', 'MessageRetentionPeriod': '86400'})
```
---
## 11. SQS+SNS vs Kafka Decision Guide
| Criteria | SQS+SNS | Kafka (MSK) |
|----------|---------|-------------|
| Ops overhead | Zero | Significant |
| Throughput | ≤ 10K msg/s | 100K+ msg/s |
| Retention | ≤ 14 days | Configurable |
| Ordering | Per-group FIFO | Per-partition |
| Replay | No | Yes |
| Integration | Deep AWS | Open ecosystem |
**Decision**: Need > 10K TPS, replay, or > 14 day retention? → **Kafka**. Otherwise → **SQS+SNS**.
---
## 12. Idempotent Consumers
```python
def process_idempotent(record):
    dedup_id = record['messageId']
    try:
        dynamodb.put_item(TableName='idempotency', Item={'pk': {'S': f"MSG#{dedup_id}"},
            'ttl': {'N': str(int(time.time()) + 86400)}}, ConditionExpression='attribute_not_exists(pk)')
    except ClientError:
        return {'status': 'duplicate'}
    try:
        return process_payment(json.loads(record['body']))
    except Exception:
        dynamodb.delete_item(TableName='idempotency', Key={'pk': {'S': f"MSG#{dedup_id}"}})
        raise
```
**Key sources**: Payment webhook → pi_id + event_type • Order → order_id + version • FIFO → MessageDeduplicationId
---
## 13. SNS Message Archiving
```text
Producer → SNS Topic ─┬─→ SQS (processing)
                       └─→ Lambda Archiver → S3 (partitioned by date)
```
```python
def archive_lambda(event, context):
    for record in event['Records']:
        dt = datetime.fromisoformat(record['Sns']['Timestamp'].replace('Z', '+00:00'))
        key = f"archives/year={dt.year}/month={dt.month}/day={dt.day}/{record['Sns']['MessageId']}.json"
        s3.put_object(Bucket='event-archive', Key=key, Body=json.dumps(json.loads(record['Sns']['Message'])))
```
**Alternative**: Subscribe Firehose to SNS for zero-code S3 archiving.
---
## 14. Simplest Mental Model
```text
┌───────────────────────────────────────────────────────────┐
│                   SIMPLEST MENTAL MODEL                    │
│   ┌─────────────────┐              ┌─────────────────┐   │
│   │ Post Office SNS │    push      │  PO Box SQS     │   │
│   │ Copies to all   │─────────────►│ Holds for pickup│   │
│   │ Broadcast, push │              │ Pull, durable   │   │
│   └─────────────────┘              └─────────────────┘   │
│                                                           │
│   Fan-out = Send one, many receive                        │
│   FIFO = Numbered letters in order                        │
│   DLQ = Return to sender after N tries                    │
│   Poison pill = Broken letter → dead letter               │
│   Exactly-once = Check "done this?" before processing     │
│                                                           │
│   Three Golden Rules:                                     │
│   1. Always use DLQs (they save you at 3 AM)             │
│   2. Always use long polling (save money)                │
│   3. Always build idempotent consumers (save data)        │
└───────────────────────────────────────────────────────────┘
```
**One Sentence**: Use SQS as buffer; use SNS to broadcast; combine for resilient pub/sub with per-consumer buffering.
**Production Settings**: VisTimeout = 6× processing time • Poll = 20s • DLQ maxReceiveCount = 5 • Batch size = 5-10 • Window = 5-30s • Filter at source • Raw delivery on • Shortest retention


---

## Code Examples

```python
# Example implementation
# [Add language-specific code demonstrating core concept]
pass
```

---

## Common Failure Modes

**Problem**: [Key issue in production]

**Root cause**: [Why it happens]

**Solution**: [How to fix]

---

## Interview Questions

### Q1: [Core concept question]

**Answer**: [Detailed explanation with trade-offs]

### Q2: [Design/architecture question]

**Answer**: [Best practices and reasoning]
