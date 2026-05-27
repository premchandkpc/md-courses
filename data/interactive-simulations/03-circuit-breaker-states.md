# Circuit Breaker Pattern — Interactive State Machine

Step-by-step walkthrough of circuit breaker states, transitions, and failure recovery.

## The 3 States

```
┌─────────┐
│ CLOSED  │ ← Normal operation, calls go through
│ (allow) │
└────┬────┘
     │ failures exceed threshold
     │
     ▼
┌─────────┐
│ OPEN    │ ← Fail fast, reject calls
│ (block) │
└────┬────┘
     │ timeout expires
     │
     ▼
┌──────────┐
│ HALF_OPEN│ ← Test the dependency, allow 1 request
│(test)    │
└──┬──────┬┘
   │      │
   │      └─ failure ──→ OPEN (reset timer)
   │
   └─ success ──→ CLOSED (reset counters)
```

---

## Scenario 1: Normal Operation (CLOSED)

```
CLIENT                    CIRCUIT BREAKER               DOWNSTREAM
  │                             │                          │
  ├─ request ────────────────→  CLOSED (allow)             │
  │                             │                          │
  │                             ├─ forward ───────────────→ │
  │                             │                       SUCCESS
  │                             │ ←── response ──────────── │
  │ ←───── response ────────────┤                          │
  │                     (record success)                   │
  │                             │                          │

Counters:
  Failures: 0
  Successes: 100
  Failure rate: 0%
  State: CLOSED (allow all)
```

**Successful call flow:**
```
1. Increment success counter
2. Reset failure counter to 0
3. Return response to caller
4. Stay in CLOSED state

Thresholds (example):
  - Failure threshold: 5 consecutive or 50% in window
  - Min requests to evaluate: 10
```

---

## Scenario 2: Failures Accumulate (CLOSED → OPEN)

```
CLIENT                    CIRCUIT BREAKER               DOWNSTREAM
  │                             │                          │
  ├─ request ────────────────→  CLOSED                     │
  │                             │ ├─ forward ─────────────→ │
  │                             │ ←── timeout/error ──────┤ ✗
  │ ←─────── ERROR ────────────┤                          │
  │                     (record failure)                   │

Failure count: 1/5

Next requests... failures keep happening:

  ├─ request ────────────────→  CLOSED                     │
  │                             │ ├─ forward ─────────────→ │
  │                             │ ←── timeout/error ──────┤ ✗
  │ ←─────── ERROR ────────────┤                          │
  │                     (record failure)                   │

Failure count: 2/5

... more failures ...

Failure count: 5/5 (THRESHOLD HIT!)
↓ ↓ ↓

CLIENT                    CIRCUIT BREAKER               DOWNSTREAM
  │                             │                          │
  ├─ request ────────────────→  OPEN (block)              │
  │                             │                      (not called)
  │ ←─ ERROR (immediately) ────┤                          │
  │                      (no downstream call)              │
```

**Transition moment:**

```
Time: T=1000ms
Failure count reaches threshold (5 failures)
State transition: CLOSED → OPEN
Action: Stop sending requests to downstream
Effect: Fast error returns to clients (fail fast)

Reason: Protect downstream service from cascading requests
        when it's clearly struggling or down
```

**Failure tracking window:**

```
Time window: Last 10 seconds
Requests in window:
  T=0-1000ms:   5 failures
  T=1000-5000ms: (none, circuit open)
  
Failure rate calculation: 5/5 = 100% > 50% threshold
→ OPEN

If failures were just 50% rate:
  T=0-1000ms: 5 failures, 5 successes
  Rate: 5/10 = 50% = threshold hit
  → OPEN (threshold is inclusive ≥)
```

---

## Scenario 3: Open State (Fast Fail)

```
T=1000ms   Circuit opens (OPEN state)
           Downstream still DOWN
           
CLIENT                    CIRCUIT BREAKER
  │                             │
  ├─ request ────────────────→  OPEN (reject)
  │                             │
  │ ←─ CIRCUIT BREAKER EXCEPTION ────┤ (instant, no call)
  │

Repeat:
  ├─ request ────────────────→  OPEN
  │ ←─ CIRCUIT BREAKER EXCEPTION ────┤
  │
  ├─ request ────────────────→  OPEN
  │ ←─ CIRCUIT BREAKER EXCEPTION ────┤
  │

Metrics:
  Rejected requests: 100
  Avg latency: 1ms (fast-fail, no downstream call)
  Error rate: 100% (expected, circuit is open)

Benefit: Prevents:
  - Wasting resources on doomed requests
  - Downstream getting hammered while recovering
  - Client threads hanging waiting for timeout
```

**Open state duration:**

```
OPEN state timeout: 30 seconds (configurable)

T=1000ms:  Circuit opens
T=1030ms:  Timeout expires → transition to HALF_OPEN
           (after 30 seconds of rejection)
           
Reason: Give downstream time to recover
        Then test if it's healthy again
```

---

## Scenario 4: Half-Open State (Testing)

```
T=1030ms   Timeout expires: OPEN → HALF_OPEN
           First request allowed (test)

CLIENT                    CIRCUIT BREAKER               DOWNSTREAM
  │                             │                          │
  ├─ request ────────────────→  HALF_OPEN (test mode)     │
  │                             │ ├─ forward ────────────→ │
  │                             │ ←── response ──────────┤ SUCCESS!
  │ ←─────── response ─────────┤                          │
  │                     (downstream recovering!)           │

Case 1: Request succeeds
         Action: HALF_OPEN → CLOSED
         Reset: failure/success counters
         Effect: Resume normal operation
         
         Next request:
         ├─ request ────────────────→  CLOSED
         │                             │ ├─ forward ──────────→
         │ ← response (normal flow) ──┤

Case 2: Request fails
         ├─ request ────────────────→  HALF_OPEN
         │                             │ ├─ forward ────────→ FAIL ✗
         │ ←─ error ──────────────────┤
         │                      downstream still down
         
         Action: HALF_OPEN → OPEN (reopen)
         Reset: timeout timer
         Effect: Reject again, wait 30s, retry
         
         Next request:
         ├─ request ────────────────→  OPEN
         │ ←─ REJECTED ───────────────┤
```

**Half-Open behavior:**

```
State: HALF_OPEN
Purpose: Probe downstream health

Incoming requests:
  - Allow exactly 1 request through (test)
  - Subsequent requests: REJECT (circuit not fully closed)
  
Success → CLOSED
  - Resume normal flow
  - All requests go through
  
Failure → OPEN
  - Downstream still unhealthy
  - Go back to fast-fail mode
  - Wait another timeout period
```

---

## Scenario 5: Recovery & Cascading Back to Normal

```
T=0:       Service A calls Service B
           Service B becomes overloaded

T=5:       Service A's circuit opens (protect B)
           Reject requests, fail fast

T=10:      Service B recovers (load decreases)
           Downstream no longer timing out

T=35:      Service A's timeout expires
           Transition to HALF_OPEN

T=36:      Test request: succeeds
           Service A: HALF_OPEN → CLOSED

T=40:      Both services stable
           Normal request flow resumed
           
         ┌───────────────────────┐
         │  SERVICE B RECOVERS   │
         └────────┬──────────────┘
                  │
              ┌───▼────┐
              │ CLOSED │ ← Service A tests
              │(test)  │
              └───┬────┘
                  │
              ┌───▼─────┐
              │ CLOSED  │ ← Success, resume
              │(allow)  │
              └─────────┘
```

**Cascading recovery example:**

```
Dependency chain: API → Payment → Database

Database recovers first (circuit timeout)
    ↓
Payment tests Database (HALF_OPEN)
    ↓
Database responds: success
    ↓
Payment: HALF_OPEN → CLOSED (resumes normal flow)
    ↓
API receives Payment responses again
    ↓
API tests (HALF_OPEN)
    ↓
API: HALF_OPEN → CLOSED
    ↓
System fully recovered

Total time: 3 timeouts × 30s = ~90 seconds
Without circuit breaker: cascading failures, manual restart needed
```

---

## Scenario 6: Flaky Service (Oscillation)

**Problem**: Service is intermittently failing.

```
Healthy: 2 requests succeed
Unhealthy: 1 request fails
Pattern repeats...

Time: T=0-100ms
  CLOSED: 10 requests, 7 success, 3 fail
  Success rate: 70% < 80% threshold
  → OPEN

Time: T=100-130ms (OPEN state, reject all)
  Fast-fail: 50 requests rejected instantly

Time: T=130ms (timeout, enter HALF_OPEN)
  Test: succeeds
  → CLOSED (again)

Time: T=130-200ms
  CLOSED: 10 requests, 7 success, 3 fail
  Success rate: 70% < 80%
  → OPEN (again)

Oscillation cycle: ~130 seconds per round
```

**Solution: Increase test request count**

```
Traditional half-open: 1 test request

Improved half-open: Allow 5 test requests before deciding
  If ≥ 4 succeed: CLOSED
  If < 4 succeed: OPEN

This reduces false positives from transient failures
```

**Solution: Increase open timeout**

```
Open timeout: 60 seconds (instead of 30)
Gives flaky service more time to stabilize
Reduces oscillation frequency
```

---

## Common Patterns

### Pattern 1: Fallback Response

```python
try:
    response = circuit_breaker.call(get_user, user_id)
except CircuitBreakerOpen:
    response = cached_user or default_user

return response
```

When circuit open:
  - Return stale data (cache)
  - Return default/empty response
  - Degrade feature gracefully

### Pattern 2: Bulkhead Pattern

```
Circuit breaker per dependency:
  CB[Database] → separate from CB[Cache]
  CB[Auth] → separate from CB[Payment]
  
If Database fails:
  - Circuit B[Database] opens
  - Auth, Cache, Payment continue
  - System degrades partially instead of completely
```

### Pattern 3: Timeout + Circuit Breaker

```
Timeout: 5 seconds per request
Circuit breaker: 5 failures in 10 seconds

Interaction:
  Request 1: timeout (5s) → failure counter: 1
  Request 2: timeout (5s) → failure counter: 2
  Request 3: timeout (5s) → failure counter: 3
  Request 4: timeout (5s) → failure counter: 4
  Request 5: timeout (5s) → failure counter: 5 → OPEN
  
  From now: requests rejected instantly (1ms)
  Instead of: wasting 5 seconds each
```

---

## Interview Questions

### Q1: What's the purpose of the HALF_OPEN state?

**Answer**: To differentiate between "still broken" and "recovered".

Without HALF_OPEN:
```
CLOSED → request fails → immediately reopen for test
Problem: If test fails, you're still in the waiting period
         Multiple tests in rapid succession
         Wastes resources
```

With HALF_OPEN:
```
CLOSED → timeout expires → HALF_OPEN (wait for test result)
  Test succeeds → CLOSED (confidence: yes)
  Test fails → OPEN (confidence: no, wait longer)
This batches testing: max 1 test per timeout period
```

### Q2: Why reject requests in HALF_OPEN instead of queuing them?

**Answer**: Fail fast principle.

If downstream is still struggling:
  - Queueing adds latency to caller
  - Downstream gets more load (bad)
  - Better to fast-fail and let caller use fallback

Trade-off:
  - Allow all requests: risk overwhelming downstream
  - Reject in HALF_OPEN: fast feedback, protects downstream

### Q3: How does circuit breaker differ from retry?

**Answer**:

Retry: "Try again, maybe it's transient"
```
Request fails → retry immediately
Useful for: transient timeouts, temporary blips
Risk: if service is down, wastes time & resources
```

Circuit breaker: "Something is wrong, stop trying"
```
Requests fail → reject future requests
Useful for: cascading failures, overload protection
Reduces: wasted resources, load on broken service
```

Combined:
```
First request: try once, then circuit breaker takes over
Subsequent: fast-fail or test (HALF_OPEN)
Optimal: retry once, then circuit breaker
```

### Q4: Can a circuit breaker cause cascading failures?

**Answer**: No, it prevents them.

Scenario:
```
Service A → Service B (healthy) → Service C (down)

Without circuit breaker:
  Service B's circuit to C opens
  Service B degrades but stays up
  Service A calls B → B returns error
  If A doesn't handle the error → A fails too
  Cascading up the chain

With circuit breaker + fallback:
  Service B's circuit to C opens
  Service B returns cached data instead
  Service A gets response, no failure
  Cascading prevented
```

Key: Circuit breaker + proper fallback handling.

---

## Real-World Configuration

```python
from pybreaker import CircuitBreaker

cb = CircuitBreaker(
    fail_max=5,              # failures before opening
    reset_timeout=30,        # seconds before half-open test
    listeners=[...],         # monitor state changes
    listeners_cls=...,
    name='payment-service',
)

# Use it
try:
    result = cb.call(payment_api.charge, customer_id, amount)
except CircuitBreakerListener:
    result = return_cached_result()  # fallback
```

Common libraries:
  - Python: pybreaker, tenacity
  - Java: Resilience4j, Hystrix (legacy)
  - Go: grpc-health-probe, failpoint
  - .NET: Polly

---

## Key Takeaways

1. **CLOSED**: Normal operation, monitor failures
2. **OPEN**: Downstream broken, fail fast (save resources)
3. **HALF_OPEN**: Test if downstream recovered
4. **Protect downstream**: Circuit breaker prevents cascading overload
5. **Fail fast**: Return quickly so caller can use fallback

Real-world impact: Netflix estimates circuit breakers prevent ~30% of outages.
