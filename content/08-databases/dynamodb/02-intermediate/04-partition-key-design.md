---
title: DynamoDB Partition Key Design: Avoiding Hot Partitions
topic: 08-databases
difficulty: intermediate
time: 30m
paths:
  - backend-junior
  - data
  - backend-senior
---

# DynamoDB Partition Key Design: Avoiding Hot Partitions

## Partition Key Fundamentals

### How DynamoDB Distributes Data

```
Partition key determines:
1. Which partition stores item
2. How data distributed across nodes
3. Maximum write throughput per partition (40KB/sec)

Example: table with 100GB data, 10 partitions = 10GB per partition
Each partition: 1 node, 40KB/sec write capacity
```

## Bad Partition Keys (The Biggest Mistakes)

### Mistake 1: Sequential Timestamp as PK

```python
# ❌ BAD: Partition key = created_at (timestamp)
# All writes go to LATEST timestamp = HOT partition

def create_order(order_data):
    timestamp = datetime.now()  # e.g., 2025-05-29 14:30:45
    dynamodb.put_item(
        TableName='orders',
        Item={
            'created_at': {'N': str(int(timestamp.timestamp()))},
            'order_id': {'S': str(uuid4())},
            'data': {'S': json.dumps(order_data)}
        }
    )
    # All orders at timestamp 14:30:45 → SAME partition
    # Partition 1: timestamp 14:30:00 (empty, unused)
    # Partition 2: timestamp 14:30:30 (20% traffic)
    # Partition 3: timestamp 14:30:45 (80% traffic) ← HOT!
    # Partition 4: timestamp 14:31:00 (cold, unused)

# Result: ONE partition gets 100% of writes
# Peak: 40KB/sec cap on entire table = BOTTLENECK
# Cluster: 4 nodes, but 1 maxed, 3 idle (waste)

# Solution: Use UUID or hash
```

### Mistake 2: Low-Cardinality Partition Key (Status)

```python
# ❌ BAD: Partition key = status (only 4 values)
dynamodb.put_item(
    TableName='orders',
    Item={
        'status': {'S': 'pending'},  # Only: pending, processing, shipped, cancelled
        'order_id': {'S': str(uuid4())},
    }
)

# Data distribution:
# Partition for status='pending': 1B items (90% of table) → JUMBO CHUNK
# Partition for status='processing': 50M items (5%)
# Partition for status='shipped': 50M items (5%)

# Problem: 
# - Cannot split jumbo partition (capacity planning broken)
# - All writes to pending → ALL bottleneck on one partition
# - Even with 10 partitions, 1 might exceed storage limit
```

### Mistake 3: Uneven Cardinality (Popular Customers)

```python
# ❌ BAD: Partition key = customer_id
# Some customers have 1M orders, some have 10

customer_orders = {
    'customer_1': 1_000_000,   # Popular customer
    'customer_2': 500_000,
    'customer_3': 10,          # Niche customer
}

# Data distribution:
# Partition 1 (customer_1): 1M orders, maybe > 10GB (HOT)
# Partition 2 (customer_2): 500K orders
# Partition 3-N: small customers
# Result: SKEWED distribution, hot partitions

# Peak traffic: customer_1 gets 10K orders/min
# Partition 1: 10K writes/min = 166 writes/sec
# Capacity: 40KB/sec = ~400 writes/sec of 100 byte orders
# Utilization: 166/400 = 42% one partition, 0% others
```

---

## Good Partition Key Design

### Strategy 1: UUID-Based (Uniform Distribution)

```python
# ✅ GOOD: Partition key = UUID
dynamodb.put_item(
    TableName='orders',
    Item={
        'order_id': {'S': str(uuid4())},  # e.g., 550e8400-e29b-41d4-a716-446655440000
        'customer_id': {'S': customer_id},  # In sort key
        'created_at': {'N': str(int(timestamp.timestamp()))}
    }
)

# Data distribution: Uniform
# UUID space: 2^128 ≈ 3.4 × 10^38 possibilities
# DynamoDB: Auto-hashes UUID into partitions
# Result: Each partition gets ~25% of writes (with 4 partitions)

# Performance:
# - Write throughput: LINEAR with partitions (scales!)
# - Hot partitions: None (even distribution)
# - Query routing: Write = single partition, Read = single partition

# Trade-off: Range queries on order_id impossible
# Solution: Use sort key for customer_id (read by customer_id)
```

### Strategy 2: Compound Key (Locality + Distribution)

```python
# ✅ GOOD: Partition key = customer_id, Sort key = created_at
dynamodb.put_item(
    TableName='orders',
    Item={
        'customer_id': {'S': customer_id},  # Partition key
        'created_at': {'N': str(int(timestamp.timestamp()))},  # Sort key
        'order_data': {'S': json.dumps(data)}
    }
)

# Data distribution: By customer (some skew if customers uneven)
# But: Each customer's orders on SAME partition → locality good!

# Query patterns:
# Q1: "All orders for customer X" → Single partition lookup (fast)
dynamodb.query(
    TableName='orders',
    KeyConditionExpression='customer_id = :cid',
    ExpressionAttributeValues={':cid': {'S': customer_id}},
    ScanIndexForward=False,  # Newest first (uses sort key order)
    Limit=20
)
# Latency: 5-10ms (single partition)

# Q2: "Orders for customer X since date Y" → Efficient range
dynamodb.query(
    TableName='orders',
    KeyConditionExpression='customer_id = :cid AND created_at > :date',
    ExpressionAttributeValues={
        ':cid': {'S': customer_id},
        ':date': {'N': str(int(date.timestamp()))}
    }
)
# Latency: 10-20ms (single partition, range scan)

# Challenge: Uneven distribution
# If customer A has 1M orders, customer B has 10:
# Partition (customer_A): 1M items, maybe jumbo
# Partition (customer_B): 10 items, tiny
# Solution: See "hot customer problem" below
```

### Strategy 3: Prefixed Hash (Distribution + Locality)

```python
# ✅ GOOD: Partition key = hash(user_id), Sort key = tenant_id + timestamp
# (Multi-tenant scenario)

def get_partition_key(user_id):
    # Hash user_id into prefix (0-99)
    return f"user#{hash(user_id) % 100}"

dynamodb.put_item(
    TableName='events',
    Item={
        'pk': {'S': get_partition_key(user_id)},  # Distributes 100 ways
        'sk': {'S': f"{tenant_id}#{int(timestamp.timestamp())}"},
        'event': {'S': json.dumps(event_data)}
    }
)

# Data distribution: Across 100 partitions
# Benefits:
# - If 1000 users, ~10 users per partition → balanced
# - User's events together (sort key locality)
# - Timestamp ranges efficient (sort key)

# Query:
dynamodb.query(
    TableName='events',
    KeyConditionExpression='pk = :pk AND sk BETWEEN :start AND :end',
    ExpressionAttributeValues={
        ':pk': {'S': get_partition_key(user_id)},
        ':start': {'S': f"{tenant_id}#{start_timestamp}"},
        ':end': {'S': f"{tenant_id}#{end_timestamp}"}
    }
)
# Latency: 5-10ms (single partition, range)
```

---

## Hot Partition Problem & Solutions

### Detecting Hot Partitions

```python
# Monitor CloudWatch metrics:
# - ConsumedWriteCapacity per partition (if exposed)
# - UserErrors increase (throttling = 400 errors)
# - RequestCount uneven (some partitions > others)

# Red flags:
# - All writes to 1 partition (all traffic waits for it)
# - UserErrors > 1% per minute (throttling happening)
# - Latency spikes when adding data (partition overload)
```

### Solution 1: Spreading with Write Sharding

```python
# Problem: All updates to same leaderboard item (hot key)
game_state = 'game_123'  # Every update writes to same partition

# Solution: Spread writes across 10 items (sub-sharding)
NUM_SHARDS = 10

def increment_score(game_id, player_id, points):
    # Pick random shard for this write
    shard = randint(0, NUM_SHARDS - 1)
    
    dynamodb.update_item(
        TableName='leaderboard',
        Key={
            'game_id': {'S': f"{game_id}#{shard}"},  # Spread across shards
            'player_id': {'S': player_id}
        },
        UpdateExpression='ADD score :p',
        ExpressionAttributeValues={':p': {'N': str(points)}}
    )
    # Each write hits different partition (shard % 10)
    # 100K writes/sec → distributed across 10 partitions
    # 100K / 10 = 10K writes/sec per partition ✓

# Read: Sum all shards
def get_score(game_id, player_id):
    total = 0
    for shard in range(NUM_SHARDS):
        response = dynamodb.get_item(
            TableName='leaderboard',
            Key={'game_id': {'S': f"{game_id}#{shard}"}, 'player_id': {'S': player_id}}
        )
        if 'Item' in response:
            total += int(response['Item']['score']['N'])
    return total

# Trade-off: Read requires 10 queries (10-50ms instead of 5ms)
# But writes now scale 10x (40KB/sec × 10 = 400KB/sec)
```

### Solution 2: Eventually-Consistent Caching

```python
# Problem: User profile accessed 100K times/sec
# Single partition: 100K reads/sec = bottleneck

# Solution: Cache in-memory + eventual consistency
import redis
import time

cache_ttl = 60  # 1 minute

def get_user_profile(user_id):
    # Try cache first
    cached = redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)  # Cache hit (99% of reads, <5ms)
    
    # Cache miss: read from DynamoDB
    response = dynamodb.get_item(
        TableName='users',
        Key={'user_id': {'S': user_id}}
    )
    profile = response['Item']
    
    # Cache it for future reads
    redis.setex(f"user:{user_id}", cache_ttl, json.dumps(profile))
    return profile

def update_user_profile(user_id, updates):
    # Update DynamoDB
    dynamodb.update_item(
        TableName='users',
        Key={'user_id': {'S': user_id}},
        UpdateExpression='SET #data = :data',
        ExpressionAttributeNames={'#data': 'profile'},
        ExpressionAttributeValues={':data': {'M': updates}}
    )
    # Invalidate cache immediately
    redis.delete(f"user:{user_id}")
    # Next read will fetch fresh data

# Result:
# Reads: 99% hit cache (Redis, <5ms), 1% read DynamoDB (5-10ms)
# Writes: DynamoDB only (5-10ms)
# Throughput: Can handle 1M reads/sec (Redis), 100 writes/sec (DynamoDB)
```

---

## Real-World Scenarios

### Scenario 1: E-Commerce Orders (500M items)

```python
# Table: orders
# Access patterns:
# 1. Get orders for customer (most common)
# 2. Get order by order_id (lookups)
# 3. Get orders in date range (analytics)

# Design:
dynamodb.create_table(
    TableName='orders',
    KeySchema=[
        {'AttributeName': 'customer_id', 'KeyType': 'HASH'},  # Partition key
        {'AttributeName': 'created_at', 'KeyType': 'RANGE'}   # Sort key
    ],
    BillingMode='PAY_PER_REQUEST'
)

# GSI for order_id lookups:
# (order_id as partition key, allows get_item by order_id)

# Capacity planning:
# 500M orders / estimated 1000 customers = 500K orders per customer avg
# Some customers: 1M orders (hot), some: 10 (cold)
# Peak: 50K new orders/sec

# Partitions needed:
# Each partition: 40KB/sec write capacity
# 50K orders/sec × 500 bytes = 25MB/sec
# 25MB / 40KB = 625 partitions needed!

# DynamoDB handles auto-scaling:
# Start with on-demand billing (pay per request)
# As load grows, DynamoDB adds partitions automatically

# Queries:
# Q1: Customer's orders (most common)
response = dynamodb.query(
    TableName='orders',
    KeyConditionExpression='customer_id = :cid AND created_at > :date',
    ExpressionAttributeValues={
        ':cid': {'S': customer_id},
        ':date': {'N': str(int(one_month_ago.timestamp()))}
    },
    ScanIndexForward=False,  # Newest first
    Limit=50
)
# Latency: 10-20ms (single partition scan)

# Q2: Analytics (orders in date range)
response = dynamodb.scan(
    TableName='orders',
    FilterExpression='created_at BETWEEN :start AND :end',
    ExpressionAttributeValues={
        ':start': {'N': str(int(start_date.timestamp()))},
        ':end': {'N': str(int(end_date.timestamp()))}
    }
)
# Latency: 100-500ms (scan all partitions)
# Recommendation: Use GSI or separate analytics table
```

### Scenario 2: Gaming Leaderboard (1B scores)

```python
# Table: leaderboard
# Requirements:
# - 500K score updates/sec (very high)
# - Query: player rank, top 100, friends ranks
# - Multi-game (some games popular, some niche)

# Design challenge: Uneven game popularity
# Game A: 100M scores
# Game B: 10M scores  
# Games C-Z: 100K scores each

# Strategy: Composite key + write sharding
dynamodb.create_table(
    TableName='leaderboard',
    KeySchema=[
        {'AttributeName': 'game_id', 'KeyType': 'HASH'},
        {'AttributeName': 'player_id', 'KeyType': 'RANGE'}
    ]
)

# For hot games, add write sharding at app level:
NUM_SHARDS_PER_GAME = 10

def update_score(game_id, player_id, points):
    # Popular games get sharded
    if game_id in HOT_GAMES:
        shard = hash(player_id) % NUM_SHARDS_PER_GAME
        actual_game_id = f"{game_id}#shard_{shard}"
    else:
        actual_game_id = game_id
    
    dynamodb.update_item(
        TableName='leaderboard',
        Key={
            'game_id': {'S': actual_game_id},
            'player_id': {'S': player_id}
        },
        UpdateExpression='ADD score :p',
        ExpressionAttributeValues={':p': {'N': str(points)}}
    )

# Capacity planning:
# Peak: 500K updates/sec across all games
# Game A: 300K updates/sec (hot)
# Game A with 10 shards: 30K updates/sec per shard ✓
# Partition capacity: 40KB/sec × 1000 ops = 40K updates/sec ✓ (fits)

# Read (get player rank in game):
# Uses sorted set pattern (DynamoDB doesn't have native sorting)
# Recommendation: Use DynamoDB Streams + Lambda to maintain top-100 cache
```

---

## Best Practices Checklist

- ✓ Never use timestamp as partition key (creates hot partitions)
- ✓ Avoid low-cardinality fields (status, yes/no) as partition key
- ✓ Distribute evenly: UUID, hash, or prefix-hash
- ✓ Sort key for range queries (efficient within partition)
- ✓ For hot items, use write sharding (spread across 10-100 logical items)
- ✓ Cache hot reads (Redis), keep only hot writes in DynamoDB
- ✓ Monitor CloudWatch UserErrors (throttling = hot partition)
- ✓ Use on-demand billing for variable loads (auto-scaling)
- ✓ Use provisioned billing if load predictable (cost savings)
- ✓ GSI for alternative query patterns (different partition key)
- ✓ Plan for growth (estimate peak throughput, adjust sharding)

---

**Summary:**
- **Partition key = everything**: determines performance, scalability
- **Good keys**: UUID (uniform), customer_id + sort key (locality)
- **Bad keys**: timestamp (sequential, hot), status (low cardinality)
- **Hot partitions**: Write sharding (10-100 spreads), or caching
- **Throughput**: 40KB/sec per partition, add partitions for scale
- **Consistency**: Eventually consistent (cache), or strongly consistent (DynamoDB direct)
