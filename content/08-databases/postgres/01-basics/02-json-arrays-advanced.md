---
title: PostgreSQL JSON, Arrays & Advanced Features
topic: 08-databases
difficulty: intermediate
time: 30m
paths:
  - backend-junior
  - data
  - backend-senior
---

# PostgreSQL JSON, Arrays & Advanced Features

## JSON vs JSONB

### JSON (Text)

```sql
-- Stores as text, parses on each query
CREATE TABLE users (
    userId INT PRIMARY KEY,
    metadata JSON
);

INSERT INTO users VALUES (1, '{"age": 30, "city": "Boston"}');

-- Query (slower, re-parses)
SELECT metadata->>'age' FROM users;
```

**Disadvantages:**
- Slower queries (re-parses each time)
- No indexing
- Whitespace preserved

### JSONB (Binary, Preferred)

```sql
-- Binary format, pre-parsed, indexable
CREATE TABLE users (
    userId INT PRIMARY KEY,
    metadata JSONB
);

INSERT INTO users VALUES (1, '{"age": 30, "city": "Boston"}');

-- Query (faster, indexed)
SELECT metadata->>'age' FROM users;
```

**Advantages:**
- Faster queries
- Indexable (GIN index)
- Whitespace normalized
- Supports operators

---

## JSON Operators

### Accessing Data

```sql
-- Text extraction (returns text)
SELECT metadata->>'age' AS age FROM users;  -- "30" (text)

-- JSON extraction (returns JSON)
SELECT metadata->'age' AS age FROM users;  -- 30 (number)

-- Array access
SELECT metadata->'tags'->>0 FROM users;  -- First tag

-- Path access
SELECT metadata#>>'{address,city}' FROM users;
```

### Checking & Querying

```sql
-- Check key exists
SELECT * FROM users WHERE metadata ? 'age';

-- Check any key exists
SELECT * FROM users WHERE metadata ?| ARRAY['age', 'city'];

-- Check all keys exist
SELECT * FROM users WHERE metadata ?& ARRAY['age', 'city'];

-- Contains check
SELECT * FROM users WHERE metadata @> '{"city": "Boston"}';

-- Contained check
SELECT * FROM users WHERE '{"age": 30}' <@ metadata;
```

### JSON Functions

```sql
-- Keys (top-level)
SELECT jsonb_object_keys(metadata) FROM users;
-- Result: age, city, name

-- Array length
SELECT jsonb_array_length(metadata->'tags') FROM users;

-- Type check
SELECT jsonb_typeof(metadata->'age') FROM users;  -- "number"

-- Pretty print
SELECT jsonb_pretty(metadata) FROM users;

-- Convert to set
SELECT jsonb_each(metadata) FROM users;
-- Result: (key, value) pairs

-- Merge JSON objects
SELECT metadata || '{"country": "USA"}'::jsonb FROM users;
```

---

## JSON Indexing

```sql
-- Create GIN index for fast JSONB queries
CREATE INDEX idx_metadata ON users USING GIN(metadata);

-- Query using index (very fast)
SELECT * FROM users WHERE metadata @> '{"city": "Boston"}';

-- Path-specific index
CREATE INDEX idx_city ON users USING GIN((metadata->'address'->>'city'));

-- Text search index (full-text in JSON)
CREATE INDEX idx_metadata_text ON users USING GIN(
    to_tsvector('english', metadata->>'description')
);
```

---

## Arrays

Native array support.

### Creating Arrays

```sql
-- Create table with array
CREATE TABLE articles (
    articleId INT PRIMARY KEY,
    title VARCHAR(255),
    tags TEXT[]
);

-- Insert arrays
INSERT INTO articles VALUES (
    1,
    'PostgreSQL Tips',
    ARRAY['database', 'sql', 'postgresql']
);

-- Alternative syntax
INSERT INTO articles VALUES (
    2,
    'JSON Guide',
    '{"json", "data", "nosql"}'::text[]
);
```

### Querying Arrays

```sql
-- Access element (1-indexed)
SELECT tags[1] FROM articles;  -- "database"
SELECT tags[1:2] FROM articles;  -- First 2 elements

-- Array length
SELECT array_length(tags, 1) FROM articles;

-- Array contains
SELECT * FROM articles WHERE 'postgresql' = ANY(tags);
SELECT * FROM articles WHERE tags @> ARRAY['postgresql'];

-- Array intersection
SELECT * FROM articles WHERE tags && ARRAY['sql', 'database'];

-- Concatenate
SELECT tags || ARRAY['new-tag'] FROM articles;
```

### Array Functions

```sql
-- Unnest (expand to rows)
SELECT UNNEST(tags) FROM articles;
-- Result: One row per tag

-- Aggregate (reverse of unnest)
SELECT array_agg(tag) FROM (
    SELECT UNNEST(tags) AS tag FROM articles
) sub;

-- Array distinct
SELECT array_agg(DISTINCT tag) FROM (
    SELECT UNNEST(tags) AS tag FROM articles
) sub;

-- Array position
SELECT array_position(tags, 'postgresql') FROM articles;
-- Result: 3 (position in array)
```

---

## Range Types

Represent ranges of values.

### Creating Ranges

```sql
-- Available ranges: int4range, int8range, numrange, daterange, tsrange

-- Date range
CREATE TABLE events (
    eventId INT PRIMARY KEY,
    title VARCHAR(255),
    dateRange daterange  -- From - To dates
);

INSERT INTO events VALUES (
    1,
    'Conference',
    '[2026-06-01, 2026-06-05)'  -- Inclusive start, exclusive end
);

-- Numeric range
SELECT * FROM events 
WHERE numrange(100, 200) @> 150;  -- 150 is in range 100-200
```

### Range Operators

```sql
-- Overlaps
SELECT * FROM events 
WHERE daterange('[2026-06-01, 2026-06-05)') && 
      daterange('[2026-06-03, 2026-06-07)');

-- Contains
SELECT * FROM events WHERE daterange('[2026-06-01, 2026-06-05)') @> '2026-06-02'::date;

-- Contained by
SELECT * FROM events WHERE '2026-06-02'::date <@ daterange('[2026-06-01, 2026-06-05)');

-- Adjacent
SELECT * FROM events 
WHERE daterange('[2026-06-01, 2026-06-05)') -|- daterange('[2026-06-05, 2026-06-10)');
```

---

## Window Functions

Aggregate without collapsing rows.

### ROW_NUMBER & RANK

```sql
SELECT 
    employeeId,
    salary,
    ROW_NUMBER() OVER (ORDER BY salary DESC) AS row_num,
    RANK() OVER (ORDER BY salary DESC) AS rank,
    DENSE_RANK() OVER (ORDER BY salary DESC) AS dense_rank
FROM employees;

-- ROW_NUMBER: 1, 2, 3, 4, 5
-- RANK: 1, 2, 2, 4, 5 (ties get same rank, skips next)
-- DENSE_RANK: 1, 2, 2, 3, 4 (ties, no gap)
```

### LAG & LEAD

```sql
SELECT 
    saleDate,
    revenue,
    LAG(revenue) OVER (ORDER BY saleDate) AS prev_revenue,
    LEAD(revenue) OVER (ORDER BY saleDate) AS next_revenue,
    revenue - LAG(revenue) OVER (ORDER BY saleDate) AS revenue_change
FROM sales;
```

### Frame-Based Aggregation

```sql
SELECT 
    saleDate,
    revenue,
    -- Running total
    SUM(revenue) OVER (ORDER BY saleDate ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total,
    -- 7-day moving average
    AVG(revenue) OVER (ORDER BY saleDate ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS moving_avg
FROM sales;
```

### Partitioned Windows

```sql
SELECT 
    department,
    employeeId,
    salary,
    RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS dept_rank,
    AVG(salary) OVER (PARTITION BY department) AS dept_avg_salary
FROM employees;

-- Separate ranking per department
```

---

## CTEs (Common Table Expressions)

Readable subqueries.

### Simple CTE

```sql
-- Define reusable query
WITH active_users AS (
    SELECT * FROM users WHERE status = 'active'
)
SELECT * FROM active_users WHERE age > 25;

-- Can chain CTEs
WITH active_users AS (
    SELECT * FROM users WHERE status = 'active'
),
user_posts AS (
    SELECT userId, COUNT(*) as postCount
    FROM posts
    GROUP BY userId
)
SELECT au.*, up.postCount
FROM active_users au
LEFT JOIN user_posts up ON au.userId = up.userId;
```

### Recursive CTE

```sql
-- Tree/hierarchy traversal
WITH RECURSIVE category_tree AS (
    -- Anchor: root categories
    SELECT categoryId, name, NULL::INT AS parentId, 0 AS level
    FROM categories
    WHERE parentId IS NULL
    
    UNION ALL
    
    -- Recursive: all children
    SELECT c.categoryId, c.name, c.parentId, ct.level + 1
    FROM categories c
    INNER JOIN category_tree ct ON c.parentId = ct.categoryId
    WHERE ct.level < 5  -- Prevent infinite loop
)
SELECT * FROM category_tree
ORDER BY level, name;
```

### Common Table with Aggregation

```sql
WITH user_stats AS (
    SELECT 
        userId,
        COUNT(*) as postCount,
        AVG(likes) as avgLikes,
        MAX(likes) as maxLikes
    FROM posts
    GROUP BY userId
)
SELECT us.*, u.email
FROM user_stats us
INNER JOIN users u ON us.userId = u.userId
WHERE us.postCount > 10
ORDER BY us.avgLikes DESC;
```

---

## Full-Text Search

Native text search capability.

### Setup

```sql
-- Create FTS index
CREATE TABLE documents (
    docId INT PRIMARY KEY,
    title VARCHAR(255),
    content TEXT,
    ts_vector TSVECTOR
);

-- Generate search vector
UPDATE documents SET ts_vector = 
    to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(content, ''));

-- Create GIN index
CREATE INDEX idx_fts ON documents USING GIN(ts_vector);
```

### Queries

```sql
-- Basic full-text search
SELECT * FROM documents
WHERE ts_vector @@ plainto_tsquery('english', 'postgresql database')
ORDER BY ts_rank(ts_vector, plainto_tsquery('english', 'postgresql database')) DESC;

-- Advanced: AND, OR, NOT
SELECT * FROM documents
WHERE ts_vector @@ to_tsquery('english', 'postgresql & (database | sql) & !mongodb');

-- Phrase search
SELECT * FROM documents
WHERE ts_vector @@ phraseto_tsquery('english', 'relational database');
```

---

## Summary

- **JSONB**: Preferred (binary, indexed, fast)
- **JSON Operators**: ->, ->>, @>, ?, etc.
- **Arrays**: Native array types with operators
- **Ranges**: int4range, daterange, tsrange
- **Window Functions**: ROW_NUMBER, RANK, LAG, LEAD
- **CTEs**: Readable subqueries, recursive support
- **FTS**: Full-text search with ranking

Next: [[03-performance-scaling.md|Performance & Scaling]]

---

**See Also:**
- [[01-overview.md|PostgreSQL Overview]]
- [[../../mysql/01-basics/03-queries-optimization.md|MySQL Query Optimization]]
- [[../../mongodb/01-basics/01-overview.md#aggregation-pipeline|MongoDB Aggregation]]
