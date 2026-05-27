# 🌐 TCP/IP Protocol Stack — Complete Deep Dive

## 📋 Table of Contents
- [OSI vs TCP/IP Model](#osi-vs-tcpip-model)
- [Ethernet](#ethernet)
- [ARP](#arp)
- [IP — Internet Protocol](#ip--internet-protocol)
- [TCP — Transmission Control Protocol](#tcp--transmission-control-protocol)
- [TCP State Machine](#tcp-state-machine)
- [TCP Flow Control](#tcp-flow-control)
- [TCP Congestion Control](#tcp-congestion-control)
- [TCP Retransmission & Timers](#tcp-retransmission--timers)
- [TCP vs QUIC](#tcp-vs-quic)
- [Simplest Mental Model](#simplest-mental-model)

---

## OSI vs TCP/IP Model

```text
OSI Model (7 Layers)          TCP/IP Model (5 Layers)      Protocol Data Unit
+-------------------+         +-------------------+         +----------------+
| 7. Application    |         | 5. Application    |         |    Data        |
| 6. Presentation   | ------> | (HTTP, DNS, TLS)  |         |                |
| 5. Session        |         |                   |         |                |
+-------------------+         +-------------------+         +----------------+
| 4. Transport      | ======> | 4. Transport      |         |    Segment     |
| (TCP/UDP)         |         | (TCP/UDP)         |         |    (Datagram)  |
+-------------------+         +-------------------+         +----------------+
| 3. Network        | ======> | 3. Network        |         |    Packet      |
| (IP)              |         | (IP)              |         |                |
+-------------------+         +-------------------+         +----------------+
| 2. Data Link      | ======> | 2. Data Link      |         |    Frame       |
| (Ethernet)        |         | (Ethernet)        |         |                |
+-------------------+         +-------------------+         +----------------+
| 1. Physical       | ======> | 1. Physical       |         |    Bits        |
| (Cables, Signal)  |         | (Cables, Signal)  |         |                |
+-------------------+         +-------------------+         +----------------+
```

**Mapping**: OSI L5-L7 collapsed into TCP/IP L5 (Application). L4→L4, L3→L3, L1-L2→L1-L2.

---

## Ethernet

### Frame Structure

```text
+----------+--------+----------+----------+----------+----------+------------+----------+
| Preamble |  SFD   |  MAC DA  |  MAC SA  | 802.1Q   |EtherType |  Payload   |   FCS    |
| 7 bytes  | 1 byte | 6 bytes  | 6 bytes  | 4 bytes  | 2 bytes  | 46-1500 B  | 4 bytes  |
|          |        |          |          |(optional)|          | (jumbo up  |          |
|          |        |          |          |Tag+TPID  |          |  to 9000)  |          |
+----------+--------+----------+----------+----------+----------+------------+----------+
```

- **Preamble** (7×10101010): Clock sync. **SFD** (10101011): Frame start marker.
- **MAC DA/SA**: 48-bit (OUI + NIC). Bit 0 = unicast(0)/multicast(1). Bit 1 = global(0)/local(1).
- **EtherType**: Protocol ID (IPv4=0x0800, IPv6=0x86DD, ARP=0x0806, 802.1Q=0x8100). Values < 1500 = 802.3 length.
- **FCS**: CRC-32 over frame (excl. preamble/SFD).

### Key Concepts

- **CSMA/CD**: Listen before talk, jam on collision, exponential backoff. Obsolete in full-duplex switched nets.
- **Full-Duplex**: Separate TX/RX pairs, no collisions, CSMA/CD disabled.
- **Auto-Negotiation**: FLP advertising capabilities → highest common denominator (speed+duplex).
- **VLAN Tagging (802.1Q)**: 4 bytes: TPID(0x8100) + PCP(3b priority) + DEI(1b drop) + VID(12b, 1-4094).
- **Jumbo Frames**: Payload up to 9000B, reduces per-frame overhead.
- **Flow Control (802.3x Pause)**: Receiver signals sender to pause. Can cause HOL blocking.

---

## ARP

### Packet Structure

```text
+---------+---------+--------+--------+----------------+----------------+----------------+----------------+
|HW Type  |Proto    |HW Len  |Proto   |  Opcode        |Sender MAC      |Sender IP       |Target MAC      |Target IP
|(2 bytes)|Type     |(1)     |Len(1)  |  (2 bytes)     |(6 bytes)       |(4 bytes)       |(6 bytes)       |(4 bytes)
|         |(2 bytes)|        |        |1=Req / 2=Reply |                |                |                |
+---------+---------+--------+--------+----------------+----------------+----------------+----------------+
```

- **ARP Cache**: `ip neigh show`. Dynamic entries expire ~60s. Static entries persist.
- **Gratuitous ARP**: Self-announcement of IP→MAC. For conflict detection, VRRP failover, NIC swap.
- **Proxy ARP**: Router answers for remote hosts, making subnets appear flat.
- **ARP Spoofing**: Forged ARP replies. Mitigation: DAI, static ARP, port security.
- **NDP (IPv6)**: Replaces ARP with ICMPv6 NS/NA, RS/RA. NUD for reachability verification.

---

## IP — Internet Protocol

### IPv4 Header

```text
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version|  IHL  |   DSCP/ECN  |         Total Length            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Identification        |Flags|     Fragment Offset     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|   TTL  |  Protocol  |        Header Checksum                  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Source Address                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     Destination Address                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options (if IHL > 5)                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

- **Version** (4). **IHL**: Header in 32-bit words (min 5). **DSCP+ECN**: QoS + congestion signals.
- **Total Length**: Header+payload, max 65535. **TTL**: Hop limit, 0→ICMP Time Exceeded.
- **Protocol**: Next header (1=ICMP, 6=TCP, 17=UDP). **Checksum**: Header only, recalculated per hop.

### Fragmentation

```text
Flags: [0][DF][MF]  DF=don't fragment, MF=more fragments
Fragment Offset: 13 bits, 8-byte blocks
  - First: offset=0, Last: MF=0, All except last must be 8B-aligned
```

**Path MTU Discovery**: Set DF, router returns ICMP Frag Needed (Type 3, Code 4) with MTU.

### IPv6 Header

```text
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version| Traffic Class |           Flow Label                  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Payload Length        |  Next Header  |  Hop Limit    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                       Source Address                          +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                     Destination Address                       +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

- **Flow Label**: 20-bit QoS without L4 inspection. **Next Header**: Extension or upper-layer.
- **No router fragmentation**: Source fragments via extension header.
- **SLAAC**: Stateless address autoconfiguration.

### Subnetting

- **CIDR**: `/24` = 255.255.255.0. Notation: `192.168.1.0/24`.
- **VLSM**: Variable masks per subnet (e.g., `/30` P2P, `/24` LAN).
- **Supernetting**: Aggregate contiguous prefixes (`192.168.0.0/23` covers two `/24`s).

---

## TCP — Transmission Control Protocol

### TCP Header

```text
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |        Destination Port       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Sequence Number                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     Acknowledgment Number                     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Offset| Reserved  |C|E|U|A|P|R|S|F|         Window            |
|      |           |W|C|R|C|S|S|Y|I|                           |
|      |           |R|E|G|K|H|T|N|N|                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Checksum            |        Urgent Pointer         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options (variable length)                  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

- **Seq#**: Byte offset of first data byte. **Ack#**: Next expected byte (cumulative).
- **Flags**: SYN(0x02), ACK(0x10), FIN(0x01), RST(0x04), PSH(0x08), URG(0x20), ECE(0x40), CWR(0x80).
- **Window**: Advertised rwnd. **Checksum**: Pseudo-header + TCP segment.

### TCP Options

| Option | Kind | Purpose |
|--------|------|---------|
| MSS | 2 | Max segment size (MTU - 40 = 1460) |
| Window Scale | 3 | Shift count (max 14) for >64KB window |
| SACK | 4/5 | Report non-contiguous received blocks |
| Timestamps | 8 | RTT measurement, PAWS |
| NOP | 1 | Alignment padding |

### Three-Way Handshake

```text
Client                                          Server
  |                                               |
  |   SYN (seq=x)                                 |
  |---------------------------------------------->|  LISTEN -> SYN-RECEIVED
  |                                               |
  |   SYN+ACK (seq=y, ack=x+1)                   |
  |<----------------------------------------------|
  |                                               |
  |   ACK (seq=x+1, ack=y+1)                     |
  |---------------------------------------------->|  SYN-RECEIVED -> ESTABLISHED
  |                                               |
  |<================ DATA FLOW ================>|
```

- **SYN Cookie**: Encode connection info in SYN-ACK seq. Client must ACK it → no SYN queue allocation.
- **TFO**: Client sends data in SYN using cached cookie. Saves 1-RTT on repeat connections.

### Connection Termination

```text
Client                                      Server
  |                                           |
  |   FIN (seq=u)                             |
  |------------------------------------------>|  ESTABLISHED -> CLOSE-WAIT
  |                                           |
  |   ACK (ack=u+1)                           |
  |<------------------------------------------|  FIN-WAIT-1 -> FIN-WAIT-2
  |                                           |
  |   (server sends remaining data)           |
  |<=========================================>|
  |                                           |
  |   FIN (seq=v, ack=u+1)                   |
  |<------------------------------------------|  CLOSE-WAIT -> LAST-ACK
  |                                           |
  |   ACK (ack=v+1)                           |
  |------------------------------------------>|  LAST-ACK -> CLOSED
  |                                           |
  |   (client enters TIME-WAIT for 2MSL)      |
```

- **TIME-WAIT (2MSL)**: ~60s. Prevents delayed segments corrupting new connections. Allows final ACK retransmission.

---

## TCP State Machine

```text
                          +-----------+
                          |   CLOSED  |
                          +-----+-----+
                                |
                          Passive|open (LISTEN)
                                v
                          +-----------+
              +---------->|  LISTEN   |<-----------+
              |           +-----+-----+            |
              |    SYN/SYN |           | SYN       |
              |    +ACK    |           | (active)  |
              |            v           |           |
              |     +-----------+      v           |
              |     |SYN-RECEIV | +-----------+    |
              |     +-----+-----+ | SYN-SENT  |    |
              |          |        +-----+-----+    |
              |          +-----------+ |           |
              |         ACK of SYN  SYN+ACK        |
              |                    received        |
              |                     |              |
              v                     v              |
        +-----------+       +-----------+          |
        |ESTABLISHED+------>|           |          |
        +-----+-----+  FIN  | CLOSE-WAIT|          |
              |              +-----+-----+          |
              | FIN               | FIN            |
              v                   v                 |
        +-----------+       +-----------+           |
        | FIN-WAIT-1+------>|   LAST-ACK|          |
        +-----+-----+  ACK  +-----------+           |
              |                                      |
              | ACK of FIN   +----------+            |
              +------------->| FIN-WAIT-2|           |
              |              +-----+----+            |
              |                    | FIN             |
              |                    v                 |
              |             +----------+             |
              +------------->| CLOSING  |            |
              |             +----+-----+             |
              |                  | ACK of FIN        |
              |                  v                   |
              |           +-----------+              |
              +-----------> TIME-WAIT |              |
                          +-----------+              |
                                | 2MSL timeout       |
                                v                    |
                          +-----------+              |
                          |   CLOSED  |              |
                          +-----------+              |
```

---

## TCP Flow Control

- **Sliding Window**: Sender sends up to `min(cwnd, rwnd)` unACKed bytes. Window slides on ACK.
- **Receive Window**: Advertised in TCP header. Zero window = stop sending.
- **Zero-Window Probe**: 1-byte probe when window closed. Persist timer backs off (5→10→30→60→120s).
- **Persist Timer**: Prevents deadlock if zero-window ACK is lost.

---

## TCP Congestion Control

### Slow Start & Congestion Avoidance

```text
cwnd (packets)     ssthresh
      ^         +----|-----+
      |        /     |      \
      |   Slow/      |       \   Congestion
      |  Start/      |        \  Avoidance (AIMD)
      |      +---+    +---+    +---+
      +----------------------------------------> RTT
```

- **Slow Start**: cwnd starts ~10MSS, doubles per RTT until cwnd ≥ ssthresh or loss.
- **ssthresh**: Initially high (`rwnd`). On loss: `ssthresh = cwnd/2`.
- **AIMD**: Additive (+1 MSS/RTT) / Multiplicative (−50%). Fairness/convergence principle.

### Fast Retransmit & Fast Recovery

- **3 duplicate ACKs** → fast retransmit (no RTO wait).
- **Fast Recovery**: `ssthresh = cwnd/2`, `cwnd = ssthresh + 3*MSS`. Inflate per dupACK. Deflate on new ACK.

### CUBIC

```text
Wcubic = C * (t - K)^3 + Wmax
  C = 0.4, beta = 0.3, K = (Wmax * beta / C)^(1/3)
  Window growth is cubic in time (RTT-independent) → fair across RTTs
```

### BBR

- **States**: `STARTUP` → `DRAIN` → `PROBE_BW` ↔ `PROBE_RTT`
- **Pacing**: `pacing_rate = pacing_gain × bandwidth_estimate`
- **Bandwidth**: Max delivery rate (windowed max filter). **RTT**: Min RTT over 10s (min filter).
- **PROBE_BW**: Cycle gains (1.25, 0.75, 1.0×6) to probe capacity. **PROBE_RTT**: Drain to 4 pkts every 10s.

---

## TCP Retransmission & Timers

### RTO

- **Jacobson**: `SRTT = 7/8×SRTT + 1/8×RTT`. `RTTvar = 3/4×RTTvar + 1/4×|SRTT - RTT|`. `RTO = SRTT + 4×RTTvar`.
- **Karn/Partridge**: Don't update RTT on retransmitted segments. Double RTO per backoff (max 60s).
- **TLP**: Send last unACKed segment ~2RTT later to detect tail loss without RTO.
- **RACK**: Time-based loss detection using most recently delivered packet.

### Timers

| Timer | Purpose | Default |
|-------|---------|---------|
| Retransmission | RTO tracking | 1s initial, 60s max |
| Persist | Zero-window probe | 5s initial, 60s max |
| Keepalive | Idle check | 7200s idle, 9 probes×75s |
| TIME-WAIT | 2MSL cleanup | 60s |
| Delayed ACK | Combine ACKs | 40ms max / 2 segments |

---

## TCP vs QUIC

| Feature | TCP | QUIC |
|---------|-----|------|
| Transport | Kernel TCP | Userspace UDP |
| Handshake | 1-RTT + optional TFO | 0-RTT integrated crypto |
| Multiplexing | Single stream | Multiple streams |
| HOL blocking | Yes — lost seg blocks all streams | No — stream-level only |
| Encryption | Optional (TLS) | Mandatory (TLS 1.3) |
| Connection migration | Breaks on IP:port change | Connection ID survives |
| Loss detection | RTO, Fast Retransmit, RACK | RACK-based, faster |

---

## Simplest Mental Model

> **TCP/IP is a postal service for computers.**
>
> - **Ethernet** = truck delivering envelopes on a local street.
> - **ARP** = looking up house number from a name on the street.
> - **IP** = city + zip code on the envelope — routes across the country.
> - **TCP** = registered mail with tracking — guarantees delivery, re-orders letters, slows when post office is congested.
> - **TCP state machine** = life cycle of a phone call (dial → hello → talk → bye → hang up).
> - **TCP flow/congestion control** = not sending too many letters at once (window) and slowing when mailbox is full.
> - **QUIC** = FedEx priority — faster setup, multiple packages without blocking each other, survives address changes mid-delivery.