# Database Learning Guide - Getting Started

Welcome to the comprehensive database systems guide. This structure covers **relational** and **NoSQL** databases from fundamentals through advanced optimization and scaling.

---

## 📚 Structure Overview

```
/08-databases/
├── README.md (Main index with all topics)
├── GETTING_STARTED.md (This file)
│
├── dynamodb/
│   ├── 01-basics/
│   │   ├── 01-overview.md/html (What is DynamoDB, features, when to use)
│   │   ├── 02-tables.md/html (Table design, keys, indexes)
│   │   └── 03-items.md/html (CRUD, batch, transactions)
│   ├── 02-intermediate/
│   │   └── 01-advanced-queries.md (Query optimization, GSI, filtering)
│   ├── 04-concurrency/
│   │   └── 01-concurrency-control.md (Optimistic/pessimistic locking, atomic ops)
│   ├── 05-optimization/
│   │   └── 01-performance-tuning.md (Capacity, caching, DAX, monitoring)
│   └── 06-scaling/
│       └── (Horizontal scaling, global tables)
│
├── mysql/
│   ├── 01-basics/
│   │   └── README.md (Overview, structure, learning path)
│   ├── 02-intermediate/
│   │   └── (To be created)
│   └── 03-advanced/
│       └── (To be created)
│
├── postgres/
│   ├── 01-basics/
│   │   └── README.md (Overview, advanced SQL features)
│   ├── 02-intermediate/
│   │   └── (To be created)
│   └── 03-advanced/
│       └── (To be created)
│
├── mongodb/
│   ├── 01-basics/
│   │   └── README.md (Overview, collections, CRUD)
│   ├── 02-intermediate/
│   │   └── (To be created)
│   └── 03-advanced/
│       └── (To be created)
│
└── oracle/
    ├── 01-basics/
    │   └── README.md (Overview, enterprise features)
    ├── 02-intermediate/
    │   └── (To be created)
    └── 03-advanced/
        └── (To be created)
```

---

## 🎯 Quick Start by Use Case

### Mobile/Web App Backend
**Best:** DynamoDB or MongoDB
- Start: DynamoDB Basics → 01-overview.md
- Focus: Table design, CRUD operations
- Key topic: Capacity planning & scaling

### Real-Time Analytics
**Best:** DynamoDB + Lambda or MongoDB Aggregation
- Start: DynamoDB 02-intermediate/01-advanced-queries.md
- Focus: Query optimization, GSI design
- Key topic: Index strategies

### Business Application
**Best:** PostgreSQL or Oracle
- Start: PostgreSQL 01-basics
- Focus: Schema design, relationships
- Key topics: Transactions, optimization

### Leaderboards / Gaming
**Best:** DynamoDB
- Start: DynamoDB 01-basics → 03-items.md
- Focus: Atomic operations, sharding
- Key topic: Concurrency control

### Content Management
**Best:** MongoDB or PostgreSQL
- Start: MongoDB 01-basics
- Focus: Flexible schema, querying
- Key topic: Indexing strategy

---

## 📖 Recommended Learning Paths

### Path 1: DynamoDB Fundamentals → Production
1. **01-overview.md** - Understand what DynamoDB is, when to use
2. **02-tables.md** - Design tables with proper keys
3. **03-items.md** - Master CRUD and batch operations
4. **02-intermediate/01-advanced-queries.md** - Optimize queries
5. **04-concurrency/01-concurrency-control.md** - Handle concurrent access
6. **05-optimization/01-performance-tuning.md** - Tune for production

### Path 2: SQL Databases (MySQL/PostgreSQL/Oracle)
1. Start with **01-basics** README for chosen database
2. Learn schema design and data types
3. Master SELECT, WHERE, JOINs
4. Study indexing for query optimization
5. Progress to **02-intermediate** for complex queries
6. **03-advanced** for performance tuning and scaling

### Path 3: NoSQL Comparison
1. **DynamoDB 01-basics** - AWS key-value
2. **MongoDB 01-basics** - Document database
3. Compare in terms of: schema flexibility, consistency, scaling

---

## 🔑 Key Concepts by Database Type

### DynamoDB (Key-Value/Document)
- Partition Key + Sort Key design
- RCU/WCU billing model
- Global Secondary Indexes (GSI)
- Eventual vs Strong consistency
- TTL for automatic expiration
- Hot partition prevention

### MongoDB (Document)
- Collections & flexible schema
- BSON data types
- Query operators & aggregation pipeline
- Compound indexes
- Replica sets & sharding

### PostgreSQL (Relational)
- Table design & relationships
- ACID transactions
- Window functions & CTEs
- Advanced data types (JSON, arrays)
- Full-text search

### MySQL (Relational)
- Schema design & constraints
- InnoDB transactions
- Storage engine options
- Replication strategies
- Read optimization

### Oracle (Enterprise Relational)
- Tablespaces & storage
- Row-level security
- Parallel execution
- Partitioning & compression
- Advanced indexing

---

## 📊 File Format

Each topic is presented in **two formats**:

### Markdown (.md)
- Detailed explanations
- Code examples in Python/SQL
- Real-world scenarios & patterns
- Best practices & anti-patterns
- "Why" and "When" guidance

### HTML (.html)
- Visual diagrams & architecture
- Interactive comparisons
- Flow charts
- Cost analysis
- Performance metrics visualization

**Tip:** Read markdown for learning, view HTML for visual understanding.

---

## 🎓 Learning Tips

1. **Start with basics**: Don't skip to advanced. Fundamentals matter.
2. **Hands-on practice**: Run code examples with sample data
3. **Understand trade-offs**: Each database has strengths/weaknesses
4. **Know your use case**: Choose database based on access patterns
5. **Monitor in production**: Use CloudWatch, logs, metrics
6. **Benchmark before choosing**: Test with your workload patterns

---

## 🚀 Next Steps

**Absolute Beginner:**
1. Read `/08-databases/README.md` for high-level overview
2. Choose your database type (relational vs NoSQL)
3. Start with 01-basics for chosen database
4. Work through examples locally

**Intermediate:**
1. Jump to 02-intermediate topics
2. Focus on optimization & design patterns
3. Study real-world scenarios in your domain

**Advanced:**
1. Read 03-advanced and 04-concurrency topics
2. Implement complex patterns (sharding, caching, etc.)
3. Performance tune production systems

---

## 📝 What's Covered

| Topic | DynamoDB | MySQL | PostgreSQL | MongoDB | Oracle |
|-------|----------|-------|-----------|---------|--------|
| Basics | ✓✓✓ | ✓ | ✓ | ✓ | ✓ |
| Intermediate | ✓✓ | - | - | - | - |
| Advanced | ✓✓ | - | - | - | - |
| Concurrency | ✓✓ | - | - | - | - |
| Optimization | ✓✓ | - | - | - | - |
| Scaling | ✓ | - | - | - | - |

*Legend: ✓✓✓ = Comprehensive | ✓✓ = Detailed | ✓ = Overview | - = To be created*

---

## 🔗 Related Topics

- **Caching**: ElastiCache, Redis, Memcached
- **Replication**: Multi-region, read replicas
- **Monitoring**: CloudWatch, Datadog, New Relic
- **Infrastructure**: AWS, GCP, Azure database services
- **Application Patterns**: ORM, query builders, migrations

---

## 💡 Common Questions

**Q: Which database should I choose?**
A: See "Quick Start by Use Case" above. Consider: consistency needs, query patterns, team expertise, scaling requirements.

**Q: Can I learn multiple databases?**
A: Yes! Core concepts transfer (transactions, indexing, optimization). Start with one, then compare.

**Q: What about costs?**
A: Each database section includes cost analysis. DynamoDB: pay per request. RDS: per instance. MongoDB Atlas: per cluster.

**Q: How do I practice?**
A: Use local Docker containers or cloud free tiers. Create sample data, write queries, measure performance.

---

## 📚 Table of Contents

- [Main Database Guide](./README.md)
- [DynamoDB Basics](./dynamodb/01-basics/)
- [DynamoDB Intermediate](./dynamodb/02-intermediate/)
- [DynamoDB Concurrency](./dynamodb/04-concurrency/)
- [DynamoDB Optimization](./dynamodb/05-optimization/)
- [MySQL Basics](./mysql/01-basics/)
- [PostgreSQL Basics](./postgres/01-basics/)
- [MongoDB Basics](./mongodb/01-basics/)
- [Oracle Basics](./oracle/01-basics/)

---

**Last Updated:** 2026-05-29
**Status:** In Development (DynamoDB comprehensive, others structure in place)
