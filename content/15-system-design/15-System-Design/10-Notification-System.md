# 10-Notification-System

Notification system design covers the delivery of messages across multiple channels (push, SMS, email, in-app) — handling templating, channel routing, batching, deduplication, rate limiting, and delivery tracking at scale.

## Key Components
- **Notification Orchestrator**: Accepts notifications from internal services via an API or queue. Routes each notification to the appropriate channel(s) based on user preferences, urgency, and channel health.
- **Template Engine**: Renders notification content from templates + dynamic variables. Supports localization (40+ languages), conditional content (show X if premium user), and A/B testing of message copy.
- **Channel Adapters**: Each delivery channel (FCM/APNs for push, Twilio for SMS, SendGrid for email) is wrapped in an adapter with a common interface. Adapters handle provider-specific retry logic, authentication, and response parsing.
- **Deduplication Service**: Prevents sending the same notification multiple times within a configurable dedup window. Uses a key derived from (user_id, notification_type, content_hash) stored in Redis with TTL.
- **Rate Limiter**: Per-user, per-channel, and global rate limits. Push notifications capped at N/hour per user to avoid app uninstalls. SMS capped due to cost. Uses token bucket or sliding window algorithm.
- **Delivery Tracking**: Callback URLs or webhooks from delivery providers capture status (sent, delivered, bounced, opened, clicked). Ingested into a stream, stored in analytics DB. Drives retry logic and deliverability monitoring.

## Key Challenges
- **Channel reliability**: No channel is 100% reliable. Push notifications may not reach offline devices. SMS gateways have variable latency. Email lands in spam. A robust system downgrades channels and retries with backoff.
- **User preferences**: Users want control over which notifications they receive, on which channels, and at what times. Preference service must be checked before every notification dispatch.
- **Cost management**: SMS is expensive ($0.01/msg). Push is essentially free after infrastructure cost. Smart routing prefers cheap channels when urgency allows. Round-robin across SMS providers for cost optimization.
- **Delivery ordering**: Notifications for the same user should be delivered in-order, but different users can be parallelized. Partition by user_id when publishing to message queues.
- **Notification volume at scale**: Push to 100M users for a critical alert means orchestrating 100M deliveries. Requires fan-out via a message queue with partitioned consumers.

## Key Design Decisions
- **Declarative notification templates**: Templates are stored in a registry with mandatory and optional parameters. Services construct notifications by providing the template ID + parameter map. The orchestrator handles rendering, localization, and channel-specific formatting.
- **Channel priority routing**: For each notification type (transactional, promotional, alert), a policy defines channel priority. E.g., password reset → always push + email (never SMS). Promotional → push first, email as fallback.
- **Outbox pattern for reliability**: Notifications are written to an outbox table in the same DB transaction as the triggering event. A background poller picks up outbox entries and publishes them to the notification queue. This ensures exactly-once creation.
- **Delivery status as event stream**: Each delivery status update (sent, opened, bounced) is published to Kafka/EventBus. Consumers update the notification store, trigger retry logic, and feed analytics dashboards.

## Related Concepts
- [11-Chat-System](11-Chat-System.md) — Real-time message delivery and presence awareness
- [04-WhatsApp](04-WhatsApp.md) — Delivery semantics and offline message queuing

---

## Mental Model
A notification system is like a postal sorting office. Letters (notifications) arrive from various senders, are sorted by recipient, checked against the recipient's delivery preferences (no junk mail, hold during vacation), stamped with the correct postage (channel choice — cheap postcard for push, expensive courier for SMS), and sent out. If the courier fails, the office tries a different carrier or sends a postcard instead.
