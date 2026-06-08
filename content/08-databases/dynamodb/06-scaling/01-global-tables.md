---
title: DynamoDB Global Tables & Multi-Region Scaling
topic: 08-databases
difficulty: intermediate
time: 30m
paths:
  - backend-junior
  - data
  - backend-senior
---

# DynamoDB Global Tables & Multi-Region Scaling

## Global Tables Overview

Replicate tables across regions for low-latency access and disaster recovery.

### Architecture

```
Region 1 (US-East)          Region 2 (Europe)         Region 3 (Asia)
  ├─ Table (Master)    ←→    ├─ Table (Replica)  ←→    ├─ Table (Replica)
  └─ Streams                 └─ Streams                 └─ Streams
     (Capture changes)          (Apply changes)           (Apply changes)
```

---

## Setup

### Enable Streams

```python
import boto3

dynamodb = boto3.client('dynamodb')

# First, enable streams on table
dynamodb.update_table(
    TableName='Users',
    StreamSpecification={
        'StreamViewType': 'NEW_AND_OLD_IMAGES'
    }
)

# Verify streams enabled
response = dynamodb.describe_table(TableName='Users')
stream_arn = response['Table']['LatestStreamArn']
```

### Create Global Table

```python
# Create global table (replicates to multiple regions)
dynamodb = boto3.client('dynamodb', region_name='us-east-1')

response = dynamodb.create_global_table(
    GlobalTableName='Users',
    ReplicationGroup=[
        {
            'RegionName': 'us-east-1'
        },
        {
            'RegionName': 'eu-west-1'
        },
        {
            'RegionName': 'ap-southeast-1'
        }
    ]
)
```

### Replica Configuration

```python
# Each replica has own throughput
dynamodb.update_table(
    TableName='Users',
    ReplicaUpdates=[
        {
            'Create': {
                'RegionName': 'eu-west-1'
            }
        },
        {
            'Create': {
                'RegionName': 'ap-southeast-1'
            }
        }
    ]
)
```

---

## Replication Behavior

### Write Semantics

```python
# Write to any region (becomes master for that write)
dynamodb_us = boto3.resource('dynamodb', region_name='us-east-1')
table_us = dynamodb_us.Table('Users')

# Write in US region
table_us.put_item(Item={
    'userId': 'user123',
    'email': 'john@example.com',
    'updated': int(time.time())
})

# Automatically replicated to EU and Asia within milliseconds
# But eventually consistent across regions
```

### Consistency Model

```python
# Eventually consistent (default)
dynamodb_eu = boto3.resource('dynamodb', region_name='eu-west-1')
table_eu = dynamodb_eu.Table('Users')

# Read might not see write immediately
response = table_eu.get_item(Key={'userId': 'user123'})
# Might not contain latest email yet (replication in progress)

# Typical replication: <1 second
# Max: Usually <100ms for same continent, <1s for intercontinental
```

---

## Multi-Region Application Pattern

### Read Local, Write Local

```python
import boto3
from datetime import datetime

class MultiRegionDB:
    def __init__(self, home_region):
        self.home_region = home_region
        self.dynamodb = boto3.resource('dynamodb', region_name=home_region)
        self.table = self.dynamodb.Table('Users')
    
    def get_user(self, user_id):
        # Read from local region (fast)
        response = self.table.get_item(Key={'userId': user_id})
        return response.get('Item')
    
    def update_user(self, user_id, updates):
        # Write to local region (becomes primary for this write)
        self.table.update_item(
            Key={'userId': user_id},
            UpdateExpression='SET #u = :updates, #t = :ts',
            ExpressionAttributeNames={
                '#u': 'data',
                '#t': 'lastUpdated'
            },
            ExpressionAttributeValues={
                ':updates': updates,
                ':ts': int(datetime.now().timestamp())
            }
        )

# In US: Use us-east-1
us_db = MultiRegionDB('us-east-1')
us_db.update_user('user123', {'status': 'active'})

# In EU: Use eu-west-1
eu_db = MultiRegionDB('eu-west-1')
eu_user = eu_db.get_user('user123')  # Fast local read
```

---

## Conflict Resolution

Multiple writes across regions can conflict.

### Last Write Wins

```python
# Timestamp-based: Latest write wins
table.update_item(
    Key={'userId': 'user123'},
    UpdateExpression='SET #data = :data, #ts = :ts',
    ConditionExpression='attribute_not_exists(#ts) OR #ts < :new_ts',
    ExpressionAttributeNames={
        '#data': 'userdata',
        '#ts': 'lastModified'
    },
    ExpressionAttributeValues={
        ':data': {'email': 'new@example.com'},
        ':new_ts': int(time.time() * 1000)  # milliseconds for precision
    }
)
```

### Region-Based

```python
# Region preference: US wins over EU
# Prefix item with region
table.put_item(Item={
    'userId': 'user123#us-east-1',  # Region in key
    'email': 'john@example.com',
    'region': 'us-east-1'
})

# Query: Get US version if exists
response = table.get_item(Key={'userId': 'user123#us-east-1'})
if 'Item' not in response:
    # Fall back to EU
    response = table.get_item(Key={'userId': 'user123#eu-west-1'})
```

### Application-Level Merge

```python
def merge_user_data(us_version, eu_version):
    # Custom merge logic
    merged = {}
    
    # Timestamp-based for each field
    if us_version.get('lastModified', 0) > eu_version.get('lastModified', 0):
        merged = us_version
    else:
        merged = eu_version
    
    # OR: Field-by-field merge
    merged = {
        'userId': us_version['userId'],
        'email': max([us_version.get('email'), eu_version.get('email')]),
        'status': us_version.get('status', eu_version.get('status')),
        'lastModified': max([
            us_version.get('lastModified', 0),
            eu_version.get('lastModified', 0)
        ])
    }
    
    return merged
```

---

## Failover Scenarios

### Region Failure

```python
# Detect region unreachable
import botocore.exceptions

def write_with_failover(user_id, data):
    regions = ['us-east-1', 'eu-west-1', 'ap-southeast-1']
    
    for region in regions:
        try:
            dynamodb = boto3.resource('dynamodb', region_name=region)
            table = dynamodb.Table('Users')
            
            table.put_item(Item={
                'userId': user_id,
                'data': data,
                'writtenTo': region
            })
            print(f"Written to {region}")
            return
        except botocore.exceptions.ClientError:
            print(f"Failed in {region}, trying next...")
            continue
    
    raise Exception("All regions failed")
```

### Read Failover

```python
def read_with_failover(user_id):
    # Try local first, then others
    regions = ['us-east-1', 'eu-west-1', 'ap-southeast-1']
    
    for region in regions:
        try:
            dynamodb = boto3.resource('dynamodb', region_name=region)
            table = dynamodb.Table('Users')
            
            response = table.get_item(Key={'userId': user_id})
            if 'Item' in response:
                return response['Item']
        except:
            continue
    
    return None
```

---

## Monitoring Multi-Region

### Replication Metrics

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Get replication latency
response = cloudwatch.get_metric_statistics(
    Namespace='AWS/DynamoDB',
    MetricName='ReplicationLatency',
    Dimensions=[
        {'Name': 'TableName', 'Value': 'Users'},
        {'Name': 'ReceivingRegion', 'Value': 'eu-west-1'}
    ],
    StartTime=datetime.now() - timedelta(hours=1),
    EndTime=datetime.now(),
    Period=300,
    Statistics=['Average', 'Maximum']
)

# Typical replication latency: 10-100ms same continent
# Cross-continent: 100ms-1s
```

### Health Check

```python
def check_region_health():
    regions = ['us-east-1', 'eu-west-1', 'ap-southeast-1']
    health = {}
    
    for region in regions:
        try:
            dynamodb = boto3.client('dynamodb', region_name=region)
            
            # Write test item
            table_name = 'HealthCheck'
            test_key = f'test_{int(time.time())}'
            
            dynamodb.put_item(
                TableName=table_name,
                Item={'id': {'S': test_key}}
            )
            
            # Read it back
            response = dynamodb.get_item(
                TableName=table_name,
                Key={'id': {'S': test_key}}
            )
            
            health[region] = 'healthy' if 'Item' in response else 'degraded'
        except Exception as e:
            health[region] = f'failed: {str(e)}'
    
    return health
```

---

## Cost Implications

### Per-Region Pricing

```
Global Table: Multiple regions, same table

Costs:
- Each region charged separately (read/write capacity or on-demand)
- Replication: Free (included)
- Multi-region write: Higher consistency costs

Example:
- US region: 100 RCU, 50 WCU = $13 + $32.50 = $45.50/day
- EU region: 100 RCU, 50 WCU = $13 + $32.50 = $45.50/day
- Asia region: 100 RCU, 50 WCU = $13 + $32.50 = $45.50/day
- Total: $136.50/day (3x single region)
```

### Optimization

```python
# Write only to primary region, replicate automatically
primary_region = 'us-east-1'
read_only_regions = ['eu-west-1', 'ap-southeast-1']

# All writes go through primary
table = boto3.resource('dynamodb', region_name=primary_region).Table('Users')
table.put_item(Item=data)

# Reads can happen in any region
eu_table = boto3.resource('dynamodb', region_name='eu-west-1').Table('Users')
item = eu_table.get_item(Key={'userId': user_id})
# Reads cheaper in replica regions
```

---

## Real-World Example: Global SaaS App

```python
class GlobalSaaSDatabase:
    def __init__(self, user_region):
        self.user_region = user_region
        self.table = boto3.resource(
            'dynamodb',
            region_name=user_region
        ).Table('Users')
    
    def create_user(self, user_id, email):
        # Write in user's region
        self.table.put_item(Item={
            'userId': user_id,
            'email': email,
            'createdAt': int(time.time()),
            'region': self.user_region
        })
    
    def get_user_fast(self, user_id):
        # Local read (1-2ms)
        return self.table.get_item(Key={'userId': user_id})['Item']
    
    def update_user(self, user_id, updates):
        # Write in user's region (becomes primary)
        self.table.update_item(
            Key={'userId': user_id},
            UpdateExpression='SET #u = :updates',
            ExpressionAttributeNames={'#u': 'updates'},
            ExpressionAttributeValues={':updates': updates}
        )

# User in US
us_db = GlobalSaaSDatabase('us-east-1')
us_db.create_user('user123', 'john@example.com')

# User in EU (local read)
eu_db = GlobalSaaSDatabase('eu-west-1')
user = eu_db.get_user_fast('user123')  # Sees data within <1s

# Data automatically consistent across all regions
```

---

## Summary

- **Global Tables**: Multi-region replication
- **Eventual Consistency**: <1s replication typical
- **Read Local**: Fast reads in any region
- **Write Local**: Write to home region, replicate automatically
- **Failover**: Automatic, multiple regions
- **Conflicts**: Last-write-wins, region-based, or application merge
- **Cost**: 3x+ for 3 regions
- **Ideal For**: Global apps, DR, low-latency access

Next: [[02-scaling-strategies.md|Scaling Strategies & Limits]]

---

**See Also:**
- [[01-performance-tuning.md|Performance Tuning]]
- [[../../mysql/02-intermediate/02-replication-ha.md|MySQL Replication]]
- [[../../postgres/02-intermediate/02-replication-scaling.md|PostgreSQL Replication]]
