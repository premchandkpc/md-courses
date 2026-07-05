# 04-Orchestration

Orchestration is a saga execution model with a central coordinator (sometimes called a saga manager or orchestrator) that tells each service what to do and in what order. The orchestrator tracks state, issues commands, and handles failures by invoking compensating actions.

## Overview
- A dedicated orchestrator service defines the saga workflow as a state machine or step sequence.
- The orchestrator sends commands (not events) to participant services and awaits responses.
- On success, the orchestrator advances to the next step. On failure, it initiates compensation by calling each service's compensating endpoint in reverse order.
- The workflow logic is centralized, making it easier to visualize, monitor, and modify.

## Key Characteristics
- **Centralized State Management**: The orchestrator holds the saga's current state. This single location makes it easy to implement retry, timeout, and escalation logic.
- **Tighter Coupling**: Participant services must expose specific command endpoints (e.g., POST /reserve-inventory, POST /cancel-reservation). The orchestrator knows which services exist and in what order to call them.
- **Higher Observability**: Saga progress, failures, and compensation can be logged, traced, and alerted from one place. Operational dashboards are straightforward.
- **Scalability Concern**: The orchestrator can become a bottleneck or single point of failure under high throughput. Mitigation includes stateless orchestrators with persistent saga logs (Event Sourcing).
- **Easier to Evolve**: Adding, removing, or reordering steps requires changing only the orchestrator — participant services remain unchanged.

## Why It Matters
Orchestration is the preferred model for complex or long-running sagas. It is easier to reason about, test, and monitor than choreography. Frameworks like Camunda, Temporal, and AWS Step Functions implement the orchestrator pattern natively. The cost is an additional service and a tighter coupling contract between the orchestrator and participants.

## Related Concepts
- [02-Saga-Pattern](02-Saga-Pattern.md) — Orchestration is one of two saga execution models.
- [03-Choreography](03-Choreography.md) — The decentralized alternative to orchestration.
- [08-Event-Sourcing](08-Event-Sourcing.md) — Often used to persist orchestrator state as an event log.

---

## Mental Model
Orchestration is like a wedding planner who calls each vendor: "Florist, deliver at 9 AM. Caterer, arrive at 10 AM. Photographer, be ready at 11 AM." If the florist cancels, the planner calls the caterer to delay and finds a new florist — all from one phone. The bride (user) sees a single point of coordination.
