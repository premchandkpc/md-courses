# 🔑 AWS IAM — Complete Deep Dive

**Related**: [S3](../s3/01-s3-deep-dive.md) · [EC2](../ec2/01-ec2-deep-dive.md) · [Lambda](../lambda/01-lambda-deep-dive.md) · [CloudWatch](../cloudwatch/01-cloudwatch-deep-dive.md)

---

## LAYER 1: Beginner's Mental Model 🧠

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Real-World Analogy

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**IAM = Restaurant Access Control:**

- **Root User** = Owner (can do anything, rarely works)
- **IAM Users** = Employees (chef, waiter, cashier each have specific access)
- **Roles** = Job titles (any person in "Chef" role can access kitchen)
- **Policies** = Rules (Chef can use stove, but not cash register)
- **Conditions** = Time-based rules (Access only 9AM-5PM, only from kitchen IP)

```
Request: "Can Waiter access Freezer?"
IAM checks:
1. Is there an EXPLICIT DENY? → DENY (DENY wins)
2. Is there an EXPLICIT ALLOW? → ALLOW
3. Otherwise? → DENY (default deny)
```

### Why IAM Matters

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Without IAM (everyone has full AWS access):**
```
Junior dev gets all credentials → accidentally deletes production DB
Startup costs: $50K/month on unused EC2 → no cost controls
Contractor leaves, forgets access key → exposed credentials
Result: $1M bill, data breach, company fails
```

**With IAM (least privilege):**
```
Junior dev: S3 read + Lambda invoke only
Startup: Cost allocation by department
Contractor: 30-day temporary credentials, auto-revoked
Result: Security, cost control, compliance ✓
```

**Real impact:**
- AWS breach cost: $6.9M average (lost customer trust)
- IAM misconfiguration: #1 AWS security incident
- Least privilege: Reduces blast radius 100x
- Compliance (PCI/HIPAA/SOC2): Requires IAM audit trail

---

## LAYER 4: Production Reality 🚨

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Common IAM Failures

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


| Failure | Symptom | Root Cause | Prevention |
|---------|---------|-----------|-----------|
| **Over-Permissive Policy** | Intern deletes prod S3 | Everyone gets admin role | Use least privilege, service roles |
| **Credential Exposure** | AWS key leaked on GitHub | Dev hardcodes key | Use IAM roles, credential rotation |
| **Forgotten Access Key** | Old employee still has access | No key rotation | Auto-rotate every 90 days |
| **Public S3 Bucket** | Data breach | Bucket policy allows public | Use Access Analyzer, block public |
| **Role Assumption Chain** | Privilege escalation | Trust policy too permissive | Whitelist specific principals |
| **Cross-Account Access Broken** | Legitimate access fails | Wrong ARN format | Test cross-account access |

### Real AWS Incident: Capital One Data Breach (2019)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Problem:** 100M customer records exposed due to IAM misconfiguration.

```
Timeline:
- Attacker exploits WAF vulnerability
- Gains access to EC2 instance
- Discovers overly permissive IAM role
- Role can read all S3 buckets across account
- Downloads 100M customer records
- Total damage: $80M settlement, reputation damage

Root cause: EC2 role had:
  "Effect": "Allow",
  "Action": "s3:*",
  "Resource": "*"
Instead of specific bucket + specific actions
```

**Lesson:** Every principal should have minimal permissions needed.

---

## Interview Questions 💼

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Level 1: Junior

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Q: What's the difference between users and roles?**

A: Users = individual identities with long-term credentials. Roles = temporary credentials for services/people, no password.

```
Users: "alice@company.com" with password + access key
Roles: EC2 instance assumes role, gets temporary credentials (1 hour)
```

**Q: What's the principal of least privilege?**

A: Give each identity only minimum permissions needed. If need S3 read only, don't give admin.

### Level 2: Intermediate

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Q: Design IAM for a startup with 10 engineers, multiple AWS accounts, and CI/CD.**

A:
```
- Dev account: Engineers full access (dev-only)
- Staging: Limited permissions (no delete)
- Prod: Admin on-call only, MFA required
- CI/CD: Service role with specific actions (deploy only)
- Audit: Read-only role for compliance
```

**Q: How would you detect IAM over-permissions?**

A: Use AWS Access Analyzer. It finds all public/cross-account access and suggests least privilege.

### Level 3: Senior

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Q: Design cross-account access for multi-tenant SaaS.**

A:
```
Each customer = separate AWS account
Central account = billing + audit
Customer assume role in central account
Role has:
  "Principal": "arn:aws:iam::customer-account:root"
  "Action": "sts:AssumeRole"
  "Condition": {
    "StringEquals": {"sts:ExternalId": "unique-customer-id"}
  }
```

---

## Production Story: AWS Lambda Over-Permissions

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Challenge:** Lambda function invoked by API Gateway had admin access (bad).

```python
# OLD: Lambda had AdministratorAccess role
# Could delete databases, instances, data

# NEW: Least privilege approach
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem", "dynamodb:PutItem"],
      "Resource": "arn:aws:dynamodb:*:*:table/events"
    },
    {
      "Effect": "Allow",
      "Action": ["logs:CreateLogGroup", "logs:CreateLogStream"],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

**Result:** If Lambda compromised, attacker only has DynamoDB + CloudWatch access (not full AWS).

---

## Summary

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


IAM fundamentals:

1. **Beginner** — Users/roles/policies, why it matters
2. **Intermediate** — Policy evaluation, conditions, trust policies (this file covers)
3. **Advanced** — Cross-account, SCPs, permission boundaries
4. **Production** — Breach patterns, least privilege enforcement
5. **Staff** — Multi-account strategy, compliance, cost allocation

**Next:** Enable Access Analyzer, audit existing roles, reduce permissions 50%.

---



```mermaid
graph LR
    USER["IAM User<br/>(Long-term Creds)"] --> GRP["IAM Group"]
    GRP --> POL["IAM Policy<br/>(JSON doc)"]
    ROLE["IAM Role<br/>(Trust Policy)"] --> POL
    POL --> EFFECT["Effect<br/>(Allow / Deny)"]
    POL --> ACTION["Action<br/>(s3:GetObject)"]
    POL --> RESOURCE["Resource<br/>(arn:aws:s3:::bucket/*)"]
    POL --> COND["Condition<br/>(IpAddress / MFA)"]
    USER --> ACCESS["Access Key +<br/>Secret Key"]
    ROLE --> STS["STS<br/>AssumeRole"]
    STS --> TEMP["Temporary<br/>Credentials"]
    style USER fill:#4a8bc2
    style GRP fill:#2d5a7b
    style POL fill:#3a7ca5
    style ROLE fill:#c73e1d
    style EFFECT fill:#3fb950
    style ACTION fill:#e8912e
    style RESOURCE fill:#6f42c1
    style COND fill:#e8912e
    style ACCESS fill:#2d5a7b
    style STS fill:#3a7ca5
    style TEMP fill:#3fb950
```

## Table of Contents

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


- [The Big Picture](#-the-big-picture)
- [1. Users](#1-users)
- [2. Groups](#2-groups)
- [3. Roles](#3-roles)
- [4. Policies (Managed vs Inline)](#4-policies-managed-vs-inline)
- [5. Trust Policies](#5-trust-policies)
- [6. Service-Linked Roles](#6-service-linked-roles)
- [7. Permission Boundaries](#7-permission-boundaries)
- [8. Access Analyzer](#8-access-analyzer)
- [9. IAM Best Practices](#9-iam-best-practices)
- [10. Least Privilege](#10-least-privilege)
- [Simplest Mental Model](#-simplest-mental-model)

---

## 🧭 The Big Picture

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
                    ┌─────────────────────────┐
                    │ AWS Identity & Access   │
                    │ Management (IAM)         │
                    ├─────────────────────────┤
                    │ Who can do WHAT          │
                    │ on which AWS resources   │
                    └─────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
      ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
      │  Identities  │ │  Policies   │ │  Analysis    │
      │  • Users    │ │  • Managed  │ │  • Access    │
      │  • Groups   │ │  • Inline   │ │    Analyzer  │
      │  • Roles    │ │  • Resource │ │  • Credential │
      │             │ │  • Boundary │ │    Report    │
      └──────────────┘ └──────────────┘ └──────────────┘
```

### Policy Evaluation Logic

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
┌─────────────────────────────────────────────────────────┐
│          IAM Policy Evaluation Logic                     │
│                                                          │
│  Request: Principal=A, Action=s3:GetObject, Resource=…   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │  1. Allow by default? → No (Implicit Deny)        │    │
│  │  2. Any explicit Deny?    → Deny (DENY WINS)      │    │
│  │  3. Any explicit Allow?   → Allow                  │    │
│  │  4. Otherwise             → Implicit Deny          │    │
│  └──────────────────────────────────────────────────┘    │
│                    │                                      │
│  Explicit Deny > Explicit Allow > Default Deny            │
└─────────────────────────────────────────────────────────┘
```

---

## 1. Users

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### User Types

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
┌─────────────────────────────────────────────────────────┐
│                    IAM Users                             │
├─────────────────────────────────────────────────────────┤
│  Root User (account owner)                              │
│  • Created with AWS account                             │
│  • Unrestricted access                                  │
│  • ⚠️ Only use for account setup                        │
│  • Enable MFA immediately                               │
│  • No access keys (unless emergency)                    │
├─────────────────────────────────────────────────────────┤
│  IAM Users (individuals)                                │
│  • Created within account                               │
│  • Long-term credentials (password + access keys)       │
│  • Best for: employees requiring AWS Console access     │
│  • 5000 users max per account (default)                 │
├─────────────────────────────────────────────────────────┤
│  Federated Users (external identity)                    │
│  • Authenticated via corporate IdP (AD, SAML, OIDC)    │
│  • No long-term AWS credentials                         │
│  • Temporary credentials via STS AssumeRole             │
│  • Best for: SSO integration with company directory     │
└─────────────────────────────────────────────────────────┘
```

### User Credentials

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
User Authentication Methods:
┌──────────────────────────────────────────────┐
│ Console Password (Interactive)               │
│  • Custom password policy                    │
│  • MFA strongly recommended                  │
│  • Password rotation policy                  │
├──────────────────────────────────────────────┤
│ Access Keys (Programmatic)                   │
│  • Access Key ID: AKIAIOSFODNN7EXAMPLE       │
│  • Secret Access Key: wJalrXUtnFEMI/K7MDENG │
│  • Rotate every 90 days                     │
│  • MAX 2 per user (active)                  │
├──────────────────────────────────────────────┤
│ SSH Keys (CodeCommit)                        │
│  • Upload SSH public key                     │
│  • Use for Git over SSH to CodeCommit        │
└──────────────────────────────────────────────┘
```

---

## 2. Groups

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Group Benefits

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
Users ──> Groups ──> Policies

Before Groups:
  ┌──────────┐   ┌──────────┐
  │ User A   │   │ Policy 1 │
  ├──────────┤   ├──────────┤
  │ User B   │   │ Policy 2 │
  ├──────────┤   ├──────────┤
  │ User C   │   │ Policy 3 │
  └──────────┘   └──────────┘
  (Each user has policies attached individually)

After Groups:
  ┌──────────┐   ┌───────────┐   ┌──────────┐
  │ User A   │   │ Developers│   │ Policy 1 │
  ├──────────┤   │ Group     ├──►├──────────┤
  │ User B   │──►│           │   │ Policy 2 │
  ├──────────┤   └───────────┘   └──────────┘
  │ User C   │
  └──────────┘
```

### Group Limitations

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


| Limitation | Value |
|------------|-------|
| Groups per account | 300 |
| Users per group | Unlimited (soft limit) |
| Groups per user | 10 |
| Policies per group | 20 (managed) + inline |
| Nested groups | ❌ Not supported |
| Group as Principal in policy | ❌ Not allowed (use role) |

---

## 3. Roles

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Role vs User

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
IAM User                              IAM Role
┌─────────────────┐                  ┌─────────────────┐
│ Long-term creds  │                  │ Temporary creds  │
│ Password + Keys  │                  │ STS tokens       │
│ Direct identity  │                  │ Assumed identity │
│ Person or app    │                  │ Service, app, or │
│                  │                  │ federated user   │
└─────────────────┘                  └─────────────────┘
WHO you are                          WHAT you can be
```

### Common Role Types

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
┌─────────────────────────────────────────────┐
│ AWS Service Roles:                          │
│                                             │
│ EC2 Role (EC2 → S3, DynamoDB, etc.)         │
│   ┌────────┐   ┌────────┐   ┌──────────┐    │
│   │ EC2    │──►│ EC2    │──►│ S3 Read  │    │
│   │Instance│   │ Role   │   │ Policy   │    │
│   └────────┘   └────────┘   └──────────┘    │
│                                             │
│ Lambda Role (Lambda → DynamoDB, SQS, etc.)   │
│   ┌────────┐   ┌────────┐   ┌──────────┐    │
│   │ Lambda │──►│ Lambda │──►│ DynamoDB │    │
│   │Function│   │ Role   │   │ Policy   │    │
│   └────────┘   └────────┘   └──────────┘    │
│                                             │
│ Cross-Account Role (Account A → Account B)  │
│   ┌──────────┐  AssumeRole  ┌──────────┐    │
│   │Account A │─────────────►│Account B │    │
│   │(trusted) │  STS token   │(trusting)│    │
│   └──────────┘              └──────────┘    │
└─────────────────────────────────────────────┘
```

---

## 4. Policies (Managed vs Inline)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Policy Types

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
AWS Managed Policies:
  ┌────────────────────────────────────┐
  │ AWS creates and maintains          │
  │ • AdministratorAccess              │
  │ • ReadOnlyAccess                   │
  │ • AmazonS3FullAccess               │
  │ • AWSLambda_FullAccess             │
  │ • AmazonEC2ReadOnlyAccess           │
  │                                    │
  │ Pros: Auto-updated by AWS          │
  │ Cons: Very permissive              │
  └────────────────────────────────────┘

Customer Managed Policies:
  ┌────────────────────────────────────┐
  │ You create and maintain            │
  │ • Least-privilege for your org     │
  │ • Reusable across multiple users   │
  │ • Version controlled (5 versions) │
  │                                    │
  │ Pros: Custom, reusable             │
  │ Cons: You maintain them           │
  └────────────────────────────────────┘

Inline Policies:
  ┌────────────────────────────────────┐
  │ Embedded directly on user/group    │
  │ • Unique to that principal         │
  │ • No ARN (not reusable)            │
  │ • Deleted when principal deleted   │
  │                                    │
  │ Pros: Tightly coupled, explicit    │
  │ Cons: Not reusable, harder to audit│
  └────────────────────────────────────┘
```

### Policy Document Structure

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "VisualEditor1",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-app-bucket",
        "arn:aws:s3:::my-app-bucket/*"
      ],
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": "203.0.113.0/24"
        }
      }
    }
  ]
}
```

### Policy Elements

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


| Element | Required | Description |
|---------|----------|-------------|
| Version | Yes | Policy language version (`2012-10-17`) |
| Statement | Yes | One or more statements |
| Sid | No | Optional identifier for the statement |
| Effect | Yes | `Allow` or `Deny` |
| Principal | No | Who the policy applies to (only in resource-based policies) |
| Action | Yes | AWS service actions (e.g., `s3:GetObject`) |
| Resource | Yes | ARN of resources the action applies to |
| Condition | No | When the policy is in effect |

---

## 5. Trust Policies

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Trust Policy Structure

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Example: Cross-Account Trust

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
Account A (123456789012)
┌──────────────────────────────┐
│ Role: DataReadRole            │
│                              │
│ Trust Policy:                 │
│ {                            │
│   "Effect": "Allow",         │
│   "Principal": {             │─────┐
│     "AWS": "arn:aws:iam::    │     │
│       098765432109:root"     │     │
│   },                         │     │
│   "Action": "sts:AssumeRole" │     │
│ }                            │     │
│                              │     │
│ Permissions Policy:          │     │
│ { "Effect": "Allow",         │     │
│   "Action": "s3:GetObject",  │     │
│   "Resource": "arn:aws:s3::: │     │
│     shared-bucket/*" }       │     │
└──────────────────────────────┘     │
                                     │
Account B (098765432109)             │
┌──────────────────────────────┐     │
│ IAM User: data-analyst       │◄────┘
│ Can assume DataReadRole     │
│ via:                         │
│ aws sts assume-role          │
│   --role-arn "arn:aws:iam:: │
│     123456789012:role/       │
│     DataReadRole"            │
│   --role-session-name "job1"│
└──────────────────────────────┘
```

### AssumeRole Flow

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
User in Account B
        │
        ▼
┌─────────────────────────┐
│ Call sts:AssumeRole      │
│ Target: Account A role   │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ Account A validates:    │
│ • Trust policy allows   │
│   Account B's principal │
│ • User has iam:PassRole │
│   permission            │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ STS returns temporary   │
│ credentials:            │
│ • AccessKeyId           │
│ • SecretAccessKey       │
│ • SessionToken          │
│ • Expiration (1h max)   │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ User makes requests     │
│ with temporary creds    │
│ (scoped by permissions  │
│  of the assumed role)   │
└─────────────────────────┘
```

---

## 6. Service-Linked Roles

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### What They Are

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
┌─────────────────────────────────────────────┐
│ Service-Linked Roles                        │
│                                             │
│ Pre-defined roles created by AWS services   │
│ that include all permissions the service    │
│ needs to call other AWS services on         │
│ your behalf.                                │
│                                             │
│ Examples:                                   │
│ • AWSServiceRoleForAutoScaling              │
│ • AWSServiceRoleForRDS                      │
│ • AWSServiceRoleForEC2Spot                  │
│ • AWSServiceRoleForLambda                   │
│                                             │
│ You cannot delete while the service         │
│ is using the role.                          │
│ Trust policy is fixed (service principal).  │
└─────────────────────────────────────────────┘
```

### Service-Linked vs Custom Role

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


| Aspect | Service-Linked | Custom Role |
|--------|---------------|-------------|
| Creation | AWS creates (or you with specified service) | You create manually |
| Trust policy | Fixed — only the service can assume it | You define |
| Permissions | Pre-defined by AWS | You define |
| Deletion | Blocked while service uses it | You can delete anytime |
| Updates | AWS updates automatically | You manage |
| Use case | EC2 Auto Scaling, RDS, Lambda VPC | Custom application needs |

---

## 7. Permission Boundaries

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### How Boundaries Work

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
Permission Boundary Model:

┌─────────────────────────────────────────────┐
│          Maximum Effective Permission        │
│                                             │
│  ┌───────────────────────────────────────┐   │
│  │       Permission Boundary             │   │
│  │       (maximum allowed permissions)   │   │
│  │                                       │   │
│  │  ┌─────────────────────────────┐      │   │
│  │  │  Identity-Based Policy      │      │   │   Effective =
│  │  │  (what role/user CAN do)   │      │   │   Intersection of
│  │  └─────────────────────────────┘      │   │   boundary + policy
│  └───────────────────────────────────────┘   │
└─────────────────────────────────────────────┘

User has:
  • Permission boundary: "Can only use S3 and EC2"
  • Identity policy: "Full admin access"
  → Effective: Only S3 and EC2 (boundary restricts)
```

### Use Case: Delegated Admin

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```json
// Permission boundary for delegated admins
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateUser",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PutUserPolicy"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Deny",
      "Action": "iam:*",
      "Resource": "arn:aws:iam::*:role/admin-*"
    }
  ]
}

// Delegated admin can create users and roles
// but cannot create/modify roles with "admin-" prefix
```

---

## 8. Access Analyzer

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Finding Analysis

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
┌─────────────────────────────────────────────┐
│ IAM Access Analyzer                         │
│                                             │
│ Continuously analyzes resource-based        │
│ policies to identify resources shared       │
│ with external entities.                    │
│                                             │
│ Findings detected:                          │
│ • S3 bucket with public access              │
│ • KMS key shared with external account      │
│ • IAM role with cross-account trust         │
│ • SQS queue with public policy              │
│ • Lambda function policy                     │
│ • Secrets Manager secret policy             │
│ • SNS topic policy                          │
└─────────────────────────────────────────────┘
```

### Policy Validation

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
┌─────────────────────────────────────────────┐
│ IAM Access Analyzer — Policy Validation     │
│                                             │
│ Checks:                                     │
│ • Security: overly permissive policies      │
│   "All principals? All actions? All         │
│    resources?" → WARNING                    │
│ • Errors: invalid JSON, missing elements    │
│ • Warnings: best practice violations        │
│ • Suggestions: unused actions, replacements │
│                                             │
│ Example warning:                            │
│ "This policy grants full admin access —     │
│  consider scoping to specific actions"      │
└─────────────────────────────────────────────┘
```

### Unused Access Analysis

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```awscli
# Generate credential report
aws iam generate-credential-report
aws iam get-credential-report

# List unused roles
aws iam list-roles --query 'Roles[?RoleLastUsed==null].[RoleName]'

# List unused access keys
aws iam list-access-keys --user-name my-user
```

---

## 9. IAM Best Practices

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Security Checklist

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
┌──────────────────────────────────────────────┐
│ IAM Security Checklist                        │
├──────────────────────────────────────────────┤
│                                              │
│ ☐  Lock down root user (MFA, no keys)        │
│ ☐  Use IAM roles for EC2/Lambda (not keys)   │
│ ☐  Enable MFA for all users                  │
│ ☐  Rotate access keys every 90 days          │
│ ☐  Use groups — don't attach policies to users│
│ ☐  Apply least privilege (start small)       │
│ ☐  Use permission boundaries for delegated   │
│     administration                            │
│ ☐  Enable CloudTrail for IAM events          │
│ ☐  Use IAM Access Analyzer regularly         │
│ ☐  Remove unused users, roles, and keys      │
│ ☐  Use conditions for extra security         │
│     (SourceIp, MFA, VPC endpoint)            │
│ ☐  Use AWS Organizations SCPs for guardrails │
│ ☐  Avoid inline policies (use managed)       │
│ ☐  Use PassRole wisely (require specific     │
│     resource ARN)                             │
└──────────────────────────────────────────────┘
```

### Common Condition Keys

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```json
{
  "Condition": {
    "IpAddress": {
      "aws:SourceIp": "10.0.0.0/8"
    },
    "Bool": {
      "aws:MultiFactorAuthPresent": "true"
    },
    "StringEquals": {
      "aws:RequestedRegion": "us-east-1"
    },
    "ArnEquals": {
      "ec2:InstanceType": "t3.micro"
    }
  }
}
```

### PassRole Guidance

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```json
// ❌ BAD — PassRole to any resource (dangerous)
{
  "Effect": "Allow",
  "Action": "iam:PassRole",
  "Resource": "*"
}

// ✅ GOOD — Restrict PassRole to specific role
{
  "Effect": "Allow",
  "Action": "iam:PassRole",
  "Resource": "arn:aws:iam::123456789012:role/ec2-app-role"
}
```

---

## 10. Least Privilege

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Strategy

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
Least Privilege Implementation:

1. Start with Deny-All
2. Add Allow for specific actions
3. Scope to specific resources
4. Add conditions
5. Review and refine

Example Evolution:

Step 1: Too Permissive
  "Action": "s3:*",
  "Resource": "*"

Step 2: Service-Scoped
  "Action": "s3:GetObject",
  "Resource": "*"

Step 3: Resource-Scoped
  "Action": "s3:GetObject",
  "Resource": "arn:aws:s3:::my-bucket/*"

Step 4: Condition-Scoped
  "Action": "s3:GetObject",
  "Resource": "arn:aws:s3:::my-bucket/*",
  "Condition": {
    "IpAddress": {
      "aws:SourceIp": "10.0.0.0/8"
    }
  }
```

### Least Privilege by Service

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


| Service | Minimum Actions |
|---------|----------------|
| **EC2 → S3** | `s3:GetObject`, `s3:ListBucket` on specific bucket |
| **Lambda → DynamoDB** | `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:UpdateItem` |
| **Lambda → SQS** | `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:GetQueueAttributes` |
| **Lambda → SNS** | `sns:Publish` on specific topic |
| **EC2 → SSM** | `ssm:GetParameter`, `kms:Decrypt` on specific parameter |

### IAM Policy Simulator

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
┌─────────────────────────────────────────────┐
│ IAM Policy Simulator                        │
│                                             │
│ Test policies before applying:              │
│                                             │
│ 1. Select user/group/role                   │
│ 2. Select service (S3, EC2, etc.)          │
│ 3. Select actions                           │
│ 4. Add conditions                           │
│ 5. Simulate → Allow/Deny/Implicit Deny     │
│                                             │
│ Results show exactly which policy           │
│ granted or denied access                    │
└─────────────────────────────────────────────┘
```

---

## 🧠 Simplest Mental Model

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```text
IAM USER        =  An employee badge. Identifies WHO you are.
                   Has a photo (password) and a card key (access keys).

IAM GROUP       =  A department team. Marketing team gets
                   "marketing badge", engineers get "dev badge".
                   Everyone in the team has the same access.

IAM ROLE        =  A temp badge for a specific task.
                   "Visitor" badge → can enter lobby only.
                   "Contractor" badge → can enter floor 3.
                   Badge expires after the task.

POLICY          =  A rulebook that says what each badge can do.
   Managed      =  Pre-written rulebook by AWS or your company.
   Inline       =  A rule written directly on one badge.

TRUST POLICY    =  "Who is allowed to wear this temp badge?"
                   Tells the system: EC2 instances can wear
                   the "S3 Reader" badge.

PERMISSION      =  A fence around a playground. The kid (user)
BOUNDARY          can't go beyond the fence no matter what
                  rules are written on their badge.

ACCESS          =  A security camera + auditor that watches
ANALYZER          all doors and reports which ones are unlocked
                  to the public.

LEAST           =  Give a valet only the car key, not the
PRIVILEGE         house key, safe key, and mail key too.
```

---

**Next**: [ECS Deep Dive](../ecs/01-ecs-deep-dive.md) — Container orchestration
