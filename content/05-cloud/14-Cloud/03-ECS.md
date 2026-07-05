# 03-ECS

Amazon Elastic Container Service is a fully managed container orchestration service that is simpler than Kubernetes while still providing production-grade scheduling, scaling, and service discovery. ECS is AWS-native and deeply integrated with the rest of the AWS ecosystem.

## Overview
ECS runs containers on either EC2 instances (you manage the cluster) or AWS Fargate (serverless — no infrastructure to manage). Tasks are defined in task definitions (JSON specifying CPU, memory, container image, ports, environment variables, IAM role). Services define how many tasks should run and how they should be deployed (rolling update, blue/green). ECS integrates with ALB/NLB for traffic distribution, CloudMap for service discovery, and CloudWatch for logging.

## Key Characteristics
- **Simplicity over Kubernetes**: No control plane to manage, no etcd, no complex networking. ECS tasks map directly to business logic. Fewer moving parts than EKS.
- **Fargate launch type**: Serverless containers — no EC2 instances to provision, patch, or scale. You define CPU and memory, AWS handles placement. Pay per task per second.
- **EC2 launch type**: More control over instances (GPU, specialized hardware). Reserved instances and Savings Plans reduce costs for steady-state workloads.
- **Deep AWS integration**: IAM roles per task definition, CloudWatch Logs, ALB target groups, CloudMap service discovery, EFS file systems. Everything is first-class in the AWS console and APIs.
- **Capacity providers**: Define how ECS scales capacity — EC2 Auto Scaling Groups or Fargate. Mixed launch types are possible within a single cluster.
- **Blue/green deployments via CodeDeploy**: Built-in integration for traffic shifting, automated rollback, and validation hooks during deployments.

## Why It Matters
ECS (especially with Fargate) offers the lowest operational overhead for running containers on AWS. Teams that don't need Kubernetes's ecosystem (custom schedulers, CRDs, extensive plugin system) often find ECS+Fargate hits the sweet spot: containerized microservices with minimal infrastructure complexity.

## Related Concepts
- [EKS](02-EKS.md) — The Kubernetes alternative for teams that need more flexibility and ecosystem
- [Lambda](04-Lambda.md) — Even simpler than ECS: serverless functions instead of containers
- [AWS](01-AWS.md) — ECS is part of AWS's compute continuum (EC2 → ECS → EKS → Lambda)

---

## Mental Model
A valet parking service (ECS). You hand over your car (container image) and specify what kind of parking spot you need (task definition: 2 vCPUs, 4GB RAM). The valet parks it, brings it back when requested, and handles all the logistics. With Fargate, the valet even provides the garage — you never think about the parking structure.
