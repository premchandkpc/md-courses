# 09-Hot-Partition

A partition that receives a disproportionately high volume of traffic compared to other partitions, creating a bottleneck that limits overall system throughput. Hot partitions are the most common performance problem in distributed systems that use partitioning or sharding.

## Overview
Hot partitions occur when the distribution of requests across partitions is skewed. A popular user, a frequently accessed key, a range of data with high activity, or a poorly chosen shard key can all create a hot spot. The hot partition becomes overloaded while other partitions sit idle. In Kafka, a single partition with a high-volume key (e.g., a viral tweet's event stream) causes consumer lag. In sharded databases, a shard holding celebrity users' data handles orders of magnitude more queries than the others. In load-balanced services, a hash ring can develop hot spots if virtual nodes are insufficient.

## Key Characteristics
- **Uneven load distribution**: One partition handles 80% of traffic while the rest share 20%. Metrics show high CPU/latency on one shard and idle resources on others.
- **Shard key is often the root cause**: Low-cardinality keys (status field, region code, tenant ID) naturally group traffic unevenly. High-cardinality keys like user ID or UUID spread load better.
- **Celebrity or "gorilla" problem**: In social systems, a small number of users (celebrities, power users) generate disproportionate traffic. Sharding by user ID concentrates their load on one shard.
- **Rebalancing is the fix**: Split the hot partition, apply consistent hashing with virtual nodes, or redesign the shard key to include a random suffix (salting).
- **Temporary vs. permanent**: A flash crowd (breaking news) creates a temporary hot partition. A systemic design issue (bad shard key) creates a permanent one.

## Why It Matters
Hot partitions defeat the purpose of horizontal scaling. The system can't achieve linear throughput because one bottlenecked partition limits everything. Detecting and mitigating hot partitions is a core operational skill. Solutions include splitting the hot partition, redistributing its data across more nodes, applying cache in front of the hot data, or redesigning the data model to avoid the hot key.

## Related Concepts
- [Sharding](03-Sharding.md) — Poor shard key selection is the primary cause of hot partitions
- [Partitioning](04-Partitioning.md) — Hot partitions can occur in any partitioned system (DB tables, Kafka topics, message queues)
- [Horizontal Scaling](01-Horizontal-Scaling.md) — More instances won't help if hot partitions bottleneck at the data layer

---

## Mental Model
A highway with 5 lanes. On a normal day, traffic spreads evenly. But on game day, everyone takes the lane leading to the stadium exit. That lane becomes a parking lot while the other 4 lanes flow freely. You could add 10 more lanes — but if they all still lead to the same stadium exit, none of them help.
