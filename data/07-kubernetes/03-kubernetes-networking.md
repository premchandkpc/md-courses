# 🌐 Kubernetes Networking — Complete Deep Dive

## ToC
- CNI Model | CNI Plugins | Pod Networking | Service Types | kube-proxy | EndpointSlices | CoreDNS | Ingress vs Gateway API | Network Policies | Cilium eBPF | Multi-Cluster | NodePort vs hostPort vs externalIP vs LB

---

## CNI Model

```
                     Node (Linux Host)
  +-----------------+    +-----------------+
  |   Pod A          |    |   Pod B          |
  | eth0 (veth)      |    | eth0 (veth)      |
  +--------+---------+    +--------+---------+
           |                       |
  +--------+-----------------------+--------+
  |               cni0 bridge              |
  +--------------------+-------------------+
              +---------+---------+
              |   eth0 (host NIC)  |
              +---------+---------+
```

**Flow:** kubelet -> pause container (netns) -> CNI ADD -> veth pair -> cni0 bridge -> IPAM -> routes

---

## CNI Plugins

| Plugin | Model | Encap | Key feature |
|--------|-------|-------|-------------|
| Flannel | Overlay | VXLAN | Simple |
| Calico | L3 | None/IPIP | NetworkPolicy, eBPF |
| Cilium | eBPF | VXLAN/None | L7, Hubble, ClusterMesh |
| Canal | Flannel+Calico | VXLAN | Both net + policy |
| Antrea | OVS | VXLAN/Geneve | Traceflow |

**Need policy?** Calico/Cilium/Antrea. **Need eBPF?** Cilium. **Simple?** Flannel.

---

## Pod Networking

**IP-per-Pod:** Each pod gets 1 IP from CNI IPAM. All containers share IP via pause container netns (localhost).

```yaml
spec:
  containers:
  - ports:
    - containerPort: 8080
      hostPort: 30080
```

---

## Service Types

**ClusterIP (default):** Virtual IP, cluster-internal. **NodePort:** All nodes listen 30000-32767, DNAT to pod.

```yaml
spec:
  type: LoadBalancer
  externalTrafficPolicy: Local   # preserve client IP
```

**LoadBalancer:** `Cluster` mode (SNAT, lose IP) vs `Local` mode (preserve IP). **ExternalName:** CNAME to external DNS.

---

## kube-proxy Modes

| Mode | Lookup | Scaling |
|------|--------|---------|
| iptables | O(n) chain | Simple |
| IPVS | O(1) hash | 10K+ services |
| userspace | Proxy | Deprecated |

---

## EndpointSlices

```yaml
kind: EndpointSlice
addressType: IPv4
ports:
- name: http
  port: 8080
endpoints:
- addresses: ["10.1.0.1"]
  conditions: {ready: true}
  topology:
    kubernetes.io/hostname: node-1
    topology.kubernetes.io/zone: us-east-1a
```

**Why:** Max 100/slice, only changed slices update, topology-aware.

---

## CoreDNS

```
  DNS: <service>.<namespace>.svc.cluster.local
  Example: my-svc.default.svc.cluster.local -> ClusterIP
```

```yaml
data:
  Corefile: |
    .:53 {
        errors
        health
        kubernetes cluster.local in-addr.arpa ip6.arpa {
          pods insecure
          ttl 30
        }
        prometheus :9153
        forward . /etc/resolv.conf
        cache 30
        loadbalance round_robin
    }
```

---

## Ingress vs Gateway API

### Ingress (v1)
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-svc
            port: 80
```

### Gateway API
```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
spec:
  gatewayClassName: istio
  listeners:
  - protocol: HTTPS
    port: 443
    tls:
      certificateRefs:
      - name: app-tls
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
spec:
  parentRefs:
  - name: prod-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: api-svc
      port: 80
    - name: api-v2-svc
      port: 80
      weight: 10             # 10% canary
```

| Feature | Ingress | Gateway API |
|---------|---------|-------------|
| Traffic split | annotation | native weight |
| Protocols | HTTP/HTTPS | HTTP, TCP, TLS, UDP, gRPC |

---

## Network Policies

### Default Deny
```yaml
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

### Selective Allow
```yaml
spec:
  podSelector:
    matchLabels:
      app: postgres
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: api
      podSelector:
        matchLabels:
          app: backend
    ports:
    - protocol: TCP
      port: 5432
```

**Rules:** ingress.from = podSelector / namespaceSelector / ipBlock. Default: no policy = all allowed. With policy = deny-all-except-matched.

---

## Cilium eBPF

```bash
hubble observe --from-pod default/nginx --to-pod default/api
hubble observe --verdict DROPPED
```

**CiliumNetworkPolicy (L7):** match HTTP method + path in policies.

**Cluster Mesh:** Direct eBPF routing across clusters, no gateway. Needs CA sharing + non-overlapping CIDRs.

---

## NodePort vs hostPort vs externalIP vs LoadBalancer

| Feature | NodePort | hostPort | externalIP | LB |
|---------|----------|----------|------------|-----|
| Port | 30000-32767 | Any | Any | Cloud |
| Client IP | SNAT | Preserved | Preserved | Varies |
| Cloud | Manual | Manual | Manual | Auto |
| Use | Dev | DaemonSet | Legacy | Prod |

```yaml
spec:
  externalIPs:
  - 192.168.1.100
```

---

## Simplest Mental Model

```
K8s networking = apartment building mail system

+------------------------------------------------------------------------------+
|  Pod = apartment unit (own IP)  |  veth = mail slot  |  bridge = lobby table |
|  Service = front desk forwarding mail  |  ClusterIP = virtual mailbox #     |
|  NodePort = lobby door  |  Ingress = doorman  |  NetworkPolicy = floor rules |
|  CNI = postal service  |  CoreDNS = phone book  |  Cilium = security cameras |
|                                                                              |
|  Core: every pod gets a real IP (no NAT between pods)                       |
|  Services decouple client from changing pod IPs                             |
+------------------------------------------------------------------------------+


---

## Code Examples

```python
# Example implementation
# [Add language-specific code demonstrating core concept]
pass
```

---

## Common Failure Modes

**Problem**: [Key issue in production]

**Root cause**: [Why it happens]

**Solution**: [How to fix]

---

## Interview Questions

### Q1: [Core concept question]

**Answer**: [Detailed explanation with trade-offs]

### Q2: [Design/architecture question]

**Answer**: [Best practices and reasoning]
