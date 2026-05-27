# 📡 HTTP & Application Protocols — Complete Deep Dive

## 📋 Table of Contents
- [HTTP/1.1](#http11)
- [HTTP/2](#http2)
- [HTTP/3 & QUIC](#http3--quic)
- [gRPC](#grpc)
- [WebSocket](#websocket)
- [SSE — Server-Sent Events](#sse--server-sent-events)
- [Simplest Mental Model](#simplest-mental-model)

---

## HTTP/1.1

### Persistent Connections (Keep-Alive)

```text
HTTP/1.0 (default: close)            HTTP/1.1 (default: keep-alive)

+-------+         +-------+          +-------+         +-------+
|Client |         |Server |          |Client |         |Server |
+---+---+         +---+---+          +---+---+         +---+---+
    |                 |                  |                 |
    |--- GET /a ----> |                  |--- GET /a ----> |
    |<--- response ---|                  |<--- response ---|
    |                 |                  |--- GET /b ----> |
    |--- GET /b ----> |   (NEW TCP)     |<--- response ---|
    |<--- response ---|                  |--- GET /c ----> |
    |                 |                  |<--- response ---|
    |--- GET /c ----> |                  |                 |
    |<--- response ---|                  |  (single TCP)   |
```

- **Connection: keep-alive** saves TCP handshake + slow start per request.
- **Hop-by-hop**: Connection, Keep-Alive, Proxy-Authorize, TE, Transfer-Encoding, Upgrade — stripped by proxies.

### Pipelining

```text
Non-pipelined: [req1][recv1][req2][recv2]
Pipelined:     [req1][req2][req3][recv1][recv2][recv3]
```
HOL blocking problem. Rarely used — browsers use 6 parallel connections instead.

### Chunked Transfer Encoding

```text
Transfer-Encoding: chunked
  5\r\nHello\r\n  7\r\n World!\r\n  0\r\n\r\n
[Trailer: X-Time: 42ms]
```
Streams response without Content-Length. Optional trailers after zero-length chunk.

### HTTP Caching

```text
Client                  Proxy Cache              Origin Server
  |                         |                       |
  |--- GET /img.png ------->|                       |
  |                         |--- (miss) ----------->|
  |                         |<-- 200 + Cache-Control|
  |                         |  + ETag: "abc123"     |
  |<-- 200 (from cache) ----|                       |
  |                         |                       |
  |--- GET /img.png ------->|                       |
  |  If-None-Match: "abc123"|--- conditional ----->|
  |                         |<-- 304 Not Modified   |
  |<-- 200 (from cache) ----|                       |
```

- **Cache-Control**: `max-age`, `s-maxage`, `public`, `private`, `no-cache`, `no-store`, `must-revalidate`, `immutable`
- **ETag**: Strong (byte-exact) or weak (`W/"abc"`). **Last-Modified**: 1s resolution.
- **Conditional Requests**: `If-None-Match` → 304, `If-Modified-Since` → 304.
- **Vary**: `Vary: Accept-Encoding` extends cache key by request headers.

---

## HTTP/2

### Binary Framing

```text
HTTP/1.1 (text):                          HTTP/2 (binary):
GET /index.html HTTP/1.1\r\n              +----------------+
Host: example.com\r\n                     | Frame (9 bytes)|
\r\n                                       | Type: HEADERS  |
                                          | Stream ID: 1   |
                                          +----------------+
```

**Frame types**: DATA(0x0), HEADERS(0x1), PRIORITY(0x2), RST_STREAM(0x3), SETTINGS(0x4), PUSH_PROMISE(0x5), PING(0x6), GOAWAY(0x7), WINDOW_UPDATE(0x8), CONTINUATION(0x9)

### Multiplexing

```text
HTTP/1.1 (6 parallel TCP):       HTTP/2 (1 TCP):
+--[TCP 1]--+ Stream A           +--------+
| Stream A  |                    | A | B  |
+--[TCP 2]--+ Stream B           | C | A  |
| Stream B  |                    | B | D  |
+--[TCP 3]--+ Stream C           +--------+
| Stream C  |
+-----------+
```

### Stream Dependencies

```text
       [root]
      /   |   \
  [A:16] [B:8] [C:4]
    |             |
  [D:12]        [E:4]
```

- **Weight**: 1-256. Relative bandwidth among siblings. Client reprioritizes via PRIORITY frame.

### Flow Control

- Initial window: 65535 bytes (configurable via SETTINGS_INITIAL_WINDOW_SIZE).
- Per-stream + per-connection credit. WINDOW_UPDATE increments. Hop-by-hop (not end-to-end).

### HPACK — Header Compression

```text
Raw headers (~200B) → Static Table (61 entries) + Dynamic Table + Huffman (~20B)
Dynamic table size negotiated via SETTINGS_HEADER_TABLE_SIZE (default 4096). LRU eviction.
```

### Server Push (PUSH_PROMISE)

```text
Client --- GET /index.html --------> Server
<---- PUSH_PROMISE (id=2) --------- "will push /style.css"
<---- HEADERS+DATA (stream 1) ----- response
<---- HEADERS+DATA (stream 2) ----- pushed style.css
```
Client can RST_STREAM unwanted pushes. Chrome disables push by default.

### HOL Blocking

```text
HTTP/1.1: request-level blocking in single connection.
HTTP/2: TCP-level — lost TCP segment blocks ALL streams.
QUIC: lost packet blocks only its stream.
```

---

## HTTP/3 & QUIC

### QUIC Transport

```text
Long Header (handshake):          Short Header (data):
+----------+----------+----+     +----------+--------+---------+
|Long Hdr  |Version   |CID |     |Short Hdr |  CID   | Pkt#    |
|          |(4B)      |8-18B    |(1B)      |        | + frames|
+----------+----------+----+     +----------+--------+---------+
```

- **Packet Types**: Initial, 0-RTT, Handshake, Retry (long), 1-RTT (short).
- **Connection ID**: Enables connection migration (survives IP:port changes).
- **Stream ID**: client/server-initiated bits + bidirectional/unidirectional bits.
- **0-RTT**: Send data immediately with cached TLS credentials. Idempotent-only safe.

### QPACK

Separate encoder/decoder unidirectional streams for dynamic table (unlike HPACK — QUIC streams are out-of-order). `SETTINGS_QPACK_MAX_FIELD_SECTION_SIZE`.

### QUIC Loss Recovery

- **RACK-based**: Track most recent delivery, declare loss when later packet ACKed + time passed.
- **NACK-based**: ACK frames report gap ranges. Monotonic packet numbers eliminate RTO ambiguity.

---

## gRPC

### HTTP/2 Framing

```text
HEADERS (END_HEADERS) :method=POST :path=/pkg.Svc/Method
  content-type=application/grpc te=trailers grpc-timeout=30S
DATA (END_STREAM) [1B comp flag][4B msg length][protobuf]
HEADERS (END_STREAM+END_HEADERS) grpc-status=0 grpc-message=OK
```

### Protocol Buffers

```protobuf
message Person {
  string name = 1;    // tag=1, wire type=2 (length-delimited)
  int32 age = 2;      // tag=2, wire type=0 (varint)
  repeated string phones = 3;  // packed in proto3
}
// Encoding: (tag << 3 | wire_type), varint(len), data
```

- **Varint**: MSB continuation bit. Small ints use fewer bytes.
- **Proto3 vs Proto2**: No `required`/`optional`. Defaults (0/""). `repeated` packed by default. `oneof`. `map<k,v>`.
- **Wire types**: 0(varint), 1(64-bit), 2(length-delimited), 5(32-bit).

### Patterns & Channels

- **Unary**, **Server streaming**, **Client streaming**, **Bidirectional streaming**.
- **Channel** → resolves name → **subchannels** → health monitoring.
- **LB policies**: `pick_first`, `round_robin`, `grpclb`, `weighted_target`, `ring_hash`.
- **xDS**: Envoy control plane + LRS (Load Reporting Service).

---

## WebSocket

### Upgrade Handshake

```http
GET /chat HTTP/1.1
Upgrade: websocket | Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ== | Sec-WebSocket-Version: 13
→ 101 Switching Protocols | Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

### Frame Structure

```text
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|F|R|R|R| opcode|M| Payload len |  Extended payload len (16/64) |
|I|S|S|S| (4)  |A| (7)         |  if 126/127                    |
|N|V|V|V|      |S|             |                                |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|               Masking-Key (4 bytes, if MASK=1)                |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

- **Opcode**: 0x0(cont), 0x1(text), 0x2(binary), 0x8(close), 0x9(ping), 0xA(pong).
- **Masking**: Client→Server MUST be masked (4-byte XOR). Server→Client MUST NOT.
- **Close**: 2-byte code + reason. 1000(normal), 1001(going away), 1002(protocol error).
- **Extensions**: `permessage-deflate` — compress payload per-message (RFC 7692).

---

## SSE — Server-Sent Events

```text
Content-Type: text/event-stream | Cache-Control: no-cache

data: {"event": "update", "id": 42}

event: notification
data: {"type": "alert", "message": "Maintenance in 5 min"}
id: 1000
retry: 3000
```

- **Fields**: `data`, `event`, `id`, `retry`. Comments start with `:`.
- **Reconnection**: Browser auto-reconnects with `Last-Event-ID`.
- **EventSource API**: `new EventSource('/events')`, `.onmessage`, `.addEventListener()`.
- **Limitations**: Text-only, unidirectional, ~6 connections/domain limit.

---

## Simplest Mental Model

> **HTTP protocols are conversations with a library's document delivery service.**
>
> - **HTTP/1.1** = One-at-a-time request/response keeping the phone line open. Can pipeline (send multiple), but one slow response blocks everything.
> - **HTTP/2** = A single phone line with numbered conversations (streams) — interleaved. Library anticipates your needs (server push). Headers compressed like shorthand (HPACK).
> - **HTTP/3 (QUIC)** = Radio instead of phone line — dropped packet doesn't block other conversations. Reconnects instantly (0-RTT). Survives moving rooms (connection migration).
> - **gRPC** = Structured forms (protobuf) over HTTP/2. Supports ongoing dialogues — send/stream many small messages.
> - **WebSocket** = 2-way walkie-talkie. Both sides speak anytime.
> - **SSE** = Ticker tape — server pushes updates unilaterally. Can't send messages back.

---

## Code Examples

```python
# Example implementation
# [Add language-specific code demonstrating core concept]
pass
```

---

## Common Failure Modes

**Problem**: [Key issue in production]

**Root cause**: [Why it happens]

**Solution**: [How to fix]

---

## Interview Questions

### Q1: [Core concept question]

**Answer**: [Detailed explanation with trade-offs]

### Q2: [Design/architecture question]

**Answer**: [Best practices and reasoning]
