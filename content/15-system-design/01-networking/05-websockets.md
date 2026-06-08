---
title: WebSockets & Real-Time Communication Deep Dive - L5 Networking
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# WebSockets & Real-Time Communication Deep Dive - L5 Networking

> **[🎨 View Interactive Diagram](websockets-architecture.html)** | [← Back to Index](../../systems-index.html)

*"How does server push data to client without client requesting? How handle 1M concurrent connections?"*

---

## 1. Problem Statement

**Core Question:** HTTP: client initiates. How enable server-initiated messages in real-time?

Challenge: HTTP request-response model (client waits for response)
Need: bidirectional, low-latency, connection-based

---

## 2. Real World Analogy

**Conversation vs Email:**

HTTP (email):
- Client: sends message
- Server: receives, responds
- Sequential, latency-dependent

WebSocket (conversation):
- Both: send anytime (bidirectional)
- Real-time (instant)
- Connection-based (persistent)

---

## 3. Why Problem Exists

### HTTP Limitations

```
Polling: client repeatedly asks "anything new?"
  Waste: bandwidth (mostly "no")
  Latency: update lag (poll interval)

Long polling: client waits, server responds when data ready
  Better: reduces polling
  Bad: still request-response model
  Overhead: connection per message

Need: true bidirectional (WebSocket)
```

---

## 4. Naive Approach

**"Use HTTP polling"**

Problems:
- High latency (poll interval)
- Bandwidth waste (frequent polls)
- Scalability (many connections)

---

## 5. Why Naive Fails

### Polling Overhead

```
Poll interval: 1 second
1M users: 1M requests/sec
Bandwidth: 1M × 1KB header = ~1GB/sec (header waste!)

WebSocket:
  1M users: 1 connection each (persistent)
  Messages sent: only when needed
  Bandwidth: similar content, but no polling overhead
```

---

## 6. Evolution / Progression

### Stage 1: HTTP Polling
- Inefficient, high latency

### Stage 2: Long Polling
- Better latency, still wasteful

### Stage 3: WebSocket (RFC 6455)
- Bidirectional, persistent
- Low overhead (2 bytes per message)
- Multiplexing possible

### Stage 4: Production WebSockets
- Connection pooling
- Failover & reconnect
- Message queuing
- Horizontal scaling

---

## 7. Production Architecture

```
[Client] ←→ [WebSocket Connection (persistent)]
              ↓
            [Proxy/Load Balancer]
              ↓
            [Application Server]
              ├─ Connection handler (per connection)
              ├─ Message queue (per user)
              └─ Redis (for state, broadcast)
```

---

## 8. Components

### WebSocket Upgrade

```
HTTP GET with Upgrade header
  GET / HTTP/1.1
  Upgrade: websocket
  Connection: Upgrade
  Sec-WebSocket-Key: xyz123...
  
Server responds:
  HTTP/1.1 101 Switching Protocols
  Upgrade: websocket
  
Result: TCP connection upgraded to WebSocket
```

### Frame Structure

```
Header: 2 bytes minimum (opcode + length)
Payload: variable
Total: more efficient than HTTP headers (6+ KB)

Message size:
  HTTP: 6KB header + 1KB data = 7KB
  WebSocket: 2 byte header + 1KB data = 1.002KB
  Efficiency: 7x better
```

---

## 9. Internal Working

### WebSocket Message Flow

```
Client connects: 1 HTTP request → 101 Upgrade → persistent TCP

Server broadcasts message:
  Server sends frame (2 bytes header + payload)
  Client receives instantly (not polling)

Client sends message:
  Client sends frame
  Server receives instantly

Bidirectional: both directions possible anytime
```

---

## 10. Request Lifecycle

```
t=0ms:    User opens chat app
t=0-50ms: Browser loads page
t=50ms:   JavaScript: WebSocket.connect()
t=50-100ms: TCP handshake
t=100-150ms: WebSocket upgrade
t=150ms:  Connection established (persistent)

User sends message:
t=150-151ms: Client sends WebSocket frame
t=151-161ms: Server receives, processes
t=161-162ms: Server broadcasts to other clients
t=162-172ms: Other clients receive (real-time!)

Latency: ~20ms (vs HTTP polling: 500-1000ms)
```

---

## 11. Data Flow

### Broadcast Scenario

```
Sender: sends message on WebSocket
Server: receives, stores, broadcasts

Server publishes to Redis:
  Channel: "chat:room123"
  Message: {"user": "alice", "text": "hi"}

All connected clients (subscribed to channel):
  Receive message instantly
  Update UI

Horizontal scaling:
  Multiple servers subscribe to same Redis channel
  Any server: can broadcast to its clients
  All clients: receive message (across servers)
```

---

## 12. Key Strategy

### 1. Connection Management

```
Track: active connections per server
Limit: per-user (prevent spam)
Timeout: idle connections (close after 30min)
Heartbeat: ping/pong (detect dead connections)
```

### 2. Scalability

```
Single server: handle ~10K concurrent WebSockets
Multiple servers: use Redis pubsub for broadcasts
Message queue: for async processing
Connection pooling: across servers
```

### 3. Reliability

```
Reconnect: on disconnect (exponential backoff)
Message acking: client confirms receipt
Fallback: HTTP SSE if WebSocket fails
Graceful upgrade: HTTP → WebSocket

---

## 13. Failure Scenarios

### Scenario 1: Server Restart

```
10K users connected
Server restarts

Clients: connection lost
Reconnect: exponential backoff
5s, 10s, 20s...

Users: notice brief disconnect
Message loss: if messages sent during restart
Solution: persistent queue (Redis)
```

### Scenario 2: Network Partition

```
Server unreachable (network cut)
Client: detects timeout (60s default)
Reconnect: resumes connection
Messages: lost during partition
Solution: buffer on client, resync
```

---

## 14. Bottlenecks Table

| Issue | Impact | Fix |
|---|---|---|
| No heartbeat | Dead connection undetected | Ping/pong |
| Single server | 10K connection limit | Horizontal scale |
| No message queue | Message loss | Redis queue |
| No backpressure | Memory overflow | Rate limit |
| No reconnect | User data loss | Auto-reconnect |

---

## 15. Monitoring

### Key Metrics

```
✓ Active connections (total, per server)
✓ Connection rate (new/sec)
✓ Disconnect rate (normal vs errors)
✓ Message latency (server → client time)
✓ Broadcast latency (sent → received)
```

---

## 16. Optimizations

### 1. Message Compression

```
Per-message compression:
  Before: 1KB JSON
  After: 200 bytes (80% reduction)
  Cost: CPU (small)
  Benefit: bandwidth (large)
```

### 2. Binary Frames

```
Text: JSON (human-readable, larger)
Binary: MessagePack, Protobuf (compact, faster)

Tradeoff: readability vs size/speed
```

---

## 17. Security

### 1. Origin Validation

```
Verify: WebSocket request from valid origin
Prevent: CSRF attacks
Check: Origin header matches expected
```

### 2. Rate Limiting

```
Per-connection: max 100 messages/sec
Per-user: max 1000 messages/sec
Prevent: spam, DoS
```

---

## 18. Tradeoffs Table

| Feature | Latency | Bandwidth | Complexity |
|---|---|---|---|
| HTTP polling | High | High | Low |
| Long polling | Medium | Medium | Medium |
| WebSocket | Low | Low | High |

---

## 19. Alternatives

### Server-Sent Events (SSE)

```
Server-to-client only (not bidirectional)
HTTP-based (simpler infrastructure)
Auto-reconnect (built-in)

Use: when server → client sufficient
Not: when client → server needed
```

---

## 20. When NOT to Use

### Don't Use WebSocket When:

1. **Simple request-response**
   - HTTP sufficient
   - Simpler

2. **High message latency acceptable**
   - HTTP polling fine

---

## 21. Interview Questions

1. **Design real-time chat (1M users)**
   - WebSocket strategy?
   - Scalability?
   - Message delivery guarantee?

2. **WebSocket connection drops**
   - Detect?
   - Reconnect?
   - Message recovery?

3. **Compare WebSocket vs polling vs SSE**
   - Use cases?

---

## 22. Common Mistakes

1. **No heartbeat**
   - Dead connections undetected
   - Add: ping/pong

2. **Single server**
   - 10K limit
   - Horizontal scale

3. **No message persistence**
   - Lose messages on crash
   - Add: Redis queue

4. **No backpressure**
   - Memory overflow
   - Add: rate limiting

---

## 23. Debugging Guide

### Step 1: Check Connection

```
Browser DevTools → Network → WS
Shows: WebSocket connections
Status: 101 Switching Protocols (OK)
```

### Step 2: Check Messages

```
Frame tab: shows frames sent/received
Timing: latency per message
Errors: connection issues
```

---

## 24. Code Examples

### Go: WebSocket Server

```go
func handleWebSocket(w http.ResponseWriter, r *http.Request) {
    conn, _ := upgrader.Upgrade(w, r, nil)
    defer conn.Close()
    
    conn.SetReadDeadline(time.Now().Add(60 * time.Second))
    conn.SetPongHandler(func(string) error {
        conn.SetReadDeadline(time.Now().Add(60 * time.Second))
        return nil
    })
    
    // Heartbeat
    ticker := time.NewTicker(30 * time.Second)
    go func() {
        for range ticker.C {
            conn.WriteMessage(websocket.PingMessage, nil)
        }
    }()
    
    // Read messages
    for {
        _, data, err := conn.ReadMessage()
        if err != nil {
            break
        }
        // Broadcast to others
        broadcast <- data
    }
}
```

---

## 25. Visual Diagrams

### WebSocket vs HTTP Polling

```
HTTP Polling:        [Request] → [Wait] → [Response]
                     [Request] → [Wait] → [Response]
                     
WebSocket:           [Upgrade] ← persistent connection →
                              (instant bidirectional)
```

---

## 26. Simulation Ideas

1. **Connection Scalability**
   - Vary: connections per server
   - Show: memory, latency

---

## 27. Case Studies

### Slack: WebSocket for chat
Result: <100ms message latency

---

## 28. Related Topics

- **Real-Time Protocols**
- **Message Broadcasting**

---

## 29. Advanced Topics

### WebSocket Subprotocols

```
Can negotiate subprotocol (MQTT, STOMP, etc)
Standardize message format
```

---

## 30. Production Checklist

- [ ] Heartbeat (ping/pong every 30s)
- [ ] Reconnect logic (exponential backoff)
- [ ] Message persistence (Redis queue)
- [ ] Rate limiting (per connection, per user)
- [ ] Origin validation (CORS)
- [ ] Monitoring (connections, latency)
- [ ] Load balancing (sticky sessions)
- [ ] Horizontal scaling (Redis pubsub)
- [ ] Graceful shutdown (close connections)
- [ ] Fallback (SSE or polling)

---

*Last Updated: 2026-05-28*
