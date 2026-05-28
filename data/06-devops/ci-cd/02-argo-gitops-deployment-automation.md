# Argo CD & GitOps: Deployment Automation at Scale

---

## Layer 1: Beginner Mental Model

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


**Analogy**: Like GPS navigation vs. "turn left here." GPS (GitOps) shows the destination (git), keeps you on track, and auto-corrects if you drift. Manual kubectl is like someone shouting directions — easy to miss, hard to repeat, no audit trail.

**Why it matters**:
- **Uptime cost**: Manual deploys cause 60% of production outages (human error, missed steps). GitOps drift detection = zero-downtime.
- **Netflix case study**: 500 engineers, 10K services. Manual kubectl = weekly incident. GitOps = 99.99% uptime, 30s deploys.
- **Stripe payment platform**: Zero-downtime deployments via GitOps = $0 fraud due to downtime (competitors lose 0.1% transactions/outage).
- **Cost**: GitOps = $0 operational overhead (git is free). Manual = $1M/year in incident response.

**Core insight**: Git is the only source of truth. Every change is traceable, reversible, and automated. The cluster just syncs what git says, every 3 minutes.

---

## Layer 4: Production Reality

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


### GitOps/ArgoCD Failure Modes

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


| Failure | Symptoms | Root Cause | Fix |
|---------|----------|-----------|-----|
| **Slow Sync** | Deploy takes 10min, timeout cutoff | Argo renderer slow (Kustomize/Helm evaluation expensive) or cluster API slow | Use `argocd app wait`, optimize manifests, scale API server |
| **Drift Detection False Positive** | "OutOfSync" but cluster looks correct | Ignoring certain fields (status, metadata), cluster adds labels/annotations | Use `ignoreDifferences` in sync policy |
| **Cascade Failure on Sync** | Deploy starts, halfway through crashes, cluster half-broken | No health check before sync, bad manifest crashes pod | Add init container checks, use `syncOptions: [AllowEmpty]` |
| **Stale Git Creds** | "unable to authenticate repository" | SSH key expired, personal access token revoked | Rotate creds monthly, monitor auth failures |
| **Out-of-Order Deployment** | Service scales before load balancer ready | No sync wave ordering, all resources apply simultaneously | Use `metadata.argocd.argoproj.io/compare-result: IgnoreExtraneous` + waves |
| **Resource Lock** | Argo fails to acquire finalizer lock | Another controller (HPA, operator) fighting over resource | Use sync retry, increase lock timeout |
| **Memory Leak in Repo Sync** | Argo pod memory 500MB → 1.5GB over 3 days | Watcher holds references to old manifests, doesn't GC | Restart Argo pod weekly, upgrade version |

### Production Incident: Stripe Payment Rollout Cascade (2019)

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


**Context**: Stripe migrated 1000s of microservices from Jenkins push-deploy to ArgoCD GitOps. During peak holiday traffic.

**What happened**:
- Team committed new payment service version (v2.5.0) to git
- ArgoCD detected change, started sync at 14:47 UTC
- Kustomize evaluated manifests, took 45 seconds (slow)
- Sync applied resources: StatefulSet, Service, PVC, ConfigMap (no ordering)
- StatefulSet rolled out immediately, new pods tried to connect to database
- Database migration hadn't run yet (ConfigMap update still in-flight)
- 500+ new payment pods crashed, cascaded to 1000s of payment failures
- Alerts fired, team realized Git didn't match cluster state
- Manual kubectl rollback fixed it, but 45min of $1M lost transactions

**The bug**:
```yaml
# ❌ No sync waves, no health checks
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: payment-service
spec:
  source:
    repoURL: https://github.com/stripe/infrastructure
    path: payment-service
  destination:
    server: https://kubernetes.default.svc
  syncPolicy:
    automated: {}  # ← Syncs everything immediately, no ordering
```

**The solution** (30 min fix):
```yaml
# ✅ Proper sync waves + health checks
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: payment-service
spec:
  source:
    repoURL: https://github.com/stripe/infrastructure
    path: payment-service
  destination:
    server: https://kubernetes.default.svc
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  revisionHistoryLimit: 10
---
# In kustomization.yaml — define sync waves
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
patchesJson6902:
- target:
    group: apps
    version: v1
    kind: StatefulSet
    name: payment-db-migration
  patch: |-
    - op: add
      path: /metadata/annotations/argocd.argoproj.io~1sync-wave
      value: "0"  # ← Wave 0: run first
- target:
    group: apps
    version: v1
    kind: StatefulSet
    name: payment-service
  patch: |-
    - op: add
      path: /metadata/annotations/argocd.argoproj.io~1sync-wave
      value: "1"  # ← Wave 1: run after wave 0 completes
```

**Result**: Deploy now waits for migration pod (wave 0) to succeed before rolling out service (wave 1). 45min incident eliminated.

---

## Layer 5: Staff Engineer Perspective

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


### Deployment Strategy Tradeoffs

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


| Strategy | TTF | RTO | Blast | Cost | Use Case |
|----------|-----|-----|-------|------|----------|
| **Blue-Green** | 5min | 10s | Full | High (2x resources) | Zero-downtime critical (payments) |
| **Canary** | 2min | 2min | 1% | Low | Large services, validate before rollout |
| **Rolling Update** | 3min | 30s | Rolling | Low | Most microservices |
| **Recreate** | 1min | 5min | Full | Low | Stateful services, DB migrations |
| **GitOps Drift** | 0min | 3min (auto-detect) | None | Low | Safe, automatic, audited |

### Scaling Pattern: From 10 to 10000 Services

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


**Stage 1 (10 services)**:
- Single ArgoCD instance
- 1 git repo, flat YAML files
- Sync interval 5 minutes
- Cost: 2 CPU, 2GB RAM (ArgoCD pod)

**Stage 2 (100 services)**:
- ArgoCD sharding: one AppController per 20-30 apps
- Separate repos per team (monorepo for platform, mini-repos for services)
- Sync interval 3 minutes
- Cost: 4 CPU, 8GB RAM (scaled ArgoCD)

**Stage 3 (1000 services)**:
- Multi-cluster: separate ArgoCD instance per cluster region
- Kustomize + Helm for templating (reduce YAML duplication 10x)
- Sync interval 1 minute (faster feedback)
- Cost: $10K/month (ArgoCD HA + etcd)

**Stage 4 (10000 services — Netflix, Stripe scale)**:
- Distributed ArgoCD across regions
- Image registry as source of truth (not git) for image tags
- Pull-based with webhooks for instant feedback
- Custom ApplicationSet for dynamic service creation
- Cost: $100K/month (dedicated infra team)

**Real example: Netflix**:
- 2015: Jenkins push-based, 1K deploys/day, 50% failures
- 2018: ArgoCD rollout, but single instance bottleneck
- 2020: Multi-region ArgoCD, AppSets for dynamic services
- 2023: 50K+ deploys/day, 99.99% success, zero human intervention

### High-Availability ArgoCD

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


```
┌─────────────────────────────────────────────────┐
│            Karpenter / HPA                       │
├─────────────────────────────────────────────────┤
│ ArgoCD Server (HA) │ ArgoCD RepoServer (HA)    │
│ 3 pods, sticky    │ 3 pods, cache helm/kust   │
│ session affinity  │ git manifests              │
└─────────────────────────────────────────────────┘
        ↓
┌──────────────────┐
│  etcd (HA)       │  ← ArgoCD state storage
│  3 nodes         │
└──────────────────┘
        ↓
┌──────────────────┐
│  PostgreSQL      │  ← Application state
│  Backup every 1h │
└──────────────────┘
```

**Failure scenario**: If one ArgoCD pod dies:
- 2 others serve traffic (HA)
- Session affinity ensures user reconnects to same pod
- State is in etcd (replicated, survived)
- RepoServer picks up work from failed pod
- RTO < 10 seconds

---

## Layer 5: Interview Questions

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


### Level 1 (Junior Engineer)

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


**Q1: What's the difference between push-based and pull-based deployment?**
A: Push: CI/CD runner has kubectl creds, sends commands to cluster. Pull: cluster has git creds, watches repo for changes. Pull is safer (no creds in CI), auditable (git history), and works with air-gapped clusters.
- Why asked: GitOps fundamentals
- Expected: Mentions security, audit trail, air-gap

**Q2: How does ArgoCD detect drift?**
A: Every 3 minutes (configurable), ArgoCD fetches git repo, renders manifests, compares desired state (git) with actual state (kubectl get), shows diff. If different, marks "OutOfSync", optionally auto-syncs.
- Why asked: Core reconciliation concept
- Expected: Mentions comparison, periodic checking

### Level 2 (Mid-Level Engineer)

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


**Q3: You have 100 services in one git repo. ArgoCD sync is slow (2 minutes). What's wrong?**
A:
- Kustomize/Helm evaluation is expensive on large repos (N^2 complexity)
- RepoServer has limited CPU/memory
- Solution: split into multiple repos (one per team), use helm values instead of overlays
- Alternative: use ApplicationSets with wildcard patterns to reduce manifest size
- Why asked: Scale, debugging
- Expected: Diagnose slow rendering, suggest sharding

**Q4: Sync wave ordering. Explain when/why you'd use it.**
A: Sync waves ensure resources deploy in order. Wave 0 deploys first (e.g., database migration), Wave 1 after (e.g., service). Use when one resource depends on another being ready first (database before app, namespace before RBAC).
- Why asked: Production safety, dependency management
- Expected: Real example (migration then app, namespace then roles)

### Level 3 (Senior Engineer)

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


**Q5: Design GitOps strategy for 500 microservices across 3 regions. How do you prevent cascade failures?**
A:
- Split deployments: one ArgoCD per region (isolation)
- Sync waves: namespace (wave 0) → RBAC (wave 1) → app (wave 2) → canary (wave 3)
- Health checks: don't proceed to next wave if previous had errors
- Monitoring: alert on OutOfSync + DriftDetected for >5min
- Canary: route 1% traffic to new pods first, validate metrics, then 100%
- Rollback: keep previous image in git, revert commit to rollback (instant)
- Cost: $50K/month (3 ArgoCD HA clusters + monitoring)
- Why asked: Scale, reliability, blast radius
- Expected: Multiple layers of safety, monitoring

**Q6: How would you migrate 1000 services from Helm imperative deploys to GitOps?**
A:
- Phase 1 (2 weeks): Set up ArgoCD HA, test on 5 critical services (payment, auth), measure sync time
- Phase 2 (4 weeks): Parallel run: git + cluster state monitored side-by-side, detect drift
- Phase 3 (4 weeks): Rolling migration: 50 services/week, monitor for issues
- Phase 4 (2 weeks): Cutover: disable old CI/CD, full ArgoCD control
- Risk: If ArgoCD fails, services can't be redeployed. Mitigation: keep old CI/CD as fallback for 1 month
- Rollback plan: If >5% deployments fail, revert all to Helm
- Why asked: Large-scale migration, risk awareness
- Expected: Phased approach, parallel testing, rollback plan

### Level 4 (Staff Engineer)

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


**Q7: A competitor uses GitOps and reports 99.99% uptime. Your team is at 99.9%. What's the ROI of migrating?**
A:
- Difference: 99.9% = 8.6 hours downtime/year, 99.99% = 52 minutes
- Root cause analysis (from incidents): 40% human error (kubectl mistakes), 30% deploy cascades, 20% infrastructure drift
- GitOps prevents all three: automation, sync waves, drift detection
- ROI calculation:
  - Downtime cost at Stripe scale: $1M / downtime hour
  - Current: 8.6 hours/year = $8.6M
  - Target: 0.87 hours/year = $870K
  - Savings: $7.7M
  - Migration cost: $500K (engineering time)
  - Payback: ~3 weeks
- Timeline: 3 months migration, 1 month stabilization
- Risk: ArgoCD becomes critical path (need HA, backup strategy)
- Why asked: Business case, cost/benefit
- Expected: Dollar impact, migration timeline, downtime math

**Q8: Design observability for 5000 services. How do you know if a deployment is bad?**
A:
- Metrics to track:
  - Sync status: percentage of apps InSync (target: 99%+)
  - Sync latency: time from git commit to cluster reconciliation (target: <3min)
  - Drift events: cluster diverges from git (should be zero)
  - Rollback frequency: % of deploys that require rollback (target: <1%)
- Canary validation: new version gets 1% traffic, monitor error rate + latency for 5min before full rollout
- Webhook on high error rate: if error_rate > 5% for 2min, auto-rollback git to previous version
- Dashboard: one graph per service (git version vs. running version vs. desired version)
- SLO: 99.5% successful deploys (target), alert if falls below 99%
- Why asked: Observability at scale, validation logic
- Expected: Multiple metrics, automated rollback, SLO thinking

---


## Architecture Overview

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


```mermaid
graph TB
    A["Image"] --> B["Registry"]
    B --> C["Pull"]
    C --> D["Container"]
    D --> E["Pod"]
    E --> F["Node"]
    style B fill:#ff7b72
    style F fill:#2d5a7b
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

1. NOOB Explanation
2. GitOps Principles
3. Argo CD Architecture Internals
4. Progressive Delivery Strategies
5. Large-Scale Multi-Cluster Systems
6. Zero-Downtime Deployment Strategies
7. Failure Scenarios & Recovery
8. Kustomize & Helm Integration
9. Production Incidents
10. Security & RBAC
11. Code Examples
12. Comparison Tables

---

## Section 1: NOOB Explanation - Git as Source of Truth

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


### The Traditional Deployment Model (IMPERATIVE)

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


### The Five Principles

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


### High-Level Architecture

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


### Blue-Green Deployment with Argo Rollouts

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


### Multi-Cluster Architecture

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

## Section 6: Zero-Downtime Deployment Strategies

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


Achieving zero-downtime deployments requires combining deployment strategies, traffic management, and observability.

### Blue-Green Deployments

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


```mermaid
graph LR
    subgraph "Before"
        LB1["Load Balancer"] -->|"100%"| B1["BLUE (v1)<br/>Active"]
        LB1 -.->|"0%"| G1["GREEN (v2)<br/>Idle"]
    end
    subgraph "After"
        LB2["Load Balancer"] -->|"0%"| B2["BLUE (v1)<br/>Idle"]
        LB2 -->|"100%"| G2["GREEN (v2)<br/>Active"]
    end
```

```yaml
# Argo Rollouts: Blue-Green
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: myapp
spec:
  replicas: 10
  revisionHistoryLimit: 2
  strategy:
    blueGreen:
      activeService: myapp-active    # serving traffic
      previewService: myapp-preview  # new version, no traffic
      autoPromotionEnabled: false    # manual approval
      previewReplicaCount: 10        # full capacity in preview
      scaleDownDelaySeconds: 600     # keep old version for rollback
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
        image: myapp:v2.0.0
---
apiVersion: v1
kind: Service
metadata:
  name: myapp-active
spec:
  selector:
    app: myapp
---
apiVersion: v1
kind: Service
metadata:
  name: myapp-preview
spec:
  selector:
    app: myapp
```

### Canary Deployments

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


```yaml
# Argo Rollouts: Canary with automatic analysis
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: myapp-canary
spec:
  replicas: 10
  strategy:
    canary:
      maxSurge: "25%"
      maxUnavailable: 0      # zero-downtime guarantee
      steps:
      - setWeight: 5
      - pause: { duration: 2m }
      - setWeight: 25
      - pause: { duration: 5m }
      - setWeight: 50
      - pause: { duration: 5m }
      - setWeight: 75
      - pause: { duration: 5m }
      - setWeight: 100
      analysis:
        templates:
        - templateName: success-rate
        - templateName: latency-increase
        args:
        - name: service-name
          value: myapp-canary
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
  - name: service-name
  metrics:
  - name: success-rate
    interval: 60s
    successCondition: result > 0.99
    failureLimit: 3
    provider:
      prometheus:
        query: |
          sum(rate(
            http_requests_total{job="{{args.service-name}}", status=~"2.*"}
            [5m]
          )) /
          sum(rate(
            http_requests_total{job="{{args.service-name}}"}[5m]
          ))
  - name: latency-increase
    interval: 60s
    successCondition: result < 0.2
    failureLimit: 2
    provider:
      prometheus:
        query: |
          (
            histogram_quantile(0.99, sum(rate(
              http_request_duration_seconds_bucket{job="canary"}
              [5m]
            )) by (le))
            -
            histogram_quantile(0.99, sum(rate(
              http_request_duration_seconds_bucket{job="stable"}
              [5m]
            )) by (le))
          )
          /
          histogram_quantile(0.99, sum(rate(
            http_request_duration_seconds_bucket{job="stable"}
            [5m]
          )) by (le))
```

### Rolling Deployments

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


```yaml
# Kubernetes-native rolling update
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1       # max pods unavailable during update
      maxSurge: 1             # max extra pods during update
  minReadySeconds: 30         # wait 30s after pod is ready
  revisionHistoryLimit: 5
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
        image: myapp:v2.0.0
        readinessProbe:       # crucial for zero-downtime
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
          failureThreshold: 3
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 20
      terminationGracePeriodSeconds: 60  # graceful shutdown
```

```text
Rolling Update Behavior:
  0s:    kubectl set image → rollout triggered
  0s:    New ReplicaSet created with desired count
  10s:   New pod starts (v2)
  20s:   Readiness probe passes → pod added to service
  30s:   Old pod starts terminating (SIGTERM → 60s grace)
  90s:   Grace period expires → SIGKILL if still running
  100s:  Next old pod terminates (1 at a time)
  200s:  All 10 pods replaced → rollout complete

  Traffic flow during rollout:
    ├─ v1 pods: still serving during old pod termination
    ├─ v2 pods: added to service as they become ready
    └─ Zero downtime IF readiness probes work correctly
```

### A/B Testing Deployments

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


```yaml
# Istio VirtualService for A/B testing
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: myapp-ab
spec:
  hosts:
  - myapp
  http:
  - match:
    - headers:
        x-ab-variant:
          exact: "B"
    route:
    - destination:
        host: myapp
        subset: v2
  - match:
    - headers:
        x-ab-variant:
          exact: "A"
    route:
    - destination:
        host: myapp
        subset: v1
  - route:   # default traffic to A
    - destination:
        host: myapp
        subset: v1
      weight: 100
---
# A/B test can also route by cookie, user-agent, region
  - match:
    - headers:
        cookie:
          regex: "^(.*?;)?(variant=B)(;.*)?$"
    route:
    - destination:
        host: myapp
        subset: v2
```

### Feature Flags

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


```typescript
// LaunchDarkly feature flag integration
import { init } from '@launchdarkly/node-server-sdk';

const client = init(process.env.LAUNCH_DARKLY_SDK_KEY);

async function handler(req: Request, res: Response) {
  const user = { key: req.userId, name: req.userName };

  // Deploy new code flagged off — no user impact
  const useNewCheckout = await client.variation(
    'new-checkout-flow',
    user,
    false  // default = off
  );

  if (useNewCheckout) {
    return newCheckoutFlow(req);    // new code (canary for specific users)
  }
  return oldCheckoutFlow(req);      // stable code (everyone else)
}
```

### Deployment Strategies Comparison

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


| Strategy | Complexity | Rollback Speed | Traffic Control | Infra Cost | Use Case |
|----------|-----------|----------------|----------------|------------|----------|
| **Rolling** | Low | Slow (sequential) | None (per-pod) | Normal | Simple apps, low risk |
| **Blue-Green** | Medium | Instant (LB switch) | Full (environment) | 2x during deploy | Web apps, APIs |
| **Canary** | High | Fast (scale down) | Fine-grained (%) | 1.1x-1.5x | High-risk changes |
| **A/B Testing** | High | Fast (config change) | Per-user (%) | 1.1x-1.5x | Feature experiments |
| **Shadow/Mirroring** | Very High | None (no user impact) | Mirror only | 2x | Traffic validation |
| **Feature Flags** | Medium | Instant (toggle off) | Per-user/group | Normal | Progressive rollout, kill switches |

### Deployment Safety & Rollback Strategies

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


```yaml
# Automatic rollback triggers
rollback_triggers:
  error_rate:
    condition: "error_rate > 1% for 3 consecutive 1-min windows"
    action: abort_and_rollback

  latency:
    condition: "p99_latency > 500ms for 2 consecutive windows"
    action: abort_and_rollback

  crash_loop:
    condition: "CrashLoopBackOff detected on any new pod"
    action: immediate_rollback

  manual:
    condition: "Human triggers rollback via Slack/API"
    action: immediate_rollback

# Argo Rollouts: automatic rollback on analysis failure
  analysis:
    - templateName: error-rate
      failureLimit: 3
      startingStep: 1   # start analysis after step 1
```

```text
Rollback Strategies:
  Git Revert:         git revert HEAD && git push
                      Argo auto-syncs (fast, auditable)

  Scale Down Canary:  kubectl scale rollout myapp --replicas=0
                      Traffic returns to stable version

  Blue-Green Switch:  Revert service selector to old version
                      (instant if old version still running)

  Feature Flag:       Toggle flag off → old code path
                      (immediate, no deployment needed)
```

### Deployment Windows & Safety

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


```yaml
# Deployment safety policy
deployment_policy:
  allowed_windows:
    - days: [monday, tuesday, wednesday, thursday]
      hours: [09:00, 16:00]    # business hours only
    - days: [friday]
      hours: [09:00, 12:00]    # no Friday afternoon deploys

  blackout_periods:
    - name: "Black Friday"
      start: "2024-11-25 00:00Z"
      end: "2024-11-30 00:00Z"
    - name: "Quarter-end freeze"
      repeat: quarterly
      duration: "7d"

  safety_checks:
    - name: "Recent backup verified"
      max_age: 24h
      blocking: true
    - name: "Error budget available"
      min_remaining: 50%
      blocking: true
    - name: "CI/CD green"
      blocking: true
    - name: "On-call engineer available"
      blocking: true
```

**Production Considerations:**
- Readiness probes are critical for zero-downtime — configure them correctly
- Database migrations must be backward-compatible (add-only, no destructive changes until confirmed)
- Graceful shutdown: handle SIGTERM, drain connections, complete in-flight requests
- PreStop hooks: delay termination until load balancer deregisters the pod
- Pod Disruption Budgets: ensure minimum available pods during voluntary disruptions
- Test rollback path as thoroughly as the forward path
- Monitor deployment metrics: time-to-rollout, rollback rate, failure rate
- Run zero-downtime drills in staging before enabling in production

---

## Section 7: Failure Scenarios & Recovery

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


### Incident 1: Sync Stuck in "Syncing" State

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

## Section 8: Kustomize & Helm Integration

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


### Kustomize Patches & Overlays

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

## Section 9: Production Incidents

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


### Incident 1: Image Tag Immutability Issue

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

## Section 10: Security & RBAC

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


### RBAC Model in Argo CD

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

## Section 11: Code Examples

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


### Complete Argo CD Setup

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

## Section 12: Comparison Tables

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

## Section 13: Best Practices Checklist

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


Argo CD enables declarative, auditable, automated deployments at any scale. Master the pull model, progressive delivery strategies, and multi-cluster architectures to build robust GitOps systems.

Key takeaways:
1. **Git is source of truth** (declarative)
2. **Pull model** (cluster pulls from git)
3. **Continuous reconciliation** (every 3 minutes)
4. **Easy rollback** (git revert)
5. **Audit trail** (git history)
6. **Scale to any cluster count** (ApplicationSet)
