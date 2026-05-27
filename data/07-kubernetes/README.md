# 07 — Kubernetes

The de facto container orchestration platform. This domain covers Kubernetes core concepts, networking, security, storage, observability, performance tuning, GitOps, policy engines (OPA/Kyverno), service mesh (Istio, Linkerd), operator pattern, and production operations at scale.

## Table of Contents

- [Core Concepts](#core-concepts)
  - [Architecture](#architecture)
  - [Pods & Workloads](#pods--workloads)
  - [Services & Networking Basics](#services--networking-basics)
  - [Configuration & Secrets](#configuration--secrets)
  - [Storage Basics](#storage-basics)
  - [RBAC & Security Basics](#rbac--security-basics)
- [Networking](#networking)
  - [CNI Plugins](#cni-plugins)
  - [Service Mesh](#service-mesh)
  - [Ingress & Gateway API](#ingress--gateway-api)
  - [Network Policies](#network-policies)
  - [DNS & Service Discovery](#dns--service-discovery)
- [Security](#security)
  - [Pod Security](#pod-security)
  - [Authentication & Authorization](#authentication--authorization)
  - [Secret Management](#secret-management)
  - [Supply Chain Security](#supply-chain-security)
  - [Runtime Security](#runtime-security)
- [Storage](#storage)
  - [Volumes & Persistent Volumes](#volumes--persistent-volumes)
  - [Storage Classes & Provisioners](#storage-classes--provisioners)
  - [CSI Drivers](#csi-drivers)
  - [Stateful Workloads](#stateful-workloads)
  - [Backup & Disaster Recovery](#backup--disaster-recovery)
- [Observability](#observability)
  - [Metrics & Monitoring](#metrics--monitoring)
  - [Logging](#logging)
  - [Tracing](#tracing)
  - [Events & Audit](#events--audit)
  - [Cost Monitoring](#cost-monitoring)
- [Performance Tuning](#performance-tuning)
  - [Cluster Autoscaling](#cluster-autoscaling)
  - [Workload Optimization](#workload-optimization)
  - [Resource Management](#resource-management)
  - [Network Performance](#network-performance)
  - [Control Plane Performance](#control-plane-performance)
- [GitOps](#gitops)
  - [Principles](#principles)
  - [ArgoCD](#argocd)
  - [Flux CD](#flux-cd)
  - [Progressive Delivery](#progressive-delivery)
- [Policy & Governance](#policy--governance)
  - [OPA / Gatekeeper](#opa--gatekeeper)
  - [Kyverno](#kyverno)
  - [Admission Controllers](#admission-controllers)
  - [Compliance & Auditing](#compliance--auditing)
- [Operators](#operators)
  - [Operator Pattern](#operator-pattern)
  - [Operator SDK](#operator-sdk)
  - [Common Operators](#common-operators)
- [Production Operations](#production-operations)
  - [Cluster Lifecycle](#cluster-lifecycle)
  - [Upgrades](#upgrades)
  - [Disaster Recovery](#disaster-recovery)
  - [Multi-Cluster](#multi-cluster)
  - [Troubleshooting](#troubleshooting)
- [Learning Path](#learning-path)
- [Cross-References](#cross-references)

---

## Core Concepts

### Architecture

- **Control Plane** — kube-apiserver (REST API gateway), etcd (distributed key-value store), kube-scheduler (Pod placement), kube-controller-manager (reconciliation loops: node, deployment, namespace, service account, etc.), cloud-controller-manager (cloud-specific: LB, nodes, routes, volumes)
- **Worker Nodes** — kubelet (node agent, Pod lifecycle), kube-proxy (network rules, iptables/IPVS), container runtime (containerd, CRI-O, Docker via cri-dockerd), CRI (Container Runtime Interface)
- **etcd** — consistent, highly-available key-value store; raft consensus; 3-5 nodes recommended; TLS encryption, snapshot/restore, defragmentation; 8GB default limit (configurable)
- **API Server** — the only component that talks to etcd; authentication, authorization, admission, validation, mutation; watch mechanism (long-polling)
- **Workflow** — user submits YAML → kube-apiserver (authn + authz + admission) → validation → stored in etcd → controller watches → scheduler places Pod → kubelet creates container

### Pods & Workloads

- **Pods** — smallest deployable unit; one or more containers, shared network namespace, shared volumes; init containers, sidecar containers, ephemeral containers
- **Workload Resources** — Deployment (stateless, replicas, rollout strategies), StatefulSet (stateful, stable identity, ordered deployment), DaemonSet (one Pod per node), Job (short-lived tasks), CronJob (scheduled tasks), ReplicaSet (declarative replica management), RC (Replication Controller, legacy)
- **Pod Lifecycle** — Pending → Running → Succeeded/Failed; container states: Waiting (CrashLoopBackOff, ImagePullBackOff, Init), Running, Terminated
- **Probes** — liveness (is app alive? restart if fails), readiness (can it serve traffic? remove from Service if fails), startup (slow-start apps, disable other probes until done); supported: httpGet, tcpSocket, exec (command), gRPC (1.24+)
- **Pod Disruption Budgets** — minAvailable/maxUnavailable for voluntary disruptions (draining, updates)
- **Topology Spread Constraints** — spread Pods across zones, nodes, or regions; maxSkew, topologyKey, whenUnsatisfiable
- **Resource QoS Classes** — Guaranteed (limits = requests for all containers), Burstable (at least one container has request < limit), BestEffort (no requests/limits set)

### Services & Networking Basics

- **ClusterIP** — internal virtual IP (iptables/IPVS), round-robin across Pods; default Service type
- **NodePort** — static port on every node (30000-32767); ingress through node IP:NodePort
- **LoadBalancer** — cloud LB provisioned (ALB/NLB, GCP TCP/HTTP LB, Azure LB); external-dns, aws-load-balancer-controller for advanced config
- **ExternalName** — DNS CNAME to external service (no proxy, no selectors)
- **Headless Service** — clusterIP=None; DNS returns Pod IPs (used by StatefulSets, custom discovery)
- **Endpoints & EndpointSlices** — mapping Service to Pod IPs; EndpointSlice scales better (10k endpoints per slice vs. 1k for Endpoints)
- **DNS** — CoreDNS (default), kube-dns (legacy); Service DNS patterns: `<svc>.<ns>.svc.cluster.local`, Pod DNS: `<pod-ip>.<ns>.pod.cluster.local`

### Configuration & Secrets

- **ConfigMaps** — key-value configuration; consumed as environment variables, command-line args, or volumes (files); immutable ConfigMap (v1.21+)
- **Secrets** — base64-encoded (not encrypted by default); types: Opaque, kubernetes.io/service-account-token, kubernetes.io/dockercfg, kubernetes.io/tls, bootstrap.kubernetes.io/token
- **Downward API** — expose Pod/Node metadata to containers via env vars or volume files (name, namespace, UID, labels, annotations, node name, service account, request/limits)
- **Environment Variable Sources** — ConfigMap key reference, Secret key reference, field reference (downward API), resource field reference (CPU, memory)
- **encryption at rest** — encrypt etcd data; AES-CBC, AES-GCM, KMS provider (AWS KMS, GCP Cloud KMS, Azure Key Vault); rotation policies

### Storage Basics

- **EmptyDir** — ephemeral volumes, shares Pod lifetime; medium: Memory (tmpfs) for high performance
- **hostPath** — node filesystem (security risk, prefer alternatives); used by DaemonSets (kube-proxy, node-exporter)
- **ConfigMap/Secret/DownwardAPI** — mounted as volumes (read-only)
- **PersistentVolume (PV)** — cluster-wide storage resource provisioned by admin; reclaim policy (Retain, Delete, Recycle)
- **PersistentVolumeClaim (PVC)** — storage request by user; access modes (ReadWriteOnce, ReadOnlyMany, ReadWriteMany, ReadWriteOncePod)
- **StorageClass** — dynamic provisioning; provisioner (EBS, EFS, GCE PD, CSI), parameters (type, IOPS, replication), reclaim policy, allowVolumeExpansion, mountOptions
- **Volume Snapshots** — CSI snapshot support; restore from snapshot, clone volume
- **Volume Expansion** — resize PVC (if StorageClass supports), online vs offline expansion

### RBAC & Security Basics

- **ServiceAccount** — identity for Pods (non-human); automatically mounted (token in /var/run/secrets/kubernetes.io/serviceaccount/); token request API for time-limited tokens (v1.24+)
- **Role & ClusterRole** — rules: apiGroups, resources, verbs, resourceNames, nonResourceURLs; Role is namespace-scoped, ClusterRole is cluster-scoped
- **RoleBinding & ClusterRoleBinding** — bind Role to subjects (User, Group, ServiceAccount); same namespace (RoleBinding) or cluster (ClusterRoleBinding)
- **RBAC Best Practices** — least privilege, use groups, no cluster-admin for dev, audit role assignments
- **SecurityContext** — runAsUser, runAsGroup, fsGroup, runAsNonRoot, privileged, capabilities (add/drop), seLinuxOptions, seccompProfile, appArmorProfile, readOnlyRootFilesystem, allowPrivilegeEscalation, procMount
- **PodSecurity Admission** — replaces PSP (PodSecurityPolicy, removed v1.25); predefined profiles: privileged, baseline, restricted; enforce, audit, warn modes

---

## Networking

### CNI Plugins

- **CNI (Container Network Interface)** — spec for networking plugins; built-in: bridge, ipvlan, macvlan, loopback; third-party: Calico, Flannel, Weave, Cilium, AWS VPC CNI, Azure CNI, GKE Dataplane V2 (Cilium-based)
- **Calico** — BGP-based, network policies, IP-in-IP or VXLAN encapsulation; Felix (agent), BIRD (BGP daemon), confd; eBPF data plane (option)
- **Cilium** — eBPF-based; replaces kube-proxy, L3-L7 policies (HTTP/gRPC/kafka), Hubble (observability), service mesh (with Envoy), transparent encryption (WireGuard); best choice for modern clusters
- **Flannel** — overlay network (VXLAN, host-gw, UDP); simple, no network policies (combine with Calico for policies)
- **AWS VPC CNI** — native VPC IP (no overlay); ENI-based, IPv4/IPv6, custom networking; security groups per Pod; prefix delegation for scale
- **Multus** — multiple network interfaces per Pod (SR-IOV, DPDK, MACVLAN); telco/NFV workloads

### Service Mesh

- **Istio** — sidecar proxy (Envoy), control plane (istiod: Pilot, Citadel, Galley); traffic management (routing, mirroring, circuit breaking), security (mTLS, authorization policies), observability (metrics, tracing, access logs)
- **Linkerd** — Rust-based proxy (linkerd-proxy), ultra-light; control plane (destination, identity, proxy-injector); tap (live traffic inspection), mTLS automagic; simpler than Istio
- **Envoy** — L3/L4/L7 proxy; xDS APIs for dynamic config; HTTP/2, gRPC, WebSocket, TCP; extensive filter chain (rate limiting, RBAC, Lua, WASM); the data plane for Istio, Consul, AWS App Mesh, Gloo
- **Consul Connect** — service mesh by HashiCorp; sidecar + native proxy; intentions (RBAC for services); integrated with Consul service discovery
- **Ambient Mesh (Istio)** — sidecar-less mesh; ztunnel (per-node proxy), waypoint proxy (per-namespace); lighter resource footprint
- **When to use** — Service mesh adds latency (1-3ms) and resource overhead (Envoy ~20-50MB per sidecar); use for strict mTLS, advanced traffic splitting, comprehensive observability

### Ingress & Gateway API

- **Ingress** — (classic) L7 HTTP/HTTPS routing; annotations (cloud-specific), path-based, SSL termination, hosted zone
- **Ingress Controllers** — ingress-nginx (NGINX-based), HAProxy, Traefik, AWS Load Balancer Controller (ALB), GKE Ingress (HTTP LB), AZure Application Gateway Ingress Controller (AGIC); Kong, Skipper, Contour (Envoy-based)
- **Gateway API** — successor to Ingress (v1.0+); role-oriented: GatewayClass (infra provider), Gateway (operational), HTTPRoute/TCPRoute/etc (application); cross-namespace routing, header matching/mirroring, traffic splitting (weighted)
- **Implementations** — Istio, Contour, Envoy Gateway, Kong, Traefik, GKE Gateway controller, AWS VPC Lattice

### Network Policies

- **NetworkPolicy** — podSelector (target), policyTypes (Ingress/Egress/ both), ingress rules (from: podSelector, namespaceSelector, ipBlock), egress rules (to: same selectors + ports)
- **Enforcement** — requires a CNI that implements network policies (Calico, Cilium, Weave, Antrea); without enforcement, policies apply to no resource
- **Default Deny** — default-allow → best practice: create default-deny ingress/egress policies, then allow required traffic
- **CiliumNetworkPolicy** — Cilium-specific policy with L7 rules (HTTP methods, paths, Kafka topics, gRPC services)

### DNS & Service Discovery

- **CoreDNS** — internal cluster DNS; add-ons: rewrite (domain rewrites), kubernetes (service discovery), forward (external DNS), prometheus (metrics), cache, hosts (static entries)
- **NodeLocal DNSCache** — DaemonSet cache on each node; reduces DNS queries to CoreDNS, improves DNS performance (especially with cluster-dns queries)
- **ExternalDNS** — syncs Ingress/Service resources with cloud DNS (Route 53, Cloud DNS, Azure DNS); annotation-based
- **Service Discovery Patterns** — straight DNS lookup, headless service for StatefulSet Pod DNS, SRV records for port discovery

---

## Security

### Pod Security

- **Pod Security Standards** — restricted (most secure), baseline, privileged (least secure); PodSecurityConfiguration per namespace
- **Seccomp** — restrict system calls; seccompProfile (RuntimeDefault, Localhost, Unconfined); Kubernetes seccomp is GA
- **AppArmor / SELinux** — mandatory access control; profile-based restrictions on container processes
- **Capabilities** — drop ALL capabilities, add specific ones (NET_BIND_SERVICE for port < 1024); avoid NET_RAW+SYS_ADMIN+SYS_PTRACE
- **ReadOnly Root Filesystem** — containers should not write to rootfs; use emptyDir for temp writes
- **runAsNonRoot** — enforce non-root user; securityContext.runAsNonRoot: true + runAsUser

### Authentication & Authorization

- **Authentication modules** — X509 (client certificates), static tokens, bootstrap tokens, OIDC, service account tokens, webhook token authentication
- **OIDC** — integrate with identity providers (Okta, Keycloak, Azure AD, Google); group-based RBAC
- **x509** — client certs for admin access; kubeconfig: client-certificate-data/client-key-data
- **Webhooks** — TokenReview API for custom auth; ImageReview API for image verification
- **Authorization modules** — RBAC (default), ABAC (legacy), Webhook, Node (for kubelet)
- **Node Authorization** — kubelet authorization; NodeRestriction admission controller

### Secret Management

- **External Secrets Operator** — sync secrets from external providers (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, Vault, 1Password) into Kubernetes Secrets
- **Sealed Secrets** — encrypt Secret into SealedSecret; only sealed-secrets controller can decrypt; safe to commit to Git
- **KMS Encryption** — encrypt etcd secrets at rest; AWS KMS + EKS, GCP KMS, Azure Key Vault
- **Vault** — HashiCorp Vault + Vault Agent Injector (mutating webhook); sidecar pulls secrets, writes to shared volume; dynamic secrets, leases, rotations
- **SOPS** — encrypt secrets in Git (age, PGP, KMS); decrypt at deploy time with Helm/Flux/Argo

### Supply Chain Security

- **Image Signing** — Cosign (Sigstore) for signing + verifying container images; keyless signing with OIDC
- **Image Policy Webhook** — admission controller to verify image signatures before Pod creation
- **Binary Authorization** (GKE) — enforce signed images at deploy time
- **SLSA Framework** — supply chain levels for software artifacts; build integrity, provenance
- **SBOM** — software bill of materials; generate with Syft, build attestations with Cosign

### Runtime Security

- **Falco** — cloud-native runtime security; eBPF + kernel module; detects anomalous behavior (shell in container, privilege escalation, file changes)
- **Tracee** — eBPF runtime security; captures syscalls, container behavior at low overhead
- **Tetragon** — Cilium-based runtime security; eBPF hooks, security observability + enforcement
- **KubeArmor** — LSM-based (AppArmor, SELinux) container-aware security policy enforcement

---

## Storage

### Volumes & Persistent Volumes

- **PV/PVC Binding** — immediate (match on spec) vs WaitForFirstConsumer (bind after Pod scheduling; topology-aware)
- **Access Modes** — ReadWriteOnce (RWO, single node), ReadOnlyMany (ROX, many nodes), ReadWriteMany (RWX, many nodes), ReadWriteOncePod (single Pod, v1.22+)
- **Volume Modes** — Filesystem (mounted into Pod) vs Block (raw block device)
- **Reclaim Policy** — Retain (admin reclaims manually), Delete (automatically delete PV + storage), Recycle (scrub + re-use, deprecated)

### Storage Classes & Provisioners

- **AWS** — gp2/gp3/io1/io2 (EBS), efs (EFS for RWX), fsx (FSx for Lustre/ONTAP)
- **GCP** — pd-standard/pd-balanced/pd-ssd/pd-extreme (GCE PD), filestore (NFS), gce-pd (regional PD)
- **Azure** — managed-csi (premium/standard SSD/HDD), azurefile (Azure Files for RWX)
- **Portworx** — software-defined storage, container-native; replication, snapshots, encryption, DR
- **Rook (Ceph)** — Ceph on Kubernetes; block, filesystem, object stores (S3); self-managing, self-healing
- **Longhorn** — lightweight block storage (Rancher); distributed, replicated, snapshots, backup to S3/NFS
- **OpenEBS** — container-attached storage; Mayastor (NVMe), cStor, Local PV

### CSI Drivers

- **CSI (Container Storage Interface)** — standard for exposing storage systems to containers
- **CSI Driver Lifecycle** — identity, controller, node services; create/delete volume, publish/unpublish, mount/unmount
- **CSI Volume Cloning** — clone a PVC from another PVC (must be same storage class)
- **CSI Volume Snapshots** — VolumeSnapshotClass, VolumeSnapshot, VolumeSnapshotContent; restore to new PVC
- **CSI Topology** — constrain volume to specific topology (region, zone, node)

### Stateful Workloads

- **StatefulSet** — stable network identity (pod-{0..N-1}.service.namespace), stable storage (each Pod has own PVC), ordered deployment and scaling, ordered graceful deletion; MaxUnavailable for parallel rolling updates
- **Headless Service** — required for StatefulSet DNS identity
- **VolumeClaimTemplate** — per-Pod PVC definitions in StatefulSet
- **StatefulSet Strategies** — RollingUpdate (default, partition for phased rollouts), OnDelete (manual Pod deletion triggers recreate)

### Backup & Disaster Recovery

- **Velero** — backup/restore cluster resources + PV snapshots; schedules, retention, restore hooks, migration across clusters
- **etcd Backup** — etcd snapshot (snapshot.db); restore to new cluster; critical for cluster recovery
- **Stork** — storage orchestration for DR; migration of stateful workloads across clusters
- **Cross-cluster DR** — backup/restore with Velero, replication with Rook, active-passive vs active-active

---

## Observability

### Metrics & Monitoring

- **Prometheus** — core metrics system; pull model, service discovery (K8s API), TSDB, PromQL, alerting (Alertmanager), recording rules
- **kube-state-metrics** — cluster-level metrics (deployments, nodes, pods, resource quotas)
- **node-exporter** — node-level (CPU, memory, disk, network)
- **cAdvisor** — built-in container metrics (CPU, memory, network, filesystem per container)
- **Grafana** — dashboards, alerting; pre-built dashboards for K8s (K8s mixin, node-exporter, Istio, etc.)
- **Thanos** — long-term storage (S3/GCS/Azure), global query view across clusters, downsampling, compactor
- **Cortex / Mimir** — horizontally scalable Prometheus; multi-tenant, long-term storage

### Logging

- **Fluentd / Fluent Bit** — log forwarder; DaemonSet, tail container logs, parse (JSON, regex), output (Elasticsearch, Loki, S3, Cloud Logging)
- **Loki** — log aggregation (like Prometheus but for logs); label-based indexing, push model, LogQL, multi-tenancy
- **Elasticsearch + Kibana** — full-text search; heavy resource consumption; being replaced by Loki in many deployments
- **Vector** — lightweight log/metric aggregator; VRL (Vector Remap Language) for transformation
- **Cluster Audit Logging** — Kubernetes API audit logs (policy-based, capture requests, responses, users)

### Tracing

- **OpenTelemetry** — unified standard for traces, metrics, logs; OTel Operator (auto-instrumentation), OTel Collector (receiver, processor, exporter)
- **Jaeger** — distributed tracing, trace storage (Elasticsearch, Badger, Cassandra), sampling strategies
- **Tempo** — Grafana's tracing backend, cheap object storage
- **Service Mesh Tracing** — Istio + Envoy generates trace context (x-request-id, x-b3-traceid); Zipkin/OTel integration

### Events & Audit

- **kubectl get events** — cluster events (Pod scheduling, failures, scaling); limited retention
- **EventRouter** — forward Kubernetes events to external sinks
- **Kuberhealthy** — synthetic monitoring for K8s (availability tests for Deployments, DNS, etc.)
- **Audit Logging** — API server audit logs; policy (none, metadata, request, requestResponse); capture for SOC/compliance

### Cost Monitoring

- **Kubecost** — real-time cost allocation (CPU, memory, GPU, storage, network); namespace/label/ deployment breakdown; savings recommendations (RIs, spot, right-sizing, cluster turndown)
- **OpenCost** — CNCF sandbox; open-source cost monitoring; standard for cost allocation
- **cloud cost + K8s** — EC2/EKS pricing; Fargate vs EC2 cost analysis

---

## Performance Tuning

### Cluster Autoscaling

- **Cluster Autoscaler** — adds/removes nodes based on unschedulable Pods; cloud-specific: AWS (ASG), GCP (MIG, Node Group), Azure (VMSS); scale-up speed vs scale-down safety; expander (random, most-packs, least-waste, priority)
- **Karpenter** — next-gen autoscaler for AWS EKS; direct EC2 API, faster (sub-minute scale-up), consolidation (right-size/replace), bin-packing, flexible instance types
- **Vertical Pod Autoscaler** — recommend/adjust CPU/memory requests based on usage; update mode: off (recommendation only), initial (apply at Pod creation), auto (update live Pods)

### Workload Optimization

- **Resource Requests & Limits** — set requests for scheduling (guaranteed resources), limits for throttling (CPU throttling if exceeded CPU limit, OOM if exceeded memory limit)
- **Pod Priority & Preemption** — PriorityClass (value); higher priority Pods can preempt lower priority Pods
- **Horizontal Pod Autoscaler** — scale based on metrics (CPU, memory, custom, external); stabilization window, scale-up/down behavior, metrics target
- **Topology Management** — CPU manager policy, device manager, NUMA-aware scheduling; CRIs and hardware topology

### Resource Management

- **ResourceQuota** — total CPU/memory/storage per namespace; count quota for objects (pods, deployments, services, secrets)
- **LimitRange** — default request/limit per container in namespace; min/max constraints
- **Quality of Service** — Guaranteed (requests == limits), Burstable (requests < limits), BestEffort (no requests/limits)
- **Node Resource Management** — system reserved, kubelet reserved, eviction thresholds (memory, disk, PID)

### Network Performance

- **eBPF** — in-kernel programmability; Cilium uses eBPF for networking, observability, security; replaces iptables (faster, more scalable)
- **MTU tuning** — Jumbo frames (9000 MTU) on supported networks; adjust overlay MTU (VXLAN overhead: 50 bytes)
- **TCP tuning** — keepalive, buffer sizes (tcp_rmem, tcp_wmem), congestion control (BBR)
- **SR-IOV** — direct NIC access to Pods (zero-copy); low latency, high throughput
- **DPDK** — userspace packet processing; bypass kernel; telco/NFV use cases

### Control Plane Performance

- **etcd Tuning** — disk I/O (SSD/NVMe), network latency, snapshot frequency, compaction; defrag regularly
- **API Server Rate Limits** — max-in-flight, max-mutating-in-flight; client-side (controller-manager, scheduler) QPS/burst
- **Conntrack** — connection tracking table size; adjust nf_conntrack_max, nf_conntrack_tcp_timeouts
- **Node Capacity** — max Pods per node (default 110, AWS VPC CNI default 20), cluster max node count

---

## GitOps

### Principles

- **Declarative Desired State** — everything defined in Git (apps, config, infra, policies)
- **Single Source of Truth** — Git repo is the only source; any drift is detected and reconciled
- **Automated Sync** — operator continuously syncs cluster state to Git state
- **Pull-based Deployment** — operator in cluster pulls from Git (vs push from CI); better security (no cluster creds in CI)

### ArgoCD

- **Application CRD** — source (Git repo path + revision), destination (cluster + namespace), sync policy (manual/auto), health status
- **ApplicationSet** — generators: list, git, clusters, SCM, pull request, matrix; template-based repetitive app creation
- **Sync Options** — prune (delete missing resources), selfHeal (revert manual changes if auto-sync), Replace (force replace), SkipSchemaValidation, ApplyOutOfSyncOnly
- **Sync Waves** — order resource creation (0 default, negative = before, positive = after)
- **Hooks** — pre-sync, sync, post-sync, sync-fail; defined as Jobs in the same manifest; skipOnSuccess?
- **SSO & RBAC** — OIDC (Dex, Keycloak, Okta, Azure AD), GitHub/GitLab; project-level RBAC
- **Notifications** — templates, triggers, subscriptions (Slack, email, webhook); notification-controller

### Flux CD

- **Source Controller** — reconcile Git repos, Helm repos, Buckets, OCI artifacts
- **Kustomize Controller** — apply kustomize overlays to cluster
- **Helm Controller** — manage Helm releases (values, dependencies, upgrade, rollback)
- **Notification Controller** — dispatch events, webhook receivers, alert providers
- **Image Automation** — update Git repo when new image is built (ImageRepository, ImagePolicy, ImageUpdateAutomation)
- **Flux vs ArgoCD** — Flux: simpler, stronger security posture (Git-only, no UI); ArgoCD: richer UI, ApplicationSet, Web terminal, wider adoption

### Progressive Delivery

- **Flagger** — progressive delivery for Istio, Linkerd, App Mesh, NGINX, Gloo, Contour; canary, A/B testing, blue-green; metric-based promotion/rollback; alerts via webhook
- **Argo Rollouts** — progressive delivery for K8s (Istio, NGINX, ALB, SMI); blue-green, canary, experiments, analysis; AnalysisTemplate (Prometheus, Datadog, New Relic, Web, Job)

---

## Policy & Governance

### OPA / Gatekeeper

- **OPA (Open Policy Agent)** — policy engine (Rego language); decouple decision-making from enforcement; REST API (data + input → decisions)
- **Gatekeeper** — OPA as admission controller; ConstraintTemplate (Rego template), Constraint (parameterized instantiation); audit (flag violations without blocking), mutation, data replication
- **Key Policies** — enforce labels, resource limits, prohibited registries, allowed capabilities, network policy coverage, require pod security standards

### Kyverno

- Kubernetes-native policy engine (no Rego, uses YAML); admission + mutation + generation + validation + cleanup
- **Policy Types** — validate (pass/fail/audit), mutate (patch images, labels, annotations), generate (create resources), verifyImages (signature check), cleanup (garbage collect stale resources)
- **ClusterPolicy vs Policy** — cluster-scoped vs namespace-scoped; background (audit), failureAction (enforce/audit)
- **Policy Exceptions** — exempt specific resources from policies
- **Kyverno vs Gatekeeper** — Kyverno: easier (YAML), richer features (generate, mutate, verify images); Gatekeeper: more flexible (Rego), established in security-conscious orgs

### Admission Controllers

- **Built-in** — NamespaceLifecycle, LimitRanger, ResourceQuota, PodSecurity, NodeRestriction, DefaultTolerationSeconds, ServiceAccount, MutatingAdmissionWebhook, ValidatingAdmissionWebhook
- **Custom** — write webhooks for custom policies; MutatingWebhookConfiguration (mutating), ValidatingWebhookConfiguration (validating); failurePolicy (Fail, Ignore), timeoutSeconds, reinvocationPolicy
- **Priorities** — mutating runs first (apply defaults), validating runs second (enforce policies)

### Compliance & Auditing

- **kube-bench** — CIS Kubernetes Benchmark checks; run as Job; check control plane, etcd, node, policies
- **kube-hunter** — penetration testing; find vulnerabilities
- **Popeye** — cluster sanitation; scan for misconfigurations, deprecated APIs, resource issues
- **Trivy** — vulnerability scanning for images, IaC (K8s YAML), cluster scanning
- **Checkov** — static analysis of IaC (Helm, Kustomize, Terraform); K8s-specific rules

---

## Operators

### Operator Pattern

- **Operator** — automated operator for managing complex applications; extends K8s API with custom resources (CRDs); encoding domain knowledge (Day 2 operations: backup, restore, scaling, upgrade, failover)
- **Reconciliation Loop** — watch custom resource → desired vs observed state → take action → update status
- **CRD + Controller** — define custom API object (CRD) → controller watches + reconciles CRD instances

### Operator SDK

- **Go** — controller-runtime, controller-tools, kubebuilder; caching, leader election, webhook scaffolding, conversion webhooks
- **Ansible** — write operators as Ansible playbooks; standard for configuration-focused operators
- **Helm** — simpler operators based on Helm charts; less powerful than Go/Ansible

### Common Operators

- **cert-manager** — TLS certificate management; issuers (ACME, SelfSigned, CA, Vault, Venafi); Certificate CRD, automatic renewal, CSI driver for mount
- **Prometheus Operator** — manage Prometheus, Alertmanager, Thanos; ServiceMonitor, PodMonitor, PrometheusRule CRDs
- **Strimzi** — Kafka operator; KafkaTopic, KafkaUser, KafkaConnector CRDs; cluster balancing, auto-tls
- **Elasticsearch Operator (ECK)** — Elasticsearch, Kibana, APM Server, Beats; snapshot/restore, rolling upgrades, node auto-scaling
- **Postgres Operator (CNPG/Zalando)** — PostgreSQL on K8s; replication, backup to S3, upgrade, connection pooling
- **Vault Operator** — manage HashiCorp Vault cluster; scaling, upgrade, replication, unseal
- **KEDA** — event-driven autoscaling; scalers (Kafka, SQS, RabbitMQ, Prometheus, Cron, HTTP); HPA-compatible

---

## Production Operations

### Cluster Lifecycle

- **Provisioning** — kubeadm, kops, kubespray, EKS (eksctl), GKE (gcloud/ Terraform), AKS (az/terraform); cluster API (Crossplane, Cluster API for declarative provisioning)
- **Node Management** — MIG (GKE), ASG (EKS), VMSS (AKS); taints/tolerations for specialized nodes (GPU, spot)
- **Maintenance** — cordon/drain nodes gracefully; PD budgets; node problem detector

### Upgrades

- **Control Plane Upgrades** — minor version upgrades (must be sequential); etcd upgrade, kube-apiserver, controller-manager, scheduler
- **Node Pool Upgrades** — surge/rolling replacement; GKE: surge (maxSurge), maxUnavailable; EKS: version skew (max 2 minor versions)
- **App Deployment** — rolling update (maxSurge, maxUnavailable), blue-green (new version full before cutover), canary (gradual traffic shift)
- **Version Skew Policy** — kube-apiserver can be 2 minor versions ahead of kubelet (for upgrades); kube-apiserver must match etcd version

### Disaster Recovery

- **etcd Backup** — periodic snapshots (cron), store externally (S3); restore by stopping API server, restoring snapshot, restarting; practice DR
- **Velero** — backup app resources + PVs; restore to new cluster (namespace remapping, restore hooks)
- **Backup Strategies** — in-cluster (Velero), etcd + resource YAML (kubectl get all --all-namespaces -o yaml); GitOps-based (re-sync from Git for stateless)

### Multi-Cluster

- **Federation** — KubeFed (deprecated in favor of... ); Cluster API (management cluster + workload clusters)
- **Service Mesh Multi-Cluster** — Istio (mesh expansion, multicluster via spire/VPN), Cilium ClusterMesh (Pod routing across clusters)
- **Submariner** — cross-cluster networking (service discovery, connectivity, Gateway)
- **Resource Management** — config management (Kustomize, Helm), policy (Kyverno, Gatekeeper per cluster), observability (Thanos query across clusters)
- **Use Cases** — HA (critical), data locality, compliance (data residency), cost optimization (spot market)

### Troubleshooting

- **Debugging Pods** — kubectl describe pod (events), kubectl logs (--previous for crashes), kubectl exec (interactive), ephemeral debug containers (kubectl debug)
- **Node Troubleshooting** — kubectl describe node (conditions, capacity), node e2e tests (sonobuoy), node problem detector (kernel logs)
- **Network Debugging** — busybox/nicolaka netshoot Pod for DNS, connectivity; tcpdump, traceroute, nslookup; inspect network policy, service endpoints
- **Performance Issues** — PromQL queries (container CPU/memory/network), kubelet metrics, apiserver metrics; kubectl top pods/nodes
- **CrashLoopBackOff** — check logs, events, resource limits, probe configuration; imagePullSecrets for private repos

---

## Learning Path

1. **Stage 1** — Docker fundamentals (build, run, Compose), container concepts
2. **Stage 2** — Kubernetes core: Pods, Deployments, Services, ConfigMaps, Secrets; kubectl fluency; minikube/kind for local
3. **Stage 3** — Networking (CNI, Ingress, network policies), storage (PV/PVC, StorageClass, StatefulSets), configuration (Helm, Kustomize)
4. **Stage 4** — Security (RBAC, Pod Security, secrets management), CI/CD (GitHub Actions + K8s), GitOps (ArgoCD/Flux)
5. **Stage 5** — Advanced: service mesh (Istio), operators, custom controllers, cluster autoscaling, performance tuning, multi-cluster

---

## Cross-References

| Domain | Connection |
|--------|-----------|
| [02 — Data Engineering](../02-data-engineering/) | Spark/Flink on K8s, data pipelines on K8s, storage for data workloads (Lakehouse, object store via CSI) |
| [03 — Backend](../03-backend/) | Deploying backend services on K8s, service discovery, canary deployments for APIs |
| [05 — Cloud](../05-cloud/) | EKS/GKE/AKS — managed K8s, node pools, cluster networking, cloud LBs |
| [06 — DevOps](../06-devops/) | CI/CD pipelines deploying to K8s, IaC for cluster provisioning, GitOps tooling |
| [08 — Databases](../08-databases/) | Running databases on K8s (operators for Postgres, MySQL, Cassandra), stateful workloads |
| [09 — Distributed Systems](../09-distributed-systems/) | K8s itself is a distributed system (etcd, raft, API server); distributed patterns on K8s |
| [10 — Messaging](../10-messaging/) | Kafka on K8s (Strimzi), message-driven autoscaling (KEDA), event-driven K8s jobs |
| [11 — Networking](../11-networking/) | CNI plugins, network policies, service mesh, DNS in K8s, eBPF networking |
| [14 — SRE/Observability](../14-sre-observability/) | Prometheus + Grafana on K8s, Loki for logs, OpenTelemetry tracing, K8s-specific SLOs |
