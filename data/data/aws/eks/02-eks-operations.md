# ☸️ EKS Operations — Complete Deep Dive

## Table of Contents
- [Managed vs Self-Managed vs Fargate](#managed-vs-self-managed-vs-fargate)
- [Cluster Autoscaler vs Karpenter](#cluster-autoscaler-vs-karpenter)
- [EBS CSI Driver](#ebs-csi-driver)
- [EFS CSI Driver](#efs-csi-driver)
- [FSx for Lustre CSI](#fsx-for-lustre-csi)
- [IRSA (IAM Roles for Service Accounts)](#irsa-iam-roles-for-service-accounts)
- [EKS Pod Identity](#eks-pod-identity)
- [CNI Deep Dive](#cni-deep-dive)
- [ALB Ingress vs AWS Load Balancer Controller](#alb-ingress-vs-aws-load-balancer-controller)
- [Gateway API on EKS](#gateway-api-on-eks)
- [EKS Add-Ons](#eks-add-ons)
- [Bottlerocket](#bottlerocket)
- [EKS Anywhere & EKS Distro](#eks-anywhere--eks-distro)
- [EKS Blueprints](#eks-blueprints)
- [Simplest Mental Model](#simplest-mental-model)

---

## Managed vs Self-Managed vs Fargate

```text
Managed Node Group:
  Auto Scaling Group with EC2s. AWS manages AMI, health, labels, join.
  You customize via launch template.

Self-Managed:
  You manage AMI, bootstrap, ASG, SG, OS patches, node draining.

Fargate:
  No nodes. Pods run on AWS-managed infra. No node management.
  Limitations: no DaemonSets, no privileged, no EBS.
```

| Aspect | Managed | Self-Managed | Fargate |
|--------|---------|-------------|---------|
| AMI updates | Automated | Manual | N/A |
| Node health | AWS | You | N/A |
| Customization | Launch template | Full control | None (CPU/mem only) |
| Scaling | ASG | ASG | Immediate |
| Cost | EC2 instance | EC2 instance | Per pod (vCPU+mem) |

**Pick managed** for 90% of workloads. **Self-managed** for custom CNI/kernel modules. **Fargate** for security-isolated, spiky apps.

---

## Cluster Autoscaler vs Karpenter

```text
Cluster Autoscaler: Pending Pod → ASG scale-up → Node in ~3-5 min
Karpenter: Pending Pod → EC2 API → Node in ~30-60s

Karpenter advantages:
  • Any instance type, not limited by ASG
  • Advanced binpacking (per-pod, not per-group)
  • Consolidation (replaces inefficient nodes)
  • Multi-arch native support
  • Spot weights per NodePool
```

| Feature | Cluster Autoscaler | Karpenter |
|---------|-------------------|-----------|
| Mechanism | ASG-based | Direct EC2 API |
| Node speed | ~3-5 min | ~30-60s |
| Instance diversity | Fixed by ASG | Any type |
| Binpacking | Basic | Advanced |
| Consolidation | ❌ | ✅ |
| Configuration | ConfigMap + ASG | CRDs |

---

## EBS CSI Driver

Dynamic provisioning of EBS volumes. `WaitForFirstConsumer` ensures AZ alignment with pod.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

**Snapshots & FSR**: VolumeSnapshots via `snapshot.storage.k8s.io/v1`. Fast Snapshot Restore pre-warms snapshot data (up to 10 FSR per volume). **Limitations**: ReadWriteOnce only, AZ-bound, no Fargate.

---

## EFS CSI Driver

Shared file storage with ReadWriteMany access across pods and AZs. Works on Fargate.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: efs-sc
provisioner: efs.csi.aws.com
parameters:
  provisioningMode: efs-ap
  fileSystemId: fs-12345678
```

**Use cases**: WordPress uploads, GitLab repos, shared configs.

---

## FSx for Lustre CSI

| Feature | EFS | FSx for Lustre |
|---------|-----|---------------|
| Protocol | NFS v4 | Lustre (POSIX) |
| Performance | Up to 10 GB/s | Up to 1 TB/s |
| Latency | ms | Sub-ms |
| Use case | Shared config | HPC, ML training |
| Fargate | ✅ | ❌ (EC2 only) |
| S3 linkage | ❌ | ✅ |

---

## IRSA (IAM Roles for Service Accounts)

```text
1. Create OIDC provider for EKS cluster
2. IAM role with OIDC trust (sub, aud conditions)
3. Annotate ServiceAccount with role ARN
4. Pod token → STS exchange → AWS credentials
```

Token injected via projected volume, auto-rotated, scoped to the pod's service account.

---

## EKS Pod Identity

Simpler than IRSA — no OIDC provider management. EKS agent handles credential vending directly.

| Aspect | IRSA | Pod Identity |
|--------|------|-------------|
| Setup | OIDC + trust policy | IAM role + association |
| Steps | More | Fewer |
| Credential source | OIDC → STS | EKS agent → STS |

---

## CNI Deep Dive

```text
VPC CNI Default: Pods get VPC IPs from ENIs. Max pods = ENIs × IPs/ENI - 1.
Prefix Delegation: /28 prefix per ENI → 110 pods/node on c5.large (vs 29).
Custom Networking: Separate CIDR for pods (10.100.0.0/16) vs nodes (10.0.1.0/24).
Security Groups Per Pod: Attach SG directly to pod via SecurityGroupPolicy CRD.
```

---

## ALB Ingress vs AWS Load Balancer Controller

AWS LB Controller supports: ALB + NLB, IngressGroup (shared ALB), SSL redirect, OIDC auth, target type `ip` or `instance`, Gateway API.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/group.name: shared-alb
spec:
  ingressClassName: alb
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /v1/orders
        pathType: Prefix
        backend:
          service:
            name: order-service
            port: { number: 80 }
```

---

## Gateway API on EKS

Gateway (LB) → HTTPRoute (routing) → Service (backend). Benefits: cross-vendor standard, role-oriented (ops vs dev), extended routing, service mesh integration.

---

## EKS Add-Ons

| Add-On | Purpose | Required |
|--------|---------|----------|
| vpc-cni | Pod networking | Yes |
| coredns | DNS | Yes |
| kube-proxy | Service networking | Yes |
| aws-ebs-csi-driver | EBS | Optional |
| aws-efs-csi-driver | EFS | Optional |
| aws-load-balancer-controller | ALB/NLB | Optional |

```awscli
aws eks create-addon --cluster-name my-cluster \
  --addon-name aws-ebs-csi-driver --addon-version v1.32.0-eksbuild.1
```

---

## Bottlerocket

Container-optimized OS by AWS. Immutable root, atomic A/B updates, no package manager. Host containers for SSH/debug. Smaller attack surface, faster boot.

---

## EKS Anywhere & EKS Distro

| | EKS (Managed) | EKS Anywhere | EKS Distro |
|---|---|---|---|
| Control plane | AWS | You | You |
| Workers | AWS | Your infra | Your infra |
| Upgrades | Auto/manual | Manual (CAPI) | Manual |
| Pricing | $0.10/hr/cluster | Subscription | Free |

**EKS Anywhere**: On-prem (VMware/Outposts). Same tooling. **EKS Distro**: Open-source K8s distro, free, for on-prem/air-gapped.

---

## EKS Blueprints

Open-source framework (Terraform/CDK): VPC + EKS + node groups + add-ons + teams (namespace, IAM, quotas). GitOps-ready (ArgoCD/Flux).

---

## Simplest Mental Model

```text
MANAGED NODES   =  Temp agency workers. Trained and managed.
SELF-MANAGED    =  Direct hires. Full HR control.
FARGATE         =  Robots. No visible people, just work done.

CLUSTER         =  Indecisive manager. Adds desks slowly.
AUTOSCALER         Takes ~5 min.

KARPENTER       =  Efficiency expert. Perfect desk instantly.
                   Consolidates half-empty desks.

EBS CSI         =  Dedicated USB-C drive. Fast. One computer.
EFS CSI         =  Network shared drive. Everyone reads.

IRSA/POD ID     =  Each pod has its own employee badge.
                   Used to share the node's badge.

CNI PREFIX      =  Phone numbers in blocks, not individually.
DELEGATION         More numbers per desk.

BOTTLEROCKET    =  Game console OS. Locked down. Atomic updates.

EKS ANYWHERE    =  Factory playbook in your garage.
EKS BLUEPRINTS  =  Pre-designed factory blueprint. Just build.
```
