# DynamoDB Performance Tuning & Optimization

## Identifying Performance Issues

### CloudWatch Metrics to Monitor

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Check consumed throughput
response = cloudwatch.get_metric_statistics(
    Namespace='AWS/DynamoDB',
    MetricName='ConsumedWriteCapacityUnits',
    Dimensions=[
        {'Name': 'TableName', 'Value': 'Users'}
    ],
    StartTime=datetime.now() - timedelta(hours=1),
    EndTime=datetime.now(),
    Period=300,  # 5 min intervals
    Statistics=['Sum', 'Average', 'Maximum']
)

# Check throttling
response = cloudwatch.get_metric_statistics(
    Namespace='AWS/DynamoDB',
    MetricName='UserErrors',
    Dimensions=[
        {'Name': 'TableName', 'Value': 'Users'}
    ]
)
```

**Key Metrics:**
- `ConsumedReadCapacityUnits` vs provisioned
- `ConsumedWriteCapacityUnits` vs provisioned
- `UserErrors` (throttling)
- `SystemErrors` (AWS issues)
- `SuccessfulRequestLatency` (latency P99, P100)

---

## Write Optimization

### Problem: Write Throttling

**Symptoms:**
- `ThrottlingException` in logs
- High latency spikes
- Periodic request failures

### Root Causes & Solutions

#### 1. Hot Partitions

```python
# ❌ Bad: All writes to same partition
userId = sequential_id (1, 2, 3...)

# ✓ Solution 1: Random prefix (sharding)
userId = f"{uuid.uuid4().hex[:2]}#{sequential_id}"

# ✓ Solution 2: Timestamp prefix
from datetime import datetime
userId = f"{datetime.now().strftime('%Y%m%d%H')}#{sequential_id}"
```

#### 2. Insufficient Capacity

```python
# Check current capacity
dynamodb_client = boto3.client('dynamodb')

response = dynamodb_client.describe_table(TableName='Users')
capacity = response['Table']['ProvisionedThroughput']['WriteCapacityUnits']

# If you're consuming >80% of capacity, increase
if consumed_wcu / capacity > 0.8:
    dynamodb_client.update_table(
        TableName='Users',
        ProvisionedThroughput={
            'ReadCapacityUnits': 100,
            'WriteCapacityUnits': 200  # Increase
        }
    )
```

#### 3. Large Writes

```python
# ❌ Bad: Large item (10KB)
table.put_item(Item={
    'userId': 'user123',
    'largeDocument': 'x' * 10000  # 10KB
})
# Costs: 10 WCU

# ✓ Better: Compress large data
import gzip
compressed = gzip.compress(large_document.encode())
table.put_item(Item={
    'userId': 'user123',
    'largeDocument': compressed  # ~1KB
})
# Costs: 1 WCU
```

### Batch Writes Optimization

```python
# ❌ Bad: Sequential writes
for item in items:
    table.put_item(Item=item)
    # N API calls, network overhead

# ✓ Better: Batch writes
from boto3.dynamodb.conditions import

def batch_write_with_retry(table, items, batch_size=25):
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        
        with table.batch_writer(
            overwrite_by_pkeys=['userId']
        ) as batch_writer:
            for item in batch:
                batch_writer.put_item(Item=item)

# 100 items, 25 per batch = 4 API calls (vs 100)
batch_write_with_retry(table, items, batch_size=25)
```

---

## Read Optimization

### Query vs Scan Efficiency

```python
# ❌ Bad: Scan entire table
response = table.scan()  # Reads all 1M items
items = [i for i in response['Items'] if i['status'] == 'active']

# ✓ Better: Query with GSI
response = table.query(
    IndexName='StatusIndex',
    KeyConditionExpression='#s = :s',
    ExpressionAttributeNames={'#s': 'status'},
    ExpressionAttributeValues={':s': 'active'}
)
```

### Read Efficiency Ratios

```python
# Strongly Consistent Read
response = table.get_item(
    Key={'userId': 'user123'},
    ConsistentRead=True
)
# Costs: 1 RCU per 4KB

# Eventually Consistent Read (default)
response = table.get_item(Key={'userId': 'user123'})
# Costs: 0.5 RCU per 4KB (50% cheaper!)

# Use eventually consistent for non-critical reads
# (user profiles, recommendations, etc.)
```

### Projection for Bandwidth

```python
# ❌ Fetches entire item (1KB)
response = table.query(
    KeyConditionExpression='userId = :uid',
    ExpressionAttributeValues={':uid': 'user123'}
)

# ✓ Fetch only needed attributes (100 bytes)
response = table.query(
    KeyConditionExpression='userId = :uid',
    ProjectionExpression='userId, #n, email',
    ExpressionAttributeNames={'#n': 'name'},
    ExpressionAttributeValues={':uid': 'user123'}
)
```

---

## Indexing Strategy

### When to Create Indexes

```python
# Monitor query patterns
queries_by_attribute = {
    'userId': 95,          # 95% of queries
    'email': 4,            # 4% of queries
    'status': 1            # 1% of queries
}

# Create indexes for top access patterns
# Main table: userId
# GSI: email (covers 4% queries)
# GSI: status (covers 1% queries)

# Don't index <1% patterns
```

### Index Cost-Benefit Analysis

```python
# Cost of GSI
# - Storage (double the data)
# - Throughput provisioning
# - Replication cost

# Benefit
# - Faster queries on alternate attribute
# - May reduce full table scans

# Decision: Create GSI if
# - Query pattern is >5% of traffic
# - Saves significant scan cost
# - Application performance critical
```

---

## Connection Pooling

```python
# ❌ Bad: Create client per request
@app.route('/users/<user_id>')
def get_user(user_id):
    dynamodb = boto3.resource('dynamodb')  # New client
    table = dynamodb.Table('Users')
    return table.get_item(Key={'userId': user_id})

# ✓ Better: Reuse client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Users')

@app.route('/users/<user_id>')
def get_user(user_id):
    return table.get_item(Key={'userId': user_id})

# Reuses connection pool, faster request handling
```

---

## TTL for Automatic Cleanup

```python
import time

# Enable TTL on table
dynamodb_client.update_time_to_live(
    TableName='Sessions',
    TimeToLiveSpecification={
        'AttributeName': 'expirationTime',
        'Enabled': True
    }
)

# Store items with TTL
ttl_timestamp = int(time.time()) + 3600  # 1 hour from now

table.put_item(Item={
    'sessionId': 'sess_abc123',
    'userId': 'user456',
    'expirationTime': ttl_timestamp
})

# Item automatically deleted at expiration
# (within 48 hours, usually much faster)
```

---

## Caching Strategy (CloudFront/ElastiCache)

```python
import hashlib

# Cache frequent queries
cache_key = f"user_{user_id}"

# Check cache first
cached = cache.get(cache_key)
if cached:
    return cached

# Cache miss: query DynamoDB
response = table.get_item(Key={'userId': user_id})
item = response['Item']

# Store in cache (1 hour TTL)
cache.set(cache_key, item, ex=3600)
return item
```

---

## DAX (DynamoDB Accelerator)

```python
# In-memory cache layer for DynamoDB
# Automatic caching, microsecond latency

from amazondax import AmazonDaxClient

# Create DAX client
dax_client = AmazonDaxClient.resource(
    endpoint_url='dax://my-cluster.123abc.dax.cache.amazonaws.com'
)
table = dax_client.Table('Users')

# Same API, but cached
response = table.get_item(Key={'userId': 'user123'})
# First call: reads from DynamoDB, caches result
# Subsequent calls: reads from DAX (microseconds!)
```

---

## Capacity Optimization

### On-Demand vs Provisioned Decision

```
On-Demand:
- Unpredictable traffic
- Spiky patterns (10 req/s → 10k req/s)
- New applications
- Cost per request

Provisioned:
- Predictable traffic (1000 req/s constant)
- Steady state
- Cost-sensitive at scale
- Reserved capacity discount available
```

### Example: Cost Comparison

```
Traffic: 1000 reads/sec, 100 writes/sec, 1KB avg item

On-Demand:
- 1000 RU/sec × $1.25/million × 2.6B/month = $3,250/month
- 100 WU/sec × $6.25/million × 2.6B/month = $1,625/month
- Total: ~$4,875/month

Provisioned:
- 1000 RCU × $0.00013/hour × 730 hours = $95/month
- 100 WCU × $0.00065/hour × 730 hours = $47.45/month
- Total: ~$142/month (34x cheaper!)

Decision: Provisioned for predictable workload
```

---

## Real-World Optimization Case Study

### Scenario: Gaming Leaderboard Service

**Problem:** Leaderboard updates throttled at peak hours

**Analysis:**
- 100k concurrent users
- Each user updates score 10x/min = 1M writes/sec
- Single partition = hot partition

**Solutions Applied:**
1. **Sharding**: Partition across 100 shards
2. **Async Writes**: Queue updates, batch write
3. **Read Cache**: DAX for top player queries
4. **Monitoring**: CloudWatch alerts at 80% capacity

**Results:**
- 99th percentile latency: 50ms → 5ms
- Throttling errors: 10k/day → 0/day
- Cost: 30% reduction due to batching

---

## Performance Tuning Checklist

- [ ] Identify query patterns (monitor CloudWatch)
- [ ] Check for hot partitions (high ConsumedWCU on one partition)
- [ ] Create GSI for frequent alternate queries
- [ ] Use projection to reduce bandwidth
- [ ] Batch operations where possible
- [ ] Enable DAX for read-heavy workloads
- [ ] Use TTL for automatic cleanup
- [ ] Monitor P99 latency
- [ ] Right-size provisioned capacity (or use on-demand)
- [ ] Test with production-like load

---

## Summary

- **Writes:** Avoid hot partitions, batch operations, compress large items
- **Reads:** Query > Scan, projection, eventually consistent when safe
- **Indexes:** Create for >5% of query traffic
- **Caching:** Use DAX for frequently accessed items
- **TTL:** Automatic cleanup for temporary data
- **Monitoring:** CloudWatch metrics, latency percentiles
- **Capacity:** Right-size based on traffic patterns

Next: [[../06-scaling/01-global-tables.md|Global Tables & Scaling]]
