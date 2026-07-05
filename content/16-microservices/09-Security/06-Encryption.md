# Encryption in Transit and at Rest

Encryption protects data from unauthorized access at two points: in transit (moving across the network) and at rest (stored on disk or in databases). Both are essential defense layers in a microservices architecture. Encryption alone is insufficient without proper key management — the security of encrypted data depends entirely on the security of the encryption keys.

## Overview

In transit, encryption ensures that data cannot be read or modified as it travels between services, clients, and databases. TLS 1.2/1.3 is the standard protocol, with mTLS providing mutual authentication for service-to-service traffic. At rest, encryption protects persisted data using symmetric algorithms (AES-256-GCM) or asymmetric wrapping. Microservices typically delegate encryption to the infrastructure layer (service mesh, database encryption features, object storage server-side encryption) rather than implementing cryptography in application code.

## Key Characteristics

- **TLS for Transit**: TLS 1.3 eliminates insecure cipher suites, reduces handshake round trips (0-RTT for resuming sessions), and provides perfect forward secrecy. Every microservice endpoint should terminate TLS. Service meshes transparently inject TLS between sidecars, ensuring all east-west traffic is encrypted without application changes.
- **AES-256-GCM for Data at Rest**: AES-256 with Galois/Counter Mode provides both confidentiality and authenticated encryption (integrity verification). It is the standard for encrypting database columns, files, and backups. GCM mode produces an authentication tag that detects tampering.
- **Envelope Encryption**: A two-layer key hierarchy. A data encryption key (DEK) encrypts the actual data. The DEK is encrypted by a key encryption key (KEK) stored in a KMS or HSM. This allows the KEK to be kept in a highly secure boundary while DEKs can be distributed more freely. If a DEK is compromised, only one DEK needs to be rotated rather than the master KEK.
- **Key Management**: The most critical and most challenging aspect of encryption. Keys must be generated securely, stored in a hardware-backed KMS, rotated regularly, and destroyed when compromised. Cloud KMS (AWS KMS, Azure Key Vault, GCP Cloud KMS) provides managed key lifecycle. Never store encryption keys alongside the data they protect.
- **Application-Level Encryption**: For sensitive fields (PII, payment data), encrypt at the application layer before data reaches the database. Column-level encryption ensures that even if the database is breached, specific fields remain protected. The tradeoff is that encrypted fields cannot be indexed or searched without techniques like deterministic encryption or searchable encryption.
- **Encryption in Memory**: Emerging practice for workloads handling highly sensitive data. Memory encryption (AMD SEV, Intel SGX) protects data even from compromised hypervisors or memory dumps. Typically used in regulated industries where data must be protected at all times.

## Why It Matters

Encryption is the last line of defense in a defense-in-depth security strategy. If an attacker bypasses network controls, authentication, and authorization, encryption ensures the data remains unreadable. In microservices, where data flows across many network hops and is stored in many systems, encryption at both layers prevents single breaches from becoming catastrophic data exposures. Compliance frameworks (PCI-DSS, HIPAA, GDPR, SOC 2) mandate both encryption types.

## Related Concepts

- [mTLS](04-mTLS.md) — Mutual TLS as the mechanism for encrypting service-to-service traffic
- [Secrets Management](05-Secrets.md) — Encryption keys are the most critical secrets to manage
- [Zero Trust](08-Zero-Trust.md) — Encryption ensures data is protected even if network boundaries are compromised
- [Service Mesh](04-Service-Mesh.md) — Mesh encrypts all east-west traffic transparently

---

## Mental Model

Encryption in transit is like putting a letter in a sealed envelope before mailing it — tampering is visible. Encryption at rest is like locking the letter in a safe once it arrives. Envelope encryption is like keeping the safe key in a bank safety deposit box while using a copy to lock the actual safe. If someone steals the copy, you only need to change one safe — the deposit box key remains secure.
