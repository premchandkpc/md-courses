---
title: MySQL Queries & Optimization
topic: 08-databases
difficulty: intermediate
time: 30m
paths:
  - backend-junior
  - data
  - backend-senior
---

# MySQL Queries & Optimization

## SELECT Query Structure

### Basic SELECT

```sql
-- All columns
SELECT * FROM users;

-- Specific columns (PREFERRED)
SELECT userId, email, firstName FROM users;

-- With aliases
SELECT userId AS id, email AS emailAddress, firstName AS name FROM users;
```

**Why specific columns?**
- Reduces network bandwidth
- Clearer intent
- Better for index utilization
- Matches SELECT *

### WHERE Clause (Filtering)

```sql
-- Equality
SELECT * FROM users WHERE status = 'active';

-- Comparison
SELECT * FROM users WHERE age > 25 AND age < 40;
SELECT * FROM users WHERE salary >= 50000;

-- String matching
SELECT * FROM users WHERE email LIKE '%@example.com';
SELECT * FROM users WHERE firstName LIKE 'J%';  -- Starts with J

-- IN list
SELECT * FROM users WHERE status IN ('active', 'premium', 'vip');

-- BETWEEN
SELECT * FROM users WHERE age BETWEEN 25 AND 40;

-- NULL check
SELECT * FROM users WHERE middleName IS NULL;
SELECT * FROM users WHERE middleName IS NOT NULL;

-- Multiple conditions
SELECT * FROM users 
WHERE status = 'active' 
AND age > 25 
AND (city = 'Boston' OR city = 'NYC');
```

### ORDER BY (Sorting)

```sql
-- Ascending (default)
SELECT * FROM posts ORDER BY createdAt ASC;

-- Descending
SELECT * FROM posts ORDER BY createdAt DESC;

-- Multiple columns
SELECT * FROM posts 
ORDER BY userId ASC, createdAt DESC;

-- With limit
SELECT * FROM posts 
ORDER BY createdAt DESC 
LIMIT 10;

-- Pagination
SELECT * FROM posts 
ORDER BY postId 
LIMIT 10 OFFSET 20;  -- Skip 20, get 10
```

---

## JOINs (Multi-Table Queries)

### INNER JOIN

Returns rows matching in both tables.

```sql
-- Get posts with user info
SELECT 
    u.userId,
    u.email,
    p.postId,
    p.title,
    p.createdAt
FROM users u
INNER JOIN posts p ON u.userId = p.userId
WHERE u.status = 'active'
ORDER BY p.createdAt DESC;

-- ❌ Common mistake: Missing ON clause
SELECT u.userId, p.postId FROM users u INNER JOIN posts p;  
-- Result: Cartesian product (user_count * post_count rows!)
```

### LEFT JOIN

All rows from left table, matching rows from right.

```sql
-- Get all users with their post count (even 0 posts)
SELECT 
    u.userId,
    u.email,
    COUNT(p.postId) AS postCount
FROM users u
LEFT JOIN posts p ON u.userId = p.userId
GROUP BY u.userId
ORDER BY postCount DESC;
```

### RIGHT JOIN

All rows from right table, matching rows from left.

```sql
-- All posts, even if user deleted
SELECT 
    p.postId,
    p.title,
    u.email
FROM users u
RIGHT JOIN posts p ON u.userId = p.userId;

-- ⚠️ Usually rewrite as LEFT JOIN instead
SELECT 
    p.postId,
    p.title,
    u.email
FROM posts p
LEFT JOIN users u ON u.userId = p.userId;
```

### Multiple JOINs

```sql
SELECT 
    u.email,
    p.title,
    c.content,
    COUNT(l.likeId) AS likeCount
FROM users u
LEFT JOIN posts p ON u.userId = p.userId
LEFT JOIN comments c ON p.postId = c.postId
LEFT JOIN likes l ON p.postId = l.postId
GROUP BY u.userId, p.postId, c.commentId;
```

---

## Aggregation

Combine multiple rows into summary.

```sql
-- COUNT
SELECT COUNT(*) AS totalUsers FROM users;
SELECT COUNT(middleName) FROM users;  -- Counts non-NULL only

-- SUM
SELECT SUM(salary) AS totalPayroll FROM employees;

-- AVG
SELECT AVG(salary) AS averageSalary FROM employees;

-- MIN / MAX
SELECT 
    MIN(salary) AS lowestSalary,
    MAX(salary) AS highestSalary
FROM employees;

-- GROUP BY
SELECT 
    departmentId,
    COUNT(*) AS employeeCount,
    AVG(salary) AS avgSalary
FROM employees
GROUP BY departmentId
HAVING COUNT(*) > 5;  -- Filter groups

-- GROUP BY multiple columns
SELECT 
    department,
    status,
    COUNT(*) AS count
FROM employees
GROUP BY department, status
ORDER BY department, status;
```

---

## Subqueries

Query within query.

```sql
-- Scalar subquery (returns 1 value)
SELECT * FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);

-- IN subquery
SELECT * FROM employees
WHERE departmentId IN (
    SELECT departmentId FROM departments WHERE location = 'Boston'
);

-- EXISTS subquery
SELECT u.userId, u.email
FROM users u
WHERE EXISTS (
    SELECT 1 FROM posts p WHERE p.userId = u.userId
);

-- Correlated subquery (slower, use JOIN instead)
SELECT u.userId, u.email,
    (SELECT COUNT(*) FROM posts WHERE userId = u.userId) AS postCount
FROM users u;

-- ✓ Better: Use JOIN instead
SELECT u.userId, u.email, COUNT(p.postId) AS postCount
FROM users u
LEFT JOIN posts p ON u.userId = p.userId
GROUP BY u.userId;
```

---

## Query Optimization

### Index Selection

```sql
-- ❌ Without index: Full table scan
SELECT * FROM users WHERE email = 'john@example.com';

-- ✓ With index: Direct lookup
CREATE INDEX idx_email ON users(email);
SELECT * FROM users WHERE email = 'john@example.com';

-- Check if index used
EXPLAIN SELECT * FROM users WHERE email = 'john@example.com';

-- Results show "key: idx_email" if index used
-- Shows "key: NULL" if full scan (bad!)
```

### EXPLAIN Query Plans

```sql
EXPLAIN SELECT * FROM users WHERE age > 25 AND status = 'active';

-- Output:
-- id | select_type | table | type | possible_keys | key | rows | Extra
-- 1  | SIMPLE      | users | ALL  | idx_status    | NULL| 1000 | Using where

-- ✓ GOOD: "type: ref" or "type: eq_ref" (uses index)
-- ⚠️ WARNING: "type: ALL" (full table scan)

-- Get more details
EXPLAIN FORMAT=JSON SELECT * FROM users WHERE age > 25;
```

### Index Best Practices

```sql
-- ❌ Bad: Index on high-cardinality column (bad selectivity)
CREATE INDEX idx_name ON users(firstName);
-- firstName has 1M values out of 1M rows (100% unique)
-- Index barely helps, full scan faster

-- ✓ Good: Index on selective column
CREATE INDEX idx_status ON users(status);
-- Status has 5 values (active, inactive, banned, etc)
-- Index eliminates 80% of rows efficiently

-- ❌ Bad: Too many indexes
CREATE INDEX idx1 ON users(firstName);
CREATE INDEX idx2 ON users(lastName);
CREATE INDEX idx3 ON users(status);
CREATE INDEX idx4 ON users(age);
-- Each index: storage cost + write overhead

-- ✓ Good: Strategic composite indexes
CREATE INDEX idx_lookup ON users(status, email);
-- Covers both lookups efficiently

-- Index on wrong column type
-- ❌ Bad: Index on BLOB or LONGTEXT
-- ✓ Use for VARCHAR, INT, DATE
```

### Query Optimization Techniques

**1. Use LIMIT**
```sql
-- ❌ Get all 1M users, sort, take 10
SELECT * FROM users ORDER BY salary DESC;

-- ✓ Get top 10 only
SELECT * FROM users ORDER BY salary DESC LIMIT 10;
```

**2. Projection (Select needed columns)**
```sql
-- ❌ Fetch everything
SELECT * FROM large_table;

-- ✓ Only needed columns
SELECT userId, email FROM users;
```

**3. Avoid Functions in WHERE**
```sql
-- ❌ Index not used (UPPER not indexed)
SELECT * FROM users WHERE UPPER(email) = 'JOHN@EXAMPLE.COM';

-- ✓ Index used
SELECT * FROM users WHERE email = 'john@example.com';

-- If must use function: create expression index
CREATE INDEX idx_upper_email ON users(UPPER(email));
```

**4. Avoid NOT IN on large sets**
```sql
-- ❌ Slow with large subquery
SELECT * FROM posts WHERE userId NOT IN (
    SELECT userId FROM users WHERE status = 'banned'
);

-- ✓ Better with JOIN
SELECT p.* FROM posts p
LEFT JOIN users u ON p.userId = u.userId AND u.status = 'banned'
WHERE u.userId IS NULL;
```

**5. Denormalization for read-heavy**
```sql
-- Normalized (requires join)
SELECT u.email, COUNT(p.postId) AS postCount
FROM users u
LEFT JOIN posts p ON u.userId = p.userId
GROUP BY u.userId;

-- Denormalized (direct read)
ALTER TABLE users ADD postCount INT DEFAULT 0;
-- Update with trigger when post created/deleted
-- Direct read: SELECT email, postCount FROM users;
```

---

## Real-World Optimization Examples

### Example 1: User Search

```sql
-- ❌ Slow: Full table scan + sorting
SELECT * FROM users 
WHERE firstName LIKE '%john%' 
ORDER BY createdAt DESC;

-- ✓ Better: Indexes on search columns
CREATE INDEX idx_firstName ON users(firstName);
CREATE INDEX idx_createdAt ON users(createdAt DESC);

SELECT userId, email, firstName FROM users
WHERE firstName LIKE 'john%'  -- Left anchor (uses index)
ORDER BY createdAt DESC
LIMIT 20;
```

### Example 2: Feed (User Posts + Friends)

```sql
-- ❌ Multiple subqueries
SELECT * FROM posts
WHERE userId IN (SELECT friendId FROM friendships WHERE userId = 123)
OR userId = 123
ORDER BY createdAt DESC;

-- ✓ Better: Single JOIN + UNION
SELECT p.* FROM posts p
INNER JOIN friendships f ON p.userId = f.friendId
WHERE f.userId = 123
UNION
SELECT p.* FROM posts p WHERE p.userId = 123
ORDER BY createdAt DESC
LIMIT 50;

-- ✓ With indexes
CREATE INDEX idx_friend ON friendships(userId);
CREATE INDEX idx_user_created ON posts(userId, createdAt);
```

### Example 3: Leaderboard

```sql
-- ❌ Calculates all scores, sorts all
SELECT * FROM scores ORDER BY score DESC;

-- ✓ Better: Top N only, with rank
SELECT 
    userId,
    score,
    RANK() OVER (ORDER BY score DESC) AS rank
FROM scores
LIMIT 100;

-- With index
CREATE INDEX idx_score DESC ON scores(score DESC);
```

---

## Common Performance Issues

### N+1 Query Problem

```javascript
// ❌ Bad (N+1): 1 query for users + 1 query per user
const users = db.query("SELECT * FROM users");
for (const user of users) {
    user.posts = db.query("SELECT * FROM posts WHERE userId = ?", user.id);
}
// Total: 1 + N queries!

// ✓ Good: Single query with JOIN
const result = db.query(`
    SELECT u.*, p.*
    FROM users u
    LEFT JOIN posts p ON u.id = p.userId
`);
```

### Missing Indexes

```sql
-- ❌ Frequently queried column, no index
SELECT * FROM orders WHERE customerId = 123;  -- Full scan

-- ✓ Add index
CREATE INDEX idx_customerId ON orders(customerId);
```

### Inefficient GROUP BY

```sql
-- ❌ Groups by many columns
SELECT user_id, post_id, date, COUNT(*) 
FROM interactions 
GROUP BY user_id, post_id, date;

-- ✓ Group by what matters
SELECT user_id, COUNT(*) as interaction_count
FROM interactions 
GROUP BY user_id;
```

---

## Summary

- **SELECT**: Specify columns, not *
- **WHERE**: Use indexes, avoid functions
- **JOIN**: Choose correct type (INNER, LEFT)
- **ORDER BY**: Use LIMIT, have indexes
- **Aggregation**: GROUP BY strategically
- **Subqueries**: Prefer JOIN when possible
- **Indexes**: Strategic placement, not everywhere
- **EXPLAIN**: Analyze query plans
- **Denormalization**: For read-heavy workloads

Next: [[../02-intermediate/01-transactions-locks.md|Transactions & Locking]]

---

**See Also:**
- [[01-overview.md|MySQL Overview]]
- [[02-schema-design.md|Schema Design]]
- [[../../postgres/01-basics/01-overview.md|PostgreSQL Advanced Queries]]
