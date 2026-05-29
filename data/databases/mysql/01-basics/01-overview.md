# MySQL Overview & Fundamentals

## What is MySQL?

MySQL is the world's most popular open-source relational database management system (RDBMS). Built on the relational model, it stores data in structured tables with predefined schemas.

### Key Characteristics

| Aspect | Feature |
|--------|---------|
| Type | Relational (RDBMS) |
| Model | Tables, rows, columns, relationships |
| License | Open Source (GPL) |
| ACID | Full transactions (with InnoDB) |
| Storage | Multiple engines (InnoDB, MyISAM) |
| Scaling | Vertical scaling, replication |
| Performance | Optimized for read-heavy workloads |

---

## Why MySQL?

### Advantages

**1. Open Source & Cost**
- Free to download, use, modify
- No licensing fees
- Active community support

**2. Reliability**
- ACID transactions (InnoDB)
- Data integrity with constraints
- Automatic recovery

**3. Performance**
- Fast read operations
- Optimized query execution
- Effective indexing

**4. Simplicity**
- Standard SQL syntax
- Easy to learn
- Widely documented

**5. Ubiquity**
- LAMP stack standard
- Runs everywhere (Linux, Windows, Mac)
- Massive ecosystem (WordPress, Drupal, etc.)

---

## When to Use MySQL

### Good Fit ✓
- Web applications (WordPress, Magento)
- E-commerce platforms
- Content management systems
- Financial/business apps
- Social networks
- User authentication systems
- Session storage
- Transactional data

### Not Ideal ✗
- Massive distributed systems
- Real-time analytics (terabytes)
- Unstructured data (documents)
- Time series at extreme scale
- NoSQL use cases (flexible schema)

---

## Architecture

```
Application Layer
    ↓
MySQL Connection Pool
    ↓
Query Parser & Optimizer
    ↓
Storage Engines
├── InnoDB (ACID, transactions) ← Default
├── MyISAM (fast, no transactions)
└── Others (Archive, NDB, etc.)
    ↓
Disk (tables, indexes, logs)
```

---

## Data Types

### Numeric Types

| Type | Range | Use Case |
|------|-------|----------|
| TINYINT | -128 to 127 | Boolean, status flags |
| SMALLINT | -32K to 32K | Small numbers |
| INT | -2B to 2B | IDs, counts, integers |
| BIGINT | -9.2E18 to 9.2E18 | Large numbers, timestamps |
| DECIMAL(10,2) | Fixed precision | Money, percentages |
| FLOAT, DOUBLE | Variable precision | Approximate decimals |

### String Types

| Type | Max Size | Use Case |
|------|----------|----------|
| VARCHAR(255) | 255 bytes | Names, emails, short text |
| CHAR(10) | Fixed length | Fixed-format data |
| TEXT | 65KB | Long text, descriptions |
| LONGTEXT | 4GB | Large documents |
| BLOB | 65KB | Binary data, images |

### Date/Time Types

| Type | Format | Use Case |
|------|--------|----------|
| DATE | YYYY-MM-DD | Birth dates, events |
| TIME | HH:MM:SS | Time of day |
| DATETIME | YYYY-MM-DD HH:MM:SS | Timestamps |
| TIMESTAMP | Seconds since 1970 | Auto-update, system time |

---

## Table Creation

### Basic Table

```sql
CREATE TABLE users (
    userId INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    firstName VARCHAR(100) NOT NULL,
    lastName VARCHAR(100) NOT NULL,
    age TINYINT,
    balance DECIMAL(10, 2) DEFAULT 0.00,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Table with Foreign Keys (Relationships)

```sql
CREATE TABLE posts (
    postId INT AUTO_INCREMENT PRIMARY KEY,
    userId INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content LONGTEXT,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userId) REFERENCES users(userId) ON DELETE CASCADE
);

CREATE TABLE comments (
    commentId INT AUTO_INCREMENT PRIMARY KEY,
    postId INT NOT NULL,
    userId INT NOT NULL,
    content TEXT NOT NULL,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (postId) REFERENCES posts(postId) ON DELETE CASCADE,
    FOREIGN KEY (userId) REFERENCES users(userId) ON DELETE CASCADE
);
```

**Key Constraints:**
- PRIMARY KEY: Unique identifier per row
- UNIQUE: No duplicates
- NOT NULL: Required field
- FOREIGN KEY: Relationship to another table
- DEFAULT: Default value
- AUTO_INCREMENT: Auto-generated numbers

---

## Basic Operations (CRUD)

### Create (INSERT)

```sql
-- Single row
INSERT INTO users (email, firstName, lastName, age)
VALUES ('john@example.com', 'John', 'Doe', 30);

-- Multiple rows
INSERT INTO users (email, firstName, lastName, age)
VALUES 
    ('jane@example.com', 'Jane', 'Smith', 28),
    ('bob@example.com', 'Bob', 'Johnson', 35);

-- From another table
INSERT INTO users (email, firstName, lastName)
SELECT email, firstName, lastName FROM temp_users;
```

### Read (SELECT)

```sql
-- All columns
SELECT * FROM users;

-- Specific columns
SELECT userId, email, firstName FROM users;

-- With WHERE clause
SELECT * FROM users WHERE age > 25;

-- With conditions
SELECT * FROM users 
WHERE email LIKE '%@example.com' 
AND age BETWEEN 20 AND 40;

-- Ordering
SELECT * FROM users ORDER BY createdAt DESC LIMIT 10;
```

### Update (UPDATE)

```sql
-- Update single row
UPDATE users 
SET firstName = 'Jonathan'
WHERE userId = 1;

-- Update multiple rows
UPDATE users
SET balance = balance + 50
WHERE createdAt > '2026-01-01';

-- Update with calculation
UPDATE users
SET age = YEAR(CURDATE()) - YEAR(birthDate)
WHERE birthDate IS NOT NULL;
```

### Delete (DELETE)

```sql
-- Delete single row
DELETE FROM users WHERE userId = 1;

-- Delete with condition
DELETE FROM users WHERE age < 18;

-- Delete all (dangerous!)
DELETE FROM users;
```

---

## Indexes

Speed up queries by organizing data.

### Single Column Index

```sql
-- Create index
CREATE INDEX idx_email ON users(email);

-- Query uses index
SELECT * FROM users WHERE email = 'john@example.com';  -- Fast!

-- Drop index
DROP INDEX idx_email ON users;
```

### Composite Index

```sql
-- Multiple columns
CREATE INDEX idx_user_created ON users(userId, createdAt);

-- Useful for queries like:
SELECT * FROM posts 
WHERE userId = 5 AND createdAt > '2026-01-01';

-- Also covers queries using just userId
SELECT * FROM posts WHERE userId = 5;  -- Uses index
```

### Index Types

| Type | Speed | Use Case |
|------|-------|----------|
| UNIQUE | Very fast | Email, username lookup |
| PRIMARY KEY | Very fast | ID lookup |
| INDEX | Fast | WHERE clauses, JOIN conditions |
| FULLTEXT | Medium | Text search |

---

## Joins (Multi-Table Queries)

### INNER JOIN

```sql
-- Get posts with user info
SELECT u.email, p.title, p.createdAt
FROM users u
INNER JOIN posts p ON u.userId = p.userId
WHERE u.userId = 5;

-- Only returns rows that match in both tables
```

### LEFT JOIN

```sql
-- Get all users, even if no posts
SELECT u.email, COUNT(p.postId) AS postCount
FROM users u
LEFT JOIN posts p ON u.userId = p.userId
GROUP BY u.userId;

-- Users with 0 posts still appear (postCount = 0)
```

### Multiple Joins

```sql
SELECT 
    u.email,
    p.title,
    c.content
FROM users u
LEFT JOIN posts p ON u.userId = p.userId
LEFT JOIN comments c ON p.postId = c.postId
ORDER BY u.email, p.createdAt;
```

---

## Transactions (ACID)

Ensure multiple operations succeed or fail together.

```sql
START TRANSACTION;

UPDATE accounts SET balance = balance - 100 WHERE accountId = 1;
UPDATE accounts SET balance = balance + 100 WHERE accountId = 2;

-- If both succeed, commit
COMMIT;

-- If error occurs, rollback
-- ROLLBACK;
```

**ACID Properties:**
- **Atomicity**: All or nothing
- **Consistency**: Valid state before and after
- **Isolation**: Concurrent transactions don't interfere
- **Durability**: Committed data survives failures

---

## Storage Engines

### InnoDB (Recommended)

```sql
CREATE TABLE users (
    userId INT PRIMARY KEY,
    email VARCHAR(255)
) ENGINE=InnoDB;
```

**Features:**
- ACID transactions
- Foreign key support
- Crash recovery
- Row-level locking
- Better concurrency

**Default since MySQL 5.5**

### MyISAM (Legacy)

```sql
CREATE TABLE logs (
    logId INT PRIMARY KEY,
    message TEXT
) ENGINE=MyISAM;
```

**Features:**
- Fast for reads
- No transactions
- Table-level locking
- Use only for read-only or legacy systems

---

## Best Practices

| Practice | Why |
|----------|-----|
| Use InnoDB | Better for data integrity |
| Set PRIMARY KEY | Every table needs unique identifier |
| Use VARCHAR not CHAR | Saves space |
| DECIMAL for money | Avoids floating point errors |
| Foreign keys | Maintain referential integrity |
| Indexes on WHERE/JOIN | Speed up queries |
| Normalize schema | Reduces redundancy |
| Transactions for multi-step | Ensures consistency |

---

## Billing (Self-Hosted vs RDS)

### Self-Hosted (Server)
- One-time: Server hardware
- Ongoing: Server maintenance, backups, updates
- Flexible: Full control

### AWS RDS (Managed)
- Per instance type per hour
- Automated backups, patches, replication
- High availability available

---

## Summary

- **Relational**: Tables, rows, columns with relationships
- **ACID**: Full transactions with InnoDB
- **Open Source**: Free, widely used
- **Standard SQL**: Easy to learn and use
- **Best For**: Web apps, transactional data, multi-table queries
- **Scaling**: Vertical scaling, replication for reads

Next: [[02-schema-design.md|Schema Design & Normalization]]

---

**See Also:**
- [[../../README.md|Back to Database Guide]]
- [[../../dynamodb/01-basics/01-overview.md|DynamoDB Overview (Comparison)]]
- [[../../postgres/01-basics/01-overview.md|PostgreSQL Overview]]
