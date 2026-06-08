# 🧪 Java Testing Advanced — Complete Deep Dive


```mermaid
graph LR
    UT["Unit Tests<br/>(JUnit 5)"] --> EXT["Extensions<br/>(ParameterResolver)"]
    UT --> MOCK["Mockito<br/>(@Mock / @InjectMocks)"]
    MOCK --> VERIFY["verify()<br/>Assertions"]
    INT["Integration Tests<br/>(SpringBootTest)"] --> TC["Testcontainers<br/>(PostgreSQL/Redis)"]
    INT --> WM["WireMock<br/>(HTTP Stubs)"]
    E2E["E2E Tests<br/>(Selenium/RestAssured)"] --> TCF["Testcontainers<br/>(Full Stack)"]
    BENCH["Benchmarks<br/>(JMH)"] --> WU["Warmup /<br/>Measurement"]
    style UT fill:#4a8bc2
    style EXT fill:#2d5a7b
    style MOCK fill:#3a7ca5
    style VERIFY fill:#3fb950
    style INT fill:#6f42c1
    style TC fill:#e8912e
    style WM fill:#c73e1d
    style E2E fill:#c73e1d
    style TCF fill:#e8912e
    style BENCH fill:#2d5a7b
    style WU fill:#3fb950
```

## Table of Contents


- [1. JUnit 5 Platform](#1-junit-5-platform)
- [2. Extensions](#2-extensions)
- [3. Parameterized Tests](#3-parameterized-tests)
- [4. Dynamic Tests](#4-dynamic-tests)
- [5. Mockito](#5-mockito)
- [6. AssertJ](#6-assertj)
- [7. Testcontainers](#7-testcontainers)
- [8. WireMock](#8-wiremock)
- [9. JMH Benchmarks](#9-jmh-benchmarks)
- [10. Pitest](#10-pitest)
- [11. Contract Testing](#11-contract-testing)
- [12. BDD](#12-bdd)
- [Simplest Mental Model](#simplest-mental-model)

---

## 1. JUnit 5 Platform


```text
┌──────────────────────────────────────────┐
│          JUnit 5 Platform                │
│  (Launcher, TestEngine Discovery)       │
├────────────────┬────────────────────────┤
│ Jupiter Engine │ Vintage Engine         │
│ (JUnit 5)      │ (JUnit 3/4 backward)  │
├────────────────┴────────────────────────┤
│       IDE / Build Tool Integration       │
└──────────────────────────────────────────┘
```

- **Platform**: foundation for `TestEngine` API
- **Jupiter**: modern annotations + extensions
- **Vintage**: legacy JUnit 3/4 on JUnit 5 platform

## 2. Extensions


Extensions hook into lifecycle: `BeforeAllCallback`, `ParameterResolver`, `TestWatcher`, `InvocationInterceptor`.

```java
public class DatabaseExtension implements BeforeAllCallback, AfterAllCallback {
  private EmbeddedDatabase db;
  @Override public void beforeAll(ExtensionContext ctx) {
    db = new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2).build();
  }
  @Override public void afterAll(ExtensionContext ctx) { if (db != null) db.shutdown(); }
}

public class RandomResolver implements ParameterResolver {
  @Override public boolean supportsParameter(ParameterContext pc, ExtensionContext ec) {
    return pc.getParameter().getType() == Random.class;
  }
  @Override public Object resolveParameter(ParameterContext pc, ExtensionContext ec) {
    return new SecureRandom();
  }
}

public class LoggingWatcher implements TestWatcher {
  @Override public void testSuccessful(ExtensionContext ctx) { /* log pass */ }
  @Override public void testFailed(ExtensionContext ctx, Throwable c) { /* log fail */ }
}

@ExtendWith({MockitoExtension.class, DatabaseExtension.class})
class MyTest { }
```

## 3. Parameterized Tests


```java
@ParameterizedTest
@ValueSource(strings = {"racecar", "radar"})
void palindromes(String s) { assertTrue(isPalindrome(s)); }

@ParameterizedTest
@CsvSource({"apple, 1.99, true", "banana, 0.59, false"})
void csv(String name, double p, boolean t) { assertEquals(t, new Product(name, p).isTaxable()); }

@ParameterizedTest
@MethodSource("fruitProvider")
void methodSource(String f) { assertNotNull(f); }
static Stream<String> fruitProvider() { return Stream.of("apple", "banana"); }

@ParameterizedTest
@EnumSource(Month.class)
void enumTest(Month m) { assertTrue(m.getValue() >= 1); }
```

## 4. Dynamic Tests


```java
@TestFactory
Stream<DynamicNode> dynamicTests() {
  return Stream.of("apple", "banana")
    .map(f -> DynamicTest.dynamicTest("Test " + f,
      () -> assertTrue(f.length() > 2)));
}
```

## 5. Mockito


```text
Mock Creation:    mock(), @Mock, spy(), @Spy, @InjectMocks, @Captor
Stubbing:         when().thenReturn(), doThrow().when(), doAnswer(), given() (BDD)
Verification:     verify(), times(), never(), InOrder, verifyNoInteractions
```

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
  @Mock UserRepository userRepo;
  @Mock EmailService emailService;
  @InjectMocks UserService userService;

  @Test void testFind() {
    when(userRepo.findById(42L)).thenReturn(Optional.of(user));
    assertThat(userService.findById(42L)).isPresent();
    verify(userRepo).findById(42L);
  }

  @Test void bddStyle() {
    given(userRepo.findById(42L)).willReturn(Optional.of(user));
    assertThat(userService.findById(42L)).isPresent();
  }

  @Captor ArgumentCaptor<Email> captor;
  @Test void testEmail() {
    userService.registerUser("alice@test.com");
    verify(emailService).send(captor.capture());
    assertEquals("Welcome!", captor.getValue().getSubject());
  }
}
```

## 6. AssertJ


```java
assertThat("Hello").startsWith("H").hasSize(5).contains("ell");
assertThat(42).isGreaterThan(10).isBetween(0, 100).isEven();
assertThat(List.of("a", "b", "c")).hasSize(3).containsExactly("a", "b", "c");
assertThat(Map.of("k1", "v1")).containsKey("k1").containsEntry("k1", "v1");
assertThat(Optional.of("hi")).isPresent().contains("hi");

assertThat(actual).usingRecursiveComparison()
  .ignoringFields("id", "createdAt").isEqualTo(expected);

assertSoftly(softly -> {
  softly.assertThat(name).isEqualTo("Alice");
  softly.assertThat(age).isEqualTo(30);
});

assertThatThrownBy(() -> parse("bad"))
  .isInstanceOf(ParseException.class).hasMessageContaining("invalid");
```

## 7. Testcontainers


```text
@Container + @Testcontainers
GenericContainer | PostgresContainer | KafkaContainer | MongoDBContainer
Wait strategies: Wait.forHttp / forLogMessage
Reusable: withReuse(true)
```

```java
@Testcontainers
class IntegrationTest {
  @Container static PostgreSQLContainer<?> pg = new PostgreSQLContainer<>("postgres:15")
    .withDatabaseName("testdb").withUsername("test").withPassword("test");

  @Container static KafkaContainer kafka = new KafkaContainer(
    DockerImageName.parse("confluentinc/cp-kafka:7.5.0"));

  @DynamicPropertySource
  static void props(DynamicPropertyRegistry r) {
    r.add("spring.datasource.url", pg::getJdbcUrl);
    r.add("spring.kafka.bootstrap-servers", kafka::getBootstrapServers);
  }

  @Container static GenericContainer<?> redis = new GenericContainer<>("redis:7-alpine")
    .withExposedPorts(6379)
    .waitingFor(Wait.forLogMessage(".*Ready.*\n", 1));
}
```

## 8. WireMock


```java
@WireMockTest(httpPort = 8089)
class PaymentTest {
  @Test void testSuccess() {
    stubFor(post(urlPathEqualTo("/api/payments"))
      .withRequestBody(matchingJsonPath("$.amount"))
      .willReturn(aResponse().withStatus(200)
        .withBody("""
          { "status": "success", "transactionId": "txn_123" }
        """)));

    assertThat(client.processPayment(new Payment(5000)).status()).isEqualTo("success");
    verify(postRequestedFor(urlPathEqualTo("/api/payments")));
  }

  @Test void testTimeout() {
    stubFor(get("/api/slow").willReturn(aResponse().withFixedDelay(10000)));
    assertThatThrownBy(() -> client.callSlow()).isInstanceOf(TimeoutException.class);
  }
}
```

## 9. JMH Benchmarks


```text
@BenchmarkMode(Mode.AverageTime)     // time/operation
@Warmup(iterations=5)                // JVM warmup
@Measurement(iterations=10)          // real measurement
@Fork(3)                             // fork JVM for isolation
@Param({"10","100"})                 // parameterized input
@State(Scope.Thread)                 // shared state
Blackhole → consume results (prevent dead-code elimination)
```

```java
@BenchmarkMode(Mode.AverageTime) @OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations=5) @Measurement(iterations=10) @Fork(3) @State(Scope.Thread)
public class StrBenchmark {
  @Param({"10", "100"}) private int len;
  private String data;
  @Setup public void setup() { data = "a".repeat(len); }
  @Benchmark public String concat() { return data + data; }
  @Benchmark public String builder() { return new StringBuilder(data).append(data).toString(); }
}
// Profilers: -prof gc, -prof stack, -prof async
```

## 10. Pitest


```text
Original code → Mutant (modified bytecode) → Run tests
  Tests FAIL → Mutant KILLED ✓
  Tests PASS → Mutant SURVIVED ✗ (test gap)
```

```xml
<plugin>
  <groupId>org.pitest</groupId><artifactId>pitest-maven</artifactId>
  <configuration>
    <targetClasses><param>com.example.service.*</param></targetClasses>
    <mutationThreshold>85</mutationThreshold>
    <incrementalAnalysis>true</incrementalAnalysis>
  </configuration>
</plugin>
```

Surviving mutation example: `age >= 18` mutated to `age > 18` — kill with boundary test `age == 18`.

## 11. Contract Testing


```text
Consumer                              Provider
 ┌──────────┐    ┌────────────┐    ┌──────────┐
 │ Defines  │───▶│ Verifier   │───▶│ Must     │
 │ contract │    │ generates  │    │ pass     │
 │          │    │ tests      │    │          │
 └──────────┘    └────────────┘    └──────────┘
```

```groovy
// Spring Cloud Contract
Contract.make {
  request { method GET(); url "/api/users/42" }
  response { status OK(); body([id: 42, name: "Alice", email: "alice@ex.com"]) }
}
```

```java
// Pact
@Pact(consumer="OrderService", provider="PaymentService")
public V4Pact createPact(PactDslWithProvider builder) {
  return builder.given("payment 5000 EUR").uponReceiving("payment request")
    .path("/api/payments").method("POST")
    .willRespondWith().status(200)
    .body(new PactDslJsonBody().stringType("status", "success"))
    .toPact(V4Pact.class);
}
```

## 12. BDD


```gherkin
Feature: Registration
  Scenario: Success
    Given a user with email "alice@test.com"
    When the user registers
    Then a welcome email is sent
```

```java
@SpringBootTest @AutoConfigureMockMvc @CucumberContextConfiguration
public class CucumberConfig { }

public class Steps {
  @When("the user registers") public void register() { }
  @Then("a welcome email is sent") public void emailSent() { verify(emailService).send(any()); }
}
```

---

## Simplest Mental Model


**Testing is insurance — policies that pay out when something breaks.**

- **JUnit 5**: Courtroom where trials happen. Extensions are bailiffs setting up.
- **Parameterized Tests**: Same script, different evidence (data).
- **Mockito**: Stunt doubles for real actors when you can't use the real database.
- **AssertJ**: The judge's gavel — clear, readable verdicts.
- **Testcontainers**: Full crime scene replica (real Redis/Postgres) in disposable boxes.
- **WireMock**: A witness who always says what you script.
- **JMH**: Nanosecond stopwatch with scientific rigor.
- **Pitest**: Evil twin that breaks code to see if tests catch it.
- **Contract**: Signed API agreement between consumer and provider.
- **Cucumber**: Plain English scenarios everyone can read.


## Production Failure Modes


### Failure 1: Flaky Integration Tests — 5% of Testcontainers Tests Fail Randomly


| Aspect | Detail |
|--------|--------|
| **Symptoms** | CI pipeline fails intermittently. Tests pass locally but fail on CI. `testOrderProcessing` fails with connection refused to PostgreSQL |
| **Root Cause** | Testcontainers container not fully ready before test starts. Default wait strategy (port check) doesn't guarantee DB is accepting connections. Resource contention on CI (multiple containers compete for memory/CPU, causing slow startup) |
| **Detection** | `container.getLogs()` shows "ready for connections" after the test already failed. `container.wait()` timeout logs. CPU/memory metrics on CI runner show 90%+ utilization when tests fail |
| **Recovery** | Add explicit `waitingFor(Wait.forLogMessage(".*database system is ready.*\n", 2))` for PostgreSQL. Increase `startupTimeout` to 120 seconds. Use `withReuse(true)` for local development |
| **Prevention** | Pin container image digests (not tags like `postgres:15`). Set Docker memory limits on CI. Use `@Testcontainers(parallel = false)` for flaky tests. Run flaky tests 3x in CI with `@RetryingTest` |

### Failure 2: Mockito Verification Oversight — Mock Returns Null in Production


| Aspect | Detail |
|--------|--------|
| **Symptoms** | All unit tests pass. In production, `NullPointerException` surfaces after deployment. Feature works in staging but fails in prod |
| **Root Cause** | Mockito returns default values for unstubbed methods (null for objects, 0 for ints). Test passes because it doesn't verify the real interaction pattern. The real implementation of `UserService.find()` calls `userRepo.findById()` but the test stubs `userRepo.findByName()` instead |
| **Detection** | `verify(userRepo, times(0)).findById(any())` — the method was never called. Test coverage shows green but assertion fails in production |
| **Recovery** | Add `verifyNoMoreInteractions()` after each test. Use `Mockito.validateMockitoUsage()` in `@AfterEach`. Add `@CheckReturnValue` annotation. Run mutation testing (Pitest) to catch missed interactions |
| **Prevention** | Always use `verify()` for every stubbed method. Use `lenient()` annotation only when explicitly needed. Enable `@ExtendWith(MockitoExtension.class)` which validates strict stubbing. Run Pitest with `mutationThreshold=85` |

### Failure 3: JMH Benchmark Misleads — Microbenchmark Does Not Predict Production Performance


| Aspect | Detail |
|--------|--------|
| **Symptoms** | Benchmarks show 50% improvement, but production latency increases. Code change merged based on benchmark data causes regression |
| **Root Cause** | JMH ran in isolation with warmup but production has: cache contention, thread scheduling, GC pauses, CPU frequency scaling, JIT compilation state differences. Benchmark measured throughput of a single object, real workload has millions |
| **Detection** | Compare benchmark conditions vs production: `-Djmh.executor=CUSTOM` thread configuration may differ. Production `-XX:+UseG1GC` vs benchmark default. Benchmark data size ('@Param({"10"})') is 1000x smaller than real |
| **Recovery** | Add production profiler data (async-profiler, JFR) to validate benchmark findings. Use `-prof gc`, `-prof perfnorm`, `-prof stack` profilers. Create realistic datasets matching production distribution |
| **Prevention** | Match benchmark setup to production: same GC, same heap (-Xms/-Xmx), same thread pool size, same data distribution. Use `@State(Scope.Thread)` for per-thread state. Never extrapolate single-thread microbenchmarks to multi-threaded production |

### Failure 4: Contract Test Stale — Consumer Tests Pass but Provider Changed API


| Aspect | Detail |
|--------|--------|
| **Symptoms** | Consumer expects response field `email`, provider renamed to `emailAddress`. Consumer tests pass because contract test wasn't regenerated. Production integration fails |
| **Root Cause** | Contract tests are generated at test time and cached. When provider changes API, CI pipeline doesn't fail because the contract was verified in the provider's pipeline but the consumer still uses the old contract. Stale contracts mask breaking changes |
| **Detection** | Pact `canDeploy()` checks consumer before production. `pact-broker can-i-deploy` returns success for old version. Provider logs show contract not re-verified during deploy |
| **Recovery** | `pact-broker can-i-deploy --pacticipant PaymentService --latest` to check. Regenerate contracts with `pact-verifier --include-wip=pactsSince=1d`. Re-run provider verification with latest consumer contracts |
| **Prevention** | Use PactFlow or Pact Broker with webhook triggers: provider deploy → re-verify all consumer contracts. Set `pact.provider.branch` and `pact.consumer.branch` to match. Use `can-i-deploy` as gating step in CI/CD |

### Failure 5: Cucumber Test Maintenance Nightmare


| Aspect | Detail |
|--------|--------|
| **Symptoms** | 500+ Gherkin scenarios. Test suite takes 2 hours. Step definitions are duplicated across features. Changing one UI element breaks 50 scenarios |
| **Root Cause** | Overuse of E2E tests (Cucumber) for scenarios that should be unit or integration tests. Step definitions use CSS selectors directly. No abstraction layer for page objects |
| **Detection** | `grep -r "click.*button" step_definitions/ | wc -l` shows 200+ duplicate selectors. Feature files contain test logic, not business behavior |
| **Recovery** | Extract page objects (Page Object Model). Move business logic tests to unit tests. Keep only end-to-end user journeys in Cucumber (<30 scenarios). Use parameterized types in Gherkin to reduce scenario count |
| **Prevention** | Limit Cucumber to critical user journeys only (login, purchase, signup). All other testing uses JUnit 5 + AssertJ. Use `@CucumberContextConfiguration` with Spring Boot for faster feedback. Set `CucumberExecutionContext: parallel execution` |

## Edge Cases


| Scenario | Challenge | Solution |
|----------|-----------|----------|
| **Testcontainers OOM on CI** | Docker containers use too much memory | Set `.withCreateContainerCmdModifier(cmd -> cmd.withMemory(512*1024*1024L))`. Use Ryuk resource cleaner |
| **Mockito @InjectMocks with constructor injection** | Ambiguous constructor resolution | Use explicit `@Mock` + constructor call instead of @InjectMocks. Prefer constructor injection in production code |
| **Parameterized test @MethodSource not static** | JUnit 5 requires static factory methods | In JUnit 5, @MethodSource must be static. Workaround: use `@TestInstance(Lifecycle.PER_CLASS)` to allow non-static |
| **WireMock stub matching too broad** | Stub matches unexpected requests, returns wrong response | Add request matching: `withHeader("X-Id", matching(".*"))`, `withRequestBody(matchingJsonPath("$.type"))` |
| **Pitest mutant timeout** | Infinite loop mutated code never terminates tests | Set `<timeoutConstant>10000</timeoutConstant>` in Pitest config. Add `<timeoutFactor>1.2</timeoutFactor>` |

## Cross-References


- [Reactive Programming](/03-backend/java/16-reactive-programming.md) — Virtual threads, reactive streams, Project Reactor testing
- [PostgreSQL Architecture](/08-databases/02-postgresql-architecture.md) — Testcontainers with real PostgreSQL replication
- [Distributed Transactions](/09-distributed-systems/02-distributed-transactions.md) — Sagas testing with Testcontainers + Kafka
- [ECS Deployment Patterns](/05-cloud/aws/ecs/02-ecs-deployment-patterns.md) — CI/CD pipeline integration tests

## Related

- [Jvm Performance](/18-performance-engineering/jvm-tuning/01-jvm-performance.md)
- [Cap Consistency](/09-distributed-systems/01-cap-consistency.md)
- [Consensus Replication](/09-distributed-systems/01-consensus-replication.md)
- [Consensus Raft](/09-distributed-systems/02-consensus-raft.md)
- [Distributed Transactions](/09-distributed-systems/02-distributed-transactions.md)
- [Distributed Caching](/09-distributed-systems/03-distributed-caching.md)

---

## Interactive Component: Java Thread Lifecycle

<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.state-machine-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px}.state-demo{text-align:center}.state-display{font-size:18px;font-family:monospace;padding:16px;border-radius:4px;margin:16px 0;color:#0b0e14;font-weight:bold;min-height:50px;display:flex;align-items:center;justify-content:center;border:2px solid currentColor}.state-new{background:#9333ea;border-color:#7e22ce}.state-runnable{background:#34d399;border-color:#22c55e}.state-running{background:#00d4ff;border-color:#0099cc;color:#0b0e14}.state-waiting{background:#fbbf24;border-color:#f59e0b}.state-terminated{background:#ef4444;border-color:#dc2626}.state-buttons{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:16px}.state-button{padding:8px 16px;border:1px solid #00d4ff;background:#1e3a5f;color:#00d4ff;border-radius:4px;cursor:pointer;font-family:monospace;font-size:12px;transition:all 0.2s}.state-button:hover{background:#2a5a8f;box-shadow:0 0 8px #00d4ff}</style>
  <div class="state-machine-title">Java Thread Lifecycle State Machine</div>
  <div class="state-demo">
    <div class="state-display state-new" id="state-display">NEW</div>
    <div class="state-buttons">
      <button class="state-button" onclick="setState('NEW', javaStateMap)">New (created)</button>
      <button class="state-button" onclick="setState('RUNNABLE', javaStateMap)">Runnable (start())</button>
      <button class="state-button" onclick="setState('RUNNING', javaStateMap)">Running (scheduler)</button>
      <button class="state-button" onclick="setState('WAITING', javaStateMap)">Waiting (lock/wait)</button>
      <button class="state-button" onclick="setState('TERMINATED', javaStateMap)">Terminated (done)</button>
    </div>
  </div>
  <script>
    const javaStateMap = {
      'NEW': { label: 'NEW', class: 'state-new' },
      'RUNNABLE': { label: 'RUNNABLE', class: 'state-runnable' },
      'RUNNING': { label: 'RUNNING', class: 'state-running' },
      'WAITING': { label: 'WAITING', class: 'state-waiting' },
      'TERMINATED': { label: 'TERMINATED', class: 'state-terminated' }
    };
    function setState(state, sm) {
      const display = document.getElementById('state-display');
      const info = sm[state];
      display.textContent = info.label;
      display.className = 'state-display ' + info.class;
    }
  </script>
</div>


---

## Interactive Component: Java Heap Memory Observability

<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.obs-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px}.obs-grid{display:grid;grid-template-columns:repeat(auto-fit, minmax(150px, 1fr));gap:12px}.obs-card{padding:12px;background:#1a2332;border:1px solid #1e3a5f;border-radius:4px;display:flex;flex-direction:column;align-items:center;transition:all 0.3s}.obs-card:hover{border-color:#00d4ff;box-shadow:0 0 8px rgba(0, 212, 255, 0.3)}.obs-label{color:#a3aab8;font-family:monospace;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px}.obs-value{font-family:monospace;font-size:20px;font-weight:bold;margin-bottom:4px;letter-spacing:0.5px}.obs-unit{color:#a3aab8;font-family:monospace;font-size:10px;text-transform:uppercase}.metric-healthy{color:#34d399}.metric-warning{color:#fbbf24}.metric-critical{color:#ef4444}</style>
  <div class="obs-title">JVM Heap Memory Metrics</div>
  <div class="obs-grid">
    <div class="obs-card">
      <div class="obs-label">Heap Used</div>
      <div class="obs-value metric-warning">712</div>
      <div class="obs-unit">MB</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Heap Max</div>
      <div class="obs-value metric-healthy">1024</div>
      <div class="obs-unit">MB</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">GC Pause</div>
      <div class="obs-value metric-healthy">85</div>
      <div class="obs-unit">ms</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Eden Usage</div>
      <div class="obs-value metric-healthy">45</div>
      <div class="obs-unit">%</div>
    </div>
  </div>
</div>


---

## Interactive Component: Thread Pool Configuration

<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.slider-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:12px}.slider-container{display:flex;flex-direction:column;gap:12px}.slider-label{color:#e3eaf0;font-family:monospace;font-size:12px}.slider-wrapper{display:flex;align-items:center;gap:12px}.slider-input{flex:1;height:6px;border-radius:3px;background:#1e3a5f;outline:none;-webkit-appearance:none;appearance:none}.slider-input::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:18px;height:18px;border-radius:50%;background:#00d4ff;cursor:pointer;box-shadow:0 0 8px #00d4ff;border:2px solid #0b0e14}.slider-input::-moz-range-thumb{width:18px;height:18px;border-radius:50%;background:#00d4ff;cursor:pointer;box-shadow:0 0 8px #00d4ff;border:2px solid #0b0e14}.slider-value{font-family:monospace;color:#34d399;min-width:80px;text-align:right;font-size:12px;font-weight:bold}</style>
  <div class="slider-title">Thread Pool Configuration</div>
  <div class="slider-container">
    <label class="slider-label">Core Pool Size:</label>
    <div class="slider-wrapper">
      <input type="range" min="1" max="64" value="8" class="slider-input" id="pool-slider">
      <span class="slider-value" id="pool-value">8 threads</span>
    </div>
  </div>
  <script>
    const slider = document.getElementById('pool-slider');
    const value = document.getElementById('pool-value');
    slider.addEventListener('input', (e) => { value.textContent = e.target.value + ' threads'; });
  </script>
</div>


---

## Interactive Component: Exception Cascade Simulator

<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.cascade-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px}.cascade-stages{display:flex;flex-direction:column;gap:12px;margin-bottom:16px}.cascade-stage{display:flex;align-items:center;gap:12px}.cascade-label{color:#e3eaf0;font-family:monospace;font-size:12px;min-width:120px}.cascade-indicator{width:24px;height:24px;border-radius:4px;background:#34d399;border:2px solid #22c55e;transition:all 0.3s}.cascade-indicator.failing{background:#ef4444;border-color:#dc2626;box-shadow:0 0 12px #ef4444;animation:cascade-fail 0.6s ease-out}@keyframes cascade-fail{0%{transform:scale(1);opacity:1}100%{transform:scale(1.2);opacity:0.8}}.cascade-controls{display:flex;gap:8px;flex-wrap:wrap}.cascade-button{padding:8px 16px;border:1px solid #00d4ff;background:#1e3a5f;color:#00d4ff;border-radius:4px;cursor:pointer;font-family:monospace;font-size:12px;transition:all 0.2s}.cascade-button:hover{background:#2a5a8f;box-shadow:0 0 8px #00d4ff}</style>
  <div class="cascade-title">Exception Stack Unwinding Cascade</div>
  <div class="cascade-stages">
    <div class="cascade-stage"><span class="cascade-label">Method A</span><div class="cascade-indicator" data-stage="a"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Method B (try)</span><div class="cascade-indicator" data-stage="b"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Method C (finally)</span><div class="cascade-indicator" data-stage="c"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Stack Unwound</span><div class="cascade-indicator" data-stage="d"></div></div>
  </div>
  <div class="cascade-controls">
    <button class="cascade-button" onclick="throwException()">Throw Exception</button>
    <button class="cascade-button" onclick="resetException()">Reset</button>
  </div>
  <script>
    function throwException() {
      const stages = ['a', 'b', 'c', 'd'];
      let delay = 0;
      stages.forEach((id) => {
        setTimeout(() => {
          document.querySelector('[data-stage="'+id+'"]').classList.add('failing');
        }, delay);
        delay += 300;
      });
    }
    function resetException() {
      document.querySelectorAll('[data-stage]').forEach(s => s.classList.remove('failing'));
    }
  </script>
</div>

