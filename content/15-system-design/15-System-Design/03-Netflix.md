# 03-Netflix

Netflix's system design covers streaming video at global scale — content ingestion, transcoding, CDN delivery, adaptive bitrate streaming, recommendation engines, and the operational practices (chaos engineering) that keep it running across 190+ countries.

## Key Components
- **Content Ingestion Pipeline**: Raw video files from studios transcoded into multiple formats/resolutions (H.264, H.265, VP9, AV1) using a distributed encoding queue. Mezzanine file stored in S3, encoding farm runs on EC2 spot instances.
- **CDN (Open Connect)**: Netflix's own CDN — purpose-built appliances deployed inside ISP data centers serving ~95% of traffic locally. Reduces backbone costs and improves latency.
- **Adaptive Bitrate Streaming**: Client downloads segments in chunks, switching quality based on bandwidth. Uses DASH (Dynamic Adaptive Streaming over HTTP). Encodes at 50+ bitrate ladders.
- **Recommendation Engine**: Matrix factorization + deep learning models scoring personalized title lists. Trained offline, served via a dedicated recommendations service with pre-computed results.
- **Chaos Engineering Tooling**: Chaos Monkey randomly terminates production instances. Chaos Kong simulates entire AWS region failures. Built to prove resilience continuously rather than test once.

## Key Challenges
- **Global content delivery**: 200M+ subscribers, peak traffic >1Tbps. Requires massive edge infrastructure and intelligent routing.
- **Personalization at scale**: 100M+ title catalog, personalized per-user. Pre-computing all combinations is infeasible; use layered ranking with coarse → fine filtering.
- **Fault tolerance**: Any AWS instance can fail at any time. Architecture assumes constant failure and is designed to degrade gracefully.
- **Multi-region state**: Read-only replica for catalog, but user state (watch history) follows the viewer. Consistency model is eventual for recommendations, strong for payments.

## Key Design Decisions
- **Micro-frontends**: The UI is assembled from independent modules (row, detail, search) owned by different teams. Each deploys independently via A/B testing infrastructure.
- **API Gateway (Zuul)**: All client requests route through Zuul for authentication, rate limiting, routing, and request/response transformation. Handles 1M+ requests/sec.
- **Message broker (EVCache/InfiniBand)**: Internal caching layer (EVCache — memcached-based) for session data. InfiniBand for high-throughput inter-service communication.
- **Database split**: Catalog metadata in EVCache + Cassandra, user viewing history in Cassandra, billing in relational DB, search in Elasticsearch.

## Related Concepts
- [06-YouTube](06-YouTube.md) — Video transcoding and CDN delivery patterns
- [17-Case-Studies/17-Netflix.md](../17-Case-Studies/17-Netflix.md) — Netflix's cloud migration story and chaos engineering origin

---

## Mental Model
Netflix is like a global TV station with infinite channels, but each viewer has their own personalized "channel lineup" generated in real-time. The content doesn't live in a local warehouse — it's streamed from mini-warehouses (Open Connect boxes) inside every neighborhood's ISP.
