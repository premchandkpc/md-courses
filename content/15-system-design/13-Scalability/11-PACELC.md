# 11-PACELC

An extension of the CAP theorem that addresses CAP's limitation: CAP only describes behavior during a network partition but says nothing about tradeoffs when the system is operating normally. PACELC stands for: If there's a Partition (P), trade off Availability vs Consistency (A vs C); Else (E), trade off Latency vs Consistency (L vs C).

## Overview
Proposed by Daniel J. Abadi in 2010, PACELC acknowledges that even when the network is healthy, databases face a fundamental choice between low latency and strong consistency. Strong consistency requires coordination (synchronous replication, distributed consensus), which adds latency. Relaxed consistency allows faster responses because nodes don't wait for each other. PACELC forces designers to consider both regimes: partitioned behavior (the CAP scenario) and normal behavior (the latency tradeoff). DynamoDB, for example, picks AP during partitions and prefers low latency over strong consistency during normal operation (PA/EL). A traditional RDBMS with synchronous replication picks CP during partitions and prefers consistency over latency during normal operation (PC/EC).

## Key Characteristics
- **Two separate tradeoffs**: During partition (P): choose C or A. Else/normal (E): choose L (latency) or C (consistency).
- **PA/EL (DynamoDB, Cassandra)**: Prefer availability during partitions and low latency during normal operation. Eventual consistency is the default.
- **PC/EC (Spanner, MySQL with sync repl)**: Prefer consistency during partitions and consistency even at the cost of latency during normal operation. Strong consistency is the default.
- **PC/EL (MongoDB, some NoSQL)**: Prefer consistency during partitions but accept higher latency to prioritize consistency during normal operation. Less common.
- **PA/EC (rare)**: Prefer availability during partitions but consistency during normal operation. Hard to achieve because the normal-mode consistency mechanism (sync replication) conflicts with partition availability goals.
- **Real-world nuance**: Many systems let you configure the tradeoff per operation or per session, not just at the system level.

## Why It Matters
PACELC is more useful than CAP for real-world database selection. Two AP databases might differ dramatically in normal operation — one may prioritize low latency (PA/EL) while another prioritizes consistency (PA/EC). When evaluating databases for a microservice, ask: "What happens during a partition? What happens during normal operation?" The answers guide the choice of Cassandra (high availability, low latency, eventual consistency) versus Spanner (strong consistency, higher latency, CP).

## Related Concepts
- [CAP Theorem](10-CAP-Theorem.md) — The foundation that PACELC extends
- [Consistency](12-Consistency.md) — Strong vs. eventual consistency is the core axis in both CAP and PACELC
- [Replication](05-Replication.md) — The mechanism that enables the tradeoffs described by PACELC

---

## Mental Model
CAP is like asking what a restaurant does when the kitchen catches fire (partition). PACELC adds: what does the restaurant do on a normal Tuesday? A fast-food chain (PA/EL) serves you quickly but might get your order slightly wrong. A fine-dining restaurant (PC/EC) ensures every dish is perfect but you wait longer — even on a normal Tuesday.
