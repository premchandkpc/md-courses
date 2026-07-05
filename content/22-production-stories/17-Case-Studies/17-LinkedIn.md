# 17-LinkedIn

LinkedIn's transition from a monolithic Rails application to a services-oriented architecture produced key infrastructure innovations — including Kafka (the de facto event streaming standard), the Voldemort key-value store, and the REST.li framework for service development.

## Problem
LinkedIn launched in 2003 as a monolithic Ruby on Rails application with a single Oracle database. As the network grew to 100M+ members (2011) and beyond, the monolith couldn't scale — database connections were exhausted, search was slow, and the site experienced frequent outages during peak traffic. The "Info" (profile feed) service in particular struggled with read/write amplification as the network grew.

## Architecture
- **Service Decomposition (2008-2012)**: LinkedIn decomposed the monolith into services along domain boundaries: member profiles, connections, search, messaging, groups, news feed, and notifications. Each service owned its data store and exposed APIs through REST.li.
- **REST.li Framework**: LinkedIn built REST.li (open-sourced 2012) as a framework for building RESTful microservices. It provides schema-based API definitions (PDSC — Pegasus Data Schema), automatic validation, dynamic discovery, and client/server code generation. REST.li ensures APIs are typed, versioned, and discoverable.
- **Apache Kafka (originated at LinkedIn)**: Kafka was created at LinkedIn to handle the real-time data feed problem — ingesting billions of member events (profile views, connections, shares) and making them available for processing. Kafka's architecture (partitioned log, consumer groups, replayability) was designed specifically for LinkedIn's scale. It became the backbone of their data pipeline.
- **Voldemort (key-value store)**: LinkedIn built Voldemort (named after the Harry Potter villain) as a distributed key-value store providing automatic replication, partitioning, and high availability. It serves LinkedIn's session data and high-read workloads at low latency.
- **Feed (Info) Architecture**: LinkedIn's news feed uses a hybrid fan-out approach. When a member shares a post, the share event is published to Kafka. Consumers update a Redis-based timeline for the member's connections. For members with 10K+ connections (power users), the feed is generated on-read to avoid massive fan-out writes. The timeline is a sorted list of share IDs retrieved with pagination.

## Lessons Learned
- **When you need a system that doesn't exist, build it**: Kafka, Voldemort, and REST.li were built because off-the-shelf solutions couldn't handle LinkedIn's scale and requirements. Kafka alone became a foundational technology for the entire data infrastructure industry.
- **Schema evolution is critical for service APIs**: REST.li's focus on typed, versioned schemas prevented the "broken contract" problem that plagues many microservice deployments. An API contract that's machine-verified catches breaking changes before deployment.
- **Fan-out for feeds needs careful tuning**: LinkedIn's hybrid approach — fan-out for most users, pull for power users — is the standard pattern. The threshold depends on the platform's graph density. Monitor the distribution and tune the threshold dynamically.
- **Data infrastructure drives product capability**: Kafka enabled real-time analytics, stream processing, and async data pipelines that were impossible before. Investing in data infrastructure (streaming, storage, processing) unlocks product features that competitors can't easily replicate.

## Related Concepts
- [05-Instagram](../15-System-Design/05-Instagram.md) — Feed generation patterns and fan-out approaches
- [04-WhatsApp](../15-System-Design/04-WhatsApp.md) — Real-time event processing and message delivery

---

## Mental Model
LinkedIn's architecture evolution is like a small town (monolith) growing into a sprawling metropolis. The original town had a single general store (Rails + Oracle) that everyone shopped at. As the city grew, specialized stores opened (services): a butcher shop (member profiles), a bakery (feed), a bank (payments). A new transit system (Kafka) moved goods between these stores. Each store managed its own inventory (database) but communicated through standardized roads (REST.li).
