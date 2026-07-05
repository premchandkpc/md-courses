# 06-YouTube

YouTube's system design covers video hosting and streaming at massive scale — handling 500+ hours of uploads per minute, transcoding to dozens of formats, global CDN delivery, recommendations, and engagement features (comments, likes, subscriptions).

## Key Components
- **Upload Pipeline**: Raw video received via HTTP multipart upload (resumable with chunked transfer). Stored temporarily on upload servers, then moved to blob storage (Google Cloud Storage). Acknowledgment returned to user immediately; processing happens asynchronously.
- **Transcoding Service**: Raw video converted into multiple resolutions (144p–4K), codecs (H.264, VP9, AV1), and packaging formats (DASH, HLS). Uses a distributed job queue — videos split into segments, each segment encoded in parallel on worker nodes, then reassembled into manifests.
- **CDN (Google Edge Cache)**: Serving video from 1000+ edge nodes worldwide. Uses DNS-based routing to direct users to the closest edge. Pre-fetching algorithm predicts user behavior (e.g., if 70% of users watch the next video, pre-fetch that segment).
- **Recommendation System**: Two-stage ranking — candidate generation (retrieve hundreds of relevant videos via collaborative filtering + content-based) followed by ranking (deep neural network scoring candidates by predicted watch time, not clicks). Adds exploration via random sampling.
- **Comment System**: Threaded comments with real-time updates. Uses a hierarchical storage structure — video → comment thread → comments → replies. Heavy write amplification for popular videos (millions of comments).
- **Subscription Service**: Fan-out on write — new upload from subscribed channel is inserted into subscriber feeds. Like Instagram, uses hybrid fan-out for high-subscriber channels.

## Key Challenges
- **Upload-to-live latency**: Seconds of latency between when a video is recorded and when viewers see it (for livestreaming). Requires chunked encoding and publishing — each segment is available for viewing before the next segment is finished.
- **Storage costs**: Exabytes of video. Cold storage costs dominate. Use multiple storage tiers: hot (SSD/persistent disk) for recently uploaded or popular content, nearline/coldline for long-tail content.
- **Bandwidth costs**: The #1 operational expense. Optimized via aggressive caching, ISP peering (Google Global Cache boxes), and adaptive bitrate to minimize unnecessary data transfer.
- **Copyright detection (Content ID)**: Fingerprint uploaded videos against a database of copyrighted content using audio and visual hash matching. Must process 500+ hours of uploads per minute in near real-time.

## Key Design Decisions
- **Segmented video storage**: Video stored as small segments (2-10 seconds) rather than monolithic files. Enables parallel encoding, adaptive bitrate switching, and partial playback.
- **Transcoding as async DAG**: A video's processing pipeline is modeled as a directed acyclic graph — each encoding step depends on the raw source but steps are parallelized. Failed steps retry independently.
- **Edge-first architecture**: Optimize for serving from edge rather than origin. Edge nodes cache popular content, pre-fetch "up next" segments, and only fall back to regional or origin servers for cache misses.
- **PostgreSQL for metadata**: Core platform data (video metadata, user data, subscriptions) in sharded PostgreSQL. Blob storage for video content.

## Related Concepts
- [03-Netflix](03-Netflix.md) — Streaming delivery patterns and adaptive bitrate approaches
- [05-Instagram](05-Instagram.md) — Feed generation and fan-out patterns for subscriptions

---

## Mental Model
YouTube is like a global library where every patron brings in new books at a staggering rate. First, the book is scanned (uploaded), then sent to a printing press (transcoding) that produces dozens of editions (resolutions) simultaneously. Each edition is stored in mini-libraries around the world (edge cache). The librarian (recommendation system) notices which books you linger on and suggests similar ones.
