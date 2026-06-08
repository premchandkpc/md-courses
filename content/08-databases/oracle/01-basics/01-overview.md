---
title: Oracle Database Overview
topic: 08-databases
difficulty: intermediate
time: 30m
paths:
  - backend-junior
  - data
  - backend-senior
---

# Oracle Database Overview

## What is Oracle Database?

Oracle Database is a powerful enterprise-grade relational database management system. Built for mission-critical systems requiring maximum performance, scalability, and security.

### Key Characteristics

| Aspect | Feature |
|--------|---------|
| Type | Enterprise Relational (RDBMS) |
| Licensing | Commercial (expensive) |
| Performance | Extreme optimization for large scale |
| Security | Industry-leading (encryption, auditing) |
| Scalability | Handles petabytes |
| HA/DR | Advanced replication & failover |
| Partitioning | Native range, list, hash |
| Compression | Transparent data compression |

---

## Why Oracle?

### Advantages

**1. Enterprise Grade**
- 99.99%+ uptime SLA
- Automatic failover
- Data recovery
- Disaster recovery

**2. Performance at Scale**
- Handles terabyte+ datasets
- Parallel query execution
- Advanced caching
- Query optimizer supreme

**3. Security**
- Encryption (transparent, network)
- Row-level security
- Advanced auditing
- Virtual Private Database

**4. Advanced Features**
- Partitioning (range, list, hash)
- Compression (table, index)
- Materialized views
- Advanced analytics

**5. Industry Trust**
- 40+ years in market
- Used by 10K+ companies
- Regulatory compliance ready
- Proven stability

---

## When to Use Oracle

### Good Fit ✓
- Large-scale enterprises
- Mission-critical systems
- Extreme performance needs
- Complex regulatory requirements
- 24/7 availability required
- Petabyte-scale data
- Advanced security
- Financial institutions

### Cost Consideration ✗
- Expensive licensing
- Complex administration
- Requires specialized DBAs
- Not for small projects
- Overkill for simple apps

---

## Architecture

```
Application Layer
    ↓
Connection Pool (Connection Manager)
    ↓
Shared Pool (Parser, Optimizer, Cache)
    ↓
PGA (Process Global Area - per connection)
    ↓
Buffer Cache (Data in memory)
    ↓
Redo Log Buffer (Transaction log)
    ↓
Storage (Tablespaces → Datafiles)
```

---

## Tablespaces & Storage

Data organized into logical tablespaces.

```sql
-- Create tablespace
CREATE TABLESPACE users_data
  DATAFILE '/oracle/data/users.dbf' SIZE 100M
  AUTOEXTEND ON NEXT 10M
  MAXSIZE 1000M;

-- Create table in tablespace
CREATE TABLE users (
  userId NUMBER PRIMARY KEY,
  email VARCHAR2(255) NOT NULL UNIQUE,
  firstName VARCHAR2(100),
  createdDate DATE DEFAULT SYSDATE
)
TABLESPACE users_data;

-- System tablespace (metadata)
-- Temp tablespace (sorting)
-- Undo tablespace (transaction rollback)
```

---

## Data Types

### Numeric

```sql
NUMBER              -- Generic numeric
NUMBER(10,2)        -- 10 digits, 2 decimal places
INTEGER             -- Whole numbers
BINARY_FLOAT        -- 32-bit float
BINARY_DOUBLE       -- 64-bit double
```

### String

```sql
VARCHAR2(255)       -- Variable-length string (preferred)
CHAR(10)            -- Fixed-length
CLOB                -- Character large object (4GB)
NVARCHAR2           -- Unicode variable
```

### Date/Time

```sql
DATE                -- Date & time
TIMESTAMP           -- More precision
TIMESTAMP WITH TIME ZONE
INTERVAL            -- Time periods
```

---

## Basic Operations

### Create

```sql
CREATE TABLE employees (
  employeeId NUMBER PRIMARY KEY,
  firstName VARCHAR2(100) NOT NULL,
  lastName VARCHAR2(100) NOT NULL,
  email VARCHAR2(255) UNIQUE,
  hireDate DATE DEFAULT SYSDATE,
  salary NUMBER(10,2)
);

-- Sequences for auto-increment
CREATE SEQUENCE emp_seq
  START WITH 1
  INCREMENT BY 1;

-- Insert with sequence
INSERT INTO employees 
  (employeeId, firstName, lastName, email, salary)
VALUES 
  (emp_seq.NEXTVAL, 'John', 'Doe', 'john@example.com', 75000);
```

### Read

```sql
-- Basic query
SELECT * FROM employees WHERE salary > 50000;

-- With column alias
SELECT firstName, lastName, salary * 12 AS annualSalary
FROM employees;

-- With ORDER BY
SELECT * FROM employees ORDER BY salary DESC;

-- Pagination (Oracle 12c+)
SELECT * FROM employees
ORDER BY employeeId
OFFSET 10 ROWS FETCH NEXT 10 ROWS ONLY;
```

### Update

```sql
UPDATE employees 
SET salary = salary * 1.10 
WHERE departmentId = 10;
```

### Delete

```sql
DELETE FROM employees WHERE employeeId = 123;
```

---

## Constraints

Enforce data quality.

```sql
CREATE TABLE users (
  userId NUMBER PRIMARY KEY,
  email VARCHAR2(255) NOT NULL UNIQUE,
  age NUMBER CHECK (age >= 18),
  status VARCHAR2(20) DEFAULT 'active' NOT NULL,
  departmentId NUMBER REFERENCES departments(departmentId)
);
```

---

## Indexes

Multiple index types for performance.

```sql
-- B-tree index (default, most common)
CREATE INDEX idx_email ON users(email);

-- Composite index
CREATE INDEX idx_dept_salary ON employees(departmentId, salary DESC);

-- Unique index
CREATE UNIQUE INDEX idx_ssn ON employees(ssn);

-- Bitmap index (for low-cardinality columns)
CREATE BITMAP INDEX idx_status ON users(status);

-- Function-based index
CREATE INDEX idx_upper_email ON users(UPPER(email));

-- Partial index (in 12.2+)
CREATE INDEX idx_active_users ON users(userId) WHERE status = 'active';
```

---

## Partitioning

Split large tables for performance.

```sql
-- Range partitioning (by date)
CREATE TABLE sales (
  saleId NUMBER,
  saleDate DATE,
  amount NUMBER
)
PARTITION BY RANGE (saleDate) (
  PARTITION sales_2025 VALUES LESS THAN (TO_DATE('2026-01-01', 'YYYY-MM-DD')),
  PARTITION sales_2026 VALUES LESS THAN (TO_DATE('2027-01-01', 'YYYY-MM-DD')),
  PARTITION sales_future VALUES LESS THAN (MAXVALUE)
);

-- List partitioning (by region)
CREATE TABLE customers (
  customerId NUMBER,
  region VARCHAR2(20)
)
PARTITION BY LIST (region) (
  PARTITION us_east VALUES ('NY', 'NJ', 'PA'),
  PARTITION us_west VALUES ('CA', 'WA', 'OR'),
  PARTITION intl VALUES (DEFAULT)
);

-- Hash partitioning (automatic distribution)
CREATE TABLE products (
  productId NUMBER,
  productName VARCHAR2(255)
)
PARTITION BY HASH (productId)
PARTITIONS 8;
```

---

## Transactions

```sql
BEGIN TRANSACTION;

UPDATE accounts SET balance = balance - 100 WHERE accountId = 1;
UPDATE accounts SET balance = balance + 100 WHERE accountId = 2;

COMMIT;  -- or ROLLBACK;
```

---

## Stored Procedures

```sql
CREATE OR REPLACE PROCEDURE transfer_funds(
  p_from_account IN NUMBER,
  p_to_account IN NUMBER,
  p_amount IN NUMBER
)
IS
BEGIN
  UPDATE accounts SET balance = balance - p_amount 
  WHERE accountId = p_from_account;
  
  UPDATE accounts SET balance = balance + p_amount 
  WHERE accountId = p_to_account;
  
  COMMIT;
EXCEPTION
  WHEN OTHERS THEN
    ROLLBACK;
    RAISE;
END transfer_funds;
/

-- Call procedure
CALL transfer_funds(1, 2, 100);
```

---

## Views

```sql
CREATE VIEW active_employees AS
SELECT employeeId, firstName, lastName, salary
FROM employees
WHERE status = 'active' AND hireDate < SYSDATE - 365;

-- Query view (same as table)
SELECT * FROM active_employees WHERE salary > 75000;
```

---

## Advanced Security

### Column Encryption (Transparent)

```sql
-- Enable column encryption
ALTER TABLE users
ADD CONSTRAINT user_ssn_encrypt
  ENCRYPT (ssn) USING 'AES192' NO SALT;
```

### Row-Level Security

```sql
-- VPD (Virtual Private Database)
-- Users see only their own data
CREATE OR REPLACE FUNCTION get_user_filter
RETURN VARCHAR2 IS
BEGIN
  RETURN 'userId = USER_ID()';
END;
/
```

---

## Advanced Indexing

### Bitmap Index (Low Cardinality)

Best for columns with few distinct values.

```sql
-- Status: 'active', 'inactive', 'suspended' (3 values)
CREATE BITMAP INDEX idx_status ON users(status);

-- Query: Very fast for this index
SELECT COUNT(*) FROM users WHERE status = 'active';
```

### Partitioned Global Index

```sql
CREATE INDEX idx_global
  ON large_table(customer_id)
  GLOBAL
  PARTITION BY RANGE (customer_id) (
    PARTITION idx_part1 VALUES LESS THAN (1000000),
    PARTITION idx_part2 VALUES LESS THAN (2000000),
    PARTITION idx_part3 VALUES LESS THAN (MAXVALUE)
  );
```

---

## Oracle vs PostgreSQL vs MySQL

| Feature | Oracle | PostgreSQL | MySQL |
|---------|--------|-----------|-------|
| Cost | $$$ | Free | Free |
| Partitioning | Native | Manual | Limited |
| Compression | Native | Extensions | No |
| Row-Security | VPD | Policies | No |
| Parallel Query | Advanced | Available | Limited |
| Scalability | Extreme | Good | Good |
| Enterprise | Yes | Limited | Limited |

---

## Licensing Costs

**Per Socket Model:**
- Database (per 2 CPU cores): $47,500/year
- Plus Enterprise Edition: $11,500/year
- Plus option like Partitioning: $11,500/year

**Total Typical Setup:** $70,000+/year for basic 2-socket enterprise

---

## When to Choose Oracle

✓ If: Large enterprise, mission-critical, must scale to petabytes, regulatory needs
✗ If: Startup, cost-sensitive, simple app, small data

---

## Summary

- **Enterprise Grade**: Built for mission-critical systems
- **Extreme Performance**: Advanced optimization at huge scale
- **Security**: Row-level, encryption, auditing
- **Partitioning**: Native range, list, hash
- **Compression**: Transparent data/index compression
- **High Availability**: Data Guard, replication
- **Cost**: Expensive but justified for enterprise

Next: [[02-partitioning-optimization.md|Partitioning & Optimization]]

---

**See Also:**
- [[../../mysql/01-basics/01-overview.md|MySQL Overview]]
- [[../../postgres/01-basics/01-overview.md|PostgreSQL Overview]]
- [[../../mongodb/01-basics/01-overview.md|MongoDB Overview]]
