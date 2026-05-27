# Infrastructure & Deployment — Architecture Blueprint

> **Status:** v0.1 — Foundational
> **Owner:** Platform Architecture Team
> **Last Updated:** 2026-05-27

---

## 1. Overview

The platform runs on Kubernetes with a service mesh (Istio), GitOps-driven deployments (ArgoCD), and a multi-environment strategy (dev/staging/prod). This blueprint covers cluster architecture, networking, database strategy, CI/CD, disaster recovery, cost optimization, and security posture.

---

## 2. Deployment Architecture

```
                             ┌──────────────────────┐
                             │   DNS / CDN           │
                             │   CloudFront / CloudFlare
                             └──────────┬───────────┘
                                        │
                                        ▼
                             ┌──────────────────────┐
                             │   Ingress Gateway     │
                             │   (Envoy / Istio)     │
                             │   TLS termination     │
                             │   Rate limiting       │
                             │   WAF                 │
                             │   OAuth2 proxy        │
                             └──────────┬───────────┘
                                        │
          ┌─────────────────────────────┼─────────────────────────────┐
          │                             │                             │
          ▼                             ▼                             ▼
 ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
 │  Knowledge Graph │      │  Simulation      │      │  Visualization   │
 │  Service         │      │  Engine          │      │  Engine          │
 │  (Go / gRPC)     │      │  (Go / WASM)     │      │  (Node / WS)     │
 ├──────────────────┤      ├──────────────────┤      ├──────────────────┤
 │  Pods: 3-10      │      │  Pods: 2-20      │      │  Pods: 3-5       │
 │  CPU: 2          │      │  CPU: 4          │      │  CPU: 1          │
 │  Mem: 4Gi        │      │  Mem: 8Gi        │      │  Mem: 2Gi        │
 │  Port: 4001      │      │  Port: 4002      │      │  Port: 4003      │
 └──────────────────┘      └──────────────────┘      └──────────────────┘
          │                         │                         │
          ▼                         ▼                         ▼
 ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
 │  AI Tutor        │      │  Content          │      │  Frontend        │
 │  Service         │      │  Pipeline         │      │  (Next.js)       │
 │  (Python / LLM)  │      │  (Node / TS)      │      │  (Node / SSR)    │
 ├──────────────────┤      ├──────────────────┤      ├──────────────────┤
 │  Pods: 3-10      │      │  Pods: 2-5       │      │  Pods: 3-10      │
 │  CPU: 8          │      │  CPU: 1          │      │  CPU: 2          │
 │  Mem: 16Gi       │      │  Mem: 2Gi        │      │  Mem: 4Gi        │
 │  GPU: optional   │      │  Port: 4005      │      │  Port: 3000      │
 │  Port: 4004      │      └──────────────────┘      └──────────────────┘
 └──────────────────┘
          │
          ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │                       DATA LAYER                                     │
 │                                                                      │
 │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐        │
 │  │ Neo4j    │  │PostgreSQL│  │  Redis   │  │  ClickHouse  │        │
 │  │ Cluster  │  │ Primary  │  │ Cluster  │  │  Cluster     │        │
 │  │ 3 nodes  │  │ + Replica│  │ 3 nodes  │  │  3 nodes     │        │
 │  ├──────────┤  ├──────────┤  ├──────────┤  ├──────────────┤        │
 │  │ CPU: 8   │  │ CPU: 4   │  │ CPU: 2   │  │ CPU: 8       │        │
 │  │ Mem: 32Gi│  │ Mem: 16Gi│  │ Mem: 8Gi │  │ Mem: 32Gi    │        │
 │  │ Disk: SSB│  │ Disk: GP3│  │ Disk: GP3│  │ Disk: GP3    │        │
 │  │ Port:7687│  │ Port:5432│  │ Port:6379│  │ Port:8123    │        │
 │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘        │
 │                                                                      │
 │  ┌──────────┐  ┌──────────┐  ┌──────────┐                           │
 │  │ Kafka    │  │ Elastic  │  │ S3 /     │                           │
 │  │ Cluster  │  │search    │  │ MinIO    │                           │
 │  │ 3 nodes  │  │ 3 nodes  │  │          │                           │
 │  ├──────────┤  ├──────────┤  ├──────────┤                           │
 │  │ CPU: 4   │  │ CPU: 4   │  │ Object   │                           │
 │  │ Mem: 8Gi │  │ Mem: 16Gi│  │ Storage  │                           │
 │  │ Disk: GP3│  │ Disk: GP3│  │          │                           │
 │  │ Port:9092│  │ Port:9200│  │          │                           │
 │  └──────────┘  └──────────┘  └──────────┘                           │
 └─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Kubernetes Cluster Architecture

### 3.1 Node Pools

```yaml
nodePools:
  - name: compute
    machineType: c6a.xlarge    # 4 vCPU, 8GB
    minSize: 3
    maxSize: 20
    spot: true
    taints: []
    labels:
      pool: compute

  - name: memory
    machineType: r6a.xlarge    # 4 vCPU, 32GB
    minSize: 3
    maxSize: 10
    spot: false
    taints:
      - key: pool
        value: memory
        effect: NoSchedule
    labels:
      pool: memory

  - name: gpu
    machineType: g6.xlarge     # 4 vCPU, 16GB, 1x T4
    minSize: 0
    maxSize: 5
    spot: false
    taints:
      - key: nvidia.com/gpu
        value: present
        effect: NoSchedule
    labels:
      pool: gpu

  - name: system
    machineType: c6a.2xlarge   # 8 vCPU, 16GB
    minSize: 3
    maxSize: 5
    spot: false
    taints:
      - key: CriticalAddonsOnly
        value: "true"
        effect: NoSchedule
    labels:
      pool: system
```

### 3.2 Pod Assignments by Pool

```
 Node Pool: compute (spot)              Node Pool: memory (on-demand)
 ┌──────────────────────────────┐       ┌──────────────────────────┐
 │  • Knowledge Graph (3-10)   │       │  • Neo4j (3)             │
 │  • Simulation Engine (2-20) │       │  • PostgreSQL (2)        │
 │  • Visualization Engine (3) │       │  • Redis (3)             │
 │  • Content Pipeline (2-5)   │       │  • ClickHouse (3)        │
 │  • Frontend (3-10)          │       │  • Elasticsearch (3)     │
 └──────────────────────────────┘       └──────────────────────────┘

 Node Pool: gpu (on-demand)            Node Pool: system (on-demand)
 ┌──────────────────────────────┐       ┌──────────────────────────┐
 │  • AI Tutor (3-10)           │       │  • Istio (3)             │
 │  • Model inference           │       │  • ArgoCD (2)            │
 └──────────────────────────────┘       │  • OTel Collector (3)    │
                                         │  • Prometheus (2)        │
                                         │  • Kafka (3)             │
                                         │  • Ingress Gateway (2)   │
                                         └──────────────────────────┘
```

---

## 4. Service Mesh (Istio)

### 4.1 Mesh Architecture

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                       ISTIO SERVICE MESH                             │
 │                                                                     │
 │  ┌──────────────────────────────────────────────────────────────┐   │
 │  │  Control Plane (istiod)                                      │   │
 │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐    │   │
 │  │  │ Pilot    │ │ Galley   │ │ Citadel  │ │ Sidecar      │    │   │
 │  │  │ (xDS)    │ │ (Config) │ │ (mTLS)   │ │ Injector     │    │   │
 │  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘    │   │
 │  └──────────────────────────────────────────────────────────────┘   │
 │                                                                     │
 │  Data Plane (Envoy proxies sidecar to every pod)                    │
 │                                                                     │
 │  Pod ┌────────────────────────────────┐                             │
 │      │  ┌──────────┐    ┌──────────┐  │                             │
 │      │  │  App     │───▶│  Envoy   │──│──▶ Service B               │
 │      │  │  Container│   │  Proxy   │  │    (mTLS)                  │
 │      │  └──────────┘    └──────────┘  │                             │
 │      └────────────────────────────────┘                             │
 │                                                                     │
 │  Traffic Flow: Pod A → Envoy A → (mTLS) → Envoy B → Pod B          │
 │                                                                     │
 │  Policies:                                                          │
 │  • mTLS: STRICT mode (all services)                                │
 │  • Authorization: per-service RBAC                                 │
 │  • Rate limiting: per-route, per-source                            │
 │  • Circuit breaking: connection pool, outlier detection            │
 │  • Retries: 2x for idempotent endpoints                            │
 │  • Timeouts: default 30s, configurable per route                   │
 └─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Istio Configuration

```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: platform
spec:
  mtls:
    mode: STRICT
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: knowledge-graph
spec:
  host: knowledge-graph.platform.svc.cluster.local
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 1000
        maxRequestsPerConnection: 10
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
    loadBalancer:
      simple: LEAST_CONN
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: platform-routes
spec:
  hosts:
    - api.platform.io
  gateways:
    - platform-gateway
  http:
    - match:
        - uri:
            prefix: /graph/
      route:
        - destination:
            host: knowledge-graph
          weight: 90
        - destination:
            host: knowledge-graph-v2
          weight: 10  # canary
---
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: platform-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
    - port:
        number: 443
        name: https
        protocol: HTTPS
      tls:
        mode: SIMPLE
        credentialName: platform-tls
      hosts:
        - api.platform.io
        - app.platform.io
```

---

## 5. Database Strategy

| Database | Use Case | Topology | Backup | Retention |
|----------|----------|----------|--------|-----------|
| **Neo4j** | Knowledge graph, relationships | 3-node core cluster, read replicas | Daily snapshot to S3 | 30 days |
| **PostgreSQL** | Catalog, users, content metadata | Primary + 2 replicas, PgBouncer | WAL archiving to S3, daily dump | 30 days + PITR |
| **Redis** | Cache, session, rate-limit | 3-node cluster with sentinel | RDB snapshot to S3 | 7 days |
| **ClickHouse** | Time-series metrics | 3-node cluster, replicated | S3 backup | 90 days |
| **Elasticsearch** | Full-text search | 3-node cluster | Snapshot to S3 | 30 days |
| **Kafka** | Event bus | 3-node KRaft cluster | Log retention 7 days | 7 days |

### 5.1 Connection Pooling

```yaml
# PgBouncer configuration
databases:
  platform:
    host: postgres-primary
    port: 5432
    dbname: platform
    auth_user: pgbouncer
    pool_size: 50
    max_db_connections: 100

pgbouncer:
  listen_addr: 0.0.0.0:5432
  pool_mode: transaction
  max_client_conn: 500
  default_pool_size: 25
  reserve_pool_size: 5
  reserve_pool_timeout: 3
  server_idle_timeout: 300
  query_timeout: 30
```

---

## 6. CI/CD Pipeline

```
 ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
 │  Git     │───▶│  Build   │───▶│  Test    │───▶│  Package │───▶│  Deploy  │
 │  Push    │    │          │    │          │    │          │    │          │
 └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
       │              │              │               │               │
       ▼              ▼              ▼               ▼               ▼
  Feature/     Go build,      Unit tests,      Docker build    ArgoCD sync
  main branch  npm build,     integration,     (distroless),   (auto/pr-based)
               lint           e2e,             Kaniko,
                              security scan    Cosign sign

 Pipeline Stages:
 1. Checkout + dependency caching
 2. Lint (golangci-lint, ESLint, Ruff)
 3. Unit tests (go test, vitest, pytest)
 4. Build (go build, tsc, webpack)
 5. Security scan (Trivy, Snyk)
 6. Container build (Kaniko, distroless)
 7. Sign image (Cosign)
 8. Generate SBOM (Syft)
 9. Push to registry (Harbor)
10. Deploy via ArgoCD (auto-sync dev, manual prod)
11. Integration test + smoke test
12. Notify (Slack, GitHub status)
```

### 6.1 GitHub Actions Workflow

```yaml
name: Build & Deploy
on:
  push:
    branches: [main, 'release/*']
  pull_request:
    branches: [main]

env:
  REGISTRY: harbor.platform.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.23'

      - name: Lint
        run: golangci-lint run --timeout=5m

      - name: Unit tests
        run: go test -race -coverprofile=coverage.out ./...

      - name: Security scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          severity: HIGH,CRITICAL
          exit-code: 1

      - name: Build container
        uses: tj-actions/kaniko@v1
        with:
          image: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tag: ${{ github.sha }}
          dockerfile: Dockerfile
          cache: true

      - name: Sign image
        uses: sigstore/cosign-installer@v3
      - run: cosign sign --key env://COSIGN_PRIVATE_KEY ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ steps.build.digest }}

      - name: Generate SBOM
        uses: anchore/syft-action@v0
        with:
          image: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

      - name: Deploy dev
        if: github.ref == 'refs/heads/main'
        run: |
          # Update image tag in Kustomize overlay
          cd platform/k8s/overlays/dev
          kustomize edit set image ${{ env.IMAGE_NAME }}:${{ github.sha }}
          git commit -am "Update image to ${{ github.sha }}"
          git push
```

---

## 7. GitOps with ArgoCD

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                      ARGOCD GITOPS FLOW                              │
 │                                                                     │
 │  ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐       │
 │  │  Dev    │───▶│  ArgoCD  │───▶│  Sync    │───▶│  Dev     │       │
 │  │  pushes │    │ detects  │    │  applies │    │  cluster │       │
 │  │  to git │    │ drift    │    │  manifests│   │  updated │       │
 │  └─────────┘    └──────────┘    └──────────┘    └──────────┘       │
 │                                                                     │
 │  ┌─────────┐    ┌──────────┐    ┌──────────┐                       │
 │  │  PR to  │───▶│  ArgoCD  │───▶│  Manual  │───▶ Staging applies │
 │  │ staging │    │ previews │    │  promote │                       │
 │  │ branch  │    │ diff     │    │          │                       │
 │  └─────────┘    └──────────┘    └──────────┘                       │
 │                                                                     │
 │  ┌─────────┐    ┌──────────┐    ┌──────────┐                       │
 │  │  PR to  │───▶│  ArgoCD  │───▶│  Manual  │───▶ Prod applies     │
 │  │  prod   │    │ previews │    │  promote │                       │
 │  │  branch │    │ diff     │    │  + rollback button              │
 │  └─────────┘    └──────────┘    └──────────┘                       │
 │                                                                     │
 │  ├── ApplicationSets: generate per-service from template            │
 │  ├── Sync waves: 0=CRDs, 1=namespaces, 2=databases, 3=apps         │
 │  ├── Automated sync: dev only                                      │
 │  └── Prune: orphans deleted                                        │
 └─────────────────────────────────────────────────────────────────────┘
```

### 7.1 ApplicationSet Template

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: platform-services
spec:
  generators:
    - list:
        elements:
          - service: knowledge-graph
            path: services/knowledge-graph
            port: 4001
          - service: simulation-engine
            path: services/simulation-engine
            port: 4002
          - service: ai-tutor
            path: services/ai-tutor
            port: 4004
  template:
    metadata:
      name: '{{service}}-{{env}}'
    spec:
      project: platform
      source:
        repoURL: https://github.com/org/platform-k8s
        targetRevision: '{{env}}'
        path: '{{path}}/overlays/{{env}}'
      destination:
        server: 'https://kubernetes.default.svc'
        namespace: 'platform-{{env}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
          - ApplyOutOfSyncOnly=true
```

---

## 8. Multi-Environment Strategy

| Environment | Purpose | Deploy Trigger | Scaling | Data |
|-------------|---------|----------------|---------|------|
| **dev** | Development, fast iteration | Auto on main push | 1 replica | Synthetic data |
| **staging** | Pre-production validation | Manual PR promote | 2-3 replicas | Anonymized copy |
| **prod** | Production | Manual PR promote + approval | 3-20 replicas | Real data |
| **review** | Per-PR preview | PR opened | 1 replica | Empty/synthetic |

### 8.1 Progressive Delivery

```yaml
# Canary release for knowledge-graph service
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: knowledge-graph
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: knowledge-graph
  service:
    port: 4001
  analysis:
    interval: 30s
    threshold: 10
    maxWeight: 50
    stepWeight: 10
    metrics:
      - name: request-success-rate
        thresholdRange:
          min: 99
        interval: 1m
      - name: p99-latency
        thresholdRange:
          max: 500
        interval: 30s
    webhooks:
      - name: smoke-test
        url: http://smoke-tester.platform.svc/run
        timeout: 30s
```

---

## 9. Disaster Recovery

### 9.1 Backup Strategy

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                    BACKUP & RESTORE MATRIX                           │
 │                                                                     │
 │  ┌──────────┬────────────┬────────────┬────────────┬────────────┐   │
 │  │ Database │ Method     │ Frequency  │ Retention  │ RPO/RTO    │   │
 │  ├──────────┼────────────┼────────────┼────────────┼────────────┤   │
 │  │ Neo4j    │ cypher dump│ Daily      │ 30 days    │ RPO: 1h    │   │
 │  │          │ + S3       │            │            │ RTO: 30m   │   │
 │  ├──────────┼────────────┼────────────┼────────────┼────────────┤   │
 │  │ Postgres │ WAL arch   │ Continuous │ PITR 7d    │ RPO: 1m    │   │
 │  │          │ + pg_dump  │ Daily dump │ 30 days    │ RTO: 15m   │   │
 │  ├──────────┼────────────┼────────────┼────────────┼────────────┤   │
 │  │ Redis    │ RDB + AOF  │ Every 6h   │ 7 days     │ RPO: 1h    │   │
 │  │          │            │            │            │ RTO: 10m   │   │
 │  ├──────────┼────────────┼────────────┼────────────┼────────────┤   │
 │  │ ClickHse │ S3 backup  │ Every 6h   │ 90 days    │ RPO: 6h    │   │
 │  │          │            │            │            │ RTO: 1h    │   │
 │  ├──────────┼────────────┼────────────┼────────────┼────────────┤   │
 │  │ S3       │ Cross-reg  │ Sync       │ Same as    │ RPO: 0     │   │
 │  │          │ replication│            │ source     │ RTO: 5m    │   │
 │  └──────────┴────────────┴────────────┴────────────┴────────────┘   │
 └─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Disaster Recovery Plan

```yaml
disaster_recovery:
  rpo: 1 hour
  rto: 15 minutes

  scenarios:
    pod_failure:
      action: Kubernetes auto-restart (kubelet)
      rto: < 30s

    node_failure:
      action: Cluster autoscaler replaces node
      rto: < 5m

    zone_failure:
      action: Pods on remaining zones (anti-affinity)
      rto: < 2m
      note: "Multi-AZ deployment"

    region_failure:
      action: |
        1. Route53 failover to secondary region
        2. ArgoCD sync to secondary cluster
        3. Promote database replicas in secondary
        4. Verify health checks
        5. Update DNS
      rto: < 15m
      rpo: < 1h

    database_corruption:
      action: |
        1. Identify corruption point (PITR)
        2. Restore from WAL archive to pre-corruption time
        3. Verify data integrity
        4. Redirect traffic to restored instance
      rto: < 30m
      rpo: < 1m
```

---

## 10. Cost Optimization

| Strategy | Impact | Implementation |
|----------|--------|----------------|
| **Spot instances** | 60-80% savings on compute | Karpenter spot pool for stateless workloads |
| **Right-sizing** | 20-40% savings | VPA recommendations, period review |
| **Cluster autoscaler** | Eliminate idle capacity | Karpenter binpacking, scale-to-zero |
| **Reserved instances** | 30-50% savings on DB | 1-year commitment for stateful workloads |
| **Object storage** | Tiered storage lifecycle | S3 Standard → Infrequent Access → Glacier |
| **Image optimization** | Reduced storage cost | Distroless base images, multi-stage builds |
| **Caching** | Reduced compute load | Redis caching, CDN for static assets |

### 10.1 Karpenter Configuration

```yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: spot-compute
spec:
  template:
    spec:
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot"]
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
        - key: karpenter.k8s.aws/instance-family
          operator: In
          values: ["c6a", "c7a", "m6a"]
      nodeClassRef:
        name: default
  limits:
    cpu: 200
    memory: 400Gi
  disruption:
    consolidationPolicy: WhenUnderutilized
    expireAfter: 720h  # 30 days
```

---

## 11. Security

### 11.1 Pod Security Standards

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: platform
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
---
# Network policy: deny all ingress by default
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: platform
spec:
  podSelector: {}
  policyTypes:
    - Ingress
---
# Allow only from Istio gateway
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-ingress-gateway
  namespace: platform
spec:
  podSelector:
    matchLabels:
      app: knowledge-graph
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              istio.io/dataplane-mode: ambient
      ports:
        - port: 4001
```

### 11.2 Secrets Management (Vault)

```yaml
# Vault configuration for Kubernetes
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: platform-secrets
spec:
  provider: vault
  parameters:
    vaultAddress: https://vault.platform.io:8200
    roleName: platform
    objects: |
      - objectName: neo4j-password
        secretPath: secret/data/platform/neo4j
        secretKey: password
      - objectName: openai-api-key
        secretPath: secret/data/platform/ai
        secretKey: openai-api-key
      - objectName: postgres-connection-string
        secretPath: secret/data/platform/postgres
        secretKey: connection-string
```

### 11.3 Supply Chain Security

```bash
# Image signing with Cosign
cosign sign --key cosign.key \
  harbor.platform.io/platform/knowledge-graph:abc123

# Verify before deployment
cosign verify --key cosign.pub \
  harbor.platform.io/platform/knowledge-graph:abc123

# SBOM generation with Syft
syft harbor.platform.io/platform/knowledge-graph:abc123 \
  -o spdx-json > sbom.json

# Vulnerability scan with Trivy
trivy image --severity HIGH,CRITICAL \
  harbor.platform.io/platform/knowledge-graph:abc123
```

### 11.4 Runtime Security (Falco)

```yaml
apiVersion: falco.org/v1alpha1
kind: FalcoRule
metadata:
  name: platform-runtime-security
spec:
  rules:
    # Sensitive file access
    - rule: Read sensitive file
      desc: Detect read access to sensitive files
      condition: >
        open_read and
        (fd.name startswith /etc/kubernetes or
         fd.name startswith /var/run/secrets)
      output: "Sensitive file read (user=%user.name command=%proc.cmdline file=%fd.name)"
      priority: NOTICE

    # Unauthorized shell
    - rule: Shell spawned in container
      desc: Detect interactive shell in container
      condition: >
        spawned_process and
        proc.name in (bash, sh, zsh, dash) and
        not k8s.ns.name in (platform-system)
      output: "Shell spawned (%user.name %proc.cmdline)"
      priority: WARNING
```

---

## 12. Observability Infrastructure

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                   OBSERVABILITY STACK ON K8S                         │
 │                                                                     │
 │  ┌──────────────────┐    ┌──────────────────┐                       │
 │  │  Prometheus      │    │  Grafana         │                       │
 │  │  (kube-prometheus│    │  (dashboards,     │                       │
 │  │   -stack)        │    │   alerting)       │                       │
 │  │  PV: 100Gi       │    │  PV: 10Gi        │                       │
 │  └──────────────────┘    └──────────────────┘                       │
 │                                                                     │
 │  ┌──────────────────┐    ┌──────────────────┐                       │
 │  │  Loki            │    │  Tempo           │                       │
 │  │  (logs)          │    │  (traces)        │                       │
 │  │  PV: 500Gi       │    │  PV: 200Gi       │                       │
 │  │  S3 backend      │    │  S3 backend      │                       │
 │  └──────────────────┘    └──────────────────┘                       │
 │                                                                     │
 │  ┌──────────────────┐    ┌──────────────────┐                       │
 │  │  Pyroscope       │    │  Mimir           │                       │
 │  │  (profiling)     │    │  (long-term      │                       │
 │  │  S3 backend      │    │   metrics)        │                       │
 │  └──────────────────┘    │  S3 backend      │                       │
 │                          └──────────────────┘                       │
 │                                                                     │
 │  Collectors:                                                        │
 │  ┌──────────────────┐    ┌──────────────────┐                       │
 │  │  OTel Collector  │    │  kube-state-     │                       │
 │  │  (daemonset)     │    │  metrics         │                       │
 │  └──────────────────┘    └──────────────────┘                       │
 │  ┌──────────────────┐    ┌──────────────────┐                       │
 │  │  Node Exporter   │    │  cAdvisor        │                       │
 │  │  (daemonset)     │    │  (daemonset)      │                       │
 │  └──────────────────┘    └──────────────────┘                       │
 └─────────────────────────────────────────────────────────────────────┘
```

---

## 13. Container Strategy

### 13.1 Dockerfile (Distroless)

```dockerfile
# Build stage
FROM golang:1.23-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/server ./cmd/server

# Runtime stage
FROM gcr.io/distroless/static-debian12:nonroot
WORKDIR /
COPY --from=builder /app/server /server
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
USER nonroot:nonroot
EXPOSE 4001
ENTRYPOINT ["/server"]
```

### 13.2 Image Size Budget

| Service | Base Image | Size Target |
|---------|-----------|-------------|
| Knowledge Graph | distroless/static | < 20MB |
| Simulation Engine | distroless/static | < 25MB |
| AI Tutor | distroless/python3 | < 100MB |
| Frontend | nginx:alpine | < 50MB |
| Content Pipeline | distroless/node | < 80MB |
