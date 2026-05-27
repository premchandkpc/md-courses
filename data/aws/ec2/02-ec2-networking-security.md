# 🖥️ EC2 Networking & Security — Complete Deep Dive

## Table of Contents
- [VPC Design Patterns](#vpc-design-patterns)
- [VPC Endpoints](#vpc-endpoints)
- [VPC Peering vs Transit Gateway](#vpc-peering-vs-transit-gateway)
- [Security Groups vs NACLs](#security-groups-vs-nacls)
- [Bastion Hosts vs SSM Session Manager](#bastion-hosts-vs-ssm-session-manager)
- [Instance Metadata & User Data](#instance-metadata--user-data)
- [Instance Profiles (IAM Roles for EC2)](#instance-profiles-iam-roles-for-ec2)
- [ENI Deep Dive](#eni-deep-dive)
- [ENA vs EFA vs ENA Express](#ena-vs-efa-vs-ena-express)
- [Placement Groups](#placement-groups)
- [Dedicated Hosts vs Dedicated Instances](#dedicated-hosts-vs-dedicated-instances)
- [Nitro System](#nitro-system)
- [Hibernate vs Stop vs Terminate](#hibernate-vs-stop-vs-terminate)
- [Systems Manager](#systems-manager)
- [EC2 Image Builder](#ec2-image-builder)
- [Simplest Mental Model](#simplest-mental-model)

---

## VPC Design Patterns

A VPC is a logically isolated network in AWS. Three subnet tiers for different workloads:

```text
+-------------------------------------------------------+
|                   VPC (10.0.0.0/16)                    |
|                                                       |
|  +----------------+  +----------------+  +----------+  |
|  | Public Subnet  |  | Private Subnet|  | Isolated  |  |
|  | 10.0.1.0/24   |  | 10.0.2.0/24   |  |10.0.3.0/24|  |
|  | IGW, ALB,     |  | NAT GW,       |  | DB, Redis |  |
|  | Bastion       |  | App Servers   |  | Internal  |  |
|  +----------------+  +----------------+  +----------+  |
+-------------------------------------------------------+
```

- **Public**: Route table -> IGW. For ALB, NAT Gateways, bastions.
- **Private**: Route table -> NAT Gateway for outbound. No direct inbound from internet.
- **Isolated**: No route to internet at all. For databases, internal caches, secrets.

**NAT Gateway vs NAT Instance**: NAT GW is managed, HA, scales up to 45 Gbps. NAT instance is deprecated, single EC2 in ASG.

## VPC Endpoints

Private access to AWS services without NAT Gateway or IGW.

| Type | Service | Cost | How |
|------|---------|------|-----|
| **Gateway** | S3, DynamoDB | Free | Route table prefix list |
| **Interface** | 130+ services | $/hr + $/GB | ENI in subnet (PrivateLink) |

**Gateway Endpoint**: Add prefix list to route table. No cost, automatically redundant. Traffic stays on AWS network.
**Interface Endpoint**: Creates ENI with private IP. Needs SG. Supports on-prem via PrivateLink + Direct Connect/VPN.

## VPC Peering vs Transit Gateway

```text
  Peering: VPC-A -- VPC-B, VPC-A -- VPC-C, VPC-B -- VPC-C (O(n^2) connections)
  TGW:     VPC-A -- TGW -- VPC-B, VPC-C, VPN, DX (O(n) connections)
```

| Feature | VPC Peering | Transit Gateway |
|---------|-------------|----------------|
| Topology | Point-to-point mesh | Hub-and-spoke star |
| Scale | < 100 VPCs | 1000s of VPCs |
| Transitive routing | No (no transitive peering) | Yes |
| Inter-region | Yes | Yes |
| VPN/Direct Connect | No | Yes |
| Route tables | Manual both sides | Centralized |

## Security Groups vs NACLs

| | Security Group | NACL |
|---|---|---|
| Scope | Instance (ENI) | Subnet |
| Rules | Allow only | Allow + Deny |
| State | Stateful | Stateless |
| Order | All evaluated | Numbered (1-32766), lowest first |
| Return traffic | Auto-allowed | Must be explicit |

**SG**: If inbound 443 allowed, outbound return traffic auto-allowed. **NACL**: Must explicitly allow outbound ephemeral ports (1024-65535) for return traffic. Use NACLs for deny lists (block bad IPs) and SGs for micro-segmentation.

## Bastion Hosts vs SSM Session Manager

**Bastion pros/cons**: EC2 in public subnet with SSH key, SG open on 22/3389, running 24/7, key management pain.

**SSM Session Manager**: Agent talks to SSM endpoint (outbound only). No public IP needed. IAM-based auth. Built-in CloudTrail logging. Port forwarding via `start-port-forwarding-session`.

**Pattern**: Never use bastions. Always SSM + EC2 Instance Connect.

## Instance Metadata & User Data

Available at `http://169.254.169.254/latest/meta-data/`. No auth (IMDSv1) or token-based (IMDSv2).

```bash
  # IMDSv2 (recommended)
  TOKEN=$(curl -X PUT http://169.254.169.254/latest/api/token \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
  curl -H "X-aws-ec2-metadata-token: $TOKEN" \
    http://169.254.169.254/latest/meta-data/instance-id
  curl -H "X-aws-ec2-metadata-token: $TOKEN" \
    http://169.254.169.254/latest/meta-data/iam/security-credentials/my-role
```

**Metadata categories**: instance-id, ami-id, hostname, public-ipv4, local-ipv4, iam/security-credentials/role-name, placement/availability-zone, tags.

**User Data**: Script at `/latest/user-data/`. Runs as root on first boot. Use for bootstrap (install packages, configure apps).

**Enforce IMDSv2**: Launch template setting `MetadataOptions.HttpTokens=required`. Or IAM policy with `ec2:MetadataHttpTokens`.

## Instance Profiles (IAM Roles for EC2)

```text
  IAM Role (e.g., S3ReadOnly) -> Instance Profile (wrapper, 1 role) -> EC2 Instance
  Credentials at: http://169.254.169.254/latest/meta-data/iam/security-credentials/role-name
```

Credentials auto-rotated every ~6 hours by EC2. Never put AWS access keys on EC2 instances.

## ENI Deep Dive

**Elastic Network Interface** = virtual network card.

- **Primary ENI** (eth0): Cannot be detached. Attached at launch.
- **Secondary ENI** (eth1+): Can be attached/detached/moved. Survives stop/start.

**Use cases**: Management network (separate data/mgmt traffic), dual-homed instances (ENI per subnet), floating IPs (move ENI + IPs for failover), network appliances (keep source IP).

**Limits**: ENIs per instance vary by type (t3.nano = 2, m5.24xlarge = 15). Each ENI gets one primary IP + multiple secondary IPs.

## ENA vs EFA vs ENA Express

| Feature | ENA | EFA | ENA Express |
|---------|-----|-----|-------------|
| Use case | General networking | HPC, ML (MPI, NCCL) | Any TCP |
| Throughput | Up to 100 Gbps | 100 Gbps + RDMA | 25 Gbps per flow |
| Latency | Standard | < 10 us (OS bypass) | Reduced via SRD |
| OS bypass | No | Yes (libfabric -> NIC) | No |

**ENA**: Standard SR-IOV networking. All modern instances.
**EFA**: Bypasses kernel TCP stack. GPU direct RDMA. P4d, P5, etc.
**ENA Express**: Uses SRD (Scalable Reliable Datagrams). Multi-path load balancing for TCP. No app changes needed.

## Placement Groups

| Type | Strategy | Limit |
|------|----------|-------|
| **Cluster** | Same rack, low latency, 10 Gbps | Single AZ, placement group limit |
| **Spread** | Distinct hardware, fault isolation | 7 instances per AZ |
| **Partition** | Groups on separate racks | 7 partitions per AZ |

**Cluster** for HPC. **Spread** for critical small apps (max 7). **Partition** for large distributed systems like Kafka, Cassandra, HDFS.

## Dedicated Hosts vs Dedicated Instances

| Feature | Dedicated Host | Dedicated Instance |
|---------|---------------|-------------------|
| BYOL | Yes (per-socket, per-core) | No |
| Host visibility | Full (sockets, cores, host ID) | None |
| Auto-scaling | Manual placement | AWS managed |
| Billing | Per host (hourly) | Per instance + $2/hr surcharge |

**Use dedicated hosts** for Windows Server/SQL Server BYOL (per-core licensing). **Dedicated instances** when you need hardware isolation without BYOL.

## Nitro System

The Nitro system is the underlying platform for all current-generation EC2 instances.

**Nitro Cards**: VPC Card (SR-IOV networking, 100 Gbps), EBS Card (NVMe storage, 260K IOPS, encryption), NVMe Card (instance store).
**Nitro Security Chip**: Hardware root of trust. Measures firmware at boot. Prevents unauthorized access.
**Nitro Hypervisor**: Lightweight KVM-based. Passes CPU/memory directly. Near bare-metal performance.

## Hibernate vs Stop vs Terminate

| | Stop | Hibernate | Terminate |
|---|---|---|---|
| Root volume | EBS persisted | EBS persisted | Deleted |
| RAM | Lost | Saved to EBS | Lost |
| Boot time | Minutes | Seconds (RAM restore) | N/A |
| Instance ID | Preserved | Preserved | Deleted |
| Private IP | Preserved | Preserved | Released |
| Public IP | Released | Released | Released |

**Hibernate needs**: RAM < 150 GB, encrypted EBS root, supported instance type (C5, M5, R5, etc.), `hibernationOptions: configured=true`.

## Systems Manager

AWS Systems Manager is a suite for fleet management.

**Run Command**: Remote execution via SSM agent. No SSH needed. IAM-based. Targets tags/IDs.
**Patch Manager**: Automated patching with maintenance windows. Pre-defined or custom patch baselines.
**Parameter Store**: Hierarchical config storage. Free tier (4 KB, standard), Advanced (8 KB, policies, $0.05/param/month). Supports `SecureString` via KMS.
**Session Manager**: Shell access via IAM. Logged to S3/CloudWatch. Port forwarding available.
**State Manager**: Enforce configuration state. Bootstrap policies.
**Automation**: Step-by-step playbooks (e.g., stop instances, create AMIs).

## EC2 Image Builder

Automated AMI pipeline:

```text
  Source Image -> Build Recipe -> EC2 Build Instance -> Test -> Distribute
       |                              |                     |
  (Amazon Linux,               Install packages,      (Target regions,
   Windows, custom)             run scripts)            share accounts)
```

**Components**: Install software, configure OS, run validation tests. **Image Recipe**: Parent + components + block device mapping. **Infrastructure Config**: Instance type, subnet, SG, IAM role. **Distribution**: Copy to regions, share with accounts.

---

## Simplest Mental Model

> **EC2 networking is building a moat with controlled drawbridges around your castle.**
>
> VPC = castle wall. Security groups = gate guards who remember who they let out (stateful). NACLs = outer wall guards checking ID each time (stateless). IMDSv2 = password-protected notice board. Instance profiles = royal seals (IAM roles). ENA/EFA/ENA Express = gravel road vs fiber optic vs multi-lane highway. Nitro = superior castle foundation.
>
> **Key rule**: never trust the network. Use IMDSv2, SSM over SSH, IAM roles over keys, least-privilege SGs, encryption everywhere.
