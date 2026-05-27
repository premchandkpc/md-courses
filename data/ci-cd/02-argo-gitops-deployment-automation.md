# Argo CD & GitOps: Deployment Automation at Scale

## Table of Contents
1. NOOB Explanation
2. GitOps Principles
3. Argo CD Architecture Internals
4. Progressive Delivery Strategies
5. Large-Scale Multi-Cluster Systems
6. Failure Scenarios & Recovery
7. Kustomize & Helm Integration
8. Production Incidents
9. Security & RBAC
10. Code Examples
11. Comparison Tables

---

## Section 1: NOOB Explanation - Git as Source of Truth

### The Traditional Deployment Model (IMPERATIVE)

```
Engineer → kubectl apply -f deployment.yaml → Kubernetes Cluster
                                  ↓
                          Ad-hoc, manual
                      Hard to audit, easy to break
```

Problems:
- "Infrastructure Drift": cluster state diverges from what you intended
- **Manual**: someone must SSH and run commands
- **Unrepeatable**: hard to redeploy if cluster crashes
- **Unauditable**: no history of who changed what

### The GitOps Model (DECLARATIVE)

```
Engineer → git commit → GitHub repo → Argo CD → Kubernetes Cluster
                            ↑                            ↓
                    Source of Truth            Continuous Sync
                    (deployment.yaml)          (every 3 minutes)
                    
Git history shows:
├─ What was deployed when
├─ Who made the change
├─ Why (commit message)
└─ Can revert any change instantly
```

Benefits:
- **Declarative**: "here's the desired state" (git), not "run these commands"
- **Auditable**: every change in git history
- **Repeatable**: revert a commit to rollback
- **Safe**: drift detection (cluster != git) triggers alerts
- **Automatic**: Argo syncs cluster to match git every N minutes

### Argo CD as the Sync Engine

Argo CD is a **pull-based** continuous deployment operator that:

1. **Watches** a git repository for changes
2. **Compares** desired state (git) with actual state (cluster)
3. **Detects drift** (cluster diverged from git)
4. **Syncs** automatically (or on demand)
5. **Reports** status (healthy, degraded, out-of-sync)

Unlike push-based CI/CD (Jenkins pushes to cluster), Argo **pulls from git**:
- Cluster can be air-gapped (no egress needed)
- Git becomes security boundary (no secrets on runners)
- Single source of truth (git repo is the authority)

---

## Section 2: GitOps Principles

### The Five Principles

**Principle 1: Declarative Description**
```yaml
# ✓ GitOps (declarative)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    spec:
      containers:
      - name: app
        image: myapp:v1.2.3

# ✗ NOT GitOps (imperative)
$ kubectl scale deployment myapp --replicas=3
$ kubectl set image deployment myapp app=myapp:v1.2.3
```

**Principle 2: Git as Source of Truth**
```
Desired State (git):          Actual State (cluster):
deployment.yaml:             kubectl get deployment:
  replicas: 3                   replicas: 3 ✓
  image: v1.2.3                image: v1.2.3 ✓

If someone manually: kubectl scale --replicas=1
  Desired: 3 (git)           Actual: 1 (cluster)
  → Drift detected!          → Argo auto-syncs → back to 3
```

**Principle 3: Pull Model (Not Push)**

```
Traditional Push Model:
┌──────┐         kubectl apply       ┌──────────────┐
│  CI  │ ────────────────────────→  │ Kubernetes   │
└──────┘  (needs cluster access)     │ Cluster      │
                                      └──────────────┘

Problems:
- CI runner needs kubectl creds
- No way to trigger deploy from git
- Cluster can't be air-gapped


GitOps Pull Model:
┌──────────────┐                    ┌──────┐
│     Git      │ ← (read git)       │ Argo │
│  Repo        │                    │  CD  │
└──────────────┘                    │ (in  │
                                     │ cluster)
                                     └──────┘
                                        │
                                        ▼
                                    ┌──────────────┐
                                    │ Kubernetes   │
                                    │ Cluster      │
                                    └──────────────┘

Benefits:
- Cluster pulls from git (only needs git auth, not kubectl)
- Cluster can pull on schedule (no push webhooks needed)
- Argo SD inside cluster (no external access needed)
```

**Principle 4: Continuous Reconciliation**

```
Every 3 minutes (configurable):
1. Argo fetches git repo
2. Renders YAML (apply overlays, helm, kustomize)
3. Compares with cluster state
4. Shows diff
5. Optionally auto-syncs

Timeline:
0min:  User commits change to git
3min:  Argo detects change
3.5min: Argo applies to cluster
4min:  Status shows "Synced"
5min:  Monitoring shows new pods running

If someone manually changes cluster:
3min:  Argo detects drift (cluster != git)
3.5min: Argo reverts the manual change
4min:  Status shows "OutOfSync → Synced"
```

**Principle 5: Observability & Visibility**

```yaml
# Git becomes audit trail
$ git log
commit abc123 - "Scale myapp to 5 replicas"
  Author: alice@company.com
  Date: 2024-05-20

commit def456 - "Update myapp image to v1.2.3"
  Author: bob@company.com
  Date: 2024-05-19

# Argo UI shows:
Application: myapp
├─ Status: Synced
├─ Sync Strategy: Auto
├─ Resources: 5 healthy, 0 degraded
├─ Desired Commit: abc123
├─ Actual Commit: abc123
├─ Last Sync: 2 minutes ago
└─ Sync History
   ├─ Synced commit abc123 (5 min ago)
   └─ Synced commit def456 (2 days ago)
```

---

## Section 3: Argo CD Architecture Internals

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster (ArgoCD)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Argo CD Server (API/UI)                     │  │
│  │  - REST API for manual sync, status queries              │  │
│  │  - Web UI (browser-based dashboard)                      │  │
│  │  - Authentication (OIDC, LDAP, local)                   │  │
│  │  - Port: 8080                                            │  │
│  └───────┬──────────────────────────────────────────────────┘  │
│          │                                                       │
│          ▼                                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │        Application Controller (Reconciliation)            │  │
│  │  - Watches Application CRDs                              │  │
│  │  - Pulls git repos on schedule                           │  │
│  │  - Renders YAML (Helm, Kustomize, Jsonnet)              │  │
│  │  - Compares desired vs actual state                      │  │
│  │  - Triggers sync (auto or manual)                        │  │
│  │  - Updates Application status                            │  │
│  │  - Replicas: 2 (HA by default)                           │  │
│  └───────┬──────────────────────────────────────────────────┘  │
│          │                                                       │
│  ┌──────────────────┬──────────────────────────────────────┐   │
│  │                  ▼                                       │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │ Git Webhook Listener (argocd-server)             │  │   │
│  │  │ - Receives github.com/gitlab.com webhooks       │  │   │
│  │  │ - Triggers immediate sync (< 5 sec)            │  │   │
│  │  │ - Updates Application status                    │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  │                                                        │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │ Notification Controller (argocd-notifications)  │  │   │
│  │  │ - Sends alerts on sync success/failure          │  │   │
│  │  │ - Integrates: Slack, Teams, Webhook             │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  │                                                        │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │ Redis Cache (session, sync state)               │  │   │
│  │  │ - Tracks in-flight syncs                        │  │   │
│  │  │ - Caches git repo contents                      │  │   │
│  │  │ - Session tokens                                │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  │                                                        │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │ Repo Server (git & helm operations)              │  │   │
│  │  │ - Clones git repos                              │  │   │
│  │  │ - Caches clone for 24h (configurable)          │  │   │
│  │  │ - Runs Helm, Kustomize, Jsonnet                │  │   │
│  │  │ - Renders final manifests                       │  │   │
│  │  │ - RPC interface for controller                  │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │        Target Cluster State (user apps)                 │  │
│  │  - All Kubernetes resources (pods, services, etc)      │  │
│  │  - Application controller watches for changes          │  │
│  │  - Syncs keep this in sync with git                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
         │
         ├─ SSH/HTTPS to → GitHub/GitLab
         │
         └─ HTTP to → Image registries (docker hub, ECR)
```

### Application CRD Definition

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
  namespace: argocd
spec:
  project: default

  # Where to fetch manifests
  source:
    repoURL: https://github.com/example/infra
    targetRevision: main  # branch, tag, or commit SHA
    path: apps/myapp      # directory in repo

    # Optional: templating
    helm:
      releaseName: myapp
      values: |
        replicas: 3
        image:
          tag: "v1.2.3"
    
    # OR kustomize
    # kustomize:
    #   namePrefix: prod-
    #   commonLabels:
    #     env: production

  # Where to deploy
  destination:
    server: https://kubernetes.default.svc  # same cluster
    namespace: production

  # Sync strategy
  syncPolicy:
    automated:
      prune: true        # delete resources removed from git
      selfHeal: true     # sync every 3 minutes
      allow:
        empty: false     # don't sync if no resources in git
    syncOptions:
    - CreateNamespace=true  # create namespace if not exists
    - RespectIgnoreDifferences=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m

  # Access control
  ignoreDifferences:
  - group: "apps"
    kind: Deployment
    jsonPointers:
    - /spec/replicas  # ignore if cluster has more replicas

  info:
  - name: Documentation
    value: https://github.com/example/infra/wiki/myapp
  - name: Slack Channel
    value: "#myapp-dev"
```

### Sync Engine Algorithm

```
Reconciliation Loop (runs every 3 minutes):

1. FETCH DESIRED STATE
   ├─ Fetch git repo at targetRevision
   ├─ Cache for 24 hours (optimization)
   ├─ Run Helm template / Kustomize / Jsonnet
   └─ Parse resulting YAML → Application resources

2. FETCH ACTUAL STATE
   ├─ Query Kubernetes API server
   ├─ Get all resources matching selector
   ├─ Read status fields (conditions, replica count)
   └─ Include custom resources (CRDs)

3. DIFF COMPARISON
   ├─ Use three-way merge (git, desired, actual)
   ├─ Apply ignoreDifferences rules
   ├─ Check status conditions
   └─ Categorize resources:
      ├─ Synced (desired == actual)
      ├─ OutOfSync (desired != actual)
      ├─ Unknown (error reading actual)
      └─ Pruned (in git but not in cluster)

4. SYNC DECISION
   ├─ If OutOfSync and automated=true:
   │  └─ Apply changes (kubectl apply)
   ├─ If Pruned and prune=true:
   │  └─ Delete from cluster (kubectl delete)
   └─ Update Application.status

5. UPDATE STATUS
   ├─ Application.status.operationState
   ├─ Application.status.resources
   ├─ Application.status.conditions
   └─ Fire notifications
```

### State Machine for Application

```
┌────────────────┐
│     Unknown    │  (first sync, error reading state)
└────────┬───────┘
         │ fetch state
         ▼
┌─────────────────────────────────────────┐
│            Syncing                      │ (applying changes)
├─────────────────────────────────────────┤
│ kubectl apply resources from git        │
│ kubectl delete pruned resources         │
│ Wait for deployments to be healthy      │
└────────┬──────────────────────┬─────────┘
         │                      │
      success              failure
         │                      │
         ▼                      ▼
    ┌──────────┐          ┌──────────┐
    │ Synced   │          │ SyncFailed
    └────┬─────┘          └────┬─────┘
         │                     │
         │ Drift detected      │ Manual changes
         │ (cluster diverges)  │ or deployment
         ▼                     │
    ┌──────────────┐          │
    │ OutOfSync    │←─────────┘
    └────┬─────────┘
         │ auto-sync enabled
         ▼
      Syncing (loop back)
```

---

## Section 4: Progressive Delivery Strategies

### Blue-Green Deployment with Argo Rollouts

```yaml
# Argo Rollouts: progressive delivery extension
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: myapp
spec:
  replicas: 10
  strategy:
    blueGreen:
      activeService: myapp
      previewService: myapp-preview
      autoPromotionEnabled: false  # manual promotion
      autoPromotionSeconds: 0

  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:v2.0.0  # new version

---
# Traffic split during canary
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: myapp-canary
spec:
  replicas: 10
  strategy:
    canary:
      steps:
      - setWeight: 10    # Send 10% of traffic to new version
      - pause:
          duration: 5m   # Wait 5 minutes
      - setWeight: 50    # 50% traffic
      - pause:
          duration: 5m
      - setWeight: 100   # 100% traffic (complete rollout)
      
      # Automatic rollback if error rate spikes
      analysis:
        interval: 1m
        threshold: 1
        templates:
        - name: error-rate
      
      trafficRouting:
        istio:
          virtualServices:
          - name: myapp-vs
            routes:
            - name: primary
```

**Timeline**:
```
Blue-Green Deployment:
0min:   Old version (v1.0.0): 10 pods
        New version (v2.0.0): 10 pods (healthy but no traffic)

3min:   Smoke tests pass, manual approval given
        → Switch service to v2.0.0

3.5min: v2.0.0 handles 100% traffic
        v1.0.0 still running (instant rollback if needed)

15min:  No errors, keep v2.0.0, delete v1.0.0


Canary Deployment:
0min:   v1.0.0: 90% traffic (9 pods)
        v2.0.0: 10% traffic (1 pod)
        Monitor metrics...

5min:   Error rate: 0.1% (normal)
        → Increase to 50% traffic
        v1.0.0: 50% (5 pods)
        v2.0.0: 50% (5 pods)

10min:  Error rate: 0.2% (normal)
        → Increase to 100% traffic
        v2.0.0: 100% (10 pods)

15min:  Scale down v1.0.0
```

### Kustomization for Environment Promotion

```
Directory structure:
├─ base/
│  ├─ kustomization.yaml
│  ├─ deployment.yaml
│  ├─ service.yaml
│  └─ configmap.yaml
│
├─ overlays/
│  ├─ dev/
│  │  ├─ kustomization.yaml
│  │  └─ patch-replicas.yaml
│  ├─ staging/
│  │  ├─ kustomization.yaml
│  │  └─ patch-replicas.yaml
│  └─ production/
│     ├─ kustomization.yaml
│     ├─ patch-replicas.yaml
│     └─ patch-resources.yaml


base/kustomization.yaml:
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: myapp
resources:
- deployment.yaml
- service.yaml
- configmap.yaml


overlays/dev/kustomization.yaml:
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
bases:
- ../../base
namePrefix: dev-
commonLabels:
  environment: dev
commonAnnotations:
  environment: dev
replicas:
- name: myapp
  count: 1
images:
- name: myapp
  newTag: "latest"
configMapGenerator:
- name: app-config
  literals:
  - LOG_LEVEL=DEBUG
  - REPLICAS=1


overlays/production/kustomization.yaml:
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
bases:
- ../../base
namePrefix: prod-
commonLabels:
  environment: production
replicas:
- name: myapp
  count: 10
images:
- name: myapp
  newTag: "v1.2.3"  # specific version
configMapGenerator:
- name: app-config
  literals:
  - LOG_LEVEL=INFO
  - REPLICAS=10
patchesStrategicMerge:
- patch-resources.yaml  # increase CPU/memory


Argo Application for each environment:
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-dev
  namespace: argocd
spec:
  source:
    repoURL: https://github.com/example/infra
    targetRevision: main
    path: overlays/dev
  destination:
    server: https://kubernetes.default.svc
    namespace: dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true

---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-prod
  namespace: argocd
spec:
  source:
    repoURL: https://github.com/example/infra
    targetRevision: main
    path: overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: false  # manual prune to avoid accidents
      selfHeal: true
    syncOptions:
    - PrunePropagationPolicy=background
    syncOptions:
    - PrunePropagationPolicy=foreground
```

---

## Section 5: Large-Scale Multi-Cluster Systems

### Multi-Cluster Architecture

```
GitHub Repo (single source of truth):
├─ clusters/
│  ├─ us-east-1/
│  │  ├─ applications.yaml
│  │  └─ overlays/
│  ├─ eu-west-1/
│  │  ├─ applications.yaml
│  │  └─ overlays/
│  └─ ap-southeast-1/
│     ├─ applications.yaml
│     └─ overlays/
└─ shared/
   ├─ base/
   └─ middleware/


Argo CD Hub Cluster:
┌──────────────────────────────────────────────────┐
│  Argo CD (multi-cluster management)              │
├──────────────────────────────────────────────────┤
│                                                   │
│  ApplicationSet Controller:                       │
│  ├─ Generate Applications for each cluster       │
│  ├─ Template path & destination per cluster      │
│  └─ Sync all clusters from single git repo       │
│                                                   │
│  Status Dashboard:                                │
│  ├─ Show health across all clusters              │
│  ├─ Drift detection per cluster                  │
│  └─ Alerts if any cluster diverges               │
│                                                   │
└──────────────────────────────────────────────────┘
       │
       ├─ Cluster 1 (us-east-1)
       │  └─ Argo CD agent (lightweight)
       │
       ├─ Cluster 2 (eu-west-1)
       │  └─ Argo CD agent
       │
       └─ Cluster 3 (ap-southeast-1)
          └─ Argo CD agent


ApplicationSet to manage all clusters:

apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: myapp-multi-cluster
spec:
  generators:
  - list:
      elements:
      - cluster: us-east-1
        region: US
      - cluster: eu-west-1
        region: EU
      - cluster: ap-southeast-1
        region: AP

  template:
    metadata:
      name: myapp-{{ cluster }}
    spec:
      project: default
      source:
        repoURL: https://github.com/example/infra
        targetRevision: main
        path: clusters/{{ cluster }}
      destination:
        server: https://{{ cluster }}-k8s.example.com
        namespace: production
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
```

### GitOps PR Workflow for Production Changes

```
Developer's workflow:

1. Create feature branch
   $ git checkout -b feature/scale-app

2. Edit Kustomization overlay
   overlays/production/kustomization.yaml:
   - count: 5  (was 3)
   + count: 10

3. Create Pull Request
   $ git push origin feature/scale-app
   $ gh pr create --title "Scale app to 10 replicas"

4. Argo CD Preview Environment
   ├─ GitHub PR webhook triggers
   ├─ Argo CD creates preview app:
   │  spec:
   │    source:
   │      targetRevision: feature/scale-app
   │    destination:
   │      namespace: argocd-preview-123
   └─ Diff shows: "Replicas: 5 → 10"

5. Code Review
   ├─ Reviewer approves changes
   ├─ Checks that diff is correct
   ├─ Verifies preview env shows 10 pods

6. Merge to main
   $ gh pr merge

7. Argo CD Auto-Syncs
   ├─ Detects main branch update
   ├─ Applies to production cluster
   ├─ Status: "Syncing..."
   ├─ Waits for 10 pods to be healthy
   ├─ Status: "Synced"

8. Monitoring
   ├─ Prometheus metrics show:
      └─ Pod count: 3 → 10 over 30 seconds
   ├─ CPU usage increases
   ├─ Latency stays stable

9. Rollback (if needed)
   $ git revert <commit>
   $ git push origin main
   
   Argo CD:
   ├─ Detects revert
   ├─ Auto-syncs
   ├─ Scales down to 5 replicas
   └─ Status: "Synced"
```

---

## Section 6: Failure Scenarios & Recovery

### Incident 1: Sync Stuck in "Syncing" State

**Symptom**: Argo shows "Syncing" for 30 minutes, manual sync also hangs

**Root Cause**:
```
Cluster state:
├─ Deployment myapp: 3/10 replicas ready
├─ Pods: 2 running, 3 pending, 5 not scheduled
└─ Node pool full (no capacity for 10 pods)

Argo sync process:
├─ Apply deployment (request 10 replicas)
├─ Wait for deployment to become healthy
├─ Readiness probe: checks all 10 pods
├─ Only 3 pods can run (node capacity)
└─ Hangs waiting for remaining 7 pods

Timeline:
0min:  Argo starts sync
2min:  kubectl apply returns
5min:  Argo polls deployment status: 3/10 ready
10min: Still 3/10 ready (no more nodes)
30min: Timeout? Hangs indefinitely
```

**Recovery**:
```yaml
# Add timeout to sync policy
syncPolicy:
  syncOptions:
  - RespectIgnoreDifferences=true
  - Prune=background
  retry:
    limit: 5
    backoff:
      duration: 5s
      factor: 2
      maxDuration: 3m

# Monitor and alert
if sync.status == "Syncing" and sync.duration > 10m:
  alert("Sync stuck - investigate deployment")

# Manual recovery
$ kubectl scale deployment myapp --replicas=3  # temporary
$ # Then add nodes to cluster
$ kubectl scale deployment myapp --replicas=10

# Or use ArgoCD CLI
$ argocd app terminate-op myapp  # kill stuck sync
$ argocd app sync myapp --retry-limit 1
```

### Incident 2: Split Brain (Cluster & Git Diverged)

**Symptom**: Application shows "OutOfSync" but manual changes were made, Argo keeps reverting

**Root Cause**:
```
Timeline:
1. Git repo: replicas: 3
2. Cluster: kubectl scale → replicas: 5
3. Argo detects drift: git(3) != cluster(5)
4. Argo syncs → applies git (3)
5. Human manually: kubectl scale → 5 again
6. Argo detects drift again → syncs → 3
   (repeats infinitely)

Why humans manually scale:
├─ "I need more replicas NOW"
├─ Didn't want to wait for PR/merge
└─ Cluster is "faster" than git process
```

**Prevention**:
```yaml
# Disable manual changes via RBAC
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]  # read-only
# Remove: ["create", "update", "patch", "delete"]

---
# Force all changes through git
$ git checkout -b feature/scale
$ vim overlays/production/kustomization.yaml
$ git commit -m "Scale to 5 replicas"
$ git push

# Argo automatically syncs after merge

---
# Self-heal enabled (revert manual changes)
syncPolicy:
  automated:
    selfHeal: true  # reverts manual kubectl apply
```

### Incident 3: Rollback Failure

**Symptom**: New deployment broken, reverted commit, but cluster still broken

**Root Cause**:
```
Version timeline:
commit A: v1.0.0 (working)
commit B: v1.1.0 (broken - scaling issue)
commit C: Revert B (back to v1.0.0)

Deployment manifests:
commit B changed:
├─ Image: v1.0.0 → v1.1.0
├─ Memory limit: 512Mi → 256Mi (bug!)
└─ New environment variable: DEBUG=true

commit C (revert) should restore:
├─ Image: v1.1.0 → v1.0.0
├─ Memory limit: 256Mi → 512Mi
└─ Remove DEBUG variable

BUT:
├─ Some pods still running v1.1.0 code
├─ New pods start with correct image (v1.0.0)
├─ Mixed versions cause compatibility issues
└─ "Synced" but still broken

Actual issue:
├─ Old pods on nodes need restart
├─ Argo only updates deployment spec
├─ Pod restart doesn't happen automatically
```

**Recovery**:
```yaml
# Force pod restart via rolling update
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1  # one pod at a time
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:v1.0.0
    # Force restart by changing pod template
    metadata:
      annotations:
        restartedAt: "2024-05-20T10:30:00Z"

# OR manual restart
$ kubectl rollout restart deployment myapp
$ kubectl rollout status deployment myapp

# Verify all pods are new version
$ kubectl get pods -o wide
$ kubectl logs <pod>  # check version
```

### Incident 4: Cascade Failure Across Clusters

**Symptom**: Change to shared base causes deployment failures in 3 clusters

**Root Cause**:
```
Repo structure:
├─ base/
│  ├─ deployment.yaml
│  ├─ service.yaml
│  └─ kustomization.yaml
└─ overlays/
   ├─ dev/
   ├─ staging/
   └─ production/

Change to base/:
- service.yaml changes selector
  OLD: app: myapp
  NEW: app: myapp-prod-only

All 3 overlays use this base:
├─ dev cluster: service selector broken
├─ staging cluster: service selector broken
└─ production cluster: service selector broken

Result:
├─ Services can't find pods
├─ All clusters show OutOfSync
├─ All applications fail to sync
└─ Cascade: one mistake → 3 clusters broken
```

**Prevention**:
```yaml
# Test changes before pushing
$ kustomize build overlays/dev | kubectl apply -f - --dry-run=client

# Use a staging git branch for testing
├─ Merge to dev branch first
├─ Verify all 3 dev apps sync correctly
├─ THEN merge to main branch

# Or: PR preview environments
├─ Create preview app for each overlay
├─ Render kustomize in CI
├─ Show diff before merge

# Limit blast radius
├─ Separate repo per cluster (safer but less DRY)
├─ Immutable base versions (tag commits)
├─ Comprehensive tests on base changes
```

---

## Section 7: Kustomize & Helm Integration

### Kustomize Patches & Overlays

```yaml
# base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    spec:
      containers:
      - name: myapp
        image: myapp:latest
        resources:
          requests:
            memory: 512Mi
            cpu: 250m
          limits:
            memory: 1Gi
            cpu: 500m

---
# overlays/production/patch-replicas.yaml
- op: replace
  path: /spec/replicas
  value: 10

---
# overlays/production/patch-resources.yaml
- op: replace
  path: /spec/template/spec/containers/0/resources
  value:
    requests:
      memory: 2Gi
      cpu: 1000m
    limits:
      memory: 4Gi
      cpu: 2000m

---
# overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
bases:
- ../../base
namePrefix: prod-
commonLabels:
  environment: production
patchesJson6902:
- target:
    group: apps
    version: v1
    kind: Deployment
    name: myapp
  patch: |-
    - op: replace
      path: /spec/replicas
      value: 10
```

### Helm Integration

```yaml
# Application using helm chart from registry
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://charts.example.com
    targetRevision: "1.2.3"  # chart version
    chart: myapp
    helm:
      releaseName: myapp
      version: "1.2.3"
      values: |
        image:
          tag: "v1.2.3"
        replicaCount: 5
        resources:
          requests:
            memory: 512Mi
            cpu: 250m
      
      # Helm parameters override
      parameters:
      - name: replicaCount
        value: "10"
      - name: image.tag
        value: "v1.2.4"

  destination:
    server: https://kubernetes.default.svc
    namespace: production
    
  syncPolicy:
    automated:
      prune: true
      selfHeal: true


# Using git repo with helm values per environment
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-prod
spec:
  source:
    repoURL: https://github.com/example/infra
    targetRevision: main
    path: helm/myapp
    helm:
      releaseName: myapp
      valueFiles:
      - values.yaml
      - values-prod.yaml  # env-specific overrides
      values: |
        image:
          tag: "v1.2.3"
```

### Helm Values Composition

```
Directory structure:
helm/myapp/
├─ Chart.yaml
├─ values.yaml (defaults)
├─ values-dev.yaml
├─ values-staging.yaml
├─ values-prod.yaml
├─ templates/
│  ├─ deployment.yaml
│  ├─ service.yaml
│  └─ configmap.yaml


values.yaml:
replicaCount: 1
image:
  repository: myapp
  tag: latest
  pullPolicy: Always
resources:
  requests:
    memory: 128Mi
    cpu: 100m
  limits:
    memory: 256Mi
    cpu: 200m
env:
  LOG_LEVEL: DEBUG


values-prod.yaml:
replicaCount: 10
image:
  tag: v1.2.3  # override
  pullPolicy: IfNotPresent
resources:
  requests:
    memory: 2Gi
    cpu: 1000m
  limits:
    memory: 4Gi
    cpu: 2000m
env:
  LOG_LEVEL: INFO


Application:
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-prod
spec:
  source:
    repoURL: https://github.com/example/infra
    path: helm/myapp
    helm:
      releaseName: myapp
      valueFiles:
      - values.yaml
      - values-prod.yaml
  destination:
    namespace: production
```

---

## Section 8: Production Incidents

### Incident 1: Image Tag Immutability Issue

**Symptom**: Deployed `latest` tag, new version pushed but pods don't update

**Root Cause**:
```
Cluster has image: myapp:latest (SHA: abc123)
New build pushes myapp:latest (SHA: def456)

But:
├─ Kubernetes caches image (imagePullPolicy: IfNotPresent)
├─ Sees myapp:latest already on node
├─ Doesn't pull new version
└─ Pods still running old SHA

Argo sync:
├─ Fetches git repo
├─ Sees image: myapp:latest
├─ Compares with cluster
├─ Sees deployment.spec.image: myapp:latest
├─ Both match (same tag)
├─ No sync needed!
└─ Old code still running
```

**Prevention**:
```yaml
# Option 1: Use specific version tags
deployment.yaml:
image: myapp:v1.2.3  # Always specific version

CI/CD pushes tags:
├─ build + push image
├─ Git commit with new tag
├─ Argo syncs and sees new image
└─ Cluster pulls (imagePullPolicy: Always)

---
# Option 2: Force imagePullPolicy: Always
spec:
  containers:
  - name: myapp
    image: myapp:latest
    imagePullPolicy: Always  # Always pull, even for :latest

---
# Option 3: Use image digest
image: myapp@sha256:abc123def456...

# CI/CD updates digest instead of tag:
image: myapp@sha256:def456789abc...
```

### Incident 2: Secret Rotation Causing Crashes

**Symptom**: Secret rotated in vault, pods immediately start failing auth

**Root Cause**:
```
Timeline:
1. Old secret: DB_PASSWORD=old_secret
   Pods restart, load old_secret from env
   Connected to DB successfully

2. Admin rotates secret: DB_PASSWORD=new_secret
   Updated in Argo CD secret store

3. Argo detects git change
   Secret ConfigMap updated with new_secret

4. Pods crash:
   ├─ Environment variable still has old_secret
   ├─ New pods get new_secret
   ├─ Database rejects old_secret
   └─ Restart loop

5. Solution: force pod restart
   Rolling restart after secret rotation
```

**Prevention**:
```yaml
# Option 1: Checksum secret in deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  template:
    metadata:
      annotations:
        checksum/secret: "{{ include (print $.Template.BasePath \"/secret.yaml\") . | sha256sum }}"
    spec:
      containers:
      - name: myapp
        env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: myapp-secret
              key: db-password

# When secret changes, checksum changes
# → triggers rolling restart

---
# Option 2: ExternalSecrets operator
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "myapp"

---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: myapp-secret
spec:
  refreshInterval: 1h  # rotate every hour
  secretStoreRef:
    name: vault
    kind: SecretStore
  target:
    name: myapp-secret
    creationPolicy: Owner
  data:
  - secretKey: db-password
    remoteRef:
      key: secrets/database
      property: password

# Pod mounts secret:
spec:
  containers:
  - env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: myapp-secret
          key: db-password
  # Secret automatically rotated every hour
```

### Incident 3: Namespace Deletion Race

**Symptom**: Developer deleted namespace, ArgoCD immediately recreated it, data loss

**Root Cause**:
```
Argo Application:
syncPolicy:
  syncOptions:
  - CreateNamespace=true

Timeline:
1. kubectl delete namespace production
2. Namespace deleted, all pods gone
3. Argo reconciliation runs (every 3 min)
4. Argo sees namespace gone
5. Argo creates namespace
6. Argo applies all manifests
7. Data loss if stateful (PVCs not recreated)
```

**Prevention**:
```yaml
# Option 1: Disable automatic creation
syncPolicy:
  syncOptions:
  - CreateNamespace=false  # Manual namespace management

# Operator must manually create namespace:
$ kubectl create namespace production

---
# Option 2: Protect namespaces from deletion
apiVersion: v1
kind: Namespace
metadata:
  name: production
  finalizers:
  - kubernetes.io/pvc-protection  # Prevent accidental deletion

---
# Option 3: Disable auto-sync for critical apps
syncPolicy:
  automated:
    selfHeal: false  # Require manual sync
    prune: false

# Manual sync only:
$ argocd app sync myapp
```

---

## Section 9: Security & RBAC

### RBAC Model in Argo CD

```yaml
# Default RBAC
argocd-server:
├─ Admins: full access
├─ Users: read-only (via OIDC)
└─ Service accounts: scoped access

---
# Custom RBAC policy
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.default: role:readonly  # default role
  
  # Users via OIDC groups
  policy.csv: |
    # role definition
    p, role:admin, applications, *, */*, allow
    p, role:developer, applications, get, frontend/*, allow
    p, role:developer, applications, sync, frontend/*, allow
    p, role:deployer, applications, sync, */*, allow
    p, role:readonly, applications, get, */*, allow
    
    # Role-to-group mapping (OIDC)
    g, engineering:frontend, role:developer
    g, engineering:devops, role:deployer
    g, engineering:admin, role:admin

---
# Service account with limited permissions
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ci-deployer
  namespace: argocd

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ci-deployer
  namespace: argocd
rules:
- apiGroups: ["argoproj.io"]
  resources: ["applications"]
  verbs: ["get", "list"]
- apiGroups: ["argoproj.io"]
  resources: ["applications/sync"]
  verbs: ["create"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ci-deployer
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: ci-deployer
subjects:
- kind: ServiceAccount
  name: ci-deployer
  namespace: argocd
```

### Git Credentials & SSH Keys

```yaml
# HTTPS with Personal Access Token
apiVersion: v1
kind: Secret
metadata:
  name: github-creds
  namespace: argocd
type: Opaque
stringData:
  url: https://github.com/example/infra.git
  username: not_used
  password: ghp_xxxxxxxxxxxx  # GitHub PAT

---
# SSH with key
apiVersion: v1
kind: Secret
metadata:
  name: github-ssh
  namespace: argocd
type: Opaque
stringData:
  url: git@github.com:example/infra.git
  sshPrivateKey: |
    -----BEGIN OPENSSH PRIVATE KEY-----
    ...
    -----END OPENSSH PRIVATE KEY-----

---
# Register credentials in Argo
Repository secret referenced in Application:
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
spec:
  source:
    repoURL: git@github.com:example/infra.git  # uses SSH secret
```

### Secret Management for App Secrets

```yaml
# Option 1: Sealed Secrets
# Install sealed-secrets controller
$ kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.18.0/controller.yaml

# Encrypt secret
$ echo -n 'mysecret' | kubectl create secret generic myapp-secret --dry-run=client -o yaml | kubeseal -o yaml > secret.sealed.yaml

# Git commit sealed secret (safe!)
$ git add secret.sealed.yaml

# Argo applies sealed secret
# Controller decrypts in cluster

---
# Option 2: External Secrets
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "argocd"

---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: myapp-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault
  target:
    name: myapp-secret
  data:
  - secretKey: db-password
    remoteRef:
      key: secret/database
      property: password

# Secrets fetched from vault on-demand
```

---

## Section 10: Code Examples

### Complete Argo CD Setup

```yaml
# 1. Install Argo CD
$ kubectl create namespace argocd
$ kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

---
# 2. Application definition
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
  namespace: argocd
  finalizers:
  - resources-finalizer.argocd.argoproj.io

spec:
  project: default

  source:
    repoURL: https://github.com/example/infra
    path: apps/myapp
    targetRevision: main

    # Kustomize
    kustomize:
      namePrefix: myapp-
      commonLabels:
        app: myapp

    # OR Helm
    # helm:
    #   releaseName: myapp
    #   values: |
    #     replicas: 3

  destination:
    server: https://kubernetes.default.svc
    namespace: production

  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
    - PrunePropagationPolicy=foreground
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m

  # Health assessment
  ignoreDifferences:
  - group: apps
    kind: Deployment
    jsonPointers:
    - /spec/replicas

  info:
  - name: Documentation
    value: https://github.com/example/infra/wiki/myapp

---
# 3. ApplicationSet for multi-cluster
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: myapp-multi
  namespace: argocd
spec:
  generators:
  - list:
      elements:
      - env: dev
        server: https://dev-k8s.example.com
      - env: staging
        server: https://staging-k8s.example.com
      - env: production
        server: https://prod-k8s.example.com

  template:
    metadata:
      name: myapp-{{ env }}
      labels:
        env: {{ env }}
    spec:
      project: default
      source:
        repoURL: https://github.com/example/infra
        path: overlays/{{ env }}
        targetRevision: main
      destination:
        server: {{ server }}
        namespace: myapp
      syncPolicy:
        automated:
          prune: true
          selfHeal: true

---
# 4. Git repository secret
apiVersion: v1
kind: Secret
metadata:
  name: github-repo
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: repository
stringData:
  type: git
  url: https://github.com/example/infra
  password: ghp_xxxxxxxxxxxx  # GitHub PAT
  username: argocd-bot

---
# 5. Notification setup
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
  namespace: argocd
data:
  service.slack: |
    token: $slack-token
  template.app-deployed: |
    message: "App {{ .app.metadata.name }} deployed"
  trigger.on-deployed: |
    - when: app.status.operationState.finishedAt != ''
  subscriptions: |
    - triggers:
      - on-deployed
      recipients:
      - slack:myapp-channel
```

---

## Section 11: Comparison Tables

| Feature | Argo CD | Flux | Helm |
|---------|---------|------|------|
| **Model** | Pull-based | Pull-based | Template engine |
| **Deployment** | Kubernetes-native | Kubernetes-native | Package manager |
| **UI** | Built-in web UI | CLI-only | N/A |
| **Multi-cluster** | ApplicationSet | Flux Multi-Tenancy | External tooling |
| **CRD** | Application | Kustomization | N/A |
| **Pricing** | Free/open-source | Free/open-source | Free/open-source |
| **Learning Curve** | Medium | Steep | Low |
| **Community** | Very large | Growing | Largest |
| **Production Ready** | Yes | Yes | Yes |

---

## Section 12: Best Practices Checklist

- [ ] **Source of Truth**: All manifests in git, never kubectl apply to prod
- [ ] **PR Reviews**: Require approval before deployment
- [ ] **Diff Preview**: Show what changes before sync
- [ ] **Automated Sync**: Enable auto-sync for non-critical apps
- [ ] **Manual Sync**: Disable auto-sync for production
- [ ] **Notifications**: Alert on sync failures
- [ ] **RBAC**: Use fine-grained roles for different teams
- [ ] **Secret Management**: Use sealed-secrets or external-secrets
- [ ] **Monitoring**: Track sync success rate, duration
- [ ] **Testing**: Validate kustomize/helm renders locally before push
- [ ] **Rollback**: Keep git history clean, enable instant rollback
- [ ] **Drift Detection**: Alert when cluster diverges from git

---

## Conclusion

Argo CD enables declarative, auditable, automated deployments at any scale. Master the pull model, progressive delivery strategies, and multi-cluster architectures to build robust GitOps systems.

Key takeaways:
1. **Git is source of truth** (declarative)
2. **Pull model** (cluster pulls from git)
3. **Continuous reconciliation** (every 3 minutes)
4. **Easy rollback** (git revert)
5. **Audit trail** (git history)
6. **Scale to any cluster count** (ApplicationSet)
