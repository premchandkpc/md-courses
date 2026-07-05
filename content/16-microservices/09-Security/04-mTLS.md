# Mutual TLS (mTLS)

Mutual TLS is a transport-layer security protocol where both the client and server present X.509 certificates to authenticate each other. Unlike standard TLS (where only the server presents a certificate), mTLS requires both parties to prove their identity cryptographically. In microservices, mTLS is the foundation for service-to-service authentication.

## Overview

mTLS ensures that every service-to-service connection is authenticated and encrypted in both directions. Each service is issued a unique certificate (often by a service mesh or SPIFFE-compatible authority) that it presents when establishing connections. The receiving service verifies the sender's certificate against a trusted CA, ensuring only authorized services can communicate. Service meshes like Istio and Linkerd automate mTLS certificate issuance, rotation, and enforcement with no application code changes.

## Key Characteristics

- **Bidirectional Authentication**: Both parties exchange and verify certificates during the TLS handshake. This prevents man-in-the-middle attacks and ensures both endpoints are who they claim to be. Even if network-level access is obtained, an attacker cannot impersonate a service without its private key and certificate.
- **SPIFFE Integration**: SPIFFE (Secure Production Identity Framework for Everyone) standardizes service identity using URIs embedded in X.509 certificates. A typical SPIFFE ID looks like `spiffe://cluster.local/ns/default/sa/webapp`. This identity is bound to the service's orchestration identity (Kubernetes service account) rather than a hostname or IP.
- **Certificate Rotation**: Short-lived certificates (hours to days) are automatically rotated to limit the blast radius of compromised keys. Service mesh control planes or dedicated certificate authorities handle the full lifecycle — issuance, renewal, and revocation. Zero-downtime rotation requires clients to load new certificates before old ones expire.
- **Service Mesh Integration**: In Istio, Envoy sidecars handle mTLS transparently. The control plane (istiod) distributes certificates to all sidecars, which terminate mTLS on behalf of their associated services. Application code never touches TLS — it communicates over plain HTTP to the local sidecar, which handles encryption.
- **Performance Overhead**: mTLS adds CPU overhead for handshake and encryption. Modern service meshes use TLS 1.3 (reduced round trips) and session resumption to minimize impact. Hardware acceleration and optimized TLS libraries (BoringSSL, rustls) further reduce the cost.

## Why It Matters

mTLS solves the fundamental challenge of service identity in microservices. Traditional IP-based or hostname-based trust is unreliable in dynamic environments where services are constantly created, destroyed, and rescheduled. With mTLS, identity is cryptographic and bound to the service's workload identity, not its network location. This enables zero-trust networking where no service implicitly trusts any other — every connection must prove its identity.

## Related Concepts

- [Service Identity](09-Service-Identity.md) — mTLS certificates encode service identity; SPIFFE standardizes the identity format
- [Zero Trust](08-Zero-Trust.md) — mTLS is a primary enforcement mechanism for zero trust architectures
- [Istio](05-Istio.md) — Istio automates mTLS across the mesh using Envoy sidecars
- [Linkerd](06-Linkerd.md) — Linkerd provides automatic mTLS with a lightweight Rust-based proxy
- [Service Mesh](04-Service-Mesh.md) — Service meshes handle mTLS lifecycle transparently

---

## Mental Model

mTLS is like a secure embassy meeting with dual ID checks. You (client) present your passport to the ambassador (server), but the ambassador also shows you their credentials first. Both sides verify the other's ID against a trusted authority (CA) before discussing anything sensitive. In a service mesh, the sidecar proxies are like embassy security handlers — they check all IDs at the door so the ambassador can focus on the conversation.
