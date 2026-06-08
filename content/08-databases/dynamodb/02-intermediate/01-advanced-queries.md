---
title: Advanced Queries & Filtering
topic: 08-databases
difficulty: intermediate
time: 30m
paths:
  - backend-junior
  - data
  - backend-senior
---

# Advanced Queries & Filtering

## Query Optimization Strategies

### Problem: Hot Partitions

**Scenario:** User IDs 1-1000 created today, causing one partition to receive 90% of writes.

**Solutions:**

```python
# ❌ Bad: Sequential IDs cause clustering
userId = 1, 2, 3, 4...

# ✓ Good: Add random prefix (sharding)
userId = f"{uuid.uuid4().hex[:2]}#{uuid.uuid4()}"
# Distributes evenly across partitions

# ✓ Good: Add timestamp prefix
userId = f"{current_year_month}#{sequential_id}"
```

### Range Key Design Patterns

#### Pattern 1: Time Series Queries
```python
# Partition: entityId (device/sensor)
# Sort: timestamp

# Query last 24 hours of data
response = table.query(
    KeyConditionExpression='deviceId = :did AND #ts BETWEEN :start AND :end',
    ExpressionAttributeNames={'#ts': 'timestamp'},
    ExpressionAttributeValues={
        ':did': 'device123',
        ':start': int(time.time()) - 86400,
        ':end': int(time.time())
    }
)
```

#### Pattern 2: Hierarchical Data
```python
# Table: Documents
# Partition: userId
# Sort: path (like file system)

# Query all docs in /projects/2026/
response = table.query(
    KeyConditionExpression='userId = :uid AND begins_with(docPath, :path)',
    ExpressionAttributeValues={
        ':uid': 'user123',
        ':path': '/projects/2026/'
    }
)
```

#### Pattern 3: Versioning
```python
# Partition: itemId
# Sort: version (descending)

# Query latest 10 versions
response = table.query(
    KeyConditionExpression='itemId = :id',
    ExpressionAttributeValues={':id': 'item123'},
    ScanIndexForward=False,  # Descending by version
    Limit=10
)
```

---

## FilterExpression Deep Dive

### Important: Filter Happens AFTER Query

```python
# ❌ Inefficient: Query returns 1000 items, filter to 10
response = table.query(
    KeyConditionExpression='userId = :uid',
    FilterExpression='#s = :status',
    ExpressionAttributeNames={'#s': 'status'},
    ExpressionAttributeValues={
        ':uid': 'user123',
        ':status': 'active'
    }
)
# Cost: 1000 RCU consumed even though only 10 returned

# ✓ Better: Use GSI with status as partition key
response = table.query(
    IndexName='StatusIndex',
    KeyConditionExpression='#s = :status AND userId = :uid',
    ExpressionAttributeNames={'#s': 'status'},
    ExpressionAttributeValues={
        ':uid': 'user123',
        ':status': 'active'
    }
)
# Cost: 10 RCU (only returns matching items)
```

### Complex FilterExpressions

```python
# Multiple conditions (AND)
FilterExpression='#s = :s AND #a BETWEEN :min AND :max',

# OR conditions
FilterExpression='#s = :s OR #t = :t',

# NOT conditions
FilterExpression='attribute_not_exists(bannedDate)',

# List/Set membership
FilterExpression='contains(tags, :tag)',

# Size functions
FilterExpression='size(comments) > :min',

# Combined complex filter
response = table.query(
    KeyConditionExpression='userId = :uid',
    FilterExpression='(#s = :s OR #t = :t) AND #a > :min AND size(attachments) > :zero',
    ExpressionAttributeNames={
        '#s': 'status',
        '#t': 'type',
        '#a': 'age'
    },
    ExpressionAttributeValues={
        ':uid': 'user123',
        ':s': 'active',
        ':t': 'premium',
        ':min': 18,
        ':zero': 0
    }
)
```

---

## Projection Expressions

Fetch only needed attributes (doesn't reduce cost, but reduces transfer).

```python
# Get specific attributes
response = table.query(
    KeyConditionExpression='userId = :uid',
    ProjectionExpression='userId, #n, email, createdDate',
    ExpressionAttributeNames={'#n': 'name'},
    ExpressionAttributeValues={':uid': 'user123'}
)

# Nested attributes
response = table.query(
    KeyConditionExpression='userId = :uid',
    ProjectionExpression='userId, #a.city, #a.country',
    ExpressionAttributeNames={'#a': 'address'},
    ExpressionAttributeValues={':uid': 'user123'}
)

# List/Map elements
response = table.query(
    KeyConditionExpression='userId = :uid',
    ProjectionExpression='userId, #t[0], #t[2]',  # 1st and 3rd items
    ExpressionAttributeNames={'#t': 'tags'},
    ExpressionAttributeValues={':uid': 'user123'}
)
```

---

## Index Selection Strategy

### When to Use Each Index

| Scenario | Best Index |
|----------|-----------|
| Query by userId | Main table |
| Query by email | GSI (email PK) |
| Query by email + date | GSI (email PK, date SK) |
| Query by status | GSI (status PK) |
| Temporal range on same PK | LSI (same PK, date SK) |

### Sparse Indexes

```python
# GSI for only active items (sparse)
# Only items with status='active' go in index
# Saves space, reduces cost

# Create GSI
table.create_global_secondary_index(
    GlobalSecondaryIndexName='ActiveUsersIndex',
    KeySchema=[
        {'AttributeName': 'status', 'KeyType': 'HASH'},
        {'AttributeName': 'userId', 'KeyType': 'RANGE'}
    ],
    Projection={'ProjectionType': 'ALL'}
)

# Only put items with status field
table.put_item(Item={
    'userId': 'user123',
    'status': 'active',  # Goes to sparse index
    'email': 'user@example.com'
})

table.put_item(Item={
    'userId': 'user999',
    # No status field
    # This item is invisible to StatusIndex
    'email': 'deleted@example.com'
})
```

---

## Scan Optimization (When Necessary)

### Parallel Scan

```python
# Segment table for parallel scanning
import concurrent.futures

def scan_segment(segment_num, total_segments):
    response = table.scan(
        Segment=segment_num,
        TotalSegments=total_segments
    )
    return response['Items']

# Scan 4 segments in parallel
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(scan_segment, i, 4)
        for i in range(4)
    ]
    all_items = []
    for future in concurrent.futures.as_completed(futures):
        all_items.extend(future.result())
```

### Scan with Projection

```python
# Only fetch needed columns
response = table.scan(
    ProjectionExpression='userId, email',
    FilterExpression='#s = :s',
    ExpressionAttributeNames={'#s': 'status'},
    ExpressionAttributeValues={':s': 'active'}
)
```

---

## Real-World Query Patterns

### Pattern: Search with Sorting

**Problem:** Find all products in category, sorted by price, filtered by rating.

**Solution:** Use GSI

```python
# GSI: categoryId (PK), price (SK)
response = table.query(
    IndexName='CategoryPriceIndex',
    KeyConditionExpression='categoryId = :cid AND price BETWEEN :min AND :max',
    FilterExpression='rating > :minrating',
    ScanIndexForward=True,  # Ascending price
    ExpressionAttributeValues={
        ':cid': 'electronics',
        ':min': 100,
        ':max': 500,
        ':minrating': 4.0
    }
)
```

### Pattern: Multi-Tenant Query

**Problem:** Query user's documents while tenant-isolating data.

```python
# Table: UserDocuments
# Partition: tenantId
# Sort: userId#documentId

response = table.query(
    KeyConditionExpression='tenantId = :tid AND begins_with(compositeKey, :uid)',
    ExpressionAttributeValues={
        ':tid': 'tenant123',
        ':uid': 'user456#'
    }
)
```

### Pattern: Geospatial Queries

**Problem:** Find users near location (simplified without dedicated geospatial DB).

```python
# Table: Users
# GSI: regionId (PK), latitude (SK)

response = table.query(
    IndexName='RegionLatitudeIndex',
    KeyConditionExpression='regionId = :region',
    FilterExpression='#lat BETWEEN :minlat AND :maxlat AND #lon BETWEEN :minlon AND :maxlon',
    ExpressionAttributeNames={
        '#lat': 'latitude',
        '#lon': 'longitude'
    },
    ExpressionAttributeValues={
        ':region': 'us-east-1',
        ':minlat': 40.0,
        ':maxlat': 41.0,
        ':minlon': -74.0,
        ':maxlon': -73.0
    }
)
```

---

## Summary

- **Query > Scan:** Always prefer queries with partition key
- **FilterExpression:** Happens after data retrieval (costs RCUs for filtered items)
- **GSI:** Use for alternate access patterns
- **Sparse Indexes:** Optimize by only indexing relevant items
- **Projection:** Reduce network transfer (not RCU cost)
- **Range Patterns:** begins_with, BETWEEN for efficient range queries

Next: [[02-indexing-optimization.md|Indexing & Optimization]]
