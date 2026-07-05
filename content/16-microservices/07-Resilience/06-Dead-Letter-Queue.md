# 06-Dead-Letter-Queue

A Dead Letter Queue (DLQ) is a holding area for messages that could not be processed successfully after all retry attempts. It prevents message loss, preserves the failure payload for forensic analysis, and enables manual or automated redrive once the underlying issue is resolved.

## Overview

In event-driven and message-bus architectures, consumers occasionally fail to process a message due to malformed payloads, missing data, transient outages, or bugs. Rather than discarding the message or blocking the queue, the broker moves it to a DLQ after exhausting the consumer's retry policy. Operations teams monitor the DLQ depth, inspect failed messages, and either fix and redrive or archive them.

## Key Characteristics

- **Automated Routing**: The message broker (RabbitMQ, Kafka, SQS) automatically moves undeliverable messages to a DLQ after the retry threshold is exceeded.
- **Payload Preservation**: The original message body, headers, and metadata are preserved, including the failure reason, stack trace, and delivery attempt count.
- **Redrive Capability**: Once the root cause is fixed, messages can be replayed from the DLQ to the original queue for reprocessing.
- **Alerting Threshold**: DLQ depth is monitored; sustained non-zero depth or rapid growth triggers an alert.
- **TTL and Archival**: Messages may have a time-to-live after which they are automatically deleted or archived to long-term storage.
- **Manual Intervention**: Some DLQ scenarios (e.g. malformed JSON) require a human to fix and redrive; others (e.g. missing reference data) can be handled by automated replay after a dependency recovers.

## Why It Matters

Without DLQs, failed messages are either silently dropped (data loss) or repeatedly retried forever (resource waste). DLQs provide a safety net: no message is ever truly lost, failures are visible and measurable, and the system can self-heal once the root cause is addressed.

## Related Concepts

- [Retry](02-Retry.md) — Messages normally retry before landing in the DLQ; the DLQ is the terminal state after retry exhaustion.
- [Fallback](05-Fallback.md) — Fallback and DLQ serve different roles: fallback returns an alternative response inline, while DLQ stores the failure for offline analysis.
- [Backpressure](07-Backpressure.md) — A growing DLQ may indicate that consumers cannot keep up, which is a backpressure signal to throttle producers.

---

## Mental Model

A DLQ is a hospital's "failed specimens" bin. If a blood sample can't be processed by the automated analyzer (malformed label, broken vial), it's set aside in a special bin. A technician periodically checks the bin, fixes the issue, and re-runs the sample. Nobody throws the sample away — it's held until it can be handled correctly.
