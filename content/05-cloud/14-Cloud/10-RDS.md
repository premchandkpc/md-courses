# 10-RDS

Amazon Relational Database Service is a managed service for relational databases: PostgreSQL, MySQL, MariaDB, Oracle, SQL Server, and Amazon Aurora. RDS automates provisioning, patching, backup, replication, and failover, freeing teams from database administration.

## Overview
RDS provides database instances with configurable compute (db.* instance types), storage (EBS gp2/gp3/io1, up to 64 TB), and networking (VPC, security groups). Key features: automated backups with point-in-time recovery (up to 35 days), Multi-AZ deployment for high availability (synchronous standby replica in another AZ), read replicas (up to 15, async) for read scaling, and storage auto-scaling (adds storage automatically when free space is low). Amazon Aurora, the MySQL/PostgreSQL-compatible engine, offers 5x better performance than standard MySQL and 3x better than PostgreSQL with a distributed, auto-healing storage volume.

## Key Characteristics
- **Multi-AZ HA**: A standby replica in a different AZ is provisioned with synchronous replication. If the primary fails, AWS automatically fails over to the standby. The DNS CNAME is updated — no connection string changes needed.
- **Read replicas**: Asynchronous replicas that offload read traffic. Can be in the same region or cross-region. Useful for read-heavy workloads, reporting, and disaster recovery. Replicas can be promoted to standalone instances.
- **Storage auto-scaling**: Dynamically adds storage when available space drops below a threshold. Prevents out-of-disk emergencies. Maximum storage limit is determined by instance type.
- **Automated maintenance**: Patching, minor version upgrades, and maintenance windows are managed by AWS. Scheduled during configurable maintenance windows to minimize disruption.
- **Encryption**: Encryption at rest (KMS) and in transit (TLS). Supports IAM database authentication in addition to password-based auth.
- **Limitations**: Maximum storage 64 TB per instance. Compute scaling requires instance type changes (restart). Connection limits depend on instance type. Upper limits exist — at extreme scale, you'll need sharding (Aurora can handle more with its distributed storage).

## Why It Matters
RDS handles the operational burden of running relational databases. Teams get automated backups, point-in-time recovery, patching, and Multi-AZ failover without hiring a DBA. For microservices that need relational data (ACID transactions, joins, complex queries), RDS — especially Aurora — is the standard choice on AWS.

## Related Concepts
- [DynamoDB](09-DynamoDB.md) — NoSQL alternative when schemas are flexible and traffic is extreme
- [Vertical Scaling](13-Scalability/02-Vertical-Scaling.md) — RDS scales vertically; sharding or Aurora read replicas handle horizontal
- [Replication](13-Scalability/05-Replication.md) — Multi-AZ (sync) and read replicas (async) provide fault tolerance and read scaling

---

## Mental Model
A managed car service: you specify the car model (PostgreSQL, MySQL) and the features (leather seats = Multi-AZ, GPS = automated backups, sunroof = read replicas). The service handles oil changes (patching), tire rotations (maintenance), and tows you to a mechanic if you break down (automatic failover). You just drive (query) and occasionally upgrade to a bigger model (scale instance type).
