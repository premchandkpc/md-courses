# 09-RabbitMQ

RabbitMQ is an open-source message broker that implements the AMQP 0-9-1 protocol. It is known for its flexible routing capabilities, mature ecosystem, and operational reliability.

## Overview

RabbitMQ routes messages from producers to queues using exchanges. An exchange receives messages and routes them to one or more queues based on routing rules (binding keys). Consumers then pull messages from queues. This exchange-queue binding pattern gives RabbitMQ extremely granular control over message routing, making it ideal for complex routing scenarios.

## Key Characteristics

- **Exchange Types**: Four types of exchanges — Direct (exact routing key match), Topic (pattern-matched routing keys, e.g., `orders.*`), Fanout (broadcast to all bound queues), and Headers (route based on header attributes). This covers virtually any routing pattern.
- **Queues and Bindings**: Queues hold messages until consumed. Bindings connect exchanges to queues with routing rules. A single exchange can route to multiple queues, and a queue can be bound to multiple exchanges.
- **ACK/NACK**: Consumers explicitly acknowledge (ACK) or negatively acknowledge (NACK) messages. This gives fine-grained control over message processing. Unacknowledged messages are re-delivered, ensuring at-least-once delivery.
- **Dead Letter Exchanges (DLX)**: Messages that cannot be processed (rejected, expired, queue-full) are routed to a dead letter exchange. DLQs are critical for handling poison messages and debugging message processing failures.
- **Publisher Confirms**: Publishers can request confirmation that their message has been received and persisted by the broker. This enables reliable publishing without sacrificing throughput.

## Why It Matters

RabbitMQ excels in scenarios requiring complex routing logic. Its exchange types and binding system let you implement sophisticated patterns like work queues, pub/sub, routing by severity, and headers-based routing — all out of the box. It's a better fit than Kafka for systems where routing flexibility matters more than throughput (typically < 50K msg/s) and where you want messages to be removed after consumption.

## Related Concepts

- [07-Message-Brokers](07-Message-Brokers.md) — overview of broker patterns
- [08-Kafka](08-Kafka.md) — Kafka vs RabbitMQ: throughput vs routing flexibility
- [10-NATS](10-NATS.md) — lighter alternative for simple pub/sub
- [01-Synchronous-vs-Asynchronous](01-Synchronous-vs-Asynchronous.md) — async messaging with RabbitMQ

---

## Mental Model

RabbitMQ is like a postal sorting facility with intelligent sorting machines (exchanges). Incoming mail goes to a sorting machine. The machine can sort by zip code (direct exchange), by region with wildcards (topic exchange), or send everything to all bins (fanout exchange). Each bin (queue) holds mail for a specific recipient. If a parcel is undeliverable, it goes to the dead letter office (DLX).
