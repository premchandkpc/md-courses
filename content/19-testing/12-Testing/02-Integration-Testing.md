# Integration Testing

Integration testing verifies a service's behavior when connected to real dependencies — databases, message brokers, caches, and external APIs. It confirms that components work together correctly.

## Overview
While unit tests verify isolated logic, integration tests validate that a service interacts correctly with its real infrastructure. They spin up actual database instances (via Testcontainers or embedded databases), connect to message brokers, and exercise the service's full data access layer. Integration tests catch issues that unit tests miss: incorrect SQL queries, serialization mismatches, transaction handling bugs, connection pool exhaustion, and timing-related failures.

## Key Characteristics
- **Real Dependencies**: Tests run against actual databases, queues, caches — not mocks or in-memory substitutes.
- **Slower Execution**: Each test involves network calls, disk I/O, and setup/teardown of infrastructure, making them slower than unit tests.
- **Flakiness Risk**: Network issues, port conflicts, and timing variations can cause intermittent failures.
- **Higher Confidence**: Passing integration tests provide strong evidence that the service will work in production.
- **Targeted Scope**: Integration tests focus on the boundary between the service and its dependencies, not on business logic.

## Why It Matters
A microservice is worthless if it can't talk to its database or publish events correctly. Unit tests with mocked repositories verify code logic, but they don't verify the SQL query syntax, the database connection string, or the transaction isolation behavior. Integration tests are the safety net that catches infrastructure-level bugs before deployment. They are essential for any service that persists data or communicates with other services.

## Related Concepts
- [Unit Testing](01-Unit-Testing.md) — tests logic in isolation; integration tests add external dependencies.
- [Testcontainers](07-Testcontainers.md) — provides disposable Docker containers for integration test dependencies.
- [Contract Testing](03-Contract-Testing.md) — tests API agreements; integration tests verify that a service uses its dependencies correctly.

---

## Mental Model
Assembling furniture and actually tightening the screws. Unit testing is checking that each screw, plank, and dowel is the right size. Integration testing is drilling them together and making sure the shelf doesn't wobble. You can have perfect individual parts and still end up with a wobbly shelf if the assembly is wrong — integration tests catch the wobble.
