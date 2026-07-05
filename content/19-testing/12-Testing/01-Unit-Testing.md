# Unit Testing

Unit testing validates individual service functions in isolation by replacing external dependencies with mocks or stubs. Tests are fast, deterministic, and run on every commit.

## Overview
A unit test exercises a single unit of code — typically a function, method, or class — in complete isolation from its surroundings. In microservices, a unit might be a validation function, a business rule calculator, a request handler, or a repository method. External dependencies (databases, message brokers, other services) are replaced with test doubles. The goal is to verify that the unit produces the correct output for a given input and handles edge cases (nulls, empty data, boundary values) correctly.

## Key Characteristics
- **Isolation**: No real network calls, database queries, or file I/O — everything is mocked or stubbed.
- **Fast Execution**: A suite of thousands of unit tests runs in seconds, enabling rapid feedback during development.
- **Deterministic**: Given the same input, a unit test always produces the same result — no flakiness from external systems.
- **Granular Failure**: A failing unit test pinpoints exactly which function and which input caused the failure.
- **High Coverage Target**: Teams typically aim for 80-90% code coverage for business logic.

## Why It Matters
Unit tests are the first line of defense against regressions. When a developer refactors a function or adds a new feature, unit tests confirm that existing behavior is preserved. In microservices, where teams independently deploy dozens of services, fast and reliable unit tests give developers confidence to release frequently. Without them, every change risks breaking subtle business logic that no one remembers exists.

## Related Concepts
- [Integration Testing](02-Integration-Testing.md) — tests real interactions with dependencies; complements unit tests at a coarser granularity.
- [Testcontainers](07-Testcontainers.md) — provides real dependencies in containers for integration tests.
- [Contract Testing](03-Contract-Testing.md) — tests API agreements between services; unit tests verify internal correctness.

---

## Mental Model
A pilot checking instruments in a flight simulator. The simulator mimics all external conditions (weather, air traffic control, engine response) without actually flying. The pilot can test emergency procedures safely and repeatedly. Each checklist item is a unit test — fast, isolated, and repeatable. You don't need a real plane to verify the landing gear logic works.
