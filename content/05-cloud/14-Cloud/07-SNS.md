# 07-SNS

Amazon Simple Notification Service is a fully managed pub/sub messaging service. SNS delivers messages from a publisher to multiple subscribers (fan-out), including SQS queues, Lambda functions, HTTP/HTTPS endpoints, email, SMS, and mobile push notifications.

## Overview
SNS organizes messages around topics. A publisher sends a message to a topic ARN. SNS immediately delivers copies to every subscriber of that topic. Each subscriber receives the full message independently. SNS supports message filtering — subscribers can specify a filter policy (e.g., only receive messages with attribute `eventType: order_placed`) to reduce noise. SNS uses a push model: it delivers messages to subscribers as they arrive, unlike SQS's pull model. SNS is regional and provides cross-region delivery via HTTP endpoints.

## Key Characteristics
- **Fan-out pattern**: One message → N subscribers. This is the primary use case. A single event (e.g., "order placed") can simultaneously update a search index, send email, push a mobile notification, and trigger a Lambda function.
- **SQS subscription**: SNS to SQS is the most common architecture for fan-out. The topic sends the message to multiple SQS queues, each consumed by a different service. SQS provides the durability and retry; SNS provides the routing.
- **Lambda subscription**: SNS can invoke Lambda functions directly. The Lambda receives the SNS event payload and processes it. Used for event-driven workflows.
- **Message filtering**: Subscribers define filter policies on message attributes. SNS evaluates the filter and only delivers matching messages. Server-side filtering reduces waste and consumer processing load.
- **Delivery retries**: SNS retries delivery to HTTP/HTTPS endpoints with exponential backoff. Failed messages can be archived to a DLQ or delivered to a Lambda for fallback processing.
- **FIFO topics**: FIFO topics (paired with FIFO SQS queues) provide ordering and deduplication for fan-out scenarios that require strict message ordering across subscribers.
- **Cost**: $0.50 per million SNS requests (publishes). SQS delivery and Lambda invocations have additional costs.

## Why It Matters
SNS enables the event-driven architecture at the heart of many microservices systems. Rather than each producer calling each consumer directly (tight coupling), services emit events to topics. Any service can subscribe without the producer knowing. This decoupling is a core microservices principle — services evolve independently, communicate through events, and the system grows by adding new subscribers.

## Related Concepts
- [SQS](06-SQS.md) — SQS is the most common SNS subscriber; SNS+SQS provides reliable fan-out
- [Lambda](04-Lambda.md) — Directly subscribable to SNS topics for event-driven processing
- [Kinesis](08-Kinesis.md) — Alternative for ordered, replayable event streams rather than fan-out

---

## Mental Model
A radio station (SNS topic) broadcasts music. Thousands of listeners (subscribers) tune in — each with their own radio (SQS, Lambda, email, SMS). When the station plays a song (publishes a message), every listener receives it simultaneously. If a listener only wants jazz (filter policy), a smart radio only plays when jazz is on, ignoring rock songs.
