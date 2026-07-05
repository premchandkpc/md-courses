# 05-WebSockets

WebSocket is a protocol providing full-duplex communication channels over a single, long-lived TCP connection. It enables real-time, bidirectional data flow between client and server.

## Overview

Unlike HTTP request-response, WebSocket begins with an HTTP upgrade handshake, then maintains an open connection through which both parties can send messages at any time. This makes it ideal for applications requiring low-latency, real-time updates — chat, live dashboards, collaborative editing, gaming, and financial tickers.

## Key Characteristics

- **Full-Duplex**: Both client and server can send messages independently over the same connection. No polling or long-polling needed.
- **Persistent Connection**: The TCP connection stays open for the duration of the session. This reduces overhead compared to establishing a new HTTP connection for each message.
- **Message Framing**: WebSocket uses a lightweight framing protocol over TCP. Messages can be text (UTF-8) or binary. There is no built-in routing or pub/sub — the application layer must handle this.
- **Heartbeat/Ping-Pong**: To detect dead connections, WebSocket has built-in ping/pong frames. The server can periodically ping the client; if no pong is received, the connection is considered dead.
- **Reconnection Strategies**: WebSocket does not auto-reconnect. The client must implement reconnection logic with exponential backoff to handle network interruptions gracefully.

## Why It Matters

WebSocket is the go-to choice when the server needs to push data to the client in real-time. In microservices, WebSocket connections are typically terminated at a gateway or BFF, which then fans out events from backend services. The main challenge is scaling WebSocket connections horizontally — sticky sessions or a shared pub/sub layer (e.g., Redis PubSub) are needed to route messages to the right server instance.

## Related Concepts

- [06-SSE](06-SSE.md) — a simpler alternative when only server-to-client data is needed
- [11-Redis-PubSub](11-Redis-PubSub.md) — often used to fan out messages across WebSocket server instances
- [02-REST](02-REST.md) — the stateless alternative for non-real-time use cases

---

## Mental Model

A WebSocket is like a garden hose with water flowing both ways. You can spray water (send data) and a friend can spray back through the same hose. The hose stays connected as long as you're both in the garden. If someone kinks it (connection drops), you have to reconnect it before you can spray again.
