# Workflow

A Workflow coordinates a long-running business process by sequencing steps, managing state, handling failures, and providing recovery mechanisms. Workflows span multiple services and may execute over hours or days.

## Overview
Unlike a pipeline (which transforms data linearly), a workflow manages the execution of a multi-step business process with branching, conditional logic, timeouts, compensations, and human-in-the-loop steps. Workflows require persistent state — if the orchestrator crashes, it must resume from the last completed step. In microservices, workflows orchestrate processes like order fulfillment, user onboarding, loan approval, and deployment rollouts. Frameworks like Temporal, Camunda, and AWS Step Functions provide workflow engines that handle state persistence, retries, and observability.

## Key Characteristics
- **Persistent State**: The workflow's current position and data are persisted, enabling recovery from crashes.
- **Step Sequencing**: Steps execute in a defined order, with support for parallel forks, joins, and conditional branches.
- **Compensation**: Failed or canceled workflows can execute compensating actions to undo completed steps (saga pattern).
- **Human Tasks**: Some steps may require manual approval or intervention before proceeding.
- **Timeouts and Retries**: Each step can have a timeout; failed steps are retried with configurable backoff.
- **Observability**: Workflow engines provide dashboards showing active workflows, stuck steps, and execution history.

## Why It Matters
Business processes are rarely linear. An order might need payment authorization, inventory check, fraud review, shipping label generation, and email notification — each handled by different services. Without a workflow orchestrator, each service must coordinate with the next through ad-hoc callbacks, creating a distributed tangle. Workflow engines provide a single source of truth for process state, guaranteed execution, and clear failure handling.

## Related Concepts
- [State](07-State.md) — models state transitions within a single entity; Workflow coordinates transitions across multiple entities and services.
- [Pipeline](10-Pipeline.md) — linear data transformation; Workflow adds branching, state persistence, and compensation.
- [Event-Driven](12-Event-Driven.md) — workflows are often driven by events (state changes trigger the next step).

---

## Mental Model
A wedding planner. The planner has a checklist of tasks: book venue (Step 1), send invitations (Step 2), confirm caterer (Step 3). Some tasks can run in parallel (book photographer, book florist). If the venue is unavailable, the planner must compensate by finding an alternative. The planner keeps a master checklist — if they get sick, the next planner picks up where they left off. The wedding is the workflow, and the planner is the orchestrator.
