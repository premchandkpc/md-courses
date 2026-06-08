---
title: MySQL Transactions & Locking
topic: 08-databases
difficulty: intermediate
time: 30m
paths:
  - backend-junior
  - data
  - backend-senior
---

# MySQL Transactions & Locking

## ACID Transactions

Ensure data consistency across multiple operations.

### Atomicity (All or Nothing)

```sql
-- Money transfer: Both succeed or both fail
START TRANSACTION;

UPDATE accounts SET balance = balance - 100 WHERE accountId = 1;
UPDATE accounts SET balance = balance + 100 WHERE accountId = 2;

COMMIT;  -- Both updates persist

-- OR if error:
ROLLBACK;  -- Both updates undone
```

### Consistency (Valid State)

```sql
-- Constraints enforced before and after
ALTER TABLE accounts ADD CONSTRAINT check_balance CHECK (balance >= 0);

START TRANSACTION;
UPDATE accounts SET balance = balance - 1000 WHERE accountId = 1;
-- If balance goes negative, transaction fails
COMMIT;
```

### Isolation (Concurrent Independence)

```sql
-- Transaction 1 (Session A)
START TRANSACTION;
SELECT balance FROM accounts WHERE accountId = 1;  -- Sees $1000
-- ... other operations ...

-- Transaction 2 (Session B)
START TRANSACTION;
UPDATE accounts SET balance = 500 WHERE accountId = 1;
COMMIT;

-- Transaction 1 still sees $1000 (isolated)
-- After T1 commits, will see new value
COMMIT;
```

### Durability (Survives Failures)

```sql
-- After COMMIT, data survives:
-- - Application crash
-- - Database restart
-- - Power failure
-- (persisted to disk + redo log)
```

---

## Isolation Levels

Control how concurrent transactions interact.

### READ UNCOMMITTED (Lowest)

```sql
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

-- Reads uncommitted (dirty) data from other transactions
-- Dirty read possible
-- Fastest but dangerous for consistency
```

**Problems:**
- Dirty reads (read data that might rollback)
- Non-repeatable reads
- Phantom reads

**Use:** Not recommended for production

### READ COMMITTED (Default InnoDB)

```sql
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- Only reads committed data
-- Solves dirty reads
```

**Example:**
```sql
-- Transaction 1
START TRANSACTION;
SELECT balance FROM accounts WHERE accountId = 1;  -- Sees $1000 (committed)

-- Transaction 2 (other session)
UPDATE accounts SET balance = 500 WHERE accountId = 1;
COMMIT;

-- Transaction 1 reads again
SELECT balance FROM accounts WHERE accountId = 1;  -- Now sees $500!
-- Non-repeatable read!
```

### REPEATABLE READ (InnoDB Default)

```sql
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- Same data within transaction
-- Solves dirty reads + non-repeatable reads
```

**Example:**
```sql
-- Transaction 1
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
SELECT balance FROM accounts WHERE accountId = 1;  -- Sees $1000

-- Transaction 2 updates
UPDATE accounts SET balance = 500 WHERE accountId = 1;
COMMIT;

-- Transaction 1 reads again (same transaction)
SELECT balance FROM accounts WHERE accountId = 1;  -- Still sees $1000!
COMMIT;  -- Now will see $500
```

**Phantom Read Issue:**
```sql
-- Transaction 1
START TRANSACTION;
SELECT COUNT(*) FROM users WHERE age > 30;  -- Sees 100 rows

-- Transaction 2 inserts new user age 35
INSERT INTO users (age) VALUES (35);
COMMIT;

-- Transaction 1 counts again
SELECT COUNT(*) FROM users WHERE age > 30;  -- Sees 101 rows!
-- Phantom read: new row appeared
```

### SERIALIZABLE (Highest)

```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- Transactions run as if sequential
-- Slowest but safest
-- Phantom reads prevented
```

---

## Comparison

| Level | Dirty Read | Non-Repeatable | Phantom | Performance |
|-------|-----------|----------------|---------|-------------|
| READ UNCOMMITTED | Yes | Yes | Yes | Fastest |
| READ COMMITTED | No | Yes | Yes | Good |
| REPEATABLE READ | No | No | Yes | Good |
| SERIALIZABLE | No | No | No | Slowest |

---

## Locking

Coordinate concurrent access.

### Shared Lock (Read Lock)

```sql
-- Multiple transactions can read same data
SELECT * FROM accounts WHERE accountId = 1 LOCK IN SHARE MODE;

-- Other transactions can also read:
SELECT * FROM accounts WHERE accountId = 1 LOCK IN SHARE MODE;  -- Allowed

-- But cannot write:
UPDATE accounts SET balance = 500 WHERE accountId = 1;  -- BLOCKED until locks released
```

### Exclusive Lock (Write Lock)

```sql
-- Only one transaction can access
SELECT * FROM accounts WHERE accountId = 1 FOR UPDATE;

-- Other transactions blocked on read or write:
SELECT * FROM accounts WHERE accountId = 1;  -- BLOCKED
SELECT * FROM accounts WHERE accountId = 1 FOR UPDATE;  -- BLOCKED
UPDATE accounts SET balance = 500 WHERE accountId = 1;  -- BLOCKED
```

### Implicit Locking

```sql
-- UPDATE automatically locks rows
UPDATE accounts SET balance = balance - 100 WHERE accountId = 1;
-- Other transactions blocked until COMMIT/ROLLBACK

-- DELETE also locks
DELETE FROM accounts WHERE accountId = 1;
```

---

## Deadlocks

When transactions wait for each other.

```sql
-- Deadlock scenario:

-- Transaction 1                    -- Transaction 2
START TRANSACTION;                 START TRANSACTION;
SELECT * FROM A FOR UPDATE;        SELECT * FROM B FOR UPDATE;
-- ... wait ...                    -- ... wait ...
SELECT * FROM B FOR UPDATE;        SELECT * FROM A FOR UPDATE;
-- DEADLOCK! T1 waits for B,       -- DEADLOCK! T2 waits for A,
-- T2 waits for A                  -- T1 waits for B

-- Result:
-- ERROR 1213 (40001): Deadlock found when trying to get lock
```

### Prevention

**1. Lock order consistency**
```sql
-- Both transactions: Always lock A before B
START TRANSACTION;
SELECT * FROM A FOR UPDATE;  -- First
SELECT * FROM B FOR UPDATE;  -- Second
-- No deadlock possible
```

**2. Minimize lock duration**
```sql
-- ❌ Long transaction
START TRANSACTION;
SELECT * FROM orders FOR UPDATE;
-- ... 10 seconds of processing ...
COMMIT;

-- ✓ Short lock
START TRANSACTION;
SELECT * FROM orders FOR UPDATE;
COMMIT;  -- Release quickly
-- Process result after
```

**3. Use timeouts**
```sql
-- Set deadlock timeout (seconds)
SET innodb_lock_wait_timeout = 2;

-- Or handle in application:
try {
    db.transaction(() => {
        // operations
    });
} catch (DeadlockError) {
    // Retry
}
```

---

## Optimistic Locking (Application-Level)

Detect conflicts using version numbers.

```sql
-- Add version column
ALTER TABLE accounts ADD version INT DEFAULT 0;

-- Read with version
SELECT accountId, balance, version FROM accounts WHERE accountId = 1;
-- Returns: id=1, balance=1000, version=5

-- Update only if version unchanged
UPDATE accounts 
SET balance = 900, version = version + 1
WHERE accountId = 1 AND version = 5;

-- If another transaction updated it:
-- WHERE clause fails (version no longer 5)
-- Zero rows updated (detect conflict)
```

---

## Pessimistic Locking (Application-Level)

Claim exclusive access.

```sql
-- Lock row for update
START TRANSACTION;
SELECT * FROM accounts WHERE accountId = 1 FOR UPDATE;
-- Other transactions blocked

-- Do work
UPDATE accounts SET balance = 900 WHERE accountId = 1;

COMMIT;  -- Release lock
```

---

## Real-World Scenarios

### Bank Transfer (Safe)

```sql
DELIMITER //
CREATE PROCEDURE transfer_funds(
    IN p_from INT,
    IN p_to INT,
    IN p_amount DECIMAL(10,2)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Lock both accounts (consistent order: smaller ID first)
    SELECT * FROM accounts WHERE accountId = LEAST(p_from, p_to) FOR UPDATE;
    SELECT * FROM accounts WHERE accountId = GREATEST(p_from, p_to) FOR UPDATE;
    
    -- Verify sufficient funds
    UPDATE accounts 
    SET balance = balance - p_amount 
    WHERE accountId = p_from AND balance >= p_amount;
    
    IF ROW_COUNT() = 0 THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient funds';
    END IF;
    
    -- Credit destination
    UPDATE accounts 
    SET balance = balance + p_amount 
    WHERE accountId = p_to;
    
    COMMIT;
END //
DELIMITER ;

-- Usage
CALL transfer_funds(1, 2, 100);
```

### Inventory Decrement (Race Condition)

```sql
-- ❌ Wrong: Race condition
SELECT stock FROM products WHERE productId = 5;  -- Returns 10
if (stock > 0) {
    // Other transaction decrements here!
    UPDATE products SET stock = stock - 1 WHERE productId = 5;
}

-- ✓ Correct: Atomic operation
UPDATE products 
SET stock = stock - 1 
WHERE productId = 5 AND stock > 0;

-- Verify success
if (mysqli_affected_rows() > 0) {
    // Stock decremented
} else {
    // Out of stock
}
```

### E-commerce Checkout

```sql
START TRANSACTION;

-- 1. Lock inventory
SELECT quantity FROM cart_items WHERE cartId = 999 FOR UPDATE;

-- 2. Verify stock
UPDATE products 
SET stock = stock - ? 
WHERE productId IN (SELECT productId FROM cart_items WHERE cartId = 999)
AND stock >= ?;

-- 3. Create order
INSERT INTO orders (customerId, totalAmount) VALUES (?, ?);

-- 4. Record items
INSERT INTO orderItems (orderId, productId, quantity) 
SELECT LAST_INSERT_ID(), productId, quantity FROM cart_items WHERE cartId = 999;

-- 5. Clear cart
DELETE FROM cart_items WHERE cartId = 999;

COMMIT;
```

---

## Performance vs Consistency Tradeoff

| Need | Isolation Level | Locking | Cost |
|------|-----------------|---------|------|
| High consistency | SERIALIZABLE | Exclusive | Slow |
| Financial | REPEATABLE READ | WHERE needed | Medium |
| Most apps | READ COMMITTED | Minimal | Fast |
| Analytics | READ UNCOMMITTED | None | Fastest |

---

## Summary

- **ACID**: Atomicity, Consistency, Isolation, Durability
- **Isolation Levels**: READ UNCOMMITTED → SERIALIZABLE
- **Shared Locks**: Multiple readers
- **Exclusive Locks**: Single writer
- **Deadlocks**: Prevent with lock order, timeouts
- **Optimistic**: Version numbers, detect conflicts
- **Pessimistic**: FOR UPDATE, prevent conflicts
- **Real-world**: Balance consistency vs performance

Next: [[02-replication-ha.md|Replication & High Availability]]

---

**See Also:**
- [[../01-basics/03-queries-optimization.md|Query Optimization]]
- [[../../postgres/01-basics/01-overview.md#acid--transactions|PostgreSQL Transactions]]
- [[../../dynamodb/04-concurrency/01-concurrency-control.md|DynamoDB Concurrency]]
