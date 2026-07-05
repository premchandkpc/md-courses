# 06-SSE

Server-Sent Events (SSE) is a standard that allows a server to push data to a client over a single HTTP connection. Unlike WebSocket, SSE is one-directional — server to client only — and uses standard HTTP.

## Overview

SSE is built on plain HTTP. The client opens a connection to the server using the `EventSource` API in JavaScript. The server sends a stream of text events with a specific format (`data:`, `event:`, `id:` fields). The connection auto-reconnects if dropped, using the last event ID to resume where it left off.

## Key Characteristics

- **One-Directional**: Server pushes events to the client. The client cannot send data over the SSE connection (use regular HTTP requests for client-to-server communication).
- **Standard HTTP**: SSE works with existing HTTP infrastructure — proxies, load balancers, firewalls — without special configuration. No upgrade handshake required.
- **Auto-Reconnect**: The browser's EventSource API automatically reconnects after a dropped connection. The server can send a last-event-ID to let the client resume from where it disconnected.
- **Text-Only**: SSE payloads are UTF-8 text (though you can embed JSON in the data field). Binary data is not supported natively.
- **Simple Event Format**: Events follow a simple text format with optional `event`, `data`, `id`, and `retry` fields. This makes SSE trivially debuggable with curl or browser dev tools.

## Why It Matters

SSE is the simplest real-time push mechanism. It's ideal for live feeds where the server is the sole data source: notification streams, stock tickers, log tails, deployment status dashboards. Because it uses standard HTTP, it works through most proxies and doesn't require a WebSocket library. The tradeoff is limited browser support for concurrent connections (browsers limit 6-8 concurrent SSE connections) and lack of binary support.

## Related Concepts

- [05-WebSockets](05-WebSockets.md) — the bidirectional, binary-capable alternative
- [02-REST](02-REST.md) — SSE can be layered on REST endpoints for push notifications
- [12-Choosing-Communication](12-Choosing-Communication.md) — when to pick SSE over WebSocket

---

## Mental Model

SSE is like a radio broadcast. The station (server) transmits continuously, and anyone with a receiver (client) can tune in. The listener can't talk back to the station through the radio, but if the signal drops, a good car radio (EventSource API) will auto-tune back to the frequency. It's one-way, simple, and reliable.
