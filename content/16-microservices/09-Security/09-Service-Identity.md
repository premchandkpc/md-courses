# Service Identity

Service identity is the practice of assigning a unique, verifiable identity to every workload in a microservices system. Unlike user identity (who the human is), service identity answers "which service is making this request?" Strong service identity is the foundation for mTLS, authorization policies, and secrets management — a service's identity determines what it can access and what trust it receives.

## Overview

In a microservices system, services must authenticate to each other to establish secure communication channels. Service identity provides the cryptographic anchor for this authentication. Each service is issued an identity document (typically an X.509 certificate) that binds the service's identity to its workload. The standard for service identity in cloud-native environments is SPIFFE (Secure Production Identity Framework for Everyone), which defines both the identity format and the API for identity issuance.

## Key Characteristics

- **SPIFFE Standard**: The SPIFFE identity is a URI in the format `spiffe://trust-domain/path`. For example, `spiffe://prod.acme.com/ns/payments/sa/processor` identifies the `processor` service account in the `payments` namespace of the `prod.acme.com` trust domain. The trust domain establishes a root of trust. The path encodes organization-specific hierarchy (namespace, service account, etc.).
- **SPIRE Implementation**: SPIRE is the production-ready SPIFFE implementation. It runs as a server that issues identities to workloads based on attestation (Kubernetes service account, node attestation, etc.). Workloads call the SPIRE agent's Unix socket to receive their identity document — a short-lived X.509 SVID (SPIFFE Verifiable Identity Document).
- **Certificate-Based Identity**: Service identity is implemented as X.509 certificates (SVIDs) signed by the SPIRE server's CA. The certificate's SAN (Subject Alternative Name) contains the SPIFFE URI. Services present this certificate during mTLS handshakes. Short lifetimes (hours) limit exposure and drive automatic rotation.
- **Workload Attestation**: Before issuing an identity, SPIRE verifies that the requesting workload is genuine. In Kubernetes, attestation checks the pod's service account, namespace, node, and container image. The attestation chain ensures that identity cannot be spoofed by an attacker running a malicious container.
- **Identity-Bound Policies**: Once identity is established, it drives authorization. A service's SPIFFE ID determines which secrets it can read from Vault, which databases it can access, which other services it can call, and which operations it can perform. Policies reference identity rather than IP addresses, making them portable across environments.
- **Rotation and Revocation**: Certificates are rotated automatically before expiration. SPIRE detects workload termination and can revoke identities. Service mesh sidecars reload certificates from SPIRE without application restarts. Revocation is propagated via CRLs or OCSP, though short lifetimes reduce reliance on revocation mechanisms.

## Why It Matters

Without service identity, microservices resort to weak trust mechanisms: shared secrets, IP whitelisting, or network-based trust. These break in dynamic environments where IPs change and containers are ephemeral. Service identity with SPIFFE provides a portable, automatable, cryptographically strong identity layer. Combined with mTLS and authorization policies, it enables zero trust networking where every service-to-service call is authenticated and authorized.

## Related Concepts

- [mTLS](04-mTLS.md) — Service identity is presented and verified through mTLS certificates
- [Zero Trust](08-Zero-Trust.md) — Strong service identity is a prerequisite for zero trust architectures
- [Secrets Management](05-Secrets.md) — Secrets access is bound to service identity
- [Istio](05-Istio.md) — Istio integrates with SPIFFE/SPIRE for service identity in the mesh
- [Linkerd](06-Linkerd.md) — Linkerd issues identities tied to Kubernetes service accounts

---

## Mental Model

Service identity is like a government-issued ID card for each microservice. The SPIFFE ID is the equivalent of a passport number — unique, verifiable, and portable across borders (environments). SPIRE is the passport office: it verifies you are who you claim to be (attestation), issues the passport (certificate), and handles renewals (rotation). Just as you need a passport to cross international borders, a service needs its identity to communicate securely with other services.
