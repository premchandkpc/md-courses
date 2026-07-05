# Secrets Management

Secrets management encompasses the tools, policies, and practices for securely storing, accessing, rotating, and auditing sensitive information such as API keys, database passwords, TLS certificates, and encryption keys. In microservices, the number and churn of secrets grows with service count, making centralized, automated secrets management essential.

## Overview

Microservices systems require secrets for almost every function: service-to-service authentication, database access, external API integration, encryption at rest, and TLS certificates. Hardcoding secrets or storing them in configuration files creates unacceptable risk. A dedicated secrets management system provides a central vault that services authenticate to (using their own identity) to retrieve secrets. Access is audited, secrets are rotated automatically, and dynamic secrets are generated on-demand rather than pre-provisioned.

## Key Characteristics

- **Centralized Vault**: A secure store (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager) that encrypts secrets at rest and controls access via policies. The vault itself is hardened and audited. Services never store secrets locally — they fetch them at startup and cache with short TTLs.
- **Dynamic Secrets**: Secrets generated on-demand rather than long-lived static credentials. For example, Vault can create a database user with a limited TTL when a service requests credentials. The user is automatically deleted when the lease expires. This eliminates the security risk of stale database accounts and credential leaks.
- **Encryption at Rest**: All secrets are encrypted before storage using envelope encryption. The vault encrypts secrets with a data encryption key (DEK), which is itself encrypted by a master key (KEK) stored in a hardware security module (HSM) or cloud KMS. The vault never sees the unencrypted master key.
- **Access Policies**: Fine-grained policies determine which identities can read which secrets. Policies are typically defined in terms of service identity (SPIFFE ID or Kubernetes service account). A policy might state: `path "database/orders/*" { capabilities = ["read"] }` for the `orders-service` identity.
- **Secret Rotation**: Automated rotation limits the exposure window if a credential is compromised. Rotation can be periodic (every 30 days) or event-driven (after a security incident). Dynamic secrets rotate naturally as leases expire, while static secrets require explicit rotation workflows with zero-downtime deployment coordination.
- **Audit Trail**: Every secret access is logged — who accessed what secret, when, and from where. Audit logs feed into SIEM systems and support compliance requirements (SOC 2, PCI-DSS, HIPAA). Anomaly detection alerts on unexpected access patterns, such as a service reading secrets it doesn't typically need.

## Why It Matters

Without a secrets management system, microservices inevitably leak credentials. Secrets end up in Docker images, environment variables in CI logs, config files committed to git, or hardcoded in source code. A centralized vault enforces a single security boundary with strong access controls, eliminates credential sprawl, and provides auditability. The principle is: no service ever "knows" a secret permanently — it leases what it needs, when it needs it.

## Related Concepts

- [Service Identity](09-Service-Identity.md) — Secrets access is bound to service identity (SPIFFE ID, service account)
- [mTLS](04-mTLS.md) — Secrets systems use mTLS to authenticate requesting services
- [Encryption](06-Encryption.md) — Envelope encryption protects secrets at rest in the vault
- [Zero Trust](08-Zero-Trust.md) — Secrets management follows zero trust principles: verify every access request

---

## Mental Model

A secrets management system is like a high-security bank vault. Each service has its own safe deposit box (secret path) and can only open its own box using its badge (service identity). The bank (vault) verifies the badge at the door (mTLS), logs every visit (audit trail), and automatically changes the lock combinations (rotation) on a schedule. If someone steals a badge, they can only access that service's box during a limited window.
