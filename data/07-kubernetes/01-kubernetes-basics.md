# ☸️ Kubernetes — Complete Deep Dive

**Related**: [Advanced K8s Patterns](02-advanced-k8s.md) · [Docker Container Basics](../docker/01-container-basics.md) · [K8s Docs](https://kubernetes.io/docs)

---


```mermaid
graph LR
    API["API Server<br/>(kube-apiserver)"] --> ETCD["etcd<br/>(Cluster State)"]
    API --> SCHED["Scheduler<br/>(kube-scheduler)"]
    SCHED --> NODE["Node<br/>(kubelet)"]
    API --> CM["Controller Manager<br/>(kube-controller-manager)"]
    CM --> DEPLOY["Deployment<br/>Controller"]
    CM --> RS["ReplicaSet<br/>Controller"]
    CM --> ENDP["EndpointSlice<br/>Controller"]
    NODE --> KUBE_PROXY["kube-proxy<br/>(iptables/IPVS)"]
    NODE --> POD["Pod<br/>Container(s)"]
    POD --> KUBELET["kubelet<br/>(CGroup/CRI)"]
    style API fill:#4a8bc2
    style ETCD fill:#2d5a7b
    style SCHED fill:#3a7ca5
    style NODE fill:#c73e1d
    style CM fill:#6f42c1
    style DEPLOY fill:#3fb950
    style RS fill:#e8912e
    style ENDP fill:#3a7ca5
    style KUBE_PROXY fill:#e8912e
    style POD fill:#3fb950
    style KUBELET fill:#2d5a7b
```

## Table of Contents

- [Cluster Architecture](#-cluster-architecture)
- [Pods](#-pods)
- [Deployments](#-deployments)
- [Services](#-services)
- [ConfigMaps & Secrets](#-configmaps--secrets)
- [Ingress](#-ingress)
- [Persistent Volumes & Claims](#-persistent-volumes--persistent-volume-claims)
- [Storage Classes](#-storage-classes)
- [StatefulSets](#-statefulsets)
- [DaemonSets](#-daemonsets)
- [Jobs & CronJobs](#-jobs--cronjobs)
- [HPA & VPA](#-hpa--vpa)
- [Network Policies](#-network-policies)
- [RBAC & Service Accounts](#-rbac--service-accounts)
- [Namespaces & Resource Quotas](#-namespaces--resource-quotas)
- [Limit Ranges](#-limit-ranges)
- [Pod Security Policies](#-pod-security-policies)
- [Liveness, Readiness & Startup Probes](#-liveness-readiness--startup-probes)
- [Affinity & Anti-Affinity](#-affinity--anti-affinity)
- [Taints & Tolerations](#-taints--tolerations)
- [kubectl Commands](#-kubectl-commands)
- [Helm Charts](#-helm-charts)
- [Operators](#-operators)
- [Simplest Mental Model](#-simplest-mental-model)

---

## 🧭 Cluster Architecture

### Control Plane & Worker Nodes

```text
Kubernetes Cluster:

┌─────────────────────────────────────────────────────────────┐
│                   CONTROL PLANE (Master)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │  API     │ │ Scheduler│ │Controller│ │   etcd        │  │
│  │  Server  │ │          │ │ Manager  │ │  (key-value   │  │
│  │ (kube-   │ │ (kube-   │ │ (kube-   │ │   store)      │  │
│  │ apiserver)│ │ scheduler)│ │controller│ │  Raft-based  │  │
│  │  :6443   │ │          │ │ -manager)│ │  consistency │  │
│  └────┬─────┘ └──────────┘ └──────────┘ └──────────────┘  │
│       │                                                     │
│       │           ┌──────────────────┐                      │
│       │           │  Cloud Controller│                      │
│       │           │  Manager (cloud) │                      │
│       │           └──────────────────┘                      │
└───────┼─────────────────────────────────────────────────────┘
        │                 (TLS / HTTP)
        ▼
┌─────────────────────────────────────────────────────────────┐
│                   WORKER NODES                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Node 1                                              │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐     │    │
│  │  │ kubelet  │ │ kube-proxy││ Container Runtime │     │    │
│  │  │ (agent)  │ │(networking)││ (containerd)     │     │    │
│  │  └──────────┘ └──────────┘ └──────────────────┘     │    │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐               │    │
│  │  │ Pod  │ │ Pod  │ │ Pod  │ │ Pod  │               │    │
│  │  └──────┘ └──────┘ └──────┘ └──────┘               │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Node 2                                              │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐     │    │
│  │  │ kubelet  │ │ kube-proxy││ Container Runtime │     │    │
│  │  └──────────┘ └──────────┘ └──────────────────┘     │    │
│  │  ┌──────┐ ┌──────┐ ┌──────┐                         │    │
│  │  │ Pod  │ │ Pod  │ │ Pod  │                         │    │
│  │  └──────┘ └──────┘ └──────┘                         │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

```text
API Server (kube-apiserver)
  ┌───────────────────────────────────────────────┐
  │ • Only component that talks to etcd            │
  │ • Authentication (TLS certs, tokens)           │
  │ • Authorization (RBAC, ABAC)                   │
  │ • Admission control (mutating/validating)      │
  │ • RESTful API — all state changes go through   │
  │ • Scales horizontally (active/active)          │
  └───────────────────────────────────────────────┘

Scheduler (kube-scheduler)
  ┌───────────────────────────────────────────────┐
  │ • Watches for unscheduled Pods (nodeName="")   │
  │ • Filtering: node resources, constraints       │
  │ • Scoring: spreads pods, affinity rules        │
  │ • Binds: writes pod→node assignment to API     │
  │ • Pluggable — custom schedulers possible       │
  └───────────────────────────────────────────────┘

Controller Manager (kube-controller-manager)
  ┌───────────────────────────────────────────────┐
  │ • Runs controller loops in a single binary     │
  │ • Node controller: health checks, evictions    │
  │ • Replication controller: maintains replicas   │
  │ • Endpoint controller: updates Service EP      │
  │ • ServiceAccount & Token controllers           │
  │ • Runs as leader-elected singleton per type    │
  └───────────────────────────────────────────────┘

etcd
  ┌───────────────────────────────────────────────┐
  │ • Distributed key-value store (Raft)           │
  │ • Stores ALL cluster state (desired + actual)  │
  │ • Only API server connects directly           │
  │ • Backup regularly — no etcd = dead cluster    │
  │ • 3 or 5 nodes for production (odd number)     │
  └───────────────────────────────────────────────┘

kubelet
  ┌───────────────────────────────────────────────┐
  │ • The "node agent" — runs on every worker      │
  │ • Registers node with API server               │
  │ • Watches for Pods assigned to this node       │
  │ • Creates/removes containers via CRI           │
  │ • Reports node/pod status, runs probes         │
  │ • Manages volume mounts                        │
  └───────────────────────────────────────────────┘

kube-proxy
  ┌───────────────────────────────────────────────┐
  │ • Network proxy — runs on every node           │
  │ • Maintains iptables/IPVS rules for Services   │
  │ • Routes traffic to Pods (round-robin)         │
  │ • Modes: iptables (default), IPVS, userspace   │
  │ • NOT a service mesh sidecar (that's Istio)    │
  └───────────────────────────────────────────────┘
```

#### Step-by-Step

1. **API Server validates request** — User runs `kubectl apply -f pod.yaml`, CLI sends HTTPS request to API server with pod manifest.
2. **Admission controllers run** — Mutating webhooks (e.g., inject sidecar), then validating webhooks (reject invalid specs).
3. **etcd persists desired state** — API server writes pod manifest to etcd (Raft consensus across 3-5 nodes).
4. **Scheduler finds node** — Scheduler watches unscheduled pods, filters nodes by resource/constraints, scores by affinity/spread, binds pod to node.
5. **kubelet pulls and starts container** — kubelet sees new pod via watch, calls container runtime (containerd), mounts volumes, runs readiness probes.
6. **kube-proxy configures network** — iptables/IPVS rules created so Services route traffic to pod's IP.

#### Code Example

```bash
# Trace a pod creation from kubectl to container start
# 1. Create a deployment
kubectl create deployment nginx --image=nginx --replicas=2

# 2. Watch API server logs (control plane)
kubectl logs -f deployment/kube-apiserver -n kube-system | grep "nginx"

# 3. Check kubelet logs on the node where pod landed
ssh node1
journalctl -u kubelet -f | grep "nginx"

# 4. Verify container runtime (containerd)
crictl ps | grep nginx

# 5. Query etcd directly (API server is the intermediary)
etcdctl get /kubernetes.io/pods/default/nginx-xxxxx
```

#### Real-World Scenario

At Uber, a misconfigured admission webhook caused all pod creation to hang for 3 minutes. The webhook was doing a synchronous DNS lookup to an external validation service that had high latency. Once identified via `kubectl describe pod` showing pending event "admission webhook timeout", they added a 5-second timeout to the webhook configuration, preventing future cascade failures.

#### Diagram

```mermaid
sequenceDiagram
    User->>API: kubectl apply pod.yaml
    API->>Admission: Validate + Mutate
    API->>etcd: Store desired state
    Scheduler->>API: Watch unscheduled pods
    Scheduler->>API: Bind pod to node1
    kubelet->>API: Watch for new pods
    kubelet->>containerd: Pull image, start container
    kube-proxy->>iptables: Create NAT rules for Service
    kubelet->>pod: Run readiness probe
```

---

## 🧭 Pods

### Pod Definition

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
  namespace: default
  labels:
    app: nginx
    tier: frontend
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "80"
spec:
  containers:
    - name: nginx
      image: nginx:1.25
      ports:
        - containerPort: 80
          protocol: TCP
          name: http
      env:
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: DB_HOST
          value: "postgres-service"
      resources:
        requests:
          memory: "64Mi"
          cpu: "250m"
        limits:
          memory: "128Mi"
          cpu: "500m"
      livenessProbe:
        httpGet:
          path: /healthz
          port: 80
        initialDelaySeconds: 3
        periodSeconds: 3
      readinessProbe:
        httpGet:
          path: /ready
          port: 80
        initialDelaySeconds: 5
        periodSeconds: 5
      volumeMounts:
        - name: nginx-config
          mountPath: /etc/nginx/conf.d
  volumes:
    - name: nginx-config
      configMap:
        name: nginx-config
  restartPolicy: Always
  nodeSelector:
    disktype: ssd
  tolerations:
    - key: "app"
      operator: "Equal"
      value: "blue"
      effect: "NoSchedule"
```

### Pod Lifecycle

```text
Pod Phase State Machine:

  ┌──────────┐
  │ PENDING   │─── API server accepted, but containers not running
  └────┬─────┘
       │
       ▼
  ┌──────────┐     ┌──────────────────┐
  │ RUNNING   │────>│ At least one      │
  │           │     │ container running │
  └────┬─────┘     └──────────────────┘
       │
       ├───────────────────────────┐
       ▼                           ▼
  ┌──────────┐              ┌──────────┐
  │ SUCCEEDED│              │  FAILED   │
  │ (0 exit) │              │(non-zero) │
  └──────────┘              └──────────┘

Container States within Pod:
  ┌────────────────┐
  │ Waiting         │── Back-off, ImagePull, CrashLoopBackOff
  ├────────────────┤
  │ Running         │── Healthy, executing
  ├────────────────┤
  │ Terminated      │── Completed or Error
  └────────────────┘
```

#### Step-by-Step

1. **API server creates pod object** — Pod manifest written to etcd in PENDING phase (no node assigned yet).
2. **Scheduler assigns to node** — Scheduler finds available node, updates pod with `spec.nodeName`.
3. **kubelet sees new pod** — kubelet watches API server, detects its node assignment, begins pulling image.
4. **Container runtime starts container** — containerd pulls image layers, creates container, runs entrypoint command.
5. **Startup probe runs** — Container initializing; kubelet runs startup probe every periodSeconds until success.
6. **Pod transitions to RUNNING** — At least one container is running; liveness and readiness probes begin.
7. **Pod terminates** — On deletion, gracefulTerminationPeriod (default 30s) given; SIGTERM sent; liveness probe disabled.

#### Code Example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-lifecycle-demo
  namespace: default
spec:
  containers:
    - name: myapp
      image: nginx:1.25
      lifecycle:
        # Hook before pod starts serving
        postStart:
          exec:
            command: ["/bin/sh", "-c", "echo 'Pod starting' > /tmp/started.log"]
        # Hook before pod terminates
        preStop:
          exec:
            command: ["/bin/sh", "-c", "sleep 15 && echo 'Pod stopping'"]
      startupProbe:
        httpGet:
          path: /health
          port: 80
        failureThreshold: 30
        periodSeconds: 10
      readinessProbe:
        httpGet:
          path: /ready
          port: 80
        initialDelaySeconds: 5
        periodSeconds: 5
      livenessProbe:
        httpGet:
          path: /healthz
          port: 80
        initialDelaySeconds: 15
        periodSeconds: 20
  terminationGracePeriodSeconds: 30
  restartPolicy: Always  # Always, OnFailure, Never
```

#### Real-World Scenario

A Netflix team noticed pods were being killed by Kubernetes during deployments even though they were healthy. Investigation revealed that `terminationGracePeriodSeconds` was 30 seconds, but their application's graceful shutdown took 45 seconds to flush in-flight requests. They increased it to 60 seconds and added a preStop hook that blocked until all connections drained, preventing request loss during rolling updates.

#### Diagram

```mermaid
stateDiagram-v2
    [*] --> Pending
    Pending --> ContainerCreating: kubelet pulls image
    ContainerCreating --> Running: container starts
    Running --> Succeeded: exit code 0
    Running --> Failed: exit code non-0
    Running --> CrashLoopBackOff: rapid failures
    Succeeded --> [*]
    Failed --> [*]
    CrashLoopBackOff --> Running: after backoff delay
```

### Multi-Container Pods

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-with-sidecar
spec:
  containers:
    - name: web
      image: nginx
      ports:
        - containerPort: 80
      volumeMounts:
        - name: shared-logs
          mountPath: /var/log/nginx
    - name: log-collector
      image: fluent/fluentd
      volumeMounts:
        - name: shared-logs
          mountPath: /var/log/nginx
      env:
        - name: FLUENTD_ARGS
          value: "-c /fluentd/etc/fluent.conf"
  volumes:
    - name: shared-logs
      emptyDir: {}
```

### Init Containers

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-init
spec:
  initContainers:
    - name: init-migrations
      image: myapp/migrations
      command: ["node", "run-migrations.js"]
      env:
        - name: DB_URL
          value: "postgres://..."
    - name: init-permissions
      image: busybox
      command: ["sh", "-c", "chown -R 1000:1000 /data"]
      volumeMounts:
        - name: data
          mountPath: /data
  containers:
    - name: app
      image: myapp/app
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      emptyDir: {}
```

---

## 🧭 Deployments

### Deployment Definition

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-deployment
  namespace: production
  labels:
    app: web
    environment: prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1          # Max pods unavailable during update
      maxSurge: 1                 # Extra pods above desired count
  minReadySeconds: 30             # Wait before considering pod ready
  revisionHistoryLimit: 5         # Keep last 5 revisions for rollback
  paused: false                   # Don't process new rollout
  progressDeadlineSeconds: 600    # Max time for rollout progress
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: nginx
          image: nginx:1.25
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: 200m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
          livenessProbe:
            httpGet:
              path: /healthz
              port: 80
      terminationGracePeriodSeconds: 30
```

#### Step-by-Step

1. **Deployment controller creates ReplicaSet** — Deployment spec creates ReplicaSet with pod template.
2. **ReplicaSet controller creates Pods** — ReplicaSet ensures desired number of pods (3) are running.
3. **Scheduler assigns to nodes** — Scheduler distributes pods across nodes respecting affinity rules.
4. **kubelet starts containers** — kubelet pulls images, runs readiness probes, adds pods to Service load balancer.
5. **Rolling update triggered** — New image version set, ReplicaSet slowly scales down old pods (maxUnavailable=1) and up new pods (maxSurge=1).
6. **Old ReplicaSet retained** — Previous ReplicaSet kept (revisionHistoryLimit=5) for quick rollback if issues detected.

#### Code Example

```bash
# Create deployment
kubectl create deployment web --image=nginx:1.25 --replicas=3

# Check rollout status
kubectl rollout status deployment/web
# Output: Waiting for deployment "web" to complete: 1 out of 3 new replicas have been updated

# Update image (triggers rolling update)
kubectl set image deployment/web nginx=nginx:1.26 --record

# Watch rolling update in real-time
kubectl rollout history deployment/web
# revision 1: image: nginx:1.25
# revision 2: image: nginx:1.26

# Pause/resume rollout (for canary testing)
kubectl rollout pause deployment/web
kubectl rollout resume deployment/web

# Rollback to previous revision
kubectl rollout undo deployment/web --to-revision=1
```

#### Real-World Scenario

A fintech company performed a rolling update of their payment API but a new image had a memory leak. Within 5 minutes, pods were OOMKilled faster than new ones could start (maxSurge=1 meant only 1 pod restarted at a time). They had set `progressDeadlineSeconds: 600` (10 min), so Kubernetes aborted the rollout at 10 minutes. They used `kubectl rollout undo` to restore the previous version in seconds, preventing payment processing outages.

#### Diagram

```mermaid
graph TB
    subgraph Initial["Initial (v1): 3 pods"]
        P1["Pod-v1"]
        P2["Pod-v1"]
        P3["Pod-v1"]
    end
    subgraph Update["Rolling Update (maxSurge=1, maxUnavailable=1)"]
        US1["Step 1: Scale RS-v2 to 1, RS-v1 at 3"]
        US2["Step 2: Scale RS-v1 to 2, RS-v2 at 2"]
        US3["Step 3: Scale RS-v1 to 1, RS-v2 at 3"]
        US4["Step 4: Scale RS-v1 to 0, RS-v2 at 3"]
    end
    Initial --> US1 --> US2 --> US3 --> US4
```

### Rolling Update

```text
Rolling Update Strategy:

  Current state: 3 pods running v1

  Step 1: kubectl set image deployment/web nginx=nginx:1.26

  v1  v1  v1                          Desired: 3
  │
  ▼
  v1  v1  v1  v2                      maxSurge=1 → creates 1 extra
  │
  ▼
  v1  v2  v2                          maxUnavailable=1 → deletes 1 v1
  │
  ▼
  v2  v2  v2                          All v2, complete

  Rollback: kubectl rollout undo deployment/web
  Revisions: kubectl rollout history deployment/web
```

### Deployment Strategies

```yaml
# RollingUpdate (default) — zero-downtime updates
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 25%          # 25% of desired can be unavailable
    maxSurge: 25%                # 25% extra can be created

# Recreate — kill all, then start new (has downtime)
strategy:
  type: Recreate
  # Use when: you can't run old and new simultaneously
  # (e.g., file system locks, schema migrations)

# Blue/Green via labels — manual switch
# Two deployments, same selector, switch Service labels:
#   kubectl label service web app=web-green
#   kubectl label service web app=web-blue

# Canary — percentage-based rollout
# Two deployments, adjust Service selector or split via Istio
# 10% new → 50% → 100%
```

### Deployment Commands

```bash
# Create and manage
kubectl create deployment nginx --image=nginx
kubectl apply -f deployment.yaml
kubectl get deployments
kubectl describe deployment web

# Rollout management
kubectl rollout status deployment/web
kubectl rollout history deployment/web
kubectl rollout undo deployment/web
kubectl rollout undo deployment/web --to-revision=2
kubectl rollout pause deployment/web
kubectl rollout resume deployment/web

# Scaling
kubectl scale deployment/web --replicas=5
kubectl autoscale deployment/web --cpu-percent=80 --min=3 --max=10

# Image update (triggers rollout)
kubectl set image deployment/web nginx=nginx:1.26
kubectl edit deployment/web
kubectl patch deployment/web -p '{"spec":{"template":{"spec":{"containers":[{"name":"nginx","image":"nginx:1.26"}]}}}}'
```

---

## 🧭 Services

### Service Types

```yaml
# ClusterIP (default) — internal cluster IP, accessible only within cluster
apiVersion: v1
kind: Service
metadata:
  name: web-clusterip
spec:
  type: ClusterIP
  selector:
    app: web
  ports:
    - name: http
      port: 80              # Service port
      targetPort: 8080       # Container port
      protocol: TCP
  clusterIP: 10.96.0.50     # Optional: specify IP (must be in service CIDR)

---
# NodePort — exposes on each node's IP at a static port
apiVersion: v1
kind: Service
metadata:
  name: web-nodeport
spec:
  type: NodePort
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080        # Optional: 30000-32767, K8s assigns if omitted

---
# LoadBalancer — provisions external LB (cloud provider)
apiVersion: v1
kind: Service
metadata:
  name: web-lb
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing"
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 8080
  loadBalancerIP: 192.0.2.50              # If supported by cloud provider
  externalTrafficPolicy: Local             # Preserve client IP

---
# ExternalName — DNS alias for external services
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  type: ExternalName
  externalName: mydb.example.com
  # No selectors, no ports — just a CNAME alias
  # Access: external-db.namespace.svc.cluster.local → mydb.example.com
```

### Service Networking

```text
Service Traffic Flow:

                                      ClusterIP: 10.96.0.1
  ┌────────┐                         ┌─────────────────────┐
  │ Client │──────> web:80 ─────────>│  iptables rules      │
  └────────┘                         │  (kube-proxy)        │
                                          │
                                          │ (random pod)
                                          ▼
                              ┌─────────────────────┐
                              │  Pod 1 (10.0.1.2:80)  │
                              │  Pod 2 (10.0.1.3:80)  │
                              │  Pod 3 (10.0.2.2:80)  │
                              └─────────────────────┘

Service resolution (CoreDNS):
  <service>.<namespace>.svc.cluster.local
  web.default.svc.cluster.local → 10.96.0.1
```

#### Step-by-Step

1. **Service object created** — User defines Service selector (e.g., `app: web`), port mapping (80→8080).
2. **EndpointSlice controller watches pods** — Finds all pods matching selector, tracks their IPs and readiness status.
3. **kube-proxy subscribes to changes** — Watches Service and EndpointSlice, writes iptables/IPVS rules locally on each node.
4. **Client resolves DNS** — Pod A wants to reach `web.default.svc.cluster.local`, CoreDNS returns Service ClusterIP (10.96.0.1).
5. **iptables performs DNAT** — Client connection to 10.96.0.1:80 is intercepted, NATted to random endpoint (10.0.1.2:8080).
6. **kube-proxy load balances** — Round-robin or hash-based selection if using IPVS mode; scales gracefully with EndpointSlice updates.

#### Code Example

```yaml
# Define Service to load-balance across pods
apiVersion: v1
kind: Service
metadata:
  name: web-service
  namespace: production
spec:
  type: ClusterIP
  selector:
    app: web
    tier: frontend
  ports:
    - name: http
      port: 80
      targetPort: 8080      # Pod container port
      protocol: TCP
  sessionAffinity: ClientIP # Optional: stick client to same pod
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
  publishNotReadyAddresses: false  # Only include Ready pods

---
# Create corresponding deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
      tier: frontend
  template:
    metadata:
      labels:
        app: web
        tier: frontend
    spec:
      containers:
        - name: nginx
          image: nginx:1.25
          ports:
            - containerPort: 8080
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            periodSeconds: 5
```

#### Real-World Scenario

A Spotify team experienced intermittent request timeouts where some traffic would hit pods that were still shutting down gracefully. The issue: pods were marked NotReady but kube-proxy took ~10 seconds to update iptables rules. They set `preStop` hook to sleep 15 seconds before containers shut down, ensuring iptables rules converged before endpoints actually disconnected.

#### Diagram

```mermaid
sequenceDiagram
    participant Client
    participant CoreDNS
    participant kube-proxy
    participant iptables
    participant Pod1
    Client->>CoreDNS: Resolve web.default.svc.cluster.local
    CoreDNS-->>Client: 10.96.0.1
    Client->>iptables: Connect to 10.96.0.1:80
    kube-proxy->>iptables: DNAT rule: 10.96.0.1:80 -> Pod IP:8080
    iptables-->>Pod1: Route to 10.0.1.2:8080
    Pod1-->>Client: HTTP response
```

### Headless Services

```yaml
# Headless Service — no ClusterIP, returns pod IPs directly
apiVersion: v1
kind: Service
metadata:
  name: statefulset-headless
spec:
  clusterIP: None              # This makes it headless
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 80

# DNS returns A/AAAA records for each pod IP:
#   statefulset-headless.default.svc.cluster.local
#   → 10.0.1.2  (Pod 1)
#   → 10.0.1.3  (Pod 2)

# Individual pod DNS:
#   pod-name.service-name.namespace.svc.cluster.local
#   my-app-0.statefulset-headless.default.svc.cluster.local
#   my-app-1.statefulset-headless.default.svc.cluster.local
```

### EndpointSlices

```yaml
# Services create EndpointSlices (replaces Endpoints API)
# Automatically managed — lists all pods matching selector
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: web-abc123
  labels:
    kubernetes.io/service-name: web
addressType: IPv4
ports:
  - name: http
    port: 80
    protocol: TCP
endpoints:
  - addresses:
      - "10.0.1.2"
    conditions:
      ready: true
    node: node1
    zone: us-east-1a
  - addresses:
      - "10.0.1.3"
    conditions:
      ready: true
```

---

## 🧭 ConfigMaps & Secrets

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  # Key-value pairs
  APP_ENV: production
  LOG_LEVEL: warn
  CACHE_TTL: "300"

  # Multi-line values
  app.properties: |
    app.name=MyApp
    app.version=1.0.0
    app.maintainer=dev@example.com

  # File content
  nginx.conf: |
    server {
      listen 80;
      location / {
        proxy_pass http://backend:8080;
      }
    }
```

```yaml
# Using ConfigMap in a Pod
apiVersion: v1
kind: Pod
metadata:
  name: configmap-demo
spec:
  containers:
    - name: app
      image: myapp
      env:
        - name: APP_ENV
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: APP_ENV
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: LOG_LEVEL
              optional: true                     # Don't fail if missing
      envFrom:
        - configMapRef:
            name: app-config
            prefix: CFG_                         # All keys prefixed
      volumeMounts:
        - name: config-volume
          mountPath: /etc/config
  volumes:
    - name: config-volume
      configMap:
        name: app-config
        items:
          - key: app.properties
            path: app.properties
```

### Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque                           # Default — arbitrary key/value
data:
  username: YWRtaW4=                   # Base64 encoded
  password: cGFzc3dvcmQxMjM=           # echo -n "mypass" | base64

stringData:                            # Plaintext (K8s converts to base64)
  api_key: "sk-abc123def456"
  db_url: "postgresql://user:pass@host:5432/db"

---
# Special secret types
apiVersion: v1
kind: Secret
metadata:
  name: tls-cert
type: kubernetes.io/tls                # For TLS certificates
data:
  tls.crt: <base64-encoded-cert>
  tls.key: <base64-encoded-key>

---
apiVersion: v1
kind: Secret
metadata:
  name: docker-registry-secret
type: kubernetes.io/dockerconfigjson    # For pulling from private registries
data:
  .dockerconfigjson: <base64-docker-config-json>
```

```yaml
# Using Secrets in a Pod
apiVersion: v1
kind: Pod
metadata:
  name: secret-demo
spec:
  containers:
    - name: app
      image: myapp
      env:
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
              optional: false
      envFrom:
        - secretRef:
            name: db-credentials
      volumeMounts:
        - name: secret-volume
          mountPath: /etc/secrets
          readOnly: true
  volumes:
    - name: secret-volume
      secret:
        secretName: db-credentials
        defaultMode: 0400                 # File permissions
        items:
          - key: username
            path: db/username             # Nested path
  imagePullSecrets:                       # For private image registry
    - name: docker-registry-secret
```

---

## 🧭 Ingress

### Ingress Controller

```text
Ingress exposes HTTP/HTTPS routes from outside the cluster to Services.

    Internet
        │
        ▼
  ┌──────────────┐
  │  Ingress     │  ← Ingress Controller (e.g., nginx, Traefik, HAProxy)
  │  Controller  │     - Watches Ingress resources
  └──────┬───────┘     - Configures reverse proxy
         │
    ┌────┴────┐
    │         │
    ▼         ▼
  Service   Service
  (web)     (api)
```

### Ingress Resource

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  namespace: production
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - myapp.example.com
        - api.example.com
      secretName: myapp-tls-secret
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web-service
                port:
                  number: 80
          - path: /static
            pathType: Prefix
            backend:
              service:
                name: static-service
                port:
                  number: 80
    - host: api.example.com
      http:
        paths:
          - path: /v1
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 8080
          - path: /v1/admin
            pathType: Prefix
            backend:
              service:
                name: admin-service
                port:
                  number: 8080
```

### Path Types

```text
Path Type Behavior:

  Prefix:
    /api matches: /api, /api/v1, /api/v1/users
    Does NOT match: /api2

  Exact:
    /api matches ONLY: /api
    Does NOT match: /api/, /api/v1

  ImplementationSpecific:
    Depends on Ingress Controller implementation
    nginx: behaves like Prefix by default
```

---

## 🧭 Persistent Volumes & Persistent Volume Claims

### PV & PVC

```yaml
# PersistentVolume — cluster resource (like a Node)
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-nfs-1
  labels:
    type: nfs
spec:
  capacity:
    storage: 100Gi
  accessModes:
    - ReadWriteOnce              # RWO: single node read-write
    - ReadOnlyMany               # ROX: many nodes read-only
  persistentVolumeReclaimPolicy: Retain    # Retain, Recycle, Delete
  storageClassName: standard
  mountOptions:
    - hard
    - nfsvers=4.1
  nfs:
    server: nfs-server.internal
    path: /exports/data

---
# PersistentVolumeClaim — request for storage (like a Pod)
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-storage
  namespace: production
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: standard               # Match PV's class
  selector:                                # Optional label selector
    matchLabels:
      type: nfs
  volumeMode: Filesystem                   # Filesystem (default) or Block
```

#### Step-by-Step

1. **Admin creates PersistentVolume** — Provisions actual storage (NFS share, AWS EBS, GCP PD) and creates PV object in Kubernetes.
2. **User creates PersistentVolumeClaim** — Pod requests storage via PVC (like a purchase order), specifies size and access mode.
3. **Kubernetes binds PVC to PV** — Finds PV matching PVC's storageClassName, accessModes, size; creates binding.
4. **Pod mounts volume** — kubelet mounts the bound PV to pod at specified mountPath (using storage driver/NFS client).
5. **Application reads/writes** — Container sees mounted directory, can persist data across pod restarts.
6. **Reclaim policy applied** — On PVC deletion, reclaim policy (Retain/Delete/Recycle) determines what happens to actual storage.

#### Code Example

```yaml
# StorageClass for dynamic provisioning (CSI driver)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer

---
# PVC requests storage dynamically (no manual PV needed)
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
  namespace: production
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 50Gi

---
# Pod uses PVC
apiVersion: v1
kind: Pod
metadata:
  name: app-with-storage
spec:
  containers:
    - name: app
      image: myapp
      volumeMounts:
        - name: data
          mountPath: /data
      command: ["/bin/sh", "-c"]
      args:
        - |
          echo "Writing to persistent storage"
          echo "timestamp: $(date)" >> /data/log.txt
          sleep 3600
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: data-pvc
```

#### Real-World Scenario

A DynamoDB team's backup job created thousands of PVCs daily, exhausting their storage quota. The issue: no reclaim policy cleanup occurred for failed job PVCs. They added a TTL controller (via Kubernetes Job cleanup or a custom operator) to delete PVCs older than 7 days, and set `reclaimPolicy: Delete` to auto-release backing storage.

#### Diagram

```mermaid
graph LR
    Admin["Admin<br/>Provisions Storage<br/>(AWS EBS/NFS)"] -->|Create PV| PV["PersistentVolume<br/>100Gi<br/>RWO"]
    User["User<br/>Requests Storage"] -->|Create PVC| PVC["PersistentVolumeClaim<br/>50Gi<br/>RWO"]
    PVC -->|Bind| PV
    Pod["Pod<br/>volumeMounts:<br/>  /data"] -->|Mount| PV
    PV -->|Actual Block Storage| Storage["AWS EBS Volume<br/>or NFS Share"]
```

### PV Lifecycle

```text
PV Lifecycle:

  Available ──> Bound ──> Released ──> Available
                    │                        │
                    │                        ├── Reclaim: Delete
                    │                        └── Reclaim: Retain (manual)
                    │
                    └── Claim deleted ──> Released

  Access Modes:
    RWO — ReadWriteOnce       (single node)
    ROX — ReadOnlyMany        (many nodes)
    RWX — ReadWriteMany       (many nodes, e.g., NFS)
    RWOP— ReadWriteOncePod    (single pod, v1.22+)
```

### PVC in a Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: storage-demo
spec:
  containers:
    - name: app
      image: nginx
      volumeMounts:
        - name: data
          mountPath: /usr/share/nginx/html
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: app-storage
        readOnly: false
```

### CSI (Container Storage Interface)

```yaml
# CSI drivers allow pluggable storage backends
# Examples: AWS EBS, GCE PD, Azure Disk, NFS, Ceph, Portworx

# StorageClass for AWS EBS
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-gp3
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer  # Create volume on pod scheduling node
allowVolumeExpansion: true
```

---

## 🧭 Storage Classes

### StorageClass Definition

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/gce-pd         # or ebs.csi.aws.com, ...
parameters:
  type: pd-ssd                            # Cloud-specific
  replication-type: regional-pd
  zones: us-central1-a,us-central1-b
reclaimPolicy: Delete                     # Delete PV when PVC deleted
allowVolumeExpansion: true                # Allow expanding PVC
volumeBindingMode: WaitForFirstConsumer   # Wait for pod scheduling
mountOptions:
  - discard
```

### Default StorageClass

```yaml
# Mark as default (no storageClassName in PVC = uses this)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: standard
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
reclaimPolicy: Delete
volumeBindingMode: Immediate
```

---

## 🧭 StatefulSets

### StatefulSet Definition

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres-headless          # Headless Service for stable network IDs
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16
          ports:
            - containerPort: 5432
              name: postgres
          env:
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: pg-secret
                  key: password
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:                   # Each pod gets its own PVC
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 100Gi
        storageClassName: fast-ssd
  podManagementPolicy: OrderedReady        # OrderedReady or Parallel
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0                         # Only update pods with ordinal >= partition
```

### StatefulSet Characteristics

```text
StatefulSet Pod Naming:
  postgres-0, postgres-1, postgres-2
  ─ Stable, predictable, ordinal-based

  Each pod has:
  • Stable hostname (postgres-0.postgres-headless.default.svc.cluster.local)
  • Stable persistent storage (PVC bound permanently)
  • Ordinal index (0, 1, 2) — for data partitioning

  Boot order:
    postgres-0 ──> Running
    postgres-1 ──> waits for postgres-0 ready
    postgres-2 ──> waits for postgres-1 ready

  Shutdown (reverse order):
    postgres-2 ──> Terminated
    postgres-1 ──> Terminated
    postgres-0 ──> Terminated

  Use for: Databases (PostgreSQL, Cassandra), Kafka, Zookeeper, Elasticsearch
```

### Headless Service for StatefulSet

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-headless
spec:
  clusterIP: None
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: postgres
      name: postgres
```

---

## 🧭 DaemonSets

### DaemonSet Definition

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd-logging
  namespace: kube-system
spec:
  selector:
    matchLabels:
      name: fluentd
  template:
    metadata:
      labels:
        name: fluentd
    spec:
      tolerations:                         # Run on all nodes including control plane
        - key: node-role.kubernetes.io/control-plane
          effect: NoSchedule
      containers:
        - name: fluentd
          image: fluent/fluentd:v1.16
          resources:
            limits:
              memory: 200Mi
              cpu: 200m
            requests:
              memory: 100Mi
              cpu: 100m
          volumeMounts:
            - name: varlog
              mountPath: /var/log
            - name: containers
              mountPath: /var/lib/docker/containers
              readOnly: true
      terminationGracePeriodSeconds: 30
      volumes:
        - name: varlog
          hostPath:
            path: /var/log
        - name: containers
          hostPath:
            path: /var/lib/docker/containers
```

### DaemonSet Use Cases

```text
DaemonSet = Exactly one pod per node (and each selected node)

  Use cases:
  • Log collection: fluentd, logstash, filebeat
  • Monitoring: Prometheus Node Exporter, Datadog agent, New Relic
  • Networking: kube-proxy, Calico, Weave Net, Cilium
  • Storage: CSI node drivers, GlusterFS, Ceph
  • Security: AppArmor profile loader, Falco, Sysdig

  Schedule on specific nodes:
    spec.template.spec.nodeSelector:
      disktype: ssd

  Run on ALL nodes (including master):
    spec.template.spec.tolerations:
      - operator: Exists              # Tolerate all taints
```

---

## 🧭 Jobs & CronJobs

### Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: data-migration
spec:
  completions: 1                       # Run to completion once
  parallelism: 1                       # How many pods run in parallel
  backoffLimit: 3                      # Retry up to 3 times
  activeDeadlineSeconds: 3600          # Max job duration (1 hour)
  ttlSecondsAfterFinished: 86400       # Auto-cleanup after 24h
  template:
    spec:
      containers:
        - name: migration
          image: myapp/migrations:latest
          command: ["node", "migrate.js"]
          env:
            - name: DB_URL
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: url
      restartPolicy: Never             # OnFailure or Never
```

### Parallel Jobs

```yaml
# Work queue pattern — each pod processes one item
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel-workers
spec:
  completions: 10                      # 10 total completions
  parallelism: 3                       # 3 pods running at once
  completionMode: Indexed             # Pod knows its index (v1.22+)
  template:
    spec:
      containers:
        - name: worker
          image: myapp/worker
          env:
            - name: JOB_INDEX
              valueFrom:
                fieldRef:
                  fieldPath: metadata.annotations['batch.kubernetes.io/job-completion-index']
      restartPolicy: Never
```

### CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-cleanup
spec:
  schedule: "0 3 * * *"               # Every day at 3 AM (cron format)
  timeZone: "America/New_York"         # Timezone (v1.25+ stable)
  startingDeadlineSeconds: 100         # Max delay if missed
  concurrencyPolicy: Forbid            # Forbid, Allow, Replace
  successfulJobsHistoryLimit: 3        # Keep last 3 successful
  failedJobsHistoryLimit: 1            # Keep last 1 failed
  suspend: false                       # Pause executions
  jobTemplate:
    spec:
      backoffLimit: 2
      ttlSecondsAfterFinished: 3600
      template:
        spec:
          containers:
            - name: cleanup
              image: myapp/cleanup
              command: ["/cleanup.sh"]
          restartPolicy: OnFailure
```

### Cron Schedule Reference

```text
  ┌───────────── minute (0-59)
  │ ┌───────────── hour (0-23)
  │ │ ┌───────────── day of month (1-31)
  │ │ │ ┌───────────── month (1-12)
  │ │ │ │ ┌───────────── day of week (0-6) (Sunday=0)
  │ │ │ │ │
  * * * * *

  "0 0 * * *"     = Every day at midnight
  "*/5 * * * *"   = Every 5 minutes
  "0 9-17 * * 1-5" = Every hour 9-5 on weekdays
  "0 0 1 */3 *"   = First of every quarter
  "0 2 * * 0"     = Every Sunday at 2 AM
```

---

## 🧭 HPA & VPA

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70         # Scale when CPU > 70%
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80         # Scale when memory > 80%
    - type: Pods
      pods:
        metric:
          name: requests-per-second
        target:
          type: AverageValue
          averageValue: "1000"           # Scale when RPS > 1000
    - type: Object
      object:
        metric:
          name: ingress_requests_per_second
        describedObject:
          apiVersion: networking.k8s.io/v1
          kind: Ingress
          name: web-ingress
        target:
          type: Value
          value: "2000"
  behavior:                             # Fine-tune scaling (v2)
    scaleDown:
      stabilizationWindowSeconds: 300    # Wait 5 min before scaling down
      policies:
        - type: Percent
          value: 10                      # Max 10% pods removed per minute
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0      # Scale up immediately
      policies:
        - type: Pods
          value: 4                       # Add max 4 pods per 60s
          periodSeconds: 60
        - type: Percent
          value: 100                     # Or double per minute
          periodSeconds: 60
      selectPolicy: Max                  # Use the policy that allows more
```

### Vertical Pod Autoscaler

```yaml
# VPA automatically adjusts CPU/memory requests (alpha/beta)
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: web-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web
  updatePolicy:
    updateMode: Auto                    # Auto, Initial, Off
  resourcePolicy:
    containerPolicies:
      - containerName: nginx
        minAllowed:
          cpu: "100m"
          memory: "128Mi"
        maxAllowed:
          cpu: "2"
          memory: "4Gi"
        controlledResources: ["cpu", "memory"]
```

---

## 🧭 Network Policies

### NetworkPolicy Definition

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-allow-only
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api                         # Apply to pods with app=api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: production
          podSelector:
            matchLabels:
              app: web                 # Allow from web pods in same namespace
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: monitoring
          podSelector:
            matchLabels:
              app: prometheus          # Allow from Prometheus in monitoring
      ports:
        - port: 8080
          protocol: TCP
    - from:
        - ipBlock:
            cidr: 10.0.0.0/16
            except:
              - 10.0.1.0/24           # Allow from 10.0.0.0/16 except 10.0.1.0/24
      ports:
        - port: 443
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: database
      ports:
        - port: 5432
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0           # Allow internet access
            except:
              - 10.0.0.0/8
              - 172.16.0.0/12
              - 192.168.0.0/16
```

### Default Policies

```yaml
# Default deny all ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
spec:
  podSelector: {}
  policyTypes:
    - Ingress

# Default deny all egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
spec:
  podSelector: {}
  policyTypes:
    - Egress

# Default allow all (if you need to revert)
# No NetworkPolicy = allow all (default behavior)
```

---

## 🧭 RBAC & Service Accounts

### RBAC Objects

```yaml
# ServiceAccount — identity for pods
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-service-account
  namespace: production
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/my-role  # IAM for IRSA

---
# Role — permissions within a namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: production
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log", "pods/status"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["pods/exec"]
    verbs: ["create"]

---
# RoleBinding — binds Role to subjects
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: production
subjects:
  - kind: User
    name: "alice@example.com"
    apiGroup: rbac.authorization.k8s.io
  - kind: ServiceAccount
    name: my-service-account
    namespace: production
  - kind: Group
    name: "developers"
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io

---
# ClusterRole — cluster-wide permissions
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-admin
rules:
  - apiGroups: ["*"]
    resources: ["*"]
    verbs: ["*"]
  - nonResourceURLs: ["*"]
    verbs: ["*"]

---
# ClusterRoleBinding — binds ClusterRole cluster-wide
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cluster-admin-binding
subjects:
  - kind: User
    name: "admin@example.com"
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
```

### RBAC Verbs & Resources

```text
Standard Verbs:
  get, list, watch, create, update, patch, delete, deletecollection

Common Resources:
  pods, pods/log, pods/exec, pods/status
  services, endpoints, endpointslices
  configmaps, secrets
  deployments, statefulsets, daemonsets, replicasets
  persistentvolumes, persistentvolumeclaims, storageclasses
  nodes, namespaces, events
  ingresses, networkpolicies
  roles, rolebindings, clusterroles, clusterrolebindings
  serviceaccounts

API Groups:
  "" (core)    — pods, services, configmaps, secrets, nodes, ...
  apps         — deployments, statefulsets, daemonsets
  networking.k8s.io — ingresses, networkpolicies
  rbac.authorization.k8s.io — roles, rolebindings
  autoscaling  — horizontalpodautoscalers
  batch        — jobs, cronjobs
```

### Service Account in Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  serviceAccountName: my-service-account
  automountServiceAccountToken: true      # Mount token (default)
  containers:
    - name: app
      image: myapp
      # Token mounted at /var/run/secrets/kubernetes.io/serviceaccount/
```

---

## 🧭 Namespaces & Resource Quotas

### Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    env: production
    team: platform
---
apiVersion: v1
kind: Namespace
metadata:
  name: staging
  labels:
    env: staging
    team: platform
```

### Resource Quota

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-quota
  namespace: production
spec:
  hard:
    requests.cpu: "10"                   # Total CPU requests
    requests.memory: "20Gi"              # Total memory requests
    limits.cpu: "20"                     # Total CPU limits
    limits.memory: "40Gi"                # Total memory limits
    pods: "50"                           # Max pods
    services: "20"                       # Max services
    configmaps: "30"                     # Max ConfigMaps
    persistentvolumeclaims: "10"         # Max PVCs
    requests.storage: "500Gi"            # Total storage requests
    count/deployments.apps: "10"         # Max deployments
    count/ingresses.networking.k8s.io: "5"
```

---

## 🧭 Limit Ranges

### LimitRange

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: container-limits
  namespace: production
spec:
  limits:
    - type: Container
      default:                           # Default limits if not specified
        cpu: "500m"
        memory: "512Mi"
      defaultRequest:                    # Default requests if not specified
        cpu: "200m"
        memory: "256Mi"
      max:                               # Maximum allowed limits
        cpu: "4"
        memory: "8Gi"
      min:                               # Minimum allowed requests
        cpu: "50m"
        memory: "64Mi"
      maxLimitRequestRatio:              # Max limit/request ratio
        cpu: "4"                         # e.g., limit=2, request≥0.5
    - type: PersistentVolumeClaim
      max:
        storage: "100Gi"
      min:
        storage: "1Gi"
```

---

## 🧭 Pod Security Policies

### Pod Security Standards (v1.23+)

```yaml
# Namespace-level enforcement (replaces PSP)
apiVersion: v1
kind: Namespace
metadata:
  name: secure-ns
  labels:
    pod-security.kubernetes.io/enforce: restricted    # privileged, baseline, restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: restricted       # Log violations
    pod-security.kubernetes.io/warn: baseline           # Warn user
```

### Pod Security Admission (v1.25+)

```yaml
# Per-namespace Pod Security Admission configuration
apiVersion: v1
kind: Namespace
metadata:
  name: prod-apps
  labels:
    pod-security.kubernetes.io/enforce: baseline      # Reject violations
    pod-security.kubernetes.io/enforce-version: "v1.28"
    pod-security.kubernetes.io/audit: restricted       # Log but accept
    pod-security.kubernetes.io/warn: restricted        # Warn but accept

---
# OPA/Gatekeeper — more flexible policy engine (see 02-advanced-k8s.md)
```

---

## 🧭 Liveness, Readiness & Startup Probes

### Probe Definitions

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: probe-demo
spec:
  containers:
    - name: app
      image: myapp
      livenessProbe:                       # Is the container alive?
        httpGet:
          path: /healthz
          port: 8080
          httpHeaders:
            - name: X-Health-Check
              value: "true"
        initialDelaySeconds: 5
        periodSeconds: 10
        timeoutSeconds: 3
        successThreshold: 1                 # Must be 1 for liveness
        failureThreshold: 3                 # Kill after 3 failures

      readinessProbe:                      # Is the container ready to serve?
        httpGet:
          path: /ready
          port: 8080
        initialDelaySeconds: 3
        periodSeconds: 5
        timeoutSeconds: 3
        successThreshold: 1
        failureThreshold: 1                 # Remove from Service on 1 failure

      startupProbe:                        # Slow-starting containers
        httpGet:
          path: /startup
          port: 8080
        initialDelaySeconds: 0
        periodSeconds: 10
        failureThreshold: 30                # Give 300 seconds to start
        # startupProbe supersedes liveness during startup period
```

### Probe Types

```yaml
# HTTP probe
livenessProbe:
  httpGet:
    path: /health
    port: 8080
    httpHeaders:
      - name: Authorization
        value: "Bearer token123"

# TCP probe
readinessProbe:
  tcpSocket:
    port: 3306
  initialDelaySeconds: 15
  periodSeconds: 10

# Command probe
livenessProbe:
  exec:
    command:
      - cat
      - /tmp/healthy
  initialDelaySeconds: 5
  periodSeconds: 5

# gRPC probe (v1.24+)
livenessProbe:
  grpc:
    port: 50051
    service: "health.HealthCheck"          # Optional
  initialDelaySeconds: 5
```

### Probe Lifecycle

```text
Pod Startup Timeline:

  Pod Created
       │
       ▼
  ┌──────────────────────────────────────────┐
  │          STARTUP PROBE PHASE              │
  │  startupProbe runs (every periodSeconds)  │
  │  Container is restarting / initializing   │
  │  livenessProbe is DISABLED during this    │
  └──────────────────┬───────────────────────┘
                     │ (startup succeeds)
                     ▼
  ┌──────────────────────────────────────────┐
  │          LIVENESS + READINESS             │
  │  livenessProbe: is it alive?              │
  │  readinessProbe: is it ready for traffic? │
  │                                           │
  │  liveness fails → restart container       │
  │  readiness fails → remove from Service    │
  └──────────────────────────────────────────┘
```

---

## 🧭 Affinity & Anti-Affinity

### Node Affinity

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: affinity-demo
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:   # Hard requirement
        nodeSelectorTerms:
          - matchExpressions:
              - key: topology.kubernetes.io/zone
                operator: In
                values:
                  - us-east-1a
                  - us-east-1b
              - key: disktype
                operator: In
                values:
                  - ssd
      preferredDuringSchedulingIgnoredDuringExecution:  # Soft preference
        - weight: 80
          preference:
            matchExpressions:
              - key: topology.kubernetes.io/zone
                operator: In
                values:
                  - us-east-1a
        - weight: 20
          preference:
            matchExpressions:
              - key: another-node-label-key
                operator: Exists
```

### Pod Affinity / Anti-Affinity

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cache-deployment
spec:
  template:
    spec:
      affinity:
        podAffinity:                             # Co-locate with other pods
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchExpressions:
                  - key: app
                    operator: In
                    values:
                      - cache
              topologyKey: topology.kubernetes.io/zone
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app: frontend
                topologyKey: kubernetes.io/hostname

        podAntiAffinity:                         # Spread pods apart
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchExpressions:
                    - key: app
                      operator: In
                      values:
                        - web
                topologyKey: kubernetes.io/hostname
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchLabels:
                  app: web
              topologyKey: topology.kubernetes.io/zone
              # Each zone gets at most one web pod
```

---

## 🧭 Taints & Tolerations

### Taints on Nodes

```bash
# Add taint to node
kubectl taint nodes node1 key=value:NoSchedule
kubectl taint nodes node1 key=value:PreferNoSchedule
kubectl taint nodes node1 key=value:NoExecute

# Remove taint
kubectl taint nodes node1 key=value:NoSchedule-
kubectl taint nodes node1 key-

# View taints
kubectl describe node node1 | grep Taints
```

### Tolerations on Pods

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: taint-demo
spec:
  tolerations:
    - key: "dedicated"
      operator: "Equal"
      value: "gpu"
      effect: "NoSchedule"

    - key: "app"
      operator: "Equal"
      value: "blue"
      effect: "NoSchedule"

    - key: "node.kubernetes.io/not-ready"     # Tolerate node issues
      operator: "Exists"
      effect: "NoExecute"
      tolerationSeconds: 300                  # Wait 5 min before eviction

    - operator: "Exists"                      # Tolerate ALL taints
      # No key, no value — matches everything
```

### Taint Effects

```text
Taint Effects:

  NoSchedule         ─── Pod won't be scheduled unless it tolerates
  PreferNoSchedule   ─── Scheduler tries to avoid (soft)
  NoExecute          ─── Evicts existing pods that don't tolerate

  Common Taints:
    node.kubernetes.io/not-ready
    node.kubernetes.io/unreachable
    node.kubernetes.io/memory-pressure
    node.kubernetes.io/disk-pressure
    node.kubernetes.io/network-unavailable
    node.kubernetes.io/unschedulable
    node.kubernetes.io/out-of-disk
```

---

## 🧭 kubectl Commands

### Essential Commands

```bash
# Cluster info
kubectl cluster-info
kubectl cluster-info dump
kubectl version --short
kubectl get nodes -o wide
kubectl describe node <node>
kubectl top node
kubectl top pod

# Namespace operations
kubectl get namespaces
kubectl config set-context --current --namespace=production

# Pod operations
kubectl get pods -n production
kubectl get pods --all-namespaces -o wide
kubectl get pods -l app=web,version=v2
kubectl describe pod <name>
kubectl logs <pod> -c <container>
kubectl logs --tail=100 -f <pod>
kubectl exec -it <pod> -- sh
kubectl cp <pod>:/path/file ./local
kubectl port-forward <pod> 8080:80
kubectl attach <pod> -i

# Events
kubectl get events --sort-by='.lastTimestamp'
kubectl get events -w

# API Resources
kubectl api-resources
kubectl api-versions
kubectl explain pod.spec.containers
```

### CRUD Operations

```bash
# Create
kubectl create deployment nginx --image=nginx
kubectl create configmap my-config --from-file=config.properties
kubectl create secret generic my-secret --from-literal=password=mypass
kubectl apply -f deployment.yaml
kubectl apply -f ./manifests/
kubectl apply -k ./kustomize-dir/                  # Kustomize

# Read
kubectl get all                                    # Pods, services, deployments
kubectl get pods -o yaml                           # Full YAML output
kubectl get pods -o json | jq '.items[].metadata.name'
kubectl get pods --watch                           # Watch for changes
kubectl get deployments,services,ingress -o wide

# Update
kubectl edit deployment/web
kubectl set image deployment/web nginx=nginx:1.26
kubectl scale deployment/web --replicas=5
kubectl label pods <pod> version=v2
kubectl annotate pods <pod> description="my desc"
kubectl patch deployment/web -p '{"spec":{"replicas":3}}'

# Delete
kubectl delete pod <name>
kubectl delete -f deployment.yaml
kubectl delete deployment,service --all -n test
kubectl delete pods -l version=v1
kubectl delete namespace test --grace-period=0 --force
```

### Output Formatting

```bash
# Output formats
kubectl get pods -o wide                            # More detail
kubectl get pods -o yaml                            # YAML
kubectl get pods -o json                            # JSON
kubectl get pods -o jsonpath='{.items[*].metadata.name}'
kubectl get pods -o=custom-columns=NAME:.metadata.name,STATUS:.status.phase
kubectl get pods --sort-by='.status.startTime'

# JSONPath examples
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'

# Dry run
kubectl apply -f deployment.yaml --dry-run=client
kubectl delete pod <name> --dry-run=server
```

### Debugging

```bash
# Debug pods
kubectl debug -it <pod> --image=busybox --target=<container>
kubectl debug node/node1 -it --image=ubuntu
kubectl logs -f --selector app=web
kubectl logs --previous <pod>                       # Previous crashed container

# Temporary proxy
kubectl proxy --port=8080                           # Access API at http://localhost:8080

# Copy files
kubectl cp <pod>:/etc/config ./local-config
kubectl cp ./local-file <pod>:/tmp/

# Execute commands
kubectl exec deploy/web -- printenv
kubectl exec <pod> -- cat /var/log/app.log

# Port forwarding
kubectl port-forward service/web 8080:80
kubectl port-forward pod/db 5432:5432
```

---

## 🧭 Helm Charts

### Helm Basics

```bash
# Repo management
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm repo list
helm search repo nginx

# Install/upgrade
helm install my-nginx bitnami/nginx --namespace web --create-namespace
helm upgrade my-nginx bitnami/nginx --set image.tag=1.25 --reuse-values

# Rollback
helm rollback my-nginx 1
helm history my-nginx

# Uninstall
helm uninstall my-nginx
```

### Chart Structure

```text
my-chart/
├── Chart.yaml                    # Metadata (name, version, description)
├── values.yaml                   # Default configuration values
├── values.schema.json            # JSON Schema for values validation
├── charts/                       # Sub-charts (dependencies)
│   └── postgresql/
├── templates/                    # Go template YAML files
│   ├── _helpers.tpl             # Template helpers
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── hpa.yaml
│   ├── serviceaccount.yaml
│   ├── tests/
│   │   └── test-connection.yaml
│   └── NOTES.txt                # Post-install instructions
└── .helmignore                   # Files to exclude
```

### Chart.yaml

```yaml
apiVersion: v2
name: my-web-app
description: A production-grade web application
type: application
version: 1.2.3
appVersion: "1.0.0"
kubeVersion: ">=1.25.0-0"
home: https://example.com
sources:
  - https://github.com/example/my-web-app
maintainers:
  - name: Dev Team
    email: dev@example.com
    url: https://example.com
dependencies:
  - name: postgresql
    version: "~12.1.0"
    repository: oci://registry-1.docker.io/bitnamicharts
    condition: postgresql.enabled
    alias: database
  - name: redis
    version: "~18.0.0"
    repository: https://charts.bitnami.com/bitnami
    condition: redis.enabled
annotations:
  category: Application
```

### Value Templates

```yaml
# values.yaml
replicaCount: 3

image:
  repository: myapp/web
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80
  targetPort: 8080

ingress:
  enabled: true
  host: myapp.example.com
  tls: true

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi

env:
  - name: NODE_ENV
    value: "production"

postgresql:
  enabled: true
  auth:
    database: myapp
    username: myapp
```

```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "my-chart.fullname" . }}
  labels:
    {{- include "my-chart.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "my-chart.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "my-chart.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - containerPort: {{ .Values.service.targetPort }}
          env:
            {{- toYaml .Values.env | nindent 12 }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
```

---

## 🧭 Operators

### Operator Pattern

```text
Operator = Custom Controller + Custom Resource Definitions (CRDs)

                    User creates Custom Resource
                             │
                             ▼
                    ┌────────────────────┐
                    │   Custom Resource   │
                    │  (e.g., RedisCluster)│
                    │  name: my-cluster   │
                    │  replicas: 3        │
                    └────────┬───────────┘
                             │
                             ▼
                    ┌────────────────────┐
                    │       Operator      │  ← Watches CR
                    │  (Custom Controller)│     Reconciles desired vs actual
                    │                     │
                    │  Manages:           │
                    │  • StatefulSet      │
                    │  • Service          │
                    │  • ConfigMap        │
                    │  • Secrets          │
                    │  • Backup Jobs      │
                    └────────────────────┘
```

### Popular Operators

```bash
# Install operators via OLM (Operator Lifecycle Manager) or Helm
helm install prometheus-operator prometheus-community/kube-prometheus-stack
helm install strimzi-kafka strimzi/strimzi-kafka-operator
helm install redis-operator ot-container-kit/redis-operator
helm install postgres-operator crunchydata/pgo
helm install cert-manager jetstack/cert-manager
```

### CRD Example

```yaml
# Custom Resource Definition
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: redisclusters.cache.example.com
spec:
  group: cache.example.com
  names:
    kind: RedisCluster
    plural: redisclusters
    singular: rediscluster
    shortNames:
      - rc
  scope: Namespaced
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          required: ["spec"]
          properties:
            spec:
              type: object
              required: ["replicas"]
              properties:
                replicas:
                  type: integer
                  minimum: 1
                version:
                  type: string
                persistence:
                  type: object
                  properties:
                    size:
                      type: string
                resources:
                  type: object
                  properties:
                    limits:
                      type: object

---
# Custom Resource (created by user)
apiVersion: cache.example.com/v1
kind: RedisCluster
metadata:
  name: production-cache
spec:
  replicas: 5
  version: "7.2"
  persistence:
    size: "100Gi"
  resources:
    limits:
      memory: "4Gi"
      cpu: "2"
```

---

## 🧠 Simplest Mental Model

```text
KUBERNETES = Hotel management for containers

  PODS = Guest rooms
    • Smallest unit — one or more guests (containers) sharing the room
    • Each guest room gets a private IP inside the hotel
    • Ephemeral: guests come and go, rooms are cleaned
    • Init Containers = Housekeeping that preps the room before guest arrives
    • Sidecar = Butler service in the same room (logging, monitoring)

  DEPLOYMENTS = Room booking system
    • "Keep 3 of these rooms available at all times"
    • If a guest checks out (pod dies), new one is automatically booked
    • Rolling Update = Renovate rooms one at a time, guests keep coming
    • HPA = "More guests arriving? Open more rooms"

  SERVICES = Hotel front desk / directory
    • ClusterIP = Internal hotel phone directory
    • NodePort = Direct phone line to a specific hotel extension
    • LoadBalancer = Main hotel phone number to the outside world
    • Ingress = Hotel concierge: routes calls based on "who's calling" (host)

  CONFIGMAPS = Bulletin board in lobby (non-sensitive info)
  SECRETS = Manager's safe (passwords, keys)
    • Both are posted on a board each room can read

  VOLUMES = Lockers outside the room
    • PV = Bank of lockers (cluster resource)
    • PVC = "I need this size locker" (request)
    • StorageClass = Different locker types (SSD, HDD, network)

  STATEFULSETS = Assigned rooms with name plates
    • postgres-0, postgres-1, postgres-2 — always the same names
    • Each has its own permanent locker (PVC)
    • Boot order: room 0 first, then 1, then 2

  DAEMONSETS = Hotel staff — one in every room
    • Maid service, security guard, maintenance
    • fluentd, Prometheus Node Exporter, kube-proxy

  JOBS = Room service delivery (run once)
  CRONJOBS = Daily turndown service at 6 PM

  NETWORK POLICIES = "Only room service can enter. No other guests."

  RBAC = Key cards
    • ServiceAccount = Automated key card for robots
    • Role = "Can enter rooms 101-110"
    • ClusterRole = "Can enter any room in any building"
    • RoleBinding = "Give this robot that key"

  TAINTS = "No peanut-allergic guests allowed"
  TOLERATIONS = "I'm not allergic to peanuts"

  NAMESPACES = Hotel floors
    • Floor 1 = production (penthouse, strict rules)
    • Floor 2 = staging (training floor)
    • Quotas = "Floor 1 can use max 100 rooms"

Kubernetes is a DECLARATIVE system: you describe the desired state,
and the control plane makes it happen, continuously reconciling.
```

---

## Interview Questions

### Beginner Level

**Q1: Explain the architecture of a Kubernetes cluster.**

**Why interviewers ask this**: Fundamental — shows you understand the control plane vs data plane split.

**Ideal answer structure**:
1. **Control plane**: API Server (front-end, validates/processes requests), etcd (distributed key-value store for cluster state), Scheduler (assigns pods to nodes), Controller Manager (runs controllers: Deployment, ReplicaSet, etc.).
2. **Data plane / Worker nodes**: kubelet (agent, manages pods via CRI), kube-proxy (network rules via iptables/IPVS/eBPF), container runtime (containerd/CRI-O).
3. **Flow**: `kubectl apply -f deploy.yaml` → API Server validates → stored in etcd → Controller Manager creates ReplicaSet → Scheduler assigns → kubelet creates pod → container runtime pulls image + starts container.

**Common wrong answer**: "etcd stores all cluster data including pod logs" — etcd only stores Kubernetes object specifications and state; logs are on node filesystem or shipped to external logging.

**Q2**: What is a Pod and why is it the smallest deployable unit instead of a container?

**Answer**: A Pod is a group of one or more containers sharing the same network namespace (same IP, localhost communication), storage volumes, and lifecycle. Why not just a container? 1) **Sidecar pattern**: a main container + helper (log shipper, proxy, config reloader) must share network. 2) **Shared volumes**: containers in a pod can mount the same volumes. 3) **Atomic scheduling**: all containers in a pod land on the same node. 4) **Co-location**: containers that are tightly coupled (e.g., web server + file sync) belong together.

### Intermediate Level

**Q3: How does a Kubernetes Service route traffic to Pods? Walk through the different proxy modes.**

**Answer**: 1) **ClusterIP**: stable virtual IP, round-robin across ready pods. 2) **NodePort**: opens port on every node, forwards to ClusterIP. 3) **LoadBalancer**: provisions cloud LB, forwards to NodePort → ClusterIP → pods. Proxy modes: **iptables** (default, random DNAT rule selection, O(1) per service but linear rule chain updates), **IPVS** (hash table, O(1) for both routing and updates, supports more algorithms), **eBPF** (Cilium, kernel-level, fastest). A Service is essentially a stable endpoint abstraction backed by EndpointSlice objects that kubelet updates via readiness probes.

**Q4**: How does the scheduler decide where to place a pod?

**Answer**: Two-phase algorithm: **Filtering** (predicates): check node resources (CPU/memory), port conflicts, nodeSelector, affinity rules, taints/tolerations, and `NodeConditions` (disk pressure, PID pressure). **Scoring** (priorities): rank remaining nodes by resource fit (LeastRequestedPriority / MostRequestedPriority), inter-pod affinity, and custom scoring plugins. The scheduler uses a **scheduling framework** with plugin-based architecture (queue sort, pre-filter, filter, post-filter, pre-score, score, normalize score, reserve, permit, pre-bind, bind). Default uses predicates + priorities, but can be extended with custom schedulers or schedulable via `spec.schedulerName`.

### Senior Level

**Q5: A pod is in `CrashLoopBackOff`. Walk through your debugging process.**

**Why interviewers ask this**: Tests practical troubleshooting skills.

**Answer**: 1) `kubectl describe pod <pod>` — check Events for image pull errors, OOMKill, liveness probe failures. 2) `kubectl logs <pod> --previous` — check logs of the crashed container. 3) Check resource limits (`resources.requests/limits`) — common OOM or CPU throttling. 4) `kubectl exec -it <pod> -- sh` — if container runs but dies, check internal state. 5) Check ConfigMap/Secret mounting — permission errors cause immediate crash. 6) Liveness probe: if probe command/HTTP check fails, K8s restarts; check probe path and timeout. 7) Init containers failing → check init container logs. 8) Check node health: `kubectl describe node <node>` for conditions.

**Q6**: Design a pod lifecycle for a stateful database in Kubernetes. How do you handle upgrades, scaling, and failures?

**Answer**: Use **StatefulSet** with `volumeClaimTemplates` (unique PVC per replica). **Upgrades**: Rolling update with `podManagementPolicy: OrderedReady` — pods updated one-by-one, each must become Ready before next starts. **Scaling**: StatefulSet creates pods in order (0, 1, 2...) and deletes in reverse. **Failures**: Headless Service for stable DNS names (`pod-0.svc.cluster.local`). Use **readiness probes** (application-level health: DB responding, replica caught up) and **liveness probes** (just TCP check). **Backup**: `VolumeSnapshot` via CSI for point-in-time snapshots. For production: use an Operator (Strimzi for Kafka, Zalando for Postgres) that adds backup, failover, and resharding logic beyond what StatefulSet provides.

### Staff/Principal Level

**Q7: Your cluster has 5000 nodes and 100K pods. kube-apiserver becomes unresponsive during rolling updates. Diagnose.**

**Why**: Tests understanding of K8s scalability limits and control plane performance.

**Answer**: **API Server watch storm**. Each controller and kubelet watches API objects. With 5000 nodes and 100K pods, a rolling update generates 100K+ pod update events — each trigger reconcile loops in every controller. etcd is likely overloaded: watch connections + compaction + MVCC history. Fix: 1) Increase `--max-requests-inflight` (default 400). 2) **API Priority and Fairness** — ensure `system` priority for kubelets (watch starving is common). 3) **Optimistic concurrency**: use `resourceVersion=0` for list-watch to get snapshot + watch. 4) **etcd defrag + compaction**: `--auto-compaction-retention=5m`. 5) **Feature gates**: `APIPriorityAndFairness=true`, `EventedPLEG` to reduce kubelet -> API server chatter. 6) Consider `Konnectivity` service for tunnel-based kubelet traffic. 7) Long-term: split into multiple clusters (federation or Cluster API).

**Q8**: Your organization wants to migrate 200 microservices from EC2 to Kubernetes with zero downtime. Design the migration strategy.

**Answer**: 1) **Phase 1 — Foundation**: Set up multi-tenant cluster with RBAC, network policies, resource quotas, monitoring (Prometheus/Grafana), and pod security standards. 2) **Phase 2 — Lift and Shift**: Migrate stateless services first — wrap in Deployment + Service, use existing RDS/ElastiCache externally. Validate traffic via DNS-based canary (Route53 weight 5% → K8s ingress). 3) **Phase 3 — Stateful**: Migrate stateful services using StatefulSets and Operators. Use `VolumeSnapshot` + `velero` for backup. 4) **Phase 4 — Optimize**: Adopt HPA (horizontal pod autoscaling), cluster-autoscaler, spot instances, service mesh (Istio/Linkerd). 5) **Rollback plan**: Maintain old EC2 ASG with zero desired, scale up on issues. Use traffic mirroring for validation. Key pitfall: DNS propagation delays (set low TTL before cutover). Ensure readiness probes match health check endpoints exactly.

### Tricky Edge Cases

**Q9**: A pod has `restartPolicy: Always` but when it exits with code 0, it restarts anyway. Why?

**Answer**: **Init container or sidecar restart behavior**. If an init container exits 0 but the main container has already started, the pod restarts the main container. Or: **restartPolicy** affects all containers in the pod — if any container exits (even 0), the pod restarts. Also: **ephemeral container** exit doesn't trigger restart. But the real edge case: **pause container** (infrastructure container) must be running for pod to be Ready. If the pause container dies (OOM from kernel memory pressure), the pod restarts despite the application container being healthy.

**Q10**: A NetworkPolicy allows traffic from app-a to app-b on port 8080. Traffic works in some node pairs but not others. Why?

**Answer**: **kube-proxy and NetworkPolicy implementation differences**. If using different CNI plugins or kube-proxy modes on different nodes (e.g., some nodes use iptables, others use eBPF/Cilium), the policy enforcement differs. Also: **NodePort traffic** bypasses NetworkPolicy (it goes directly through kube-proxy, not through the CNI's policy engine). Or: some CNI plugins (Calico) enforce at the node level via iptables, while others (Cilium) enforce at eBPF level — if the policy references `ipBlock` with CIDR that includes some nodes' pod CIDR but not others, traffic intermittently fails.


> **Run the live simulator**: [kubernetes-scheduling.html](/07-kubernetes/kubernetes-scheduling.html) — add pods, watch the scheduler score and bind them to nodes interactively.


## Related

- [Readme](05-cloud/README.md)
- [Cloudwatch Deep Dive](05-cloud/aws/cloudwatch/01-cloudwatch-deep-dive.md)
- [Cloudwatch Observability](05-cloud/aws/cloudwatch/02-cloudwatch-observability.md)
- [Ec2 Deep Dive](05-cloud/aws/ec2/01-ec2-deep-dive.md)
- [Ec2 Networking Security](05-cloud/aws/ec2/02-ec2-networking-security.md)
- [Ecs Deep Dive](05-cloud/aws/ecs/01-ecs-deep-dive.md)

## Runtime Flow: Pod Scheduling

```
Step  Control Plane                       Component           Time
────  ──────────────────────────────       ───────────────     ─────
  1   User runs: kubectl apply -f pod.yaml    kubectl          0ms
  2   API Server validates + persists pod    etcd              5-50ms
  3   Scheduler watches unscheduled pods     Scheduler         0.1ms
  4   Scheduler runs filter plugins:          Scheduling        1-5ms
      ├── NodeUnschedulable (node status)
      ├── NodeResourcesFit (CPU/MEM/GUARANTEED)
      ├── NodePorts (port conflict check)
      └── InterPodAffinity (pod topology)
  5   Scheduler runs score plugins:           Scoring           1-5ms
      ├── NodeResourcesBalancedAllocation
      ├── PodTopologySpread (zones)
      └── ImageLocality (pull latency)
  6   Scheduler picks winning node            bind decision     0.01ms
  7   Scheduler POSTs binding to API Server   Bind              1ms
  8   etcd persists binding                   etcd              5ms
  9   kubelet watches pod binding on its node  kubelet          0.1ms
 10   kubelet invokes CRI to create container  containerd       50-200ms
 11   CRI pulls image (if not cached)          Registry pull    1-30s
 12   CRI creates sandbox (pause container)    runc             50ms
 13   CRI creates app container                runc             50ms
 14   CNI plugin assigns IP + configures net   Calico/Cilium   10-50ms
 15   CSI plugin mounts volumes                EBS/EFS driver   100-500ms
 16   kubelet updates pod status to Running    kubelet          0.1ms
 17   kube-proxy updates iptables/IPVS         kube-proxy       1-5ms
 18   Service endpoints updated + ready        EndpointSlice    1-10ms
```

```mermaid
sequenceDiagram
    participant U as kubectl
    participant A as API Server
    participant E as etcd
    participant S as Scheduler
    participant K as kubelet
    participant C as CRI
    participant N as CNI
    participant V as CSI

    U->>A: apply pod.yaml
    A->>E: persist Pod spec
    S->>A: watch unscheduled pods
    S->>S: filter + score nodes
    S->>A: bind pod to node-3
    A->>E: persist binding
    K->>A: watch my pods
    K->>C: CreateContainer (pod sandbox)
    C->>C: pull image, runc create
    K->>N: AssignPodIP (CNI)
    K->>V: MountVolume (CSI)
    K->>A: update PodStatus=Running
```

## Deep Internals: CRI — Container Runtime Interface

### Pod Sandbox Lifecycle

```mermaid
sequenceDiagram
    participant K as kubelet
    participant C as CRI Runtime (containerd)
    participant S as shim (containerd-shim)
    participant R as runc
    participant N as Namespaces

    K->>C: RunPodSandbox (config)
    C->>S: create shim process
    S->>R: runc create (pause container)
    R->>N: create namespaces (PID, NET, MNT, UTS, IPC)
    R-->>S: pause container running
    S-->>C: sandbox ID
    C-->>K: PodSandboxID
    
    K->>C: CreateContainer (nginx, config)
    C->>C: unpack image (snapshotter: overlayfs)
    C->>S: create container in sandbox
    S->>R: runc create nginx
    R->>N: join sandbox namespaces
    R->>R: apply cgroups (CPU, MEM limits)
    R-->>S: container ready
    S-->>C: container ID
    
    K->>C: StartContainer (container ID)
    C->>S: exec init process
    S->>R: runc start
    R->>R: exec nginx (PID 1 in container)
    R-->>S: running
    S-->>C: started
    C-->>K: Container running
```

### CRI Components

```
kubelet                              Control Plane
   │
   ├── CRI gRPC API (runtime.v1.RuntimeService)
   │   ├── RunPodSandbox / StopPodSandbox
   │   ├── CreateContainer / StartContainer / StopContainer / RemoveContainer
   │   ├── ContainerStatus / ListContainers
   │   └── Exec / Attach / PortForward
   │
   ▼
containerd                           Container Runtime
   │
   ├── containerd-shim               Per-container shim (keeps runc alive)
   │   └── manages STDIO + exit code
   │
   ▼
runc (OCI Runtime)                   Low-level runtime
   ├── creates container (namespaces + cgroups)
   └── runs container process
```

### Namespace Isolation

| Namespace | Isolates | Created by CRI |
|---|---|---|
| **PID** | Process IDs | Sandbox + each container |
| **NET** | Network stack, IP, ports | Sandbox (shared by all containers in pod) |
| **MNT** | Mount points | Container rootfs + volumes |
| **UTS** | Hostname + domain | Sandbox |
| **IPC** | System V IPC + POSIX msg | Sandbox |
| **User** | User/group IDs | Optional (user-namespace remapping) |

### CRI Container Create Flow Detail

```
Step  kubelet → CRI         What Happens
────  ─────────────────────  ─────────────────────────────────
  1   ImageService.PullImage  Check local cache → pull from registry
  2   Snapshooter.Prepare     Create overlayfs layer (diff + lower)
  3   CreateContainer         Write OCI spec.json (config.json)
  4   OCI spec includes:
      ├── Rootfs path (overlay mount)
      ├── Process args (entrypoint + cmd)
      ├── Mounts (volumes, secrets, configmaps)
      ├── Linux.Namespaces (join sandbox)
      ├── Linux.Resources (CPU/MEM cgroups)
      └── Linux.Seccomp (syscall filter)
  5   runc create             Fork + exec into namespaces
  6   runc start              Execute init process
```
