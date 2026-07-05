# 11-Chat-System

Real-time chat system design covers the infrastructure for instant messaging — WebSocket connection management, presence detection, typing indicators, message history, offline delivery, and multi-device synchronization.

## Key Components
- **WebSocket Gateway**: Manages persistent TCP/WebSocket connections between clients and servers. Each connection is associated with a user_id. The gateway authenticates the WebSocket upgrade request (JWT or session cookie), then routes messages bidirectionally.
- **Message Router**: Receives messages from senders, looks up which gateway server the recipient is connected to, and forwards the message. For recipients on the same server, routes locally. For cross-server delivery, uses a pub-sub backend (Redis Pub/Sub or Kafka).
- **Presence Service**: Tracks online/offline/idle status. Users subscribe to presence updates of their contacts/circle. On state change (user goes online), publishes an event to all subscribers. Uses heartbeat pings with configurable timeout (e.g., 30s missed ping → mark as offline).
- **Typing Indicator**: When a user types, sends a "typing" event to the recipient every ~3 seconds. Server throttles these — they are ephemeral, not stored. The "stop typing" event is sent immediately when the user pauses or sends the message.
- **Message History Store**: Append-only log of messages per conversation. Messages stored with sequence numbers for pagination. Indexed by conversation_id and timestamp. Supports search and scroll-back.
- **Offline Message Queue**: Messages for offline users are stored in a queue (per user, in Redis or Cassandra). When the user reconnects, the queue is replayed in order, then drained.

## Key Challenges
- **Connection state at scale**: Millions of concurrent WebSocket connections. Each connection consumes a file descriptor and memory. Use an event-loop architecture (Node.js, Erlang, or Netty) with per-connection state in shared memory, not per-process.
- **Horizontal scaling of WebSockets**: Connections are sticky to a specific gateway server (connection affinity). When a user reconnects (e.g., phone→laptop), they may land on a different server. Need a routing table mapping user_id → gateway server, stored in Redis.
- **Ordering guarantees**: Messages in a one-on-one conversation must be delivered in the order they were sent. Server assigns a monotonically increasing sequence number per conversation. Clients order by sequence number before display.
- **Offline→online transition**: When a user reconnects, the system must flush queued messages, send the latest presence status to contacts, and sync read receipts. This burst of activity must be throttled to avoid connection floods.
- **Multi-device**: A user may be logged in on phone, laptop, and tablet simultaneously. Messages must be delivered to all online devices. Read receipts are per-message per-device; the "last read" watermark is the max across devices.

## Key Design Decisions
- **Separate gateway from logic**: The WebSocket gateway is a thin proxy handling connection management. Message logic (routing, storage, validation) lives in stateless services behind the gateway. This allows the gateway to scale independently.
- **Redis for presence and routing**: User→server mapping stored in Redis with TTL (renewed on each heartbeat). Presence subscriptions use Redis Pub/Sub. Channel for cross-server message routing.
- **Cassandra for message history**: Write-optimized, linear scalability. Messages are stored with conversation_id as partition key and timestamp as clustering key. Supports "read recent N" and "read since sequence X" efficiently.
- **Idempotent message delivery**: Server assigns a unique message ID on receipt. The delivery acknowledgment is the last safely-received sequence number per conversation (like TCP ACKs). The client can safely replay undelivered messages.

## Related Concepts
- [04-WhatsApp](04-WhatsApp.md) — End-to-end encryption and delivery semantics in messaging
- [10-Notification-System](10-Notification-System.md) — Push notification fallback for offline users

---

## Mental Model
A chat system is like an old telephone switchboard. The operator (WebSocket gateway) plugs your call into the right port for the person you're talking to. If you hang up and call again (reconnect), the operator remembers which switchboard the other person is on. Meanwhile, a postal service (offline queue) holds any letters that arrived while you were away and delivers them when you call in.
