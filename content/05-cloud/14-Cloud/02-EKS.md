# 02-EKS

Amazon Elastic Kubernetes Service provides a managed Kubernetes control plane on AWS. EKS handles the heavy lifting of operating the K8s API server, etcd, and controller manager while giving users full control over worker nodes and pod scheduling.

## Overview
EKS runs the upstream Kubernetes control plane across three Availability Zones for high availability. Users define node groups (EC2 instances or Fargate) that execute workloads. EKS integrates natively with AWS services: IAM for pod-level authentication (IRSA), ALB/NLB for ingress, EBS/EFS for storage, and CloudWatch for logging. Cluster updates and security patches are managed by AWS for the control plane, while node group updates remain the user's responsibility.

## Key Characteristics
- **Managed control plane**: AWS manages the K8s API server, etcd cluster, and controllers. No manual configuration or patching needed. Certified Kubernetes conformant.
- **Node group flexibility**: Choose EC2 managed node groups (self-managed instances) or AWS Fargate (serverless, no node management). Node groups can span multiple AZs for high availability.
- **IAM integration for pods**: IRSA (IAM Roles for Service Accounts) lets each pod assume an IAM role. Fine-grained permissions without storing credentials in secrets.
- **Network integration**: Uses VPC-native networking via the VPC CNI plugin. Each pod gets a real VPC IP address, simplifying security group rules and network policies.
- **Cost**: You pay for the control plane ($0.10/hour per cluster) plus the resources consumed by worker nodes. Fargate pricing is per-pod, per-second.
- **Operational complexity**: While simpler than self-managed K8s, EKS still requires expertise in Kubernetes concepts, Helm charts, Istio or similar service mesh, and cluster autoscaling.

## Why It Matters
EKS is the primary choice for teams that adopt Kubernetes on AWS. It eliminates control-plane management while preserving full Kubernetes API compatibility. For microservices, EKS provides a uniform deployment platform with service discovery, load balancing, auto-scaling, and rolling updates — all via standard K8s manifests.

## Related Concepts
- [ECS](03-ECS.md) — AWS's simpler, K8s-alternative container orchestration service
- [Horizontal Scaling](13-Scalability/01-Horizontal-Scaling.md) — EKS enables horizontal pod autoscaling (HPA) based on CPU, memory, or custom metrics
- [AWS](01-AWS.md) — EKS is one component of the broader AWS ecosystem

---

## Mental Model
A managed apartment building (EKS) where the landlord handles the roof, foundation, and plumbing (control plane). You furnish and maintain your own apartment (node groups). If you choose Fargate, the landlord even provides the furniture — just bring your belongings (containers).
