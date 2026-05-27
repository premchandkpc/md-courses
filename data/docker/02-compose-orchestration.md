# 🐳 Docker Compose & Orchestration — Complete Deep Dive

**Related**: [Container Basics](01-container-basics.md) · [Kubernetes Basics](../kubernetes/01-kubernetes-basics.md) · [Compose Spec](https://compose-spec.io)

---

## Table of Contents

- [docker-compose.yml](#-docker-composeyml)
- [Services](#-services)
- [Networks](#-networks)
- [Volumes](#-volumes)
- [depends_on](#-depends_on)
- [Healthcheck](#-healthcheck)
- [Profiles](#-profiles)
- [Replicas & Deploy Config](#-replicas--deploy-config)
- [Secrets & Configs](#-secrets--configs)
- [Environment Variables](#-environment-variables)
- [Logging Drivers](#-logging-drivers)
- [Restart Policies](#-restart-policies)
- [Compose Watch](#-compose-watch)
- [Docker Swarm Stack Deploy](#-docker-swarm-mode-stack-deploy)
- [Simplest Mental Model](#-simplest-mental-model)

---

## 🧭 docker-compose.yml

### Structure Overview

```yaml
version: "3.9"                              # Compose file format version

name: myapp                                  # Project name (v2.1+)

services:                                    # Define containers
  web:
    build: ./web
    ports:
      - "8080:80"
    # ...

networks:                                    # Define networks
  frontend:
  backend:

volumes:                                     # Define named volumes
  postgres-data:
  redis-data:

secrets:                                     # Define secrets
  db_password:
    file: ./secrets/db_password.txt

configs:                                     # Define configs
  nginx_config:
    file: ./nginx.conf

x-common: &common                            # YAML anchors for reuse
  restart: unless-stopped
  logging:
    driver: json-file
    options:
      max-size: "10m"
      max-file: "3"
```

### File Resolution Order

```text
Compose resolves config from multiple sources (each overrides previous):

1. Default values
2. docker-compose.yml
3. docker-compose.override.yml  (auto-loaded if exists)
4. -f docker-compose.prod.yml   (explicit file flags)
5. --env-file .env              (environment variable substitution)
6. Environment variables (shell) — highest priority

Usage:
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up
  docker compose --env-file .env.prod up
```

---

## 🧭 Services

### Service Definition

```yaml
services:
  api:
    build:                                      # Build from Dockerfile
      context: .
      dockerfile: Dockerfile.api
      args:                                     # Build args
        NODE_ENV: production
      target: production                        # Multi-stage target
      cache_from:
        - myapp/api:latest
      labels:
        - "com.example.service=api"

    image: myapp/api:latest                     # Image name (or use for pull)

    ports:                                      # Port mappings
      - "8080:80"                               # host:container
      - "443:443"
      - "9090-9100:9090-9100"                   # Range
      - target: 80
        published: 8080
        protocol: tcp
        mode: host                              # host = bypass routing mesh

    expose:                                     # Expose to linked services only
      - "3000"

    command: ["node", "--max-old-space-size=512", "server.js"]
    entrypoint: ["/docker-entrypoint.sh"]
    user: "1000:1000"

    working_dir: /app
    container_name: my-api                      # Fixed name (can't scale)
    hostname: api.example.com

    dns:                                        # Custom DNS
      - 8.8.8.8
      - 1.1.1.1
    dns_search: example.com

    extra_hosts:                                # /etc/hosts entries
      - "host.docker.internal:host-gateway"
      - "db.internal:10.0.0.5"

    init: true                                  # Use init process (tini)
    stdin_open: true                            # -i
    tty: true                                   # -t

    sysctls:                                    # Kernel parameters
      - net.core.somaxconn=1024
      - net.ipv4.tcp_syncookies=0

    cap_add:                                    # Extra capabilities
      - NET_BIND_SERVICE
    cap_drop:
      - ALL
    privileged: false
    security_opt:
      - seccomp:custom-profile.json
      - no-new-privileges:true
```

---

## 🧭 Networks

### Network Definitions

```yaml
services:
  web:
    networks:
      frontend:                                 # With custom IP
        ipv4_address: 172.20.0.10
        aliases:
          - web.local                           # DNS alias
      backend:

  db:
    networks:
      backend:
        aliases:
          - db-primary

networks:
  frontend:
    driver: bridge                              # Single host
    ipam:
      config:
        - subnet: 172.20.0.0/24
          gateway: 172.20.0.1

  backend:
    driver: overlay                             # Swarm mode
    attachable: true                            # Standalone containers can join
    internal: true                              # No external access
    driver_opts:
      encrypted: "true"                         # IPSec encryption

  public:
    external: true                              # Use pre-existing network
    name: production-network
```

### Network Modes

```yaml
services:
  host-mode:
    network_mode: host                          # Share host network stack
    # No port mapping needed — uses host ports directly

  none-mode:
    network_mode: none                          # No network access

  service-mode:
    network_mode: "service:proxy"               # Share another service's network

  bridge-default:
    # network_mode defaults to bridge
    # Can reach: other services on same network, internet (via NAT)
```

---

## 🧭 Volumes

### Volume Definitions

```yaml
services:
  postgres:
    image: postgres:16
    volumes:
      - pg-data:/var/lib/postgresql/data       # Named volume
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro  # Bind mount read-only
      - type: volume
        source: pg-config
        target: /etc/postgresql
        read_only: true
        volume:
          nocopy: true                          # Don't copy from container on first use

  nginx:
    volumes:
      - type: bind
        source: ./html
        target: /usr/share/nginx/html
        bind:
          propagation: rshared                  # Bind propagation

      - type: tmpfs
        target: /cache
        tmpfs:
          size: 64M
          mode: 0700

volumes:
  pg-data:
    driver: local
    driver_opts:
      type: nfs
      o: addr=192.168.1.100,rw,nfsvers=4
      device: ":/path/to/data"

  pg-config:
    external: true                             # Volume exists already
    name: myapp-postgres-config

  cache:
    driver: local
    labels:
      - "env=production"
```

---

## 🧭 depends_on

### Dependency Control

```yaml
services:
  web:
    build: .
    depends_on:
      db:
        condition: service_healthy             # Wait for healthy
      redis:
        condition: service_started             # Default — just started
      migrations:
        condition: service_completed_successfully  # Wait for exit code 0

  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U myapp"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 30s

  redis:
    image: redis:7-alpine

  migrations:
    build: ./migrations
    depends_on:
      db:
        condition: service_healthy
```

```text
depends_on behavior:

  WITHOUT condition (default):
    web starts after db container starts (but db may not be ready!)
    Race condition: web starts, db is still initializing

  WITH service_healthy:
    web starts only when db healthcheck passes
    Safe startup order — but requires healthcheck on dependency

  WITH service_completed_successfully:
    web waits for migrations to run and exit with code 0
    Use for: schema migrations, seed data scripts

  Dependency graph:
    migrations ────> db (healthy)
    web ────────────> db (healthy)
    web ────────────> redis (started)
    web ────────────> migrations (completed)
```

---

## 🧭 Healthcheck

### Configuration

```yaml
services:
  web:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      # Alternative forms:
      # test: curl -f http://localhost/health || exit 1          # Shell form
      # test: ["CMD-SHELL", "pg_isready -U myapp"]                # Shell in exec
      # test: ["NONE"]                                           # Disable inherited
      interval: 30s             # Check every 30s
      timeout: 10s              # Max time for single check
      retries: 3                # Consecutive failures before unhealthy
      start_period: 40s         # Wait before first check (startup grace)
      start_interval: 5s        # Check interval during start period (v3.9+)

  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
```

### Container States

```text
Container Lifecycle with Healthcheck:

  ┌──────────────┐
  │   CREATED     │  docker compose create
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │   STARTING    │  docker compose start
  │ (start_period)│  ───  healthchecks run but don't count failures
  └──────┬───────┘
         ▼ (first check passes after start_period)
  ┌──────────────┐
  │   HEALTHY     │  Normal operation
  └──────┬───────┘
         │ (3 consecutive failures)
         ▼
  ┌──────────────┐
  │  UNHEALTHY    │  Container still running, but marked unhealthy
  │               │  depends_on waits for healthy
  └──────────────┘

Check status: docker compose ps
               docker inspect <container> | jq '.[0].State.Health'
```

---

## 🧭 Profiles

### Profile-Based Service Selection

```yaml
services:
  web:
    build: .
    profiles: []                               # Always started (empty or absent)

  db:
    image: postgres:16
    # No profiles — always started

  redis:
    image: redis:7-alpine
    profiles: ["core"]                         # Started with --profile core

  mailhog:
    image: mailhog/mailhog
    profiles: ["dev"]                          # Only in dev profile

  adminer:
    image: adminer
    profiles: ["dev", "tools"]                 # Multiple profiles

  jaeger:
    image: jaegertracing/all-in-one
    profiles: ["debug", "tracing"]

  kafka:
    image: confluentinc/cp-kafka
    profiles: ["debug"]
```

```bash
# Without profile — only services without profiles
docker compose up

# With profile(s)
docker compose --profile dev up
docker compose --profile dev --profile debug up
docker compose --profile "*" up              # All services

# Check which services are enabled
docker compose config --services

# Use cases:
#   dev profile: mailhog, adminer, hot-reload config
#   debug profile: jaeger, kafka, redis-insight
#   tools profile: cron jobs, backup agents
#   ci profile: minimal services for CI pipeline
```

---

## 🧭 Replicas & Deploy Config

### Deploy Section (Swarm Mode)

```yaml
services:
  web:
    image: myapp/web:latest
    deploy:
      mode: replicated                          # replicated (default) or global
      replicas: 3                               # For replicated mode

      placement:
        constraints:                            # Where to schedule
          - node.role == worker                 # Only worker nodes
          - node.labels.env == production       # Label matching
          - node.platform.os == linux
        preferences:                            # Spread strategy
          - spread: node.labels.zone            # Spread across zones
        max_replicas_per_node: 2                 # Limit per node

      resources:
        limits:                                 # Hard limits
          cpus: "0.50"
          memory: 512M
        reservations:                           # Guaranteed minimum
          cpus: "0.25"
          memory: 256M

      restart_policy:
        condition: any                          # any, on-failure, none
        delay: 5s
        max_attempts: 3
        window: 120s

      update_config:
        parallelism: 2                          # Update 2 at a time
        delay: 10s                              # Wait between batches
        failure_action: rollback                # rollback, pause, continue
        monitor: 60s                            # Monitor after update
        max_failure_ratio: 0.3                  # 30% max failures
        order: start-first                      # start-first, stop-first

      rollback_config:
        parallelism: 1
        delay: 5s
        failure_action: pause
        monitor: 30s
        order: stop-first

      labels:
        - "com.example.service=web"
        - "com.example.environment=production"

  worker:
    image: myapp/worker:latest
    deploy:
      mode: global                              # One per node
      # Useful for: log collectors, monitoring agents, node-level daemons
```

---

## 🧭 Secrets & Configs

### Secrets

```yaml
services:
  web:
    secrets:
      - db_password                             # Mount at /run/secrets/db_password
      - source: api_key
        target: /etc/secrets/api_key            # Custom path
        uid: "1000"                             # File ownership
        gid: "1000"
        mode: 0400                              # File permissions

  db:
    secrets:
      - db_password

secrets:
  db_password:
    file: ./secrets/db_password.txt             # From file
    # OR from external (Swarm):
    # external: true
    # name: swarm_secret_db_password

  api_key:
    environment: API_KEY                        # From env var
    # OR:
    # external: true
    # name: swarm_secret_api_key
```

### Configs

```yaml
services:
  nginx:
    configs:
      - source: nginx_config
        target: /etc/nginx/nginx.conf
        uid: "101"
        mode: 0440

  prometheus:
    configs:
      - source: prometheus_config
        target: /etc/prometheus/prometheus.yml

configs:
  nginx_config:
    file: ./nginx.conf
  prometheus_config:
    file: ./prometheus.yml
  # Swarm external:
  #   external: true
  #   name: swarm_prometheus_config
```

### Secrets vs Configs

```text
SECRETS:
  • Sensitive data (passwords, keys, certs)
  • Written to tmpfs in-memory (not on disk)
  • File permissions: 0400 by default
  • /run/secrets/<name> by default
  • Encrypted at rest in Swarm (Raft log)

CONFIGS:
  • Non-sensitive config (config files, templates)
  • Written to tmpfs (same as secrets)
  • Same mechanism as secrets
  • Use: nginx.conf, prometheus.yml, logback.xml
```

---

## 🧭 Environment Variables

### Variable Sources

```yaml
services:
  web:
    # 1. Inline key=value
    environment:
      NODE_ENV: production
      PORT: "8080"

    # 2. List format
    environment:
      - NODE_ENV=production
      - PORT=8080

    # 3. From .env file (interpolation)
    environment:
      - DB_HOST=${DB_HOST:-localhost}
      - DB_PORT=${DB_PORT:-5432}
      - APP_VERSION=${BUILD_VERSION:-latest}

    # 4. env_file
    env_file:
      - ./common.env
      - ./app.env                      # Later files override earlier

    # 5. Variable expansion in compose.yml
    image: myapp:${TAG:-latest}

    # 6. From shell environment (no default)
    environment:
      - AWS_SECRET_ACCESS_KEY          # Read from shell without value
```

### .env File

```bash
# .env — placed next to docker-compose.yml, loaded automatically
COMPOSE_PROJECT_NAME=myapp
TAG=latest
DB_HOST=prod-db.example.com
DB_PORT=5432
NODE_ENV=production
LOG_LEVEL=warn
```

### Precedence

```text
Variable Substitution Priority (highest to lowest):

  1. Shell environment variables  ← highest priority
  2. --env-file file contents
  3. .env file (automatic)
  4. Compose file defaults (${VAR:-default})
  5. Empty string                 ← lowest priority
```

---

## 🧭 Logging Drivers

### Available Drivers

```yaml
services:
  web:
    logging:
      driver: json-file                         # Default
      options:
        max-size: "10m"                         # Rotate at 10MB
        max-file: "3"                           # Keep 3 rotated files
        compress: "true"                        # Gzip rotated logs

  fluentd:
    image: myapp/fluentd
    logging:
      driver: fluentd
      options:
        fluentd-address: localhost:24224
        tag: "{{.Name}}/{{.ID}}"               # Template for log tag

  awslogs:
    logging:
      driver: awslogs
      options:
        awslogs-region: us-east-1
        awslogs-group: myapp
        awslogs-stream: web
        awslogs-create-group: "true"

  syslog:
    logging:
      driver: syslog
      options:
        syslog-address: "tcp://192.168.1.100:514"
        syslog-facility: local0
        tag: "{{.Name}}"

  gelf:
    logging:
      driver: gelf
      options:
        gelf-address: "udp://192.168.1.100:12201"
        tag: "web"

  none:
    logging:
      driver: none                              # Completely disable logging
```

### Logging Drivers Comparison

| Driver | Use Case | Pros | Cons |
|--------|----------|------|------|
| json-file | Local dev | Simple, default | No aggregation, uses disk |
| journald | Systemd systems | Integrated logging | Linux only |
| syslog | Legacy infrastructure | Standard protocol | UDP unreliable |
| fluentd | Aggregation pipeline | Rich routing, plugins | Extra infrastructure |
| awslogs | AWS ECS | Direct to CloudWatch | AWS vendor lock |
| gelf | Graylog | Structured JSON | Extra infrastructure |
| splunk | Splunk users | Direct to Splunk | Splunk license cost |
| none | Debug/CI | Zero overhead | No logs at all |

---

## 🧭 Restart Policies

### Policies

```yaml
services:
  web:
    restart: unless-stopped              # Most common for production

  worker:
    restart: on-failure                  # Only restart on crash
    restart: on-failure:5                # Max 5 retries (compose v2.18+)

  cron:
    restart: no                          # Don't restart (run once)

  db:
    restart: always                      # Always restart, even if stopped manually
```

```text
Restart Policy Behavior:

  no             ──  Never restart (default)
  always         ──  Always restart, even after manual stop or daemon restart
  on-failure     ──  Restart only if exit code ≠ 0
  unless-stopped ──  Restart always, EXCEPT if manually stopped

  Container exit codes:
    0    = Normal exit (won't restart with on-failure)
    1    = Error / crash
    137  = SIGKILL (OOM killed)
    143  = SIGTERM (docker stop)
```

---

## 🧭 Compose Watch

### Hot Reload (v2.22+)

```yaml
services:
  web:
    image: node:18-alpine
    working_dir: /app
    command: npm run dev                        # Dev server with hot reload
    ports:
      - "3000:3000"
    develop:                                    # Compose Watch config
      watch:
        - action: sync                          # Sync changed files
          path: ./src
          target: /app/src
          ignore:
            - node_modules/
            - .test.ts

        - action: rebuild                       # Rebuild + restart
          path: package.json                    # Deps changed
          ignore:
            - node_modules/

        - action: sync+restart                  # Sync files, then restart process
          path: ./config
          target: /app/config

  db:
    image: postgres:16
    develop:
      watch:
        - action: rebuild
          path: ./init.sql
```

```bash
# Start with file watching
docker compose up --watch

# Watches files and executes actions:
#   sync        → Copy files into the container (fast, no restart)
#   rebuild     → Rebuild image + recreate container
#   sync+restart → Sync files + restart container process
```

---

## 🧭 Docker Swarm Mode Stack Deploy

### Stack File

```yaml
# docker-stack.yml — production deployment to Swarm
version: "3.9"

services:
  web:
    image: registry.myapp.com/web:${TAG}
    ports:
      - target: 80
        published: 80
        mode: host                         # Direct port (no routing mesh)
    networks:
      - traefik-net
    environment:
      - NODE_ENV=production
    secrets:
      - db_password
    deploy:
      mode: replicated
      replicas: 5
      resources:
        limits:
          cpus: "0.5"
          memory: 512M
      update_config:
        parallelism: 2
        delay: 10s
        order: start-first
      rollback_config:
        parallelism: 1
      restart_policy:
        condition: any
      placement:
        constraints:
          - node.role == worker
          - node.labels.env == production

  db:
    image: postgres:16
    volumes:
      - pg-data:/var/lib/postgresql/data
    networks:
      - internal
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    deploy:
      mode: replicated
      replicas: 2
      placement:
        constraints:
          - node.labels.type == database
      resources:
        reservations:
          memory: 1G

networks:
  traefik-net:
    driver: overlay
    external: true
  internal:
    driver: overlay
    internal: true

volumes:
  pg-data:
    driver: local

secrets:
  db_password:
    external: true
    name: swarm_db_password
```

### Stack vs Compose

```text
Key differences when deploying as stack:

  Feature              docker compose           docker stack
  ─────────────────────────────────────────────────────────────
  build                ✓                        ✗ (pre-built images only)
  container_name       ✓                        ✗ (auto-generated)
  depends_on           ✓                        ✗ (use healthcheck)
  deploy.resources     ignored                  ✓ (enforced)
  deploy.replicas      ignored                  ✓
  restart              ✓                        ✗ (use deploy.restart_policy)
  ports (host mode)    ✓                        ✓
  links                ✓                        ✗ (use networks)
  scale                docker compose up --scale ✓ (docker service scale)
  secrets              file:                     external: true
  configs              file:                     external: true
```

### Stack Commands

```bash
# Deploy stack
docker stack deploy -c docker-stack.yml myapp

# List stacks
docker stack ls

# List services in stack
docker stack services myapp

# List tasks (containers) in stack
docker stack ps myapp

# View service logs
docker service logs myapp_web
docker service logs --tail 100 -f myapp_web

# Scale services
docker service scale myapp_web=10

# Update service
docker service update --image myapp/web:v2 myapp_web
docker service update --env-add NODE_ENV=staging myapp_web

# Rollback
docker service update --rollback myapp_web

# Remove stack
docker stack rm myapp

# Inspect service
docker service inspect --pretty myapp_web
```

---

## 🧠 Simplest Mental Model

```text
DOCKER COMPOSE = Group project instructions (single host)

  Think of docker-compose.yml as a group project plan:
  • Services = team members (each runs a specific task)
  • Networks = which members can talk to each other
  • Volumes = shared whiteboard (data persists even when someone leaves)
  • depends_on = "wait for Bob to finish setup before Alice starts"
  • healthcheck = "Bob, are you ready yet? Okay Alice, go!"
  • profiles = "extra team members only needed for weekend work"

  docker compose up = "Team, let's start working!"
  docker compose down = "Pack up, we're done."

  Compose Watch = Boss watching over your shoulder copying your
  code changes into the container instantly. No rebuild needed.

DOCKER STACK / SWARM = Multi-city deployment

  Swarm is like having the same team in multiple cities:
  • Manager nodes = headquarters (make decisions, Raft voting)
  • Worker nodes = branch offices (run the actual work)
  • Service = the job description, not the person
  • Tasks = individual workers doing the job (containers)
  • Overlay network = company VPN between all offices
  • Rolling update = replace workers one by one, no downtime

  docker stack deploy = "Roll out the new process to all offices."
  docker service scale = "Hire 5 more people for this job."
  docker node drain = "Close this office for renovations."

KEY INSIGHT:
  Compose is for development (build, test, iterate fast).
  Stack/Swarm is for production (scale, update, keep running).

  One compose file CAN serve both — use deploy section for Swarm,
  use build/environment for Compose. The deploy section is ignored by Compose.
```

---

**Next**: [Kubernetes Basics](../kubernetes/01-kubernetes-basics.md)
