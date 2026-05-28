# Networking Deep Dive

Network fundamentals: how data moves between systems at scale.

## Topics

### 1. TCP/IP Protocol Stack
- OSI model layers
- TCP connection lifecycle (3-way handshake)
- Congestion control & flow control
- Packet retransmission & reliability
- TCP performance tuning

### 2. DNS Resolution
- Domain name resolution process
- DNS caching & TTL
- DNS query types (A, CNAME, MX, SRV)
- DNS load balancing
- DNS failures & resilience

### 3. HTTP/HTTPS
- HTTP request/response model
- HTTP methods & status codes
- HTTP/1.1 vs HTTP/2 vs HTTP/3
- SSL/TLS handshake & encryption
- Certificate management

### 4. UDP & Datagram Protocols
- UDP vs TCP tradeoffs
- Connectionless communication
- Packet loss & ordering
- QUIC protocol
- Real-time applications (gaming, streaming)

### 5. WebSockets & Real-Time
- WebSocket upgrade & protocol
- Persistent connections
- Server-sent events (SSE)
- Message ordering & reliability
- Connection management at scale

### 6. Load Balancing
- Load balancing algorithms
- Layer 4 vs Layer 7 (transport vs application)
- Health checks & failover
- Sticky sessions & connection affinity
- Geographic load balancing

### 7. CDN (Content Delivery Networks)
- Edge caching & geographic distribution
- Cache invalidation strategies
- Origin shields & cache hierarchies
- DDoS protection via CDN
- Cost optimization

### 8. BGP & Routing
- Border Gateway Protocol basics
- Route propagation & convergence
- Failover & multi-path routing
- AS (Autonomous System) concepts
- Network partitions & recovery

### 9. Network Security
- Firewalls & DDoS protection
- Rate limiting at network layer
- VPN & encrypted tunnels
- Network segmentation
- Threat detection & mitigation

### 10. Network Performance & Optimization
- Latency sources (routing, propagation, processing)
- Bandwidth optimization
- Packet loss & retransmission
- Network monitoring & metrics
- Capacity planning

---

Each topic covers: fundamentals, production patterns, failure modes, debugging, code examples, monitoring, and optimization strategies.

**Prerequisites:** System Design Foundations (scalability, latency, throughput, availability).
