# 🔍 Service Discovery — Complete Deep Dive

**Related**: [API Gateway](04-api-gateway.md) · [Circuit Breaker](05-circuit-breaker-resilience.md) · [Kubernetes](../k8s.md)

---

## Table of Contents

- [Why Service Discovery?](#-why-service-discovery)
- [1. Client-Side Discovery](#1-client-side-discovery)
- [2. Server-Side Discovery](#2-server-side-discovery)
- [3. Service Registry Patterns](#3-service-registry-patterns)
- [4. Health Checks](#4-health-checks)
- [5. Spring Cloud Netflix Eureka](#5-spring-cloud-netflix-eureka)
- [6. Kubernetes Service Discovery](#6-kubernetes-service-discovery)
- [7. Consul](#7-consul)
- [Comparison Table](#-comparison-table)
- [Simplest Mental Model](#-simplest-mental-model)

---

## 🧭 Why Service Discovery?

### The Problem

```text
In a monolith:
  UserService.verifyEmail(userId);  // direct method call — always works

In microservices:
  User Service is deployed at: 192.168.1.10:8082
  But what if it's restarted and moved to 192.168.1.11:8082?
  What if you scale to 3 instances? 10 instances?
  What about auto-scaling in Kubernetes?

  ❌ Hardcoding IPs breaks constantly
  ❌ Config files can't keep up with dynamic changes
  ❌ Load balancer configs become outdated
```

### The Solution

```text
Service Registry — a dynamic phone book:

┌─────────────────────────────────────────────┐
│              Service Registry               │
│              (Eureka / Consul)              │
│                                             │
│  user-service:                               │
│    ├── 192.168.1.10:8082                     │
│    ├── 192.168.1.11:8082                     │
│    └── 192.168.1.12:8082                     │
│  order-service:                              │
│    └── 192.168.1.20:8083                     │
└─────────────────────────────────────────────┘
         ▲                            ▲
         │ register                   │ query
         │                            │
  ┌──────────────┐           ┌──────────────┐
  │ User Service │           │ Order Service │
  │ (at startup) │           │ (at runtime)  │
  └──────────────┘           └──────────────┘
```

---

## 1. Client-Side Discovery

```text
Client queries the registry and picks an instance directly.

Flow:
  Client (Order Service)
        │
        ├── 1. Query: "Where is user-service?"
        ├── 2. Registry returns: [10.0.0.1:8082, 10.0.0.2:8082]
        ├── 3. Pick one (round-robin / random)
        └── 4. Send HTTP request directly to 10.0.0.1:8082

Pros:
  • Fewer moving parts (no extra LB)
  • Efficient (client picks best instance)
  • No single point of failure (if registry down, cache)

Cons:
  • Every service needs discovery logic
  • Client-side load balancing code
  • Not language-agnostic
```

### Code: Client-Side with Spring Cloud

```java
// Enable service discovery
@SpringBootApplication
@EnableDiscoveryClient  // registers with Eureka automatically
public class OrderServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrderServiceApplication.class, args);
    }
}

// Client-side load balancer
@Service
public class UserServiceClient {
    // @LoadBalanced RestTemplate — uses client-side discovery
    private final RestTemplate loadBalancedRest;

    public UserServiceClient(@LoadBalanced RestTemplate rest) {
        this.loadBalancedRest = rest;
    }

    public UserDTO getUser(Long id) {
        // "user-service" = service ID (not host name!)
        return loadBalancedRest.getForObject(
            "http://user-service/api/users/{id}", UserDTO.class, id);
    }
}

// Config — creates load-balanced RestTemplate
@Configuration
public class RestTemplateConfig {
    @Bean
    @LoadBalanced  // ← this is the key annotation
    public RestTemplate restTemplate() {
        return new RestTemplateBuilder()
            .connectTimeout(Duration.ofSeconds(3))
            .readTimeout(Duration.ofSeconds(10))
            .build();
    }
}

// For discovery-aware WebClient (Spring WebFlux)
@Bean
@LoadBalanced
public WebClient.Builder webClientBuilder() {
    return WebClient.builder();
}
```

### Custom Client-Side Load Balancing

```java
// Manual discovery (without Spring Cloud)
public class SimpleServiceDiscovery {
    private final DiscoveryClient discoveryClient;

    public SimpleServiceDiscovery(DiscoveryClient discoveryClient) {
        this.discoveryClient = discoveryClient;
    }

    public URI getServiceUrl(String serviceId) {
        List<ServiceInstance> instances = discoveryClient.getInstances(serviceId);

        if (instances == null || instances.isEmpty()) {
            throw new ServiceNotFoundException("No instances for: " + serviceId);
        }

        // Round-robin selection
        int index = (int) (System.currentTimeMillis() % instances.size());
        ServiceInstance instance = instances.get(index);

        return instance.getUri();
    }
}

// Using it
@Service
public class ResilientClient {
    private final SimpleServiceDiscovery discovery;
    private final RestTemplate restTemplate;

    public UserDTO getUser(Long id) {
        URI serviceUrl = discovery.getServiceUrl("user-service");
        return restTemplate.getForObject(
            serviceUrl + "/api/users/{id}", UserDTO.class, id);
    }
}
```

---

## 2. Server-Side Discovery

```text
Client goes through a load balancer that knows where services are.

Flow:
   API Client (Browser / Mobile)
        │
        ├── 1. Send request to load balancer
        ▼
   ┌────────────────────┐
   │  Load Balancer     │
   │  (AWS ALB / NGINX) │
   │  queries registry  │
   └────────┬───────────┘
            │
        ┌───┴───────────────┐
        │                   │
        ▼                   ▼
   User Service:1    User Service:2

Pros:
  • Client doesn't know about discovery
  • Language-agnostic
  • Centralized control

Cons:
  • Extra network hop
  • LB can become bottleneck
  • More infrastructure
```

### Code: Server-Side with NGINX

```nginx
# NGINX as server-side discovery + load balancing
upstream user-service {
    # If using Consul Template, these are dynamically populated
    server 192.168.1.10:8082 weight=5;
    server 192.168.1.11:8082 weight=5;
    server 192.168.1.12:8082 weight=5 max_fails=3 fail_timeout=30s;
}

upstream order-service {
    server 192.168.1.20:8083;
    server 192.168.1.21:8083;
}

server {
    listen 80;
    location /api/users {
        proxy_pass http://user-service;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
    }
    location /api/orders {
        proxy_pass http://order-service;
    }
}
```

### Server-Side with AWS ALB + ECS

```yaml
# AWS ECS Service Definition (server-side discovery)
services:
  user-service:
    # ALB auto-discovers ECS tasks
    # No registry configuration needed
    load_balancer:
      target_group_arn: arn:aws:elasticloadbalancing:...
      container_name: user-service
      container_port: 8082
    desired_count: 3
    auto_scaling:
      min_capacity: 2
      max_capacity: 10
      target_cpu: 70
```

---

## 3. Service Registry Patterns

### 3.1 Self-Registration

```text
Service registers itself on startup, deregisters on shutdown.

  Service           Registry
    │                  │
    │── register ─────>│  POST /eureka/apps/USER-SERVICE
    │                  │  { hostname, port, healthCheckUrl }
    │                  │
    │── heartbeat ────>│  Every 30s: PUT /eureka/apps/USER-SERVICE/status
    │                  │
    │ (crashes)        │  (no heartbeat → registry removes after 90s)
    │                  │
    │── deregister ───>│  DELETE /eureka/apps/USER-SERVICE/instanceId
```

```java
// Spring Cloud — self-registration is automatic
@SpringBootApplication
@EnableEurekaClient  // self-register on startup
public class UserServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(UserServiceApplication.class, args);
    }
}

// Configure registration
// application.yml:
//   eureka:
//     instance:
//       hostname: ${HOST:localhost}
//       prefer-ip-address: true
//       lease-renewal-interval-in-seconds: 30
//       lease-expiration-duration-in-seconds: 90
//     client:
//       serviceUrl:
//         defaultZone: http://eureka-server:8761/eureka/
```

### 3.2 Third-Party Registration

```text
An external registrar handles registration (e.g., Kubernetes).

  Pod            Kubelet          API Server        etcd
   │                │                │               │
   │── start ──────>│                │               │
   │                │── register ───>│               │
   │                │                │── store ─────>│
   │                │                │               │
   │ (any pod)      │                │               │
   │ (crashes)      │                │               │
   │                │── detect ─────>│               │
   │                │── deregister ─>│               │
   │                │                │── delete ────>│
```

```yaml
# Kubernetes — third-party registration via API Server
apiVersion: v1
kind: Service
metadata:
  name: user-service
spec:
  selector:
    app: user-service  # targets pods with this label
  ports:
    - port: 80
      targetPort: 8082
  type: ClusterIP  # internal DNS: user-service.default.svc.cluster.local
```

---

## 4. Health Checks

### Why Health Checks Matter

```text
Without health checks:
  Registry thinks service is healthy → routes traffic
  But service is actually in a broken state
  → 50x errors, cascading failures

Types of health checks:
  1. Liveness Probe  — Is the process alive?
  2. Readiness Probe — Is the service ready to accept traffic?
  3. Deep Health     — Are dependencies (DB, cache) working?
```

### Code: Health Checks

```java
// Spring Boot Actuator — built-in health endpoint
@SpringBootApplication
public class UserService {
    public static void main(String[] args) {
        SpringApplication.run(UserService.class, args);
    }
}

// Custom health indicator — deep health
@Component
public class DatabaseHealthIndicator implements HealthIndicator {
    private final DataSource dataSource;

    public DatabaseHealthIndicator(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @Override
    public Health health() {
        try (Connection conn = dataSource.getConnection()) {
            if (conn.isValid(2)) {
                return Health.up()
                    .withDetail("database", "PostgreSQL")
                    .withDetail("validation", "passed")
                    .build();
            }
            return Health.down()
                .withDetail("database", "PostgreSQL")
                .withDetail("validation", "failed - timeout")
                .build();
        } catch (Exception e) {
            return Health.down(e)
                .withDetail("database", "PostgreSQL")
                .build();
        }
    }
}

// Discovery-aware health check — Eureka checks /actuator/health
// If DOWN → Eureka removes from list
```

### Kubernetes Probes

```yaml
# Kubernetes health checks
apiVersion: v1
kind: Pod
metadata:
  name: user-service
spec:
  containers:
    - name: user-service
      image: user-service:latest
      livenessProbe:
        httpGet:
          path: /actuator/health/liveness
          port: 8082
        initialDelaySeconds: 30
        periodSeconds: 10
        timeoutSeconds: 5
        failureThreshold: 3
      readinessProbe:
        httpGet:
          path: /actuator/health/readiness
          port: 8082
        initialDelaySeconds: 10
        periodSeconds: 5
        timeoutSeconds: 3
        successThreshold: 1
        failureThreshold: 2
      startupProbe:  # for slow-starting containers
        httpGet:
          path: /actuator/health
          port: 8082
        initialDelaySeconds: 0
        periodSeconds: 5
        failureThreshold: 30  # up to 150s to start
```

### Custom Discovery Health Check

```java
@Component
public class DiscoveryHealthCheck {
    private final EurekaClient eurekaClient;

    public DiscoveryHealthCheck(EurekaClient eurekaClient) {
        this.eurekaClient = eurekaClient;
    }

    public boolean isServiceHealthy(String serviceId) {
        InstanceInfo instance = eurekaClient.getNextServerFromEureka(serviceId, false);
        return InstanceInfo.InstanceStatus.UP.equals(instance.getStatus());
    }

    // Circuit breaker aware
    @CircuitBreaker(name = "discovery", fallbackMethod = "checkCache")
    public boolean check(String serviceId) {
        return isServiceHealthy(serviceId);
    }

    public boolean checkCache(String serviceId, Throwable t) {
        log.warn("Discovery down, using cached status for {}", serviceId);
        return healthCache.getOrDefault(serviceId, true);
    }
}
```

---

## 5. Spring Cloud Netflix Eureka

### Eureka Server

```java
@SpringBootApplication
@EnableEurekaServer
public class EurekaServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(EurekaServerApplication.class, args);
    }
}
```

```yaml
# eureka-server/application.yml
server:
  port: 8761

eureka:
  instance:
    hostname: localhost
    prefer-ip-address: true
  client:
    register-with-eureka: false  # server doesn't register with itself
    fetch-registry: false         # server doesn't need to discover
    serviceUrl:
      defaultZone: http://${eureka.instance.hostname}:${server.port}/eureka/
  server:
    enable-self-preservation: true  # protect against network partitions
    renewal-percent-threshold: 0.85
    eviction-interval-timer-in-ms: 5000  # check dead instances every 5s
```

### Eureka Client

```yaml
# user-service/application.yml
spring:
  application:
    name: user-service

server:
  port: ${PORT:8082}

eureka:
  instance:
    prefer-ip-address: true
    lease-renewal-interval-in-seconds: 10   # heartbeat every 10s
    lease-expiration-duration-in-seconds: 30  # 30s no heartbeat = dead
    instance-id: ${spring.application.name}:${random.value}
    metadata-map:
      version: ${VERSION:1.0}
      region: ${REGION:us-east-1}
  client:
    serviceUrl:
      defaultZone: http://eureka-master:8761/eureka/,http://eureka-backup:8762/eureka/
    registry-fetch-interval-seconds: 10  # refresh local cache every 10s
    healthcheck:
      enabled: true  # use /actuator/health instead of heartbeat
```

### Eureka Flow

```text
Startup:
  Client ──POST──> Eureka Server
  POST /eureka/apps/USER-SERVICE
  { instanceId, hostname, ipAddr, port, statusPageUrl,
    healthCheckUrl, metadata }

Heartbeat:
  Client ──PUT──> Eureka Server (every 10s)
  PUT /eureka/apps/USER-SERVICE/{instanceId}
  { status: UP }

Discovery Query:
  Client ──GET──> Eureka Server (cached locally, refresh every 10s)
  GET /eureka/apps/USER-SERVICE
  → Returns all instances with status

Eviction:
  Eureka evicts if no heartbeat for 30s (configurable)
  Self-preservation: if >85% of heartbeats missed in 1min,
  Eureka stops evicting (protects against network partition)
```

---

## 6. Kubernetes Service Discovery

### DNS-Based Discovery

```yaml
apiVersion: v1
kind: Service
metadata:
  name: user-service
  namespace: production
spec:
  selector:
    app: user-service
  ports:
    - port: 80
      targetPort: 8082
  type: ClusterIP
```

```text
DNS naming:
  user-service.production.svc.cluster.local

Kubernetes DNS resolves to:
  • ClusterIP (if using Service)
  • Pod IPs (if using Headless Service with DNS SRV records)

Usage from other pods:
  http://user-service/api/users/1          ← same namespace
  http://user-service.production/api/...   ← cross-namespace
```

### Spring Boot on Kubernetes

```java
// No Eureka needed — use Kubernetes Service DNS
@SpringBootApplication
public class OrderService {
    public static void main(String[] args) {
        SpringApplication.run(OrderService.class, args);
    }
}

// Just use the service name directly
@Service
public class UserServiceClient {
    private final RestTemplate rest;

    public UserServiceClient(RestTemplate rest) {
        this.rest = rest;
    }

    public UserDTO getUser(Long id) {
        // Kubernetes DNS resolves this
        return rest.getForObject(
            "http://user-service/api/users/{id}", UserDTO.class, id);
    }
}

// For advanced load balancing, use Spring Cloud Kubernetes
@Bean
@LoadBalanced
public RestTemplate restTemplate() {
    return new RestTemplate();
}
```

### Headless Service + StatefulSet

```yaml
# For stateful services that need stable DNS
apiVersion: v1
kind: Service
metadata:
  name: kafka
spec:
  clusterIP: None  # headless — DNS returns all pod IPs
  selector:
    app: kafka
  ports:
    - port: 9092
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: kafka
spec:
  serviceName: kafka  # must match the headless Service
  replicas: 3
  selector:
    matchLabels:
      app: kafka
  template:
    metadata:
      labels:
        app: kafka
    spec:
      containers:
        - name: kafka
          image: confluentinc/cp-kafka:latest
```

```text
StatefulSet DNS naming:
  kafka-0.kafka.default.svc.cluster.local
  kafka-1.kafka.default.svc.cluster.local
  kafka-2.kafka.default.svc.cluster.local
```

---

## 7. Consul

### Setup

```hcl
# consul-config.hcl
server = true
bootstrap_expect = 3
data_dir = "/opt/consul"
ui = true
client_addr = "0.0.0.0"

connect {
  enabled = true
}
```

### Spring Boot with Consul

```yaml
# application.yml
spring:
  cloud:
    consul:
      host: localhost
      port: 8500
      discovery:
        enabled: true
        register: true
        instance-id: ${spring.application.name}:${random.value}
        health-check-interval: 10s
        health-check-path: /actuator/health
        prefer-ip-address: true
        tags:
          - version=1.0
          - region=us-east-1
```

### Consul vs Eureka vs Kubernetes DNS

| Feature | Eureka | Consul | Kubernetes DNS |
|---------|--------|--------|----------------|
| CAP | AP (CP with quorum) | CP | CP (etcd) |
| Health checks | Client heartbeat | Agent checks | Kubelet probes |
| Self-preservation | Yes (AP) | No (CP) | No |
| KV store | No | Yes | Yes (ConfigMap) |
| Multi-DC | Limited | Native | Cluster-local |
| Service mesh | No | Yes (Connect) | Yes (Istio) |
| DNS interface | Custom lib | DNS + HTTP | Native DNS |

---

## 📊 Comparison Table

| Aspect | Client-Side | Server-Side |
|--------|-------------|-------------|
| Complexity | More in app | More in infra |
| Latency | Direct | +1 hop |
| Scalability | Good | LB can bottleneck |
| Resilience | Cache = no SPOF | LB = SPOF |
| Language | Requires lib | Any client |
| Typical | Spring Cloud + Eureka | AWS ALB + ECS |
| LB algorithm | Ribbon, custom | NGINX, HAProxy |

---

## 🧠 Simplest Mental Model

```text
SERVICE        =  A phone book for microservices. Instead of
REGISTRY          memorizing everyone's phone numbers (IPs),
                  you look them up when needed.

SELF-          =  "Hi, I'm the Pizza Service. My number is 555-0100.
REGISTRATION      I'm at 123 Main St." Tells the registry on arrival.

HEARTBEAT      =  Calling the registry every 30 seconds:
                   "Still alive! Still at 555-0100."

HEALTH CHECK   =  Not just "am I alive?" but "can I actually work?"
                   "My oven is broken (DB is down) — don't send customers."

CLIENT-SIDE    =  You have a contact book on your phone.
DISCOVERY         When you need the pizza place, you check your phone
                  and call them directly. No operator needed.

SERVER-SIDE    =  You call the restaurant operator. They connect you
DISCOVERY         to whichever kitchen is free. You never know which
                  kitchen you got.

KUBERNETES     =  Built-in magic. Pods come and go, but you just say
DNS               "user-service" and it works. Like calling "Pizza"
                  and getting connected automatically.
```

---

**Next**: [API Gateway](04-api-gateway.md)
