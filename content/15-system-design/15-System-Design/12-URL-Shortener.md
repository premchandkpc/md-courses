# 12-URL-Shortener

URL shortener system design covers the creation of compact short URLs that redirect to longer target URLs — including hash generation, redirection with HTTP 301/302, analytics tracking, rate limiting, custom aliases, and link expiration.

## Key Components
- **URL Generation Service**: Accepts a long URL and returns a short key (e.g., `abc123`). Keys are base62-encoded unique IDs. Users can optionally request a custom alias (e.g., `my-link`). Checks for collision and availability.
- **Redirection Service**: Handles incoming `GET /{short_key}` requests. Looks up the short key, retrieves the long URL, and returns a redirect response (HTTP 301 for permanent, 302 for temporary). 301s are cached by browsers — good for bandwidth, bad for real-time analytics.
- **Analytics Service**: Logs each redirect hit — timestamp, IP address, user-agent, referrer, geolocation (from IP). Data is written asynchronously to avoid adding latency to the redirect. Stored in a time-series database or data warehouse.
- **Rate Limiter**: Prevents abuse — per-IP, per-user, and global rate limits on URL creation and redirection. Uses token bucket or sliding window. Aggressive limits on creation to prevent spam, moderate limits on redirect to avoid analytics pollution.
- **Key Collision Detection**: For auto-generated keys, the probability of collision is low if the key space is large enough (base62 of 7 chars = 3.5 trillion combinations). For custom aliases, collisions are checked before assignment — use a unique constraint on the key column.

## Key Challenges
- **Key generation without centralized sequencer**: Distributed systems need to generate unique keys without a single bottleneck. Approaches include: pre-generated key pools (batch-generate keys and store them), distributed ID generators (Snowflake-style), or hash-based keys (MD5/SHA of long URL, take first N chars — but collision handling is needed).
- **Redirect latency**: The redirect should be as fast as possible — ideally <10ms. Use an in-memory cache (Redis or local LRU) on the redirect server. Cache hits serve the redirect without a DB query.
- **Analytics without blocking redirect**: Analytics writes must not block the redirect response. Write events to an in-memory buffer, batch, and flush to a queue asynchronously. Use ring buffer or disruptor pattern for high throughput.
- **Expiration and cleanup**: Short URLs may expire after a configurable TTL. Expired keys are either recycled back to the key pool or deleted. Cleanup runs as a background job with a TTL index.
- **Custom alias abuse**: Users may try to squat common words or brand names. Validate custom aliases against a blocklist. Implement a moderation flow for disputed aliases.

## Key Design Decisions
- **Pre-generated key pool**: A background job generates random base62 keys and stores them in a Redis set. The URL service pops from the set on each creation request. Eliminates collision concerns and O(1) allocation. Periodic replenishment at low watermark.
- **Redis cache for redirects**: Redirect servers maintain a local Redis cache (or shared Redis cluster) mapping keys to long URLs. Cache misses fall back to the database. Tune TTL based on redirect type: 301s are cached for days (rely on browser caching), 302s for minutes.
- **Base62 encoding**: Uses [a-z, A-Z, 0-9] = 62 characters. 7-character key yields 62^7 ≈ 3.5 trillion combinations. Base64 (with - and _) gives more but is less user-friendly for verbal sharing.
- **Database of record**: PostgreSQL or MySQL for the key→URL mapping. Indexed on key with unique constraint. The redirect cache is a read-optimized layer on top. Analytics data goes to a separate analytics DB (ClickHouse, BigQuery) to avoid impacting the redirect path.

## Related Concepts
- [10-Notification-System](10-Notification-System.md) — Rate limiting patterns for API protection
- [07-Payment-System](07-Payment-System.md) — Idempotency key concepts for duplicate request handling

---

## Mental Model
A URL shortener is like a hotel's front desk directory. Guests are given a room number (short key) for their name (long URL). The directory maps room numbers to names. When you ask the front desk for room 3B (short key redirect), they point you to the guest's actual room (long URL). The hotel also keeps a log of who asked which room and when (analytics).
