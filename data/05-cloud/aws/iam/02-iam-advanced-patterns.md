# 🔐 IAM Advanced Patterns — Complete Deep Dive



```mermaid
graph LR
    PB["Permission<br/>Boundary"] --> USER["IAM User<br/>/ Role"]
    SCP["SCP<br/>(AWS Organizations)"] --> ACC["AWS Account"]
    ACC --> PB
    RB["Resource-Based<br/>Policy"] --> S3["S3 Bucket<br/>Policy"]
    IB["Identity-Based<br/>Policy"] --> USER
    POL_EVAL["Policy Evaluation<br/>Logic"] --> DENY["Explicit Deny<br/>(Wins)"]
    POL_EVAL --> ALLOW["Allow<br/>(OR across policies)"]
    POL_EVAL --> DEFAULT["Default Deny<br/>(Implicit)"]
    ABAC["ABAC<br/>(Tags)" --> COND_CK["Condition Key<br/>(aws:ResourceTag)"]
    CROSS["Cross-Account<br/>Role"] --> TRUST["Trust Policy<br/>(Source Account)"]
    style PB fill:#4a8bc2
    style USER fill:#2d5a7b
    style SCP fill:#c73e1d
    style ACC fill:#3a7ca5
    style RB fill:#e8912e
    style S3 fill:#6f42c1
    style IB fill:#3fb950
    style POL_EVAL fill:#3a7ca5
    style DENY fill:#c73e1d
    style ALLOW fill:#3fb950
    style DEFAULT fill:#e8912e
    style ABAC fill:#2d5a7b
    style CROSS fill:#6f42c1
    style TRUST fill:#e8912e
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


| Service | Trust Principal | How Credentials Work |
|---------|----------------|---------------------|
| EC2 | `ec2.amazonaws.com` | Instance profile → metadata endpoint (~6h rotation) |
| Lambda | `lambda.amazonaws.com` | Execution role specified at creation |
| ECS Task | `ecs-tasks.amazonaws.com` | Task role (separate from execution role) |
| ECS Execution | `ecs-tasks.amazonaws.com` | Image pull, log shipping |

---

## Cross-Account Role Assumption

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


---

## Role Chaining

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


User → Role A → Role B. Max 1 hop. 1-hour sessions. Don't chain — call `sts:AssumeRole` directly on the target role instead.

---

## Session Tags

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


Tags propagated to assumed session for ABAC.

```awscli
aws sts assume-role --role-arn "arn:aws:iam::123:role/ProjectRole" \
  --tags Key=Project,Value=ProjectX --transitive-tag-keys Project
```

**Use cases**: Cost allocation, environment gating, temporary elevated access.

---

## ABAC (Attribute-Based Access Control)

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
External Access Findings: S3 bucket → external account → HIGH risk
Unused Access Findings: Role unused 90 days, permission never used
```

**Zones of trust**: Current account (trusted), same Organization (trusted), external accounts (findings).

---

## IAM Identity Center (SSO)

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


Centralized access across accounts. Identity source (AWS/AD/Okta) → Permission Sets → Account assignments.

| Aspect | Permission Set | IAM Role |
|--------|---------------|----------|
| Created by | SSO auto-creates | Manual |
| Assignment | SSO user/group → account | Manual trust policy |
| Session | Configurable 1-12h | 1h default |
| MFA | Integrated with IdP | Separate condition |

---

## Policy Conditions Deep Dive

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


Temporary AWS credentials for external servers (on-prem, other clouds) via X.509 certificates. Trust anchor (root CA) → profile (links IAM role) → `aws_signing_helper` returns temp creds.

---

## Service-Linked Roles

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


Pre-built IAM roles for AWS services (fixed trust policy, auto-updated permissions). Examples: RDS (Multi-AZ), Auto Scaling (lifecycle hooks), Lambda (VPC functions), EKS (cluster creation). Auto-created when feature enabled. Deleted only when no resources remain.

---

## Simplest Mental Model

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


```python
import boto3
import json

iam = boto3.client('iam')
sts = boto3.client('sts')

# Generate cross-account trust policy
def cross_account_trust(source_account: str, mfa_required: bool = True) -> dict:
    policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Effect': 'Allow',
            'Principal': {'AWS': f'arn:aws:iam::{source_account}:root'},
            'Action': 'sts:AssumeRole',
        }]
    }
    if mfa_required:
        policy['Statement'][0]['Condition'] = {
            'Bool': {'aws:MultiFactorAuthPresent': 'true'}
        }
    return policy

# ABAC policy generator — tag-based access
def abac_ec2_policy() -> dict:
    return {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Effect': 'Allow',
                'Action': 'ec2:StartInstances',
                'Resource': 'arn:aws:ec2:*:*:instance/*',
                'Condition': {
                    'StringEquals': {
                        'ec2:ResourceTag/Project': '${aws:PrincipalTag/Project}'
                    }
                }
            },
            {
                'Effect': 'Allow',
                'Action': 'ec2:Describe*',
                'Resource': '*'
            }
        ]
    }

# Validate policy (simulate evaluation)
def validate_policy(actions: list, resource: str, policy: dict) -> bool:
    # Simplified policy simulator logic
    for statement in policy['Statement']:
        if statement['Effect'] == 'Allow':
            target_actions = statement.get('Action', [])
            if isinstance(target_actions, str):
                target_actions = [target_actions]
            if all(action in target_actions for action in actions):
                if resource.startswith(statement['Resource'].replace('*', '')):
                    return True
    return False

# Create an IAM role for EC2 with boundary
def create_ec2_role(role_name: str, boundary_arn: str = None):
    trust = {'Version': '2012-10-17',
             'Statement': [{'Effect': 'Allow',
               'Principal': {'Service': 'ec2.amazonaws.com'},
               'Action': 'sts:AssumeRole'}]}
    kwargs = {'RoleName': role_name, 'AssumeRolePolicyDocument': json.dumps(trust)}
    if boundary_arn:
        kwargs['PermissionsBoundary'] = boundary_arn
    return iam.create_role(**kwargs)
```

```bash
# Test cross-account access
aws sts assume-role --role-arn "arn:aws:iam::TARGET:role/DataReader" \
  --role-session-name "audit-session" --duration-seconds 3600

# List unused roles (Access Analyzer CLI)
aws accessanalyzer list-findings --analyzer-arn arn:aws:access-analyzer:... \
  --query 'findings[?resourceType==`AWS::IAM::Role` && status==`ACTIVE`]'
```

---

## Common Failure Modes

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


**Problem**: Accidental privilege escalation through IAM role chaining

**Root cause**: IAM Role A can `sts:AssumeRole` into Role B, which has broader permissions. A user with access to Role A can chain to Role B, bypassing the intended restrictions on Role A. This is particularly dangerous when Role A is EC2 instance profile — any code on the instance can chain to a more privileged role.

**Detection**: CloudTrail events show `sts:AssumeRole` calls where `sourceIdentity` differs from the original role. Access Analyzer shows unused roles being accessed through chain patterns. Credential report shows roles assumed from unexpected principals.

**Solution**: Don't chain roles — call `sts:AssumeRole` directly on the target role. Set `aws:SourceIdentity` condition to restrict role assumption to specific identities. Use `aws:ViaAWSService` condition key to prevent chaining. Apply permission boundaries on all roles to limit their maximum scope. Monitor CloudTrail for `sts:AssumeRole` chains exceeding 1 hop.

**Problem**: Overly permissive wildcard policies granting unintended access

**Root cause**: `Action: "s3:*"` or `Resource: "*"` in an allow policy grants access to all current and future resources/services. Teams write permissive policies for convenience, creating massive blast radius. A developer role with `Action: "ec2:*"` and `Resource: "*"` can terminate any instance, delete any security group, or modify any VPC.

**Detection**: IAM Access Analyzer Unused Access findings show actions never used. AWS Config rules (`iam-policy-no-statements-with-admin-access`) flag admin-equivalent policies. Policy Summary dashboard shows excessive service coverage.

**Solution**: Use least-privilege - specify exact actions and ARNs. Use `deny` statements to explicitly block dangerous actions like `iam:PassRole` unrestricted. Apply permission boundaries to enforce maximum scope. Use IAM Access Analyzer to generate least-privilege policies from CloudTrail logs. Implement a policy-as-code pipeline that rejects PRs with wildcard resources.

---

## Interview Questions

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


### Q1: Explain AWS policy evaluation logic — how does a request get allowed or denied?

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


**Answer**: AWS evaluates policies in a specific order: (1) SCP from AWS Organizations, (2) Resource-based policies, (3) Permission boundaries, (4) Identity-based policies, (5) Session policies. At each layer, if there's an explicit `Deny`, the request is immediately denied. If no `Deny` exists but there's an `Allow` at any layer, the request is allowed. If there's neither deny nor allow, the implicit default-deny kicks in. Explicit deny always wins — even if the identity policy allows it, a SCP with deny blocks it. Permission boundaries set a maximum: even if the identity policy allows action X, the boundary restricts it. Session policies further restrict assumed roles. The key insight: there's no "allow override" — you must not have any applicable deny at any layer, and must have at least one allow.

### Q2: How do you design IAM for a multi-account AWS Organization with 20+ accounts?

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


**Answer**: Use AWS Organizations with a well-structured OU hierarchy (e.g., Security, Infrastructure, Workloads, Sandbox). Apply SCPs at the OU level for guardrails: deny root user actions, restrict regions, block leaving the organization. Use IAM Identity Center (SSO) for centralized user access with Permission Sets — grant access at the account/OU level rather than creating individual IAM users. Use IAM Roles (cross-account) for service-to-service access: central audit account reads CloudTrail from all accounts, central network account manages Transit Gateway. Use Resource-based policies (S3 bucket policies, KMS key policies) for cross-account data access. Use Access Analyzer continuously to detect unintended cross-account access. Automate account provisioning with Control Tower.
