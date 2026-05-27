# 💰 Distributed Transactions — Complete Deep Dive

> **Scope**: Two-Phase Commit (2PC) protocol and failure modes, Three-Phase Commit (3PC) non-blocking properties, Saga patterns (choreography vs orchestration), XA specification and Java transactions (JTA, JDBC XADataSource), TCC (Try-Confirm-Cancel), Outbox pattern with CDC (Debezium, Kafka Connect), practical pattern selection guide.

## Table of Contents

1. Two-Phase Commit (2PC)
2. 2PC Failure Modes
3. Three-Phase Commit (3PC)
4. Saga: Choreography Pattern
5. Saga: Orchestration Pattern
6. XA Transactions & JTA
7. TCC: Try-Confirm-Cancel
8. Outbox Pattern & CDC
9. Distributed Transaction Pattern Guide

---

## 1. Two-Phase Commit (2PC)

```text
Phase 1: PREPARE                     Phase 2: COMMIT/ABORT

Coordinator         Participants     Coordinator         Participants
    |                    |               |                    |
    |-- prepare -------->|               |-- commit --------->|
    |<-- ready/abort ----|               |<-- ack ------------|
    |-- prepare -------->|               |-- commit --------->|
    |<-- ready/abort ----|               |<-- ack ------------|
    | commit point       |               |                    |
```

**Phase 1 — Prepare:** Coordinator sends `prepare`. Participants acquire locks, write prepare log, respond `ready` or `abort`.

**Phase 2 — Commit/Abort:** If all `ready`, coordinator logs commit, sends `commit`. If any `abort`, coordinator logs abort, sends `abort`.

**Commit Point:** The instant coordinator decides. After this, outcome is fixed.

**Doubt Period:** Phase between prepare and commit/abort. Participants hold locks, uncertain of outcome.

```sql
-- Participant prepare log
INSERT INTO tx_log (tx_id, state, data) VALUES ('txn-123', 'PREPARED', 'serialized_changes');
-- Coordinator decision log
INSERT INTO tx_log (tx_id, state) VALUES ('txn-123', 'COMMITTED');
```

---

## 2. 2PC Failure Modes

**Coordinator Crash in Phase 1:** Participants hold locks, blocked until coordinator recovers.

**Coordinator Crash After Decision:** Some participants committed, some missed decision. Recovery resolves on restart.

```text
In-Doubt Transaction:
  Participant A: PREPARED (locks held)
  Coordinator: CRASHED (decision unknown)
  
  Participants blocked indefinitely until coordinator recovers.
  
Heuristic Commit/Abort: unilateral decision by participant.
  DANGEROUS — can violate atomicity.
  Heuristic mix: some commit, some abort → data inconsistency.
```

2PC is **blocking**. Prepared participants wait indefinitely for coordinator recovery.

---

## 3. Three-Phase Commit (3PC)

3PC adds a timeout-based phase to avoid blocking.

```text
Phase 1: canCommit          Phase 2: preCommit        Phase 3: doCommit
Coordinator                 Coordinator               Coordinator
    |                           |                          |
    |-- canCommit ------------->|                          |
    |<-- yes -------------------|-- preCommit ------------>|-- doCommit --->
    |                           |<-- ack ------------------|<-- ack --------
    |-- canCommit ------------->|-- preCommit ------------>|-- doCommit --->
    |<-- yes -------------------|<-- ack ------------------|<-- ack --------
    | commit point              |                          |
```

**Differences from 2PC:**
1. **canCommit:** Probe without locks.
2. **preCommit:** Prepare and acknowledge. Commit point is after all preCommit acks.
3. **doCommit:** Actual commit. Participants commit on receipt, abort on timeout.

**Non-Blocking:** If coordinator fails during preCommit, participants time out and abort. If during doCommit, they time out and commit.

**Limitation:** Assumes eventual synchrony. True async networks can still violate atomicity.

---

## 4. Saga: Choreography Pattern

Saga: long-lived business transaction decomposed into local transactions with compensating actions.

```text
Step 1: Order Service → publishes "OrderCreated"
                ↓
Step 2: Payment Service → processes payment → publishes "PaymentProcessed"
                ↓
Step 3: Inventory → reserves → publishes "InventoryReserved"
                ↓
Step 4: Shipping → schedules → "ShipmentScheduled"

Compensation (on any failure):
  Step N fails → publish failure event
  Each prior step has a compensating handler
  e.g., PaymentFailed → RefundPayment, InventoryFailed → ReleaseReservation
```

```text
+-----------+    OrderCreated    +-----------+  PaymentProcessed  +-----------+
|   Order   | -----------------> |  Payment  | -----------------> | Inventory |
+-----------+ <----------------- +-----------+                   +-----------+
               OrderCancelled                    InventoryFailed
                        |                              |
                        v                              v
                  RefundPayment              ReleaseInventory
```

**Compensation:** Application-level rollback. Unlike 2PC, compensation is eventual and application-specific.

**Pros:** No coordinator, loose coupling. **Cons:** Hard to trace, cycles possible.

```java
// Choreography Saga — Event Handler
@Component
public class OrderSagaHandler {
    @EventListener
    public void onPaymentProcessed(PaymentProcessedEvent e) {
        reserveInventory(e.getOrderId());
    }
    @EventListener
    public void onPaymentFailed(PaymentFailedEvent e) {
        cancelOrder(e.getOrderId());
    }
    @EventListener
    public void onInventoryFailed(InventoryFailedEvent e) {
        publishRefund(e.getOrderId());  // compensation
    }
}
```

---

## 5. Saga: Orchestration Pattern

**Orchestrator (Saga Execution Coordinator):** Central state machine that tells each participant what to do.

```text
                    +-------------------+
                    |  Saga Orchestrator |
                    |  (state machine)  |
                    +--------+----------+
                           /|\
              doOrder() /  |  \ compensate()
                      v    |   v
               +-----------+ | +-----------+
               |  Order    | | |  Payment  |  (and so on for each step)
               +-----------+ | +-----------+
```

```python
class SagaOrchestrator:
    def execute_saga(self, saga_id, steps):
        self.log[saga_id] = {"step": 0, "state": "STARTED"}
        for i, step in enumerate(steps):
            try:
                step.execute()
                self.log[saga_id]["step"] = i
            except Exception:
                self._compensate(saga_id, steps[:i])
                return False
        self.log[saga_id]["state"] = "COMPLETED"
        return True

    def _compensate(self, saga_id, steps):
        for step in reversed(steps):
            step.compensate()  # reverse order
```

**Pros:** Centralized flow, easy to trace. **Cons:** Orchestrator single point of failure.

**Isolation Countermeasure:** Since saga lacks ACID isolation, steps might see intermediate states. Use semantic locks (reservation fields), reread before update, idempotent handlers.

---

## 6. XA Transactions & JTA

**X/Open XA Standard:** Distributed transaction coordination across multiple resource managers.

```text
+-------------------+          +-------------------+
| Transaction       |          | Resource Manager  |
| Manager (TM)      |<---XA--->| (RM) — DB, Queue  |
| - coordinates XA  |          | - manages resources|
+-------------------+          +-------------------+
```

**XA Interface:**

| Method | Description |
|--------|-------------|
| `xa_start` | Associate XID with current work |
| `xa_end` | Disassociate XID |
| `xa_prepare` | Phase 1 — prepare for commit |
| `xa_commit` | Phase 2 — commit prepared |
| `xa_rollback` | Abort prepared transaction |
| `xa_recover` | List prepared transactions |

```java
// XA via JDBC
XADataSource xaDS = new OracleXADataSource();
xaDS.setURL("jdbc:oracle:thin:@db-host:1521:ORCL");
XAConnection xaConn = xaDS.getXAConnection();
XAResource xaRes = xaConn.getXAResource();
Xid xid = new XidImpl(123, new byte[]{0x01}, new byte[]{0x01});

xaRes.start(xid, XAResource.TMNOFLAGS);
// ... SQL operations ...
xaRes.end(xid, XAResource.TMSUCCESS);
xaRes.prepare(xid);
xaRes.commit(xid, false);
```

**JTA (Java Transaction API):**
- `UserTransaction`: `begin()`, `commit()`, `rollback()` — simple application interface.
- `TransactionManager`: For application servers — `suspend()`, `resume()`, `setTransactionTimeout()`.

**Heuristics:** `XA_HEURCOM` (committed), `XA_HEURRB` (rolled back), `XA_HEURMIX` (mixed outcome).

---

## 7. TCC: Try-Confirm-Cancel

Three-phase protocol for resource reservation.

```text
PHASE 1: TRY (Reserve)
  Payment: Reserve $100 → "Reservation-123"
  Inventory: Reserve SKU-456 → "Hold-789"
  Shipping: Reserve slot → "Slot-ABC"

PHASE 2: CONFIRM or CANCEL
  All TRY succeed → confirm each (make permanent, idempotent)
  Any TRY fails → cancel each (release, idempotent)
```

```java
public interface PaymentTccService {
    String tryReserve(String accountId, double amount);
    boolean confirm(String reservationId);  // idempotent
    boolean cancel(String reservationId);   // idempotent
}
```

**TCC vs 2PC:**

| Aspect | TCC | 2PC |
|--------|-----|-----|
| Coordination | Application-level | Infrastructure (TM) |
| Lock Duration | Short (TRY reserves) | Long (full locks) |
| Blocking | Non-blocking | Blocking |
| Consistency | Eventual | Strong |
| Use Case | Long-lived business txns | Short ACID txns |

---

## 8. Outbox Pattern & CDC

Write domain event in the same DB transaction as the business change. Separate process publishes events reliably.

```sql
CREATE TABLE outbox (
    id              UUID PRIMARY KEY,
    aggregate_type  VARCHAR(100),
    event_type      VARCHAR(255),
    payload         JSONB,
    created_at      TIMESTAMP DEFAULT NOW(),
    published_at    TIMESTAMP
);
```

**Polling Publisher:**
```python
class OutboxPoller:
    def poll(self):
        records = self.db.fetch(
            "SELECT * FROM outbox WHERE published_at IS NULL "
            "ORDER BY created_at LIMIT 100 FOR UPDATE SKIP LOCKED")
        for record in records:
            self.broker.publish(record.event_type, record.payload)
            self.db.execute("UPDATE outbox SET published_at = NOW() WHERE id = %s", [record.id])
```

**CDC (Change Data Capture) with Debezium:**
```text
Application              PostgreSQL                      Kafka
    |                        |                             |
    |-- INSERT INTO outbox ->|                             |
    |                        |-- WAL write                 |
    |                        |  Debezium reads WAL         |
    |                        |------->Kafka Topic--------->|
    |                        |        "outbox.event"       |
```

Debezium reads PostgreSQL WAL, streams changes to Kafka via Kafka Connect. Avoids polling.

**Exactly-Once:** Consumer checks dedup table (`event_id` already processed?) before processing.

---

## 9. Distributed Transaction Pattern Guide

| Requirement | Best Pattern | Why |
|---|---|---|
| Strong ACID across DBs | 2PC | Synchronous, atomic |
| Non-blocking commit | 3PC | Timeout-based, no indefinite locks |
| Long-lived business flow | Saga | Compensation, eventual |
| Resource reservation | TCC | Short locks, reservation pattern |
| Reliable event publication | Outbox + CDC | Exactly-once delivery |

```text
Consistency Strength:
  STRONG <-------------------------------------------------> WEAK
  2PC ----- 3PC --------- TCC -------- Saga ------------- Choreography

Latency / Scalability:
  LOW (blocking) <----------------------------------------> HIGH (async)
  2PC ----- XA ------ TCC ------ Outbox/CDB ------ Saga (choreographed)
```

---

## Simplest Mental Model

**2PC is like asking everyone to promise before telling them to go — if anyone says no, nobody moves.** Everyone waits until they hear the final decision. **Saga is the opposite:** do each step, and if one fails, run cleanup for the ones that succeeded. **Outbox ensures events aren't lost** by writing them in the same DB transaction as the business change. Pick 2PC for strict atomicity; Saga for long-running flows where perfect consistency isn't required.
