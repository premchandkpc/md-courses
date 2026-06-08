---
title: UDP & Datagram Protocols Deep Dive - L5 Networking
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# UDP & Datagram Protocols Deep Dive - L5 Networking

> **[🎨 View Interactive Diagram](udp-architecture.html)** | [← Back to Index](../../systems-index.html)

*"Why do video streams use UDP instead of TCP? Isn't reliability important?"*

---

## 1. Problem Statement

**Core Question:** When is losing some data acceptable? When can you trade reliability for speed?

Tradeoff:
- TCP: reliable, ordered, slow (100-200ms handshake + flow control)
- UDP: unreliable, unordered, fast (<1ms, no handshake)

Use UDP when:
- Real-time apps (gaming, video)
- Latency critical (better to lose packet than delay)
- Broadcast/multicast needed

---

## 2. Real World Analogy

**Live TV Broadcast:**

TCP approach (guaranteed delivery):
- Every frame must be received
- If frame lost: wait for retransmit
- Result: lag, buffering, user frustration

UDP approach (best effort):
- Some frames may be lost
- If frame lost: skip, move on
- Result: occasional artifact, but smooth overall

User prefers: smooth stream with rare glitches

---

## 3. Why Problem Exists

### TCP Overhead

```
TCP handshake: 1 RTT (100ms)
Flow control: adds latency (waits for window)
Congestion control: backs off on loss
Retransmit: adds 1-2s delay

Total: can add 100-2000ms overhead

For video: unacceptable (user sees lag)
```

### UDP Advantages

```
No handshake: immediate (0ms setup)
No flow control: send at wire speed
No retransmit: lost packet ignored
Result: latency minimal, throughput high
```

---

## 4. Naive Approach

**"Use UDP for everything"**

Problems:
- Packets may be lost (silent)
- Out-of-order delivery (confusion)
- No congestion control (overwhelming network)
- Application must handle reliability (complex)

---

## 5. Why Naive Fails

### Packet Loss Compounding

```
No congestion control:
  Sender: sends at 100Mbps
  Network: can only handle 10Mbps
  Loss rate: grows (congestion)
  Sender: doesn't care, keeps sending
  Loss rate: increases to 50%+
  Network: becomes unusable

TCP: would back off, reduces loss to <1%
```

### Ordering Issues

```
Send: "transfer $100 from A to B"
  Packet 1: "$100"
  Packet 2: "from A to B"

Arrive out of order:
  Packet 2 arrives first: "from A to B" (incomplete)
  Packet 1 arrives later: "$100" (late)

Application: must handle out-of-order
```

---

## 6. Evolution / Progression

### Stage 1: Raw UDP
- No reliability, no ordering
- Application handles everything

### Stage 2: QUIC
- UDP-based, but adds reliability
- 0-RTT (faster than TCP)
- Better loss recovery
- Congestion control built-in

### Stage 3: Custom Protocols
- Apps: implement reliability as needed
- Video: FEC (forward error correction)
- Gaming: delta compression (send only changes)

---

## 7. Production Architecture

```
[Application: Video Stream]
    │ (encode video → packets)
    ▼
[UDP Socket]
    ├─ Each frame: 1-10 packets
    ├─ Send immediately (no queue)
    └─ No ack waiting
    
[Network]
    ├─ Best effort (may drop)
    ├─ No guarantees
    ├─ May reorder
    └─ May duplicate

[Receiver]
    ├─ Receive packets
    ├─ Reorder if needed (sequence #s)
    ├─ Decode frame (FEC: reconstruct lost)
    └─ Display (skip if too late)
```

---

## 8. Components

### UDP Header

```
Source Port (16 bits)
Dest Port (16 bits)
Length (16 bits)
Checksum (16 bits) - optional for IPv4

Total: 8 bytes (vs TCP: 20 bytes minimum)

Minimal overhead: good for latency
```

### Packet Sequence Numbers

```
Sender tags each packet: seq_num
Receiver: reorders if out-of-order
Lost packet: detected (gap in sequence)

Frame reconstruction:
  Lost packet 5 of 10
  FEC: reconstruct from remaining 9 (if coded)
  Or: skip, decode without (lossy)
```

### Forward Error Correction (FEC)

```
Send: 10 data packets + 3 redundant packets
  Redundant: linear combination of data

Receive: any 10 of 13 packets
  Can reconstruct all 10 data packets

Cost: 30% overhead (13 vs 10)
Benefit: tolerates 30% loss
```

---

## 9. Internal Working

### UDP vs TCP Latency

```
Sending 1 packet:

TCP:
  t=0:    Create socket
  t=0-1:  TCP handshake (1 RTT)
  t=1:    Send data
  t=1-2:  Network delay
  t=2:    Receive (total: 2 RTT + 1 = ~101ms)

UDP:
  t=0:    Send packet
  t=0-1:  Network delay
  t=1:    Receive (total: 1 RTT = ~50ms)

Difference: 2x faster
```

### Congestion in UDP Network

```
Without congestion control:
  Sender: sends at 100Mbps
  Link: 10Mbps, queue: 90Mbps backed up
  Router: queue overflows (drops packets)
  Loss rate: 50%+ (runaway)

With TCP:
  After loss detected
  Congestion window: halved
  Rate: reduced to 50Mbps
  Loss: stops
  Network: recovers
```

---

## 10. Request Lifecycle

```
Video streaming:

t=0ms:      Frame 1 encoded (H.264)
t=0-5ms:    Split into 10 packets
t=5ms:      Send all 10 via UDP
t=5-25ms:   Network transit
t=25ms:     Receiver gets packets 1,3,4,5,7,8,9,10 (packet 2,6 lost)
t=25-30ms:  FEC reconstruct (or skip lost)
t=30-35ms:  Decode frame 1
t=35ms:     Display frame 1

Latency: 35ms (vs TCP: would be 100-200ms with retransmits)
Quality: slight artifact (2 packets lost), but smooth
```

---

## 11. Data Flow

### Multicast Scenario

```
Sender: broadcasts video to 1000 users
  Packet sent once on network
  Router: duplicates to all recipients
  Cost: 1 × data rate

TCP equivalent:
  1000 separate connections
  1000 × handshakes
  1000 × retransmits
  Cost: 1000x overhead

UDP: efficient, but unreliable (typical is acceptable)
```

---

## 12. Key Strategy

### 1. Use UDP for Real-Time Apps

```
Video streaming: UDP (tolerance for loss)
Online gaming: UDP (latency critical)
VoIP: UDP (some audio loss acceptable)
DNS: UDP (retry if no response)
NTP: UDP (coarse accuracy needed)
```

### 2. Implement Selective Reliability

```
Critical: use retransmit + ack
Non-critical: fire and forget

Example: game packet
  Player position: non-critical (next packet overrides)
  Player action: critical (attack must hit)

Send critical packets via TCP or UDP with ack
Send non-critical via pure UDP
```

### 3. Add Congestion Control

```
Even for UDP: monitor loss rate
If loss > 5%: reduce send rate
If loss < 1%: increase send rate

Custom algorithm or: use QUIC (built-in)
```

---

## 13. Failure Scenarios

### Scenario 1: Network Congestion

```
UDP without congestion control:
  Sender: keeps sending at max rate
  Loss: increases (queue overflows)
  Loss: 50%+ (unusable)

Solution: implement backoff
  Loss > 5%: reduce rate by 10%
  Loss < 1%: increase rate by 10%
```

### Scenario 2: Packet Reordering

```
Send: packets 1,2,3,4
Arrive: 1,3,2,4

Without handling: application confusion
With sequence numbers:
  Receiver: buffers out-of-order
  Reassembles: 1,2,3,4
  Delivers: in order
```

---

## 14. Bottlenecks Table

| Issue | Impact | Fix |
|---|---|---|
| No congestion control | Network collapse | Add backoff |
| Out-of-order packets | Application error | Sequence numbers |
| Packet loss | Missing data | FEC or retransmit |
| No flow control | Sender too fast | Rate limiting |

---

## 15. Monitoring

### Key Metrics

```
Packet loss rate: % lost (target: <1%)
Out-of-order rate: % reordered (target: <0.1%)
Jitter: variation in delay (target: <50ms)
Reachability: % of destinations reached
```

---

## 16. Optimizations

### 1. Batch Packets

```
Instead of: send 1 packet at a time (overhead)
Batch: send 10 packets per call (amortize)

Result: higher throughput, lower CPU
```

### 2. FEC (Forward Error Correction)

```
Send: 10 data + 5 redundant (50% overhead)
Receive: any 10 of 15 → reconstruct all

Trade: overhead vs loss tolerance
```

---

## 17. Security

### 1. DDoS via UDP

```
Attacker: send massive UDP packets
Amplification: DNS, NTP (respond larger)

Defense: rate limiting, source IP validation
```

---

## 18. Tradeoffs Table

| Aspect | UDP | TCP |
|---|---|---|
| Latency | Low (<50ms) | High (100-200ms) |
| Reliability | No | Yes |
| Overhead | Minimal | High |
| Use Case | Real-time | Reliable data |

---

## 19. Alternatives

### QUIC

```
UDP-based, but adds:
  Reliability (if needed)
  Congestion control (automatic)
  0-RTT (faster)

Benefits: TCP reliability + UDP speed
```

---

## 20. When NOT to Use

### Don't Use UDP When:

1. **Data loss unacceptable**
   - Banking, payments
   - Use TCP

---

## 21. Interview Questions

1. **Design video streaming (1M users)**
   - TCP or UDP?
   - Why?
   - Handle packet loss?

2. **UDP packet loss 10%**
   - Root cause?
   - Solutions?

3. **Online game networking**
   - Protocol choice?
   - Latency target?
   - Reliability needs?

---

## 22. Common Mistakes

1. **Using UDP without loss handling**
   - Expect: unreliable
   - Reality: 50% loss on congestion
   - Add: congestion control

2. **Ignoring packet ordering**
   - Packets arrive scrambled
   - Add: sequence numbers

3. **Not rate limiting**
   - Overwhelming network
   - Add: congestion control

---

## 23. Debugging Guide

### Step 1: Check Loss Rate

```
netstat -u (UDP stats)
Packets in/out: loss rate

High loss (>1%):
  Network issue or
  Sender too fast
```

### Step 2: Check Latency

```
ping -c 100 (average latency)
ping (latency variance/jitter)

High jitter: congestion
```

---

## 24. Code Examples

### Go: UDP Server

```go
func udpServer() {
    addr := net.UDPAddr{
        Port: 8080,
        IP:   net.ParseIP("0.0.0.0"),
    }
    
    conn, _ := net.ListenUDP("udp", &addr)
    defer conn.Close()
    
    buffer := make([]byte, 1024)
    for {
        n, remoteAddr, _ := conn.ReadFromUDP(buffer)
        
        // Echo back
        conn.WriteToUDP(buffer[:n], remoteAddr)
    }
}
```

---

## 25. Visual Diagrams

### UDP vs TCP Latency

```
Time to First Packet:

TCP:    [Handshake: 1 RTT] [Send] [Receive]
UDP:    [Send] [Receive]

UDP: 2x faster
```

---

## 26. Simulation Ideas

1. **Congestion Control Simulator**
   - Vary: loss rate
   - Show: impact of backoff

---

## 27. Case Studies

### YouTube: VP9 over UDP
Result: 25% faster, handles 10% loss

---

## 28. Related Topics

- **Packet Loss & Retransmission**
- **Congestion Control**
- **Real-Time Protocols**

---

## 29. Advanced Topics

### QUIC Protocol

```
UDP-based, but:
  Multiplexing (like HTTP/2)
  Reliable delivery (optional)
  0-RTT connection (faster)
  Congestion control (built-in)
```

---

## 30. Production Checklist

- [ ] Use UDP for real-time apps
- [ ] Implement packet sequence numbers
- [ ] Handle out-of-order packets
- [ ] Implement congestion control
- [ ] Monitor packet loss rate
- [ ] Monitor latency/jitter
- [ ] Use FEC if needed
- [ ] Rate limiting to prevent DDoS
- [ ] Test with packet loss simulator
- [ ] Document reliability guarantees

---

*Last Updated: 2026-05-28*
