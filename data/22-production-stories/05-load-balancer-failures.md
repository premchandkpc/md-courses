# ⚖️ Load Balancer Production Failures — Production Incident Deep Dive

> **Scope:** Real-world load balancer failure patterns covering connection exhaustion, sticky session drift, circuit breaker cascade, DNS resolution failures, and cross-region failover delays. Each scenario follows symptom → detection → investigation → root cause → mitigation → permanent fix → lessons learned.
>
> **Applicability:** SRE teams, platform engineers, network engineers, and application developers managing L4/L7 load balancers (HAProxy, Nginx, AWS ALB/NLB, GCP HTTP LB) in production.

---

## Table of Contents

1. [Scenario A: Connection Exhaustion (L4) — SYN Flood → maxconn Reached → Health Check Fails → All Backends Down](#scenario-a-connection-exhaustion-l4--syn-flood--maxconn-reached--health-check-fails--all-backends-down)
2. [Scenario B: Sticky Session Drift — Session Persistence via Cookie → Instance Fails → Session Affinity to Dead Node → Session Loss](#scenario-b-sticky-session-drift--session-persistence-via-cookie--instance-fails--session-affinity-to-dead-node--session-loss)
3. [Scenario C: Circuit Breaker Cascade — One Slow Upstream → Timeout to LB → LB Marks All Unhealthy → DB Overload → Full Outage](#scenario-c-circuit-breaker-cascade--one-slow-upstream--timeout-to-lb--lb-marks-all-unhealthy--db-overload--full-outage)
4. [Scenario D: DNS Resolution Failure — LB DNS Record TTL Too High → Failover Slow → Users Hit Dead LB IP](#scenario-d-dns-resolution-failure--lb-dns-record-ttl-too-high--failover-slow--users-hit-dead-lb-ip)
5. [Scenario E: Cross-Region Failover — Primary Region Fails → DNS Update → Client DNS Cache Still Points to Primary → Extended Outage](#scenario-e-cross-region-failover--primary-region-fails--dns-update--client-dns-cache-still-points-to-primary--extended-outage)
6. [Detection and Monitoring Reference](#detection-and-monitoring-reference)
7. [Mitigation Playbook](#mitigation-playbook)
8. [Permanent Fixes and Configuration Reference](#permanent-fixes-and-configuration-reference)

---

## Scenario A: Connection Exhaustion (L4) — SYN Flood → maxconn Reached → Health Check Fails → All Backends Down

### Symptom

```
14:30:00  Traffic spike: 50,000 req/s → 150,000 req/s (DDoS / flash crowd)
14:30:15  Nginx maxconn (65536) reached
14:30:20  New connections: 503 Service Unavailable
14:30:25  Health check connections also blocked (same port)
14:30:30  Health check fails → Nginx marks ALL backends as down
14:30:35  No backends available → 100% 503 error rate
14:30:40  Full outage — no traffic served
```

### Detection

```
Alert: active_connections == maxconn
Alert: request_rate spike > 2x average
Alert: upstream_server_checks_failing > 0
Alert: error_rate (5xx) > 5%
Alert: LB SYN backlog overflow (netstat -s | grep SYN)

Nginx metrics:
  $ curl http://localhost:8080/nginx_status
  Active connections: 65536 ← maxed out
  server accepts handled requests
   2147483647 2147483647 5120001234
  Reading: 0 Writing: 512 Waiting: 65024

HAProxy stats:
  $ echo "show stat" | socat /var/run/haproxy.sock stdio
  # pxname,svname,qcur,qmax,scur,smax,slim
  backend,orders-api,0,0,65536,65536,65536 ← maxed

SYN backlog:
  $ netstat -s | grep -i "syn"
    34123 SYNs to LISTEN sockets dropped
    15234 times the listen queue of a socket overflowed

Connection state:
  $ ss -tan | grep :443 | awk '{print $1}' | sort | uniq -c
  45000 ESTAB
  15000 TIME-WAIT
   5536 CLOSE-WAIT    ← CLOSE-WAIT accumulation = connection leak
```

### Investigation

```

── 1. IDENTIFY TYPE OF EXHAUSTION

# Connection counts by state:
$ ss -tan state time-wait | wc -l  # Normal if < 5000
$ ss -tan state close-wait | wc -l # Should be near 0
$ ss -tan state fin-wait-1 | wc -l # Should be near 0

# If CLOSE-WAIT > 1000:
# → Backend application not closing connections
# → Application reads HTTP response but never calls close()
# → LB keeps connection open until timeout
# → fd leak in application

── 2. CHECK APPLICATION CONNECTION HANDLING

# Backend server — check open file descriptors:
$ lsof -p $(pgrep -f orders-api) | wc -l
# If approaching ulimit -n → file descriptor leak

# Check keepalive settings mismatch:
# LB timeout: keepalive_timeout = 75s (Nginx default)
# App server: keepalive = 30s (Tomcat default)
# → App closes connection but LB keeps it in CLOSE-WAIT

── 3. CHECK HEALTH CHECK ENDPOINT

$ curl -v http://10.0.1.50:8080/health
# Returns 200 OK but actually slow/down?
# Common: health endpoint returns 200 even when DB is down
# → LB thinks backend is healthy → sends traffic → connection hangs
```

### Root Cause

```
CONNECTION EXHAUSTION DEATH SPIRAL
═══════════════════════════════════

                    ┌─────────────────────────────────────┐
                    │  Traffic spike exceeds maxconn       │
                    │  (150K req/s, maxconn=65536)         │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │  LB rejects new connections          │
                    │  → 503 Service Unavailable           │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │  Health check endpoint also blocked  │
                    │  (same port, same maxconn pool)      │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │  Health check FAILS                 │
                    │  → All backends marked DOWN          │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │  No backends available               │
                    │  → 100% 503 error rate               │
                    │  → FULL OUTAGE                      │
                    └─────────────────────────────────────┘

  COMPOUNDING FACTORS:
  • maxconn includes HEALTH CHECK connections
  • No dedicated health check port
  • Backend connection leak → CLOSE-WAIT accumulation → fd exhaustion
  • Keepalive timeout mismatch → connections stuck in CLOSE-WAIT
  • No connection queue / backlog tuning
  • No rate limiting before LB
```

### Mitigation

```

── IMMEDIATE: INCREASE MAXCONN TEMPORARILY

# Nginx:
$ vi /etc/nginx/nginx.conf
worker_connections 100000;  # Was 65536
# Reload: nginx -s reload

# HAProxy:
$ vi /etc/haproxy/haproxy.cfg
global
  maxconn 100000

── IMMEDIATE: ADD RATE LIMITING AT LB LEVEL

# Nginx:
limit_req_zone $binary_remote_addr zone=iplimit:10m rate=1000r/s;
server {
    location / {
        limit_req zone=iplimit burst=2000 nodelay;
        proxy_pass http://backend;
    }
}

# HAProxy:
frontend http-in
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    http-request deny deny_status 429 if { src_http_req_rate(10s) gt 1000 }

── IMMEDIATE: USE DEDICATED HEALTH CHECK PORT

# Run health check on separate port (e.g., 8081)
server {
    listen 8081;  # Health check port — never saturated by traffic
    location /health {
        return 200;
    }
}

# AWS ALB: Use separate health check port target group
```

### Permanent Fix

```nginx
# Nginx production configuration
user nginx;
worker_processes auto;
worker_rlimit_nofile 200000;

events {
    worker_connections 100000;
    multi_accept on;
    use epoll;
}

http {
    # Connection pooling
    keepalive_timeout 65;
    keepalive_requests 10000;

    # Upstream keepalive
    upstream backend {
        server 10.0.1.50:8080 max_fails=3 fail_timeout=30s;
        server 10.0.1.51:8080 max_fails=3 fail_timeout=30s;
        keepalive 32;
        keepalive_requests 1000;
        keepalive_timeout 60s;
    }

    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=per_ip:10m rate=500r/s;
    limit_conn_zone $binary_remote_addr zone=addr:10m;

    server {
        listen 80 backlog=1024;
        listen 443 ssl backlog=1024;

        # Rate limiting
        limit_req zone=per_ip burst=1000 nodelay;
        limit_conn addr 100;

        # Dedicated health check
        location /health {
            access_log off;
            return 200;
            add_header Content-Type text/plain;
        }

        location / {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }
    }
}
```

```haproxy
# HAProxy production configuration
global
    maxconn 100000
    ulimit-n 200000
    nbproc 4
    tune.maxaccept 100

defaults
    log global
    mode http
    option httplog
    option dontlognull
    option http-server-close
    option redispatch
    retries 3
    timeout http-request 10s
    timeout queue 1m
    timeout connect 10s
    timeout client 1m
    timeout server 1m
    timeout http-keep-alive 60s
    timeout check 10s
    maxconn 5000

frontend http-in
    bind *:80
    bind *:443

    # Rate limiting
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    http-request track-sc0 src
    http-request deny deny_status 429 if { sc_http_req_rate(0) gt 1000 }

    default_backend orders-api

backend orders-api
    balance roundrobin
    option httpchk GET /health
    server app-1 10.0.1.50:8080 check inter 5s fall 3 rise 2 maxconn 200
    server app-2 10.0.1.51:8080 check inter 5s fall 3 rise 2 maxconn 200
    # Health check is on the same backend port
    # Better: use separate port for health checks
```

---

## Scenario B: Sticky Session Drift — Session Persistence via Cookie → Instance Fails → Session Loss

### Symptom

```
Web server 3 (10.0.1.52) crashes at 15:00:00.
Users with sessions pinned to server 3:
  → First request after crash: routed to server 3 (based on cookie)
  → Server 3 is down → connection refused / timeout
  → After health check timeout (30s), LB marks server 3 DOWN
  → Users redirected to server 1 or 2
  → BUT HTTP session data is on server 3's local memory → LOST
  → Users see: "Session expired" / "Please log in again"
  → For shopping cart: cart is empty
  → Business impact: 40% of active users lose session
```

### Detection

```
Alert: Error rate spike for users with session cookies
Alert: Login page requests spike (users re-authenticating)
Alert: User complaints: "Session expired" errors
Alert: Customer support ticket volume spike

Application logs:
  "Session [ABC123] not found on this instance"
  "IllegalStateException: Session already invalidated"
  "HttpSessionBindingException: No session data for key 'cart'"
```

### Root Cause

```
STICKY SESSION DRIFT TIMELINE
═════════════════════════════

  ┌──────────────────────────────────────────────────────────────┐
  │  14:59:00  User A has session on web-3                      │
  │            Cookie: ROUTEID=.web-3; JSESSIONID=ABC123        │
  │            Cart: 3 items ($127.50)                          │
  │            ↓                                                 │
  │  15:00:00  web-3 crashes (OOM)                               │
  │            Load balancer still routes to web-3 via cookie    │
  │            ↓                                                 │
  │  15:00:02  User A request → web-3 → connection refused      │
  │            Browser retries... still fails                    │
  │            ↓                                                 │
  │  15:00:15  Health check fails → LB marks web-3 DOWN         │
  │            User A retries → LB routes to web-1 (no cookie)  │
  │            ↓                                                 │
  │  15:00:16  Web-1: no session ABC123                         │
  │            → Creates new session → cart empty               │
  │            → User sees "Your cart is empty"                  │
  │            ↓                                                 │
  │  BUSINESS IMPACT: Lost carts, re-authentication required    │
  └──────────────────────────────────────────────────────────────┘
```

### Mitigation

```

── IMMEDIATE: FORCE REMOVE DEAD INSTANCE FROM LB POOL

# Remove dead server immediately (don't wait for health check)
# Nginx:
upstream backend {
    server 10.0.1.50:8080;
    server 10.0.1.51:8080;
    # server 10.0.1.52:8080;  # Commented out — removed
}

$ nginx -s reload

── IMMEDIATE: REDUCE HEALTH CHECK INTERVAL

# Faster failover: check every 2s, fail after 3 failures
# Before: check inter 30s fall 3 → 90s to detect failure
# After:  check inter 2s fall 2  → 4s to detect failure

── IMMEDIATE: USE STATELESS SESSION STORAGE

# Move sessions from local memory to Redis:
spring.session.store-type=redis  # Spring Boot
php-session.save-handler=redis   # PHP
sessionStateProvider=Redis       # ASP.NET

$ kubectl set env deployment/webapp SPRING_SESSION_STORE_TYPE=redis
```

### Permanent Fix

```yaml
# Use external session store (Redis / Memcached)
spring:
  session:
    store-type: redis
  redis:
    host: redis-cluster.example.com
    port: 6379
    timeout: 2000ms

# Remove sticky sessions entirely — apps should be stateless
# AWS ALB: Disable stickiness
# Nginx: Remove ip_hash / sticky directive
# HAProxy: Remove cookie directive
```

---

## Scenario C: Circuit Breaker Cascade — One Slow Upstream → Timeout to LB → Cascade Failure

### Symptom

```
16:00:00  Payment service (payments-svc) experiences slowdown (DB contention)
16:00:05  Payment response time: 200ms → 5s (normal threshold: 2s)
16:00:10  Orders API calls payments-svc → timeout (2s LB timeout)
16:00:15  Orders API: tomcat thread pool saturates with waiting payment calls
16:00:20  Orders API health check: returns 503 (thread pool exhausted)
16:00:25  LB marks orders-api backends as unhealthy (health check fails)
16:00:30  All traffic to orders-api stops — orders service FULLY DOWN
16:00:35  Fallback: orders-api directly calls DB (bypassing payments)
16:00:40  DB gets 10x normal traffic → DB overload → ALL services slow
16:00:45  Full system outage
```

### Detection

```
Alert: Upstream response time p99 > timeout threshold
Alert: Health check failures for backend pool
Alert: Thread pool exhaustion on application servers
Alert: DB query rate spike > 5x normal
Alert: Circuit breaker open for payments-svc calls
Alert: Error propagation — errors in upstream services increase

# Tracing (Jaeger / Zipkin):
orders-api → payments-svc: 95% of spans show timeout errors
root cause: payments-svc response time 5s (DB contention)
```

### Root Cause

```
CIRCUIT BREAKER CASCADE DIAGRAM
════════════════════════════════

  ┌──────────┐    ┌──────────┐    ┌────────────┐
  │  Client  │───>│  Orders  │───>│  Payments  │
  │          │    │  API     │    │  Service   │
  └──────────┘    └──────────┘    └────────────┘
                       │                │
                       │                ▼
                       │          ┌────────────┐
                       │          │  DB        │
                       │          │  (contention│
                       │          └────────────┘
                       │
                       ▼
                  ┌──────────┐
                  │  DB      │
                  │  (direct  │
                  │  fallback)│
                  └──────────┘

  SEQUENCE:
  1. payments-svc slows down (DB lock contention)
  2. orders-api calls payments-svc → timeout (2s)
  3. orders-api threads WAIT for 2s per call
  4. Orders API thread pool (100 threads) fills up in ~10s
  5. Orders API can't process ANY request (threads all blocked)
  6. Orders API health check returns 503 (can't even check health)
  7. LB marks ALL orders-api backends as unhealthy
  8. Orders API traffic goes to ZERO → orders-svc DOWN
  9. Fallback: client calls DB directly (desperate measure)
  10. DB gets 10x load → DB also overloaded
  11. All downstream services now timeout → FULL CASCADE
```

### Mitigation

```

── IMMEDIATE: INCREASE TIMEOUTS TEMPORARILY

# Nginx — longer timeout for payments upstream:
location /payments/ {
    proxy_pass http://payments-svc;
    proxy_read_timeout 10s;    # Was 2s
    proxy_connect_timeout 5s;
}

── IMMEDIATE: DRAIN AFFECTED BACKENDS

# Remove unhealthy backends manually:
$ vi /etc/nginx/conf.d/upstreams.conf
upstream orders-api {
    server 10.0.1.50:8080 max_fails=3 fail_timeout=30s;
    # server 10.0.1.51:8080;  # Temporarily remove slow ones
}

── IMMEDIATE: RESTART SLOW SERVICE

$ kubectl rollout restart deployment payments-svc

── IMMEDIATE: ADD CIRCUIT BREAKER (client-side)

# In Java (Resilience4j):
@CircuitBreaker(name = "payments-svc", fallbackMethod = "paymentFallback")
public PaymentResponse processPayment(PaymentRequest request) {
    return paymentsClient.processPayment(request);
}

public PaymentResponse paymentFallback(PaymentRequest request, Throwable t) {
    log.warn("payments-svc unavailable, using fallback", t);
    return PaymentResponse.fallback(request.getOrderId());
}
```

### Permanent Fix

```yaml
# Server-side timeout configuration (HAProxy)
backend payments-svc
    option httpchk GET /health
    timeout server 5s
    timeout connect 3s
    timeout http-request 30s
    retries 2
    server pay-1 10.0.1.60:8080 check inter 5s fall 3 rise 2

# Application-level circuit breaker (Resilience4j)
resilience4j:
  circuitbreaker:
    configs:
      default:
        slidingWindowSize: 10
        minimumNumberOfCalls: 5
        failureRateThreshold: 50
        waitDurationInOpenState: 10s
        permittedNumberOfCallsInHalfOpenState: 3
        automaticTransitionFromOpenToHalfOpenEnabled: true
    instances:
      payments-svc:
        baseConfig: default
      inventory-svc:
        baseConfig: default

# Bulkhead — limit concurrent calls per service
resilience4j:
  bulkhead:
    instances:
      payments-svc:
        maxConcurrentCalls: 10
        maxWaitDuration: 100ms

# Retry with exponential backoff
resilience4j:
  retry:
    instances:
      payments-svc:
        maxAttempts: 3
        waitDuration: 500ms
        exponentialBackoffMultiplier: 2
```

---

## Scenario D: DNS Resolution Failure — LB DNS Record TTL Too High → Failover Slow

### Symptom

```
08:00:00  Primary LB (10.0.1.10) fails — network failure
08:00:05  DNS record updated: api.example.com → 10.0.1.11 (backup LB)
08:00:10  But TTL = 300 seconds (5 min)
08:00:15  Users still resolving to 10.0.1.10 → connection refused
08:00:30  Clients retry... still get cached 10.0.1.10
08:01:00  ~20% of clients have refreshed DNS → working
08:03:00  ~50% of clients working
08:05:00  TTL expires → all clients eventually get new IP
08:05:00  Total outage duration: 5 minutes (DNS propagation delay)
```

### Detection

```

── IDENTIFY DNS ISSUE

$ dig api.example.com
;; ANSWER SECTION:
api.example.com. 300 IN A 10.0.1.10  ← OLD IP (stale)
# TTL = 300s = 5 min ← too high

── CHECK DNS PROPAGATION

$ dig api.example.com @ns1.cloudflare.com  # Authoritative
api.example.com. 60 IN A 10.0.1.11  ← Correct IP (updated)

$ dig api.example.com @8.8.8.8              # Google DNS
api.example.com. 240 IN A 10.0.1.10  ← Cached (stale)

── CHECK CLIENT-SIDE DNS RESOLUTION (Java)

# Java DNS cache:
$ java -Dnetworkaddress.cache.ttl=30 App
# Default JVM DNS TTL: 30 seconds (successful lookup)
# Default JVM negative DNS TTL: 10 seconds (failed lookup)
# BUT: security property can override: networkaddress.cache.ttl=30
```

### Root Cause

```

DNS FAILOVER TIMELINE
══════════════════════

  ┌──────────────────────────────────────────────────────────────┐
  │  t=0s: Primary LB fails                                      │
  │  ↓                                                           │
  │  t=5s: DNS record updated (TTL=300)                          │
  │  ↓                                                           │
  │  t=0-300s: DNS PROPAGATION WINDOW                            │
  │  ┌──────────────────────────────────────────────────────┐    │
  │  │  During this window:                                 │    │
  │  │  • All clients with cached DNS point to dead LB      │    │
  │  │  • Clients retry cached IP for up to 300s            │    │
  │  │  • DNS resolvers (ISP, 8.8.8.8) may cache longer     │    │
  │  │  • Result: extended outage                           │    │
  │  └──────────────────────────────────────────────────────┘    │
  │  ↓                                                           │
  │  t=300s: All TTLs expired → all clients get new IP          │
  │  ↓                                                           │
  │  t=300s: Full recovery (BUT: 5-minute outage)               │
  └──────────────────────────────────────────────────────────────┘

  WHY TTL WAS HIGH:
  • DNS record for production LB: TTL=300 (best practice is 60)
  • TTL=300 chosen to reduce DNS query volume
  • But this trades off failover speed for query reduction
```

### Mitigation

```

── IMMEDIATE: REDUCE DNS TTL

# Update DNS record with low TTL:
$ curl -X PATCH "https://api.cloudflare.com/client/v4/zones/.../dns_records/..." \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ttl": 60}'

── IMMEDIATE: USE ANYCAST VIP WITH BGP

# Instead of DNS-based failover, use anycast VIP:
# Single IP address announced from multiple locations via BGP
# BGP convergence: 30-90 seconds (vs 300s DNS TTL)

── IMMEDIATE: IMPLEMENT ACTIVE DNS HEALTH CHECKING

# Use DNS-based load balancing with health checks:
# Route53: DNS failover with health checks
# Traffic Director: gRPC health checking + DNS updates
```

### Permanent Fix

```yaml
# DNS configuration
api.example.com:
  type: A
  ttl: 60                        # 60 seconds max for failover speed
  failover: active-passive
  primary: 10.0.1.10
  secondary: 10.0.1.11
  health_check:
    type: HTTP
    path: /health
    interval: 10s
    timeout: 5s
    threshold: 3

# Anycast VIP with BGP
# Use Route Health Injection (RHI):
# When LB fails → withdraw BGP route → immediate convergence
routing:
  protocol: BGP
  asn: 65001
  vip: 203.0.113.10
  health-check:
    - "if LB health check fails → withdraw /32 route"
    - "BGP convergence: ~30s (vs 300s DNS)"

# Client-side DNS TTL configuration
# Java:
java -Dnetworkaddress.cache.ttl=10 -Dnetworkaddress.cache.negative.ttl=5

# Application code — respect DNS TTL:
import java.security.Security;
Security.setProperty("networkaddress.cache.ttl", "10");
```

---

## Scenario E: Cross-Region Failover — Primary Region Fails → Slow DNS Update → Extended Outage

### Symptom

```
Primary region (us-east-1) experiences full AZ failure.
DNS-based failover to us-west-2 is configured.

09:00:00  us-east-1 AZ failure — multiple services down
09:00:05  Route53 health check detects failure
09:00:10  Route53 updates DNS: api.example.com → us-west-2 LB IP
09:00:15  BUT: many clients have DNS cached (TTL=60s)
09:00:30  US-East clients in AWS: some still resolving to old IP
09:01:00  TTL expires → most clients get new IP
09:01:30  BUT: some corporate DNS servers ignore TTL (cache for 30 min+)
09:03:00  Still seeing some traffic to dead us-east-1 endpoint
09:05:00  ~95% of traffic shifted to us-west-2
09:10:00  Remaining 5% of users still hitting dead endpoint
```

### Detection

```

── CHECK DNS PROPAGATION STATUS

$ dig api.example.com @8.8.8.8
api.example.com. 45 IN A 10.0.1.10  ← Still resolving to old IP

$ dig api.example.com @1.1.1.1
api.example.com. 45 IN A 10.0.1.10  ← Same

$ dig api.example.com @ns-xxx.awsdns-xx.net  ← Authoritative
api.example.com. 60 IN A 10.0.1.11  ← Correct (us-west-2 IP)

── CHECK CLIENT TRAFFIC DISTRIBUTION

# Traffic still hitting us-east-1 LB:
$ aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name RequestCount \
  --dimensions Name=LoadBalancer,Value=app/us-east-1-lb/... \
  --statistics Sum \
  --period 60

# Should be near zero after failover
# If not: DNS propagation issue
```

### Root Cause

```

CROSS-REGION FAILOVER TIMELINE
═══════════════════════════════

  ┌──────────────────────────────────────────────────────────────┐
  │  us-east-1 AZ FAILURE                                        │
  │      ↓                                                       │
  │  Route53 health check (every 10s): 3 consecutive failures   │
  │      ↓ (30s to detect)                                       │
  │  DNS failover triggered                                      │
  │      ↓                                                       │
  │  Authoritative DNS updated immediately                       │
  │      ↓                                                       │
  │  ┌──────────────────────────────────────────────────────┐    │
  │  │  PROPAGATION DELAYS:                                │    │
  │  │                                                     │    │
  │  │  1. ISP DNS resolver cache: TTL=60s → up to 60s    │    │
  │  │  2. Corporate DNS proxy: ignore TTL → 30+ minutes  │    │
  │  │  3. JVM DNS cache: default 30s                      │    │
  │  │  4. Java Security: networkaddress.cache.ttl=30      │    │
  │  │  5. Browser DNS cache: varies (Chrome: 60s)         │    │
  │  │  6. OS DNS cache: varies (Linux nscd: 60s)         │    │
  │  └──────────────────────────────────────────────────────┘    │
  │      ↓                                                       │
  │  Extended outage for users with aggressive DNS caching       │
  └──────────────────────────────────────────────────────────────┘
```

### Mitigation

```

── IMMEDIATE: USE APPLICATION-LAYER REDIRECT

# Old LB still running? Deploy redirect rule:
# Nginx on old LB:
server {
    listen 443;
    server_name api.example.com;
    return 301 https://api-us-west.example.com$request_uri;
}

── IMMEDIATE: FLOOD DNS CACHES WITH LOW TTL

# Push DNS update with very low TTL repeatedly:
$ for i in 1 2 3; do
  aws route53 change-resource-record-sets \
    --hosted-zone-id ZONEID \
    --change-batch '{
      "Changes": [{
        "Action": "UPSERT",
        "ResourceRecordSet": {
          "Name": "api.example.com.",
          "Type": "A",
          "TTL": 30,
          "ResourceRecords": [{"Value": "203.0.113.10"}]
        }
      }]
    }'
  sleep 5
done

── IMMEDIATE: CONTACT CLIENTS TO FLUSH DNS

# Internal: ask teams to flush DNS
# External: post status page, advise users
```

### Permanent Fix

```yaml
# Multi-region failover architecture
global:
  regions:
    - name: us-east-1
      lb: arn:aws:elasticloadbalancing:us-east-1:...:loadbalancer/app/...
      health_check: /health
    - name: us-west-2
      lb: arn:aws:elasticloadbalancing:us-west-2:...:loadbalancer/app/...

  dns:
    ttl: 30                        # Aggressive TTL
    routing: latency-based          # Route to lowest-latency region
    failover: active-passive        # us-east-1 primary, us-west-2 backup
    health_check:
      type: HTTP
      path: /deep-health            # Checks DB, cache, dependencies
      interval: 5s
      threshold: 3

  anycast:                          # Optional: BGP-based failover
    vip: 203.0.113.10
    asn: 65001
    rhi: enabled                    # Route Health Injection

# Client-side DNS configuration:
# Java system properties:
#   -Dnetworkaddress.cache.ttl=10
#   -Dnetworkaddress.cache.negative.ttl=3

# Kubernetes pod DNS config:
# pod.spec.dnsConfig:
#   options:
#   - name: ndots
#     value: "1"
#   - name: single-request-reopen
#     value: ""

# Application-level retry with region fallback:
class CrossRegionClient:
    def __init__(self):
        self.regions = [
            "https://api.us-east-1.example.com",
            "https://api.us-west-2.example.com",
        ]

    def request(self, path, retries=3):
        for region in self.regions:
            try:
                return http.get(f"{region}{path}", timeout=2)
            except (ConnectionError, TimeoutError):
                continue
        raise AllRegionsFailed()
```

---

## Detection and Monitoring Reference

### Critical LB Metrics

| Metric | Source | Warning | Critical |
|--------|--------|---------|----------|
| `active_connections / maxconn` | Nginx/HAProxy | > 80% | > 95% |
| `upstream_response_time p99` | Nginx/HAProxy | > 1s | > 5s |
| `upstream_server_checks_failing` | Nginx/HAProxy | > 0 | > 50% |
| `error_rate (5xx)` | Nginx access log | > 1% | > 5% |
| `CLOSE_WAIT connections` | `ss -tan` | > 100 | > 1000 |
| `SYN backlog overflow` | `netstat -s` | > 0 | > 100/min |
| `Health check failure rate` | LB telemetry | > 10% | > 50% |
| `DNS TTL vs actual failover time` | Dig + monitoring | > 60s | > 300s |

### HAProxy Stats

```bash
# HAProxy statistics
$ echo "show stat" | socat /var/run/haproxy.sock stdio | \
  awk -F',' '{print $1, $2, $5, $6, $7, $8, $18, $19, $36}'

# Key columns:
# $5 = current queued requests (qcur)
# $6 = max queued (qmax)
# $7 = current sessions (scur)
# $8 = max sessions (smax)
# $18 = current server state (0=down, 1=up)
# $19 = weight
# $36 = last health check status (L7OK, L7STS, L4OK, L4TOUT)
```

---

## Mitigation Playbook

### Connection Exhaustion

```
1. CHECK: ss -tan | grep :443 | awk '{print $1}' | sort | uniq -c
2. INCREASE: maxconn temporarily (worker_connections, maxconn)
3. ADD: Rate limiting at LB level
4. DEDICATE: Separate health check port from traffic port
5. FIX: Keepalive timeout matching between LB and backend
6. PREVENT: Connection pooling, connection limits per backend
```

### Sticky Session Failure

```
1. REMOVE: Delete dead backend from upstream config
2. REPAIR: Reduce health check interval to 2s
3. MIGRATE: Move sessions to external store (Redis)
4. ELIMINATE: Remove sticky session dependency — make apps stateless
```

### Circuit Breaker Cascade

```
1. RESTART: Restart the slow service
2. INCREASE: Timeouts temporarily to stop cascade
3. ADD: Circuit breaker pattern to client code
4. ISOLATE: Bulkhead pattern (limit concurrent calls per service)
5. PREVENT: Health check must check dependencies (deep health)
```

### DNS Failover

```
1. UPDATE: Reduce TTL to 30-60s
2. VERIFY: Check authoritative DNS vs resolver caches
3. REDIRECT: Application-layer redirect from old VIP
4. FLOOD: Push DNS update with low TTL repeatedly
5. PREVENT: Use anycast VIP + BGP RHI for sub-minute failover
```

---

## Lessons Learned

1. **Health check connections must use a separate port** from application traffic to avoid health check failures during connection exhaustion.
2. **Sticky sessions couple users to instances.** Stateless applications are more resilient — use external session stores.
3. **Circuit breakers and bulkheads prevent cascading failures.** One slow service should not bring down the entire system.
4. **DNS TTL directly impacts failover speed.** A TTL of 300 seconds means up to 5 minutes of extended outage during DNS failover.
5. **JVM DNS caching ignores TTL by default.** Java applications cache DNS for 30 seconds (success) and 10 seconds (failure) — configure via `networkaddress.cache.ttl`.
6. **Health check endpoints should perform deep checks** (DB connectivity, cache connectivity, disk space) to accurately represent service health.
7. **CLOSE-WAIT connection accumulation indicates application bugs.** Backend is not closing connections properly — check keepalive timeout matching and FD leaks.
8. **Test failover scenarios regularly.** A DNS failover that works in theory may fail when the primary region actually goes down.
9. **Rate limiting at the LB protects backends from traffic spikes.** Always configure rate limiting zones.
10. **Use both L4 (NLB) and L7 (ALB/Nginx) load balancers** in layers — NLB for high-throughput connection handling, ALB for intelligent routing.
