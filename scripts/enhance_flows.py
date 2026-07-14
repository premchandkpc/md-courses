#!/usr/bin/env python3
"""Enhance all k8s.html flows with deeper Q&A, more traps, and richer cheatsheets."""

import re
import json

# Additional Q&A pairs per flow step (indexed by flow id)
EXTRA_QA = {
    'control': [
        {"q":"Q: What is the difference between authentication, authorization, and admission in the EKS API server pipeline?","a":"A: Authentication answers 'who are you?' (IAM/x509). Authorization answers 'can you do this?' (RBAC). Admission control answers 'is this request valid and should it be mutated?' (webhooks). All three run in sequence before anything touches etcd."},
        {"q":"Q: How does the EKS API server handle etcd compaction and defragmentation?","a":"A: EKS manages etcd compaction automatically (removes superseded revisions) and defragmentation (reclaims space). You have no control over timing, but you can monitor etcd health via the /healthz endpoint. Compaction runs periodically; defragmentation runs during low-traffic windows."},
        {"q":"Q: What happens to existing workloads when the API server has a brief network partition?","a":"A: Already-running pods continue executing (kubelet has a local cache). New scheduling, scaling, and deployment operations fail until connectivity is restored. The controller-manager's 5-minute timeout for node status eventually triggers pod rescheduling if the partition persists."},
        {"q":"Q: Can you run a custom API server extension ( aggregated API server ) on EKS?","a":"A: Yes — via APIService resources that register custom API groups. The custom server runs in your cluster and the EKS API server proxies requests to it. This is how metrics-server, custom resource definitions, and admission webhooks extend the API."},
        {"q":"Q: What is the blast radius if the EKS control plane goes down?","a":"A: Running pods continue (kubelet has cached state). No new deployments, scaling, or scheduling. Service DNS resolution continues (CoreDNS runs on data plane). etcd becomes unreachable for writes. Recovery: AWS restores the control plane, typically within minutes."},
    ],
    'nodes': [
        {"q":"Q: How do you migrate workloads from a self-managed node group to a managed node group?","a":"A: (1) Create a new managed node group, (2) cordon old self-managed nodes, (3) drain them one by one (respecting PDBs), (4) verify pods are running on new nodes, (5) terminate old EC2 instances. The migration is online — no downtime if PDBs are correct."},
        {"q":"Q: What is the difference between node selector, node affinity, and taint/toleration?","a":"A: Node selector is a simple key-value match (hard constraint). Node affinity adds 'requiredDuringScheduling' and 'preferredDuringScheduling' (soft/hard). Taints/tolerations work in reverse: nodes are tainted, pods must tolerate the taint to be scheduled there. Taints are how dedicated nodes (GPU, spot) work."},
        {"q":"Q: How does EKS handle node bootstrap security?","a":"A: Managed node groups use a hardened AMI with limited attack surface, kubelet configured with --protect-kernel-defaults, and node roles scoped via aws-auth. Self-managed nodes require you to configure these yourself. EKS also supports custom launch templates for additional hardening."},
        {"q":"Q: What are the failure modes when an EC2 instance backing an EKS node dies?","a":"A: (1) kubelet stops heartbeating, (2) node marked NotReady after 40s, (3) node lifecycle controller confirms via EC2 API, (4) NoExecute taint applied, (5) pods evicted after pod-eviction-timeout (5min default), (6) pods rescheduled to healthy nodes. For StatefulSets, the old pod must be confirmed gone first."},
        {"q":"Q: Can you run Windows nodes in an EKS managed node group?","a":"A: Yes — EKS supports Windows Server 2019/2022 managed node groups. Windows nodes can't run Linux pods (different OS, different container runtime). You need separate node groups for Windows and Linux workloads, with appropriate node selectors on your pods."},
    ],
    'fargate': [
        {"q":"Q: What is the maximum pod density per Fargate task?","a":"A: One pod per task. Fargate doesn't support multiple pods sharing a task (no sidecar sharing via pod spec). If you need sidecars (e.g. Fluent Bit), define them as containers within the same pod spec — Fargate runs them all in the same microVM."},
        {"q":"Q: How do you monitor Fargate pod resource usage if there's no node to scrape?","a":"A: Fargate exposes resource metrics through the Kubernetes metrics API (metrics-server works). For detailed monitoring, use CloudWatch Container Insights with the Fargate recipe, or deploy a Prometheus sidecar container within the pod spec."},
        {"q":"Q: What are the networking limitations of Fargate compared to EC2 nodes?","a":"A: Fargate gets one ENI per pod (no secondary IPs, no prefix delegation). No hostNetwork mode. No custom CNI plugins (VPC CNI only). Security groups are task-level, not pod-level. Pod-to-pod traffic across different Fargate tasks goes through the VPC, not a local bridge."},
        {"q":"Q: How do you implement readiness gates for Fargate pods?","a":"A: Readiness gates work the same as EC2 — define a custom condition in the pod spec, and an external controller sets it. Fargate pods support all standard Kubernetes conditions including custom readiness gates."},
        {"q":"Q: What happens to Fargate pods during an EKS control plane upgrade?","a":"A: Fargate pods continue running during control plane upgrades (they're on the data plane). The Fargate profile and agent are managed by AWS — no action needed from you. After the upgrade, verify pod health and add-on compatibility."},
    ],
    'cni': [
        {"q":"Q: How does VPC CNI handle pod-to-pod traffic across different nodes in the same AZ vs across AZs?","a":"A: Same-AZ: traffic goes through the VPC's local route (fast, low latency). Cross-AZ: traffic traverses the VPC's cross-AZ routing (slightly higher latency, AWS charges ~$0.01/GB). Both use real VPC IPs — no overlay, no encapsulation."},
        {"q":"Q: What is the maximum number of pods per node with VPC CNI, and how do you increase it?","a":"A: Depends on instance type ENI/IP limits. m5.large: 3 ENIs × 6 IPs = 18 pods. Fix: enable prefix delegation (ENABLE_PREFIX_DELEGATION=true) → 3 ENIs × 16 IPs = 48 pods. Or use larger instance types with more ENI slots."},
        {"q":"Q: How does VPC CNI interact with Kubernetes network policies?","a":"A: VPC CNI alone doesn't enforce network policies. You need a policy engine (Calico, Cilium, or AWS Network Policy Controller) on top. VPC CNI provides the networking layer; the policy engine provides the enforcement layer."},
        {"q":"Q: What are the costs associated with VPC CNI's use of secondary IPs?","a":"A: Each secondary IP is a real VPC IP — no additional charges for the IPs themselves, but cross-AZ traffic using these IPs incurs standard AWS cross-AZ data transfer charges (~$0.01/GB). The main cost consideration is ENI/IP exhaustion leading to pod scheduling failures."},
        {"q":"Q: How do you debug VPC CNI issues on a specific node?","a":"A: Check aws-node pod logs: kubectl -n kube-system logs <aws-node-pod> -c aws-node. Check warm IP pool status. Verify ENI limits for the instance type. Use aws ec2 describe-network-interfaces to see attached ENIs and their IP assignments."},
    ],
    'vpc': [
        {"q":"Q: How do you design a VPC for a production EKS cluster with 3 AZs?","a":"A: 3 public subnets (ALB, NAT GW, bastion) + 3 private subnets (EKS nodes) + optionally 3 isolated subnets (RDS, ElastiCache). Each AZ gets one public + one private subnet. NAT Gateway in each public subnet for HA. CIDR: /19 subnets from a /16 VPC gives ~8K IPs each."},
        {"q":"Q: What is the cost of running NAT Gateways for an EKS cluster?","a":"A: ~$32/month per NAT Gateway (3 for 3-AZ HA = ~$96/month) + $0.045/GB processed. VPC endpoints for S3 (free), ECR (~$7/month each), STS (~$7/month) can reduce NAT data processing by 60-80%. Budget ~$150-200/month for networking infrastructure."},
        {"q":"Q: How do you connect an on-premises data center to EKS?","a":"A: (1) AWS Direct Connect (dedicated circuit, lowest latency), (2) Site-to-Site VPN (IPSec over internet, quicker setup), (3) Transit Gateway (hub for multiple VPCs + VPN). For hybrid DNS, use Route 53 Resolver endpoints."},
        {"q":"Q: What is the maximum VPC CIDR size you can use with EKS?","a":"A: /16 (65,536 IPs) is the maximum VPC CIDR. You can add secondary CIDRs to expand. For EKS, ensure pod CIDR (from VPC CNI) doesn't overlap with VPC CIDR or other VPCs you peer with. Plan CIDRs carefully — changing them later requires recreating the VPC."},
        {"q":"Q: How do you implement zero-trust networking for EKS pods?","a":"A: (1) Private subnets for all nodes, (2) VPC endpoints for AWS services, (3) Security Groups for Pods (VPC CNI), (4) Network Policies (Calico/Cilium), (5) mTLS (service mesh), (6) IAM for service-to-service auth. Layer these for defense in depth."},
    ],
    'schedule': [
        {"q":"Q: What is the difference between a Pod's 'Pending' and 'ContainerCreating' phases?","a":"A: Pending = scheduler hasn't found a suitable node yet (resource constraints, taints, affinity). ContainerCreating = node is assigned but container runtime is pulling images, setting up network, or running init containers. Pending → Running → Succeeded/Failed is the normal lifecycle."},
        {"q":"Q: How does the scheduler handle pod affinity and anti-affinity at scale?","a":"A: Required affinity/anti-affinity scales poorly — O(n²) complexity where n = number of pods. At 1000+ pods, scheduling can take minutes. Use preferredDuringScheduling for soft constraints, and topology spread constraints for more efficient spreading."},
        {"q":"Q: What are topology spread constraints and when should you use them?","a":"A: TopologySpreadConstraints let you spread pods across zones/nodes based on labels. Use them instead of pod anti-affinity for HA spreading — they're more efficient, more flexible, and scale better. Example: spread frontend pods across zones with maxSkew=1."},
        {"q":"Q: How do init containers affect pod scheduling?","a":"A: Init containers run before the main container. If an init container has resource requests, those are counted against the pod's total request for scheduling purposes. A slow init container delays the pod becoming Ready, which affects deployment rollout timing."},
        {"q":"Q: What is the scheduling queue and how does it prioritize pods?","a":"A: The scheduling queue holds unscheduled pods and processes them in priority order. Pod priority and preemption: high-priority pods can evict low-priority pods from nodes. Use PriorityClasses to define priority levels. Preemption is disruptive — use carefully."},
    ],
    'docker': [
        {"q":"Q: What is the difference between containerd and CRI-O?","a":"A: Both are CRI-compliant runtimes that replace Docker's dockershim. containerd is more feature-rich (supports Docker CLI, buildkit). CRI-O is purpose-built for Kubernetes (smaller, follows K8s versioning). EKS uses containerd by default. Both run OCI images."},
        {"q":"Q: How do containers share the kernel and why does that matter for security?","a":"A: Containers share the host kernel via namespaces (isolation) and cgroups (resource limits). A kernel exploit can potentially escape container isolation. VMs have separate kernels (stronger isolation). This is why Fargate's Firecracker microVMs (separate kernel per pod) are more secure than plain containers."},
        {"q":"Q: What is the difference between SIGTERM and SIGKILL in container lifecycle?","a":"A: SIGTERM is graceful shutdown (app can clean up, drain connections). SIGKILL is forced termination (no cleanup). Kubernetes sends SIGTERM first, waits terminationGracePeriodSeconds (default 30s), then SIGKILL. Your app should handle SIGTERM by stopping acceptance and draining."},
        {"q":"Q: How do container image layers affect rebuild speed?","a":"A: Each Dockerfile instruction creates a layer. Docker caches layers — if a layer's instruction and inputs haven't changed, it's reused. Put rarely-changing steps (apt install) before frequently-changing ones (COPY source). A code change invalidates the cache from that layer down."},
        {"q":"Q: What is the pause container and why does every pod have one?","a":"A: The pause container (k8s.gcr.io/pause) holds the pod's network namespace and other shared namespaces. All containers in a pod join this namespace (same IP, same loopback). The pause container does nothing else — it's a namespace anchor that outlives container restarts."},
    ],
    'docker-secure': [
        {"q":"Q: What is SLSA (Supply-chain Levels for Software Artifacts) and how does it relate to container security?","a":"A: SLSA is a framework for supply chain integrity. Level 1: build process is documented. Level 2: build platform is hosted, provenance is signed. Level 3: build platform is hardened, isolated. Container signing (Cosign) + SLSA provenance attestations provide end-to-end supply chain verification."},
        {"q":"Q: How do you handle secrets in Docker builds without embedding them in images?","a":"A: (1) BuildKit secrets (--mount=type=secret) for build-time secrets, (2) multi-stage builds to exclude build credentials, (3) ECR pull-through cache for base image auth, (4) runtime injection via K8s Secrets/IRSA. Never COPY secrets into image layers."},
        {"q":"Q: What is distroless and when should you use it over alpine?","a":"A: Distroless images (Google-maintained) contain only the app runtime + minimal dependencies — no shell, no package manager, no apt/apk. Use when you want the smallest attack surface. Use alpine when you need shell access for debugging or package installation at runtime."},
        {"q":"Q: How do you implement image pull policy correctly in production?","a":"A: Use unique tags (git SHA, semver) + imagePullPolicy: Always, or immutable digests + imagePullPolicy: IfNotPresent. Never use :latest with IfNotPresent — stale images will persist. Enable ECR tag immutability as a safety net."},
        {"q":"Q: What is the difference between Trivy, Snyk, and Grype for image scanning?","a":"A: Trivy (open-source, Aqua Security) — fast, covers OS packages + language deps + IaC. Snyk (commercial) — broader language support, better remediation advice. Grype (Anchore) — lightweight, pairs with Syft for SBOM generation. All three are production-ready; choose based on your CI/CD integration needs."},
    ],
    'svc': [
        {"q":"Q: What is the difference between ClusterIP, NodePort, and LoadBalancer service types?","a":"A: ClusterIP (default) — internal VIP, accessible only within cluster. NodePort — opens a port on every node (30000-32767), accessible externally via node IP. LoadBalancer — provisions cloud LB (ALB/NLB), external access. For EKS, prefer Ingress for HTTP or LoadBalancer for TCP."},
        {"q":"Q: How does kube-proxy's iptables mode handle session affinity?","a":"A: Session affinity (clientIP) uses iptables statistic module to hash client IP and always route to the same pod. Not true sticky sessions — hash can change if endpoints change. For true sticky sessions, use a service mesh or ALB with sticky sessions."},
        {"q":"Q: What happens to Service traffic during a rolling update?","a":"A: Only Ready pods receive traffic. During rollout, old pods are removed from Endpoints as they terminate, new pods are added as they pass readinessProbe. Traffic shifts gradually — no dual-serving unless both old and new pods are in Endpoints simultaneously."},
        {"q":"Q: How do headless services differ from regular ClusterIP services?","a":"A: Headless (clusterIP: None) returns individual pod IPs instead of a single VIP. Used for StatefulSets (pod DNS: pod-name.service-name.namespace.svc.cluster.local), DNS-based service discovery, and stateful applications that need direct pod addressing."},
        {"q":"Q: What is ExternalName DNS and when would you use it?","a":"A: ExternalName maps a service name to a CNAME (e.g. mydb → mydb.rds.amazonaws.com). Used for accessing external services (RDS, external APIs) via a Kubernetes service name. The DNS lookup returns a CNAME, not a ClusterIP — traffic goes directly to the external service."},
    ],
    'ingress': [
        {"q":"Q: What is the difference between an Ingress and a Gateway API resource?","a":"A: Gateway API is the next-generation replacement for Ingress — it's more expressive (separates routing from infrastructure), supports TCP/UDP, and has role-oriented design (infra admin vs app developer). EKS supports both; Gateway API is the future standard."},
        {"q":"Q: How does the ALB handle WebSocket connections?","a":"A: ALB supports WebSocket natively — once the HTTP upgrade handshake completes, ALB maintains a persistent TCP connection between client and target. No special configuration needed. Idle timeout applies (default 60s, configurable up to 4000s)."},
        {"q":"Q: What is the cost of running an ALB for a small EKS cluster?","a":"A: ALB pricing: ~$22/month fixed + $0.008/hour per LCU (Load Balancer Capacity Unit). For low-traffic clusters, 1 LCU is enough (~$6/month). Total: ~$28-35/month per ALB. Use IngressGroup to share one ALB across multiple Ingresses to save cost."},
        {"q":"Q: How do you configure rate limiting on ALB for EKS services?","a":"A: AWS WAF on the ALB provides rate-based rules (e.g. 1000 requests per 5 minutes per IP). Configure via WAFv2 ACL attached to the ALB. The AWS Load Balancer Controller supports WAFv2 annotations on Ingress resources."},
        {"q":"Q: What are the gotchas with ALB deregistration delay?","a":"A: Default 300s — too long for fast deployments. Set to 10-30s for most services. Must align with pod terminationGracePeriodSeconds. If ALB keeps sending traffic after pod starts terminating, you get 502s. If pod dies before ALB stops sending, you get connection resets."},
    ],
    'alb-nlb': [
        {"q":"Q: When would you use a Global Accelerator with EKS?","a":"A: Global Accelerator provides static anycast IPs and AWS backbone routing for global applications. Use it with NLB for: global TCP/UDP workloads, multi-region failover, consistent low latency worldwide. Not needed for single-region HTTP (ALB handles that)."},
        {"q":"Q: How does NLB handle cross-zone load balancing?","a":"A: NLB distributes traffic evenly across all targets in all AZs by default (cross-zone enabled). Disable it if you want even distribution per-AZ (targets in each AZ get equal traffic regardless of size). Cross-zone adds inter-AZ data transfer charges."},
        {"q":"Q: What is the difference between NLB TCP and TLS listeners?","a":"A: TCP listener: passes encrypted traffic through without termination (client handles TLS). TLS listener: terminates TLS at NLB using an ACM certificate, forwards decrypted traffic to targets. Use TLS listener if you want centralized TLS management."},
        {"q":"Q: How do you implement custom health checks for NLB targets?","a":"A: NLB health checks use the target group's configured protocol/port/path. For TCP: checks if port is open. For HTTP: checks the path (default /). Customize via target group health check settings. For EKS, the AWS LB Controller manages this based on readinessProbe."},
        {"q":"Q: What are the scaling limits of NLB vs ALB?","a":"A: NLB: scales to millions of requests/second, 50 Gbps throughput. ALB: scales to 100K requests/second per ALB, 100 LCUs. For extreme TCP/UDP workloads, NLB is better. For HTTP with path routing, ALB is better. Both scale automatically within their limits."},
    ],
    'irsa': [
        {"q":"Q: How do you troubleshoot IRSA when AssumeRoleWithWebIdentity fails silently?","a":"A: (1) Verify OIDC provider is registered: aws iam list-open-id-connect-providers. (2) Check SA annotation: kubectl get sa <sa> -o yaml. (3) Verify trust policy condition matches the exact namespace:SA. (4) Check pod env vars: AWS_ROLE_ARN and AWS_WEB_IDENTITY_TOKEN_FILE. (5) Test with aws sts assume-role-with-web-identity manually."},
        {"q":"Q: Can IRSA work across AWS accounts?","a":"A: Yes — the target account's IAM role trust policy can reference the source account's OIDC provider ARN. The pod in account A assumes a role in account B. Cross-account trust is configured in the role's trust policy with a condition on the OIDC issuer."},
        {"q":"Q: What is the token refresh mechanism for IRSA?","a":"A: The projected token has a 1-hour TTL. The webhook/servicetoken controller rotates it automatically. The AWS SDK caches the token and refreshes it before expiry. If the controller is down, pods get stale tokens that STS rejects after 1 hour."},
        {"q":"Q: How does IRSA compare to node instance profile for pod AWS access?","a":"A: IRSA: per-pod, least-privilege, auto-rotating, no shared blast radius. Instance profile: per-node, broad permissions, all pods on the node share the same credentials via IMDS. IRSA is always preferred for security."},
        {"q":"Q: What happens if the aws-iam-authenticator or EKS access entry is misconfigured?","a":"A: kubectl commands fail with 'unable to authenticate' or 'forbidden'. Pods using IRSA fail with STS errors. Debug: aws eks get-token, check kubeconfig, verify aws-auth configmap or access entries. The authentication chain: IAM → kubectl → API server → RBAC."},
    ],
    'pod-identity': [
        {"q":"Q: Can Pod Identity and IRSA coexist for the same ServiceAccount?","a":"A: Yes — a pod can have both an IRSA annotation and a Pod Identity association. The SDK credential chain checks both. In practice, migrate one service at a time: remove the IRSA annotation after confirming Pod Identity works."},
        {"q":"Q: What are the limitations of Pod Identity compared to IRSA?","a":"A: (1) Pod Identity is EKS-only (IRSA works on any Kubernetes). (2) Cross-account role assumption is more complex with Pod Identity. (3) Pod Identity is newer — fewer blog posts, examples, and community tools. (4) IRSA has a longer track record in production."},
        {"q":"Q: How does Pod Identity handle credential refresh?","a":"A: The Pod Identity agent manages credential refresh automatically — similar to IRSA's projected token rotation. The SDK's default credential chain picks up refreshed credentials transparently. No app code changes needed."},
        {"q":"Q: What permissions does the Pod Identity agent DaemonSet need?","a":"A: The agent needs the AmazonEKSPodIdentityAgentPolicy managed policy (attached to node roles). It also needs EKS API permissions to exchange node tokens for pod credentials. These are managed by AWS — no manual configuration needed."},
        {"q":"Q: How do you audit which pods are using Pod Identity vs IRSA?","a":"A: Check Pod Identity associations: aws eks list-pod-identity-associations. Check IRSA annotations: kubectl get sa -A -o json | grep role-arn. CloudTrail logs both AssumeRole (IRSA) and EKS Pod Identity API calls for auditing."},
    ],
    'scale': [
        {"q":"Q: What is the difference between HPA v1 (metrics API) and HPA v2 (custom metrics)?","a":"A: HPA v1 only scales on CPU/memory from metrics-server. HPA v2 scales on any metric: CPU, memory, custom metrics (from Prometheus), external metrics (SQS depth, etc.). HPA v2 is the default in modern Kubernetes. Use KEDA for event-driven autoscaling."},
        {"q":"Q: How does the cluster autoscaler decide which nodes to scale down?","a":"A: Scale-down checks: node utilization < 50% (configurable), no PDB preventing eviction, pods can be moved to other nodes, node has been underutilized for 10+ minutes. CA cordons the node, drains pods, then terminates the EC2 instance."},
        {"q":"Q: What is Karpenter's disruption budget and how does it differ from PDB?","a":"A: Karpenter NodePool disruption budgets limit how many nodes can be disrupted simultaneously (e.g. maxUnavailable: 2). PDBs protect individual pods during eviction. Karpenter respects both its own budgets AND PDBs when consolidating."},
        {"q":"Q: How do you set up HPA for a custom metric like requests-per-second?","a":"A: (1) Expose metrics via Prometheus metrics endpoint, (2) Deploy Prometheus Adapter to serve metrics via the Kubernetes custom metrics API, (3) Configure HPA with type: Pods and metric name matching the Prometheus query. KEDA simplifies this with built-in ScaledObject."},
        {"q":"Q: What happens when HPA and VPA are configured on the same metric?","a":"A: They fight each other — HPA scales out (more pods), VPA scales up (bigger pods), creating a feedback loop. Solution: use VPA in 'Recommendation' mode only (not Auto), or configure HPA to use a different metric than VPA."},
    ],
    'pdb': [
        {"q":"Q: How do you calculate minAvailable vs maxUnavailable for a given deployment?","a":"A: minAvailable: 'at least N pods must run' (absolute number or percentage). maxUnavailable: 'at most N pods can be down' (absolute or percentage). For a 10-replica deployment: minAvailable=8 means 2 can go down; maxUnavailable=2 means 2 can go down. They're complementary — use whichever gives you the behavior you want."},
        {"q":"Q: Can a PDB prevent a node from being drained entirely?","a":"A: Yes — if any pod on the node is protected by a PDB that can't be satisfied, the drain hangs. Example: PDB minAvailable=3 on a 3-replica deployment, all on the same node. The drain can't evict any of them without violating the PDB."},
        {"q":"Q: How do PDBs interact with Karpenter's consolidation?","a":"A: Karpenter respects PDBs during consolidation — it won't evict pods that would violate a PDB. But it may pause consolidation entirely if PDBs are too strict, leading to underutilized nodes that can't be reclaimed. Tune PDBs and Karpenter disruption budgets together."},
        {"q":"Q: What is the difference between PDB for StatefulSet vs Deployment pods?","a":"A: For StatefulSets, PDBs work the same way but eviction is more complex — StatefulSet pods have ordered identity. Evicting pod-2 may prevent pod-3 from starting until pod-2 is confirmed gone. This is why the 5-minute pod-eviction-timeout matters more for StatefulSets."},
        {"q":"Q: How do you test PDB effectiveness before a real node drain?","a":"A: Use 'kubectl drain --dry-run=server' to simulate without applying. Or manually evict a single pod: kubectl evict pod <pod> --grace-period=30. If it succeeds, the PDB allows it. If it fails, the PDB blocks it. Check 'kubectl get pdb' for current status."},
    ],
    'storage': [
        {"q":"Q: What is the difference between EBS volume types gp3, io2, and st1?","a":"A: gp3: general purpose, 3000 IOPS baseline (configurable to 16K), 125 MB/s baseline (configurable to 1000). io2: high-performance, up to 64K IOPS, for latency-sensitive databases. st1: throughput-optimized HDD, for big data/streaming, not for boot volumes. sc1: cold HDD, infrequent access."},
        {"q":"Q: How do you migrate a PVC from one StorageClass to another?","a":"A: You can't change a PVC's StorageClass after creation. Migration: (1) create a new PVC with the target StorageClass, (2) use a tool like pv-mover or rsync to copy data, (3) update the Deployment to use the new PVC, (4) delete the old PVC. StatefulSets require volumeSnapshot migration."},
        {"q":"Q: What is the maximum size of an EBS volume?","a":"A: gp3: 16 TiB. io2: 64 TiB. st1: 16 TiB. sc1: 16 TiB. For EKS, the CSI driver supports all sizes. Note: larger volumes take longer to format (mkfs) on first use, adding pod startup latency."},
        {"q":"Q: How do volume snapshots work with EBS CSI?","a":"A: Create a VolumeSnapshot resource pointing to a VolumeSnapshotClass. The CSI driver calls EBS CreateSnapshot. Use for backups, data migration, or creating pre-initialized volumes. Snapshots are stored in S3, managed by AWS. Restore by creating a PVC from the snapshot."},
        {"q":"Q: What happens when a pod using an EBS PVC is evicted and rescheduled to a different AZ?","a":"A: The pod stays Pending — EBS volumes are zonal and can't attach to instances in a different AZ. The CSI driver sets topology constraints to keep pods in the same AZ as their volume. Fix: use EFS for cross-AZ needs, or ensure topology-aware scheduling."},
    ],
    'efs': [
        {"q":"Q: What is the performance model of EFS compared to EBS?","a":"A: EFS: shared NFS, 100 MB/s baseline per TB, burstable to 3 GB/s, higher latency (~1-3ms) for metadata operations. EBS gp3: dedicated block, 3000 IOPS baseline, 125 MB/s, low latency (<1ms). EFS for shared access; EBS for single-pod high-performance."},
        {"q":"Q: How do you implement encryption for EFS in EKS?","a":"A: Enable encryption at rest via AWS KMS (create EFS file system with encrypted=true). Encryption in transit: NFS over TLS (mount options: vers=4.1,tls). The EFS CSI driver supports both. KMS key management is automatic with AWS-managed keys or customer-managed CMKs."},
        {"q":"Q: What are the cost tiers of EFS and how do you optimize?","a":"A: Standard: $0.30/GB-month. Infrequent Access (IA): $0.16/GB-month. Lifecycle policies automatically move files to IA after N days. For EKS: configure lifecycle policies to reduce costs for infrequently accessed data. EFS is more expensive per-GB than EBS but doesn't require provisioned capacity."},
        {"q":"Q: How do you handle EFS performance for small file workloads?","a":"A: EFS metadata operations (ls, find, stat) can be slow with millions of small files. Solutions: (1) batch small files into larger ones, (2) use EFS Access Points to shard across directories, (3) use EFS Provisioned Throughput for guaranteed IOPS, (4) consider S3 for object-heavy workloads."},
        {"q":"Q: How does EFS handle disaster recovery across regions?","a":"A: EFS doesn't natively replicate across regions. Use AWS Backup to copy EFS backups to a secondary region. For active-active cross-region access, use data synchronization (EFS Sync) or application-level replication. EFS is regional — data stays in the region where it was written."},
    ],
    'rollout': [
        {"q":"Q: What is the difference between RollingUpdate and Recreate deployment strategies?","a":"A: RollingUpdate: gradually replaces old pods with new ones (zero downtime). Recreate: kills all old pods before creating new ones (downtime window). Use Recreate only when two versions can't coexist (e.g. database migrations with breaking schema changes)."},
        {"q":"Q: How do you implement blue-green deployments on EKS?","a":"A: (1) Deploy new version alongside old, (2) switch Service selector to new version, (3) verify, (4) delete old version. Tools: Argo Rollouts, Flagger, or manual via kubectl. Blue-green gives instant rollback (switch selector back) but requires 2× resources during transition."},
        {"q":"Q: What is a canary deployment and how does it differ from rolling update?","a":"A: Canary: route a small percentage of traffic to the new version (e.g. 5%), monitor, then gradually increase. Rolling update: replace pods 1:1 with new version. Canary is safer for catching issues early but requires traffic splitting (ALB weighted target groups, Istio, Flagger)."},
        {"q":"Q: How do you handle database migrations during a zero-downtime deployment?","a":"A: (1) Deploy migration as a pre-upgrade Job, (2) ensure migration is backward-compatible, (3) deploy new app version, (4) run post-migration cleanup. Never break backward compatibility in migrations — old pods may still be running during the rollout."},
        {"q":"Q: What is the impact of minReadySeconds on deployment rollout speed?","a":"A: minReadySeconds adds a wait after each pod becomes Ready before the Deployment considers it 'available'. A 30s minReadySeconds with 10 replicas adds 300s total to the rollout. Use it to prevent flapping pods from advancing the rollout, but keep it low for fast deployments."},
    ],
    'ecr': [
        {"q":"Q: What is the difference between ECR basic and enhanced scanning?","a":"A: Basic: scans at push time only (free). Enhanced (Inspector): continuous rescanning as new CVEs are published (paid per image/month). Enhanced catches CVEs published after the image was pushed. Basic alone misses post-push vulnerabilities."},
        {"q":"Q: How do you implement cross-account ECR image sharing?","a":"A: (1) ECR repository policy: grant pull access to the target account, (2) Target account's node/IRSA role: needs ecr:GetDownloadUrlForLayer and BatchGetImage permissions. No imagePullSecret needed for same-region cross-account pulls."},
        {"q":"Q: What is ECR pull-through cache and when should you use it?","a":"A: ECR pull-through cache automatically pulls and stores upstream images (Docker Hub, GitHub, Quay) in your private ECR. Use it to: avoid Docker Hub rate limits, cache base images for faster pulls, centralize all images in one registry. Configure via ECR settings."},
        {"q":"Q: How do you implement image immutability for ECR repositories?","a":"A: Enable tag immutability on the ECR repository: aws ecr put-image-tag-mutability --repository-name myapp --image-tag-mutability IMMUTABLE. Prevents overwriting existing tags. Use with unique tags (git SHA) for production — forces new tags for new images."},
        {"q":"Q: What are ECR lifecycle policies and how do they save costs?","a":"A: Lifecycle policies automatically clean up old images. Example: keep only last 10 tagged images, delete untagged images after 7 days, keep only last 5 images with prefix 'v'. Reduces storage costs significantly for active repositories. Configure via JSON policy document."},
    ],
    'secrets': [
        {"q":"Q: What is the difference between Kubernetes Secrets and external secrets (Secrets Manager)?","a":"A: K8s Secrets: stored in etcd (base64 by default, encrypted with KMS optionally), managed via kubectl. External: stored in AWS Secrets Manager/Parameter Store, synced to K8s via ESO, single source of truth, supports rotation. Always prefer external for production."},
        {"q":"Q: How do you implement secret rotation without pod restarts?","a":"A: (1) Use volume-mounted secrets (kubelet auto-syncs ~60-90s), (2) ESO with refreshInterval, (3) App reads secret from file and watches for changes, (4) For env vars: no way without restart — use volume mounts for rotatable secrets."},
        {"q":"Q: What is the security difference between base64 encoding and encryption at rest?","a":"A: base64 is encoding (trivially reversible, zero security). Encryption at rest (KMS envelope encryption) is cryptographic protection. K8s Secrets are base64 by default — anyone with RBAC access can decode them. Enable KMS encryption for etcd at-rest protection."},
        {"q":"Q: How do you audit who accessed a Kubernetes Secret?","a":"A: Enable Kubernetes audit logging (EKS: enable audit logging in cluster config). Filter audit events for 'secrets' resources. Send to CloudWatch Logs or a SIEM. Also audit AWS Secrets Manager access via CloudTrail. Both are needed for full audit trail."},
        {"q":"Q: What is the blast radius if etcd is compromised without encryption?","a":"A: Attacker has all Secrets in plain text: database passwords, API keys, TLS certificates, SSH keys. Enable KMS envelope encryption, restrict etcd access (EKS manages this), use IRSA instead of static credentials, rotate all secrets if compromise is suspected."},
    ],
    'nodefail': [
        {"q":"Q: What is the difference between a node going NotReady vs being terminated?","a":"A: NotReady: kubelet stopped heartbeating (could be network partition, kubelet crash, node overload). Node still exists. Terminated: EC2 instance is gone (Spot reclaim, ASG termination, manual termination). Different recovery paths: NotReady may self-heal; terminated requires rescheduling."},
        {"q":"Q: How does Karpenter handle multiple simultaneous node failures?","a":"A: Karpenter provisions replacement nodes in parallel across AZs, matching pending pods' requirements. It respects disruption budgets and tries to right-size replacements. Multiple failures trigger multiple provisioning calls simultaneously — generally faster than ASG-based recovery."},
        {"q":"Q: What is the pod-eviction-timeout and why is it 5 minutes by default?","a":"A: After a node goes NotReady, pods are marked for eviction but not immediately deleted. The 5-minute timeout exists to prevent split-brain: the node might be network-partitioned but still running pods. For StatefulSets, this prevents duplicate instances writing to shared storage."},
        {"q":"Q: How do you detect and handle silent node failures (no Spot notice)?","a":"A: Monitor node heartbeat age via kube-state-metrics. Set up alerts for nodes NotReady > 2 minutes. Karpenter/CA react to unschedulable pods. For stateless workloads: fast rescheduling. For stateful: ensure PDBs and graceful shutdown handling."},
        {"q":"Q: What is the recovery time for a Spot interruption on EKS?","a":"A: 2-minute warning → handler cordons/drains node → pods evicted (respecting PDBs) → Karpenter/CA provisions replacements → new pods start. Total: 2-5 minutes depending on PDB strictness, image pull time, and node provisioning speed. Pre-warming or warm pools can reduce this."},
    ],
    'upgrade': [
        {"q":"Q: What is the maximum version skew between control plane and kubelet on EKS?","a":"A: kubelet can be up to 3 minor versions behind the control plane (n-3). During upgrade: control plane is 1.30, nodes can still run 1.27 kubelet. But this is a transient state — upgrade nodes promptly. API server won't use kubelet-only features from newer versions."},
        {"q":"Q: How do you handle add-on compatibility during an EKS upgrade?","a":"A: (1) Check add-on versions for target K8s version: aws eks describe-addon-versions. (2) Upgrade add-ons AFTER control plane upgrade. (3) Test in dev first. (4) Use --resolve-conflicts PRESERVE to keep custom configurations. Add-ons are the most common post-upgrade failure point."},
        {"q":"Q: What happens to PDBs during a managed node group upgrade?","a":"A: The upgrade process drains nodes one at a time, respecting PDBs. If a PDB blocks eviction, the drain pauses. AWS waits up to a timeout (configurable) before force-terminating. Ensure PDBs allow at least one pod disruption for smooth upgrades."},
        {"q":"Q: How do you prepare for an EKS upgrade?","a":"A: (1) Run deprecation scan (pluto detect-api-resources), (2) Check add-on compatibility, (3) Update dev/staging clusters first, (4) Review PodDisruptionBudgets, (5) Test application health checks, (6) Schedule maintenance window, (7) Monitor CloudWatch metrics during upgrade."},
        {"q":"Q: What is the EKS extended support model and how does it affect upgrades?","a":"A: EKS supports Kubernetes versions for 14 months (standard) or 26 months (extended, additional cost). After end-of-support, you must upgrade. Extended support buys time but doesn't change the upgrade process — you still go one version at a time."},
    ],
    'ssm': [
        {"q":"Q: What is the difference between SSM Session Manager and EC2 Instance Connect?","a":"A: SSM: persistent sessions, no SSH keys, works in private subnets, audit trail. Instance Connect: one-time SSH connections (60s limit), requires SSH key injection, works via bastion. SSM is preferred for debugging; Instance Connect for quick one-off access."},
        {"q":"Q: How do you set up SSM for a fully private EKS cluster (no NAT)?","a":"A: Create VPC endpoints for SSM: ssm, ssmmessages, ec2messages. These are interface endpoints (~$7/month each). Without NAT, SSM traffic goes through these endpoints. Ensure the node's instance role has AmazonSSMManagedInstanceCore policy."},
        {"q":"Q: Can you use SSM to forward ports to a pod (not just the node)?","a":"A: SSM port forwarding tunnels to the node, not directly to a pod. From the SSM session, use kubectl port-forward or kubectl exec to reach pod-level services. For direct pod access from your laptop, use kubectl port-forward via the API server instead."},
        {"q":"Q: How do you audit SSM sessions for compliance?","a":"A: SSM logs all sessions to CloudTrail with the IAM principal that started the session. Session Manager preferences can enable: session logging (to S3/CloudWatch), shell audit logging (every command). Configure via SSM console → Session Manager → Preferences."},
        {"q":"Q: What is SSM Run Command and how does it differ from Session Manager?","a":"A: Run Command: execute commands on multiple nodes simultaneously (like Ansible). Session Manager: interactive shell on a single node. Run Command is for fleet management (update kubelet, install packages); Session Manager is for debugging specific nodes."},
    ],
    'observability': [
        {"q":"Q: What is the difference between metrics-server and Prometheus in Kubernetes?","a":"A: metrics-server: lightweight, real-time only (no history), powers HPA and kubectl top. Prometheus: full time-series database, long-term storage, PromQL, alerting rules, custom metrics. metrics-server is for scaling decisions; Prometheus is for monitoring, alerting, and dashboards."},
        {"q":"Q: How do you set up alerting for EKS cluster health?","a":"A: (1) Amazon Managed Prometheus for metrics, (2) Grafana for dashboards, (3) Prometheus AlertManager or Amazon Managed Grafana alerting. Key alerts: pod crash looping, node NotReady, high CPU/memory, etcd latency, API server error rate."},
        {"q":"Q: What is ADOT and how does it relate to EKS observability?","a":"A: ADOT (AWS Distro for OpenTelemetry) is a certified OpenTelemetry distribution for EKS. It collects metrics, traces, and logs and exports to AWS backends (CloudWatch, X-Ray, Prometheus). Use ADOT instead of Fluent Bit + Prometheus for a unified telemetry pipeline."},
        {"q":"Q: How do you correlate logs with metrics in EKS?","a":"A: Use OpenTelemetry (ADOT) to add trace IDs to logs and metric labels. CloudWatch Container Insights correlates logs/metrics by pod. Amazon Managed Grafana can overlay logs and metrics on the same dashboard. Correlation requires consistent pod metadata labels."},
        {"q":"Q: What is the cost of running CloudWatch Container Insights on EKS?","a":"A: Container Insights: ~$0.30/pod/month for metrics + CloudWatch Logs ingestion costs (~$0.50/GB). For 100 pods: ~$30/month metrics + log storage. Compare to self-hosted Prometheus (free software, but EC2/compute costs). Managed services save operational overhead."},
    ],
    'compose': [
        {"q":"Q: How do you manage environment-specific configurations in Docker Compose?","a":"A: (1) Multiple compose files: docker-compose -f base.yml -f prod.yml, (2) .env files for variable substitution, (3) Profiles for optional services, (4) Override files: docker-compose.override.yml loaded automatically. For production, use Kubernetes with Kustomize/Helm instead."},
        {"q":"Q: What is the difference between docker compose up and docker compose up --build?","a":"A: Without --build: uses cached images (fast, no rebuild). With --build: forces rebuilding images from Dockerfiles (slower, picks up code changes). Use --build when Dockerfiles or dependencies change. Without it, only changed layers are rebuilt (Docker cache)."},
        {"q":"Q: How do you implement health checks in Docker Compose?","a":"A: Add healthcheck to service definition: healthcheck: { test: ['CMD', 'curl', '-f', 'http://localhost:8080/health'], interval: 30s, timeout: 10s, retries: 3 }. Use with depends_on: { condition: service_healthy } for proper startup ordering."},
        {"q":"Q: What is the difference between volumes and bind mounts in Docker Compose?","a":"A: Named volumes: Docker-managed, portable, stored in /var/lib/docker/volumes. Bind mounts: host directory mounted directly, faster for development (live code reload), but host-dependent. Use named volumes for data persistence; bind mounts for development code mounting."},
        {"q":"Q: How do you profile Docker Compose services for resource usage?","a":"A: docker stats shows real-time CPU/memory usage. docker compose top shows processes. docker system df shows disk usage. For production monitoring, use Prometheus + cAdvisor or Docker's built-in metrics endpoint (--metrics-addr on dockerd)."},
    ],
    'dnet': [
        {"q":"Q: What is Docker's embedded DNS server and when does it activate?","a":"A: 127.0.0.11 — activates on user-defined networks (not default bridge). Resolves container names, service names, and network aliases. On default bridge: no DNS, only IP communication. Always use custom networks (Compose creates them automatically)."},
        {"q":"Q: How do you set up DNS search domains for containers?","a":"A: Use dns_search in Compose or --dns-search on docker run. Example: dns_search: [example.com] means 'web' resolves to 'web.example.com'. Useful for services that expect FQDN resolution."},
        {"q":"Q: What is the difference between container name and service name in Docker?","a":"A: Service name: defined in Compose file, used for DNS resolution within the network. Container name: set with --name, used for docker commands (docker exec). Service name is the DNS hostname; container name is the Docker management identifier."},
        {"q":"Q: How do you implement network isolation between containers?","a":"A: (1) Separate custom networks for different tiers (frontend, backend, database), (2) Only connect containers to networks they need, (3) No inter-network communication by default. Compose example: frontend network for web+api, backend network for api+db."},
        {"q":"Q: What happens to container DNS when the container restarts?","a":"A: DNS entries are dynamic — recreated with the new IP. Container names remain the same across restarts (Compose preserves names). This is why using service names (not IPs) for inter-container communication is critical."},
    ],
    'helm': [
        {"q":"Q: What is the difference between helm install and helm upgrade --install?","a":"A: helm install: creates a new release (fails if release exists). helm upgrade --install: creates if not exists, upgrades if exists (idempotent). Use upgrade --install in CI/CD for idempotent deployments."},
        {"q":"Q: How do you manage Helm chart dependencies?","a":"A: helm dependency update ./chart pulls charts from repositories specified in Chart.yaml. Charts can be from Helm repos, OCI registries, or local paths. For Kustomize-like dependency management, use umbrella charts with subchart values."},
        {"q":"Q: What is Helm's release history and how do you use it?","a":"A: helm list shows releases. helm history shows revisions. helm rollback <release> <revision> restores a previous version. Default history limit is 10 revisions. Increase with --history-max for more rollback points."},
        {"q":"Q: How do you handle Helm secrets for sensitive values?","a":"A: (1) helm-secrets plugin (encrypts values.yaml with SOPS), (2) External Secrets Operator, (3) sealed-secrets (encrypt K8s secrets), (4) AWS Secrets Manager + ESO. Never commit plain-text secrets to git. helm-secrets is the most common pattern."},
        {"q":"Q: What is the difference between Helm hooks and Argo CD sync hooks?","a":"A: Helm hooks (pre-install, post-upgrade) run during helm install/upgrade. Argo CD hooks (PreSync, PostSync) run during git sync. Helm hooks are invisible to Argo CD. For GitOps: use Argo CD hooks instead of Helm hooks."},
    ],
    'iam-patterns': [
        {"q":"Q: What are the AWS managed policies for EKS workloads and when should you use them?","a":"A: AmazonEKSClusterPolicy (control plane), AmazonEKSWorkerNodePolicy (nodes), AmazonEKSCNIPolicy (VPC CNI), AmazonSSMManagedInstanceCore (SSM). For pods: use IRSA/Pod Identity with custom policies, not managed node policies."},
        {"q":"Q: How do you implement ABAC (Attribute-Based Access Control) for EKS?","a":"A: Use IAM policy conditions with resource tags. Example: s3:GetObject only when s3:ResourceTag/Environment matches the pod's environment tag. Combined with IRSA, each pod gets credentials that only access resources matching its attributes."},
        {"q":"Q: What is the difference between IAM policy condition keys and resource conditions?","a":"A: IAM conditions: evaluated when the API call is made (e.g. aws:SourceVpc, aws:CurrentTime). Resource conditions: evaluated against the resource's attributes (e.g. s3:ExistingObjectTag). Both add fine-grained access control layers."},
        {"q":"Q: How do you implement least privilege for a pod that reads S3 and writes CloudWatch?","a":"A: Two policy statements: (1) s3:GetObject on specific bucket/prefix ARN, (2) logs:CreateLogStream + PutLogEvents on specific log group ARN. Each statement is independently scoped. Never use s3:* or logs:*."},
        {"q":"Q: What is the Security Token Service (STS) and how does it relate to IRSA?","a":"A: STS issues temporary credentials (access key, secret key, session token) after AssumeRoleWithWebIdentity. IRSA/Pod Identity use STS to exchange Kubernetes service account tokens for AWS credentials. STS credentials auto-expire (default 1 hour) and are refreshed automatically."},
    ],
    'addons': [
        {"q":"Q: What is the difference between EKS add-ons and self-managed add-ons?","a":"A: EKS-managed: AWS handles version lifecycle, upgrades, and compatibility. Self-managed: you handle everything (DaemonSet manifests, upgrades, config). EKS-managed is preferred for CoreDNS, kube-proxy, VPC CNI, EBS CSI — less operational burden."},
        {"q":"Q: How do you customize EKS add-on configuration without losing it on upgrades?","a":"A: Use --resolve-conflicts PRESERVE when updating the add-on. For ConfigMaps: they're user-managed (not add-on-managed), so changes persist. For DaemonSet/Deployment changes: they may be overwritten on add-on update. Use launch template overrides for persistent customizations."},
        {"q":"Q: What happens if you manually edit an EKS add-on's DaemonSet?","a":"A: The add-on detects drift and may revert your changes on the next update cycle. Some changes (env vars, resources) are add-on-managed and will be overwritten. ConfigMaps are user-managed and persist. Check the add-on documentation for what's user-managed vs add-on-managed."},
        {"q":"Q: How do you rollback a failed EKS add-on update?","a":"A: aws eks update-addon --cluster-name my-cluster --addon-name vpc-cni --resolve-conflicts OVERWRITE with the previous version. Or: aws eks update-addon --cluster-name my-cluster --addon-name vpc-cni --configuration-values to adjust settings. The add-on rolls back the DaemonSet/Deployment."},
        {"q":"Q: Can you run multiple versions of an EKS add-on simultaneously?","a":"A: No — each add-on has one version cluster-wide. During a rolling update, old and new versions coexist briefly (pods on different nodes). But the add-on version is a cluster-level setting, not per-node."},
    ],
}

# Additional traps per flow
EXTRA_TRAPS = {
    'control': [
        'The API server is the <b>single point of entry</b> — all kubectl, controller, and kubelet communication goes through it.',
        'etcd is <b>not directly accessible</b> in EKS — only through the API server. Never try to SSH into etcd nodes.',
        'RBAC <b>deny rules</b> always override allow rules — a single deny blocks access regardless of other role bindings.',
    ],
    'nodes': [
        'Managed node groups <b>still require manual AMI updates</b> — AWS builds the AMI, you trigger the rollout.',
        'The <b>aws-auth ConfigMap</b> is the bridge between IAM and Kubernetes RBAC — get it wrong and nodes can\'t join.',
        'Fargate <b>doesn\'t support DaemonSets</b> — plan sidecar-based alternatives for node-level agents.',
    ],
    'fargate': [
        'Fargate resource requests are <b>rounded to fixed slots</b> — 0.3 vCPU becomes 0.5 vCPU, 2× the cost.',
        'Cold starts take <b>60-90 seconds</b> — significantly slower than EC2 nodes. Plan for latency-sensitive workloads.',
        'EFS is the <b>only persistent storage</b> option — no EBS, no local NVMe, no FSx.',
    ],
    'cni': [
        'VPC CNI assigns <b>real VPC IPs</b> — no overlay, but limited by ENI/IP density per instance type.',
        'Cross-AZ pod traffic <b>incurs AWS data transfer charges</b> (~$0.01/GB) — factor this into multi-AZ costs.',
        'The aws-node DaemonSet is <b>critical infrastructure</b> — if it crash-loops, new pods can\'t get IPs on that node.',
    ],
    'vpc': [
        'NAT Gateways cost <b>~$32/month each</b> — VPC endpoints for S3/ECR/STS can cut NAT costs by 60-80%.',
        'VPC CIDR changes require <b>recreating the VPC</b> — plan CIDRs carefully before deploying EKS.',
        'Private subnets need <b>either NAT Gateway or VPC endpoints</b> for outbound internet access.',
    ],
    'schedule': [
        'The scheduler <b>only talks to the API server</b> — it never communicates directly with kubelet.',
        'Pod priority and preemption can <b>evict low-priority pods</b> — use PriorityClasses carefully in production.',
        'Topology spread constraints are <b>more efficient than pod anti-affinity</b> at scale — prefer them for HA.',
    ],
    'docker': [
        'Containers <b>share the host kernel</b> — no hypervisor, no separate kernel, weaker isolation than VMs.',
        'Exit code 137 = SIGKILL (OOM) — <b>different from exit code 1</b> (app crash) or 143 (SIGTERM).',
        'CPU limits <b>throttle</b> (latency), memory limits <b>kill</b> (restart) — different failure modes.',
    ],
    'docker-secure': [
        'Multi-stage builds are <b>the only way</b> to truly exclude build tools from the final image.',
        'Distroless images have <b>no shell</b> — debugging requires tools like debug sidecar or ephemeral containers.',
        'Image signing proves <b>integrity</b> (not tampered); scanning proves <b>hygiene</b> (no CVEs) — different guarantees.',
    ],
    'svc': [
        'ClusterIP is <b>a virtual IP</b> — no process listens on it, no socket exists. It\'s purely a routing rule.',
        'EndpointSlices <b>replace monolithic Endpoints</b> for scalability — understand the difference.',
        'DNS resolution is <b>eventually consistent</b> — new services take a few seconds to appear in DNS.',
    ],
    'ingress': [
        'An Ingress resource <b>does nothing without a controller</b> — EKS has no built-in Ingress controller.',
        'ALB <b>IP target mode</b> is required for Fargate — Instance target mode doesn\'t work with serverless pods.',
        'Misaligned <b>deregistration delay</b> and terminationGracePeriodSeconds causes silent 502s during deploys.',
    ],
    'alb-nlb': [
        'ALB = L7 (HTTP routing, WAF). NLB = L4 (TCP/UDP, static IPs). <b>Choose based on protocol, not preference.</b>',
        'NLB <b>preserves client source IPs</b> — ALB does not (client IP is in X-Forwarded-For header).',
        'WAF <b>only works on ALB</b> — for NLB protection, use Security Groups and Shield.',
    ],
    'irsa': [
        'Trust policy condition must match the <b>exact namespace:SA pair</b> — copy-pasting breaks silently.',
        'OIDC provider must be <b>registered in IAM once per cluster</b> — a forgotten step that breaks all IRSA.',
        'IRSA tokens have <b>1-hour TTL</b> — the controller rotates them automatically, but stale tokens cause transient failures.',
    ],
    'pod-identity': [
        'Pod Identity is <b>EKS-only</b> — IRSA works on any Kubernetes distribution.',
        'The Pod Identity agent must be <b>installed on every node</b> — missing nodes can\'t inject credentials.',
        'Pod Identity and IRSA can <b>coexist</b> — migrate one service at a time.',
    ],
    'scale': [
        'HPA scales <b>pods</b>; Karpenter/CA scales <b>nodes</b> — conflating the two is the #1 mistake.',
        'metrics-server has <b>no history</b> — it can\'t answer "what was CPU usage an hour ago."',
        'VPA in Auto mode <b>fights with HPA</b> on the same metric — use VPA in Recommendation mode only.',
    ],
    'pdb': [
        'PDBs protect against <b>voluntary</b> disruptions only — crashes, OOM kills, and AWS force-termination ignore them.',
        '<code>minAvailable: 100%</code> on a single-replica Deployment <b>deadlocks</b> drains permanently.',
        'HPA scale-down <b>doesn\'t check PDBs</b> — it uses the ReplicaSet controller, not the Eviction API.',
    ],
    'storage': [
        'EBS volumes are <b>zonal</b> — pods rescheduled to a different AZ can\'t reattach the volume.',
        'CSI has <b>two components</b>: controller (cluster-wide) and node (per-node) — they serve different purposes.',
        '<code>WaitForFirstConsumer</code> avoids provisioning volumes in the wrong AZ — always use it.',
    ],
    'efs': [
        'EFS is the <b>only persistent storage for Fargate</b> — EBS, FSx, and local NVMe don\'t work.',
        'EFS throughput <b>scales with size</b> — small filesystems have low baseline throughput.',
        'NFS locking has <b>overhead</b> — high-concurrency writes may need architecture changes.',
    ],
    'rollout': [
        'A pod being "Running" <b>doesn\'t mean it\'s receiving traffic</b> — only Ready pods are in Endpoints.',
        '<code>kubectl rollout undo</code> works by pointing to a <b>kept, scaled-to-zero</b> ReplicaSet revision.',
        'Setting both maxSurge and maxUnavailable to 0 <b>deadlocks</b> the rollout completely.',
    ],
    'ecr': [
        '<code>:latest</code> + <code>imagePullPolicy: IfNotPresent</code> = <b>silent stale-image risk</b> in production.',
        'ECR basic scanning <b>only runs at push time</b> — enhanced scanning is needed for continuous CVE detection.',
        'Private clusters need <b>three VPC endpoints</b> for ECR: ecr.api, ecr.dkr, and S3 gateway.',
    ],
    'secrets': [
        'K8s Secrets are <b>base64, not encrypted</b> — confidentiality comes from RBAC, not encoding.',
        'Env var secrets are <b>frozen at container start</b> — volume mounts auto-refresh on change.',
        'Secrets Manager rotation and etcd encryption are <b>independent controls</b> — don\'t conflate them.',
    ],
    'nodefail': [
        'Spot rebalance recommendation (early, probabilistic) is <b>not the same</b> as interruption notice (2-minute, mandatory).',
        'PDBs can delay <b>voluntary</b> evictions but can\'t stop AWS from terminating the instance.',
        'The 5-minute pod-eviction-timeout exists to <b>prevent split-brain</b> on stateful workloads.',
    ],
    'upgrade': [
        'EKS control-plane upgrades are <b>one minor version at a time</b> — no skipping.',
        'Upgrading the control plane <b>doesn\'t upgrade add-ons or nodes</b> — three separate steps.',
        'Control-plane upgrades are <b>irreversible</b> — no in-place downgrade exists.',
    ],
    'ssm': [
        'SSM requires <b>zero inbound ports</b> — the agent connects outbound to SSM service.',
        'The session runs as <code>ssm-user</code>, not root — use <code>sudo</code> for elevated commands.',
        'SSM works in <b>fully private subnets</b> with VPC endpoints — no NAT needed.',
    ],
    'observability': [
        '<code>kubectl logs</code> only reads <b>local node logs</b> — if the node is gone, logs are gone.',
        'metrics-server and Prometheus are <b>architecturally different</b> — don\'t conflate them.',
        'HPA cannot query Prometheus directly — it needs an <b>adapter</b> for custom metrics.',
    ],
    'compose': [
        '<code>depends_on</code> waits for container <b>start</b>, not service <b>readiness</b> — use healthchecks.',
        '<code>docker compose down</code> keeps volumes; <code>down -v</code> <b>destroys</b> them.',
        'Compose v2 is the only maintained version — v1 (Python) is <b>end-of-life</b>.',
    ],
    'dnet': [
        '<b>localhost</b> inside a container is the container itself, not the host.',
        'Default bridge has <b>no DNS</b> — only user-defined networks do.',
        'Use <b>service names</b>, not IPs — container IPs change on every restart.',
    ],
    'helm': [
        'Helm templates are <b>not valid YAML until rendered</b> — debug with <code>helm template</code>.',
        'Kustomize has <b>no release concept</b> — rollback via git history.',
        'Helm hooks are <b>invisible to Argo CD</b> — use Argo CD hooks for GitOps.',
    ],
    'iam-patterns': [
        'Broad IAM policies are the <b>#1 blast radius risk</b> — one compromised pod gets everything.',
        'Both IAM policy AND resource policy must allow — <b>either can deny</b>.',
        'Use <b>CloudTrail</b> to observe actual API calls and tighten policies over time.',
    ],
    'addons': [
        'Add-on versions must match <b>control plane version</b> — check compatibility after upgrades.',
        'Auto-update covers <b>patch versions only</b> — minor updates are always manual.',
        'EBS CSI add-on still needs an <b>IRSA role</b> — the add-on doesn\'t create IAM roles.',
    ],
}

# Additional cheatsheet commands per flow
EXTRA_CHEAT = {
    'control': [
        'kubectl get --raw /readyz           # API server readiness',
        'kubectl get --raw /livez            # API server liveness',
        'kubectl api-resources               # list all API resource types',
        'kubectl get --raw /metrics | head   # API server metrics',
    ],
    'nodes': [
        'kubectl describe node <node> | grep -A10 Conditions',
        'kubectl get nodes --show-labels',
        'kubectl label node <node> my-label=value',
        'kubectl cordon <node>               # mark unschedulable',
    ],
    'fargate': [
        'kubectl describe pod <pod> | grep -A5 Events',
        'kubectl get events --field-selector reason=ScalingReplicaSet -A',
        'aws eks list-fargate-profiles --cluster-name my-cluster',
        'kubectl get pod <pod> -o jsonpath=\'{.spec.containers[*].resources}\'',
    ],
    'cni': [
        'kubectl -n kube-system exec -it <aws-node> -- ip addr show',
        'aws ec2 describe-instance-types --instance-types m5.large --query "InstanceTypes[].NetworkInfo"',
        'kubectl -n kube-system logs -l k8s-app=aws-node -c aws-node --tail=50',
        'kubectl get node <node> -o jsonpath=\'{.status.capacity}\'',
    ],
    'vpc': [
        'aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=vpc-xxx"',
        'aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=vpc-xxx"',
        'kubectl get nodes -o wide           # see AZ and subnet info',
        'aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-xxx"',
    ],
    'schedule': [
        'kubectl describe pod <pod> | grep -A5 Events   # scheduling failures',
        'kubectl get priorityclasses',
        'kubectl get pods --field-selector spec.nodeName=   # unscheduled pods',
        'kubectl get events --field-selector reason=FailedScheduling --sort-by=.lastTimestamp',
    ],
    'docker': [
        'docker inspect <container> --format=\'{{.State.Pid}}\'  # container PID on host',
        'docker diff <container>            # see filesystem changes',
        'docker commit <container> snapshot  # create image from running container',
        'docker stats                       # real-time resource usage',
    ],
    'docker-secure': [
        'trivy image --download-db-only      # update CVE database',
        'cosign verify --key cosign.pub <image>',
        'docker scout recommendations <image>',
        'kubectl get verifyingwebhookconfigurations  # check admission webhooks',
    ],
    'svc': [
        'kubectl get endpointslices -l kubernetes.io/service-name=myservice',
        'kubectl -n kube-system get cm coredns -o yaml',
        'kubectl exec -it debugpod -- nslookup myservice.default.svc.cluster.local',
        'kubectl get svc myservice -o yaml',
    ],
    'ingress': [
        'kubectl -n kube-system logs -l app.kubernetes.io/name=aws-load-balancer-controller --tail=100',
        'aws elbv2 describe-target-health --target-group-arn <arn>',
        'kubectl get targetgroupbindings -A',
        'kubectl describe ingress my-ingress | grep -A20 Rules',
    ],
    'alb-nlb': [
        'aws elbv2 describe-load-balancers --query "LoadBalancers[?Type==\'APPLICATION\']"',
        'aws elbv2 describe-target-groups --load-balancer-arn <arn>',
        'kubectl get svc -A --field-selector spec.type=LoadBalancer',
        'aws elbv2 describe-rules --listener-arn <arn>',
    ],
    'irsa': [
        'aws sts get-caller-identity          # verify current IAM identity',
        'kubectl exec -it mypod -- env | grep AWS_',
        'kubectl get sa -A -o json | grep role-arn',
        'aws iam list-attached-role-policies --role-name myapp',
    ],
    'pod-identity': [
        'aws eks list-pod-identity-associations --cluster-name my-cluster',
        'kubectl logs -n kube-system -l app.kubernetes.io/name=eks-pod-identity-agent',
        'aws eks describe-pod-identity-association --cluster-name my-cluster --association-id xxx',
        'kubectl get sa -A -o json | grep -v role-arn',
    ],
    'scale': [
        'kubectl get hpa -A -o wide',
        'kubectl top pods --sort-by=cpu',
        'kubectl get events --field-selector reason=FailedScheduling --sort-by=.lastTimestamp',
        'kubectl -n karpenter get nodeclaims,nodepools',
    ],
    'pdb': [
        'kubectl get pdb -A -o wide',
        'kubectl describe pdb <name>',
        'kubectl drain <node> --ignore-daemonsets --dry-run=server',
        'kubectl get pods -l app=myapp -o wide   # see distribution across nodes',
    ],
    'storage': [
        'kubectl get pv,pvc -A',
        'kubectl describe pvc <name> | grep -A5 Events',
        'kubectl -n kube-system get pods -l app=ebs-csi-controller',
        'aws ec2 describe-volumes --filters "Name=tag:kubernetes.io/created-for/pvc/name,Values=mypvc"',
    ],
    'efs': [
        'kubectl get sc | grep efs',
        'kubectl -n kube-system get pods -l app=efs-csi-controller',
        'aws efs describe-file-systems --query "FileSystems[].FileSystemId"',
        'kubectl get pvc -A | grep ReadWriteMany',
    ],
    'rollout': [
        'kubectl rollout status deployment/myapp',
        'kubectl rollout history deployment/myapp',
        'kubectl rollout undo deployment/myapp --to-revision=2',
        'kubectl get rs -l app=myapp --sort-by=.metadata.creationTimestamp',
    ],
    'ecr': [
        'aws ecr describe-repositories --query "repositories[?contains(repositoryName,\'myapp\')]"',
        'aws ecr describe-image-scan-findings --repository-name myapp --image-id imageTag=v1',
        'aws ecr get-lifecycle-policy --repository-name myapp',
        'crictl pull <image>                  # test pull directly on node',
    ],
    'secrets': [
        'kubectl get secret mysecret -o jsonpath="{.data.password}" | base64 -d',
        'kubectl describe externalsecret myapp-secret',
        'kubectl get sa myapp -o yaml',
        'aws eks describe-cluster --name my-cluster --query "cluster.encryptionConfig"',
    ],
    'nodefail': [
        'kubectl get nodes -o wide --watch',
        'kubectl describe node <node> | grep -A10 Conditions',
        'kubectl get events --field-selector involvedObject.kind=Node --sort-by=.lastTimestamp',
        'kubectl get nodeclaims,nodepools   # Karpenter-specific',
    ],
    'upgrade': [
        'aws eks describe-cluster --name my-cluster --query "cluster.version"',
        'aws eks describe-addon-versions --kubernetes-version 1.30',
        'kubectl get nodes -o custom-columns=NAME:.metadata.name,KUBELET:.status.nodeInfo.kubeletVersion',
        'pluto detect-api-resources -d ./manifests',
    ],
    'ssm': [
        'aws ssm describe-instance-information --filters "Key=PlatformTypes,Values=Linux"',
        'aws ssm list-documents --filters "Key=Owner,Values=Amazon"',
        'kubectl get node <name> -o jsonpath=\'{.spec.providerID}\'',
        'aws ssm start-session --target i-xxx --document-name AWS-StartPortForwardingSession --parameters \'{"portNumber":["8080"],"localPortNumber":["8080"]}\'',
    ],
    'observability': [
        'kubectl logs pod --previous         # logs from crashed pod',
        'kubectl get apiservices | grep metrics',
        'aws amp list-workspaces',
        'kubectl -n kube-system get cm coredns -o yaml | grep -A5 forwarders',
    ],
    'compose': [
        'docker compose ps -a                # all services including stopped',
        'docker compose images               # image sizes per service',
        'docker compose config               # validate and render compose file',
        'docker compose cp service:/path /host/path   # copy files',
    ],
    'dnet': [
        'docker network inspect <network>   # see all containers and IPs',
        'docker network connect <network> <container>   # attach to network',
        'docker network disconnect <network> <container>',
        'docker run --rm alpine nslookup <service>      # test DNS',
    ],
    'helm': [
        'helm lint ./mychart                 # check chart for issues',
        'helm show values ./mychart          # display default values',
        'helm search repo <keyword>          # find charts in repos',
        'helm plugin list                    # installed plugins',
    ],
    'iam-patterns': [
        'aws iam simulate-principal-policy --policy-source-arn <arn> --action-names s3:GetObject',
        'aws cloudtrail lookup-events --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=ASIAxxx',
        'kubectl get sa myapp -o jsonpath=\'{.metadata.annotations}\'',
        'aws iam list-policies --scope Local   # customer-managed policies',
    ],
    'addons': [
        'aws eks list-addons --cluster-name my-cluster',
        'aws eks describe-addon --cluster-name my-cluster --addon-name vpc-cni',
        'kubectl -n kube-system get deploy,ds --show-labels',
        'aws eks update-addon --cluster-name my-cluster --addon-name vpc-cni --resolve-conflicts PRESERVE',
    ],
}


def enhance_flow(flow_text, flow_id):
    """Enhance a single flow with extra Q&A, traps, and cheatsheet commands."""
    
    # Add extra Q&A pairs to steps using brace-counting parser
    if flow_id in EXTRA_QA:
        extra_qa_list = EXTRA_QA[flow_id]
        qa_idx = 0
        
        # Find all qa:{...} blocks by scanning for "qa:{" and counting braces
        result = []
        i = 0
        while i < len(flow_text):
            # Look for qa:{ pattern
            qa_pos = flow_text.find('qa:{', i)
            if qa_pos == -1:
                result.append(flow_text[i:])
                break
            
            # Add everything before this qa block
            result.append(flow_text[i:qa_pos])
            
            # Count braces to find the end of the qa object
            depth = 0
            j = qa_pos + 3  # skip "qa:"
            while j < len(flow_text):
                if flow_text[j] == '{':
                    depth += 1
                elif flow_text[j] == '}':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            
            # Extract the full qa:{...} block
            qa_block = flow_text[qa_pos:j+1]
            result.append(qa_block)
            
            # Add extra Q&A if available
            if qa_idx < len(extra_qa_list):
                extra = extra_qa_list[qa_idx]
                qa_idx += 1
                q_text = extra["q"].replace("'", "\\'")
                a_text = extra["a"].replace("'", "\\'")
                insertion = ",qa2:{q:'" + q_text + "',a:'" + a_text + "'}"
                result.append(insertion)
            
            i = j + 1
        
        flow_text = ''.join(result)
    
    # Add extra traps
    if flow_id in EXTRA_TRAPS:
        extra_traps = EXTRA_TRAPS[flow_id]
        for trap in extra_traps:
            escaped_trap = trap.replace("'", "\\'")
            traps_start = flow_text.find('traps:[')
            if traps_start != -1:
                # Find ], on its own line (with indentation) after traps:
                m = re.search(r'\n  \],\n  cheat:', flow_text[traps_start:])
                if m:
                    insert_pos = traps_start + m.start()
                    flow_text = flow_text[:insert_pos] + "\n    '" + escaped_trap + "',\n" + flow_text[insert_pos:]
    
    # Add extra cheatsheet commands
    if flow_id in EXTRA_CHEAT:
        extra_cmds = EXTRA_CHEAT[flow_id]
        for cmd in extra_cmds:
            escaped_cmd = cmd.replace("'", "\\'")
            cheat_start = flow_text.find('cheat:[')
            if cheat_start != -1:
                # Find ]} on its own line (end of cheat array, before flow closing })
                m = re.search(r'\n  \]\}', flow_text[cheat_start:])
                if m:
                    insert_pos = cheat_start + m.start()
                    flow_text = flow_text[:insert_pos] + "\n    '" + escaped_cmd + "',\n" + flow_text[insert_pos:]
    
    return flow_text


def main():
    input_file = '/Users/premchand/projects/git/md-courses/k8s.html'
    output_file = '/Users/premchand/projects/git/md-courses/k8s_enhanced.html'
    
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Find the FLOWS array
    flows_start = content.find('const FLOWS = [')
    if flows_start == -1:
        print("Could not find FLOWS array")
        return
    
    # Find each flow by its id and enhance it
    flow_ids = list(EXTRA_QA.keys())
    enhanced_content = content
    
    for flow_id in flow_ids:
        # Find the flow's start position
        pattern = f"{{ id:'{flow_id}'"
        pos = enhanced_content.find(pattern)
        if pos == -1:
            print(f"Could not find flow: {flow_id}")
            continue
        
        # Find the flow's end - look for the next flow's start or the array end
        # Count braces to find the matching closing brace
        depth = 0
        i = pos
        flow_started = False
        while i < len(enhanced_content):
            if enhanced_content[i] == '{':
                depth += 1
                flow_started = True
            elif enhanced_content[i] == '}':
                depth -= 1
                if flow_started and depth == 0:
                    # Found the end of this flow object
                    flow_text = enhanced_content[pos:i+1]
                    enhanced_flow = enhance_flow(flow_text, flow_id)
                    enhanced_content = enhanced_content[:pos] + enhanced_flow + enhanced_content[i+1:]
                    print(f"Enhanced flow: {flow_id}")
                    break
            i += 1
    
    with open(output_file, 'w') as f:
        f.write(enhanced_content)
    
    print(f"\nEnhanced file written to: {output_file}")
    print(f"Original size: {len(content)} chars")
    print(f"Enhanced size: {len(enhanced_content)} chars")
    print(f"Added: {len(enhanced_content) - len(content)} chars")


if __name__ == '__main__':
    main()
