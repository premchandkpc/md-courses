# DynamoDB Overview

## What is DynamoDB?

DynamoDB is AWS's fully managed NoSQL database service. It's a key-value and document database that provides high performance, scalability, and availability without managing infrastructure.

### Key Characteristics

| Aspect | Feature |
|--------|---------|
| Type | NoSQL - Key-Value & Document |
| Management | Fully managed (AWS) |
| Scaling | Auto-scaling or provisioned capacity |
| Consistency | Eventual or strong (configurable) |
| Throughput | On-demand or provisioned |
| Backup | Continuous, point-in-time recovery |
| Global | Global tables for multi-region |

---

## Why DynamoDB?

### Advantages

**1. Fully Managed**
- No server provisioning
- Automatic backups
- Patch management handled by AWS

**2. Scalability**
- Handles millions of requests/second
- Scales horizontally automatically
- No downtime during scaling

**3. Performance**
- Single-digit millisecond latency
- Consistent performance at any scale
- Automatic optimization

**4. Availability**
- Multi-AZ replication
- 99.99% uptime SLA
- Automatic failover

**5. Cost Efficiency**
- Pay per request (on-demand)
- Or provisioned capacity (predictable)
- No over-provisioning needed

---

## When to Use DynamoDB

### Good Fit ✓
- Mobile and web apps
- IoT applications
- Real-time analytics
- Session storage
- Leaderboards and rankings
- Content metadata
- User profiles
- Chat applications
- Gaming backends
- Catalog systems

### Not Ideal ✗
- Complex joins across many tables
- Complex transactions (>10 items)
- Large aggregations (GROUP BY)
- Strongly consistent reads required always
- Complex reporting queries
- ACID across multiple entities

---

## Architecture

```
Application Layer
       ↓
DynamoDB API (SDK)
       ↓
Partition Layer (Distributed)
├── Partition 1 → 3-way Replication
├── Partition 2 → 3-way Replication
└── Partition N → 3-way Replication
```

---

## Billing Models

### On-Demand
- Per read/write unit consumed
- Auto-scales instantly
- Ideal for unpredictable workloads
- More expensive at high volume

### Provisioned
- Fixed capacity units per second
- Must forecast traffic
- Cheaper at predictable high volume
- Auto-scaling available

### Example Costs
```
On-Demand:
- $1.25 per million read units
- $6.25 per million write units

Provisioned (us-east-1):
- Read: $0.00013 per RCU-hour
- Write: $0.00065 per WCU-hour
```

---

## Basic Concepts

| Term | Meaning |
|------|---------|
| **Table** | Collection of items (like a relation) |
| **Item** | Single record (like a row) |
| **Attribute** | Field in an item (like a column) |
| **Partition Key** | Primary key for distribution |
| **Sort Key** | Secondary key for ordering |
| **RCU** | 1 KB read capacity unit |
| **WCU** | 1 KB write capacity unit |

---

## Data Types Supported

- **Scalar**: String (S), Number (N), Binary (B), Boolean (BOOL), Null
- **Document**: Map (M), List (L)
- **Set**: String Set (SS), Number Set (NS), Binary Set (BS)
- **TTL**: Time-to-live expiration

Example:
```json
{
  "userId": "user123",
  "name": "John Doe",
  "age": 30,
  "email": "john@example.com",
  "addresses": [
    {
      "street": "123 Main St",
      "city": "Boston"
    }
  ],
  "tags": ["premium", "verified"]
}
```

---

## Basic Operations

### Create (PutItem)
```python
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Users')

table.put_item(Item={
    'userId': 'user123',
    'name': 'John Doe',
    'age': 30,
    'email': 'john@example.com'
})
```

### Read (GetItem)
```python
response = table.get_item(Key={'userId': 'user123'})
item = response.get('Item')
```

### Update (UpdateItem)
```python
table.update_item(
    Key={'userId': 'user123'},
    UpdateExpression='SET #a = :val',
    ExpressionAttributeNames={'#a': 'age'},
    ExpressionAttributeValues={':val': 31}
)
```

### Delete (DeleteItem)
```python
table.delete_item(Key={'userId': 'user123'})
```

---

## Read Consistency Options

### Eventually Consistent (Default)
- Reads from any replica
- May return stale data
- ~50% cheaper
- Typical delay: <1 second

### Strongly Consistent
- Reads from primary replica
- Always latest data
- Double RCU cost
- Use for critical operations

Example:
```python
# Strongly consistent read
response = table.get_item(
    Key={'userId': 'user123'},
    ConsistentRead=True
)
```

---

## Comparison: DynamoDB vs SQL

| Aspect | DynamoDB | SQL (RDS) |
|--------|----------|-----------|
| Schema | Flexible | Rigid |
| Queries | Key lookup, scan | Complex joins |
| Scaling | Horizontal | Vertical |
| Cost | Predictable | Per instance |
| Latency | <10ms typical | Variable |
| Transactions | Limited (10 items max) | Full ACID |

---

## Summary

- **Fully managed** NoSQL service by AWS
- **Scales automatically** to any throughput
- **Single-digit latency** at any scale
- **Two pricing models**: on-demand or provisioned
- **Best for**: Key-based lookups, mobile apps, real-time systems
- **Not for**: Complex queries, heavy joins, strong ACID needs
- **Billing**: Pay per request or per capacity unit-hour

Next: [[02-tables.md|Table Design & Creation]]
