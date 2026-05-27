# 🔐 IAM Advanced Patterns — Complete Deep Dive

## Table of Contents
- [Permission Boundaries vs SCP vs Service Control](#permission-boundaries-vs-scp-vs-service-control)
- [Resource-Based vs Identity-Based Policies](#resource-based-vs-identity-based-policies)
- [Policy Evaluation Logic](#policy-evaluation-logic)
- [IAM Roles for EC2/Lambda/ECS](#iam-roles-for-ec2lambdaecs)
- [Cross-Account Role Assumption](#cross-account-role-assumption)
- [Role Chaining](#role-chaining)
- [Session Tags](#session-tags)
- [ABAC (Attribute-Based Access Control)](#abac-attribute-based-access-control)
- [Access Analyzer](#access-analyzer)
- [IAM Identity Center (SSO)](#iam-identity-center-sso)
- [Policy Conditions Deep Dive](#policy-conditions-deep-dive)
- [IAM Roles Anywhere](#iam-roles-anywhere)
- [Service-Linked Roles](#service-linked-roles)
- [Simplest Mental Model](#simplest-mental-model)

---

## Permission Boundaries vs SCP vs Service Control

```text
AWS Organization Account:
┌────────────────────────────────────────────┐
│  SCP (Service Control Policy)              │
│  "Maximum allowed for ALL principals"      │
│  │                                         │
│  │  ┌─────────────────────────────────┐   │
│  │  │  Permission Boundary            │   │
│  │  │  "Max for a specific principal" │   │
│  │  │  │                             │   │
│  │  │  ┌───────────────────────┐     │   │
│  │  │  │ Identity Policy      │     │   │
│  │  │  │ "What CAN do"        │     │   │
│  │  │  └───────────────────────┘     │   │
│  │  └─────────────────────────────────┘   │
│  └────────────────────────────────────────┘
```

| Layer | Scope | Purpose |
|-------|-------|---------|
| **SCP** | Organization/OU | Guardrails. Cannot grant, only restrict |
| **Permission Boundary** | User/Role | Max permissions boundary |
| **Identity Policy** | User/Role/Group | What principal can actually do |
| **Session Policy** | STS session | Temporary restrict assumed role |

**Effective permission** = Intersection of SCP ∩ Boundary ∩ Identity Policy ∩ Session Policy.

---

## Resource-Based vs Identity-Based Policies

```text
Identity-Based (attached to principal):
  IAM User/Role → "Allow s3:GetObject on bucket X"
  Policy travels with principal.

Resource-Based (attached to resource):
  S3 Bucket Policy → "Allow arn:aws:iam::123:role/DataAccess"
  Policy travels with resource. Cross-account without trust policy.
```

| Aspect | Identity-Based | Resource-Based |
|--------|---------------|----------------|
| Attached to | User, group, role | Resource (S3, SQS, KMS, Lambda) |
| Controls | What principal can do | Who can access resource |
| Cross-account | Needs trust policy | Works directly (specify ARN) |
| Principal element | Not required (implied) | Required |

**Use identity-based** for EC2/Lambda/ECS roles. **Use resource-based** when resource owner controls access without IAM users in their account.

---

## Policy Evaluation Logic

```text
1. Is there a DENY? (SCP, boundary, identity, session, resource)
   YES → DENY (explicit deny always wins)
   NO  → Continue

2. Is there an ALLOW? (any policy anywhere)
   YES → ALLOW
   NO  → Default Deny (implicit deny)

Order: SCP → Resource-Based → Permission Boundary →
       Identity Policy → Session Policy → DENY
```

**Key rule**: An explicit `Deny` in ANY policy overrides any number of `Allow` statements.

---

## IAM Roles for EC2/Lambda/ECS

| Service | Trust Principal | How Credentials Work |
|---------|----------------|---------------------|
| EC2 | `ec2.amazonaws.com` | Instance profile → metadata endpoint (~6h rotation) |
| Lambda | `lambda.amazonaws.com` | Execution role specified at creation |
| ECS Task | `ecs-tasks.amazonaws.com` | Task role (separate from execution role) |
| ECS Execution | `ecs-tasks.amazonaws.com` | Image pull, log shipping |

---

## Cross-Account Role Assumption

```text
Account A ──sts:AssumeRole──► Account B's Role (temp creds returned)

IAM User in Acct A has policy allowing sts:AssumeRole on Role in Acct B.
Role in Acct B has trust policy allowing Acct A's principal.
```

```json
{
  "Effect": "Allow",
  "Principal": { "AWS": "arn:aws:iam::123456789012:root" },
  "Action": "sts:AssumeRole",
  "Condition": { "Bool": { "aws:MultiFactorAuthPresent": "true" } }
}
```

### Common Patterns: Central audit (one security account), central network (TGW management), data lake (prod reads from sources).

---

## Role Chaining

User → Role A → Role B. Max 1 hop. 1-hour sessions. Don't chain — call `sts:AssumeRole` directly on the target role instead.

---

## Session Tags

Tags propagated to assumed session for ABAC.

```awscli
aws sts assume-role --role-arn "arn:aws:iam::123:role/ProjectRole" \
  --tags Key=Project,Value=ProjectX --transitive-tag-keys Project
```

**Use cases**: Cost allocation, environment gating, temporary elevated access.

---

## ABAC (Attribute-Based Access Control)

```text
RBAC: Policy references ARNs → update per new resource.
ABAC: Policy uses tags (resource tag = principal tag) → automatic.

{
  "Effect": "Allow",
  "Action": "ec2:StartInstances",
  "Resource": "arn:aws:ec2:*:*:instance/*",
  "Condition": {
    "StringEquals": {
      "ec2:ResourceTag/Environment": "${aws:PrincipalTag/Environment}"
    }
  }
}
```

| Aspect | RBAC | ABAC |
|--------|------|------|
| Policy count | Many (per resource set) | Few (attribute-based) |
| Scalability | Manual per resource | Automatic (tags) |
| Use case | Static environments | Dynamic, multi-tenant |

---

## Access Analyzer

```text
External Access Findings: S3 bucket → external account → HIGH risk
Unused Access Findings: Role unused 90 days, permission never used
```

**Zones of trust**: Current account (trusted), same Organization (trusted), external accounts (findings).

---

## IAM Identity Center (SSO)

Centralized access across accounts. Identity source (AWS/AD/Okta) → Permission Sets → Account assignments.

| Aspect | Permission Set | IAM Role |
|--------|---------------|----------|
| Created by | SSO auto-creates | Manual |
| Assignment | SSO user/group → account | Manual trust policy |
| Session | Configurable 1-12h | 1h default |
| MFA | Integrated with IdP | Separate condition |

---

## Policy Conditions Deep Dive

```text
Common Conditions:
  aws:SourceIp          — "Only from office IP"
  aws:SourceVpce       — "Only through VPC Endpoint"
  aws:RequestedRegion   — "Lock to us-east-1"
  aws:MultiFactorAuth   — "Require MFA"
  aws:PrincipalOrgID    — "Only from my org"
  ec2:InstanceType      — "Allow only t3.micro"
  s3:Prefix             — "Access to /prefix/*"
```

```json
// Source IP restriction
{ "Effect": "Deny", "Action": "*", "Resource": "*",
  "Condition": { "NotIpAddress": { "aws:SourceIp": ["203.0.113.0/24", "10.0.0.0/8"] } } }

// VPC Endpoint only
{ "Effect": "Allow", "Action": "s3:*", "Resource": "*",
  "Condition": { "StringEquals": { "aws:SourceVpce": "vpce-123abc" } } }

// Organization restriction
{ "Effect": "Deny", "Action": "s3:PutBucketPolicy", "Resource": "*",
  "Condition": { "StringNotEquals": { "aws:PrincipalOrgID": "o-abc123" } } }
```

| Type | Example |
|------|---------|
| `StringEquals` | `SourceVpce: vpce-123` |
| `IpAddress` | `SourceIp: 10.0.0.0/8` |
| `Bool` | `MultiFactorAuthPresent: true` |
| `ArnEquals` | `ec2:InstanceType: t3.micro` |

---

## IAM Roles Anywhere

Temporary AWS credentials for external servers (on-prem, other clouds) via X.509 certificates. Trust anchor (root CA) → profile (links IAM role) → `aws_signing_helper` returns temp creds.

---

## Service-Linked Roles

Pre-built IAM roles for AWS services (fixed trust policy, auto-updated permissions). Examples: RDS (Multi-AZ), Auto Scaling (lifecycle hooks), Lambda (VPC functions), EKS (cluster creation). Auto-created when feature enabled. Deleted only when no resources remain.

---

## Simplest Mental Model

```text
PERMISSION       =  Maximum spending limit on a credit card.
BOUNDARY            No matter how rich, card won't work above it.

SCP              =  Company policy: "No one can buy yachts."
                   Even the CEO cannot bypass this.

IDENTITY POLICY  =  Your personal card limit.
                   What you are individually authorized.

RESOURCE POLICY  =  Store policy on who can enter.
                   "Employees only after 9pm."

CROSS-ACCOUNT    =  Borrowing a friend's Costco card.
ROLE                Use their membership, expires after shopping.

ABAC             =  "Only files with YOUR name on them."
                   Tag-based, not identity-based.

IAM IDENTITY     =  One badge for 10 offices. Access all
CENTER              offices you are authorized for.

ROLES ANYWHERE   =  Badge dispenser for remote workers.
                   Cert verifies ID, badge expires.

CONDITIONS       =  "Only from office WiFi" (SourceIp),
                   "only with badge" (MFA).

SERVICE-LINKED   =  Pre-configured uniform for each
ROLE                service (RDS, Lambda). Tailored fit.
```


---

## Code Examples

```python
# Example implementation
# [Add language-specific code demonstrating core concept]
pass
```

---

## Common Failure Modes

**Problem**: [Key issue in production]

**Root cause**: [Why it happens]

**Solution**: [How to fix]

---

## Interview Questions

### Q1: [Core concept question]

**Answer**: [Detailed explanation with trade-offs]

### Q2: [Design/architecture question]

**Answer**: [Best practices and reasoning]
