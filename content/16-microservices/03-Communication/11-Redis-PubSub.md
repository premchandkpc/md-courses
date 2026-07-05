# 11-Redis-PubSub

Redis PubSub is a publish/subscribe messaging paradigm built into Redis. It follows a fire-and-forget model — messages are pushed to all subscribers and not persisted.

## Overview

Redis PubSub implements a simple pub/sub pattern: publishers send messages to channels (named strings), and subscribers receive messages on channels they've subscribed to. Messages are delivered to all active subscribers in real-time. There is no message persistence, no message queuing for offline subscribers, and no delivery acknowledgment. If a subscriber disconnects, it misses all messages sent while it was offline.

## Key Characteristics

- **Fire-and-Forget**: Messages are delivered to currently connected subscribers. If no subscriber is listening, the message is lost. This is the defining characteristic of Redis PubSub — use it only when message loss is acceptable.
- **Pattern Subscriptions**: Subscribers can use glob-style patterns (`orders:*`, `events.*`) to subscribe to multiple channels in a single command. This is similar to NATS wildcards but uses Redis's `PSUBSCRIBE` command.
- **No Persistence**: Unlike Redis streams or Kafka, PubSub messages are not stored on disk or in memory. Once sent, they're gone if not delivered to a connected subscriber.
- **Low Latency**: Because there's no persistence or ack mechanism, Redis PubSub has extremely low latency — typically microseconds within the same data center.
- **Integration with Redis Ecosystem**: PubSub can be combined with other Redis features. It's commonly used to broadcast state changes across Redis instances and to distribute WebSocket messages across server instances.

## Why It Matters

Redis PubSub is the simplest pub/sub system available — it's a single Redis command away. Its main use case in microservices is real-time inter-service notifications where message loss is acceptable: cache invalidation broadcasts, WebSocket server mesh coordination, live dashboards, and internal event notifications. For durable messaging, use Redis Streams (which add persistence and consumer groups) or a dedicated broker like Kafka or RabbitMQ.

## Related Concepts

- [07-Message-Brokers](07-Message-Brokers.md) — broker comparison
- [08-Kafka](08-Kafka.md) — durable alternative to Redis PubSub
- [05-WebSockets](05-WebSockets.md) — Redis PubSub is often used to fan out messages across WebSocket servers
- [10-NATS](10-NATS.md) — similar lightweight pub/sub with broader capabilities

---

## Mental Model

Redis PubSub is like a public address system in a stadium. The announcer (publisher) speaks into a microphone, and everyone currently listening on the speakers (subscribers) hears the message in real-time. If you're in the bathroom when an announcement is made, you miss it — there's no recording. It's perfect for "attention, lost child at gate 5" messages but useless for "please read this important document" notifications.
