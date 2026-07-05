# 08-Exponential-Backoff

Exponential backoff is a retry delay strategy where the wait time between attempts increases exponentially. When combined with jitter (randomization), it prevents the thundering herd problem — the synchronized retry storm that occurs when many clients retry simultaneously after an outage.

## Overview

The basic formula is `delay = base_delay × multiplier^attempt`, where `base_delay` is the initial wait (e.g. 100ms), `multiplier` is typically 2, and `attempt` starts at 0. After a 3rd attempt the delay would be 100 × 2³ = 800ms. Without jitter, exponential backoff still produces synchronized retries because all clients with the same base delay will retry at the same times.

## Key Characteristics

- **Multiplier**: Typically 2 (doubling), but can be adjusted. Conservative multipliers (1.5) are gentler on downstream services; aggressive multipliers (3) recover faster.
- **Base Delay**: The minimum delay before the first retry. Common values are 50–500ms depending on the operation's expected latency.
- **Maximum Cap**: A hard upper bound (e.g. 30 seconds) prevents delays from growing indefinitely.
- **Jitter**: Random variance applied to the delay. Full jitter (`random(0, current_delay)`) is recommended over equal jitter (`current_delay / 2 + random(0, current_delay / 2)`).
- **Formula Variations**: Full jitter: `sleep = random(0, min(cap, base × 2^attempt))`; this spreads retry times uniformly across the window.
- **Reset on Success**: Once a call succeeds, the backoff state resets so the next failure starts from the base delay.

## Why It Matters

When a downstream service fails, thousands of upstream clients may retry simultaneously once they detect recovery. Without jitter, their retries arrive in synchronized waves, overwhelming the recovering service and causing it to fail again (thundering herd). Exponential backoff with jitter spreads these retries across time, giving the service room to recover fully.

## Related Concepts

- [Retry](02-Retry.md) — Exponential backoff is the delay algorithm used between retry attempts; retry defines the attempt count and error conditions.
- [Circuit Breaker](01-Circuit-Breaker.md) — After the circuit breaker transitions to HALF-OPEN, exponential backoff is inappropriate; a single probe should be sent immediately.
- [Backpressure](07-Backpressure.md) — Backpressure and backoff are complementary: backpressure signals capacity, backoff paces retries.

---

## Mental Model

Exponential backoff is like trying to get through to a busy radio contest hotline. You call, get a busy signal, wait 30 seconds, and try again. Then wait a minute, then two minutes, then four. If you and everyone else all waited exactly 30 seconds, you'd all call at the same instant — total chaos. So you add randomness: wait 30–60 seconds, giving everyone a different window and keeping the phone lines clear enough for one lucky caller to get through.
