# TCP/IP Protocol Stack Deep Dive - L5 Networking

> **[🎨 View Interactive Diagram](tcp-ip-architecture.html)** | [🎨 TCP Lifecycle Simulator](../../../html/09-tcp-connection-lifecycle-viz.html) | [← Back to Index](../../systems-index.html)

*"Why does establishing a connection take 100ms? What happens in that three-way handshake?"*

---

## 1. Problem Statement

**Core Question:** How does data reliably travel between two computers across the internet?

Key challenges:
- Network unreliable (packets lost, reordered)
- Packets limited in size (MTU: 1500 bytes)
- Routes change dynamically
- Congestion varies over time

TCP/IP: abstraction layer hiding these complexities

---

## 2. Real World Analogy

**Mail Delivery Scenario:**

No TCP (raw IP):
- Sender: write letter, throw out window
- Recipient: find letters scattered, sometimes lost
- No guarantee: all letters arrive, in order, without damage

TCP:
- Sender: hand letter to mail service (guaranteed delivery)
- Service: track, resend lost, reorder, deliver in order
- Recipient: guaranteed: all letters arrive, in order, intact

Cost: overhead (tracking, resending, ordering)
Benefit: reliability

---

## 3. Why Problem Exists

### Network Unreliability

```
IP (Internet Protocol): best-effort delivery
  - Packet may be lost (router overflow, corruption)
  - Packet may arrive out of order
  - Packet may be delayed

Application needs: reliability

Solution: TCP (Transmission Control Protocol)
  - Detect lost packets (via sequence numbers)
  - Retransmit lost packets
  - Reorder out-of-order packets
  - Acknowledge receipt
```

### Packet Size Limits

```
MTU (Maximum Transmission Unit): 1500 bytes
Application sends: 10KB file

TCP: breaks into ~7 packets (1500 bytes each)
Network: delivers packets (may be lost individually)
TCP: reorders, reassembles
Application: receives 10KB intact

Abstraction: application doesn't worry about packet boundaries
```

### Flow Control

```
Sender rate: 100 Mbps
Receiver buffer: 64KB

Mismatch:
  Sender sends: 100 Mbps
  Receiver can't keep up: buffers overflow
  Packets dropped

TCP: flow control
  Receiver: "I can accept 64KB"
  Sender: slows down (doesn't exceed 64KB)
```

---

## 4. Naive Approach

**"Use IP directly, application handles reliability"**

Problems:
- Application must track packets
- Detect loss, implement retransmit
- Handle out-of-order, reordering
- Complex, error-prone

---

## 5. Why Naive Fails

### Application Complexity

```
Application must:
  - Assign packet numbers
  - Track ack/nack
  - Implement retry logic
  - Handle duplicate packets
  - Detect timeouts
  - Reorder packets

Result: every application reinvents TCP
  Code: thousands of lines of complex logic
  Bugs: race conditions, edge cases
  Security: vulnerabilities
```

### Performance Degradation

```
Naïve retry: exponential backoff (1s, 2s, 4s...)
TCP: smarter (adaptive based on RTT)

Result: TCP faster on lossy networks
```

---

## 6. Evolution / Progression

### Stage 1: Raw IP
- Unreliable, connectionless
- No flow control
- Application handles everything

### Stage 2: TCP Protocol
- Connection-oriented (handshake)
- Reliability (acks, retransmit)
- Flow control (window mechanism)
- Congestion control (throttle on loss)

### Stage 3: TCP Optimizations
- Selective acknowledgment (SACK)
- Fast retransmit (don't wait for timeout)
- Explicit congestion notification (ECN)

### Stage 4: Modern TCP (CUBIC, BBR)
- Better congestion control
- Reduced latency variance
- Improved throughput on high-latency links

---

## 7. Production Architecture

```
[Application]
    │ (data: "hello")
    ▼
[TCP Layer]
    ├─ Add TCP header (source port, dest port, seq#, ack#)
    ├─ Segmentation: split into MSS-sized chunks (1460 bytes)
    ├─ Add sequence numbers (for reliability)
    └─ Send to IP layer
    
[IP Layer]
    ├─ Add IP header (source IP, dest IP, TTL)
    ├─ Route packet to destination
    └─ Send to Link layer
    
[Link Layer (Ethernet)]
    ├─ Add MAC header (source MAC, dest MAC)
    ├─ Send on wire (1500 byte frame)
    └─ Deliver to next hop (router or destination)
    
[Network (Physical)]
    ├─ Electrical signals on wire
    └─ Travel to destination (or routers)

[Destination: reverse process]
    ├─ Ethernet: extract IP packet
    ├─ IP: extract TCP segment
    ├─ TCP: reassemble, deliver to application
    └─ Application: receives complete message
```

---

## 8. Components

### TCP Three-Way Handshake (SYN, SYN-ACK, ACK)

```
Client → Server: SYN (seq=100)
  "I want to connect, my seq starts at 100"
  
Server → Client: SYN-ACK (seq=200, ack=101)
  "OK, my seq starts at 200, I ack your 100"
  
Client → Server: ACK (seq=101, ack=201)
  "I ack your 200, connection established"

Result: both know starting sequence numbers, connection open
Cost: 1 RTT (round-trip time, ~100ms globally)
```

### Window-Based Flow Control

```
TCP Window: how much data can be in-flight

Receiver: "I have 64KB buffer"
  Sends: window=64KB
  
Sender: can send up to 64KB without ack
  Sends: 64KB
  
Receiver: processes 32KB, can now accept 32KB more
  Sends: window=32KB (now)
  
Sender: slows down (only 32KB more allowed)
  Sends: 32KB
  
Receiver: finishes, can accept 64KB again
  Sends: window=64KB
  
Sender: accelerates (64KB available)

Result: flow control prevents buffer overflow
```

### Congestion Control (AIMD: Additive Increase, Multiplicative Decrease)

```
Congestion window (cwnd): how much to send

Normal: cwnd grows (additive increase)
  cwnd = cwnd + 1 per RTT
  Throughput slowly increases

Loss detected: cwnd shrinks (multiplicative decrease)
  cwnd = cwnd / 2
  Back off quickly

Result: adapt to network capacity
  High bandwidth: cwnd grows large
  Congested: cwnd shrinks, reduces load
```

---

## 9. Internal Working

### TCP Sequence Number Example

```
Client sends: "HELLO" (5 bytes)
  Seq: 100, Len: 5
  Bytes: 100-104

Server acks: ack=105 (next expected seq)
  "I got bytes up to 104"

Client sends: "WORLD" (5 bytes)
  Seq: 105, Len: 5
  Bytes: 105-109

Server acks: ack=110
  "I got bytes up to 109"

If loss:
  Client sends: "HELLO" (seq=100)
  Loss (dropped)
  Client doesn't get ack
  Timeout (usually ~1 second)
  Retransmit: "HELLO" (seq=100) again
  Server acks: ack=105
```

### Connection States

```
Client side:
  CLOSED → SYN_SENT (sends SYN) → ESTABLISHED (got SYN-ACK) → CLOSE_WAIT → CLOSED

Server side:
  LISTEN → SYN_RECEIVED (got SYN) → ESTABLISHED (sent SYN-ACK) → CLOSE_WAIT → CLOSED

Normal flow:
  Client: SYN_SENT → ESTABLISHED
  Server: LISTEN → SYN_RECEIVED → ESTABLISHED
  (data transfer)
  Client: close() → FIN_WAIT_1 → FIN_WAIT_2 → CLOSED
  Server: close() → LAST_ACK → CLOSED
```

---

## 10. Request Lifecycle

```
t=0ms:      Client application: socket.connect(server_ip:8080)
t=0-10ms:   Network: SYN travels to server
t=10ms:     Server receives SYN
t=10-20ms:  Network: SYN-ACK travels to client
t=20ms:     Client receives SYN-ACK
t=20-30ms:  Network: ACK travels to server
t=30ms:     Server receives ACK, connection established

Actual latency from client perspective:
  t=0 to t=30ms (3-way handshake)
  Usually ~30-100ms (depending on distance)

After connection:
t=30ms:     Client: send("GET /api HTTP/1.1")
t=30-40ms:  Network: request travels
t=40ms:     Server receives request
t=40-100ms: Server: process request (60ms)
t=100-110ms: Network: response travels
t=110ms:    Client receives response

Total: 110ms
```

---

## 11. Data Flow

### Multi-Packet Message

```
Application sends: 10KB message

TCP segments:
  Packet 1: seq=100, data=1460 bytes (100-1459)
  Packet 2: seq=1560, data=1460 bytes (1560-3019)
  Packet 3: seq=3020, data=1460 bytes (3020-4479)
  Packet 4: seq=4480, data=1460 bytes (4480-5939)
  Packet 5: seq=5940, data=1460 bytes (5940-7399)
  Packet 6: seq=7400, data=1460 bytes (7400-8859)
  Packet 7: seq=8860, data=1240 bytes (8860-10099)

Network delivers (possibly out of order):
  Packet 2 arrives first (routed differently)
  Packet 1 arrives (but late)
  Packet 3 arrives
  Packet 4 lost (will retransmit)
  Packet 5 arrives
  ...

TCP reassembles:
  Buffers out-of-order packets
  Acks: "I got up to packet 1"
  Waits for packet 4
  Retransmit triggered
  Packet 4 arrives
  Delivers all 10KB to application (in order)
```

---

## 12. Key Strategy

### 1. Tune TCP Parameters

```
TCP_NODELAY: disable Nagle (batch small packets)
  For: low-latency apps (trading, games)
  Default: enabled (batch for efficiency)

TCP_WINDOW_CLAMP: limit window size
  For: prevent large buffers
  Trade: throughput vs memory

SO_SNDBUF, SO_RCVBUF: socket buffer sizes
  Default: kernel tunes automatically
  Manual: may help for specific workloads
```

### 2. Connection Pooling

```
Cost per connection: TCP handshake (100ms)
Cost per request (without pooling):
  - Handshake: 100ms
  - Request: 10ms
  - Total: 110ms

Cost per request (with pooling):
  - Reuse connection: 0ms (already open)
  - Request: 10ms
  - Total: 10ms

Benefit: 10x faster (handshake amortized)
```

### 3. Keepalive & Connection Management

```
Long-lived connections:
  Routers timeout idle connections (15-30 minutes default)
  
Solution: TCP keepalive
  Send: "ping" every 30 seconds
  Keeps: connection alive (no idle timeout)
  Cost: minimal (one packet every 30s)
```

---

## 13. Failure Scenarios

### Scenario 1: Packet Loss on Slow Network

```
RTT: 1000ms (satellite link)
Packet lost

Timeout mechanism:
  RTO (Retransmission Timeout): estimated from RTT
  Default: 2 × RTT = 2000ms (adaptive)

Timeline:
  t=0ms: send packet
  t=1000ms: no ack received
  t=2000ms: timeout, retransmit
  t=3000ms: receive ack
  t=3000ms: got ack for retransmitted packet

Result: works, but slow (2 second delay for loss)
```

### Scenario 2: Half-Open Connection

```
Client crashed (TCP_KEEPALIVE disabled)
Server still thinks connection is open
Sends data to client
No response

Server:
  Waits for ack
  Timeout (2 minutes default, very long)
  Finally closes

Solution: TCP_KEEPALIVE
  Server: sends keepalive probe every 30s
  Client: offline (no response)
  Server: detects dead connection (90s)
  Closes immediately
```

### Scenario 3: Slow Client (Slow Read)

```
Application: slow reading (processes 1KB/sec)
TCP: window shrinks (as application can't consume)
Client: eventually window = 0
Sender: stops sending (backpressure)

Scenario:
  Sender: sends 100KB/sec
  Receiver: reads 1KB/sec
  Receiver buffer: 64KB
  After ~1 second: buffer full
  Window = 0
  Sender: blocked (can't send more)
  
Result: sender backpressured (good, prevents packet loss)
```

---

## 14. Bottlenecks Table

| Bottleneck | Impact | Symptoms | Fix |
|---|---|---|---|
| Slow RTT | Handshake latency | Connection setup slow | Connection pooling |
| Packet loss | Retransmits | High latency variance | Better routing, QoS |
| Congestion | Reduced throughput | High packet loss | Congestion control |
| Buffer overflow | Packet loss | Dropped packets | Flow control, scaling |
| Slow reader | Sender blocked | Sender throughput drops | Speed up reader |

---

## 15. Monitoring

### Key Metrics

```
Connection health:
  ✓ Established connections: current count
  ✓ Connection rate: new connections/sec
  ✓ Connection latency: time to establish (3-way)
  ✓ Time-wait connections: cleanup rate

Packet health:
  ✓ Retransmit rate: % packets retransmitted
  ✓ Packet loss: % lost (should be < 0.1%)
  ✓ Out-of-order packets: detected
  ✓ Duplicate acks: indicates loss

Application impact:
  ✓ Throughput: bytes/sec
  ✓ Latency: P50, P99, P999
  ✓ Error rate: timeouts, resets
```

### Red Flags

- Retransmit rate > 1% (network issues)
- Packet loss detected (congestion or corruption)
- Many TIME_WAIT connections (port exhaustion risk)
- Connection setup time increasing (network latency changing)

---

## 16. Optimizations

### 1. TCP Fast Open (TFO)

```
Standard TCP:
  1. SYN
  2. SYN-ACK
  3. ACK
  4. Data

TCP Fast Open:
  1. SYN (with cookie request)
  2. SYN-ACK (with cookie)
  3. Data (with cookie, on next connection)

Result: skip handshake on repeat connections (0 RTT)
```

### 2. Selective Acknowledgment (SACK)

```
Standard:
  Packet 1, 3, 4 arrive (2 lost)
  Ack: "I got up to packet 1" (inefficient, have 3,4 but can't use)

SACK:
  Packet 1, 3, 4 arrive
  Ack: "Got 1, also got 3-4" (explicit about what arrived)
  Sender: retransmits only 2 (knows 3,4 safe)

Result: fewer retransmits on selective loss
```

### 3. BBR Congestion Control

```
Traditional (CUBIC): optimize for loss detection
  Slow to respond to changes
  High latency variance

BBR: optimize for bottleneck bandwidth and minimum RTT
  Measure: actual network capacity
  Adapt: quickly to changes
  Result: lower latency, higher throughput

Trade: more complex, requires kernel support (Linux 4.9+)
```

---

## 17. Security

### 1. SYN Flood DDoS

```
Attack: send massive SYNs (don't complete handshake)
Server: allocates resources for each SYN
Result: resource exhaustion

Mitigation:
  - SYN cookies (don't allocate until ACK)
  - Rate limiting (reject excess SYNs)
  - Firewall: filter obvious attacks
```

### 2. RST Attacks

```
Attacker: send RST packet (forged source)
Connection: closes unexpectedly
Application: error

Prevention:
  - Sequence number randomization (hard to guess)
  - Window scaling (makes RST harder to craft)
```

---

## 18. Tradeoffs Table

| Feature | Throughput | Latency | Complexity |
|---|---|---|---|
| Nagle (batching) | Higher | Higher (batches) | Low |
| TCP_NODELAY | Lower | Lower | Low |
| Large window | Higher | Same | Low |
| SACK | Higher (selective) | Same | Medium |
| BBR | Higher | Lower | High |

---

## 19. Alternatives

### QUIC (Quick UDP Internet Connections)

```
TCP over UDP:
  - 0-RTT connection (no handshake)
  - Faster loss recovery (selective retransmit)
  - Multiplexing (multiple streams)
  - Better mobile support (connection migration)

Trade: more complex, newer implementations
```

---

## 20. When NOT to Use

### TCP When:

1. **Latency critical, some loss acceptable**
   - Real-time gaming
   - Video streaming
   - Use UDP instead

2. **Multicast/broadcast needed**
   - TCP point-to-point only
   - Use UDP multicast

---

## 21. Interview Questions

1. **Design connection pool (reuse TCP connections)**
   - How many connections?
   - How long idle?
   - Health checks?

2. **High packet loss (2%) on network**
   - Impact on throughput?
   - TCP adapts how?
   - What can you do?

3. **Connection setup slow (200ms)**
   - Likely causes?
   - How diagnose?
   - Solutions?

4. **Compare TCP vs QUIC**
   - Tradeoffs?
   - When use each?

5. **Slow client reading from buffer**
   - What happens?
   - Sender impact?
   - How prevent?

---

## 22. Common Mistakes

1. **Ignoring connection pooling**
   - Create new connection per request
   - Handshake cost: 100ms
   - Request cost: 10ms
   - Total: 110ms (handshake dominates!)

2. **Disabling TCP_NODELAY for latency-critical apps**
   - Nagle: batches small packets
   - Latency: added (wait for batch)
   - Fix: TCP_NODELAY=1

3. **Not tuning TCP buffers**
   - Small buffers: throughput limited
   - Large buffers: memory wasted
   - Tune: for your bandwidth/RTT product

4. **Ignoring packet loss**
   - Assume: no loss
   - Reality: ~0.1% on internet
   - Impact: affects latency, throughput
   - Monitor: retransmit rate

5. **Not handling TIME_WAIT properly**
   - Closed connections: stay in TIME_WAIT (60s)
   - Rapid reconnects: port unavailable
   - Fix: SO_REUSEADDR, tcp_tw_reuse kernel parameter

---

## 23. Debugging Guide

### Step 1: Check Connection State

```
ss -tan (show TCP connections)
Output:
  LISTEN: waiting for connections
  ESTABLISHED: active connection
  TIME_WAIT: closing (normal, cleanup)
  SYN_SENT: connection in progress
  
Issue: many TIME_WAIT?
  Fix: tcp_tw_reuse or wait 60s
```

### Step 2: Monitor Retransmits

```
netstat -i (show interface stats)
Output:
  RX: bytes received
  TX: bytes sent
  Err: errors

ss -i (detailed TCP stats)
Output:
  Retrans: retransmitted segments
  
Issue: high retransmit rate?
  Root cause: packet loss, latency variance
```

### Step 3: Trace Connection

```
tcpdump -i eth0 'tcp port 8080'

Output:
  SYN, SYN-ACK, ACK (handshake)
  DATA transfers
  FIN (close)
  
Identify:
  Handshake latency (time between SYN and SYN-ACK)
  Packet loss (missing acks, retransmits)
  Out-of-order packets
```

---

## 24. Code Examples

### Go: TCP Connection Pooling

```go
type ConnectionPool struct {
    addr    string
    maxSize int
    idle    chan net.Conn
    mu      sync.Mutex
}

func NewConnectionPool(addr string, maxSize int) *ConnectionPool {
    return &ConnectionPool{
        addr:    addr,
        maxSize: maxSize,
        idle:    make(chan net.Conn, maxSize),
    }
}

func (cp *ConnectionPool) Get(ctx context.Context) (net.Conn, error) {
    select {
    case conn := <-cp.idle:
        // Reuse existing connection
        return conn, nil
    default:
        // Create new connection
        return net.DialContext(ctx, "tcp", cp.addr)
    }
}

func (cp *ConnectionPool) Put(conn net.Conn) error {
    select {
    case cp.idle <- conn:
        return nil
    default:
        // Pool full, close connection
        return conn.Close()
    }
}

// Usage:
pool := NewConnectionPool("example.com:443", 100)
conn, _ := pool.Get(context.Background())
defer pool.Put(conn) // Return to pool for reuse

// Write data
conn.Write([]byte("GET / HTTP/1.1\r\n..."))
// Read response
buf := make([]byte, 4096)
conn.Read(buf)
```

### Go: TCP Tuning

```go
func dialWithTuning(addr string) (net.Conn, error) {
    d := net.Dialer{
        Timeout:   30 * time.Second,
        KeepAlive: 30 * time.Second, // TCP keepalive
    }
    
    conn, err := d.Dial("tcp", addr)
    if err != nil {
        return nil, err
    }
    
    // Tune TCP options
    tcpConn := conn.(*net.TCPConn)
    
    // Disable Nagle (reduce latency)
    tcpConn.SetNoDelay(true)
    
    // Tune buffers (if needed)
    // tcpConn.SetReadBuffer(131072)   // 128KB
    // tcpConn.SetWriteBuffer(131072)
    
    // Keep connection alive
    tcpConn.SetKeepAlive(true)
    tcpConn.SetKeepAlivePeriod(30 * time.Second)
    
    return tcpConn, nil
}

// Usage:
conn, _ := dialWithTuning("example.com:443")
defer conn.Close()
```

---

## 25. Visual Diagrams

### TCP Handshake Timeline

```
Client              Server
  │                   │
  ├─ SYN ──────────→ │ (seq=100)
  │                   │
  │                 ←─ SYN-ACK (seq=200, ack=101)
  │                   │
  ├─ ACK ──────────→ │ (seq=101, ack=201)
  │                   │
  │                  ESTABLISHED
ESTABLISHED
  │
  ├─ DATA ──────────→ │
  │                   │
  │                 ←─ ACK
  │                   │

Time: ~100ms per arrow (roundtrip = 200ms total)
```

### TCP Window Scaling

```
Sender          Receiver
 │              buffer (64KB)
 │              │
 ├─ 1KB ──────→ │ (window: 63KB left)
 │              │
 ├─ 1KB ──────→ │ (window: 62KB left)
 │              │
 ├─ 1KB ──────→ │ (window: 61KB left)
 │              │
 ... (60KB more, buffer full)
 │
 ├─ 1KB ──────→ │ (window: 0)
 │              │
 │ (BLOCKED, can't send more)
 │
 │         processes...
 │
 │              ← ACK (window: 32KB)
 │
 │ (can send 32KB more)
```

---

## 26. Simulation Ideas

1. **TCP Handshake Latency Calculator**
   - Vary: distance (RTT)
   - Output: connection setup time

2. **Packet Loss Impact**
   - Vary: loss rate (0-5%)
   - Show: throughput degradation, latency increase

3. **Window Scaling Simulator**
   - Show: dynamic window size
   - Show: sender throughput adapting

4. **Congestion Control Visualizer**
   - Compare: CUBIC vs BBR
   - Show: throughput, latency, adaptation

---

## 27. Case Studies

### Case 1: Google QUIC → HTTP/3
Problem: TCP slow on high-loss networks
Solution: QUIC (0-RTT, better loss handling)
Result: YouTube latency reduced, throughput increased

### Case 2: Amazon EC2 Network Tuning
Problem: Default TCP slow for high-throughput workloads
Solution: tune buffers, use BBR, connection pooling
Result: 2-3x throughput improvement

---

## 28. Related Topics

- **Packet Loss & Retransmission**
- **Congestion Control Algorithms**
- **Network Latency & RTT**

---

## 29. Advanced Topics

### TCP_DEFER_ACCEPT

```
Problem: SYN-ACK uses resources, some connections never send data
Solution: defer ACK until data received
Result: save resources on abandoned connections
```

### TCP_FASTOPEN Cookie Rotation

```
TFO cookies expire for security
Clients must renew periodically
Cache: recent cookies for fast repeat connections
```

---

## 30. Production Checklist

- [ ] Enable TCP keepalive (SO_KEEPALIVE, 30s interval)
- [ ] Disable Nagle for latency-critical apps (TCP_NODELAY)
- [ ] Implement connection pooling (reuse connections)
- [ ] Monitor retransmit rate (alert if > 1%)
- [ ] Monitor packet loss (alert if detected)
- [ ] Tune TCP buffers (for your bandwidth×RTT)
- [ ] Handle TIME_WAIT properly (SO_REUSEADDR, tcp_tw_reuse)
- [ ] Test with packet loss simulator (chaos engineering)
- [ ] Monitor connection pool exhaustion
- [ ] Document TCP tuning decisions (why each setting)
- [ ] Test on high-latency links (satellite, intercontinental)
- [ ] Implement graceful connection degradation (fallback)

---

*Last Updated: 2026-05-28*
