# Testcontainers

Testcontainers is a library that provides lightweight, disposable Docker containers for integration testing. It allows tests to use real database, message broker, and cache instances without manual infrastructure setup.

## Overview
Traditionally, integration tests either used embedded/in-memory substitutes (H2 for PostgreSQL, embedded Kafka) or required a pre-configured test environment. Both approaches have drawbacks: substitutes behave differently from real systems, and shared environments cause test pollution and flakiness. Testcontainers solves this by programmatically spinning up Docker containers during test execution — each test (or test suite) gets a fresh instance of the real dependency. When tests complete, containers are automatically torn down.

## Key Characteristics
- **Real Instances**: Tests run against actual PostgreSQL, MySQL, Redis, Kafka, Elasticsearch — not emulators.
- **Programmatic Lifecycle**: Containers are started and stopped from test code (JUnit `@ClassRule`, `@Container`).
- **Ephemeral by Design**: Each container is disposable — no cleanup needed between test runs.
- **Network Isolation**: Containers run on random ports and isolated networks, preventing port conflicts.
- **Image Flexibility**: Tests can use specific versions, custom Dockerfiles, or Docker Compose for multi-service setups.
- **Language Support**: Native libraries for Java, Kotlin, Go, Python, Node.js, .NET, and Rust.

## Why It Matters
In-memory substitutes (H2 instead of PostgreSQL) are notorious for hiding production bugs: they support different SQL dialects, don't enforce constraint validation the same way, and have different transaction behavior. Shared test databases create flaky tests due to leftover state. Testcontainers eliminates both problems — tests use the real database, in isolation, with zero manual setup. This dramatically increases the reliability and value of integration tests.

## Related Concepts
- [Integration Testing](02-Integration-Testing.md) — Testcontainers is the primary tool for running integration tests with real dependencies.
- [Unit Testing](01-Unit-Testing.md) — Testcontainers is not for unit tests (which use mocks); it bridges unit and system testing.
- [Performance Testing](08-Performance-Testing.md) — Testcontainers can be used to spin up the infrastructure needed for performance benchmarks.

---

## Mental Model
A pop-up restaurant kitchen. You don't build a permanent commercial kitchen to test a new menu. Instead, you set up a portable cooking station with real stoves, sinks, and refrigerators. You cook the meal (run the tests), evaluate the results, then pack the whole thing away. The next day, you set up a fresh station for the next menu. Testcontainers is the portable kitchen — real equipment, temporary setup, zero cleanup burden.
