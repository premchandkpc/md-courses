# Database Comparison & Selection Guide

## Quick Decision Matrix

| Requirement | Best Fit | Second Choice | Avoid |
|---|---|---|---|
| **Schema flexibility** | MongoDB | DynamoDB | Oracle, PostgreSQL |
| **Complex queries/joins** | PostgreSQL | MySQL | MongoDB, DynamoDB |
| **Global scalability** | DynamoDB | MongoDB | MySQL, PostgreSQL |
| **Enterprise SLA** | Oracle | PostgreSQL | DynamoDB (shared) |
| **Cost (small)** | MySQL | PostgreSQL | Oracle, DynamoDB |
| **Cost (large)** | DynamoDB | MongoDB | Oracle |
| **Real-time analytics** | DynamoDB | PostgreSQL | Oracle |
| **Transactions** | PostgreSQL | MySQL | MongoDB (limited) |
| **ACID** | PostgreSQL | MySQL | DynamoDB (10 items max) |

---

## Feature Comparison

### Data Model

| Feature | MySQL | PostgreSQL | MongoDB | DynamoDB | Oracle |
|---------|-------|-----------|---------|----------|--------|
| **Schema** | Rigid | Rigid | Flexible | Flexible | Rigid |
| **Joins** | Native | Native | Manual ($lookup) | Via GSI | Native |
| **Nested docs** | No | JSON | Yes | Limited | No |
| **Arrays** | No | Yes | Yes | No | No |
| **Full-text** | Limited | Native | Native | No | Yes |
| **Geospatial** | Limited | Yes (PostGIS) | Native | No | Yes |

### Performance

| Scenario | Winner | Why |
|----------|--------|-----|
| **Single key read** | DynamoDB | <1ms, auto-scaling |
| **Complex query** | PostgreSQL | Best optimizer |
| **Bulk write** | MongoDB | Batching, sharding |
| **Time-series** | DynamoDB | Partition by time |
| **Full-text search** | PostgreSQL | FTS scoring |
| **Range query** | PostgreSQL | BRIN indexes |

### Scaling

| Type | MySQL | PostgreSQL | MongoDB | DynamoDB | Oracle |
|------|-------|-----------|---------|----------|--------|
| **Vertical** | ✓✓ | ✓✓ | ✓✓ | ✓ | ✓✓✓ |
| **Horizontal (read)** | ✓ | ✓ | ✓✓ | ✓✓✓ | ✓✓ |
| **Horizontal (write)** | ✗ | ✗ | ✓✓ | ✓✓✓ | ✗ |
| **Sharding** | Manual | Manual | Native | Native | Partitioning |
| **Global** | ✗ | ✗ | ✓✓ | ✓✓✓ | ✓ |

### Consistency & Transactions

| Property | MySQL | PostgreSQL | MongoDB | DynamoDB | Oracle |
|----------|-------|-----------|---------|----------|--------|
| **ACID** | Full | Full | Limited (4.0+) | 10 items max | Full |
| **Isolation levels** | 4 | 4 | 2 | 1 | 4 |
| **Default** | READ COMMITTED | READ COMMITTED | Eventual | Eventual | READ COMMITTED |
| **Multi-doc xacts** | N/A | Yes | Yes (4.0+) | Up to 10 items | Yes |
| **Lock types** | Row | Row | Document | Key | Row |

---

## Cost Analysis

### Small Project (1GB, low traffic)

```
DynamoDB: $1-5/month (on-demand)
MySQL: $10-20/month (RDS small)
PostgreSQL: $10-20/month (RDS small)
MongoDB: $50+/month (Atlas)
Oracle: $500+/month (minimum license)

Winner: DynamoDB (if key-value), otherwise MySQL
```

### Medium Project (100GB, moderate traffic)

```
DynamoDB: $100-500/month
MySQL: $50-200/month (multi-AZ)
PostgreSQL: $50-200/month (multi-AZ)
MongoDB: $200-500/month (Atlas)
Oracle: $2,000+/month

Winner: MySQL or PostgreSQL
```

### Large Project (1TB+, high traffic)

```
DynamoDB: $1,000-10,000/month
MySQL: $500-2,000/month (read replicas)
PostgreSQL: $500-2,000/month (read replicas)
MongoDB: $1,000-5,000/month
Oracle: $5,000-20,000+/month

Winner: DynamoDB (if horizontal), PostgreSQL (if complex)
```

---

## Use Case Routing

### Web Application Backend

**Technology Stack:**
- Python/Node/Go backend
- React/Vue frontend
- Session storage
- User profiles
- Posts/comments
- Authentication

**Best:** MySQL or PostgreSQL
- Simple schema fits relational
- Transactions for orders/payments
- Mature ecosystem
- LAMP/MEAN stack standard

**Alternative:** MongoDB
- If rapid schema changes expected
- If nested data (posts + comments in one doc)

**Not:** DynamoDB
- Complex queries (posts with comments)
- Foreign key relationships needed

---

### Mobile App Backend

**Requirements:**
- Real-time data sync
- Offline support
- Global users
- Variable schema
- Low latency

**Best:** DynamoDB
- Serverless, auto-scaling
- Global tables for multi-region
- Excellent performance
- Session tokens + push notifications

**Alternative:** MongoDB
- Flexible schema for evolving apps
- Geospatial queries for location features

---

### Real-Time Analytics

**Requirements:**
- 1000+ events/second
- Time-series data
- Aggregate queries
- Historical analysis
- Low latency reads

**Best:** DynamoDB
- Partition by time
- On-demand scaling
- Stream processing integration

**Alternative:** PostgreSQL
- For historical analytics (OLAP)
- Complex aggregations
- Time-series extensions

---

### Content Management / Blog

**Requirements:**
- Posts, comments, tags
- Full-text search
- Author profiles
- Content versioning
- Media storage

**Best:** PostgreSQL
- JSONB for flexible content
- Full-text search native
- Versioning via triggers
- Media metadata in DB

**Alternative:** MySQL
- Simpler schema
- Proven for WordPress scale

---

### Leaderboards / Rankings

**Requirements:**
- Real-time updates
- Sorted rankings
- Player profiles
- Global visibility
- Concurrent updates

**Best:** DynamoDB
- Atomic counters
- Distributed sharding
- Global tables
- Millisecond latency

**Not Ideal:** 
- MySQL (scaling bottleneck)
- PostgreSQL (horizontal scaling harder)

---

### Financial / Banking

**Requirements:**
- Strict ACID
- Audit trail
- Compliance
- Complex transactions
- Data integrity critical

**Best:** PostgreSQL
- Full ACID
- Strong consistency
- Transaction guarantees
- Enterprise support

**Alternative:** Oracle
- Regulatory trust
- Advanced security
- Partitioning for scaling

**Not:** MongoDB, DynamoDB
- Weak transaction guarantees
- ACID not robust

---

### IoT / Time-Series

**Requirements:**
- Millions of metrics/second
- Time-based partitioning
- Real-time dashboards
- Historical queries
- Compression

**Best:** DynamoDB
- Partitioning by time
- Auto-scaling writes
- Streams for processing

**Alternative:** InfluxDB, TimescaleDB
- Purpose-built for time-series
- Better compression

---

### Data Warehouse / OLAP

**Requirements:**
- Complex aggregations
- Historical analysis
- Large joins
- Columnar queries
- Reporting

**Best:** PostgreSQL
- Advanced SQL
- Window functions
- CTEs
- BRIN indexes

**Not:** DynamoDB
- Expensive full scans
- No complex aggregations

---

## Migration Paths

### MySQL → PostgreSQL

```sql
-- Both relational, similar SQL
-- Migration: mysqldump → pg_restore
-- Effort: Low-Medium
-- Downtime: Minimal (dump/restore window)
```

**Reasons to migrate:**
- Need advanced SQL features
- Better performance needed
- JSON/array support
- Full-text search
- Open source + power combo

```bash
# Migration steps
mysqldump app > dump.sql
# Edit dump.sql (MySQL → PostgreSQL syntax)
psql < dump.sql
```

### MySQL → MongoDB

```javascript
// Relational → Document
// Complex transformation
// Schema redesign needed
// Effort: High

// Example: Blog schema transformation
// SQL: users, posts, comments (3 tables, joins)
// MongoDB: posts with nested comments
```

**Reasons:**
- Need schema flexibility
- Scaling writes
- Nested data benefits

---

### Relational → DynamoDB

```python
# Complex transformation
# Denormalization required
# Query patterns must be known upfront
# Effort: Very High

# Example: E-commerce
# SQL: orders, items, products (joins needed)
# DynamoDB: orders (includes item details, prices)
```

**Reasons:**
- Need global scaling
- Serverless preferred
- Query patterns fixed
- Cost optimization

---

## Hybrid Approaches

### MySQL + Redis

```
MySQL (persistent, relational)
  ↓
Redis (cache, sessions, real-time)
  ↑
Application
```

**Use:** Cache hot data, speed up reads

### PostgreSQL + Elasticsearch

```
PostgreSQL (relational, structured)
  ↓
Elasticsearch (full-text search)
  ↑
Application
```

**Use:** Complex search, faceted queries

### DynamoDB + S3

```
DynamoDB (metadata, structured)
  ↓
S3 (large objects, media)
  ↑
Application
```

**Use:** Cost optimization, large data

---

## Selection Flowchart

```
Start
  ↓
Is schema fixed?
  ├─ NO → MongoDB (or DynamoDB for serverless)
  └─ YES ↓
       Complex queries needed?
         ├─ YES → PostgreSQL
         └─ NO ↓
              Need global scale?
                ├─ YES → DynamoDB
                └─ NO → MySQL (cheaper) or PostgreSQL
```

---

## Evaluation Checklist

**Choose DynamoDB if:**
- [ ] Serverless preferred
- [ ] Global users
- [ ] Key-based access
- [ ] Predictable queries
- [ ] Willing to pay per-request
- [ ] Schema flexible helpful

**Choose PostgreSQL if:**
- [ ] Complex queries
- [ ] Strong consistency required
- [ ] Advanced SQL needed
- [ ] Transactions important
- [ ] Cost-sensitive
- [ ] Analytics heavy

**Choose MongoDB if:**
- [ ] Schema evolving
- [ ] Nested data natural
- [ ] Horizontal scaling critical
- [ ] JSON documents fit
- [ ] Willing to pay for Atlas

**Choose MySQL if:**
- [ ] Simple relational schema
- [ ] LAMP stack
- [ ] Cost very important
- [ ] Mature ecosystem important
- [ ] Don't need advanced features

**Choose Oracle if:**
- [ ] Enterprise required
- [ ] Extreme scale (petabytes)
- [ ] Regulatory mandated
- [ ] Advanced security needed
- [ ] Budget large

---

## Summary

| Database | Best At | Avoid For |
|----------|---------|-----------|
| **MySQL** | Small projects, blogs | Complex queries, scaling |
| **PostgreSQL** | Complex queries, analytics | Horizontal scaling |
| **MongoDB** | Schema flexibility, scaling writes | Transactions, complex joins |
| **DynamoDB** | Global scale, serverless | Complex queries, low cost |
| **Oracle** | Enterprise, extreme scale | Cost, open source |

---

**See Also:**
- [[README.md|Main Guide]]
- [[GETTING_STARTED.md|Quick Start]]
- Individual database guides for details

