# Redis Caching Strategies: Patterns & Production Patterns

## Caching Fundamentals

### Cache Hierarchy

```
L1: Local Process Cache (in-memory Python dict/HashMap)
    - Latency: 1-2ms
    - Size: 100MB-1GB per instance
    - Access: Super-fast, no network
    - Consistency: Stale (doesn't auto-update)

L2: Redis Shared Cache (network)
    - Latency: 5-15ms (network round-trip)
    - Size: 1GB-100GB across cluster
    - Access: Network round-trip
    - Consistency: More fresh than L1, but eventual

L3: Database (Authoritative)
    - Latency: 50-500ms
    - Size: Unlimited
    - Consistency: Fresh, authoritative
    - Access: Slowest
```

## Caching Strategies

### Strategy 1: Cache-Aside (Lazy Loading)

```python
def get_user(user_id):
    # Step 1: Try cache first
    cached = redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)  # Cache hit (fast!)
    
    # Step 2: Cache miss - load from DB
    user = db.query(f"SELECT * FROM users WHERE id = {user_id}")
    if not user:
        raise NotFound()
    
    # Step 3: Cache for future requests
    redis.setex(f"user:{user_id}", ttl=3600, value=json.dumps(user))
    return user

# Usage:
user = get_user(123)  # First call: DB hit (100ms), cached
user = get_user(123)  # Second call: Cache hit (5ms)

# Pros:
# - Only cache hot data (accessed recently)
# - Code simple
# - No wasted cache space on unused items

# Cons:
# - First access slow (DB hit)
# - Cache stampede (many concurrent cache misses → thundering herd)
# - Stale data if DB changes but cache not invalidated
```

### Strategy 2: Write-Through Cache

```python
def update_user(user_id, updates):
    # Step 1: Update database first
    db.update(f"UPDATE users SET ... WHERE id = {user_id}")
    
    # Step 2: Update cache immediately
    user = db.query(f"SELECT * FROM users WHERE id = {user_id}")
    redis.setex(f"user:{user_id}", ttl=3600, value=json.dumps(user))
    
    return user

# Usage:
update_user(123, {"name": "John"})  # Update DB + cache
get_user(123)  # Cache hit with fresh data

# Pros:
# - Cache always fresh (updated immediately)
# - No stale data issue
# - Consistent reads

# Cons:
# - Write latency: must wait for both DB + cache writes
# - Adds ~5-10ms per write (cache I/O)
# - Wasted cache space on unaccessed items
```

### Strategy 3: Write-Behind (Async Write)

```python
import queue
import threading

# In-memory buffer for updates
update_queue = queue.Queue()

def update_user_async(user_id, updates):
    # Step 1: Update cache immediately (fast)
    user_data = {**get_user_from_db(user_id), **updates}
    redis.setex(f"user:{user_id}", ttl=3600, value=json.dumps(user_data))
    
    # Step 2: Queue DB update for later (async)
    update_queue.put(('user', user_id, updates))
    return user_data  # Return immediately

# Background worker (writes to DB in batches)
def batch_writer():
    batch = []
    while True:
        try:
            item = update_queue.get(timeout=1)
            batch.append(item)
            
            if len(batch) >= 100:  # Batch 100 updates
                # Write all to DB in one transaction
                for entity, id, data in batch:
                    db.update(entity, id, data)
                batch = []
        except queue.Empty:
            if batch:
                db.update(batch)  # Flush remaining
                batch = []

# Thread running in background:
threading.Thread(target=batch_writer, daemon=True).start()

# Pros:
# - Write latency: Cache only (5ms instead of 105ms for DB)
# - Batches DB writes (more efficient)
# - Throughput: 10-100x better (cache writes, DB batches)

# Cons:
# - Data loss risk (crash before DB write)
# - Eventual consistency (DB delayed from cache)
# - Complex: need background worker
```

## Cache Invalidation

### Pattern 1: TTL-Based

```python
def cache_with_ttl(key, value, ttl_seconds=300):
    redis.setex(key, ttl_seconds, json.dumps(value))

# Usage:
cache_with_ttl("user:123", user_data, ttl_seconds=300)
# Cache expires after 5 minutes

# Pros:
# - Simple (automatic expiry)
# - No stale data forever

# Cons:
# - Stale data for up to TTL duration (5 min gap)
# - May re-fetch even if unchanged
```

### Pattern 2: Event-Based Invalidation

```python
# Update model
class User:
    def __init__(self, id, name):
        self.id = id
        self.name = name
    
    def save(self):
        db.update(self)
        # Invalidate cache immediately
        redis.delete(f"user:{self.id}")
        # Next read will fetch fresh data

# Usage:
user = User(123, "John")
user.save()  # DB updated, cache invalidated
get_user(123)  # Reads fresh data from DB

# Pros:
# - Always fresh data (invalidated immediately)
# - No stale data window

# Cons:
# - Complex (must track all places that change data)
# - Cascading invalidations (update user → invalidate orders → invalidate reports)
```

### Pattern 3: Cache Tags

```python
def cache_with_tags(key, value, ttl, tags):
    # Store value + add to tag set
    redis.setex(key, ttl, json.dumps(value))
    for tag in tags:
        redis.sadd(f"tag:{tag}", key)

def invalidate_by_tag(tag):
    # Find all keys with this tag
    keys = redis.smembers(f"tag:{tag}")
    # Delete all
    if keys:
        redis.delete(*keys)
    redis.delete(f"tag:{tag}")

# Usage:
cache_with_tags(
    "user:123:orders",
    user_orders,
    ttl=3600,
    tags=["user:123", "orders"]  # Tags for invalidation
)

# When user updates:
invalidate_by_tag("user:123")
# Deletes: user:123, user:123:orders, user:123:profile (all tagged)

# Pros:
# - Cascade invalidation simple
# - Grouped invalidation

# Cons:
# - Extra memory (tag sets)
# - Complexity (must tag consistently)
```

## Cache Stampede & Thundering Herd

### Problem

```python
# Popular item expires at T=1000
# 10K users request it at T=1001
# All 10K miss cache
# All 10K query database
# Database: 10K queries in 1 second → bottleneck!

# Impact:
# Normal: 1 DB query per item per TTL (every 300 sec)
# Stampede: 10K queries in 1 second
```

### Solution 1: Probabilistic Early Expiry

```python
def get_cached(key, fetch_fn, ttl=300):
    value = redis.get(key)
    if not value:
        # Cache miss: fetch and cache
        value = fetch_fn()
        redis.setex(key, ttl, json.dumps(value))
        return value
    
    # Cache hit: check if we should refresh early
    ttl_remaining = redis.pttl(key) / 1000  # milliseconds → seconds
    
    # Early refresh: if < 20% TTL remaining + random chance
    if ttl_remaining < ttl * 0.2 and random.random() < 0.1:
        # Refresh early, only 10% of users refresh per second
        value = fetch_fn()
        redis.setex(key, ttl, json.dumps(value))
    
    return value

# Usage:
user = get_cached(
    f"user:{user_id}",
    lambda: db.get_user(user_id),
    ttl=300
)

# Behavior:
# First 240 seconds: all users get cache hit (instant)
# Last 60 seconds: 10% of users trigger refresh early
# Result: Distributed refresh, no thundering herd
```

### Solution 2: Lock-Based Refresh

```python
import redis

def get_cached_with_lock(key, fetch_fn, ttl=300):
    value = redis.get(key)
    if value:
        return json.loads(value)
    
    # Cache miss: try to get lock
    lock_key = f"{key}:lock"
    lock = redis.set(lock_key, "1", nx=True, ex=10)  # 10 sec lock
    
    if lock:
        # Got lock: fetch data
        value = fetch_fn()
        redis.setex(key, ttl, json.dumps(value))
        redis.delete(lock_key)
        return value
    else:
        # Another thread has lock: wait for value
        for _ in range(50):  # Wait up to 5 seconds
            time.sleep(0.1)
            value = redis.get(key)
            if value:
                return json.loads(value)
        
        # Timeout waiting: fetch anyway
        return fetch_fn()

# Usage:
user = get_cached_with_lock(
    f"user:{user_id}",
    lambda: db.get_user(user_id)
)

# Behavior:
# Multiple cache misses:
# - First thread: gets lock, fetches data
# - Other threads: wait (polling)
# - Result: Only 1 DB query instead of 10K
```

---

## Real-World Caching Patterns

### Pattern 1: Session Storage

```python
def login(username, password):
    user = authenticate(username, password)
    
    # Store session in Redis
    session_id = str(uuid4())
    redis.setex(
        f"session:{session_id}",
        ttl=1800,  # 30 minutes
        value=json.dumps({
            'user_id': user['id'],
            'username': user['username'],
            'ip': request.remote_addr
        })
    )
    
    return {'session_id': session_id, 'user': user}

def get_session(session_id):
    session = redis.get(f"session:{session_id}")
    if not session:
        raise Unauthorized()
    return json.loads(session)

# Performance:
# Authentication: 5-10ms (Redis, no DB)
# Scale: 1M concurrent sessions = 100KB-1GB Redis
# Cost: $10-50/month Redis vs $1K+/month DB for same scale
```

### Pattern 2: Rate Limiting

```python
from redis import Redis

def rate_limit(user_id, limit=100, window=60):
    key = f"ratelimit:{user_id}"
    count = redis.incr(key)  # Increment counter
    
    if count == 1:
        # First request in window: set expiry
        redis.expire(key, window)
    
    if count > limit:
        raise TooManyRequests(f"Rate limit exceeded: {count}/{limit}")
    
    return {"remaining": limit - count}

# Usage:
rate_limit("user:123", limit=100, window=60)  # 100 requests per 60 seconds

# Performance:
# Check: 1-2ms (Redis INCR)
# Scale: 1M users × 100 reqs/min = 100M increments/min
# Single Redis instance: handles easily (50K ops/sec)
```

### Pattern 3: Leaderboard (Sorted Set)

```python
def update_score(game_id, player_id, points):
    # Store in sorted set (score = Z-score)
    redis.zadd(
        f"leaderboard:{game_id}",
        {player_id: points},  # {member: score}
        xx=False  # Create if not exists
    )

def get_top_players(game_id, limit=100):
    # Get top scores (highest first)
    top = redis.zrevrange(
        f"leaderboard:{game_id}",
        0,
        limit - 1,
        withscores=True  # Include scores
    )
    return [(player_id, int(score)) for player_id, score in top]

def get_player_rank(game_id, player_id):
    # Rank is position in sorted set (0-indexed)
    rank = redis.zrevrank(f"leaderboard:{game_id}", player_id)
    return rank + 1 if rank is not None else None

# Performance:
# Update score: 1-2ms (ZADD)
# Get top 100: 5-10ms (ZREVRANGE)
# Get rank: 1-2ms (ZREVRANK)

# Memory:
# 1M players × 50 bytes per entry = 50MB (small!)
# Throughput: 50K updates/sec easily
```

---

## Monitoring Cache Performance

### Key Metrics

```python
def get_cache_stats():
    info = redis.info('stats')
    return {
        'total_commands': info['total_commands_processed'],
        'connections': info['connected_clients'],
        'memory_used': info['used_memory_human'],
        'memory_peak': info['used_memory_peak_human'],
        'evictions': info['evicted_keys'],  # Keys removed due to memory pressure
        'expired_keys': info['expired_keys'],  # TTL expired
    }

# Monitor:
# Hit ratio: hits / (hits + misses)
# - Good: > 90%
# - Poor: < 70%
# If poor: increase TTL or cache more items

# Memory usage:
# - If > 80% capacity: evictions start
# - If > 95%: significant performance degradation
# - Set maxmemory-policy to handle full cache

# Eviction rate:
# - High evictions: cache too small, increase size
# - Pattern: sudden spike = cache clear (outdated data)
```

---

## Best Practices Checklist

- ✓ Use cache-aside for read-heavy workloads
- ✓ Cache-through for consistency (but slower writes)
- ✓ TTL to prevent stale data forever (even with invalidation)
- ✓ Event-based invalidation for critical data
- ✓ Prevent thundering herd (early refresh, locks)
- ✓ Monitor hit ratio (should be >85%)
- ✓ Monitor memory (alert at >75% capacity)
- ✓ Set eviction policy (LRU for most cases)
- ✓ Batch writes to DB (write-behind cache)
- ✓ Don't cache unhashable data (unless serialized)
- ✓ Use compression for large values
- ✓ Security: encrypt sensitive cached data

---

**Summary:**
- **Cache-Aside**: Simple, only hot data cached, thundering herd risk
- **Write-Through**: Consistent, but slower writes
- **Write-Behind**: Fast writes, eventual consistency, data loss risk
- **Invalidation**: TTL simple but stale, event-based fresh but complex
- **Stampede**: Probabilistic early refresh or lock-based
- **Real patterns**: Sessions (Redis), rate limiting (simple counter), leaderboard (sorted sets)
