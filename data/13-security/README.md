# Security Engineering — Complete Deep Dive 🔒

Security engineering is about building systems that remain **confidential, integral, and available** in the face of adversaries. It spans cryptography, application security, infrastructure hardening, identity management, and supply chain defense.

**Related**: [Web Security](../security/web-security.md) · [Networking Security](../11-networking/README.md) · [Cloud Security](../05-cloud/README.md) · [DevSecOps](../06-devops/README.md)

---

## Table of Contents

- [Core Security Principles](#-core-security-principles)
- [Threat Modeling](#1-threat-modeling-)
- [Cryptography](#2-cryptography-)
- [Authentication & Authorization](#3-authentication--authorization-)
- [OWASP Top 10](#4-owasp-top-10-)
- [Web Security](#5-web-security-)
- [Network Security](#6-network-security-)
- [Cloud Security](#7-cloud-security-)
- [Zero Trust Architecture](#8-zero-trust-architecture-)
- [Supply Chain Security](#9-supply-chain-security-)
- [Secrets Management](#10-secrets-management-)
- [Penetration Testing](#11-penetration-testing-)
- [Security Operations](#12-security-operations-)
- [Incident Response](#13-incident-response-)
- [Compliance & Standards](#14-compliance--standards-)
- [Learning Path](#-learning-path)
- [Related Domains](#-related-domains)
- [Simplest Mental Model](#-simplest-mental-model)

---

## 🎯 Core Security Principles

### CIA Triad
- **Confidentiality**: Data accessible only to authorized parties (encryption, ACLs)
- **Integrity**: Data not tampered with (signatures, checksums, immutable logs)
- **Availability**: Systems accessible when needed (redundancy, DDoS protection)

### Extended Triad (Parkerian Hexad)
Confidentiality + Integrity + Availability + **Possession/Control** + **Authenticity** + **Utility**

### Foundational Principles
- **Least Privilege**: Minimum permissions necessary
- **Defense in Depth**: Multiple layers of security controls
- **Fail Safe**: System fails into secure state
- **Complete Mediation**: Every access checked
- **Economy of Mechanism**: Simpler = more secure
- **Open Design**: Security shouldn't rely on secrecy
- **Separation of Duties**: No single person has all power
- **Least Common Mechanism**: Minimize shared mechanisms

### Security by Design
- **Shift Left**: Security integrated from design phase
- **Secure SDLC**: Threat modeling at design, SAST/DAST in CI/CD
- **Security Champions**: Embedded security advocates in each team

---

## 1. Threat Modeling 🕵️

### STRIDE (Microsoft)
| Threat | Definition | Example |
|--------|------------|---------|
| **S**poofing | Impersonating someone | Fake login page |
| **T**ampering | Modifying data | Altering transaction amount |
| **R**epudiation | Denying action | User claims "I didn't do that" |
| **I**nformation Disclosure | Leaking data | SQL injection exposing PII |
| **D**enial of Service | Disrupting service | DDoS attack |
| **E**levation of Privilege | Gaining unauthorized access | Privilege escalation via bug |

### DREAD (Risk Rating)
- **D**amage Potential
- **R**eproducibility
- **E**xploitability
- **A**ffected Users
- **D**iscoverability

### PASTA (Process for Attack Simulation and Threat Analysis)
7-stage risk-centric methodology: Define objectives → Define technical scope → Application decomposition → Threat analysis → Weakness analysis → Attack modeling → Risk/impact analysis

---

## 2. Cryptography 🔐

### Symmetric Encryption
| Algorithm | Key Size | Block Size | Mode | Status |
|-----------|----------|------------|------|--------|
| AES | 128/192/256 | 128 | ECB/CBC/GCM/CTR | Recommended |
| ChaCha20 | 256 | Stream | Poly1305 (AEAD) | Recommended |
| DES | 56 | 64 | Various | Broken |
| 3DES | 112/168 | 64 | Various | Deprecated |
| Blowfish | 32-448 | 64 | Various | Legacy |

### Modes of Operation
- **ECB**: Deterministic, leaks patterns — never use
- **CBC**: Requires IV, sequential, needs padding
- **CTR**: Counter mode, parallelizable, stream-like
- **GCM** (Galois/Counter): AEAD (auth encryption + integrity), recommended
- **ChaCha20-Poly1305**: AEAD, fast in software, recommended

### Asymmetric Encryption
| Algorithm | Key Size | Use Case | Security Level |
|-----------|----------|----------|----------------|
| RSA | 2048/4096 | Key exchange, signatures | 112-128 bit |
| ECDSA | 256/384 | Signatures (smaller keys) | 128-256 bit |
| Ed25519 | 256 | Signatures (fast, secure) | 128 bit |
| ECDH | 256/384 | Key agreement | 128-256 bit |
| X25519 | 256 | Key agreement (fast) | 128 bit |
| Dilithium | Post-quantum | Signatures | NIST PQC |

### Hash Functions
| Algorithm | Output Size | Status |
|-----------|-------------|--------|
| SHA-256 | 256 bits | Recommended |
| SHA-3 | 224-512 bits | Recommended (newer) |
| BLAKE2b | 512 bits | Recommended |
| bcrypt | Variable | Password hashing |
| Argon2 | Variable | Password hashing (recommended) |
| MD5 | 128 bits | Broken |
| SHA-1 | 160 bits | Deprecated (SHAttered) |

### TLS 1.3
- **Handshake**: 1-RTT (or 0-RTT for resumption)
- **Removed**: RSA key exchange, static DH, CBC mode ciphers
- **Forward Secrecy**: Mandatory (ECDHE/DHE)
- **AEAD only**: AES-GCM, ChaCha20-Poly1305
- **Encrypted handshake**: Entire handshake encrypted after ServerHello
- **0-RTT**: Replayable but fast — use for idempotent data

### Key Management
- **Generation**: Secure random (`/dev/urandom`, hardware RNG)
- **Storage**: HSM, KMS (AWS KMS, HashiCorp Vault, GCP Cloud KMS)
- **Rotation**: Regular key rotation, automatic in KMS
- **Hardware Security Module (HSM)**: Tamper-resistant key storage

---

## 3. Authentication & Authorization 🪪

### OAuth 2.0
- **Roles**: Resource Owner, Client, Authorization Server, Resource Server
- **Grant Types**:
  - Authorization Code (most secure, for web apps)
  - PKCE (Proof Key for Code Exchange, for mobile/SPA)
  - Client Credentials (machine-to-machine)
  - Device Code (smart TVs, CLI tools)
  - Refresh Token (long-lived access)
- **Flow**: Auth Code + PKCE
  ```
  User → Client → Auth Server (login) → Auth Code ← Client
  Client → Auth Server (code + verifier) → Access Token
  Client → Resource Server (token) → Protected Resource
  ```
- **Best practices**: Short-lived tokens, refresh rotation, never embed in URLs

### OpenID Connect (OIDC)
- **Identity layer on top of OAuth 2.0**
- **ID Token**: JWT with user identity claims (`sub`, `email`, `name`)
- **Discovery**: `/.well-known/openid-configuration`
- **UserInfo Endpoint**: Additional claims
- **Providers**: Auth0, Okta, Keycloak, AWS Cognito, Azure AD

### SAML 2.0
- **XML-based**: Security Assertion Markup Language
- **Federated identity**: Single sign-on across domains
- **Components**: Identity Provider (IdP), Service Provider (SP)
- **Flows**: SP-initiated, IdP-initiated
- **vs OIDC**: SAML is XML/heavier, OIDC is JSON/lighter

### Authorization Models
| Model | Description | Example |
|-------|-------------|---------|
| RBAC | Role-Based Access Control | Admin, Editor, Viewer |
| ABAC | Attribute-Based (user, resource, environment) | "Manager can edit docs in their org" |
| ReBAC | Relationship-Based | "Friends of friends can view" |
| PBAC | Policy-Based (OPA, Cedar) | "Any principal can read if resource.public=true" |
| ACL | Access Control Lists | Unix file permissions |

### JWT (JSON Web Token)
- **Structure**: `header.payload.signature`
- **Header**: `{"alg": "RS256", "typ": "JWT"}`
- **Claims**: `iss`, `sub`, `aud`, `exp`, `iat`, custom claims
- **Signing**: HMAC (symmetric) or RSA/ECDSA (asymmetric)
- **Security concerns**: Token leakage, no revocation (use short expiry + refresh)

---

## 4. OWASP Top 10 (2021) 🐛

| Rank | Category | Description |
|------|----------|-------------|
| A01 | Broken Access Control | Users act outside permissions |
| A02 | Cryptographic Failures | Weak encryption, exposed data |
| A03 | Injection | SQL, NoSQL, OS, LDAP injection |
| A04 | Insecure Design | Missing threat modeling |
| A05 | Security Misconfiguration | Default creds, verbose errors |
| A06 | Vulnerable Components | Outdated libraries, CVEs |
| A07 | Auth Failures | Weak passwords, session theft |
| A08 | Data Integrity Failures | Unsigned updates, deserialization |
| A09 | Logging & Monitoring Fail | Invisible breaches |
| A10 | SSRF | Server-side request forgery |

### Prevention by Category
- **Injection**: Parameterized queries, prepared statements, ORM
- **XSS**: Output encoding, CSP headers, `HttpOnly` cookies
- **CSRF**: Anti-CSRF tokens, SameSite cookies, `Origin`/`Referer` validation
- **SSRF**: Allow-list destinations, disable HTTP redirect following, network segmentation

---

## 5. Web Security 🌐

### Same-Origin Policy
- Browser restricts cross-origin reads
- Origin = scheme + host + port

### CORS (Cross-Origin Resource Sharing)
- Server allows cross-origin via headers
- `Access-Control-Allow-Origin`, `Allow-Methods`, `Allow-Credentials`
- Preflight requests for non-simple requests (OPTIONS)

### CSP (Content Security Policy)
- Defense-in-depth against XSS
- `Content-Security-Policy` header: `default-src 'self'`, `script-src`, `style-src`
- Report-only mode: `Content-Security-Policy-Report-Only`

### Session Security
- Secure + HttpOnly + SameSite cookies
- Session rotation (regenerate on login)
- Session timeout (idle + absolute)
- Fingerprinting (User-Agent + IP on server)

---

## 6. Network Security 🌐

### Firewalls
- **Packet Filter**: Stateless ACL based on IP/port
- **Stateful**: Tracks connection state (conntrack)
- **Next-Gen** (NGFW): Application-layer inspection, IPS, SSL inspection

### IDS/IPS
- **Signature-based**: Known attack patterns (Snort, Suricata)
- **Anomaly-based**: ML detection of abnormal traffic
- **Network vs Host**: NIDS (network tap) vs HIDS (host agents)

### VPNs
- **IPsec**: Network-layer encryption (tunnel/transport mode)
- **WireGuard**: Modern, simpler, in-kernel since Linux 5.6
- **OpenVPN**: TLS-based, widely compatible

---

## 7. Cloud Security ☁️

### Shared Responsibility Model
```
┌──────────────────────┬──────────────────────┐
│     SaaS             │     On-Prem          │
│ User: data, config   │ User: everything     │
│ Provider: infra      │                      │
├──────────────────────┤                      │
│     PaaS             │                      │
│ User: app, data      │                      │
│ Provider: runtime    │                      │
├──────────────────────┤                      │
│     IaaS             │                      │
│ User: OS, app, data  │                      │
│ Provider: hypervisor  │                      │
└──────────────────────┴──────────────────────┘
```

### Cloud Security Controls
- **IAM**: Least privilege, roles, policies, service accounts
- **Network Security**: VPC, security groups, NACLs, private subnets
- **Data Encryption**: Server-side (SSE) and client-side encryption
- **Logging**: CloudTrail (AWS), Audit Logs (GCP), Activity Log (Azure)
- **Infrastructure as Code scanning**: Checkov, tfsec, cfn-nag

### CASB (Cloud Access Security Broker)
Visibility, compliance, data security, and threat protection between users and cloud apps.

---

## 8. Zero Trust Architecture 🚫

### Core Tenets (NIST SP 800-207)
1. **Never trust, always verify**
2. Authenticate and authorize every request (not just network perimeter)
3. Least privilege access
4. Assume breach — micro-segmentation, continuous monitoring

### Implementation Pillars
- **Identity**: Strong MFA, continuous authentication
- **Device**: Device health posture check before access
- **Network**: Micro-segmentation, per-request authorization
- **Workload**: Service identity (mTLS in service mesh)
- **Data**: Encryption at rest + in transit, DLP, classification

### Zero Trust Ready Tools
- **BeyondCorp** (Google): Device + user identity-based access
- **Zscaler / Cloudflare Access**: Identity-aware proxy
- **Tailscale / Wireguard**: Mesh VPN with identity-based auth
- **Istio / Linkerd**: mTLS + RBAC in service mesh

---

## 9. Supply Chain Security 📦

### SLSA (Supply-chain Levels for Software Artifacts)
| Level | Requirements |
|-------|-------------|
| SLSA 1 | Build process documented |
| SLSA 2 | Hosted build, signed provenance |
| SLSA 3 | Hermetic build, reproducible |
| SLSA 4 | Two-party review, attested |

### SBOM (Software Bill of Materials)
- **Format**: SPDX, CycloneDX
- **Contents**: All dependencies + versions + licenses
- **Tooling**: `syft`, `trivy`, `dependency-track`
- **Use cases**: Vulnerability scanning, license compliance

### Signing & Verification
- **Cosign**: Container signing, integrated with Sigstore
- **Sigstore**: Free OIDC-based code signing (Fulcio + Rekor + Cosign)
- **in-toto**: Framework for software supply chain integrity

### Dependency Management
- **SCA tools**: Snyk, Dependabot, Renovate, Trivy
- **Dependency confusion**: Verify package source, pin versions
- **Typosquatting**: Package name verification

---

## 10. Secrets Management 🤫

### Where Secrets Live
```yaml
Bad places:
  - Source code / Git history
  - Config files in plaintext
  - Environment variables (visible in /proc)
  - CI/CD pipeline logs

Good places:
  - Vault (HashiCorp)
  - AWS Secrets Manager
  - GCP Secret Manager
  - Azure Key Vault
  - Kubernetes External Secrets
```

### Best Practices
- **Never hardcode** secrets in source code
- **Automated rotation**: Periodic + on-compromise
- **Least privilege**: Service-specific secrets, scoped permissions
- **Audit logging**: Every secret access logged
- **Dynamic secrets**: Ephemeral, time-bound credentials (Vault)
- **Encryption at rest**: KMS-backed encryption
- **Secret scanning**: `git secrets`, `truffleHog`, Gitleaks in CI

---

## 11. Penetration Testing 🎯

### Phases
1. **Reconnaissance**: OSINT, DNS enumeration, subdomain discovery
2. **Scanning**: Nmap, masscan, vulnerability scanners
3. **Exploitation**: Metasploit, Burp Suite, custom exploits
4. **Post-exploitation**: Privilege escalation, lateral movement
5. **Reporting**: Findings, risk rating, remediation

### Web App Testing
- **Burp Suite**: Proxy, scanner, intruder, repeater
- **ZAP**: OWASP Zed Attack Proxy (free, CI-integrated)
- **SQLMap**: Automated SQL injection detection/exploitation

### Infrastructure Testing
- **Nmap**: Port scanning, service detection, NSE scripts
- **CrackMapExec**: Active Directory assessment
- **BloodHound**: AD privilege escalation path visualization

---

## 12. Security Operations 🏢

### SOC (Security Operations Center)
- **Tiers**: T1 (triage), T2 (investigation), T3 (hunting/threat intel)
- **SIEM**: Splunk, ELK, Sentinel, QRadar
- **SOAR**: Automation of incident response (Splunk SOAR, Demisto)
- **Threat Intel**: MITRE ATT&CK, STIX/TAXII

### Security Tools Stack
| Category | Tools |
|----------|-------|
| SAST | SonarQube, Checkmarx, Semgrep, CodeQL |
| DAST | Burp Suite, OWASP ZAP, Acunetix |
| SCA | Snyk, Dependabot, Trivy, Grype |
| Container | Trivy, Clair, Anchore, Falco |
| Cloud | ScoutSuite, Prowler, CloudSploit |
| EDR | CrowdStrike, SentinelOne, Osquery, Wazuh |

---

## 13. Incident Response 🚨

### IR Framework (NIST 800-61)
1. **Preparation**: Runbooks, tools, team, communication channels
2. **Detection & Analysis**: Alert → triage → scope → contain
3. **Containment, Eradication & Recovery**: Isolate, remove, restore
4. **Post-Incident**: Lessons learned, improvements

### Common Incident Types
| Incident | TTP | Mitigation |
|----------|-----|------------|
| Ransomware | Phishing → lateral → encrypt | Backups, EDR, email filtering |
| Data Breach | SQLi/SSRF → exfiltrate | WAF, encryption, monitoring |
| Account Takeover | Cred stuffing / phishing | MFA, rate limiting, anomaly detection |
| DDoS | Volumetric / protocol / app-layer | CDN, rate limiting, scrubbing |
| Insider Threat | Data exfiltration | DLP, UEBA, least privilege |

---

## 14. Compliance & Standards 📋

### Standards & Frameworks
| Standard | Focus | Region |
|----------|-------|--------|
| ISO 27001 | ISMS | Global |
| SOC 2 | Service org controls | US |
| PCI DSS | Payment card data | Global |
| HIPAA | Healthcare data | US |
| GDPR | Personal data protection | EU |
| FedRAMP | Cloud for US gov | US |
| NIST CSF | Cybersecurity framework | US |

### Auditing
- **Control mapping**: Map controls to multiple frameworks
- **Continuous compliance**: Automated evidence collection
- **Penetration testing**: Annual + after major changes

---

## 📚 Learning Path

### Phase 1: Foundations
1. OWASP Top 10 — understand each vulnerability
2. Web security — XSS, CSRF, SQLi hands-on (PortSwigger Labs)
3. Cryptography basics — AES, RSA, TLS handshake
4. Linux security — permissions, PAM, AppArmor

### Phase 2: Tools & Practices
1. Burp Suite / ZAP for web app testing
2. OAuth 2.0 + OIDC implementation
3. HashiCorp Vault for secrets management
4. SAST/DAST integration in CI/CD

### Phase 3: Advanced
1. Threat modeling (STRIDE, PASTA)
2. Zero-trust architecture design
3. Cloud security (AWS Security Hub, GCP Security Command Center)
4. Supply chain security (SLSA + Sigstore)

### Phase 4: Specialization
- **AppSec**: SAST/DAST tooling, code review, security champions
- **CloudSec**: CSPM, CNAPP, IAM policy engineering
- **Crypto**: PKI, HSMs, post-quantum cryptography
- **IR/SOC**: Threat hunting, forensics, malware analysis

---

## 🔗 Related Domains

| Domain | Connection |
|--------|-----------|
| [Networking](../11-networking/README.md) | TLS, firewalls, VPNs, mTLS, network segmentation |
| [Cloud Computing](../05-cloud/README.md) | Shared responsibility, cloud security controls |
| [DevOps](../06-devops/README.md) | DevSecOps, CI/CD security, SAST/DAST |
| [Microservices](../16-microservices/README.md) | mTLS, API security, OAuth2, service mesh security |
| [SRE & Observability](../14-sre-observability/README.md) | Security monitoring, SIEM, threat detection |
| [Software Engineering](../25-software-engineering/README.md) | Secure coding, code review, threat modeling |
| [Distributed Systems](../09-distributed-systems/README.md) | Authentication in distributed systems, consensus |

---

## 🧠 Simplest Mental Model

```
Security = Castle Defense

Castle walls    → Firewall / Network perimeter
Drawbridge      → Authentication (who can enter)
Gatekeeper      → Authorization (who goes where)
Locked chests   → Encryption (data at rest)
Secret language → Encryption (data in transit)
Guard patrols   → IDS/IPS / monitoring
Food taster     → Input validation / sanitization
Moat            → Defense in depth
Spy network     → Threat intelligence
Blueprints      → SBOM / architecture documentation
```

Every layer can be bypassed — that's why you need **defense in depth** (all of them).

---

**Next**: [SRE & Observability](../14-sre-observability/README.md) · [Cloud Computing](../05-cloud/README.md)
