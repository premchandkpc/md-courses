# System Design Interview — Complete Preparation Guide

System design interviews evaluate your ability to architect large-scale distributed systems. These are the most important interviews at senior+ levels (FAANG, top tech companies).

## The Framework

```
1. Requirements (5 min)
   - Functional: What does the system do?
   - Non-functional: Scale, latency, availability, durability

2. Data Model & API (5 min)
   - Schema design, API endpoints
   - Data sizes, access patterns

3. High-Level Design (10 min)
   - Architecture diagram, components
   - Client → Load Balancer → Services → DB

4. Deep Dive (15-20 min)
   - Focus on one interesting component
   - Trade-offs, bottlenecks, failure modes

5. Wrap (5 min)
   - Summary, alternative approaches
   - What would you do with more time?
```

## Must-Know Systems

| System | Key Challenge | Interview Angle |
|--------|--------------|-----------------|
| URL Shortener | Key generation, redirect | TinyURL, bit.ly |
| Chat System | Real-time messaging, ordering | WhatsApp, Messenger |
| News Feed | Fan-out, ranking, caching | Twitter, Instagram |
| Search Engine | Crawling, indexing, ranking | Google Search |
| Video Streaming | Large files, CDN, bitrate | YouTube, Netflix |
| Ride Sharing | Real-time matching, geo-index | Uber, Lyft |
| Payment System | Idempotency, consistency | Stripe, PayPal |
| Rate Limiter | Distributed counting, throttling | API Gateway |
| Proximity Service | Geospatial indexing | Yelp, Nearby |
| Distributed Queue | Ordering, persistence, replication | Kafka, SQS |

## Key Technologies Cheat Sheet

| Concern | Technology |
|---------|-----------|
| Load Balancing | Round Robin, Least Connections, Consistent Hashing |
| Caching | Redis, Memcached, CDN (CloudFront, Cloudflare) |
| Database | PostgreSQL (relational), Cassandra (wide-column), DynamoDB (KV), S3 (blob) |
| Queue | Kafka, RabbitMQ, SQS, Pulsar |
| Search | Elasticsearch, Solr |
| Monitoring | Prometheus, Grafana, Datadog |
| Service Mesh | Envoy, Linkerd |
| Container | Kubernetes, ECS, Docker |

## Common Deep Dives

### Database Scaling
```
Single DB → Read Replicas → Sharding → Distributed DB
```
- **Sharding key**: choose for even distribution + query efficiency
- **Consistent hashing**: minimize rebalancing on node changes

### Caching Strategy
```
Client Cache → CDN → Application Cache (Redis) → DB Cache → DB
```
- **Cache-aside**: app checks cache first, writes on miss
- **Write-through**: write to cache + db synchronously
- **Write-behind**: write to cache, async write to db

### CAP Trade-offs
```
CP (Consistency + Partition Tolerance):   Spanner, HBase, Zookeeper
AP (Availability + Partition Tolerance):  Cassandra, DynamoDB, Couchbase
CA (Consistency + Availability):          Single-node PostgreSQL
```

## Common Mistakes

- **Diving into detail too early**: start with high-level, then deep dive
- **Ignoring data sizing**: always estimate storage, bandwidth, QPS
- **Forgetting failure modes**: what happens when a service/cache/DB goes down?
- **Over-engineering**: don't propose sharding for 10K users
- **Missing trade-offs**: every design choice has pros and cons — discuss them
- **No numbers**: estimate latency (1ms in DC, 100ms cross-region), throughput, storage

## Estimation Reference

```
1 byte = 8 bits
1 KB = 10³ bytes
1 MB = 10⁶ bytes
1 GB = 10⁹ bytes
1 TB = 10¹² bytes
1 PB = 10¹⁵ bytes

QPS for 100M DAU:
  - Daily active users: 100M
  - Actions per user per day: 10
  - Total daily actions: 1B
  - QPS peak: 1B / 86400 * 2 (peak factor) ≈ 23K QPS

Storage for 1B items:
  - 1B items × 1KB per item = 1TB
  - With 3x replication = 3TB
  - 3-year growth = 9TB

Network latency:
  - Same DC: 0.5-2ms
  - Cross-region (US-EU): 100-150ms
  - CDN edge: <50ms
```

## Interview Checklist

- [ ] Clarified requirements before designing
- [ ] Estimated data sizes and QPS
- [ ] Drew architecture diagram
- [ ] Discussed trade-offs explicitly
- [ ] Covered failure modes and fallbacks
- [ ] Mentioned monitoring and alerting
- [ ] Discussed how to test the system
- [ ] Summarized key decisions

## Resources

- **Books**: Designing Data-Intensive Applications (Kleppmann), System Design Interview (Alex Xu)
- **Practice**: System Design Primer (GitHub), Daily Coding Problem
- **Roadmaps**: This repo's `15-system-design/` (86 files), `21-roadmaps/`
