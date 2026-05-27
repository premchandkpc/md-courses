# 🏗️ System Design Blueprints — Complete Deep Dive

## 📋 Table of Contents
- [URL Shortener](#url-shortener)
- [Chat System](#chat-system)
- [Video Streaming Service](#video-streaming-service)
- [Rate Limiter](#rate-limiter)
- [Simplest Mental Model](#simplest-mental-model)

---

## URL Shortener

### Requirements

```
Functional:
  - Shorten long URL to 6-7 char key
  - Redirect to original (302 for analytics, 301 for perf)
  - Optional: custom alias, TTL, analytics

Non-Functional:
  - Read:write ≈ 100:1. 100M URLs/month → ~38 writes/s, ~3800 reads/s
  - Redirect < 10ms p99. 100% availability. URLs last forever.
```

### Key Generation

```python
BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

def encode_base62(num: int) -> str:
    if num == 0: return BASE62[0]
    result = []
    while num > 0:
        result.append(BASE62[num % 62])
        num //= 62
    return ''.join(reversed(result))

# Snowflake ID (64-bit): 41b timestamp | 5b dc | 5b machine | 12b sequence
def snowflake_id(ts: int, dc: int, machine: int, seq: int) -> int:
    return (ts << 22) | (dc << 17) | (machine << 12) | seq
```

### Redirect Flow

```text
Browser                          URL Shortener
  |-- GET /abc123 ----------------------> | Cache lookup
  |                                       |   hit → return URL
  |                                       |   miss → DB → populate cache
  |<-- 301 Location: https://example.com  |

301 = permanent, browser caches, no analytics on repeat
302 = temporary, always hits shortener, enables click counting
```

### Data Model

```sql
CREATE TABLE urls (
    id BIGINT PRIMARY KEY, short_key VARCHAR(7) UNIQUE,
    original_url TEXT NOT NULL, user_id BIGINT,
    created_at TIMESTAMP DEFAULT NOW(), expires_at TIMESTAMP NULL
);
-- Sharding: hash(short_key) → consistent hashing
-- Bloom filter at cache layer rejects invalid keys fast
```

**bit.ly Architecture**: Snowflake IDs. Redis cache (50M entries). 301 for repeat visitors, 302 for first hit (track once). Data warehouse for analytics.

---

## Chat System

### Requirements

```
1:1: Real-time <100ms, persistent history, typing/read receipts, delivery status
Group: Up to 5000 members. Write fanout (small groups), read fanout (large).
Scale: 500M DAU, 100B msg/day → ~1.2M msg/s peak
```

### Architecture

```text
+--------+     WS     +----------+       +----------+
| Client |<---------->| Gateway  |<----->| Presence |
+--------+            +----------+       | Service  |
                            |            +----------+
                            |            +----------+
                            +----------->| Chat     |
                                         | Service  |
                                         +----------+

Connection Manager: WS + session(user_id, device_id). Heartbeat 30s, timeout 90s.
Reconnection: client sends last_message_id. Backpressure: drop if client lags.
```

### Message Flow

```python
def send_message(sender_id: str, receiver_id: str, content: str) -> Message:
    msg = Message(id=generate_sequential_id(), sender_id=sender_id,
                  receiver_id=receiver_id, content=content, status="sent")
    msg_db.store(msg, partition=hash_conversation(sender_id, receiver_id))

    conn = presence_service.get_connection(receiver_id)
    if conn:
        gateway.send(conn, msg); msg.status = "delivered"
    else:
        push_notification(receiver_id, msg)
    return msg
```

### Group Chat Fanout

```text
Small Group (≤500) — Write Fanout:
  Write 1 copy to group store. Read member list. Write 1 copy per online inbox.

Large Group (500-5000) — Read Fanout (Pull):
  Write 1 copy to group store. Members pull on reconnect (track last_read_id).

WhatsApp: ≤256 = write fanout, >256 = read fanout. Inbox per user (time-ordered).
```

### Presence Service

```text
Redis model:
  SET user:{id}:online → {conn_id_1, conn_id_2}
  STRING user:{id}:status → {"last_seen": ts, "status": "online|away|offline"}
  PUB/SUB presence:{id} → notify friends

Heartbeat 30s. No beat 90s→away, 300s→offline. Wait before marking offline (spotty).
```

### Message Ordering

- **Sequential ID per conversation**: Monotonic counter. Clients sort by ID.
- **HLC**: Physical time + logical counter. Causal ordering without full vector clocks.

---

## Video Streaming Service

### Encoding Pipeline

```text
Ingest → Transcode → Segment → Package → Deliver

                            Audio (AAC)
Raw Video ──┬─> 1080p ────┤
             ├─> 720p ─────┤── CMAF ──► HLS (.m3u8 + .ts)
             ├─> 480p ─────┤          └► DASH (.mpd + .m4s)
             ├─> 360p ─────┤
             └─> 240p ─────┤
```

### HLS

```text
# master.m3u8
#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080
high.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1280x720
medium.m3u8

# medium.m3u8
#EXTM3U #EXT-X-TARGETDURATION:6 #EXT-X-MEDIA-SEQUENCE:160
#EXTINF:6.000, segment_160.ts
#EXTINF:6.000, segment_161.ts
```

### DASH

```xml
<MPD type="dynamic" availabilityStartTime="2025-05-27T00:00:00Z">
  <Period id="1">
    <AdaptationSet mimeType="video/mp4">
      <Representation bandwidth="2500000" width="1280" height="720">
        <SegmentTemplate media="seg_$Number$.m4s" startNumber="160" duration="2"/>
      </Representation>
    </AdaptationSet>
  </Period>
</MPD>
```

### Adaptive Bitrate (ABR)

```python
def select_bitrate(throughputs: list[float], bitrates: list[int],
                   safety: float = 0.8) -> int:
    safe = sum(throughputs)/len(throughputs) * safety
    return max([b for b in bitrates if b <= safe] + [bitrates[0]])
```
- **Throughput-based**: Select highest bitrate ≤ 80% measured throughput.
- **Buffer-based (BOLA)**: Maintain 10-30s buffer. Growing → upgrade. Shrinking → downgrade.
- **Netflix Open Connect**: OCAs at ISPs. Custom NGINX + FreeBSD. Own CDN.
- **DRM**: Widevine, FairPlay, PlayReady. Signed URLs / cookies for CDN auth.

---

## Rate Limiter

### Algorithms

```python
# Token Bucket — most common
class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens/sec
        self.tokens = capacity
        self.last_refill = time.time()

    def allow_request(self) -> bool:
        now = time.time()
        self.tokens = min(self.capacity,
                          self.tokens + (now - self.last_refill) * self.refill_rate)
        self.last_refill = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

# Sliding Window Counter — approximate, memory efficient, ~0.3% error
class SlidingWindowCounter:
    def __init__(self, limit: int, window_ms: int, sub_windows: int = 10):
        self.limit = limit
        self.subwindow_ms = window_ms // sub_windows
        self.counts = {}

    def allow_request(self, key: str) -> bool:
        now = time.time() * 1000
        curr_win = int(now / self.subwindow_ms)
        prev_win = curr_win - 1
        elapsed = now - curr_win * self.subwindow_ms
        weight = 1.0 - elapsed / self.subwindow_ms
        # Approximate = prev_count * weight + curr_count
        # ... increment if under limit
```

Other algorithms: **Fixed Window** (burst at boundary), **Sliding Window Log** (accurate but memory-heavy), **GCRA** (Cloudflare/Kong, O(1) per key).

### Distributed Rate Limiting

```text
Single-node Redis + Lua: atomic INCR + PEXPIRE. SPOF but accurate.
Local counters + periodic sync: faster, allows small bursts (drift = limit × sync_interval/window).
Consistent hashing → user mapped to fixed limiter node. Exact per-node, rebalancing cost.
```

### Headers & Layering

```http
200 OK:  X-RateLimit-Limit: 100  X-RateLimit-Remaining: 87  X-RateLimit-Reset: 1716825600
429 Too Many Requests:  Retry-After: 30  X-RateLimit-Remaining: 0
```

```text
Edge (IP/DDoS) → App (user/endpoint) → DB (connection pool)

Burst handling: short bursts to limit (token bucket), queue (limited), fail fast (429),
degraded response (stale data).
```

---

## Simplest Mental Model

> **These blueprints are specialized buildings to solve specific problems.**
>
> - **URL Shortener** = Coat check counter. Hand in long coat (URL), get ticket stub (short code). Return ticket → get coat. Stub lookup is fast (cache). Invalid tickets checked against a guest list (bloom filter). The counter never closes.
> - **Chat System** = Walkie-talkie network across a city. Each user has a base station (WebSocket). Gateways route messages. Small groups get messages forwarded to everyone (write fanout). Large groups check a bulletin board (read fanout). Presence service = live on/offline directory.
> - **Video Streaming** = Multi-format printing press. Upload photo, press produces wallet(240p), 4×6(480p), 8×10(720p), poster(1080p) all at once. Each format cut into strips (segments) and packed in envelopes (HLS/DASH). Local print shops stock popular sizes (CDN). Your phone picks the right size based on connection speed (ABR).
> - **Rate Limiter** = Club bouncer counting people per time window. Token bucket = bowl of tokens replenishing at fixed rate, need one to enter. Sliding window = exactly how many entered in last 60s. Distributed = multiple bouncers coordinating across doors. 429 = "Club is full, come back later."