# ⚡ Java Reactive Programming — Complete Deep Dive

## Table of Contents
- [Reactive Manifesto](#reactive-manifesto)
- [Reactive Streams Spec](#reactive-streams-spec)
- [Project Reactor: Core Types](#project-reactor-core-types)
- [Reactor Operators by Category](#reactor-operators-by-category)
- [Reactor Context](#reactor-context)
- [Reactor Backpressure](#reactor-backpressure)
- [Schedulers](#schedulers)
- [Reactor Testing](#reactor-testing)
- [Reactor Debugging](#reactor-debugging)
- [RxJava3 vs Reactor](#rxjava3-vs-reactor)
- [Reactor Ecosystem](#reactor-ecosystem)
- [WebFlux](#webflux)

---

## Reactive Manifesto

```text
┌─────────────────────────────────────────────────────┐
│              Reactive Manifesto                       │
│                                                       │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐       │
│  │Responsive│◄──►│ Resilient│    │          │       │
│  │(fast resp│    │(self-heal)─┐──►│ Message  │       │
│  └────┬─────┘    └──────────┘ │  │ Driven   │       │
│       │                       │  │(async    │       │
│  ┌────▼─────┐    ┌──────────┐ │  │ comm)    │       │
│  │  Elastic │◄──►│Scalable  │◄┘  └──────────┘       │
│  │(adapt    │    │(up/down) │                        │
│  └──────────┘    └──────────┘                        │
└─────────────────────────────────────────────────────┘
```

Message-driven → loose coupling + isolation → resilience + elasticity → responsiveness.

## Reactive Streams Spec

```text
┌─────────────────────────────────────────────────────┐
│  Reactive Streams Contract                           │
│                                                       │
│  Publisher          ──subscribe──→   Subscriber      │
│  ┌────────┐                        ┌────────────┐   │
│  │        │  onSubscribe(Subscription)│           │   │
│  │        │◄─────────────────────────│           │   │
│  │        │      request(n)          │           │   │
│  │        │◄─────────────────────────│           │   │
│  │        │  onNext(T) (×n)          │           │   │
│  │        │ ────────────────────────→│           │   │
│  │        │  onError(Throwable) /    │           │   │
│  │        │  onComplete()            │           │   │
│  │        │ ────────────────────────→│           │   │
│  └────────┘                        └────────────┘   │
└─────────────────────────────────────────────────────┘
```

```java
// Reactive Streams interfaces
public interface Publisher<T> {
    void subscribe(Subscriber<? super T> subscriber);
}

public interface Subscriber<T> {
    void onSubscribe(Subscription subscription);
    void onNext(T item);
    void onError(Throwable throwable);
    void onComplete();
}

public interface Subscription {
    void request(long n);       // backpressure: ask for n items
    void cancel();              // stop receiving
}

public interface Processor<T, R> extends Publisher<R>, Subscriber<T> {}
```

## Project Reactor: Core Types

```text
┌─────────────────────────────────────────────────────┐
│  Reactor Types                                       │
│                                                       │
│  ┌──────────────────────────┐                        │
│  │  Mono<T>                  │  0 or 1 item         │
│  │  async, lazy, cold       │                        │
│  └──────────────────────────┘                        │
│                                                       │
│  ┌──────────────────────────┐                        │
│  │  Flux<T>                  │  0..N items           │
│  │  async, lazy, cold/hot   │                        │
│  └──────────────────────────┘                        │
└─────────────────────────────────────────────────────┘
```

```java
// Creating sequences
Mono<String> mono = Mono.just("hello");
Mono<String> empty = Mono.empty();
Mono<String> error = Mono.error(new RuntimeException("fail"));
Mono<String> deferred = Mono.defer(() -> Mono.just(expensiveBuild()));

Flux<Integer> range = Flux.range(1, 10);
Flux<Long> interval = Flux.interval(Duration.ofSeconds(1));
Flux<String> fromArray = Flux.just("a", "b", "c");

// Subscribe
flux.subscribe(
    value -> System.out.println("Next: " + value),
    error -> System.err.println("Error: " + error),
    () -> System.out.println("Complete"),
    subscription -> subscription.request(5) // manual backpressure
);
```

## Reactor Operators by Category

```java
// === TRANSFORMATION ===
flux.map(String::toUpperCase);                          // 1:1 sync
flux.flatMap(v -> asyncService.call(v));                // 1:N async, interleaved
flux.concatMap(v -> asyncService.call(v));              // 1:N async, ordered
flux.switchMap(v -> timeoutBasedStream(v));             // cancel prev, use latest
flux.flatMapMany(mono -> mono.flatMapMany(v -> ...));   // Mono → Flux

// === FILTERING ===
flux.filter(v -> v > 10);
flux.take(5).takeLast(3).takeUntil(v -> v > 100);
flux.skip(3).skipLast(2).skipUntil(v -> v > 50);
flux.distinct().distinctUntilChanged();
flux.elementAt(5).single().singleOrEmpty();

// === COMBINING ===
Flux.zip(fluxA, fluxB, (a, b) -> a + b);           // combine pairwise
Flux.merge(fluxA, fluxB);                           // interleaved
Flux.mergeSequential(fluxA, fluxB);                 // all A then all B
Flux.concat(fluxA, fluxB);                          // subscribe sequentially
Flux.combineLatest(fluxA, fluxB, (a, b) -> a + b); // latest from each

// === ERROR HANDLING ===
flux.onErrorResume(ex -> Flux.just("fallback"));
flux.onErrorContinue((ex, val) -> log.warn("Skipping {}", val));
flux.onErrorReturn("default");
flux.retry(3);
flux.retryWhen(Retry.max(3).filter(IOException.class::isInstance));
flux.retryBackoff(3, Duration.ofSeconds(1));

// === SIDE EFFECTS ===
flux.doOnNext(v -> log.info("Processing: {}", v));
flux.doOnError(ex -> log.error("Error", ex));
flux.doOnSubscribe(s -> log.info("Subscribed"));
flux.doFinally(type -> log.info("Terminated: {}", type));
flux.doOnCancel(() -> log.info("Cancelled"));
```

## Reactor Context

```java
// Context: per-subscriber state (like ThreadLocal but reactive)
Flux<String> flux = Flux.deferContextual(ctx ->
    Mono.just("User: " + ctx.get("user"))
);

flux.contextWrite(ctx -> ctx.put("user", "alice"))
    .subscribe(System.out::println); // User: alice

// Context is immutable, propagated downstream→upstream
// Each transform creates a new Context
```

## Reactor Backpressure

```text
Backpressure Strategies:
┌─────────────────────────────────────────────────────┐
│  unbounded()   ─── incoming ──────→ ┌────────────┐ │
│  (no limit)              drops      │ queue       │ │
│                                       └────────────┘ │
│  onBackpressureBuffer(size=1000)                    │
│    ┌───────────────────────────────────────────────┐ │
│    │  Bounded queue; overflow → error              │ │
│    └───────────────────────────────────────────────┘ │
│  onBackpressureDrop(v -> logDropped(v))             │
│  onBackpressureLatest()                             │
│  onBackpressureError()                              │
└─────────────────────────────────────────────────────┘
```

```java
// Limit incoming request rate
flux.limitRate(10);         // request(10) then replenish
flux.limitRequest(100);     // never request more than 100 total

// Backpressure strategies
flux.onBackpressureBuffer(100);            // bounded buffer
flux.onBackpressureDrop(v -> log.info("dropped {}", v));
flux.onBackpressureLatest();               // keep latest, drop intermediate
flux.onBackpressureError();                // error if downstream can't keep up
```

## Schedulers

```text
subscribeOn vs publishOn:
┌─────────────────────────────────────────────────────┐
│  subscribeOn(Scheduler X)                            │
│    Affects the ENTIRE chain (where subscribe happens)│
│                                                       │
│  publishOn(Scheduler Y)                              │
│    Affects DOWNSTREAM operators (where they execute) │
│                                                       │
│  Example:                                             │
│  source ──subscribeOn(Sched.A)──→ map ──publishOn→ map ──→ sub│
│           (A thread)        (A thread)  (B thread)        │
└─────────────────────────────────────────────────────┘
```

```java
// Built-in schedulers
Scheduler parallel = Schedulers.parallel();         // for CPU-bound work
Scheduler elastic = Schedulers.boundedElastic();    // for I/O, default
Scheduler immediate = Schedulers.immediate();       // current thread
Scheduler single = Schedulers.single();             // single reusable thread

// Custom
Scheduler custom = Schedulers.fromExecutorService(Executors.newFixedThreadPool(4));

// Where work runs
flux.subscribeOn(Schedulers.boundedElastic())   // subscription on elastic
    .publishOn(Schedulers.parallel())            // downstream on parallel
    .subscribe();
```

## Reactor Testing

```java
// StepVerifier
StepVerifier.create(Flux.just("a", "b", "c"))
    .expectNext("a")
    .expectNextCount(2)
    .verifyComplete();

// Virtual time (for interval/delay)
StepVerifier.withVirtualTime(() -> Flux.interval(Duration.ofHours(1)).take(2))
    .expectSubscription()
    .thenAwait(Duration.ofHours(2))
    .expectNext(0L, 1L)
    .verifyComplete();

// TestPublisher: control emission
TestPublisher<String> publisher = TestPublisher.create();
StepVerifier.create(publisher.flux())
    .then(() -> publisher.emit("a", "b", "c"))
    .expectNext("a", "b", "c")
    .then(publisher::complete)
    .verifyComplete();
```

## Reactor Debugging

```java
// Enable global operator stack traces
Hooks.onOperatorDebug();  // costly, only for dev

// Checkpoint: lightweight debugging
flux.checkpoint("after map", true); // description + stack trace

// Tags for observability
flux.tag("http.method", "GET")
    .tag("endpoint", "/api/users");
```

## RxJava3 vs Reactor

| Concept | Reactor | RxJava3 |
|---------|---------|---------|
| 0..N stream | Flux | Flowable (w/ backpressure) / Observable (w/o) |
| 0..1 stream | Mono | Single / Maybe / Completable |
| Backpressure | Built-in (request) | Flowable only |
| Context | `Context` | Not built-in |
| Schedulers | `Schedulers.*` | `Schedulers.*` |
| Android | No | Yes (RxAndroid) |
| Kotlin | Reactor Kotlin Ext | RxKotlin |

```java
// RxJava3
Observable.fromIterable(list)
    .map(String::toUpperCase)
    .subscribe(System.out::println);

Flowable.just("a", "b")
    .subscribeOn(Schedulers.io())
    .observeOn(Schedulers.computation())
    .subscribe();
```

## Reactor Ecosystem

```java
// Reactor Kafka
ReceiverOptions<Integer, String> opts = ReceiverOptions.create(props);
KafkaReceiver.create(opts.onPartitionsAssigned(assigner))
    .receive()
    .doOnNext(record -> process(record.value()))
    .subscribe();

// Reactor Netty (TCP/UDP/HTTP client-server)
HttpClient.create()
    .get()
    .uri("http://example.com")
    .responseContent()
    .aggregate()
    .asString();

// RSocket: 4 interaction models
RSocketConnector.create()
    .connect(TcpClientTransport.create("localhost", 7000))
    .flatMap(rsocket ->
        rsocket.requestResponse(Mono.just(DefaultPayload.create("ping")))
    );
```

## WebFlux

```java
// Functional endpoints
RouterFunction<ServerResponse> routes = route()
    .GET("/users/{id}", request -> {
        String id = request.pathVariable("id");
        return ok().body(userService.findById(id), User.class);
    })
    .POST("/users", request ->
        request.bodyToMono(User.class)
            .flatMap(userService::save)
            .flatMap(u -> created(URI.create("/users/" + u.id())).build())
    )
    .build();

// WebClient (replacement for RestTemplate)
WebClient client = WebClient.create("http://api.example.com");

client.get()
    .uri("/users/{id}", 1)
    .retrieve()
    .bodyToMono(User.class);

client.post()
    .uri("/users")
    .body(Mono.just(new User("alice")), User.class)
    .retrieve()
    .bodyToMono(User.class);

// SSE (Server-Sent Events)
client.get()
    .uri("/events")
    .accept(MediaType.TEXT_EVENT_STREAM)
    .retrieve()
    .bodyToFlux(Event.class)
    .subscribe(event -> handleEvent(event));
```

## Simplest Mental Model

> **Reactive = async data pipelines with backpressure**
>
> - **Publisher → Operator → Subscriber**: data flows downstream, demand flows upstream
> - **Mono** (0-1), **Flux** (0-N): lazy sequence operators (map, flatMap, filter)
> - **Backpressure**: subscriber controls rate via `request(n)`
> - **Schedulers**: `subscribeOn` (where subscribe runs), `publishOn` (where downstream runs)
> - **Context**: scoped state (like ThreadLocal) that works across async boundaries
> - **WebFlux**: non-blocking HTTP on Netty, functional routing, WebClient for downstream calls
