# System Design Foundations

Master the fundamental concepts that underpin ALL distributed systems.

## Topics

### 1. [Scalability](/15-system-design/00-foundations/01-scalability.md)
- Vertical scaling limits
- Horizontal scaling challenges
- Amdahl's law
- Little's law
- Universal Scalability Law

### 2. [Latency](/15-system-design/00-foundations/02-latency.md)
- Sources of latency
- Measurement & percentiles
- P99, P99.9, P999
- Latency budgets
- Latency vs throughput tradeoff

### 3. [Throughput](/15-system-design/00-foundations/03-throughput.md)
- QPS calculation
- Bandwidth
- Bottleneck identification
- Maximum sustainable throughput
- Throughput degradation

### 4. [Availability](/15-system-design/00-foundations/04-availability.md)
- Nines (99.9%, 99.99%)
- Downtime budgets
- SLI/SLO/SLA
- MTTR & MTTF
- Availability vs consistency

### 5. [Consistency Models](/15-system-design/00-foundations/05-consistency.md)
- Strong consistency
- Eventual consistency
- Causal consistency
- Read-after-write consistency
- Consistency implications

### 6. [Reliability & Durability](/15-system-design/00-foundations/06-reliability-durability.md)
- Mean time between failures
- Data durability guarantees
- Replication strategies
- Backup & recovery

### 7. [CAP Theorem](/15-system-design/00-foundations/07-cap-theorem.md)
- CAP theorem fundamentals
- Consistency vs availability
- Partition tolerance
- CP vs AP systems
- Implications

### 8. [PACELC Theorem](/15-system-design/00-foundations/08-pacelc-theorem.md)
- PACELC extends CAP
- Consistency vs latency
- Synchronous vs asynchronous replication
- Quorum-based approaches

### 9. [Idempotency](/15-system-design/00-foundations/09-idempotency.md)
- Why idempotency matters
- Implementation patterns
- Request deduplication
- Exactly-once semantics

### 10. [Backpressure](/15-system-design/00-foundations/10-backpressure.md)
- Flow control
- Queue management
- Cascading failures
- Rate limiting & rejection
- Backpressure propagation

---

Each topic includes:
- Problem explanation
- Real-world impact
- Measurement techniques
- Production patterns
- Failure scenarios
- Debugging approaches

**Read in order. Foundations required before advanced topics.**
