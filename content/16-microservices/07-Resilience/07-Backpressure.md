# 07-Backpressure

Backpressure is the mechanism by which a downstream consumer signals an upstream producer to slow down when it cannot keep up with the rate of incoming data. It prevents resource exhaustion by making the sender responsible for managing the flow, rather than overwhelming the receiver with unbounded queues.

## Overview

In distributed systems, producers often emit data faster than consumers can process it. Without backpressure, the consumer's buffers grow, memory pressure increases, garbage collection pauses lengthen, and eventually the consumer crashes or drops messages. Backpressure propagates the capacity signal upstream so the producer can adapt its emission rate, batch differently, or shed load at the source.

## Key Characteristics

- **Reactive Streams**: Standardized protocol (Reactive Streams / RSocket) where the consumer tells the producer exactly how many items it can accept via a `request(n)` signal.
- **Bounded Queues**: Internal queues have a fixed maximum size; once full, the consumer rejects new items or applies a rejection strategy.
- **Rejection Strategies**: Block (caller waits), drop (throw away the new item), discard-oldest (replace the oldest buffered item), or propagate error.
- **Upstream Propagation**: When Service B signals backpressure to Service A, A may in turn slow down its upstream, creating a chain of backpressure to the origin.
- **Discriminating Pressure**: Not all work is equal — critical requests may bypass backpressure bounds via priority queuing.
- **Monitoring**: Queue depth, reject rate, and processing latency per stage reveal where the bottleneck lies.

## Why It Matters

Unbounded queues hide problems until they cause an OOM crash. Backpressure makes capacity limits explicit and pushes the slowdown decision to the entity best positioned to make it — the producer, which can prioritize, sample, or drop less important work before the consumer is overwhelmed.

## Related Concepts

- [Bulkhead](04-Bulkhead.md) — Bulkheads isolate resources; backpressure prevents those resources from being overrun.
- [Circuit Breaker](01-Circuit-Breaker.md) — Backpressure is a continuous signal (slow down), while circuit breakers are a binary signal (stop all requests).
- [Exponential Backoff](08-Exponential-Backoff.md) — Producers receiving backpressure may use exponential backoff before retrying rejected messages.

---

## Mental Model

Backpressure is like a busy waiter telling the kitchen to slow down. When the dining room is full, the waiter signals "stop sending plates — I can't serve them faster than the customers can eat." The kitchen doesn't keep piling plates on the counter (unbounded queue). Instead, the chef slows cooking until the waiter signals "ready for more."
