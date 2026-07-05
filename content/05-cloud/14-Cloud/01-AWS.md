# 01-AWS

Amazon Web Services is the most widely adopted cloud platform for microservices, offering over 200 services across compute, storage, databases, networking, messaging, and observability. AWS provides the building blocks for deploying, running, and scaling microservices in production.

## Overview
AWS's service portfolio maps directly to microservices concerns. Compute: EC2 (VMs), ECS/EKS (containers), Lambda (serverless). Databases: RDS (relational), DynamoDB (NoSQL), ElastiCache (Redis/Memcached). Messaging: SQS (queues), SNS (pub/sub), EventBridge (event bus), Kinesis (streaming). API: API Gateway, App Mesh, CloudFront. Observability: CloudWatch (metrics/logs), X-Ray (tracing). Identity: IAM (roles, policies), Cognito (user auth). Each service is independently scalable and accessible via API, fitting the microservices philosophy of distributed, autonomous components.

## Key Characteristics
- **Broadest service portfolio**: Every microservices pattern has an AWS-native implementation. You rarely need to build infrastructure plumbing from scratch.
- **Pay-as-you-go pricing**: Costs scale with usage. No upfront capital expenditure. Services like Lambda charge per-millisecond, enabling extreme cost efficiency for variable workloads.
- **Regional and AZ architecture**: AWS Regions contain multiple Availability Zones (AZs). Deploying across AZs provides high availability with minimal latency. Global services (CloudFront, Route 53) operate across regions.
- **IAM for security**: Fine-grained access control via IAM roles and policies. Each service, instance, and function can have its own identity with least-privilege permissions.
- **Managed services reduce operational burden**: Managed databases (RDS, DynamoDB), message queues (SQS), and load balancers (ALB) remove the need to run and patch infrastructure.

## Why It Matters
AWS is the default cloud for many organizations adopting microservices. Its managed services eliminate undifferentiated heavy lifting — teams build business logic instead of managing ZooKeeper clusters, load balancers, or database failover scripts. Understanding the core AWS services and how they compose is essential for any microservices architect.

## Related Concepts
- [EKS](02-EKS.md) — Managed Kubernetes on AWS for container orchestration
- [Lambda](04-Lambda.md) — Serverless functions that scale automatically with no infrastructure management
- [DynamoDB](09-DynamoDB.md) — AWS's managed NoSQL database for microservices at scale

---

## Mental Model
A hardware store with every tool you could possibly need, organized by category (compute aisle, database aisle, messaging aisle). You rent tools by the minute, returning them when done. The store handles maintenance, security, and restocking. You just focus on building with the right tool for each job.
