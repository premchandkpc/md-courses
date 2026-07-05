# 04-WhatsApp

WhatsApp's system design covers a globally-scalable messaging platform with end-to-end encryption, reliable delivery semantics, presence awareness, group chat, and media sharing — serving billions of users with a lean engineering team.

## Key Components
- **Connection Manager**: Persistent TCP/WebSocket connections maintained between client and server. Handles routing of messages, presence, and typing indicators. Must survive mobile network handoffs (WiFi → cellular).
- **Message Store**: Per-user append-only log of messages. Servers store messages until delivered (not forever). Designed for sequential read — when a user reconnects, all undelivered messages are replayed.
- **End-to-End Encryption (Signal Protocol)**: Each message encrypted with a per-message key derived from the recipient's public key. Server cannot read content. Double Ratchet algorithm provides forward secrecy and future secrecy.
- **Presence Service**: Tracks online/battery/last-seen state. Uses pub-sub channels per user — when user goes online, a message is published to all their contacts' presence subscriber lists.
- **Group Chat**: Messages stored on server, then fanned out to all group members. For very large groups, server uses sender-side fan-out (sender uploads once, server distributes). Uses a hybrid model for Medium groups (e.g., 50 members — deliver to each) and Large groups (e.g., 256 members — use a broadcast channel).

## Key Challenges
- **Delivery semantics**: "Last seen" at 2:34 AM — must be accurate within seconds while handling billions of daily active users. Balance between privacy (show exact time? show "recently"?) and infrastructure load.
- **End-to-end encryption**: If you can't read messages, you can't deduplicate or search them server-side. This rules out many traditional optimization techniques.
- **Offline delivery**: Devices off the network for hours or days. Messages must persist in server-side queues and be flushed when the device reconnects, in order.
- **Group scalability**: A group with 256 members sending one message creates 256 deliveries. At WhatsApp scale, this fan-out multiplication overwhelms naive approaches.

## Key Design Decisions
- **Erlang/OTP on FreeBSD**: Chosen for soft real-time, massive concurrency (lightweight processes), and hot code swapping without downtime. Each connection manager runs as an Erlang process.
- **No message IDs per-user**: Instead, watermark-based delivery tracking. Each user's message store has a watermark pointer marking which messages have been delivered. Simplifies acknowledgments.
- **Server does NOT store messages long-term**: Once delivered to all devices, the message is purged from the server. This keeps storage manageable and aligns with privacy guarantees.
- **Phone number as identity**: No usernames, no profile discovery. This eliminates spam accounts and simplifies the identity model — tied to SIM card ownership.

## Related Concepts
- [11-Chat-System](11-Chat-System.md) — Real-time messaging architecture and WebSocket management
- [10-Notification-System](10-Notification-System.md) — Push notification delivery channels

---

## Mental Model
WhatsApp is like a postal service that encrypts every letter before it leaves the sender's hand. The carrier (server) delivers the sealed envelope but can't open it. If you aren't home, the carrier holds your mail until you return (reconnect) and hands it all to you at once, in the order it was sent.
