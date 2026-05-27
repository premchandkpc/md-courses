# ⚡ Kubernetes Performance Tuning — Complete Deep Dive

## Scope

Production-grade reference for Kubernetes cluster performance covering node sizing, etcd tuning, API server tuning, kubelet tuning, CNI/network tuning, autoscaling, scheduler optimization, and resource management for large-scale clusters.

## Table of Contents

- [Cluster Scaling Limits](#cluster-scaling-limits)
- [Node Sizing & Pod Density](#node-sizing--pod-density)
- [etcd Tuning](#etcd-tuning)
- [API Server Tuning](#api-server-tuning)
- [Kubelet & Node Tuning](#kubelet--node-tuning)
- [Scheduler Tuning](#scheduler-tuning)
- [kube-proxy & Network Tuning](#kube-proxy--network-tuning)
- [CNI Performance](#cni-performance)
- [Autoscaling Tuning](#autoscaling-tuning)
- [Pod Resource Optimization](#pod-resource-optimization)
- [Cost Optimization](#cost-optimization)
- [Failure Analysis](#failure-analysis)

---

## Cluster Scaling Limits

### Kubernetes Hard Limits

```
  Resource                  Default Limit     Tuned Limit
  ──────────────────────────────────────────────────────────
  Nodes per cluster         1000              3000
  Pods per node             110               250 (custom CNI)
  Pods per cluster          110K              750K (large clusters)
  Services per cluster      10000             10000
  Namespaces per cluster    10000             10000
  ConfigMaps per namespace  1000              1000 (kube-apiserver limit)
  Secrets per namespace     1000              1000
  etcd max DB size          8GB               8GB (MVCC overhead)
  etcd max keys             1M                depends on value size
  etcd max request size     1.5MB             1.5MB
```

### Scaling Bottleneck Hierarchy

```
  ┌─────────────────────────────────────────────────────────────┐
  │                  Most Common Bottleneck                       │
  │  1. etcd performance (write throughput ~300-500 ops/s)       │
  │  2. API server watch cache memory overhead                   │
  │  3. kubelet watch starvation (too many pods/node)            │
  │  4. CNI agent resource usage (calico felix, cilium)          │
  │  5. kube-proxy iptables rule explosion > 1000 services       │
  └─────────────────────────────────────────────────────────────┘
```

---

## Node Sizing & Pod Density

### Instance Type Selection

```yaml
# EC2 instance benchmarks for Kubernetes
# General purpose: c5.4xlarge (16vCPU, 32GB) — balanced
# Compute: c5d.12xlarge (48vCPU, 96GB, NVMe) — CPU workloads
# Memory: r5.8xlarge (32vCPU, 256GB) — memory-intensive (DB, cache)
# GPU: p4d.24xlarge (96vCPU, 1152GB, 8x A100) — ML training

# Instance selection criteria:
# - CPU:Memory ratio matching workload (1:2 typical, 1:4 memory-heavy)
# - Network bandwidth: 10Gbps+ for data-plane workloads
# - EBS throughput: gp3 3000 IOPS baseline + burst
# - ENI limits: affects max pods per node

# Max pods per node formula (AWS):
#   max_pods = (number_of_enis * ip_per_eni - 1) + 1
#   c5.4xlarge: 4 ENIs * 30 IPs = 120 pods
#   c5.12xlarge: 8 ENIs * 50 IPs = 400 pods
```

### Pod Density Decision Tree

```
  Target pods/node?
  │
  ├── < 50 pods/node
  │   ├── Default setup works
  │   └── Use AWS CNI VPC
  │
  ├── 50-110 pods/node
  │   ├── Increase kubelet --max-pods=110
  │   ├── Tune kubelet node-status-update-frequency=5s
  │   └── Use Calico + Typha for scale
  │
  └── > 110 pods/node (high density)
      ├── Custom CNI with prefix delegation (AWS prefix mode)
      ├── Cilium with cluster-pool mode
      ├── Disable kube-proxy (Cilium eBPF replaces it)
      └── Decrease kubelet --registry-qps and --event-qps
```

---

## etcd Tuning

### etcd Architecture & Compaction Flow

```
  ┌─────────────────────────────────────────────────────────────┐
  │                     etcd Cluster (3 or 5 nodes)              │
  │                                                             │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
  │  │  Leader  │──│ Follower │──│ Follower │                   │
  │  │          │  │          │  │          │                   │
  │  │ Raft log │  │ apply    │  │ apply    │                   │
  │  │ state    │  │ snapshot │  │ snapshot │                   │
  │  └────┬─────┘  └──────────┘  └──────────┘                   │
  │       │                                                     │
  │       ▼                                                     │
  │  ┌──────────────────┐                                       │
  │  │  Backend DB      │  BoltDB/Bbolt (key-value store)       │
  │  │  ┌──────────────┐│                                       │
  │  │  │ MVCC history ││  All revisions kept until compacted   │
  │  │  │ revision 1..N││  Size = current data + MVCC history  │
  │  │  └──────────────┘│                                       │
  │  └──────────────────┘                                       │
  └─────────────────────────────────────────────────────────────┘

  Compaction Flow:
  1. etcdctl compact N            — remove revisions < N
  2. Wait for compaction to finish
  3. etcdctl defrag               — reclaim disk space

  ┌─────┐    ┌──────────────┐    ┌──────────────┐    ┌─────┐
  │ 8GB ├────► compact rev= │───► wait          ├────► defrag
  │ full│    │ current-1000 │    │ compaction OK │    │ 4GB │
  └─────┘    └──────────────┘    └──────────────┘    └─────┘
```

### etcd Configuration

```bash
# Critical etcd flags
--auto-compaction-retention=8         # auto compact every 8 revisions
--quota-backend-bytes=8589934592      # 8GB max DB size (default)
--max-txn-ops=10000                   # max transactions per txn (default 128)
--max-request-bytes=1572864           # 1.5MB max request size (default)

# Performance flags
--experimental-compact-hash-check-enabled  # detect corruption during compaction
--experimental-watch-progress-notify-interval=10s  # progress for watchers

# Disk
--wal-dir=/var/lib/etcd/wal          # separate disk for WAL strongly recommended
--data-dir=/var/lib/etcd/data         # SSD mandatory
```

### etcd Performance Tuning

```yaml
# Disk requirements:
disk:
  type: NVMe SSD             # minimum: SSD provisioned at 3000 IOPS
  fsync latency: < 10ms      # p99 fsync duration
  IOPS: > 3000               # sustained, not burst
  separate_wal: true         # WAL on separate disk for write isolation

# Network:
network:
  latency: < 2ms             # between etcd nodes
  bandwidth: > 1Gbps
  dedicated_network: true    # avoid sharing with data-plane traffic

# OS tuning:
os:
  net.core.somaxconn: 1024   # connection backlog
  vm.swappiness: 0           # never swap etcd
  fs.file-max: 100000        # file handle limits
```

### Defragmentation Schedule

```bash
# Cron: etcd defrag every 4 hours
0 */4 * * * /usr/local/bin/etcd-defrag.sh

# etcd-defrag.sh
#!/bin/bash
ETCDCTL_API=3
ENDPOINTS="https://etcd-1:2379,https://etcd-2:2379,https://etcd-3:2379"
CERT_FLAGS="--cacert=/etc/kubernetes/pki/etcd/ca.crt \
            --cert=/etc/kubernetes/pki/etcd/server.crt \
            --key=/etc/kubernetes/pki/etcd/server.key"

# Compact revisions older than 1 hour
LATEST_REV=$(etcdctl $CERT_FLAGS --endpoints=$ENDPOINTS endpoint status --write-out=json \
  | jq -r '.[0].Status.revision')
COMPACT_REV=$((LATEST_REV - 1000))
etcdctl $CERT_FLAGS --endpoints=$ENDPOINTS compact $COMPACT_REV
sleep 10

# Defragment each member
for ep in $(echo $ENDPOINTS | tr ',' ' '); do
  etcdctl $CERT_FLAGS --endpoints=$ep defrag
done
```

---

## API Server Tuning

### Key Flags

```bash
# Inflight request limits
--max-mutating-requests-inflight=200      # default 200
--max-requests-inflight=800               # default 400, increase for large clusters

# Watch cache
--watch-cache-sizes=secrets#200,configmaps#200  # per-resource cache size

# Event rate limiting
--event-qps=50                            # default 5, increase for noisy clusters
--event-burst=100

# Request timeout
--request-timeout=60s                     # default 60s

# Encryption
--encryption-provider-config=/etc/kubernetes/encryption-config.yaml
# KMS provider adds 5-10ms latency per write
# Consider: AES-CBC local (no KMS) for performance-critical secrets

# Garbage collection
--concurrent-gc-syncs=20                  # default 20, increase for high churn
```

### Watch Cache Tuning

```yaml
# API server watch cache: 100 entries per resource type default
# Large clusters need more:
#   secrets#200, configmaps#200, pods#5000, endpoints#2000

# Memory cost: ~1-5MB per resource per API server
# Too small → clients reconnect → high etcd watch load
# Too large → API server memory bloat

# Recommend per cluster size:
#    < 100 nodes: defaults
#   < 500 nodes: secrets#500, configmaps#500, pods#10000
#  < 2000 nodes: secrets#1000, configmaps#1000, pods#50000, endpoints#50000
```

---

## Kubelet & Node Tuning

### Kubelet Configuration

```yaml
# kubelet-config.yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
maxPods: 110                      # increase from default 110
kubeAPIQPS: 50                    # default 5, increase for many pods
kubeAPIBurst: 100                 # default 10
eventRecordQPS: 10                # default 5
eventBurst: 20                    # default 10
serializeImagePulls: false        # pull images in parallel
registryPullQPS: 5                # default 5
registryBurst: 10                 # default 10
imageGCHighThresholdPercent: 85   # default 85%
imageGCLowThresholdPercent: 80    # default 80%
nodeStatusUpdateFrequency: 10s    # default 10s (4s for high pods)
nodeStatusReportFrequency: 60s    # defaults to 5m

evictionHard:
  memory.available: "500Mi"
  nodefs.available: "10%"
  nodefs.inodesFree: "5%"
  imagefs.available: "15%"

evictionSoft:
  memory.available: "800Mi"
  nodefs.available: "15%"

evictionSoftGracePeriod:
  memory.available: "1m30s"
  nodefs.available: "1m30s"

podPidsLimit: 4096                # limit PIDs per pod (prevent fork bombs)
```

### Node Lifecycle with Eviction Thresholds

```
  Node Memory Status Flow (kubelet eviction manager):

   Memory Usage
       │
  100% │                              OOM Kill (kernel)
       │                         ┌───
   95% │                         │   evictionHard
       │                         │   memory.available: 500Mi
   85% │                    ┌────┤
       │                    │    │   evictionSoft
   70% │               ┌────┤    │   memory.available: 800Mi
       │               │    │    │
   50% │          ┌────┤    │    │
       │          │    │    │    │
   30% │     ┌────┤    │    │    │
       │     │    │    │    │    │
   10% │─────┤    │    │    │    │
       │     │    │    │    │    │
       └─────┴────┴────┴────┴────┴────────────────────► Time
             │    │    │    │    │
             │    │    │    │    └── Pods evicted (Hard)
             │    │    │    └─────── Pods evicted (Soft)
             │    │    └──────────── Eviction signal triggered
             │    └─────────────── Soft grace period
             └────────────────── Node pressure condition
```

### Image GC Policy

```yaml
# Image garbage collection runs every 5 minutes by default
# Removes images in LRU order when above HighThresholdPercent
# Stops removal when LowThresholdPercent reached

# Tuning for large deployments:
# - Increase thresholds if pulling images often
# - Decrease thresholds if node disk space is premium
# - Use containerd image store for layered caching

# Monitor:
# kubelet_container_garbage_collected_total
# kubelet_image_garbage_collected_total
```

---

## Scheduler Tuning

### Scheduler Flags

```bash
# Scheduling rate
--kube-api-qps=100                    # default 50
--kube-api-burst=200                  # default 100

# Node scoring percentage
# --percentage-of-nodes-to-score: controls sampling
#   < 100 nodes: 50% (default)
#   100-1000 nodes: 50% → 5% exponential
#   > 1000 nodes: 5% minimum
# -- Filter then score; fewer scored nodes = faster scheduling

# Disable scoring plugins if not needed
--plugins=QueueSort,PreFilter,Filter,Score

# Extender configuration for custom scheduling
--extender-config=/etc/kubernetes/scheduler-extender.yaml
```

### Scheduler Performance

```
  Scheduling latency vs cluster size:
   (pod -> binding)

   Latency (ms)
   500 │
   400 │                        ┌─── No tuning
   300 │                   ┌────┤
   200 │              ┌────┤    │
   100 │         ┌────┤    │    └─── With tuning
    50 │    ┌────┤    │    │
     0 └────┴────┴────┴────┴────────────────► Nodes
        100   500  1000  2000  3000

  Tuning effect:
  - percentage-of-nodes-to-score=5% reduces scoring time 90%
  - kube-api-qps=200 prevents scheduling backpressure
  - Disable Score plugins if priority equalization not needed
  - PodTemplate-based caching skips re-filtering for similar pods
```

---

## kube-proxy & Network Tuning

### iptables vs IPVS

```yaml
# kube-proxy mode comparison
iptables:
  scalability: up to ~1000 services
  algorithm: sequential rule matching (O(n) per packet)
  update: full iptables restore on every change (slow, 5-10s for 10K rules)
  memory: proportional to service count + endpoint count
  use case: small clusters, simple networking

IPVS:
  scalability: 10,000+ services
  algorithm: hash table lookup (O(1) per packet)
  update: ipvsadm incremental (fast, milliseconds)
  scheduler: rr, wrr, lc, wlc, lblc, sh, dh
  use case: large clusters, high-throughput
  conntrack: higher connection tracking limits needed

config:
  mode: ipvs
  ipvs:
    scheduler: "lc"              # least connection (default rr)
    minSyncPeriod: 1s            # reduce sync frequency
    syncPeriod: 30s
```

### Network sysctl Tuning

```bash
# /etc/sysctl.d/99-kubernetes.conf

# Connection tracking
net.netfilter.nf_conntrack_max=5000000        # default 65536
net.netfilter.nf_conntrack_tcp_timeout_established=86400  # 24h
net.netfilter.nf_conntrack_buckets=1048576    # hash table size

# TCP buffer tuning
net.core.rmem_max=134217728                    # 128MB
net.core.wmem_max=134217728
net.ipv4.tcp_rmem="4096 87380 134217728"      # min, default, max
net.ipv4.tcp_wmem="4096 65536 134217728"

# Socket backlog
net.core.somaxconn=4096                        # default 128
net.core.netdev_max_backlog=50000

# Fast recycling (use with caution, breaks NAT)
net.ipv4.tcp_tw_reuse=1                        # reuse TIME_WAIT sockets
# net.ipv4.tcp_tw_recycle removed in kernel 4.12

# Inotify — important for large directories (logs, etc)
fs.inotify.max_user_watches=524288
fs.inotify.max_user_instances=8192

# Jumbo frames (9001 MTU for AWS)
net.ipv4.tcp_mtu_probing=1
```

---

## CNI Performance

### Calico Tuning

```yaml
# Calico for large clusters (> 50 nodes)
# Enable Typha: dedicated daemon reduces felix -> datastore load
# Without Typha: every felix agent watches API server directly
# 100 nodes + 1000 policies = 1100 watches on API server
# With Typha: 1 watch per Typha replica, fan-outs to felix

calico:
  networking: "vxlan"           # IPIP or VXLAN (VXLAN better with Azure/GCP)
  typha: enabled
  typha_replicas: 3             # for 100+ node clusters
  felix:
    logseverity: "warning"
    policy_sync_interval: 1s
    iptables_backend: "nft"     # nftables for kernel >= 5.10
  ipip: "never"                 # disable IPIP if using VXLAN

# Kubernetes datastore (instead of etcd)
# Uses CRDs for policy storage
# Better if already running Kubernetes API server
# Use etcd datastore for large clusters (> 500 nodes)
```

### Cilium Tuning

```yaml
cilium:
  mode: "kube-proxy-replacement"  # full, replaces kube-proxy
  bpf:
    map_dynamic_size_ratio: 0.002  # 0.2% of node memory, increase for large nodes
    events_buffer_size: 16         # lower = less CPU
    policy_audit_mode: false       # change to false in production
  ipam:
    mode: "cluster-pool"
    operator:
      replicas: 2
  cluster:
    name: "prod-cluster"
    id: 1
  max_connected_clusters: 255      # ClusterMesh limit
  k8sServiceHost: "api-server.internal"
  k8sServicePort: 6443

# Key metrics:
# cilium_endpoint_count
# cilium_forward_count_total
# cilium_drop_count_total
# cilium_policy_import_errors
```

---

## Autoscaling Tuning

### HPA Tuning

```yaml
# Controller flags
--horizontal-pod-autoscaler-sync-period=15s     # default 15s
--horizontal-pod-autoscaler-upscale-delay=3m    # default 3 min
--horizontal-pod-autoscaler-downscale-delay=5m  # default 5 min
--horizontal-pod-autoscaler-downscale-stabilization=5m  # default 5m
--horizontal-pod-autoscaler-tolerance=0.1       # default 0.1 (10%)

# Example HPA with custom metrics
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 3
  maxReplicas: 50
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300   # 5 min scale-down delay
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0     # immediate scale-up
      policies:
      - type: Pods
        value: 4
        periodSeconds: 15
      - type: Percent
        value: 100
        periodSeconds: 15
      selectPolicy: Max                 # use policy with higher change
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: requests_per_second
      target:
        type: AverageValue
        averageValue: 1000
```

### HPA Scaling Timeline

```
  Request Rate
     │
  100K│    ┌──────────────────────────────┐
     │    │     Traffic Spike               │
  80K │    │                              │
     │    │                              │
  60K │    │                              │
     │    │                              │
  40K │    │                              │
     │    │                              │
  20K │    │                              │
     │    │                              │
     └────┴──────────────────────────────┴────► Time
         10:00  10:05  10:10  10:15  10:20

  Replicas
     │
  40 │                               ┌───
     │                          ┌────┤
  30 │                     ┌────┤    │  Scale-up completed
     │                ┌────┤    │    │  (~3-5 min from metric spike)
  20 │           ┌────┤    │    │    │
     │      ┌────┤    │    │    │    │
  10 │──────┤    │    │    │    │    │
     │      │    │    │    │    │    │
   0 └──────┴────┴────┴────┴────┴────┴────► Time
         10:00  10:05  10:10  10:15  10:20

    Metrics:
    - Metric spike → HPA scales after upscale-delay (3m)
    - If tolerance exceeded (>10% deviation), action taken
    - Cooldown prevents thrashing
    - Fast scale-up, slow scale-down
```

### Cluster Autoscaler + VPA

```yaml
# Cluster Autoscaler configuration
# --scale-down-delay-after-add=10m
# --scale-down-delay-after-delete=10s
# --scale-down-unneeded-time=10m
# --max-node-provision-time=15m
# --expander=least-waste       # pod distribution strategy
# --balance-similar-node-groups

# VPA (Vertical Pod Autoscaler)
# Modes: Auto, Initial, Off
# VPA recommendations:
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: web-app-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  updatePolicy:
    updateMode: "Off"           # Start with Off, review recommendations
  resourcePolicy:
    containerPolicies:
    - containerName: "*"
      minAllowed:
        cpu: 100m
        memory: 128Mi
      maxAllowed:
        cpu: 4
        memory: 8Gi
      controlledResources: ["cpu", "memory"]
```

---

## Pod Resource Optimization

### QoS Classes

```yaml
# Guaranteed QoS — highest priority, never evicted before Burstable/BestEffort
# All containers must have both requests == limits for all resources
apiVersion: v1
kind: Pod
metadata:
  name: guaranteed-pod
spec:
  containers:
  - name: app
    resources:
      requests:
        cpu: "2"
        memory: "4Gi"
      limits:
        cpu: "2"          # == request → Guaranteed
        memory: "4Gi"      # == request → Guaranteed

---
# Burstable QoS — at least one container with request < limit
apiVersion: v1
kind: Pod
metadata:
  name: burstable-pod
spec:
  containers:
  - name: app
    resources:
      requests:
        cpu: "1"
        memory: "2Gi"
      limits:
        cpu: "4"          # > request → Burstable
        memory: "8Gi"     # > request → Burstable

---
# BestEffort QoS — no resources specified
# First to be evicted under memory pressure
apiVersion: v1
kind: Pod
metadata:
  name: best-effort-pod
spec:
  containers:
  - name: app
    # no resources set → BestEffort
```

### PID Limits

```yaml
# Pod PID limits — prevent fork bomb from exhausting node PIDs

# Node-level: --system-reserved=pid=1000
# Pod-level: --pod-max-pids=4096 or spec:

apiVersion: v1
kind: Pod
metadata:
  name: pid-limited
spec:
  hostPID: false
  containers:
  - name: app
    env:
    - name: JVM_MAX_THREADS
      value: "500"
    resources:
      limits:
        cpu: "2"
        memory: "4Gi"
        # PID limits are set via kubelet, not spec
        # Use cgroups v2 pids controller

# Node kubelet:
# --pod-max-pids=4096  (per pod)
# --pods-pids-limit=4096

# Or kubelet config:
podPidsLimit: 4096
```

### Priority Classes & Preemption

```yaml
# Priority classes — critical workloads evict lower priority
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000               # high value = higher priority
globalDefault: false
description: "Critical production workloads"

---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: batch-priority
value: 100
globalDefault: false
preemptionPolicy: PreemptLowerPriority  # default, can be Never

---
apiVersion: v1
kind: Pod
metadata:
  name: critical-app
spec:
  priorityClassName: high-priority
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        cpu: 500m
        memory: 1Gi

# Eviction order under pressure:
# 1. BestEffort pods (no resources)
# 2. Burstable pods with higher resource usage than requested
# 3. Lower priority pods
# 4. Guaranteed pods (last)
# 5. System pods (kube-system) — protected
```

---

## Cost Optimization

### Spot Instances + Cluster Autoscaler

```yaml
# Spot instance configuration
nodeSelector:
  eks.amazonaws.com/capacityType: SPOT

tolerations:
- key: "spotInstance"
  operator: "Exists"
  effect: "NoSchedule"

# Cluster Autoscaler for spot
# --scale-down-unneeded-time=3m     # faster scale-down for spot
# --max-graceful-termination-sec=120
# --expander=random                 # spreads across spot pools

# Karpenter — modern alternative (AWS only)
# Binpacking-first: higher pod density per node
# Consolidation: automatically replaces with cheaper nodes
# Interruption handling: drains before spot interruption
```

### Cost Comparison Table

```
  Purchase Model    Discount   Term        Risk
  ──────────────────────────────────────────────────────────
  On-Demand         None       None        None
  Reserved          30-60%     1-3 year    Underutilization
  Savings Plans     30-60%     1-3 year    More flexible than RI
  Spot              60-90%     Interrupt   Termination 2min notice
  Compute Optimized 0%        Instance     Higher throughput for less

  Storage Costs:
  - gp3 EBS: $0.08/GB-month (3000 IOPS baseline)
  - EFS: $0.30/GB-month (elastic NFS)
  - Instance store: free (ephemeral, lost on stop)
```

### Right-Sizing with VPA

```yaml
# VPA in recommendation mode — analyze first, apply later
# Recommended CPU: 1.2x of P95 usage
# Recommended Memory: 1.2x of P95 usage + 10% headroom

# Sample VPA recommendation output:
# Container "app":
#   minAllowed:
#     cpu: 500m
#     memory: 512Mi
#   maxAllowed:
#     cpu: 4
#     memory: 8Gi
#   target:
#     cpu: 2500m       # <-- actual recommendation
#     memory: 3.8Gi    # <-- actual recommendation
#   uncappedTarget:
#     cpu: 2800m
#     memory: 4.2Gi
#   lowerBound:
#     cpu: 2100m
#     memory: 3.2Gi
#   upperBound:
#     cpu: 3500m
#     memory: 5.1Gi
```

---

## Failure Analysis

### 1. etcd Performance Degradation

```
  Symptoms:
    - API server latency increases (> 1s for list operations)
    - kube-apiserver etcd_request_duration_seconds spike
    - Watch timeouts in controller logs
    - etcd_db_total_size_in_bytes approaching 8GB

  Root Causes:
    1. Too many watches (API server inflight requests)
       Check: etcd_grpc_server_started_total per method
    2. etcd disk fsync latency > 10ms
       Check: etcd_disk_wal_fsync_duration_seconds
    3. etcd state too large (approaching 8GB quota)
       Check: etcd_mvcc_db_total_size_in_bytes
    4. Event storage (events in kube-system) not cleaned up
       Check: kubectl get events --all-namespaces | wc -l

  Resolution:
    - Increase auto-compaction-retention to 8 (lower = more frequent)
    - Run manual defrag: etcdctl compact + defrag
    - Delete old events: kubectl delete events --field-selector lastTimestamp<date
    - Separate WAL onto dedicated NVMe disk
    - Add etcd member nodes for read distribution
```

### 2. Pod Eviction Storm

```
  Symptoms:
    - Many pods in Terminating/Pending across nodes
    - kubelet eviction logs: "evicted pod" + reason
    - Node memory pressure flag set

  Root Causes:
    1. Memory oversubscription: limits > node capacity
       Check: sum(pod resource limits) > node allocatable
    2. DaemonSet memory usage spikes
       Check: Calico, kube-proxy, node-exporter memory
    3. evictionHard thresholds too aggressive
       Check: kubelet_eviction_stats

  Resolution:
    - EvictionHard: memory.available: "500Mi" (not too tight)
    - Reserve system resources: --system-reserved=memory=2Gi
    - Set resource limits on all pods, especially DaemonSets
    - Use Guaranteed QoS for critical workloads
    - Add node-pressure anti-affinity
```

### 3. API Server Watch Overload

```
  Symptoms:
    - etcd_grpc_server_handled_total errors (deadline exceeded)
    - kube-apiserver watch response size > 1.5MB
    - Controllers report "too old resource version"
    - kubelet watch connection re-establishing frequently

  Root Causes:
    1. Too many controllers watching the same resources
       Check: number of watchers on pods/nodes/secrets
    2. Large snapshot transmission on watch reconnect
       (list-watch pattern: list 5000 pods, then watch)
    3. ConfigMap/Secret updates triggering cascading watches
       (every pod watching its mounted secrets)

  Resolution:
    - Increase watch-cache-sizes for heavily watched resources
    - Implement bookmark events (Kubernetes 1.18+)
    - Reduce ConfigMap/Secret updates (batch changes)
    - Use informer with ResyncPeriod > 10 minutes
    - Separate controllers onto their own API server instances
```

### 4. DNS Resolution Failures (CoreDNS)

```
  Symptoms:
    - Application DNS lookup failures (NXDOMAIN)
    - CoreDNS pod CPU throttled
    - coredns_request_duration_seconds > 1s

  Root Causes:
    1. CoreDNS autoscaling insufficient for pod count
       k8s_dns_pods_per_node > 5 → need more CoreDNS replicas
    2. ndots:5 causing excessive DNS lookups
       (every query tries <name>.namespace.svc.cluster.local, etc.)
    3. Conntrack table full on nodes

  Resolution:
    - Autoscale CoreDNS: cluster-proportional-autoscaler
    - Set ndots:3 or ndots:2 in pod dnsConfig
    - Increase CoreDNS cache: cache 10000 30
    - Increase conntrack: net.netfilter.nf_conntrack_max
    - Use NodeLocal DNSCache (stub daemon on each node)
```
