# 🐳 ECS Deployment & Operations — Complete Deep Dive

## Table of Contents
- [Service Auto-Scaling](#service-auto-scaling)
- [Rolling vs Blue/Green vs Canary](#rolling-vs-bluegreen-vs-canary)
- [Circuit Breaker](#circuit-breaker)
- [Task Networking (awsvpc/bridge/host)](#task-networking-awsvpcbridgehost)
- [Cloud Map Service Discovery](#cloud-map-service-discovery)
- [App Mesh](#app-mesh)
- [ECS Exec](#ecs-exec)
- [ECS Anywhere](#ecs-anywhere)
- [Capacity Providers](#capacity-providers)
- [Task Placement](#task-placement)
- [GPU & Windows Support](#gpu--windows-support)
- [Fargate Spot](#fargate-spot)
- [EFS for Stateful Workloads](#efs-for-stateful-workloads)
- [EventBridge Scheduling](#eventbridge-scheduling)
- [Container Insights](#container-insights)
- [Simplest Mental Model](#simplest-mental-model)

---

## Service Auto-Scaling

Three strategies for ECS services:

```text
Target Tracking (recommended):
  Target CPU at 70%. ECS adjusts desired count.
  Simple, effective.

Step Scaling:
  CPU > 80% → +2 tasks | CPU > 60% → +1 task
  CPU < 30% → -1 task  | CPU < 10% → -2 tasks
  More control, more config.

Scheduled Scaling:
  09:00 → desired=10 (business hours)
  18:00 → desired=3  (after hours)
  Predictable patterns.
```

```awscli
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/my-cluster/my-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 --max-capacity 20

aws application-autoscaling put-scaling-policy \
  --policy-name cpu-target-tracking \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration \
    TargetValue=70.0,\
    PredefinedMetricSpecification={PredefinedMetricType=ECSServiceAverageCPUUtilization}
```

---

## Rolling vs Blue/Green vs Canary

```text
Rolling Update:
  v2 │ v2 │ v1 │ v1 │ v1  (oldest → new)
  Min healthy = 50%, Max = 200%

Blue/Green (CodeDeploy):
  Blue (v1, 100% traffic) | Green (v2, 0% traffic)
  Validate → shift 100% → instant rollback

Canary (CodeDeploy):
  v1: 90% ───┐
  v2: 10% ───┤ Monitor → shift 100%
```

| Aspect | Rolling | Blue/Green | Canary |
|--------|---------|-----------|--------|
| Speed | Fast | Medium | Slow |
| Risk | Medium (overlap) | Low | Lowest |
| Rollback | Redeploy old | Instant flip | Instant flip |
| Cost | Normal | 2x during deploy | 2x during deploy |
| Setup | Built-in ECS | CodeDeploy | CodeDeploy |

---

## Circuit Breaker

```text
Deploy → replace tasks → monitor health checks
    ↓              ↓
Continue       X consecutive failures
Healthy        Rollback to previous task def
```

`deploymentCircuitBreaker.enable = true`, `deploymentCircuitBreaker.rollback = true`. Timeout reached without steady state → rollback.

---

## Task Networking

```text
awsvpc: Each task gets ENI + VPC IP. Works with ALB/NLB.
  Required for Fargate. Best for EC2.

bridge: docker0 bridge, port mapping. Container not VPC-reachable.
  EC2 only.

host: Container port = host port. No isolation. EC2 only.
```

| Mode | Fargate | EC2 | ENI per task | DNS |
|------|---------|-----|-------------|-----|
| awsvpc | ✅ Required | ✅ | ✅ | ✅ |
| bridge | ❌ | ✅ | ❌ | ❌ |
| host | ❌ | ✅ | ❌ | ❌ |

---

## Cloud Map Service Discovery

Tasks auto-register as DNS A/SRV records. Clients resolve `order-api.internal.example.local` to task IPs. Only healthy tasks appear (TTL + health checks).

---

## App Mesh

Service mesh for ECS/EKS. Envoy sidecars handle mTLS, tracing, retries, circuit breaking, traffic shifting (canary). Control plane configures VirtualNode/VirtualRouter/VirtualService.

---

## ECS Exec

Shell access to running containers — no SSH needed.

```awscli
aws ecs execute-command --cluster my-cluster --task abc123def \
  --container app --command "/bin/bash" --interactive
```

Flow: CLI → SSM → ECS Agent → Container. **Requirements**: `enableExecuteCommand=true`, SSM agent, IAM policy `ecs:ExecuteCommand`. Logged to CloudWatch + S3.

---

## ECS Anywhere

Run ECS tasks on on-prem infrastructure. Requirements: Linux (x86_64/ARM64), Docker, ECS agent, SSM agent, internet to AWS endpoints.

---

## Capacity Providers

```text
Cluster
  ├── FARGATE (weight: 1, base: 2)  ← First 2 + 1/4 remainder
  └── FARGATE_SPOT (weight: 3)       ← 3/4 remainder

Strategy: { base guarantees count, weight distributes rest }
```

---

## Task Placement (EC2 only)

**BINPACK**: Fill nodes to max utilization. **SPREAD**: Even across AZs/instances. **Constraints**: `distinctInstance` (one per host), `memberOf` (expression-based).

---

## GPU & Windows Support

**GPU**: EC2 only. `resourceRequirements: [{ type: "GPU", value: "1" }]`. Instances: p3/p4/g5/g6. ML training, transcoding.
**Windows**: EC2 only. `operatingSystemFamily: "WINDOWS_SERVER_2022_CORE"`. bridge/host network only. No GPU, no Fargate.

---

## Fargate Spot

Up to 70% discount. 2-min interruption warning (SIGTERM → SIGKILL). Best practices: handle SIGTERM (save state), weight-based capacity providers, stateless tasks, SQS-backed retry.

---

## EFS for Stateful Workloads

Shared file storage across all tasks (ReadWriteMany). Works with Fargate natively. Use for WordPress uploads, GitLab repos, shared configs.

---

## EventBridge Scheduling

```text
EventBridge Schedule: cron(0 6 * * ? *) → ECS RunTask
Task runs → does work → exits. Pay only for duration (Fargate).
```

Use: Daily ETL, weekly reports, hourly cleanup.

---

## Container Insights

ECS metrics: CPU, memory, network, storage per task + per cluster. Task count dashboards. Per CloudWatch custom metric cost.

---

## Simplest Mental Model

```text
SCALING         =  Restaurant adding tables during rush.
   Target Track   Aim for 70% full.
   Step           Add 2 if 80% full.
   Scheduled      20 tables at 6 PM.

ROLLING         =  Paint fence plank by plank.
BLUE/GREEN      =  New fence next to old. Switch traffic.
CANARY          =  1 in 10 tries new fence. Roll back if fail.

CIRCUIT BREAKER =  Auto-switch to old fence after 5 planks fall.

AWSVPC          =  Each container gets its own office + phone.
ECS EXEC        =  Remote hatch with badge, not key.
CAPACITY        =  Valet vs economy parking by weight.
FARGATE SPOT    =  Carpool lane. Cheap, 2-min notice.
```
