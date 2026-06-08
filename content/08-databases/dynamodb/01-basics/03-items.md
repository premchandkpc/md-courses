---
title: DynamoDB Item Operations
topic: 08-databases
difficulty: intermediate
time: 30m
paths:
  - backend-junior
  - data
  - backend-senior
---

# DynamoDB Item Operations

## CRUD Operations

### Create (PutItem)

Insert new item or overwrite existing.

```python
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('Users')

# Simple put
table.put_item(Item={
    'userId': 'user123',
    'name': 'John Doe',
    'email': 'john@example.com',
    'age': 30
})

# With TTL (expires Jan 1, 2026)
table.put_item(Item={
    'userId': 'session_abc',
    'sessionData': 'some_token',
    'expirationTime': 1767225600  # Unix timestamp
})
```

**Costs:**
- Item ≤ 1KB: 1 WCU
- Item 5KB: 5 WCU
- Item 10.5KB: 11 WCU

### Read (GetItem)

Fetch single item by key.

```python
# Eventually consistent (default, 50% cheaper)
response = table.get_item(
    Key={'userId': 'user123'}
)
item = response.get('Item')

# Strongly consistent (latest data guaranteed)
response = table.get_item(
    Key={'userId': 'user123'},
    ConsistentRead=True
)

# Get specific attributes only
response = table.get_item(
    Key={'userId': 'user123'},
    ProjectionExpression='name, email'
)
```

**Costs:**
- 1 RCU per 4KB (eventually consistent)
- 1 RCU per 4KB (strongly consistent, not 2x)
- ProjectionExpression doesn't reduce cost

### Update (UpdateItem)

Modify existing item without replacing entire item.

```python
# Add attribute
table.update_item(
    Key={'userId': 'user123'},
    UpdateExpression='SET email = :email',
    ExpressionAttributeValues={':email': 'newemail@example.com'}
)

# Increment counter
table.update_item(
    Key={'userId': 'user123'},
    UpdateExpression='SET loginCount = if_not_exists(loginCount, :zero) + :inc',
    ExpressionAttributeValues={
        ':zero': 0,
        ':inc': 1
    }
)

# Add item to list
table.update_item(
    Key={'userId': 'user123'},
    UpdateExpression='SET tags = list_append(if_not_exists(tags, :empty), :newtag)',
    ExpressionAttributeValues={
        ':empty': [],
        ':newtag': ['premium']
    }
)

# Remove attribute
table.update_item(
    Key={'userId': 'user123'},
    UpdateExpression='REMOVE lastLogin'
)

# Conditional update
table.update_item(
    Key={'userId': 'user123'},
    UpdateExpression='SET #a = :newage',
    ConditionExpression='#a < :maxage',
    ExpressionAttributeNames={'#a': 'age'},
    ExpressionAttributeValues={
        ':newage': 35,
        ':maxage': 50
    }
)
```

### Delete (DeleteItem)

Remove item from table.

```python
# Simple delete
table.delete_item(Key={'userId': 'user123'})

# Conditional delete
table.delete_item(
    Key={'userId': 'user123'},
    ConditionExpression='#s = :status',
    ExpressionAttributeNames={'#s': 'status'},
    ExpressionAttributeValues={':status': 'inactive'}
)

# Get item before deletion
response = table.delete_item(
    Key={'userId': 'user123'},
    ReturnValues='ALL_OLD'  # Returns deleted item
)
```

---

## Batch Operations

### BatchGetItem

Read multiple items efficiently (up to 16MB, 100 items).

```python
# Batch read
response = dynamodb.batch_get_item(
    RequestItems={
        'Users': {
            'Keys': [
                {'userId': 'user123'},
                {'userId': 'user456'},
                {'userId': 'user789'}
            ]
        }
    }
)

items = response['Responses']['Users']
```

**Advantages:**
- 33% cheaper than individual requests
- Parallel reads under hood
- Handles partial failures gracefully

### BatchWriteItem

Write/delete multiple items (up to 16MB, 25 items).

```python
# Batch write
dynamodb.batch_write_item(
    RequestItems={
        'Users': [
            {
                'PutRequest': {
                    'Item': {'userId': 'user001', 'name': 'Alice'}
                }
            },
            {
                'PutRequest': {
                    'Item': {'userId': 'user002', 'name': 'Bob'}
                }
            },
            {
                'DeleteRequest': {
                    'Key': {'userId': 'user999'}
                }
            }
        ]
    }
)
```

---

## Transactions (All-or-Nothing)

### TransactWriteItems

Multiple operations succeed or all fail (up to 10 items, 4MB).

```python
# Atomic transfer (debit account A, credit account B)
dynamodb.transact_write_items(
    TransactItems=[
        {
            'Update': {
                'TableName': 'Accounts',
                'Key': {'accountId': 'acc123'},
                'UpdateExpression': 'SET balance = balance - :amount',
                'ExpressionAttributeValues': {':amount': 100}
            }
        },
        {
            'Update': {
                'TableName': 'Accounts',
                'Key': {'accountId': 'acc456'},
                'UpdateExpression': 'SET balance = balance + :amount',
                'ExpressionAttributeValues': {':amount': 100}
            }
        }
    ]
)
```

### TransactGetItems

Strongly consistent read of multiple items.

```python
response = dynamodb.transact_get_items(
    TransactItems=[
        {'Get': {'TableName': 'Users', 'Key': {'userId': 'user123'}}},
        {'Get': {'TableName': 'Orders', 'Key': {'orderId': 'order456'}}}
    ]
)

results = response['Responses']
```

---

## Query: Fetch Multiple Items from Partition

Use partition key + optional sort key conditions.

### Simple Query

```python
# All posts by user123
response = table.query(
    KeyConditionExpression='userId = :uid',
    ExpressionAttributeValues={':uid': 'user123'}
)
```

### Range Query

```python
# Posts created in January 2026
response = table.query(
    KeyConditionExpression='userId = :uid AND createdDate BETWEEN :d1 AND :d2',
    ExpressionAttributeValues={
        ':uid': 'user123',
        ':d1': '2026-01-01',
        ':d2': '2026-01-31'
    }
)
```

### Pagination

```python
# First 10 items
response = table.query(
    KeyConditionExpression='userId = :uid',
    ExpressionAttributeValues={':uid': 'user123'},
    Limit=10
)

items = response['Items']
last_key = response.get('LastEvaluatedKey')

# Next 10 items
if last_key:
    response = table.query(
        KeyConditionExpression='userId = :uid',
        ExpressionAttributeValues={':uid': 'user123'},
        Limit=10,
        ExclusiveStartKey=last_key
    )
```

### Reverse Order

```python
# Posts in reverse date order
response = table.query(
    KeyConditionExpression='userId = :uid',
    ExpressionAttributeValues={':uid': 'user123'},
    ScanIndexForward=False  # Descending order
)
```

**Cost:** RCU = items scanned (not returned) / 4KB

---

## Scan: Full Table Scan

Read all items (expensive, avoid in production).

```python
# Scan entire table
response = table.scan()

# With filter (reduces results, not cost)
response = table.scan(
    FilterExpression='#s = :status',
    ExpressionAttributeNames={'#s': 'status'},
    ExpressionAttributeValues={':status': 'active'}
)

# Pagination
while True:
    items = response['Items']
    
    if 'LastEvaluatedKey' not in response:
        break
    
    response = table.scan(
        ExclusiveStartKey=response['LastEvaluatedKey']
    )
```

**Cost:** RCU = all scanned items / 4KB (regardless of FilterExpression)

**When to use:**
- Import/export entire table
- Initial data load
- Rare analytics queries
- Never for application queries

---

## Expression Syntax

### UpdateExpression Actions

| Action | Example |
|--------|---------|
| SET | `SET age = :val, #n = :name` |
| ADD | `ADD loginCount :inc` (increment) |
| REMOVE | `REMOVE lastLogin` |
| DELETE | `DELETE tags :val` (remove from set) |

### ConditionExpression

```python
# Only update if age < 50
ConditionExpression='age < :max'

# Only if attribute exists
ConditionExpression='attribute_exists(email)'

# Only if attribute doesn't exist
ConditionExpression='attribute_not_exists(bannedDate)'

# Only if value equals something
ConditionExpression='#s = :expected'

# Complex conditions
ConditionExpression='age > :min AND age < :max'
```

---

## Real-World Examples

### Leaderboard Score Update

```python
table.update_item(
    Key={'gameId': 'game123', 'playerId': 'player456'},
    UpdateExpression='SET score = :newscore, lastUpdated = :now',
    ConditionExpression='attribute_not_exists(score) OR score < :newscore',
    ExpressionAttributeValues={
        ':newscore': 9500,
        ':now': int(time.time())
    },
    ReturnValues='ALL_NEW'  # Return updated item
)
```

### Session Management

```python
# Store session with 1-hour expiration
ttl_timestamp = int(time.time()) + 3600

table.put_item(Item={
    'sessionId': 'sess_abc123',
    'userId': 'user456',
    'tokens': ['token1', 'token2'],
    'expirationTime': ttl_timestamp
})
```

### Comment Counter

```python
# Increment comment count atomically
table.update_item(
    Key={'postId': 'post123'},
    UpdateExpression='SET #cc = if_not_exists(#cc, :zero) + :inc',
    ExpressionAttributeNames={'#cc': 'commentCount'},
    ExpressionAttributeValues={
        ':zero': 0,
        ':inc': 1
    }
)
```

---

## Performance Tips

| Operation | Cost Optimization |
|-----------|------------------|
| GetItem | Use eventually consistent reads (50% cheaper) |
| Query | Use sort key to limit scan range |
| Batch* | Prefer BatchGetItem over individual reads |
| Update | Use conditional updates to avoid failures |
| Scan | Avoid in production (use Query + GSI) |
| Projection | Include only needed attributes |

---

## Summary

- **CRUD**: PutItem, GetItem, UpdateItem, DeleteItem
- **Batch**: BatchGetItem, BatchWriteItem (33% cheaper)
- **Transactions**: TransactWriteItems, TransactGetItems (all-or-nothing)
- **Query**: Fast, uses partition + sort key
- **Scan**: Slow, reads entire table (avoid!)
- **Expression**: SET, ADD, REMOVE, DELETE, ConditionExpression

Next: [[../02-intermediate/01-advanced-queries.md|Advanced Queries & Filters]]
