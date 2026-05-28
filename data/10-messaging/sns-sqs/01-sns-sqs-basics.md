# ☁️ SNS & SQS — Complete Deep Dive

> Comprehensive reference for Amazon SQS and SNS — every major concept, feature, and integration pattern.



```mermaid
graph LR
    PROD_SNS["Producer"] --> SNS["SNS Topic"]
    SNS --> SQS1["SQS Queue A<br/>(Subscription)"]
    SNS --> SQS2["SQS Queue B<br/>(Subscription)"]
    SNS --> LAMBDA1["Lambda<br/>(Subscription)"]
    SNS --> EMAIL["Email / SMS<br/>(Subscription)"]
    SQS_STD["SQS Standard"] --> MAX_THR["Unlimited TPS<br/>(At-Least-Once)"]
    SQS_FIFO["SQS FIFO"] --> ORDER["Strict Ordering<br/>(Exactly-Once)"]
    SQS_FIFO --> DEDUP["Deduplication<br/>(MessageDeduplicationId)"]
    SQS_STD --> VISIBILITY["Visibility Timeout<br/>(30s default)"]
    SQS_STD --> DLQ_SQS["Dead-Letter Queue<br/>(maxReceiveCount)"]
    LONG_POLL["Long Polling<br/>(WaitTimeSeconds=20)"] --> SQS_STD
    LONG_POLL --> REDUCED["Reduces Empty<br/>Responses"]
    style PROD_SNS fill:#4a8bc2
    style SNS fill:#2d5a7b
    style SQS1 fill:#3a7ca5
    style SQS2 fill:#3a7ca5
    style LAMBDA1 fill:#c73e1d
    style EMAIL fill:#e8912e
    style SQS_STD fill:#6f42c1
    style MAX_THR fill:#3fb950
    style SQS_FIFO fill:#c73e1d
    style ORDER fill:#3a7ca5
    style DEDUP fill:#e8912e
    style VISIBILITY fill:#3fb950
    style DLQ_SQS fill:#c73e1d
    style LONG_POLL fill:#6f42c1
    style REDUCED fill:#3fb950
```

## 📑 Table of Contents

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


- [1. Core Concepts](#1-core-concepts)
- [2. SQS — Standard vs FIFO](#2-sqs--standard-vs-fifo)
- [3. Visibility Timeout](#3-visibility-timeout)
- [4. Dead-Letter Queues](#4-dead-letter-queues)
- [5. Delay Queues & Message Timers](#5-delay-queues--message-timers)
- [6. Large Messages via S3](#6-large-messages-via-s3)
- [7. Short Polling vs Long Polling](#7-short-polling-vs-long-polling)
- [8. Batch Operations & Throughput](#8-batch-operations--throughput)
- [9. FIFO Deduplication & Exactly-Once](#9-fifo-deduplication--exactly-once)
- [10. Consumer Patterns](#10-consumer-patterns)
- [11. SQS Extended Client Library](#11-sqs-extended-client-library)
- [12. SNS — Topics & Subscriptions](#12-sns--topics--subscriptions)
- [13. SNS — Message Filtering](#13-sns--message-filtering)
- [14. SNS — Fan-Out & Durability](#14-sns--fan-out--durability)
- [15. SNS — Delivery Policies & DLQ](#15-sns--delivery-policies--dlq)
- [16. SNS — FIFO Topics](#16-sns--fifo-topics)
- [17. Combined — Fan-Out to SQS](#17-combined--fan-out-to-sqs)
- [18. Combined — SNS+SQS Pub/Sub](#18-combined--snssqs-pubsub)
- [19. Combined — S3 → SNS → SQS](#19-combined--s3--sns--sqs)
- [20. Simplest Mental Model](#20-simplest-mental-model)

---

## 1. Core Concepts

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```mermaid
sequenceDiagram
    participant Client
    participant Component
    participant Result
    Client->>Component: Request
    Component->>Component: Process
    Component-->>Result: Generate
    Result-->>Client: Response
```

| Aspect | SQS | SNS |
|--------|-----|-----|
| Model | Queue (pull) | Topic (push) |
| Retention | 1 min – 14 days | None |
| Persistence | Durable | Transient |
| Ordering | FIFO only | FIFO only |
| Throughput | Standard: unlimited | Regional limits |

### Step-by-Step

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


1. **Producer publishes** message to SNS topic or sends directly to SQS queue
2. **SNS fan-out** distributes message to all subscribed endpoints (SQS, Lambda, HTTP, email)
3. **SQS buffering** queues messages persistently; consumers pull at their own pace
4. **Consumer receives** polls queue, visibility timeout begins (message hidden from others)
5. **Processing** consumer processes message; on success, deletes; on failure, message reappears after timeout
6. **Dead-letter queue** if message fails multiple times (maxReceiveCount), moves to DLQ for investigation

### Code Example

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```python
# Python: SNS Publisher → SQS Consumer via boto3
import boto3
import json
from datetime import datetime

# Setup
sns = boto3.client('sns', region_name='us-east-1')
sqs = boto3.client('sqs', region_name='us-east-1')

# Create queue and topic
queue_resp = sqs.create_queue(QueueName='order-processing')
queue_url = queue_resp['QueueUrl']

topic_resp = sns.create_topic(Name='order-events')
topic_arn = topic_resp['TopicArn']

# Subscribe queue to topic (fan-out)
subscription = sns.subscribe(
    TopicArn=topic_arn,
    Protocol='sqs',
    Endpoint=sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['QueueArn'])['Attributes']['QueueArn']
)

# PRODUCER: Publish to SNS topic
def publish_order_event(order_id, amount, status):
    message = {
        'order_id': order_id,
        'amount': amount,
        'status': status,
        'timestamp': datetime.now().isoformat()
    }
    
    sns.publish(
        TopicArn=topic_arn,
        Subject='Order Status Changed',
        Message=json.dumps(message)
    )
    print(f"Published: {message}")

# CONSUMER: Poll SQS queue
def consume_order_events():
    while True:
        # Long poll with 20s wait (reduces empty responses)
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20,
            VisibilityTimeout=300  # 5-minute timeout for processing
        )
        
        for message in response.get('Messages', []):
            try:
                body = json.loads(json.loads(message['Body'])['Message'])
                print(f"Processing order {body['order_id']}: {body['status']}")
                
                # Simulate processing
                if body['amount'] > 10000:
                    raise Exception("Amount exceeds limit")
                
                # On success, delete message
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
                print(f"Processed and deleted message")
            
            except Exception as e:
                print(f"Error processing: {e}")
                # Message visibility timeout expires, will retry
                # After maxReceiveCount (default 3), moves to DLQ

# Run
publish_order_event('ORD-123', 99.99, 'SHIPPED')
consume_order_events()
```

### Real-World Scenario

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


Shopify's order pipeline uses SNS to fan out OrderCreated events to 12 services: billing, recommendation, notification, analytics, fulfillment, tracking, etc. Each subscribes SQS queue to the topic. When notification service is slow (email API rate-limited), its queue backs up to 500K messages, but other services process normally. After 4 failed delivery attempts, messages move to DLQ; Shopify's ops team reviews manually the next day—zero impact to order flow.

## 2. SQS — Standard vs FIFO

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
┌─────────────────────────┐  ┌────────────────────────┐
│      Standard           │  │        FIFO            │
│  • Best-effort order    │  │  • Strict order        │
│  • At-least-once        │  │  • Exactly-once        │
│  • Unlimited TPS        │  │  • 300 TPS (3000 batch)│
│  • May duplicate        │  │  • No duplicates       │
└─────────────────────────┘  └────────────────────────┘
```

**Standard**: Unlimited throughput, best-effort ordering, at-least-once, occasional duplicates. Use for decoupling, buffering spikes, background jobs.

**FIFO**: 300 TPS (3000 batch), strict ordering, exactly-once. Name must end `.fifo`. Use for banking, orders.

```python
sqs.create_queue(QueueName='my-queue')
sqs.create_queue(QueueName='my-queue.fifo', Attributes={'FifoQueue': 'true', 'ContentBasedDeduplication': 'true'})
```

---

## 3. Visibility Timeout

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
Poll → msg received → timeout starts → process → delete
                                    fail → msg reappears for other consumers
```

**Default**: 30s. **Range**: 0s–12h. **Heartbeat**: `change_message_visibility` extends timeout.

```python
response = sqs.receive_message(QueueUrl=url, VisibilityTimeout=60, MaxNumberOfMessages=10)
for msg in response.get('Messages', []):
    sqs.change_message_visibility(QueueUrl=url, ReceiptHandle=msg['ReceiptHandle'], VisibilityTimeout=60)
    process(msg['Body'])
    sqs.delete_message(QueueUrl=url, ReceiptHandle=msg['ReceiptHandle'])
```

**Rule**: Set to 6× expected processing time. Too short → duplicates. Too long → slow recovery.

---

## 4. Dead-Letter Queues

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
Source → consumer fails → retry × N → DLQ → investigate → redrive
```

**maxReceiveCount**: Messages move to DLQ after N receives. Type must match source.

```python
dlq = sqs.create_queue(QueueName='my-dlq')
dlq_arn = sqs.get_queue_attributes(QueueUrl=dlq['QueueUrl'], AttributeNames=['QueueArn'])['Attributes']['QueueArn']
sqs.create_queue(QueueName='source', Attributes={
    'RedrivePolicy': json.dumps({'deadLetterTargetArn': dlq_arn, 'maxReceiveCount': 5})
})
```

**Redrive**: `sqs.start_message_move_task(SourceArn=dlq_arn)` returns messages after fix.

---

## 5. Delay Queues & Message Timers

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


- **Queue-level DelaySeconds**: 0–900s (all messages delayed)
- **Per-message delay**: 0–900s (Standard only)
- **FIFO**: Queue-level only

```python
sqs.create_queue(QueueName='delayed', Attributes={'DelaySeconds': '60'})
sqs.send_message(QueueUrl=url, MessageBody='slow-task', DelaySeconds=120)
```

---

## 6. Large Messages via S3

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**256 KB limit**. Larger messages use S3: upload payload → send S3 pointer in SQS → consumer fetches.

```python
if len(json.dumps(body)) > 256 * 1024:
    key = f"sqs-msg/{uuid4()}.json"
    s3.put_object(Bucket='bucket', Key=key, Body=json.dumps(body))
    sqs.send_message(QueueUrl=url, MessageBody=json.dumps({'s3Bucket': 'bucket', 's3Key': key}))
else:
    sqs.send_message(QueueUrl=url, MessageBody=json.dumps(body))
```

---

## 7. Short Polling vs Long Polling

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


| Feature | Short Polling | Long Polling |
|---------|--------------|--------------|
| WaitTimeSeconds | 0 | 1–20 |
| Empty responses | Common | Rare |
| Cost | Higher | ~70% less |

**Always use long polling**.

```python
sqs.receive_message(QueueUrl=url, WaitTimeSeconds=20, MaxNumberOfMessages=10)
sqs.set_queue_attributes(QueueUrl=url, Attributes={'ReceiveMessageWaitTimeSeconds': '20'})
```

---

## 8. Batch Operations & Throughput

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


- **SendMessageBatch**: 10 msgs max, 256 KB total
- **DeleteMessageBatch**: 10 max

| Queue Type | Base TPS | With Batching (10) |
|------------|----------|-------------------|
| Standard | Unlimited | Unlimited |
| FIFO send | 300 msg/s | 3,000 msg/s |

```python
sqs.send_message_batch(QueueUrl=url, Entries=[
    {'Id': '1', 'MessageBody': '{"a":1}', 'MessageGroupId': 'g1', 'MessageDeduplicationId': str(uuid4())},
    {'Id': '2', 'MessageBody': '{"a":2}', 'MessageGroupId': 'g1', 'MessageDeduplicationId': str(uuid4())},
])
```

---

## 9. FIFO Deduplication & Exactly-Once

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
Content-Based: SHA-256(body) → Dedup ID
Explicit:      User provides MessageDeduplicationId
Window: 5 minutes within same MessageGroupId
```

```python
sqs.create_queue(QueueName='orders.fifo', Attributes={'FifoQueue': 'true', 'ContentBasedDeduplication': 'true'})
sqs.send_message(QueueUrl=url, MessageBody=json.dumps({'id': '123'}), MessageGroupId='orders', MessageDeduplicationId='order-123-v1')
```

---

## 10. Consumer Patterns

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
SQS ◄── poll ── Worker (EC2/ECS) ──► process + delete
SQS ────────── Lambda event source mapping
```

**Lambda trigger**:
```python
def lambda_handler(event, context):
    failures = []
    for record in event['Records']:
        try:
            process_message(record['body'])
        except Exception:
            failures.append({'itemIdentifier': record['messageId']})
    return {'batchItemFailures': failures}
```

**Best Practices**: Heartbeat via `change_message_visibility`, graceful shutdown.

---

## 11. SQS Extended Client Library

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


Java/.NET SDK extension. Transparently offloads > 256 KB to S3.

```java
ExtendedSqsClient extendedClient = new ExtendedSqsClient.Builder()
    .sqsClient(sqsClient).s3Client(s3Client).payloadBucket("my-large-msgs").build();
extendedClient.sendMessage(SendMessageRequest.builder().queueUrl(url).messageBody(largePayload).build());
```

Python: manual S3 pointer pattern.

---

## 12. SNS — Topics & Subscriptions

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
              ┌─────────┐
              │  Topic  │
              └────┬────┘
     ┌─────────────┼─────────────┐
     │       │         │         │
   SQS    Lambda    HTTP     Email/Firehose
```

**Protocols**: SQS (durable), Lambda (serverless), HTTP/HTTPS (webhooks), Email, SMS, Platform, Firehose.

```python
topic = sns.create_topic(Name='order-events')
sns.subscribe(TopicArn=topic['TopicArn'], Protocol='sqs', Endpoint='arn:aws:sqs:...:queue')
sns.subscribe(TopicArn=topic['TopicArn'], Protocol='lambda', Endpoint='arn:aws:lambda:...:func')
```

**HTTP**: Must confirm subscription within 3 days via `SubscribeURL`.

---

## 13. SNS — Message Filtering

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Attribute-based**: SNS evaluates `MessageAttributes` against `FilterPolicy` on each subscription.

```python
sns.set_subscription_attributes(SubscriptionArn=sub_arn, AttributeName='FilterPolicy',
    AttributeValue=json.dumps({'event': ['order_placed'], 'priority': ['high']}))
sns.set_subscription_attributes(SubscriptionArn=sub_arn, AttributeName='FilterPolicy',
    AttributeValue=json.dumps({'event_type': [{'numeric': ['>', 100]}]}))
```

Publisher sends attributes:
```python
sns.publish(TopicArn=topic_arn, Message=json.dumps({'id': '123'}),
    MessageAttributes={'event': {'DataType': 'String', 'StringValue': 'order_placed'}})
```

---

## 14. SNS — Fan-Out & Durability

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
Producer → SNS Topic ─┬─→ SQS A (audit)
                       ├─→ SQS B (process)
                       ├─→ Lambda (cache)
                       └─→ HTTP (notify)
```

**Durability**: SNS replicates across AZs. SQS: 14-day retention. HTTP: 23 retries. Lambda: 3 retries.

---

## 15. SNS — Delivery Policies & DLQ

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```python
# Delivery policy (HTTP retry behavior)
sns.set_subscription_attributes(SubscriptionArn=sub_arn, AttributeName='DeliveryPolicy',
    AttributeValue=json.dumps({'minDelayTarget': 1, 'maxDelayTarget': 300, 'numRetries': 10}))

# DLQ for failed deliveries
sns.set_subscription_attributes(SubscriptionArn=sub_arn, AttributeName='RedrivePolicy',
    AttributeValue=json.dumps({'deadLetterTargetArn': 'arn:aws:sqs:...:sns-dlq'}))

# Raw message delivery (strip SNS envelope for SQS)
sns.set_subscription_attributes(SubscriptionArn=sub_arn, AttributeName='RawMessageDelivery', AttributeValue='true')
```

---

## 16. SNS — FIFO Topics

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


Topic name `.fifo`. Subscribers: SQS FIFO only. Ordering per `MessageGroupId`.

```python
fifo_topic = sns.create_topic(Name='orders.fifo', Attributes={'FifoTopic': 'true', 'ContentBasedDeduplication': 'true'})
sns.publish(TopicArn=fifo_topic['TopicArn'], Message=json.dumps({'order_id': '123'}),
    MessageGroupId='123', MessageDeduplicationId='dedup-1712345678')
```

**Limits**: 300 TPS (3000 batch) • SQS FIFO only • 5-min dedup window

---

## 17. Combined — Fan-Out to SQS

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```python
sqs.set_queue_attributes(QueueUrl=queue_url, Attributes={'Policy': json.dumps({
    'Version': '2012-10-17',
    'Statement': [{'Effect': 'Allow', 'Principal': {'Service': 'sns.amazonaws.com'},
        'Action': 'sqs:SendMessage', 'Resource': queue_arn,
        'Condition': {'ArnEquals': {'aws:SourceArn': topic_arn}}}]
})})
sub = sns.subscribe(TopicArn=topic_arn, Protocol='sqs', Endpoint=queue_arn)
sns.set_subscription_attributes(SubscriptionArn=sub['SubscriptionArn'], AttributeName='FilterPolicy',
    AttributeValue=json.dumps({'event': ['order_placed']}))
```

---

## 18. Combined — SNS+SQS Pub/Sub

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
┌──────────┐   ┌──────────┐   ┌──────────┐
│Publisher │   │Publisher │   │Publisher │
│Service A │   │Service B │   │Service C │
└─────┬────┘   └─────┬────┘   └────┬─────┘
      │              │              │
      └──────────────┼──────────────┘
                     ▼
              ┌──────────────┐
              │   SNS Topic  │
              └──────┬───────┘
          ┌──────────┴──────────┐
          ▼                     ▼
   ┌────────────┐         ┌────────────┐
   │ SQS Alpha  │         │ SQS Beta   │
   └──────┬─────┘         └──────┬─────┘
          ▼                      ▼
   Consumer A1/A2          Consumer B1/B2
```

**Benefits**: Decoupled publishers. Each team owns their queue.

---

## 19. Combined — S3 → SNS → SQS

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
S3 Upload → S3 Event → SNS Topic → SQS Queue → Consumer
```

```python
s3.put_bucket_notification_configuration(Bucket='source', NotificationConfiguration={
    'TopicConfigurations': [{'TopicArn': topic_arn, 'Events': ['s3:ObjectCreated:*'],
        'Filter': {'Key': {'FilterRules': [{'Name': 'prefix', 'Value': 'uploads/'}]}}}]
})
```

---

## 20. Simplest Mental Model

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
┌───────────────────────────────────────────────────────────┐
│                   SIMPLEST MENTAL MODEL                    │
│                                                           │
│   ┌──────────────────┐    ┌──────────────────┐           │
│   │        📬        │    │        📦        │           │
│   │  SNS = Mailroom  │    │  SQS = PO Box    │           │
│   │  Push to all     │    │  Pull when ready │           │
│   └──────────────────┘    └──────────────────┘           │
│                                                           │
│   SNS + SQS = Mailroom delivers to each PO Box           │
│                                                           │
│   Standard = Best-effort order, may duplicate            │
│   FIFO     = Strict order, no duplicates, slower          │
│   DLQ      = Return to sender after N failed tries        │
│   Long poll = Wait at mailbox for mail to arrive          │
└───────────────────────────────────────────────────────────┘
```

**Key Numbers**: Max msg 256KB • Retention 14d • VisTimeout 12h • FIFO 300 TPS (3000 batch) • Poll 20s • Delay 900s • Batch 10


## Practical Example

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


See code examples above for practical usage patterns.