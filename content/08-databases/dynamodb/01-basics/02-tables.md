---
title: DynamoDB Table Design & Creation
topic: 08-databases
difficulty: intermediate
time: 30m
paths:
  - backend-junior
  - data
  - backend-senior
---

# DynamoDB Table Design & Creation

## Table Fundamentals

A DynamoDB table is a collection of items (records). Each table has:
- **Partition Key** (required) - distributes data across partitions
- **Sort Key** (optional) - orders items within a partition
- **Attributes** - flexibly typed data fields
- **TTL** - optional automatic expiration

---

## Partition Key (Primary Key)

Distributes data evenly across partitions for scalability.

### Single Partition Key
```
Table: Users
Partition Key: userId

Items:
user123 → {name: "John", email: "john@example.com"}
user456 → {name: "Jane", email: "jane@example.com"}
```

**Rules:**
- Must be unique across table
- Cannot be changed after table creation
- Should have high cardinality (many distinct values)
- Distributes evenly for balanced partitions

---

## Composite Primary Key (Partition + Sort Key)

Enables complex queries and multiple items per partition.

### Pattern: User Posts
```
Table: UserPosts
Partition Key: userId
Sort Key: postId

Items:
user123 | post001 → {title: "Hello World", created: "2026-01-01"}
user123 | post002 → {title: "DynamoDB Tips", created: "2026-01-02"}
user456 | post001 → {title: "AWS Guide", created: "2026-01-03"}
```

**Benefits:**
- Multiple items per partition key
- Query within range (postId between X and Y)
- Order results by sort key
- Atomic batch operations

### Pattern: Time Series Data
```
Table: Metrics
Partition Key: serverId
Sort Key: timestamp

Items:
server001 | 2026-01-01T10:00:00 → {cpu: 45, memory: 70}
server001 | 2026-01-01T10:01:00 → {cpu: 48, memory: 72}
server001 | 2026-01-01T10:02:00 → {cpu: 50, memory: 75}
```

Query all metrics for server001 between timestamps efficiently.

---

## Designing Primary Keys

### Anti-Patterns to Avoid

**❌ Bad: Low Cardinality**
```python
# Partition Key: status (only "active", "inactive")
# Result: Hot partitions, uneven distribution
```

**❌ Bad: Sequential IDs**
```python
# Partition Key: userId = 1, 2, 3...
# Result: New data goes to one partition, causing hot partition
```

**❌ Bad: Timestamps as Partition Key**
```python
# Partition Key: date (only today's value)
# Result: All writes today go to one partition
```

### ✓ Good: High Cardinality

```python
# Partition Key: userId (millions of distinct values)
# Distributed evenly across partitions
```

```python
# Partition Key: email
# Partition Key + Sort Key: productId, timestamp
# Good distribution + flexible queries
```

---

## Creating Tables

### AWS SDK (Python - Boto3)

```python
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Create table with on-demand billing
table = dynamodb.create_table(
    TableName='Users',
    KeySchema=[
        {'AttributeName': 'userId', 'KeyType': 'HASH'},  # Partition Key
        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}  # Sort Key
    ],
    AttributeDefinitions=[
        {'AttributeName': 'userId', 'AttributeType': 'S'},  # String
        {'AttributeName': 'timestamp', 'AttributeType': 'N'}  # Number
    ],
    BillingMode='PAY_PER_REQUEST'  # On-demand
)
```

### Provisioned Capacity

```python
table = dynamodb.create_table(
    TableName='Users',
    KeySchema=[
        {'AttributeName': 'userId', 'KeyType': 'HASH'}
    ],
    AttributeDefinitions=[
        {'AttributeName': 'userId', 'AttributeType': 'S'}
    ],
    BillingMode='PROVISIONED',
    ProvisionedThroughputCapacity={
        'ReadCapacityUnits': 100,
        'WriteCapacityUnits': 100
    }
)
```

### CloudFormation (Infrastructure as Code)

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  UsersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: Users
      AttributeDefinitions:
        - AttributeName: userId
          AttributeType: S
        - AttributeName: email
          AttributeType: S
      KeySchema:
        - AttributeName: userId
          KeyType: HASH
        - AttributeName: email
          KeyType: RANGE
      BillingMode: PAY_PER_REQUEST
      StreamSpecification:
        StreamViewType: NEW_AND_OLD_IMAGES
```

---

## Global Secondary Indexes (GSI)

Query tables by non-key attributes.

### Example: Query by Email

```python
# Main table: Partition Key = userId
# Want to: Find user by email

# Solution: Add GSI with email as partition key

table.create_global_secondary_index(
    GlobalSecondaryIndexName='EmailIndex',
    KeySchema=[
        {'AttributeName': 'email', 'KeyType': 'HASH'}
    ],
    Projection={
        'ProjectionType': 'ALL'  # Include all attributes
    },
    ProvisionedThroughputCapacity={
        'ReadCapacityUnits': 50,
        'WriteCapacityUnits': 50
    }
)

# Query by email
response = table.query(
    IndexName='EmailIndex',
    KeyConditionExpression='email = :email',
    ExpressionAttributeValues={':email': 'john@example.com'}
)
```

### GSI vs Main Table

| Aspect | Main Table | GSI |
|--------|-----------|-----|
| Partition Key | Fixed | Flexible |
| Updates | Immediate | Eventually consistent |
| Throughput | Shared | Separate |
| Cost | Included | Additional |
| Size Limit | 10GB | Unlimited |

---

## Local Secondary Indexes (LSI)

Alternate sort key for same partition key.

```python
# When creating table, add LSI:
table = dynamodb.create_table(
    TableName='Orders',
    KeySchema=[
        {'AttributeName': 'customerId', 'KeyType': 'HASH'},
        {'AttributeName': 'orderId', 'KeyType': 'RANGE'}
    ],
    LocalSecondaryIndexes=[
        {
            'IndexName': 'OrderDateIndex',
            'KeySchema': [
                {'AttributeName': 'customerId', 'KeyType': 'HASH'},
                {'AttributeName': 'orderDate', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'}
        }
    ]
)

# Query by date instead of orderId
response = table.query(
    IndexName='OrderDateIndex',
    KeyConditionExpression='customerId = :cid AND orderDate BETWEEN :d1 AND :d2',
    ExpressionAttributeValues={
        ':cid': 'cust123',
        ':d1': '2026-01-01',
        ':d2': '2026-01-31'
    }
)
```

### LSI Constraints

- Must be created at table creation (cannot add later)
- 10GB size limit per partition key
- Shares throughput with main table
- Use for data with strong range patterns

---

## Table Settings

### Point-in-Time Recovery (PITR)
```python
dynamodb_client = boto3.client('dynamodb')

dynamodb_client.update_continuous_backups(
    TableName='Users',
    PointInTimeRecoverySpecification={
        'PointInTimeRecoveryEnabled': True
    }
)
```

### Streams (Capture Changes)
```python
table = dynamodb.create_table(
    TableName='Users',
    StreamSpecification={
        'StreamViewType': 'NEW_AND_OLD_IMAGES'  # Capture before/after
    }
)
```

### TTL (Auto-Expiration)
```python
table.ttl.enable(Attribute='expirationTime')

# Item expires automatically at this Unix timestamp
table.put_item(Item={
    'userId': 'user123',
    'name': 'John',
    'expirationTime': 1735689600  # Jan 1, 2025
})
```

---

## Table Capacity Planning

### Estimating Throughput

**RCU Calculation:**
```
One RCU = One 4KB read per second (strongly consistent)
          OR Two 4KB reads per second (eventually consistent)

Example: Read 1KB item → costs 1 RCU
         Read 5KB item → costs 2 RCU (rounded up to 4KB block)
```

**WCU Calculation:**
```
One WCU = One 1KB write per second

Example: Write 1KB item → costs 1 WCU
         Write 2.5KB item → costs 3 WCU (rounded up to 1KB blocks)
```

### Example: E-commerce Site
```
Expected traffic: 1000 reads/sec, 100 writes/sec
Item size: ~2KB average

RCU needed: 1000 reads × 1 RCU (per 4KB) = 1000 RCU
WCU needed: 100 writes × 2 WCU (per 2KB) = 200 WCU

Total monthly: ~$3,000 (estimate)
```

---

## Summary

- **Partition Key**: Distributes data, must be high cardinality
- **Sort Key**: Enables range queries within partition
- **GSI**: Query alternate attributes, separate throughput
- **LSI**: Alternate sort key, created at table time, shares throughput
- **Billing**: Choose on-demand or provisioned based on traffic patterns
- **PITR**: Enable for production tables
- **Streams**: Enable if you need change data capture

Next: [[03-items.md|Item Operations & Queries]]
