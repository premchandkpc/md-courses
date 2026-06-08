---
title: PostgreSQL Overview & Advanced SQL
topic: 08-databases
difficulty: intermediate
time: 30m
paths:
  - backend-junior
  - data
  - backend-senior
---

# PostgreSQL Overview & Advanced SQL

## What is PostgreSQL?

PostgreSQL (Postgres) is a powerful, open-source object-relational database system. Known for advanced SQL features, reliability, and extensibility.

### Key Characteristics

| Aspect | Feature |
|--------|---------|
| Type | Relational (ORDBMS) |
| License | Open Source (PostgreSQL License) |
| SQL | Highly compliant, advanced features |
| ACID | Full transactions, strong consistency |
| Scaling | Vertical + horizontal (via partitioning) |
| Extensibility | Custom types, functions, operators |
| Advanced | JSON, arrays, ranges, full-text search |

---

## Why PostgreSQL?

### Advantages

**1. Advanced SQL Support**
- Window functions
- Common Table Expressions (CTEs)
- Recursive queries
- JSON/JSONB operators
- Range types
- Array types
- Full-text search

**2. Reliability & Data Integrity**
- ACID transactions
- Foreign key constraints
- CHECK constraints
- Unique constraints
- Triggers & rules

**3. Performance**
- Efficient query optimizer
- Partial indexes
- BRIN indexes (big data)
- Parallel query execution

**4. Extensibility**
- Custom data types
- Custom functions (SQL, PL/pgSQL, Python)
- Custom operators
- Procedural languages

**5. No License Restrictions**
- Open source (free)
- Community support
- Commercial support available

---

## When to Use PostgreSQL

### Good Fit ✓
- Complex business applications
- Data warehousing / analytics
- GIS / geospatial data
- Full-text search
- JSON/semi-structured data
- Financial systems
- Regulatory compliance needs
- Complex queries & relationships

### Not Ideal ✗
- Simple key-value lookups
- Horizontally scaled NoSQL
- Schema-less rapid iteration
- Extreme write throughput

---

## PostgreSQL vs MySQL

| Feature | PostgreSQL | MySQL |
|---------|-----------|-------|
| Standard Compliance | Excellent | Good |
| Window Functions | Yes | Yes (8.0+) |
| CTEs | Yes | Yes (8.0+) |
| JSON | JSONB (native) | JSON (limited) |
| Full-text | Native | Limited |
| Partitioning | Native | Requires MyISAM |
| Transactions | Strong | Good (InnoDB) |
| Replication | Streaming | Binlog |
| Scaling | Vertical + Partitions | Vertical + Read replicas |

---

## Data Types

### Numeric

```sql
SMALLINT       -- -32K to 32K
INTEGER        -- Standard 32-bit
BIGINT         -- 64-bit
DECIMAL(10,2)  -- Arbitrary precision (money)
NUMERIC        -- Same as DECIMAL
REAL           -- Single precision float
DOUBLE         -- Double precision float
```

### String

```sql
CHAR(n)           -- Fixed length
VARCHAR(n)        -- Variable, max n
VARCHAR           -- Unlimited
TEXT              -- Unlimited (preferred over VARCHAR)
BYTEA             -- Binary data
UUID              -- Universal unique ID
```

### Advanced Types

```sql
JSON             -- JSON document
JSONB            -- Binary JSON (queryable, preferred)
ARRAY            -- Arrays of any type: INTEGER[], TEXT[]
RANGE            -- INT4RANGE, DATERANGE, etc.
ENUM             -- Enumerated type
HSTORE           -- Key-value store
GEOMETRY/POINT   -- Geospatial data
```

### Date/Time

```sql
DATE               -- YYYY-MM-DD
TIME               -- HH:MM:SS
TIMESTAMP          -- Date + time
TIMESTAMP WITH TZ  -- With timezone info
INTERVAL           -- Time periods
```

---

## JSON/JSONB

Native JSON support with operators.

```sql
-- Create table with JSONB
CREATE TABLE users (
    userId INT PRIMARY KEY,
    email VARCHAR(255),
    metadata JSONB  -- Better performance than JSON
);

-- Insert JSON data
INSERT INTO users VALUES (
    1, 
    'john@example.com',
    '{"age": 30, "city": "Boston", "tags": ["vip", "verified"]}'
);

-- Query JSON fields
SELECT metadata->>'age' AS age FROM users;  -- Returns text: "30"
SELECT (metadata->>'age')::INT AS age FROM users;  -- Cast to integer

-- Array access
SELECT metadata->'tags'->0 AS firstTag FROM users;

-- Check key exists
SELECT * FROM users WHERE metadata ? 'age';

-- JSONB operators
SELECT * FROM users WHERE metadata @> '{"city": "Boston"}';  -- Contains
```

---

## Arrays

```sql
-- Create table with array column
CREATE TABLE articles (
    articleId INT PRIMARY KEY,
    title VARCHAR(255),
    tags TEXT[],
    scores INT[]
);

-- Insert arrays
INSERT INTO articles VALUES (
    1,
    'PostgreSQL Tips',
    ARRAY['database', 'sql', 'postgresql'],
    ARRAY[95, 87, 92]
);

-- Query arrays
SELECT tags[1] FROM articles;  -- First element
SELECT array_length(tags, 1) AS tagCount FROM articles;

-- Array contains
SELECT * FROM articles WHERE 'postgresql' = ANY(tags);

-- Unnest array to rows
SELECT UNNEST(tags) FROM articles;
```

---

## Window Functions

Aggregate without collapsing rows.

```sql
CREATE TABLE sales (
    saleId INT,
    month VARCHAR(10),
    revenue DECIMAL(10, 2)
);

-- Running total
SELECT 
    saleId,
    month,
    revenue,
    SUM(revenue) OVER (ORDER BY saleId) AS runningTotal
FROM sales;

-- Rank within group
SELECT 
    saleId,
    revenue,
    RANK() OVER (ORDER BY revenue DESC) AS rank,
    DENSE_RANK() OVER (ORDER BY revenue DESC) AS denseRank
FROM sales;

-- Compare to previous/next
SELECT 
    saleId,
    revenue,
    LAG(revenue) OVER (ORDER BY saleId) AS prevRevenue,
    LEAD(revenue) OVER (ORDER BY saleId) AS nextRevenue
FROM sales;
```

---

## CTEs (Common Table Expressions)

Readable subqueries with WITH clause.

```sql
-- Simple CTE
WITH active_users AS (
    SELECT * FROM users WHERE status = 'active'
)
SELECT * FROM active_users WHERE age > 25;

-- Recursive CTE (tree/hierarchy)
WITH RECURSIVE hierarchy AS (
    -- Base case: top-level categories
    SELECT categoryId, name, NULL::INT AS parentId, 0 AS level
    FROM categories
    WHERE parentId IS NULL
    
    UNION ALL
    
    -- Recursive case: all children
    SELECT c.categoryId, c.name, c.parentId, h.level + 1
    FROM categories c
    INNER JOIN hierarchy h ON c.parentId = h.categoryId
    WHERE h.level < 5  -- Prevent infinite recursion
)
SELECT * FROM hierarchy;
```

---

## Indexes

```sql
-- B-tree (default, most common)
CREATE INDEX idx_email ON users(email);

-- Hash index (equality only)
CREATE INDEX idx_hash ON users USING HASH(email);

-- BRIN (Block Range Index, for large data)
CREATE INDEX idx_timestamp ON logs USING BRIN(createdAt);

-- Partial index (indexed subset)
CREATE INDEX idx_active_users ON users(email) WHERE status = 'active';

-- Expression index
CREATE INDEX idx_upper_email ON users(UPPER(email));

-- Multi-column
CREATE INDEX idx_user_date ON posts(userId, createdAt DESC);
```

---

## Functions

Create reusable logic.

```sql
-- SQL function
CREATE FUNCTION get_user_post_count(p_userId INT) RETURNS INT AS $$
    SELECT COUNT(*) FROM posts WHERE userId = p_userId;
$$ LANGUAGE SQL;

-- PL/pgSQL function
CREATE FUNCTION calculate_discount(p_amount DECIMAL, p_customer_type VARCHAR)
RETURNS DECIMAL AS $$
DECLARE
    discount DECIMAL := 0;
BEGIN
    IF p_customer_type = 'vip' THEN
        discount := p_amount * 0.20;
    ELSIF p_customer_type = 'premium' THEN
        discount := p_amount * 0.10;
    END IF;
    RETURN p_amount - discount;
END;
$$ LANGUAGE plpgsql;

-- Use function
SELECT calculate_discount(100.00, 'vip');
```

---

## Triggers

Automatic actions on events.

```sql
CREATE TABLE audit_log (
    logId SERIAL PRIMARY KEY,
    tableName VARCHAR(50),
    operation VARCHAR(10),
    userId INT,
    changedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger on UPDATE
CREATE TRIGGER log_user_update
AFTER UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION log_audit('users', 'UPDATE');

CREATE FUNCTION log_audit(p_table TEXT, p_op TEXT)
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (tableName, operation, userId)
    VALUES (p_table, p_op, NEW.userId);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

## ACID & Transactions

```sql
BEGIN TRANSACTION;

UPDATE accounts SET balance = balance - 100 WHERE accountId = 1;
UPDATE accounts SET balance = balance + 100 WHERE accountId = 2;

-- Savepoints for partial rollback
SAVEPOINT before_reversal;

DELETE FROM transactions WHERE transactionId = 999;

-- Rollback to savepoint
ROLLBACK TO before_reversal;

COMMIT;
```

---

## Full-Text Search

Native text search capability.

```sql
-- Create full-text search index
CREATE TABLE articles (
    articleId INT PRIMARY KEY,
    title VARCHAR(255),
    content TEXT,
    tsv TSVECTOR
);

-- Create index for FTS
CREATE INDEX idx_fts ON articles USING GIN(tsv);

-- Generate search vector
UPDATE articles SET tsv = 
    to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(content, ''));

-- Query with full-text search
SELECT title FROM articles 
WHERE tsv @@ plainto_tsquery('english', 'postgresql database')
ORDER BY ts_rank(tsv, plainto_tsquery('english', 'postgresql database')) DESC;
```

---

## Summary

- **Advanced SQL**: Window functions, CTEs, recursive queries
- **JSONB**: Native JSON with operators
- **Arrays & Ranges**: Complex data structures
- **Functions**: Custom SQL & PL/pgSQL
- **Triggers**: Automation & auditing
- **Full-Text Search**: Native text search
- **Performance**: Multiple index types, parallel queries
- **Extensibility**: Custom types, operators, functions

Next: [[02-advanced-queries.md|Advanced Queries & Optimization]]

---

**See Also:**
- [[../../mysql/01-basics/01-overview.md|MySQL Overview]]
- [[../../dynamodb/01-basics/01-overview.md|DynamoDB Overview]]
