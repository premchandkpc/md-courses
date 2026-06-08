---
title: MySQL Transactions, ACID Properties & Isolation Levels Deep Dive
topic: 08-databases
difficulty: intermediate
time: 30m
paths:
  - backend-junior
  - data
  - backend-senior
---

# MySQL Transactions, ACID Properties & Isolation Levels Deep Dive

## ACID Properties Explained

### Atomicity (All or Nothing)

```sql
-- Transfer money: A → B
START TRANSACTION;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;

-- Either BOTH updates happen, or NEITHER happen
-- No partial transfers (A debited but B not credited)

-- Example of failure:
-- Update 1: Debit A (-$100) ✓
-- [Server crash here]
-- Update 2: Credit B (+$100) ✗ (never executed)
-- Result: Transaction rolled back, A and B unchanged

-- Mechanism: Redo log
-- Before commit: writes to redo log
-- Crash: recovery replays redo log (all-or-nothing)
```

### Consistency (Valid State to Valid State)

```sql
-- Constraint: account balance >= 0
CREATE TABLE accounts (
    id INT PRIMARY KEY,
    balance DECIMAL(10,2) NOT NULL CHECK (balance >= 0)
);

-- Attempt: violate constraint
START TRANSACTION;
UPDATE accounts SET balance = -50 WHERE id = 1;  -- Violates check
COMMIT;  -- FAILS! Transaction rolled back, balance unchanged

-- Mechanism: Constraint enforcement
-- Before commit: checks all constraints
-- If any violated: entire transaction rolled back
```

### Isolation (Transactions Independent)

```sql
-- Transaction A:
START TRANSACTION;
SELECT balance FROM accounts WHERE id = 1;  -- Sees $100 (consistent view)
-- ... some processing ...
SELECT balance FROM accounts WHERE id = 1;  -- Still sees $100 (isolated from T2)
COMMIT;

-- Transaction B (running simultaneously):
UPDATE accounts SET balance = balance + 50 WHERE id = 1;  -- Changes balance to $150
COMMIT;

-- Isolation level determines whether T1 sees T2's changes
-- READ UNCOMMITTED: T1 might see $150 (dirty read)
-- REPEATABLE READ: T1 sees $100 both times (isolated)
-- See "Isolation Levels" section below
```

### Durability (Persisted After Commit)

```sql
-- Write is durable after COMMIT returns
START TRANSACTION;
UPDATE accounts SET balance = balance + 100 WHERE id = 1;
COMMIT;  -- Returns to client

-- At this point: data persisted to disk (if innodb_flush_log_at_trx_commit = 1)
-- Even if server crashes 1 second later: data still there
-- Recovery process: replays redo log

-- Mechanism: Redo log flushed to disk
-- Before COMMIT returns: redo log written to disk
-- Crash: recovery reads redo log, re-applies transaction
```

---

## Isolation Levels: Complete Guide

### READ UNCOMMITTED (Level 0)

```sql
SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

-- Connection 1 (Transaction A):
START TRANSACTION;
SELECT balance FROM accounts WHERE id = 1;  -- Sees 100

-- Connection 2 (Transaction B):
UPDATE accounts SET balance = 200 WHERE id = 1;
-- NOT COMMITTED YET (but A can see it!)

-- Connection 1:
SELECT balance FROM accounts WHERE id = 1;  -- Sees 200 (DIRTY READ!)

-- Connection 2:
ROLLBACK;  -- Transaction rolled back, balance back to 100

-- Connection 1:
SELECT balance FROM accounts WHERE id = 1;  -- Sees 100 (inconsistent with earlier read!)

-- Anomalies allowed: dirty reads, non-repeatable reads, phantoms
-- Use case: Never (correctness issues)
-- Performance: Fastest (10-50K txn/sec)
```

### READ COMMITTED (Level 1)

```sql
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- Connection 1:
START TRANSACTION;
SELECT balance FROM accounts WHERE id = 1;  -- Sees 100 (locked for read)

-- Connection 2:
UPDATE accounts SET balance = 200 WHERE id = 1;  -- Blocked (can't update while read locked)
COMMIT;

-- Connection 1:
SELECT balance FROM accounts WHERE id = 1;  -- Now sees 200 (NON-REPEATABLE READ)
-- Prevented dirty read (A waited for T2 to commit)
-- But second read sees different value

-- Anomalies allowed: non-repeatable reads, phantoms (but NOT dirty reads)
-- Use case: Web applications (eventual consistency ok)
-- Performance: Good (5-20K txn/sec)
```

### REPEATABLE READ (MySQL Default, Level 2)

```sql
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- Connection 1:
START TRANSACTION;
SELECT balance FROM accounts WHERE id = 1;  -- Sees 100 (snapshot at T1 start)

-- Connection 2:
UPDATE accounts SET balance = 200 WHERE id = 1;
COMMIT;

-- Connection 1:
SELECT balance FROM accounts WHERE id = 1;  -- Still sees 100 (REPEATABLE!)
-- MVCC: reads version from snapshot taken at transaction start

-- Anomalies allowed: phantoms (with gap locks prevent some)
-- Gap lock: prevents INSERT in range that was read
-- Use case: Financial systems, inventory
-- Performance: Medium (2-10K txn/sec)
-- Storage: +25-50% for version history (MVCC)
```

### SERIALIZABLE (Level 3)

```sql
SET SESSION TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- Connection 1:
START TRANSACTION;
SELECT * FROM accounts WHERE id BETWEEN 1 AND 10;  -- Locks range [1,10]

-- Connection 2:
INSERT INTO accounts (id, balance) VALUES (5, 100);  -- Blocked by gap lock!
-- Gap lock prevents phantom (new row in range)

UPDATE accounts SET balance = 200 WHERE id = 2;  -- Also blocked by gap lock
-- Range lock prevents modifications in [1,10]

-- Both operations wait until T1 commits

-- Anomalies prevented: ALL (dirty, non-repeatable, phantom)
-- Use case: Compliance, critical financial systems
-- Performance: Slowest (2-5K txn/sec, 10-100x slower)
```

---

## Lock Types & Mechanics

### Shared Lock (Read Lock)

```sql
-- Multiple transactions can hold shared lock
SELECT * FROM accounts WHERE id = 1 FOR SHARE;  -- Acquire shared lock

-- Connection 1 & 2 both:
SELECT * FROM accounts WHERE id = 1 FOR SHARE;  -- Both get lock, both read

-- Connection 3 (writer):
UPDATE accounts SET balance = 100 WHERE id = 1;  -- BLOCKS (shared lock blocks writes)

-- When both readers release locks: writer can proceed
```

### Exclusive Lock (Write Lock)

```sql
-- Only ONE transaction can hold exclusive lock
UPDATE accounts SET balance = 100 WHERE id = 1;  -- Acquires exclusive lock

-- Any other transaction:
SELECT * FROM accounts WHERE id = 1;  -- BLOCKS (exclusive lock blocks reads)
UPDATE accounts SET balance = 200 WHERE id = 1;  -- Also BLOCKS

-- When updater commits: other transactions proceed
```

### Gap Lock (Range Lock)

```sql
-- REPEATABLE READ or SERIALIZABLE:
SELECT * FROM accounts WHERE id BETWEEN 100 AND 200;
-- Acquires gap lock [100, 200)

-- Another transaction:
INSERT INTO accounts (id, balance) VALUES (150, 100);  -- BLOCKED by gap lock
-- Phantom prevention: can't insert new row in locked range

-- Trade-off: 5-10% latency overhead, but prevents phantoms
```

---

## Deadlock Handling

### Classic Deadlock Scenario

```sql
-- Connection 1:
START TRANSACTION;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;  -- Lock row 1
SLEEP(5);  -- Simulate processing
UPDATE accounts SET balance = balance + 100 WHERE id = 2;  -- Wait for row 2 (LOCK!)

-- Connection 2:
UPDATE accounts SET balance = balance - 100 WHERE id = 2;  -- Lock row 2
UPDATE accounts SET balance = balance + 100 WHERE id = 1;  -- Wait for row 1 (LOCK!)

-- Result: Both waiting for each other
-- MySQL detects within 50-100ms: DEADLOCK ERROR

-- Error: "Deadlock found when trying to get lock; try restarting transaction"

-- Application retry logic:
def transfer_with_retry(from_id, to_id, amount):
    for attempt in range(5):
        try:
            db.execute(f"""
                UPDATE accounts SET balance = balance - {amount} WHERE id = {from_id};
                UPDATE accounts SET balance = balance + {amount} WHERE id = {to_id};
            """)
            return True
        except DeadlockError:
            wait_time = (2 ** attempt) * 10  # Exponential backoff
            time.sleep(wait_time / 1000)  # 10ms, 20ms, 40ms, ...
    return False
```

### Prevention: Lock Ordering

```sql
-- Instead of: random order
UPDATE accounts SET balance = ... WHERE id = 2;
UPDATE accounts SET balance = ... WHERE id = 1;

-- Always lock in same order:
UPDATE accounts SET balance = balance - 100 WHERE id IN (1, 2) ORDER BY id;
UPDATE accounts SET balance = balance + 100 WHERE id IN (2, 1) ORDER BY id;

-- Both transactions lock in order: 1 first, then 2
-- No circular wait = no deadlock

-- SQL pattern (atomic, no deadlock):
START TRANSACTION;
SELECT * FROM accounts WHERE id IN (1, 2) FOR UPDATE ORDER BY id;
-- Locks both rows in order
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
```

---

## Real-World Scenarios

### Scenario 1: E-Commerce Order Placement (High Traffic)

```sql
-- Requirements:
-- - 1000 order placements per second
-- - Need inventory deduction + order creation
-- - Speed critical (user waiting for confirmation)

-- Configuration:
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
SET SESSION innodb_lock_wait_timeout = 5;  -- 5 second timeout (fast failure)

-- Code:
def place_order(customer_id, items):
    try:
        db.start_transaction()
        
        # 1. Deduct inventory
        for item in items:
            db.update(f"""
                UPDATE inventory 
                SET quantity = quantity - {item['qty']} 
                WHERE product_id = {item['id']}
                AND quantity >= {item['qty']}  -- Prevent oversell
            """)
        
        # 2. Create order
        order_id = db.insert('orders', {
            'customer_id': customer_id,
            'items': json.dumps(items),
            'status': 'confirmed'
        })
        
        db.commit()
        return order_id
    
    except IntegrityError:  # Inventory constraint violated
        db.rollback()
        return None  # Out of stock
    except DeadlockError:
        time.sleep(0.01)
        return place_order(customer_id, items)  # Retry

# Performance:
# Latency: 10-50ms per order
# Throughput: 1000 orders/sec × 8 cores = 8000 orders/sec ✓
# Isolation: READ COMMITTED (eventual consistency ok for ecommerce)
```

### Scenario 2: Banking Transfers (Compliance Critical)

```sql
-- Requirements:
-- - Every transfer must be atomic + isolated
-- - Cannot lose money in transit
-- - Audit trail required
-- - Slower, but guaranteed correct

-- Configuration:
SET SESSION TRANSACTION ISOLATION LEVEL SERIALIZABLE;
SET SESSION innodb_lock_wait_timeout = 10;

-- Code:
def transfer_money(from_id, to_id, amount):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            db.start_transaction()
            
            # 1. Verify balance
            from_acct = db.query(f"""
                SELECT balance FROM accounts 
                WHERE id = {from_id} 
                FOR UPDATE
            """)
            
            if from_acct['balance'] < amount:
                db.rollback()
                raise InsufficientFunds()
            
            # 2. Debit + Credit (must be atomic)
            db.update(f"UPDATE accounts SET balance = balance - {amount} WHERE id = {from_id}")
            db.update(f"UPDATE accounts SET balance = balance + {amount} WHERE id = {to_id}")
            
            # 3. Log transaction
            db.insert('transfer_log', {
                'from_id': from_id,
                'to_id': to_id,
                'amount': amount,
                'timestamp': now(),
                'status': 'completed'
            })
            
            db.commit()
            return True
        
        except DeadlockError:
            wait_time = (2 ** attempt) * 100
            time.sleep(wait_time / 1000)
        except Exception as e:
            db.rollback()
            raise
    
    raise MaxRetriesExceeded()

# Performance:
# Latency: 100-500ms per transfer (slow but guaranteed)
# Throughput: 100-200 transfers/sec (serializable overhead)
# Isolation: SERIALIZABLE (all anomalies prevented)
# Auditability: 100% (every transfer logged)
```

### Scenario 3: Inventory System (Prevent Oversell)

```sql
-- Requirements:
-- - Cannot oversell (inventory < 0)
-- - High concurrency (flash sales)
-- - Need balance between speed and correctness

-- Configuration:
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SET SESSION innodb_lock_wait_timeout = 3;

-- Code:
def reserve_inventory(product_id, qty):
    try:
        db.start_transaction()
        
        # 1. Check availability (gap lock prevents phantom stock)
        stock = db.query(f"""
            SELECT quantity FROM inventory 
            WHERE product_id = {product_id}
            FOR UPDATE
        """)
        
        if stock['quantity'] < qty:
            db.rollback()
            raise OutOfStock()
        
        # 2. Reserve
        db.update(f"""
            UPDATE inventory 
            SET quantity = quantity - {qty}, reserved = reserved + {qty}
            WHERE product_id = {product_id}
        """)
        
        db.commit()
        return True
    
    except DeadlockError:
        time.sleep(0.001)  # 1ms backoff, retry
        return reserve_inventory(product_id, qty)

# Performance:
# Latency: 50-200ms per reservation
# Throughput: 500-1000 reservations/sec
# Correctness: Prevents oversell (gap locks)
# Balance: REPEATABLE READ (good isolation, reasonable speed)
```

---

## Monitoring & Troubleshooting

### Check Lock Status

```sql
-- View current locks
SHOW PROCESSLIST;  -- Shows all transactions
SHOW OPEN TABLES WHERE In_use > 0;  -- Tables with locks

-- View waits
SELECT * FROM INFORMATION_SCHEMA.INNODB_TRX;  -- Active transactions
SELECT * FROM INFORMATION_SCHEMA.INNODB_LOCKS;  -- Lock info
SELECT * FROM INFORMATION_SCHEMA.INNODB_LOCK_WAITS;  -- Who waiting for what

-- Example output:
-- trx_id | trx_state | trx_started | trx_wait_started
-- 7812   | RUNNING   | 2025-05-29  | NULL (no wait)
-- 7813   | LOCK WAIT | 2025-05-29  | 2025-05-29 14:30:05 (waiting for row)
```

### Monitor Deadlocks

```sql
-- Check deadlock stats
SHOW ENGINE INNODB STATUS;

-- Look for section:
-- LATEST DETECTED DEADLOCK
-- *** (1) TRANSACTION:
-- ...
-- HOLDS THE LOCK(S):
-- RECORD LOCKS space id 0 page no 3 n bits 80 index GEN_CLUST_INDEX
-- ...

-- If many deadlocks:
-- - Check for lock ordering issues
-- - Consider reducing isolation level
-- - Add retry logic to application
```

---

## Best Practices Checklist

- ✓ Use READ COMMITTED for web apps (speed > strict isolation)
- ✓ Use REPEATABLE READ (MySQL default) for financial data (gap locks prevent phantoms)
- ✓ Use SERIALIZABLE only if compliance requires (significant performance hit)
- ✓ Lock ordering to prevent deadlocks (always lock in same order)
- ✓ Keep transactions SHORT (<100ms, <1000 rows modified)
- ✓ Avoid long-running transactions (block others, grow undo log)
- ✓ Set innodb_lock_wait_timeout to 5-10 sec (fail fast)
- ✓ Deadlock retry with exponential backoff (1ms, 2ms, 4ms, ...)
- ✓ Monitor deadlock rate (alert if > 1/sec, code issue)
- ✓ Monitor lock wait time (alert if > 10% query time)
- ✓ Test concurrent access patterns before deploy
- ✓ Log all transactions (audit trail)

---

**Summary:**
- **ACID**: Atomicity (all-or-nothing), Consistency (constraints), Isolation (independent), Durability (persisted)
- **READ COMMITTED**: Fast (5-20K txn/sec), eventual consistency, web apps
- **REPEATABLE READ**: Medium (2-10K txn/sec), isolated reads, MySQL default
- **SERIALIZABLE**: Slow (2-5K txn/sec), prevents all anomalies, compliance
- **Deadlocks**: Lock ordering prevents most, retry + exponential backoff handles rest
- **Performance**: Keep short, avoid long-running, index well for lock efficiency
