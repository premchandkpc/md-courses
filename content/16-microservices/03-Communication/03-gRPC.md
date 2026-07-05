# 03-gRPC

gRPC is a high-performance RPC framework developed by Google that uses HTTP/2 for transport and Protocol Buffers for serialization. It provides strong typing, bidirectional streaming, and automatic code generation.

## Overview

gRPC defines service contracts in `.proto` files, specifying methods, request types, and response types with strict schema definitions. The Protobuf compiler generates client and server code in 11+ languages, eliminating manual serialization and deserialization. HTTP/2 provides multiplexed streams, header compression, and server push, making gRPC significantly more efficient than REST/JSON for internal service-to-service communication.

## Key Characteristics

- **Strong Typing**: Protobuf schemas define exact field types, required/optional constraints, and numeric field tags. This catches contract violations at compile time rather than runtime.
- **Streaming**: Four communication modes — unary (request-response), server streaming, client streaming, and bidirectional streaming. Streaming is useful for real-time data feeds and large result sets.
- **Deadlines and Timeouts**: Every gRPC call carries a deadline. The server checks this deadline and aborts if it's exceeded, preventing cascade failures. This is a significant improvement over HTTP timeouts.
- **Code Generation**: `protoc` generates idiomatic stubs for both client and server. This eliminates boilerplate and ensures the client and server always agree on the contract.
- **Interceptors**: Middleware pattern for cross-cutting concerns: logging, auth, rate limiting, tracing. Analogous to HTTP middleware but for RPC calls.

## Why It Matters

gRPC is the preferred protocol for internal microservice communication in performance-sensitive systems. Benchmarks show 5-10x better throughput than JSON/REST in high-volume scenarios. The strong typing and code generation reduce integration bugs. The tradeoffs are: browser support requires gRPC-Web (or a proxy), debugging is harder (binary wire format), and the ecosystem is less familiar than REST for many developers.

## Related Concepts

- [02-REST](02-REST.md) — the main alternative for sync communication
- [10-Schema-Evolution](../02-Service-Design/10-Schema-Evolution.md) — Protobuf schema evolution rules apply directly to gRPC
- [12-Choosing-Communication](12-Choosing-Communication.md) — when to choose gRPC over REST

---

## Mental Model

gRPC is like a submarine's communication system — highly efficient, structured, and purpose-built. Instead of human-readable radio messages (JSON), the crew uses binary-coded signals (Protobuf) that are faster to transmit and guaranteed to be understood correctly. The protocol definition (`.proto` file) is the codebook that both sides share before deployment.
