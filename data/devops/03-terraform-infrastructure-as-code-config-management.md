# Terraform & Infrastructure as Code: From Local to Distributed

## Table of Contents
1. NOOB Explanation
2. Complete Terraform Internals
3. Terraform Workflows
4. Large-Scale IaC Architecture
5. State Management & Locking
6. Drift Detection & Validation
7. Failure Analysis & Root Causes
8. Edge Cases & Safety Mechanisms
9. Production Incidents
10. Security & Secrets
11. Code Examples
12. Comparison Tables (Ansible, Pulumi, CloudFormation)

---

## Section 1: NOOB Explanation - Infrastructure as Code Fundamentals

### The Manual Infrastructure Model (ANTI-PATTERN)

```
Month 1: Create manually
1. SSH to AWS console
2. Click: EC2 → Create Instance
3. Choose: Ubuntu 20.04, t3.medium
4. Security groups: 80, 443, 22
5. Storage: 50GB gp2
6. Launch
7. Assign elastic IP
8. Configure load balancer

Month 2: Scale up
1. Create 4 more instances (copy steps above)
2. Click 4 times... identical steps

Month 3: Update security group
1. SSH to console
2. Find the instance (which one was it?)
3. Click security group
4. Add rule
5. Repeat for 5 instances
6. Did I miss one?

Month 4: Disaster recovery
1. "How did we set up the security groups again?"
2. Developer leaves, knowledge lost
3. New developer recreates infrastructure differently
4. Inconsistency: prod != staging

Problems:
├─ Manual: error-prone, time-consuming
├─ Undocumented: no history of who changed what
├─ Unrepeatable: hard to recreate after disaster
├─ Unversioned: no git history
├─ Scale nightmare: manual * N = disaster
```

### The Terraform Model (DECLARATIVE IaC)

```
File: main.tf
resource "aws_instance" "web" {
  count         = 5
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"
  
  tags = {
    Name = "web-${count.index}"
  }
}

resource "aws_security_group" "web" {
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

$ terraform init      (download AWS provider)
$ terraform plan      (show what will be created)
$ terraform apply     (create infrastructure)

Benefits:
├─ Declarative: describe DESIRED state
├─ Versioned: all changes in git
├─ Repeatable: terraform apply = identical infrastructure
├─ Auditable: git log shows who changed what
├─ Testable: plan before apply
└─ Scalable: count = 5 creates 5 identical instances
```

### Terraform Workflow (High Level)

```
┌──────────────────────────────────────────────────────────┐
│ Developer: Write Terraform code                         │
│ resource "aws_instance" "web" { ... }                   │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ terraform init (download providers)                      │
│ .terraform/providers/aws/...                            │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ terraform validate (syntax check)                        │
│ ✓ Config is valid                                        │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ terraform plan (show diff)                               │
│ + aws_instance.web will be created                      │
│ + aws_security_group.web will be created                │
│ Plan: 6 to add, 0 to change, 0 to destroy               │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ Code review: "Does the plan look correct?"              │
│ ✓ Approved                                               │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ terraform apply (execute plan)                           │
│ 1. Acquire state lock (prevent concurrent applies)       │
│ 2. Validate configuration again                          │
│ 3. Call AWS API to create resources                      │
│ 4. Update terraform.tfstate file                         │
│ 5. Release state lock                                    │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ AWS Deployment                                           │
│ ✓ EC2 instances running                                  │
│ ✓ Security groups applied                                │
│ ✓ Infrastructure matches terraform code                  │
└──────────────────────────────────────────────────────────┘
```

---

## Section 2: Complete Terraform Internals

### State File Anatomy

```json
{
  "version": 4,
  "terraform_version": "1.5.0",
  "serial": 42,
  "lineage": "abc-def-123",
  "outputs": {
    "instance_id": {
      "value": "i-0123456789abcdef0",
      "type": "string"
    }
  },
  "resources": [
    {
      "mode": "managed",
      "type": "aws_instance",
      "name": "web",
      "instances": [
        {
          "schema_version": 1,
          "attributes": {
            "id": "i-0123456789abcdef0",
            "ami": "ami-0c55b159cbfafe1f0",
            "instance_type": "t3.medium",
            "private_ip": "10.0.1.100",
            "public_ip": "54.123.45.67",
            "availability_zone": "us-east-1a",
            "tags": {
              "Name": "web-0"
            }
          },
          "sensitive_attributes": []
        }
      ]
    },
    {
      "mode": "data",
      "type": "aws_ami",
      "name": "ubuntu",
      "instances": [
        {
          "attributes": {
            "id": "ami-0c55b159cbfafe1f0",
            "name": "ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-20240101"
          }
        }
      ]
    }
  ]
}
```

Key concepts:
- **version**: terraform state format version
- **serial**: incremented on each apply (detect conflicts)
- **lineage**: unique ID for this state (prevent mixing)
- **resources**: actual infrastructure (as known to terraform)
- **outputs**: values exported from root module

### Plan File Format

```hcl
# Command: terraform plan -out=plan.tfplan

# Binary format (compressed, signed)
$ file plan.tfplan
plan.tfplan: data

# Convert to readable JSON
$ terraform show -json plan.tfplan | jq '.'

{
  "format_version": "1.2",
  "terraform_version": "1.5.0",
  "planned_values": {
    "root_module": {
      "resources": [
        {
          "address": "aws_instance.web[0]",
          "mode": "managed",
          "type": "aws_instance",
          "name": "web",
          "index": 0,
          "values": {
            "ami": "ami-0c55b159cbfafe1f0",
            "instance_type": "t3.medium",
            "tags": {
              "Name": "web-0"
            }
          }
        }
      ]
    }
  },
  "resource_changes": [
    {
      "address": "aws_instance.web[0]",
      "mode": "managed",
      "type": "aws_instance",
      "name": "web",
      "index": 0,
      "change": {
        "actions": ["create"],
        "before": null,
        "after": { ... },
        "after_unknown": {
          "id": true,
          "private_ip": true,
          "public_ip": true
        },
        "before_sensitive": false,
        "after_sensitive": { ... }
      }
    }
  ]
}
```

Plan changes breakdown:
- **create** (`+`): new resource
- **update** (`~`): modify existing
- **delete** (`-`): remove resource
- **delete then create** (`-/+`): replace (can't modify)
- **read** (`<=`): data source fetch

### Provider Execution Model

```
┌─────────────────────────────────────────────────────────┐
│ Terraform Core (HCL parser, state management)           │
├─────────────────────────────────────────────────────────┤
│                      ▼                                    │
│         Plugin System (gRPC over HTTP)                  │
│         (Terraform ↔ Provider communication)            │
└──────────┬──────────────────────────┬──────────────────┘
           │                          │
           ▼                          ▼
    ┌──────────────────────┐  ┌──────────────────┐
    │  AWS Provider        │  │ Google Provider  │
    │  (aws)               │  │ (google)         │
    ├──────────────────────┤  ├──────────────────┤
    │ GetSchema()          │  │ GetSchema()      │
    │ PlanResourceChange() │  │ PlanResourceChange()
    │ ApplyResourceChange()│  │ ApplyResourceChange()
    │ ImportResourceState()│  │ ImportResourceState()
    └──────────────────────┘  └──────────────────┘
           │                          │
           ▼                          ▼
      AWS API (boto3)            Google API (client library)
```

Provider initialization:
```bash
$ terraform init

Initializing the backend...
Initializing modules...
- using aws from registry.terraform.io/hashicorp/aws
- downloading aws v5.0.0

Terraform has been successfully initialized!

# .terraform/
├─ .terraform.lock.hcl    (locked versions)
├─ terraform.tfstate      (local state)
└─ providers/
   └─ registry.terraform.io/hashicorp/aws/5.0.0/...
      └─ terraform-provider-aws_v5.0.0_x5
```

### Resource Lifecycle

```
1. REFRESH
   terraform read <resource>
   ├─ Query provider (e.g., describe_instances)
   ├─ Update state with actual resource state
   └─ Detect if resource was manually deleted

2. PLAN
   terraform show planned_changes
   ├─ For each resource in code:
   │  ├─ Compare desired (code) vs actual (state)
   │  └─ Determine action (create, update, delete)
   ├─ Resolve dependencies (order matters)
   └─ Output plan

3. APPLY
   terraform apply
   ├─ Load plan (or re-plan if not saved)
   ├─ Acquire state lock (DynamoDB, Consul)
   ├─ For each resource in dependency order:
   │  ├─ Call provider.ApplyResourceChange()
   │  ├─ Wait for resource to stabilize
   │  ├─ Read back attributes (IDs, IPs, etc)
   │  └─ Update state
   ├─ Compute outputs
   └─ Release state lock

4. DESTROY (optional)
   terraform destroy
   ├─ Plan destruction of all resources
   ├─ Apply in reverse dependency order
   └─ Remove from state


Example lifecycle for AWS instance:

┌─────────────────────────────────┐
│ Resource: aws_instance.web      │
├─────────────────────────────────┤
│ Code:                           │
│  ami = "ami-123456"             │
│  instance_type = "t3.medium"    │
└────────────┬────────────────────┘
             │
             ▼ (terraform plan)
┌─────────────────────────────────┐
│ Action: CREATE                  │
│ Reason: resource doesn't exist  │
│ in state                        │
└────────────┬────────────────────┘
             │
             ▼ (terraform apply)
┌─────────────────────────────────┐
│ AWS API Call:                   │
│ RunInstances(                   │
│   ImageId: ami-123456,          │
│   InstanceType: t3.medium       │
│ )                               │
│ Response: InstanceId = i-abc123 │
└────────────┬────────────────────┘
             │
             ▼ (wait for running)
┌─────────────────────────────────┐
│ State Updated:                  │
│ {                               │
│   id: "i-abc123",               │
│   public_ip: "54.123.45.67"     │
│ }                               │
└─────────────────────────────────┘
```

---

## Section 3: Terraform Workflows

### Local Development Workflow

```bash
# Step 1: Initialize working directory
$ terraform init
Initializing the backend...
Initializing modules...
Initializing the version constraint helpers...
Initializing provider plugins...

# Step 2: Write/edit Terraform code
$ vim main.tf
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"
}

# Step 3: Validate syntax
$ terraform validate
Success! The configuration is valid.

# Step 4: Format code
$ terraform fmt
1 file changed

# Step 5: Plan locally
$ terraform plan -out=plan.tfplan
aws_instance.web: Refreshing state... [id=i-0123456789abcdef0]

No changes. Your infrastructure matches the configuration.

# Step 6: Apply locally
$ terraform apply plan.tfplan
aws_instance.web: Modifying... [id=i-0123456789abcdef0]
aws_instance.web: Modification complete after 1s [id=i-0123456789abcdef0]

Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

# Step 7: Inspect outputs
$ terraform output
instance_id = "i-0123456789abcdef0"
public_ip   = "54.123.45.67"
```

### Remote State Workflow (Team)

```
Problem: Multiple engineers, one state file

Solution: Terraform Cloud or S3 backend

1. Terraform Cloud (recommended)
apiVersion: apps/v1
kind: ConfigMap
metadata:
  name: terraform-backend
data:
  backend.tf: |
    terraform {
      cloud {
        organization = "my-org"
        workspaces {
          name = "production"
        }
      }
    }

$ terraform init
Initializing Terraform Cloud...
Do you want to copy existing state to the new backend?

2. S3 + DynamoDB (DIY)
terraform {
  backend "s3" {
    bucket         = "terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-lock"
  }
}

$ terraform init
Successfully configured the backend "s3"!

# State file now stored in S3
$ aws s3 ls s3://terraform-state/prod/
2024-05-20 10:30:00 terraform.tfstate

# Lock table in DynamoDB
$ aws dynamodb scan --table-name terraform-lock
{
  "Items": [
    {
      "LockID": "prod/terraform.tfstate",
      "Info": "{\"ID\":\"...\",\"Operation\":\"OperationTypeApply\"}",
      "Reason": "Terraform applying changes",
      "Who": "alice@example.com",
      "Version": "1.5.0",
      "Created": 1234567890
    }
  ]
}
```

### CI/CD Integration Workflow

```yaml
# .github/workflows/terraform.yml

name: Terraform Apply
on:
  push:
    branches: [main]
    paths: [terraform/**]

jobs:
  plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.5.0

      - name: Terraform Init
        run: terraform init
        env:
          TF_CLI_ARGS: "-backend-config=key=prod/terraform.tfstate"

      - name: Terraform Validate
        run: terraform validate

      - name: Terraform Plan
        run: terraform plan -out=tfplan
        env:
          AWS_ROLE_ARN: arn:aws:iam::123456789:role/github-actions
          AWS_WEB_IDENTITY_TOKEN_FILE: /tmp/web_identity_token
          OIDC_PROVIDER_ARN: arn:aws:iam::123456789:oidc-provider/token.actions.githubusercontent.com

      - name: Upload Plan
        uses: actions/upload-artifact@v3
        with:
          name: tfplan
          path: tfplan

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const plan = require('fs').readFileSync('tfplan', 'utf-8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## Terraform Plan\n\`\`\`\n${plan}\n\`\`\``
            });

  apply:
    needs: plan
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v2

      - name: Download Plan
        uses: actions/download-artifact@v3
        with:
          name: tfplan

      - name: Terraform Apply
        run: terraform apply -no-color -input=false tfplan
        env:
          AWS_ROLE_ARN: arn:aws:iam::123456789:role/github-actions

      - name: Export Outputs
        run: |
          terraform output -json > outputs.json
          echo "::set-output name=outputs::$(cat outputs.json)"
```

---

## Section 4: Large-Scale IaC Architecture

### Multi-Environment Setup

```
Directory structure:
├─ modules/
│  ├─ vpc/
│  ├─ eks/
│  ├─ rds/
│  └─ iam/
├─ environments/
│  ├─ dev/
│  │  ├─ main.tf
│  │  ├─ terraform.tfvars
│  │  └─ outputs.tf
│  ├─ staging/
│  └─ production/
└─ global/
   ├─ s3/
   └─ iam/


modules/vpc/main.tf:
variable "cidr_block" {
  type = string
}

variable "environment" {
  type = string
}

resource "aws_vpc" "main" {
  cidr_block = var.cidr_block

  tags = {
    Environment = var.environment
  }
}

output "vpc_id" {
  value = aws_vpc.main.id
}


environments/dev/main.tf:
module "vpc" {
  source = "../../modules/vpc"

  cidr_block  = "10.0.0.0/16"
  environment = "dev"
}

module "eks" {
  source = "../../modules/eks"

  vpc_id       = module.vpc.vpc_id
  cluster_name = "dev-cluster"
}


environments/production/terraform.tfvars:
# All variables defined here
vpc_cidr_block = "10.1.0.0/16"
eks_node_count = 20
db_instance_class = "db.r5.4xlarge"


environments/production/main.tf:
variable "vpc_cidr_block" {
  type = string
}

module "vpc" {
  source = "../../modules/vpc"
  cidr_block = var.vpc_cidr_block
}

# terraform init
# terraform plan -var-file=terraform.tfvars
# terraform apply -var-file=terraform.tfvars
```

### Workspaces for Parallel Environments

```bash
# Create separate workspaces
$ terraform workspace new dev
Created and switched to workspace "dev"!

$ terraform workspace new staging
Created and workspace "staging"!

$ terraform workspace new production
Created and workspace "production"!

# Switch workspace
$ terraform workspace select production
Switched to workspace "production".

# State is now isolated
$ terraform apply
  (applies to production workspace only)

# Show workspace in output
outputs:
  environment = "production"
  state_file = "terraform.tfstate.d/production/terraform.tfstate"

# List workspaces
$ terraform workspace list
  default
  dev
* production
  staging


Backend state structure:
s3://terraform-state/
├─ prod/terraform.tfstate        (separate per env)
├─ staging/terraform.tfstate
└─ dev/terraform.tfstate

DynamoDB locks:
├─ prod/terraform.tfstate (locked during prod apply)
├─ staging/terraform.tfstate (unlocked)
└─ dev/terraform.tfstate (locked during dev apply)
```

### Multi-Account Architecture

```
AWS Organization:
├─ Management Account (root)
├─ Production Account (111111111111)
├─ Staging Account (222222222222)
└─ Dev Account (333333333333)

Terraform:
├─ root.tf (assume roles into each account)
├─ accounts/
│  ├─ production/
│  │  ├─ main.tf
│  │  └─ providers.tf
│  ├─ staging/
│  └─ dev/
└─ modules/


accounts/production/providers.tf:
provider "aws" {
  alias  = "production"
  region = "us-east-1"

  assume_role {
    role_arn          = "arn:aws:iam::111111111111:role/TerraformRole"
    session_name      = "terraform"
    duration_seconds  = 3600
  }
}

resource "aws_vpc" "production" {
  provider   = aws.production
  cidr_block = "10.1.0.0/16"
}


accounts/staging/providers.tf:
provider "aws" {
  alias  = "staging"

  assume_role {
    role_arn = "arn:aws:iam::222222222222:role/TerraformRole"
  }
}


root.tf:
module "production" {
  source = "./accounts/production"
}

module "staging" {
  source = "./accounts/staging"
}

# Both accounts configured from single terraform init!
$ terraform apply
  # Applies to both production AND staging
  # (be careful!)
```

---

## Section 5: State Management & Locking

### State Lock Mechanism

```
Lock flow (DynamoDB):

1. User runs: terraform apply

2. Terraform acquires lock:
   DynamoDB put-item:
   {
     "LockID": "prod/terraform.tfstate",
     "Info": "{\"ID\":\"abc123\",\"Operation\":\"OperationTypeApply\",\"Who\":\"alice\"}",
     "Reason": "Terraform applying changes",
     "Version": "1.5.0",
     "Created": 1234567890
   }

3. If lock already exists:
   ├─ Check lock age
   ├─ If < 10 minutes: wait, then retry
   ├─ If > 10 minutes: assume stale, force unlock
   └─ Display warning: "Acquired lock after force unlock"

4. Apply completes

5. Release lock:
   DynamoDB delete-item(LockID)

6. Lock released, others can now apply


Problem: Process crashes during apply
├─ Lock acquired at 10:00:00
├─ terraform apply crashes at 10:05:00
├─ Process killed, lock not released
├─ Lock sits in DynamoDB

Result at 10:15:00:
├─ Next user: terraform apply
├─ Detects lock is 15 minutes old
├─ Assumes stale, acquires lock
├─ Applies changes (dangerous!)
├─ May conflict with previous apply
```

### State Corruption & Recovery

```
Scenario 1: Concurrent applies (no locking)

State file before: resources = []

Apply 1:                    Apply 2:
├─ Read state              ├─ Read state (same)
├─ Add resource A          ├─ Add resource B
├─ Write state             ├─ Write state
   resources = [A]           resources = [B]  ← lost A!

Result: Resource A lost from state, but still in AWS!

Recovery:
$ terraform import aws_instance.web i-abc123
  (re-add to state)
$ terraform refresh
$ terraform plan  (should show no changes)


Scenario 2: Partial apply failure

Apply starts: aws_instance, aws_security_group, aws_rds
├─ Create aws_instance ✓
├─ Create aws_security_group ✓
├─ Create aws_rds ✗ (fails, e.g., storage quota exceeded)

State is now inconsistent:
├─ instance: created ✓
├─ security group: created ✓
├─ rds: NOT in state (never created)

Result: Instance orphaned (not in terraform state)

Recovery:
$ terraform import aws_instance.web i-abc123  (not needed, already in state)
$ terraform plan  (what do we have?)
  Plan: 1 to add (RDS), 0 to change, 0 to destroy

$ terraform apply  (retry, now succeeds)
```

### State Backup & Migration

```bash
# Backup state file
$ cp terraform.tfstate terraform.tfstate.backup

# OR export all resources
$ terraform state pull > backup.json

# Migrate local state to remote (S3)
# Step 1: Add backend config
terraform {
  backend "s3" {
    bucket         = "terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-lock"
  }
}

# Step 2: Re-initialize
$ terraform init
Do you want to copy existing state to the new backend?
> yes

# Terraform copies local state to S3:
$ aws s3 ls s3://terraform-state/prod/
terraform.tfstate

# Verify no drift
$ terraform plan
No changes. Your infrastructure matches the configuration.

# Delete local state
$ rm terraform.tfstate*


# Migrate S3 to Terraform Cloud
# Step 1: Create organization
# Step 2: Create workspace in TF Cloud
# Step 3: Update backend config
terraform {
  cloud {
    organization = "my-org"
    workspaces {
      name = "production"
    }
  }
}

# Step 4: Migrate
$ terraform login
  (generates API token)

$ terraform init
Do you want to copy existing state to the new backend?
> yes

# Terraform migrates S3 → Terraform Cloud
```

---

## Section 6: Drift Detection & Validation

### Detecting Infrastructure Drift

```
Terraform State:
- Instance: i-abc123 (running, t3.medium)
- Security group: sg-123 (port 80 open)

Actual AWS:
- Instance: i-abc123 (stopped! manually by ops)
- Security group: sg-123 (ports 80, 443 open! manual change)

Detection:
$ terraform plan
aws_instance.web: Refreshing state... [id=i-abc123]
aws_instance.web: has changed

  resource "aws_instance" "web" {
    id            = "i-abc123"
  - state         = "running" → "stopped"
  }

aws_security_group.web: Refreshing state... [id=sg-123]
aws_security_group.web: has changed

  resource "aws_security_group" "web" {
    id = "sg-123"
  - ingress rules have changed
  }

Plan: 0 to add, 2 to change, 0 to destroy.

^ Drift detected!

Recovery options:
1. Terraform apply (revert to declared state)
   $ terraform apply
   aws_instance.web: Modifying... [id=i-abc123]
   aws_instance.web: Modification complete [state restored]
   
2. Accept new state (import drift)
   $ terraform refresh
   $ terraform state pull > new_state.json
   (state now matches actual, but code doesn't!)
   
3. Update code to match reality
   # Edit main.tf
   resource "aws_instance" "web" {
     state = "stopped"  # accept reality
   }
```

### Policy as Code (Sentinel/OPA)

```hcl
# Sentinel policy: enforce production changes

import "tfplan/v2" as tfplan

# Admins can create anything
if user.group == "admin" {
    main = rule { true }
}

# Non-admins: restrict deletions
if user.group != "admin" {
    deletions_allowed = rule {
        length(tfplan.resource_changes.aws_instance) == 0
        and length(tfplan.resource_changes.aws_rds_cluster) == 0
    }
    main = rule { deletions_allowed }
}

# Enforce tags
enforce_tags = rule {
    all tfplan.resources as _, resources {
        all resources as _, r {
            all r.values.tags as _, tags {
                tags contains "Environment" and
                tags contains "Owner"
            }
        }
    }
}


# OPA (Open Policy Agent) example
package terraform

# All resources must have tags
deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_instance"
    not resource.change.after.tags
    msg := sprintf("Resource %v must have tags", [resource.address])
}

# Enforce tagging
required_tags := ["Environment", "Owner", "CostCenter"]

deny[msg] {
    resource := input.resource_changes[_]
    action := resource.change.actions[_]
    action != "delete"
    tags := resource.change.after.tags
    missing := [t | t := required_tags[_]; not tags[t]]
    count(missing) > 0
    msg := sprintf("Resource %v missing tags: %v", [resource.address, missing])
}
```

---

## Section 7: Failure Analysis & Root Causes

### Incident 1: State Lock Stuck

**Symptom**: `Error: Error acquiring the lock` - all terraform commands hang

**Root Cause**:
```
Timeline:
1. Engineer A: terraform apply (10:00)
   - Acquires lock in DynamoDB
   - Lock acquired for 10 minutes TTL

2. Infrastructure change takes 15 minutes
   - Database migration (10:00 - 10:15)
   - Lock held entire time

3. At 10:10, network connectivity lost
   - terraform process still running locally
   - Lock still held in DynamoDB
   - No heartbeat sent (connection lost)

4. At 10:20, lock expires (20 min TTL)
   - Lock released by DynamoDB

5. At 10:25, Engineer B: terraform apply
   - No lock exists (A's lock timed out)
   - Acquires lock, starts applying
   - Conflict: both A and B applying simultaneously!

6. Result: Partial apply, state corruption
```

**Prevention**:
```hcl
terraform {
  backend "s3" {
    dynamodb_table = "terraform-lock"
    
    # Increase lock timeout (default 10 min)
    # Manual in code, but important for long operations
  }
}

# In bash script
terraform apply -lock-timeout=30m  # Wait up to 30 min for lock

# Monitor lock health
$ watch 'aws dynamodb scan --table-name terraform-lock'

# Alert if lock held > 20 minutes
if lock.age > 20m and lock.operation == "apply":
  alert("Stuck terraform apply detected")
  # Manual intervention needed
```

**Recovery**:
```bash
# Force unlock (dangerous!)
$ terraform force-unlock abc123
  (abc123 = lock ID from error message)

# Verify state consistency after
$ terraform plan
$ # If plan shows unexpected changes, rollback
$ git revert <commit>
```

### Incident 2: Partial Apply Failure

**Symptom**: `terraform apply` crashed halfway, some resources created, some not

**Root Cause**:
```
Apply order:
1. aws_vpc - created ✓
2. aws_subnet - created ✓
3. aws_eks_cluster - FAILED ✗
   (e.g., invalid AMI in target AZ)

State after failure:
- vpc: exists in state
- subnet: exists in state
- eks: NOT in state (never created)

Problem: Infrastructure partially created
├─ VPC and subnet exist in AWS
├─ EKS not created
├─ State doesn't match reality

Next terraform apply:
$ terraform plan
Plan: 1 to add, 0 to change, 0 to destroy

^ Wrong! Tries to add EKS, but VPC/subnet already exist
```

**Recovery**:
```bash
# Option 1: Retry (if transient error)
$ terraform apply  (retry, may succeed if error was temporary)

# Option 2: Fix error and retry
# Error message: "Invalid AMI: ami-xxxx in us-east-1b"
# Fix: use valid AMI in code
$ vim main.tf
# data "aws_ami" "eks" {
#   filter "availability-zone" = "us-east-1a"
# }

$ terraform apply  (retry)

# Option 3: Destroy partial and restart
$ terraform destroy
  (removes what was created)
$ terraform apply
  (fresh apply from scratch)

# Option 4: Manual cleanup + state update
# Manual: delete VPC in AWS console
$ terraform state rm aws_vpc.main
$ terraform state rm aws_subnet.main
$ terraform apply
  (recreates from scratch)
```

### Incident 3: State File Corruption

**Symptom**: `Error: Error reading state: invalid JSON structure`

**Root Cause**:
```
State file: terraform.tfstate

Scenario 1: Concurrent writes (no lock)
├─ Process A: writes state (500 lines)
├─ Process B: writes state (500 lines, different content)
└─ Result: interleaved writes, invalid JSON

Scenario 2: Disk full during write
├─ state write starts (500 lines)
├─ Disk fills up after 250 lines
├─ State file truncated, invalid JSON

Scenario 3: Encryption key changed
├─ Old state encrypted with key A
├─ New state encrypted with key B
├─ Can't decrypt old, new doesn't exist
└─ Invalid state file
```

**Prevention**:
```bash
# Always use remote state + locking
terraform {
  backend "s3" {
    encrypt        = true
    dynamodb_table = "terraform-lock"
  }
}

# Monitor disk space
$ df -h
Filesystem      Size  Used Avail Use%
/dev/sda1       100G   95G   5G  95%
^ Alert if < 20G free!

# Regular backups
$ aws s3 cp s3://terraform-state/terraform.tfstate terraform.tfstate.backup

# Encrypted at rest
$ aws s3api head-object --bucket terraform-state --key terraform.tfstate | grep ServerSideEncryption
"ServerSideEncryption": "AES256"
```

**Recovery**:
```bash
# Step 1: Restore from backup
$ aws s3 cp s3://terraform-state/terraform.tfstate.backup terraform.tfstate

# Step 2: Validate
$ terraform validate

# Step 3: Verify state consistency
$ terraform plan
  (should show no unexpected changes)

# Step 4: Push to S3
$ terraform state push terraform.tfstate

# Step 5: Verify
$ terraform refresh
$ terraform plan
```

### Incident 4: Provider Version Mismatch

**Symptom**: `Error: resource not found` in production, but works in dev

**Root Cause**:
```
Dev machine:
$ terraform --version
Terraform v1.5.0

$ terraform providers
aws v5.0.0

Production CI/CD:
$ terraform --version
Terraform v1.4.0

$ terraform providers
aws v4.5.0  ← older version!

Difference:
dev (aws 5.0.0): supports aws_ec2_instance_state attribute
prod (aws 4.5.0): doesn't support this attribute

Code:
resource "aws_instance" "web" {
  state = "stopped"  # only in v5.0.0!
}

Result:
├─ Dev: terraform plan works
├─ Prod: terraform apply fails
│  "state is not supported by provider aws v4.5.0"
```

**Prevention**:
```hcl
# Lock provider versions
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0.0"  # lock to 5.x
    }
  }
}

# Commit lock file
.terraform.lock.hcl:
{
  "aws" = {
    "version" = "5.0.0"
    "constraints" = "~> 5.0.0"
    "hashes" = [...]
  }
}

# CI/CD uses exact versions
$ terraform init
terraform did not find locked provider hashicorp/aws for v5.0.0
using terraform.lock.hcl, installing hashicorp/aws v5.0.0
```

### Incident 5: Destroy Safety (Cascade Delete)

**Symptom**: `terraform destroy` deleted RDS database with data!

**Root Cause**:
```
Terraform assumes all resources are disposable:

resource "aws_db_instance" "production" {
  identifier = "prod-db"
  allocated_storage = 100
  # skip_final_snapshot = true  ← dangerous!
}

$ terraform destroy
aws_db_instance.production: Destroying... [id=prod-db]
aws_db_instance.production: Destruction complete

Result: Database deleted immediately, no backup!

Alternative cascade:
resource "aws_eks_cluster" "production" {
  name = "prod-cluster"
}

resource "aws_eks_node_group" "production" {
  cluster_name       = aws_eks_cluster.production.name
  node_group_name    = "nodes"
  node_role_arn      = aws_iam_role.node_role.arn
}

$ terraform destroy
└─ Tries to delete cluster
└─ Fails: node group still attached
└─ Manual intervention needed

Risk: Half-deleted infrastructure, stuck state
```

**Prevention**:
```hcl
# Add lifecycle protection
resource "aws_db_instance" "production" {
  identifier             = "prod-db"
  allocated_storage      = 100
  skip_final_snapshot    = false
  final_snapshot_identifier = "prod-db-final-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  
  lifecycle {
    prevent_destroy = true  # Error if someone tries to destroy
  }
}

# Require explicit unlocking
$ terraform destroy
Error: Resource has prevent_destroy lifecycle rule

To remove this resource, edit the resource and remove the
`prevent_destroy` lifecycle rule, then re-run "destroy".

---
# Before production destroy:
1. Edit code, remove prevent_destroy
2. Create PR (requires review)
3. Merge to main
4. terraform destroy (after explicit approval)

# Or use terraform workspace isolation
$ terraform workspace new safe
$ terraform apply  (applies only to "safe" workspace)
$ # Main workspace is untouched!
```

---

## Section 8: Edge Cases & Safety Mechanisms

### Resource Replacement vs In-Place Update

```
In-place update (safe):
resource "aws_instance" "web" {
  tags = {
    Name = "old-name" → "new-name"  # can change in-place
  }
}

$ terraform apply
aws_instance.web: Modifying...
aws_instance.web: Modifications complete

Result: Tag changed, instance still running


Forced replacement (destructive):
resource "aws_instance" "web" {
  ami           = "ami-old" → "ami-new"  # can't change in-place!
  instance_type = "t3.medium"           # needs new instance
}

$ terraform apply
aws_instance.web: Destroy-and-recreate
aws_instance.web: Destroying... [id=i-abc123]
aws_instance.web: Destroying completed [id=i-abc123]
aws_instance.web: Creating... [i-def456]
aws_instance.web: Creation complete [id=i-def456]

Result: 
- Old instance deleted
- New instance created
- IP changed (if public)
- Data loss (if not backed up)
- Downtime during replacement


Common forced replacements:
- ec2 ami change
- rds engine version change
- eks cluster version change
- s3 bucket name change (s3 names global)

Solution: Use blue-green deployment
resource "aws_instance" "blue" { ... }
resource "aws_instance" "green" { ... (new ami) }
resource "aws_lb_target_group_attachment" "route" {
  target_id = var.use_blue ? aws_instance.blue.id : aws_instance.green.id
}

# Apply changes gradually:
# 1. Create green with new ami
# 2. Route traffic to green
# 3. Destroy blue
```

### Cyclic Dependencies

```hcl
# Terraform detects cycles at parse time

resource "aws_security_group" "web" {
  vpc_id = aws_vpc.main.id  # depends on VPC
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  depends_on = [aws_security_group.web]  # CYCLE!
}

$ terraform init
Error: Cyclic dependency detected
Resource aws_vpc.main depends on aws_security_group.web
Resource aws_security_group.web depends on aws_vpc.main

---
# Solution: Use implicit dependencies
resource "aws_security_group" "web" {
  vpc_id = aws_vpc.main.id  # implicit: depends on VPC
  # Don't add explicit depends_on
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  # No depends_on needed
}

$ terraform apply
# Terraform orders: VPC first, then SG
```

### Sensitive Attributes

```hcl
# Mark passwords as sensitive
resource "aws_db_instance" "main" {
  username = "admin"
  password = var.db_password
  
  # Don't log password!
  sensitive = true
}

output "db_password" {
  value       = aws_db_instance.main.password
  sensitive   = true  # redact in logs
  description = "Database password (redacted)"
}

$ terraform apply
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:
db_password = <sensitive>

---
# But sensitive value is still in state file!
$ cat terraform.tfstate | grep password
"password_": "actualpassword123"  ← in plain text!

Solution: Use AWS Secrets Manager
resource "aws_secretsmanager_secret" "db" {
  name = "prod-db-password"
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id     = aws_secretsmanager_secret.db.id
  secret_string = random_password.db.result
}

# Don't store in state, fetch from Secrets Manager instead
# Reduces exposure if state file leaked
```

---

## Section 9: Production Incidents

### Incident 1: Accidental Database Deletion

**Timeline**:
- 14:00: Engineer refactoring code, removes RDS block
- 14:05: Commits change
- 14:10: CI/CD runs, plan shows "1 destroy"
- 14:12: Approves and merges (didn't read carefully!)
- 14:15: terraform apply, RDS deleting
- 14:20: Someone notices alerts, but too late
- 14:25: RDS deleted, 10 GB of data gone

**Prevention**:
```hcl
resource "aws_db_instance" "production" {
  db_instance_identifier = "prod-db"
  allocated_storage      = 1000
  
  # Enable protection
  skip_final_snapshot       = false
  final_snapshot_identifier = "prod-db-snapshot-${formatdate("YYYY-MM-DD", now())}"
  
  # Prevent accidental deletion
  lifecycle {
    prevent_destroy = true
  }
}

---
# Attempt to delete:
$ terraform destroy
Error: Instance has prevent_destroy lifecycle rule
You must remove this rule before destroying

# Forces explicit change in code + approval
1. PR to remove prevent_destroy
2. Requires security team approval
3. Code review catches deletion intent
```

### Incident 2: Infrastructure Drift Accumulation

**Timeline**:
- Month 1: Ops team manually scales instances (4 → 6)
- Month 2: Security adds new security group rule manually
- Month 3: DBA increases RDS storage manually
- Month 4: Terraform plan shows 10+ divergences
- Month 5: Someone tries to apply, massive changes
- Month 6: Disaster, half the changes fail, state corruption

**Prevention**:
```bash
# Regular drift detection
$ terraform plan
  (diff against current state)

# Alert if drift detected
if len(plan.resource_changes) > 0:
  alert("Infrastructure drift detected")
  
# Automated scan
$ terraform plan -out=tfplan > drift-report.txt
$ # Email daily report to ops team

# Prevent manual changes (RBAC)
apiVersion: iam.aws.amazon.com/v1
kind: IAMPolicy
metadata:
  name: prevent-manual-changes
rules:
  - effect: Deny
    actions:
      - ec2:RunInstances
      - ec2:ModifyInstanceAttribute
      - rds:ModifyDBInstance
      - elasticache:ModifyCluster
    principals:
      - ops-team
```

### Incident 3: Multi-Account State Confusion

**Symptom**: Apply to dev account deleted production database!

**Root Cause**:
```
Terraform config (shared):
provider "aws" {
  alias   = "production"
  profile = "default"  # uses ~/.aws/credentials
}

Developer's ~/.aws/credentials:
[default]
aws_access_key_id = AKIA...(dev account)
aws_secret_access_key = ...

Manager's ~/.aws/credentials:
[default]
aws_access_key_id = AKIA...(production account!)
aws_secret_access_key = ...

Timeline:
1. Dev terraform applies (expected: dev account)
   └─ Actually applies to production (wrong account!)
2. Resources created in prod instead of dev
3. Next manager terraform apply deletes old prod resources
4. Disaster!
```

**Prevention**:
```hcl
# Explicit account IDs in code
provider "aws" {
  alias  = "production"
  region = "us-east-1"
  
  assume_role {
    role_arn = "arn:aws:iam::111111111111:role/TerraformRole"
  }
}

provider "aws" {
  alias  = "dev"
  region = "us-east-1"
  
  assume_role {
    role_arn = "arn:aws:iam::333333333333:role/TerraformRole"
  }
}

---
# Verify account in code
resource "aws_iam_policy" "verify_account" {
  statement {
    effect = "Deny"
    actions = ["*"]
    resources = ["*"]
    condition = {
      StringNotEquals = {
        "aws:SourceAccount" = "111111111111"  # hardcoded prod account
      }
    }
  }
}

---
# CI/CD safeguard
$ export AWS_ROLE_ARN="arn:aws:iam::111111111111:role/github-actions"
$ # Assume role explicitly, can't use wrong account
$ terraform init
```

---

## Section 10: Security & Secrets

### Managing Secrets in Terraform

**Problem**: Don't store secrets in state files!

```hcl
# ✗ BAD: Secret in code (exposed!)
resource "aws_db_instance" "main" {
  username = "admin"
  password = "super_secret_password_123"  # git history!
}

---
# ✓ GOOD: Use variables from environment
variable "db_password" {
  type      = string
  sensitive = true
}

resource "aws_db_instance" "main" {
  username = "admin"
  password = var.db_password
}

---
$ export TF_VAR_db_password="secret"  # from env var
$ terraform apply

---
# ✓ BEST: Use AWS Secrets Manager

data "aws_secretsmanager_secret" "db" {
  name = "prod-db-password"
}

data "aws_secretsmanager_secret_version" "db" {
  secret_id = data.aws_secretsmanager_secret.db.id
}

locals {
  db_password = jsondecode(data.aws_secretsmanager_secret_version.db.secret_string)["password"]
}

resource "aws_db_instance" "main" {
  username = "admin"
  password = local.db_password  # never stored in state
}
```

### State File Encryption

```bash
# S3 backend with encryption
terraform {
  backend "s3" {
    bucket         = "terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true  # AES-256 server-side
    dynamodb_table = "terraform-lock"
  }
}

---
# S3 bucket configuration
resource "aws_s3_bucket" "terraform_state" {
  bucket = "terraform-state"
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"  # keep history
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"  # encrypt at rest
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true  # prevent accidental public access
}

---
# DynamoDB lock table with encryption
resource "aws_dynamodb_table" "terraform_lock" {
  name           = "terraform-lock"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  sse_specification {
    enabled = true
    sse_type = "KMS"  # KMS encryption (can use customer-managed key)
  }
}
```

### Audit Logging

```hcl
# CloudTrail logs all Terraform API calls
resource "aws_cloudtrail" "terraform" {
  name           = "terraform-audit"
  s3_bucket_name = aws_s3_bucket.cloudtrail.id
  depends_on     = [aws_s3_bucket_policy.cloudtrail]

  is_multi_region_trail = true
  enable_log_file_validation = true
  include_global_service_events = true
}

---
# Query who applied what when
$ aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=PutObject \
  --region us-east-1 \
  --query 'Events[*].[EventTime,Username,EventName,CloudTrailEvent]'

# Output:
# 2024-05-20T14:15:00Z	alice@company.com	PutObject
# 2024-05-20T10:30:00Z	terraform-role	RunInstances
```

---

## Section 11: Code Examples

### Complete Multi-Region Production Setup

```hcl
# root.tf
terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  cloud {
    organization = "my-org"
    workspaces {
      name = "production"
    }
  }
}

# Providers for each region
provider "aws" {
  alias  = "us-east-1"
  region = "us-east-1"

  assume_role {
    role_arn = "arn:aws:iam::${var.aws_account_id}:role/TerraformRole"
  }
}

provider "aws" {
  alias  = "eu-west-1"
  region = "eu-west-1"

  assume_role {
    role_arn = "arn:aws:iam::${var.aws_account_id}:role/TerraformRole"
  }
}

---
# variables.tf
variable "aws_account_id" {
  type = string
  description = "AWS Account ID"
}

variable "environment" {
  type = string
  default = "production"
}

variable "app_name" {
  type = string
  default = "myapp"
}

variable "instance_count" {
  type = number
  default = 10
}

variable "instance_type" {
  type = string
  default = "t3.large"
}

---
# vpc.tf
module "vpc_us_east" {
  source = "./modules/vpc"
  
  providers = {
    aws = aws.us-east-1
  }

  region = "us-east-1"
  cidr_block = "10.1.0.0/16"
  app_name = var.app_name
  environment = var.environment
}

module "vpc_eu_west" {
  source = "./modules/vpc"
  
  providers = {
    aws = aws.eu-west-1
  }

  region = "eu-west-1"
  cidr_block = "10.2.0.0/16"
  app_name = var.app_name
  environment = var.environment
}

---
# eks.tf
module "eks_us_east" {
  source = "./modules/eks"
  
  providers = {
    aws = aws.us-east-1
  }

  cluster_name = "${var.app_name}-${var.environment}-us-east"
  vpc_id = module.vpc_us_east.vpc_id
  subnet_ids = module.vpc_us_east.private_subnets
  node_count = var.instance_count
  instance_type = var.instance_type
}

module "eks_eu_west" {
  source = "./modules/eks"
  
  providers = {
    aws = aws.eu-west-1
  }

  cluster_name = "${var.app_name}-${var.environment}-eu-west"
  vpc_id = module.vpc_eu_west.vpc_id
  subnet_ids = module.vpc_eu_west.private_subnets
  node_count = var.instance_count
  instance_type = var.instance_type
}

---
# outputs.tf
output "us_east_cluster_endpoint" {
  value = module.eks_us_east.cluster_endpoint
  description = "US-EAST EKS cluster endpoint"
}

output "eu_west_cluster_endpoint" {
  value = module.eks_eu_west.cluster_endpoint
  description = "EU-WEST EKS cluster endpoint"
}

output "state_file_location" {
  value = "Terraform Cloud (my-org/production)"
  description = "Remote state file location"
}

---
# terraform.tfvars
aws_account_id = "123456789012"
environment = "production"
app_name = "myapp"
instance_count = 20
instance_type = "t3.xlarge"
```

---

## Section 12: Comparison Tables

| Tool | Type | State | Agents | Cost | Learning |
|------|------|-------|--------|------|----------|
| **Terraform** | IaC | Required | Optional | Free | Medium |
| **CloudFormation** | IaC | Implicit | N/A (AWS native) | Free | Hard (JSON/YAML) |
| **Pulumi** | IaC | Required | Optional | Free | Low (Python/JS) |
| **Ansible** | Config Mgmt | None | Required | Free | Medium |
| **Chef** | Config Mgmt | None | Required | ~$100/year | Hard (Ruby) |

### Terraform vs CloudFormation vs Pulumi

**Terraform**:
```hcl
resource "aws_instance" "web" {
  ami           = "ami-123456"
  instance_type = "t3.medium"
  count         = 5
  tags = { Name = "web-${count.index}" }
}

output "ids" {
  value = aws_instance.web[*].id
}
```

**CloudFormation**:
```yaml
Resources:
  WebInstance:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: ami-123456
      InstanceType: t3.medium
      Tags:
        - Key: Name
          Value: !Sub "web-${AWS::StackName}"

Outputs:
  InstanceId:
    Value: !Ref WebInstance
```

**Pulumi**:
```python
import pulumi
import pulumi_aws as aws

instances = []
for i in range(5):
    instance = aws.ec2.Instance(f"web-{i}",
        ami="ami-123456",
        instance_type="t3.medium",
        tags={"Name": f"web-{i}"})
    instances.append(instance)

pulumi.export("instance_ids", [i.id for i in instances])
```

---

## Section 13: Best Practices Checklist

- [ ] **Remote State**: Always use remote backend (S3, Terraform Cloud)
- [ ] **State Locking**: Enable DynamoDB locking for concurrent safety
- [ ] **Encryption**: Encrypt state at rest (AES-256, KMS)
- [ ] **Secrets**: Never hardcode, use AWS Secrets Manager
- [ ] **Versioning**: Lock provider versions in `.terraform.lock.hcl`
- [ ] **Plan Review**: Always review plan before apply
- [ ] **Testing**: Use terraform validate, tfsec, checkov
- [ ] **Drift Detection**: Regular `terraform plan` checks
- [ ] **Permissions**: Principle of least privilege (IAM)
- [ ] **Backups**: Regular state file backups
- [ ] **Monitoring**: Alert on failed applies, stuck locks
- [ ] **Documentation**: Maintain module README files
- [ ] **Modules**: DRY (Don't Repeat Yourself) - use modules
- [ ] **Git**: Commit code + lock file, not state files
- [ ] **Destroy Safety**: Use prevent_destroy lifecycle rules

---

## Conclusion

Terraform enables scalable, auditable, repeatable infrastructure management. Master state management, locking, and safety mechanisms to avoid production disasters.

Key takeaways:
1. **State is critical** (don't lose it, don't corrupt it)
2. **Locking prevents conflicts** (concurrent safety)
3. **Drift happens** (detect and fix regularly)
4. **Plan before apply** (mistakes are expensive)
5. **Test in lower environments first** (dev → staging → prod)
6. **Security is hard** (protect state, rotate secrets, audit logs)
7. **Scale with modules** (DRY code, reusable components)
8. **Rollback is easy** (git revert, but test first!)
