# 📊 Kubernetes Observability — Complete Deep Dive

## ToC
- Metrics Server | kube-state-metrics | Prometheus Operator | VictoriaMetrics vs Prometheus | Grafana | Loki | OpenTelemetry | Jaeger/Tempo | cAdvisor | Eviction | Custom Metrics API

---

## Metrics Server

```
  +-----------+     +-----------+     +-----------+
  | Metrics   |---->| kubelet   |---->| cAdvisor  |
  | Server    |<----| (Summary  |<----| (built-in)|
  +-----------+     +-----------+     +-----------+
       |
       | /apis/metrics.k8s.io/v1beta1
       v
  +-----------+
  | HPA/VPA   |
  | kubectl   |
  | top       |
  +-----------+
```

```bash
kubectl top nodes
kubectl top pods -A
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes | jq
```

### HPA Integration
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## kube-state-metrics

**Key metrics:**
```
kube_deployment_status_replicas{deployment="my-app"}
kube_pod_status_phase{phase="Running|Failed"}
kube_node_status_condition{condition="Ready"}
```

**Cardinality:** Use `--metric-labels-allowlist` to restrict pod labels on large clusters.

---

## Prometheus Operator

```
  +------------------+     +------------------+
  | ServiceMonitor   |     | PodMonitor       |
  +--------+---------+     +--------+---------+
           |                        |
           v                        v
  +------------------+     +------------------+
  | Prometheus       |---->| Alertmanager     |
  | (scrape, store)  |     | (dedup, route)   |
  +------------------+     +------------------+
```

### ServiceMonitor & Rules
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
spec:
  selector:
    matchLabels:
      app: my-app
  namespaceSelector:
    matchNames:
    - prod
  endpoints:
  - port: metrics
    interval: 15s
---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
spec:
  groups:
  - name: app.rules
    rules:
    - alert: HighErrorRate
      expr: |
        sum(rate(http_requests_total{status=~"5.."}[5m]))
        / sum(rate(http_requests_total[5m])) > 0.05
      for: 5m
      severity: critical
---
apiVersion: monitoring.coreos.com/v1
kind: AlertmanagerConfig
spec:
  route:
    receiver: pagerduty
  receivers:
  - name: pagerduty
    pagerdutyConfigs:
    - routingKey:
        name: pagerduty-key
```

**Thanos:** Prometheus sidecar -> S3/GCS -> Thanos Query + Compactor for long-term HA storage.

---

## VictoriaMetrics vs Prometheus

| Feature | Prometheus | VictoriaMetrics |
|---------|-----------|----------------|
| Storage | Local TSDB | Local + object store |
| HA | Thanos needed | Built-in (vmcluster) |
| Downsampling | Thanos | Built-in |
| Resource usage | Higher | 30-50% less |
| Retention | Days-weeks | Months-years |

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: victoria-metrics
spec:
  template:
    spec:
      containers:
      - name: main
        image: victoriametrics/victoria-metrics:v1.95.0
        args:
        - -storageDataPath=/data
        - -retentionPeriod=12
```

---

## Grafana Dashboards

**Essential:** Cluster Overview (node/pod resources), Pod Details (per-pod metrics), Nodes (conditions, errors), etcd (leader changes, latency p99)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  labels:
    grafana_dashboard: "1"
data:
  cluster-dashboard.json: |
    { "title": "Kubernetes Cluster Overview", "panels": [...] }
```

---

## Loki

```
  +----------+     +----------+     +----------+
  | Promtail |---->| Loki     |---->| Grafana  |
  | (logs)   |     | (store)  |     | (explore)|
  +----------+     +----------+     +----------+
```

**Promtail config:**
```yaml
scrape_configs:
- job_name: kubernetes-pods
  kubernetes_sd_configs:
  - role: pod
  relabel_configs:
  - source_labels: [__meta_kubernetes_namespace]
    target_label: namespace
  - source_labels: [__meta_kubernetes_pod_name]
    target_label: pod
```

**LogQL:**
```logql
{app="nginx", namespace="prod"} |= "error"
rate({app="nginx"} |= "error" [5m])
sum by(pod) (count_over_time({app="nginx"} |= "error" [5m]))
{app="api"} | json | method = "POST" and status >= 500
```

---

## OpenTelemetry

```
  App (auto-instr) -> OTel Collector -> Jaeger/Tempo (traces)
                                    -> Prometheus (metrics)
                                    -> Loki (logs)

  Collector pipeline:
  Receivers (OTLP, Prom) -> Processors (batch, attr, k8s) -> Exporters
```

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
processors:
  batch:
    timeout: 1s
  memory_limiter:
    limit_mib: 512
  k8sattributes:
    extract:
      metadata:
      - k8s.pod.uid
      - k8s.namespace.name
      - k8s.node.name
exporters:
  otlp:
    endpoint: tempo:4317
  prometheus:
    endpoint: 0.0.0.0:8889
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [k8sattributes, batch]
      exporters: [otlp]
    metrics:
      receivers: [otlp, prometheus]
      processors: [batch]
      exporters: [prometheus]
```

**Auto-instrumentation:** `Instrumentation` CRD + namespace annotation `instrumentation.opentelemetry.io/inject-java: "true"`

---

## Jaeger/Tempo

```
  Service A -> OTel Col -> Tempo/Jaeger -> S3 -> Grafana Explore Traces
```

**Tail sampling (OTel):** Sample 100% errors + 100% traces >1s + 10% probabilistic.

**Exemplars:** Link metrics to traces. Click scatter point in Grafana -> open trace. `http_request_duration_seconds_bucket{le="0.5"} 12 {trace_id="abc"}`

---

## cAdvisor

**Embedded in kubelet.** Exposes `/metrics/cadvisor`.

```bash
kubectl get --raw /api/v1/nodes/node-1/proxy/metrics/cadvisor
kubectl get --raw /api/v1/nodes/node-1/proxy/stats/summary
```

**Key metrics:** `container_cpu_usage_seconds_total`, `container_memory_working_set_bytes`, `container_network_receive_bytes_total`, `container_oom_events_total`

---

## Eviction Pressure

**Memory:** `--eviction-hard=memory.available<100Mi`. Eviction order: BestEffort > Burstable > Guaranteed.

**Disk:** `--eviction-hard=nodefs.available<10%,imagefs.available<15%`. GC dead containers + unused images.

**PID:** `--eviction-hard=pids.available<10%`.

```promql
kube_node_status_condition{condition="MemoryPressure",status="true"}
increase(container_oom_events_total[5m]) > 0
```

---

## Custom Metrics API

**prometheus-adapter:**
```yaml
rules:
- seriesQuery: 'http_requests_total{namespace!="",pod!=""}'
  resources:
    overrides:
      namespace: {resource: namespace}
      pod: {resource: pod}
  name:
    matches: "^http_requests_total$"
    as: "requests_per_second"
  metricsQuery: 'sum(rate(<<.Series>>{<<.LabelMatchers>>}[2m])) by (<<.GroupBy>>)'
```

**HPA with custom metrics:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  metrics:
  - type: Pods
    pods:
      metric:
        name: requests_per_second
      target:
        type: AverageValue
        averageValue: 100
```

**VPA:**
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  updatePolicy:
    updateMode: Auto
  resourcePolicy:
    containerPolicies:
    - containerName: "*"
      minAllowed:
        cpu: 100m
        memory: 128Mi
      maxAllowed:
        cpu: 4
        memory: 8Gi
```

---

## Simplest Mental Model

```
K8s observability = hospital monitoring system

+------------------------------------------------------------------------------+
|  Metrics Server = vitals now  |  ksm = patient chart board                   |
|  Prometheus = central monitor  |  Thanos = records archive                   |
|  Grafana = all patient charts  |  Loki = nurse's log book                   |
|  Promtail = nurse writing logs  |  OpenTelemetry = standard chart format     |
|  Jaeger/Tempo = patient journey ER->Xray->Surgery->Recovery                 |
|  cAdvisor = per-patient machine readouts  |  HPA = call more nurses          |
|                                                                              |
|  Core: Metrics (what is happening) + Logs (what happened) + Traces (where)  |
|  = full observability. If only one, logs are most useful.                   |
+------------------------------------------------------------------------------+
