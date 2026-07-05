# Pipeline

A Pipeline processes data through sequential stages, where each stage transforms the input and passes the result to the next stage. Pipelines are the foundation of ETL, middleware stacks, data processing, and CI/CD workflows.

## Overview
The Pipeline pattern structures computation as a series of discrete processing stages connected in sequence. Each stage receives data, performs a transformation, and forwards the result to the next stage. Stages can run in the same process, across threads, or on different machines connected by queues. In microservices, pipelines are used for data ingestion, stream processing (Kafka Streams, Flink), request middleware, and batch job orchestration.

## Key Characteristics
- **Sequential Transformation**: Data flows through stages in a fixed order; output of one stage is input to the next.
- **Stage Isolation**: Each stage is independent — it knows only its input schema and output schema.
- **Parallelizable**: Individual stages can be scaled independently, and fan-out/fan-in splits work across parallel workers.
- **Reusable Stages**: A normalization stage can be inserted into multiple pipelines handling different data types.
- **Observability**: Each stage can report its own metrics — throughput, error rate, latency — enabling fine-grained monitoring.

## Why It Matters
Microservices generate and consume large volumes of data that must be transformed, enriched, filtered, and routed. Hard-coding these transformations in a single service creates a monolithic processing blob that is difficult to test, reason about, or scale. Pipelines decompose processing into small, testable, independently deployable stages. Need to add data enrichment? Insert a stage. Need to scale aggregation? Run more aggregator instances.

## Related Concepts
- [Chain of Responsibility](09-Chain-of-Responsibility.md) — both sequence handlers; Pipeline transforms data, while Chain of Responsibility decides whether to process or pass.
- [Decorator](04-Decorator.md) — wraps a single call; Pipeline connects multiple stages linearly.
- [Workflow](11-Workflow.md) — coordinates business processes with state and recovery; Pipeline focuses on data transformation without persistent state.

---

## Mental Model
An assembly line in a car factory. The chassis enters Stage 1 (engine installation), then moves to Stage 2 (paint), then Stage 3 (interior). Each stage transforms the car and passes it to the next. If Stage 2 needs to run slower, buffers between stages absorb the difference. The assembly line is a pipeline — each station is a stage, the car is the data, and the conveyor belt is the transport between stages.
