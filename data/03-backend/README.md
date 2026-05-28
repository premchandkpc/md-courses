# 03 — Backend Engineering

The art and science of building server-side systems that power applications—APIs, services, data processing, authentication, and integration. Backend engineering covers language-specific mastery, API design, architecture patterns, performance optimization, and production operations.


```mermaid
graph LR
    A["Thread 1"] --> D["Shared<br/>Resource"]
    B["Thread 2"] --> D
    C["Thread 3"] --> D
    D --> E["Mutex/<br/>Lock"]
    style A fill:#4a8bc2
    style B fill:#4a8bc2
    style C fill:#4a8bc2
    style D fill:#c73e1d
    style E fill:#1a5d3a
```

## Table of Contents

- [Languages](#languages)
  - [Java](#java)
  - [Go](#go)
  - [Python](#python)
  - [TypeScript](#typescript)
- [API Design](#api-design)
  - [REST](#rest)
  - [GraphQL](#graphql)
  - [gRPC](#grpc)
- [Backend Patterns](#backend-patterns)
  - [Architecture Patterns](#architecture-patterns)
  - [Design Patterns](#design-patterns)
  - [Concurrency Patterns](#concurrency-patterns)
- [Server Architecture](#server-architecture)
  - [Runtimes & Frameworks](#runtimes--frameworks)
  - [Request Lifecycle](#request-lifecycle)
  - [Connection Management](#connection-management)
- [Performance Engineering](#performance-engineering)
  - [Profiling & Benchmarking](#profiling--benchmarking)
  - [Caching Strategies](#caching-strategies)
  - [Database Performance](#database-performance)
- [Production Operations](#production-operations)
  - [Observability](#observability)
  - [Deployment](#deployment)
  - [Resilience](#resilience)
- [Learning Path](#learning-path)
- [Cross-References](#cross-references)

---

## Languages

### Java

The enterprise standard. Mature ecosystem, strong typing, JVM performance.

- **Core** — OOP, interfaces, abstract classes, generics, annotations, enums; records, sealed classes (Java 17+), pattern matching, virtual threads (Loom)
- **Concurrency** — Thread, Runnable, Callable, Future, CompletableFuture, ExecutorService, ForkJoinPool; synchronized, volatile, Locks, Atomics, Concurrent collections
- **JVM Internals** — class loading, bytecode, JIT compilation (C1/C2), GC (G1, ZGC, Shenandoah), memory model (JMM), heap/stack/metaspace, profiling (JFR, JMC, async-profiler)
- **Ecosystem** — Spring Boot (dominant), Micronaut, Quarkus; Hibernate/JPA, JDBC, Flyway; JUnit 5, Mockito, Testcontainers; Maven/Gradle; Netty, Vert.x
- **Build & Deployment** — Maven/Gradle, shading, multi-module projects; Docker + Jlink (custom JRE), GraalVM native-image

### Go

Cloud-native default. Simplicity, fast compilation, excellent concurrency.

- **Core** — goroutines, channels (buffered/unbuffered), select, sync primitives (Mutex, RWMutex, WaitGroup, Cond, Once, Pool), context, interface composition, error handling
- **Standard Library** — net/http, encoding/json, database/sql, io, sync, context, testing/benchmark; most cloud-native tools are in Go
- **Concurrency Model** — CSP (Communicating Sequential Processes); goroutine scheduling (M:N), work stealing, GOMAXPROCS
- **Performance** — escape analysis, inlining, bounds check elimination, PGO (profile-guided optimization); GC tuning (GOGC, memory limit)
- **Tooling** — go modules, go vet, staticcheck, pprof, trace, delve debugger; wire for DI, sqlc for type-safe SQL

### Python

The versatile workhorse. Data science, ML, scripting, API servers.

- **Core** — duck typing, decorators, generators, context managers, metaclasses, descriptors; typing (PEP 484, Pydantic for validation)
- **Async** — asyncio, event loop, coroutines, tasks, futures, async/await; uvloop for speed; trio (structured concurrency), anyio
- **Web Frameworks** — FastAPI (modern, async-native, OpenAPI auto-docs), Django (batteries-included), Flask (lightweight), Starlette (async core)
- **Data** — NumPy, Pandas, Polars (fast), Dask (distributed), SQLAlchemy, Alembic, psycopg (async)
- **Performance** — profiling (cProfile, py-spy, pyright), C extensions (Cython, C extensions), multiprocessing vs threading vs asyncio
- **Packaging** — pip, poetry, uv (fast), rye, conda; build systems (setuptools, hatch, flit)

### TypeScript

The full-stack language. Typed JavaScript with excellent tooling.

- **Type System** — structural typing, generics, utility types (Partial, Pick, Omit, Record, ReturnType), conditional types, mapped types, template literal types
- **Runtime** — Node.js (V8 libuv, event loop, worker_threads), Deno (secure, TypeScript-native), Bun (fast, built-in bundler/test runner)
- **Frameworks** — NestJS (modular, DI, decorators), Express (minimalist), Fastify (fast, schema-based), Hono (lightweight, multi-runtime)
- **Async** — Promises, async/await, EventEmitter, Streams, backpressure handling
- **Tooling** — tsc, esbuild (bundling), SWC (compilation), Biome/ESLint (linting), Vitest/Jest (testing), Prisma/Drizzle (ORM)

---

## API Design

### REST

Architectural style for networked APIs. Constraint-based: stateless, cacheable, uniform interface.

- **Resource Modeling** — nouns, not verbs; URL structure (collection, item, sub-resource); HATEOAS (links)
- **HTTP Methods** — GET (read), POST (create), PUT (replace), PATCH (partial update), DELETE; idempotency, safety
- **Status Codes** — 200, 201, 204, 400, 401, 403, 404, 409, 422, 429, 500, 502, 503
- **Versioning** — URL path (/v1/), header (Accept-Version), content negotiation
- **Pagination** — cursor-based (recommended), offset-based, keyset pagination; page size limits
- **Validation** — request validation, error response format (RFC 7807 Problem Details), input sanitization
- **Documentation** — OpenAPI/Swagger spec, code-first vs design-first; Stoplight, Redoc

### GraphQL

Query language for APIs. Client specifies exact data needs.

- **Schema** — types, queries, mutations, subscriptions; input types, enums, unions, interfaces, scalars
- **Resolver Pattern** — DataLoader for batching + caching; n+1 prevention; field-level permissions
- **Execution** — root value resolver, field resolver chain; query complexity analysis, depth limiting, cost analysis
- **Federation** — Apollo Federation, GraphQL Mesh; composing multiple subgraphs into one supergraph
- **Performance** — persisted queries, response caching, automatic persisted queries (APQ), deduplication
- **Tooling** — Apollo Server, Yoga, Hot Chocolate; GraphiQL, Apollo Studio, GraphQL Inspector

### gRPC

High-performance RPC using HTTP/2 and Protocol Buffers. Default for microservice communication.

- **Service Definition** — `.proto` files, service + rpc definitions, message types, field numbers, oneof, maps
- **RPC Types** — unary, server-streaming, client-streaming, bidirectional streaming
- **HTTP/2** — multiplexed streams, header compression (HPACK), flow control, stream prioritization
- **Interceptors** — client/server middleware for logging, auth, metrics, rate limiting
- **Load Balancing** — client-side LB (lookaside), service mesh (Istio), headless services
- **Tooling** — protoc, Buf (lint/breaking changes), grpcurl, grpc-web, gRPC-health-probe

---

## Backend Patterns

### Architecture Patterns

- **Monolith** — single deployable; simple, but hard to scale team/deploy independently
- **Microservices** — independently deployable services; bounded contexts, domain events, choreography vs orchestration
- **Event-Driven** — async communication via event bus; event sourcing, CQRS; eventual consistency
- **Serverless** — FaaS (Lambda, Cloud Functions), managed services; scale to zero, cold starts
- **Clean Architecture** — dependency inversion, layers (entities → use cases → interface adapters → frameworks)
- **Hexagonal (Ports & Adapters)** — core business logic isolated, adapters for external communication

### Design Patterns

- **Creational** — Singleton, Factory, Abstract Factory, Builder, Prototype
- **Structural** — Adapter, Facade, Proxy, Decorator, Composite, Bridge
- **Behavioral** — Strategy, Observer, Command, Chain of Responsibility, Template Method, State, Visitor
- **Enterprise** — Repository, Unit of Work, Data Mapper, Service Layer, DTO, DAO
- **Modern** — Circuit Breaker, Bulkhead, Retry + Backoff, Saga, Outbox, Transactional Outbox

### Concurrency Patterns

- **Fan-out/Fan-in** — distribute work to multiple goroutines/tasks, aggregate results
- **Pipeline** — stages connected by channels; each stage processes + passes to next
- **Worker Pool** — bounded goroutine/thread pool, job queue; rate limiting
- **Pub/Sub** — broadcast to multiple consumers, topic-based routing
- **Actor Model** — (Akka, Proto.Actor) isolated actors, message passing, supervision

---

## Server Architecture

### Runtimes & Frameworks

- **JVM** — Spring Boot (auto-configuration, embedded Tomcat/Netty, Actuator), Quarkus (fast boot, GraalVM), Micronaut (compile-time DI)
- **Go** — net/http (stdlib), Chi, Gin, Echo, Fiber; Fx/Uber for dependency injection
- **Python** — FastAPI (async, OpenAPI), Django (ORM, admin, auth), Flask (micro)
- **TypeScript** — NestJS (modular, opinionated), Express, Fastify, Hono

### Request Lifecycle

- **HTTP Server** — accept TCP conn → TLS termination → HTTP parsing → route matching → middleware chain → handler → response → logging
- **Middleware** — auth, rate limiting, logging, tracing, compression, CORS, request ID, timeout, recovery
- **Context Propagation** — request-scoped values (tenant ID, user ID, trace ID, deadline); Go context, Java MDC, Python contextvars

### Connection Management

- **Connection Pooling** — database (HikariCP, pgx), HTTP (keepalive), gRPC; pool sizing, max lifetime, validation
- **Rate Limiting** — token bucket, leaky bucket, sliding window; per-user, per-IP, per-endpoint
- **Graceful Shutdown** — SIGTERM → stop accepting → drain in-flight → cleanup → exit; health check endpoints for load balancer

---

## Performance Engineering

### Profiling & Benchmarking

- **CPU Profiling** — flame graphs, call graphs, hot methods; async-profiler (Java), pprof (Go), py-spy (Python), clinic (Node)
- **Memory Profiling** — heap dumps, allocation profiling, GC analysis, leak detection
- **Benchmarking** — JMH (Java), testing.B (Go), pytest-benchmark (Python), autocannon/Artillery (HTTP benchmarks)
- **Latency Analysis** — percentile distributions (p50, p99, p999), tail latency, coordinated omission

### Caching Strategies

- **Cache Types** — in-memory (local), distributed (Redis, Memcached), CDN (edge), HTTP (browser)
- **Patterns** — cache-aside, read-through, write-through, write-behind, refresh-ahead
- **Invalidation** — TTL-based, event-driven (cache eviction on data change), versioned keys
- **Pitfalls** — cache stampede, thundering herd, stale data, cache/memory size planning

### Database Performance

- **Indexing** — B-tree, hash, GIN/GiST, covering indexes; index-only scans; composite index column order
- **Query Optimization** — EXPLAIN ANALYZE, execution plan reading, query rewriting, CTEs, window functions
- **Connection Pool Sizing** — rule of thumb: (core_count * 2) + effective_spindle_count; too many = context thrash
- **Read/Write Splitting** — primary for writes, replicas for reads; replication lag handling

---

## Production Operations

### Observability

- **Logging** — structured JSON logs, log levels, correlation IDs; tools: ELK, Loki, Datadog
- **Metrics** — RED method (Rate, Errors, Duration), USE method (Utilization, Saturation, Errors); Prometheus + Grafana
- **Tracing** — distributed tracing (OpenTelemetry, Jaeger, Zipkin); trace context propagation, sampling strategies

### Deployment

- **CI/CD** — automated build, test, deploy; canary deploys, blue-green, rolling updates
- **Environment Management** — dev, staging, prod; feature flags, environment parity
- **Immutable Infrastructure** — bake artifacts (not at runtime), versioned images

### Resilience

- **Timeouts** — connect, read, write timeouts; client-side timeouts (circuit breaker's trip threshold)
- **Retries** — exponential backoff + jitter; retry budgets; idempotency keys
- **Circuit Breaker** — tripped by error rate; half-open for recovery probes
- **Bulkhead** — isolate resources (connection pools, thread pools per dependency)
- **Health Checks** — liveness (is app alive?), readiness (can it serve traffic?), startup (first ready?)

---

## Learning Path

1. **Stage 1** — Pick one language (Java, Go, Python, or TS) and become proficient: syntax, data structures, standard library, testing
2. **Stage 2** — HTTP, REST API design, basic web framework, databases (SQL + ORM), authentication (JWT, OAuth2)
3. **Stage 3** — Advanced: concurrency, caching, profiling, API design (REST + GraphQL + gRPC), design patterns
4. **Stage 4** — Architecture: microservices, event-driven, observability, resilience patterns
5. **Stage 5** — Production: deployment (CI/CD, containers), monitoring, performance tuning, scaling

---

## Cross-References

| Domain | Connection |
|--------|-----------|
| [00 — Foundations](/00-foundations/) | Data structures, algorithms, complexity analysis are daily tools for backend engineers |
| [01 — AI/ML](/01-ai-ml/) | Model serving infrastructure, embedding-based features, AI-powered API features |
| [02 — Data Engineering](/02-data-engineering/) | Backend services often feed/read from data pipelines; CDC patterns, event-driven ETL |
| [04 — Frontend](/04-frontend/) | Backend APIs consumed by frontend; BFF pattern, SSR hydration, real-time WebSocket |
| [05 — Cloud](/05-cloud/) | Compute (EC2, GKE, ECS), managed DBs (RDS, Cloud SQL), load balancers, auto-scaling |
| [06 — DevOps](/06-devops/) | CI/CD for backend services, Docker image building, infrastructure as code |
| [08 — Databases](/08-databases/) | Every backend service connects to a database; query design, connection management, migrations |
| [09 — Distributed Systems](/09-distributed-systems/) | Microservice communication, consistency, distributed transactions, consensus for coordination |
| [10 — Messaging](/10-messaging/) | Async integration of services, event-driven patterns, message queues for decoupling |
| [11 — Networking](/11-networking/) | HTTP/gRPC protocol details, TCP tuning, DNS resolution, TLS termination |

## Language Comparison

| Feature | Java | Go | Python | TypeScript |
|---|---|---|---|---|
| **Typing** | Static, strong | Static, strong | Dynamic, duck | Static, gradual (any) |
| **Concurrency** | Threads + Loom (virtual threads) | Goroutines + channels (built-in) | asyncio (library) | event loop (Node.js) |
| **Compilation** | JIT (JVM) | AOT (native binary) | Interpreted (C Python) | JIT (V8) / transpiled |
| **Memory** | GC (G1/ZGC/Shenandoah) | GC (concurrent) | GC (ref counting + generational) | GC (V8 Orinoco) |
| **Startup** | Slow (JVM warmup) | Fast (native binary) | Fast (interpreted) | Fast (but V8 warmup) |
| **Deployment** | JAR/WAR (JRE needed) | Single binary | pip + interpreter | npm + Node.js |
| **Ecosystem** | Maven/Gradle, Spring | Go modules, stdlib rich | pip, Django/FastAPI | npm, React/Next.js |
| **Best For** | Enterprise, big data, Android | CLI, networking, microservices | Data science, scripting, web | Web frontend, full-stack |

## Key Topics by Language

| Language | Architecture | Concurrency | Performance | Testing |
|---|---|---|---|---|
| Java | `01-oop-concepts` → `12-spring-boot` | `04-multithreading` + `15-concurrency-deep-dive` | `19-performance-tuning` | `18-testing-advanced` |
| Go | `01-goroutines-channels` | `01-goroutines-channels` (built-in) | `03-go-profiling` | Testing (std `testing` pkg) |
| Python | `01-python-internals` | `03-python-concurrency-async` | `01-python-internals` (GIL) | `04-python-testing-packaging` |
| TypeScript | `01-types-system-deep-dive` | Event loop (Node.js eventemitter) | `03-internals-performance` | Jest / Vitest |
