# DynamoDB Concurrency & Conflict Resolution

## Optimistic Locking (Version Numbers)

Prevent overwriting unintended changes in concurrent updates.

### Problem: Lost Updates

```python
# Two clients reading same item
client1_reads: balance = 100
client2_reads: balance = 100

# Both try to update
client1_update: balance = 100 - 50 = 50
client2_update: balance = 100 + 25 = 125

# Result: One update is lost!
# (Last write wins, but earlier update forgotten)
```

### Solution: Version Numbers

```python
# Item stored with version
table.put_item(Item={
    'accountId': 'acc123',
    'balance': 100,
    'version': 1
})

# Client 1 reads
response = table.get_item(Key={'accountId': 'acc123'})
balance, version = 100, 1

# Client 2 reads (same time)
response = table.get_item(Key={'accountId': 'acc123'})
balance2, version2 = 100, 1

# Client 1 updates (succeeds)
table.update_item(
    Key={'accountId': 'acc123'},
    UpdateExpression='SET balance = :new, #v = :newv',
    ConditionExpression='#v = :oldv',  # version check
    ExpressionAttributeNames={'#v': 'version'},
    ExpressionAttributeValues={
        ':new': 50,
        ':newv': 2,
        ':oldv': 1
    }
)

# Client 2 tries update (FAILS - version mismatch)
table.update_item(
    Key={'accountId': 'acc123'},
    UpdateExpression='SET balance = :new, #v = :newv',
    ConditionExpression='#v = :oldv',
    ExpressionAttributeNames={'#v': 'version'},
    ExpressionAttributeValues={
        ':new': 125,
        ':newv': 2,
        ':oldv': 1  # ← Now version is 2, not 1!
    }
)
# Raises: ConditionalCheckFailedException

# Client 2 must retry: reread, recalculate, update
```

---

## Pessimistic Locking (Leases)

Prevent concurrent access by claiming exclusive access temporarily.

### Implementation

```python
import time

def lock_item(table, item_id, duration_seconds=30):
    """Acquire exclusive lock on item"""
    lock_id = str(uuid.uuid4())
    lock_expires = int(time.time()) + duration_seconds
    
    try:
        table.update_item(
            Key={'itemId': item_id},
            UpdateExpression='SET lockId = :lid, lockExpires = :exp',
            ConditionExpression='attribute_not_exists(lockId) OR lockExpires < :now',
            ExpressionAttributeValues={
                ':lid': lock_id,
                ':exp': lock_expires,
                ':now': int(time.time())
            }
        )
        return lock_id
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise Exception("Item is locked by another process")
        raise

def unlock_item(table, item_id, lock_id):
    """Release lock if still owned by us"""
    table.update_item(
        Key={'itemId': item_id},
        UpdateExpression='REMOVE lockId, lockExpires',
        ConditionExpression='lockId = :lid',
        ExpressionAttributeValues={':lid': lock_id}
    )

def critical_section(table, item_id):
    """Exclusive access to item"""
    lock_id = lock_item(table, item_id)
    try:
        # Do exclusive work
        response = table.get_item(Key={'itemId': item_id})
        # Modify item...
        table.update_item(Key={'itemId': item_id}, ...)
    finally:
        unlock_item(table, item_id, lock_id)
```

### Deadlock Prevention

```python
# ❌ Bad: Can deadlock
lock_item(table, item1)
lock_item(table, item2)  # If another process locked in opposite order

# ✓ Good: Lock in consistent order (sorted)
items_to_lock = sorted([item1, item2])
for item in items_to_lock:
    lock_item(table, item)
```

---

## Atomic Counters

Safe increment without explicit locking.

### Using ADD

```python
# Atomic increment
table.update_item(
    Key={'metricId': 'pageviews'},
    UpdateExpression='ADD count :inc',
    ExpressionAttributeValues={':inc': 1}
)

# Multiple concurrent updates automatically serialized
# Result is always consistent
```

### Distributed Counters (Sharding)

For very high-volume counters, shard across multiple items:

```python
import random

def increment_counter(table, counter_name, shards=10):
    """Increment counter across random shard (reduces hot partition)"""
    shard = random.randint(0, shards - 1)
    shard_id = f"{counter_name}#{shard}"
    
    table.update_item(
        Key={'counterId': shard_id},
        UpdateExpression='ADD count :inc',
        ExpressionAttributeValues={':inc': 1}
    )

def get_counter(table, counter_name, shards=10):
    """Get total across all shards"""
    total = 0
    for shard in range(shards):
        shard_id = f"{counter_name}#{shard}"
        response = table.get_item(Key={'counterId': shard_id})
        if 'Item' in response:
            total += response['Item'].get('count', 0)
    return total
```

---

## Transactions Across Distributions

DynamoDB transactions are limited to 10 items. For larger distributed transactions, use idempotent writes:

```python
import hashlib

def idempotent_write(table, item, idempotency_key):
    """Write item only if key not seen before"""
    key_hash = hashlib.sha256(idempotency_key.encode()).hexdigest()
    
    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(#idk)',
            ExpressionAttributeNames={'#idk': 'idempotencyKey'},
        )
        # Mark as seen
        table.update_item(
            Key={'idempotencyKey': key_hash},
            UpdateExpression='SET processedAt = :now',
            ExpressionAttributeValues={':now': int(time.time())}
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # Already processed, safe to ignore
            pass
        else:
            raise
```

---

## Consistency Levels

### Eventually Consistent (Default)

```python
# Read may return stale data
response = table.get_item(Key={'userId': 'user123'})
# Might read from replica that hasn't replicated yet
# ~50% cheaper RCU
```

**Use for:**
- User profiles
- Session data
- Analytics
- Caching

### Strongly Consistent

```python
# Always reads from primary
response = table.get_item(
    Key={'userId': 'user123'},
    ConsistentRead=True
)
# Always latest data
# Double RCU cost
```

**Use for:**
- Financial transactions
- Inventory (stock levels)
- Critical updates
- Order processing

### What Happens Between?

```
Write to Primary → Replicated to Replica A, B
↓
Eventually Consistent Read from Replica A (might miss latest)
↓
Strongly Consistent Read from Primary (always latest)
```

---

## Real-World Patterns

### Pattern: Optimistic Locking for User Updates

```python
def update_user_profile(user_id, new_email, expected_version):
    try:
        table.update_item(
            Key={'userId': user_id},
            UpdateExpression='SET email = :email, #v = #v + :inc',
            ConditionExpression='#v = :ev',
            ExpressionAttributeNames={'#v': 'version'},
            ExpressionAttributeValues={
                ':email': new_email,
                ':inc': 1,
                ':ev': expected_version
            },
            ReturnValues='ALL_NEW'
        )
        return True  # Success
    except ClientError as e:
        if 'ConditionalCheckFailedException' in str(e):
            return False  # Version mismatch, retry needed
        raise
```

### Pattern: Distributed Counter for Leaderboard

```python
def increment_score(player_id, points, leaderboard_id, shards=50):
    shard = hash(player_id) % shards
    
    # Atomic increment in sharded counter
    table.update_item(
        Key={'leaderboardId': leaderboard_id, 'shardId': shard},
        UpdateExpression='ADD scores :val SET lastUpdated = :now',
        ExpressionAttributeValues={
            ':val': points,
            ':now': int(time.time())
        }
    )
```

---

## Concurrency Best Practices

| Pattern | Use Case | Consistency |
|---------|----------|-------------|
| Optimistic Locking | Collaborative edits | Eventual |
| Pessimistic Locking | Mutual exclusion | Strong |
| Atomic ADD | Counters | Strong |
| Transactions | Multi-item atomic | Strong (10 items max) |
| Idempotent Keys | Duplicate prevention | Eventual |

---

## Summary

- **Optimistic:** Version numbers for conflict detection
- **Pessimistic:** Locks/leases for exclusive access
- **Atomic:** Use ADD for safe counter increments
- **Sharding:** Distribute counters to avoid hot partitions
- **Consistency:** Choose based on data criticality
- **Idempotency:** Key for distributed reliability

Next: [[../05-optimization/01-performance-tuning.md|Performance Tuning]]
