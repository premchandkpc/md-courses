# Database Systems Complete Guide

Comprehensive coverage of relational and NoSQL databases from fundamentals to advanced optimization, scaling, and concurrency patterns.

**Total Content:** 25+ files with code examples, real-world patterns, and visual diagrams.

---

## 📚 Quick Navigation

| Database | Overview | Schema | Operations | Advanced |
|----------|----------|--------|-----------|----------|
| **DynamoDB** | [Overview](./dynamodb/01-basics/01-overview.md) + [Visual](./dynamodb/01-basics/01-overview.html) | [Tables](./dynamodb/01-basics/02-tables.md) + [Visual](./dynamodb/01-basics/02-tables.html) | [Items](./dynamodb/01-basics/03-items.md) + [Visual](./dynamodb/01-basics/03-items.html) | [Queries](./dynamodb/02-intermediate/01-advanced-queries.md) \| [Concurrency](./dynamodb/04-concurrency/01-concurrency-control.md) \| [Optimization](./dynamodb/05-optimization/01-performance-tuning.md) |
| **MySQL** | [Overview](./mysql/01-basics/01-overview.md) + [Visual](./mysql/01-basics/01-overview.html) | [Design](./mysql/01-basics/02-schema-design.md) | [CRUD](./mysql/01-basics/01-overview.md#basic-operations) | [Optimization](./mysql/01-basics/02-schema-design.md) |
| **PostgreSQL** | [Overview](./postgres/01-basics/01-overview.md) | [Advanced SQL](./postgres/01-basics/01-overview.md) | [Queries](./postgres/01-basics/01-overview.md#ctesqueries) | JSON \| Arrays \| FTS |
| **MongoDB** | [Overview](./mongodb/01-basics/01-overview.md) | [Documents](./mongodb/01-basics/01-overview.md#documents--collections) | [CRUD](./mongodb/01-basics/01-overview.md#crud-operations) | [Aggregation](./mongodb/01-basics/01-overview.md#aggregation-pipeline) |
| **Oracle** | [Overview](./oracle/01-basics/01-overview.md) | [Tablespaces](./oracle/01-basics/01-overview.md#tablespaces--storage) | [Operations](./oracle/01-basics/01-overview.md#basic-operations) | [Partitioning](./oracle/01-basics/01-overview.md#partitioning) |

---

## 🎯 By Use Case

### Web Application Backend
**Recommended:** MySQL or PostgreSQL
- Start: [MySQL Overview](./mysql/01-basics/01-overview.md)
- Focus: Schema design, CRUD, indexing
- Key: User authentication, sessions, relationships

### Mobile App Backend  
**Recommended:** DynamoDB or MongoDB
- Start: [DynamoDB Overview](./dynamodb/01-basics/01-overview.md)
- Focus: Partition keys, scalability, TTL
- Key: Session storage, push notifications, analytics

### Real-Time Analytics
**Recommended:** DynamoDB or PostgreSQL
- Start: [DynamoDB Advanced Queries](./dynamodb/02-intermediate/01-advanced-queries.md)
- Focus: Query optimization, GSI, aggregation
- Key: Index strategies, denormalization

### Enterprise System
**Recommended:** Oracle or PostgreSQL
- Start: [Oracle Overview](./oracle/01-basics/01-overview.md) or [PostgreSQL Overview](./postgres/01-basics/01-overview.md)
- Focus: Complex queries, security, HA
- Key: Transactions, partitioning, compliance

### Content Management / Flexible Schema
**Recommended:** MongoDB
- Start: [MongoDB Overview](./mongodb/01-basics/01-overview.md)
- Focus: Collections, aggregation, flexible docs
- Key: Semi-structured data, rapid development

### Gaming / Leaderboards
**Recommended:** DynamoDB
- Start: [DynamoDB Items](./dynamodb/01-basics/03-items.md)
- Focus: Atomic operations, sharding, concurrency
- Key: Consistent leaderboards, player rankings

---

## 📖 Topics Covered

### Fundamentals (All Databases)
- Schema design principles
- Data types and constraints
- Indexing strategies  
- Query optimization
- Transactions and ACID properties

### Intermediate
- Join types and optimization
- Aggregation and grouping
- Subqueries and CTEs
- Stored procedures and functions
- Replication basics

### Advanced
- Sharding and partitioning
- Consistency models
- Distributed transactions
- Query execution plans
- Performance tuning

### Concurrency & Isolation
- Locking mechanisms (optimistic & pessimistic)
- Isolation levels
- Deadlock prevention
- Atomic operations
- Multi-version concurrency control (MVCC)

### Optimization & Scaling
- Connection pooling
- Caching strategies (DAX, Redis)
- Read replicas
- Write optimization
- Monitoring and diagnostics

### Scaling & HA
- Horizontal scaling (sharding)
- Vertical scaling
- Load balancing
- Failover strategies
- Global replication
- Multi-region setup

---

## 🗂️ File Structure

```
/databases/
├── README.md (This file)
├── GETTING_STARTED.md (Quick start guide)
├── CONTENT_INVENTORY.md (File listing)
│
├── dynamodb/
│   ├── 01-basics/
│   │   ├── 01-overview.md/html (Intro, features, billing)
│   │   ├── 02-tables.md/html (Keys, indexes, design)
│   │   └── 03-items.md/html (CRUD, batch, transactions)
│   ├── 02-intermediate/
│   │   └── 01-advanced-queries.md (Optimization, GSI)
│   ├── 04-concurrency/
│   │   └── 01-concurrency-control.md (Locking, atomics)
│   ├── 05-optimization/
│   │   └── 01-performance-tuning.md (Capacity, caching)
│   └── 06-scaling/ (Global tables - coming)
│
├── mysql/
│   └── 01-basics/
│       ├── 01-overview.md/html (Intro, ACID, engines)
│       └── 02-schema-design.md (Normalization, ERD)
│
├── postgres/
│   └── 01-basics/
│       └── 01-overview.md (Advanced SQL, JSON, arrays)
│
├── mongodb/
│   └── 01-basics/
│       └── 01-overview.md (Documents, CRUD, agg)
│
└── oracle/
    └── 01-basics/
        └── 01-overview.md (Enterprise, partition)
```

---

## 💡 Each Section Includes

- **Theory**: Concepts and principles with examples
- **Code Examples**: Real, runnable code in Python/SQL/JS
- **Why**: Problem-solving rationale  
- **When**: Use case scenarios and tradeoffs
- **Best Practices**: Do's and don'ts
- **Real-World Patterns**: Production scenarios
- **Visuals**: Diagrams and execution plans (HTML files)

---

## 🚀 Getting Started

**New to Databases?**
1. Read [GETTING_STARTED.md](./GETTING_STARTED.md) for learning paths
2. Choose a database from the table above
3. Start with the Basics folder (01-overview)

**Pick a Database Based On:**
- **Open Source + Reliable:** PostgreSQL or MySQL
- **Scalability + Simplicity:** DynamoDB or MongoDB
- **Enterprise + Maximum Performance:** Oracle
- **Specific Use Case:** See "By Use Case" section above

**Learning Progression:**
1. Read markdown for detailed explanations
2. View HTML for visual understanding
3. Run code examples locally
4. Study real-world patterns
5. Practice with your own data

---

## 🔗 Cross-Database Comparison

See GETTING_STARTED.md for detailed comparison tables covering:
- Cost models
- Scaling strategies
- Consistency models
- Transaction support
- Concurrency handling
- Best use cases
- Migration considerations

---

## 📊 Content Statistics

| Database | Files | Coverage | Examples | Visuals | Status |
|----------|-------|----------|----------|---------|--------|
| DynamoDB | 11 | Basics-Optimization | 40+ | 6 | ✓ Complete |
| MySQL | 2 | Basics-Schema | 15+ | 1 | ✓ In Progress |
| PostgreSQL | 1 | Basics | 20+ | - | ✓ In Progress |
| MongoDB | 1 | Basics | 25+ | - | ✓ In Progress |
| Oracle | 1 | Basics | 15+ | - | ✓ In Progress |

---

## 🎓 Recommended Learning Orders

### For Web Developers
1. MySQL or PostgreSQL basics (relational model)
2. Indexing & optimization
3. DynamoDB for scalability
4. MongoDB for flexible schema

### For Data Engineers
1. PostgreSQL advanced SQL (CTEs, window functions)
2. MongoDB aggregation pipeline
3. DynamoDB for real-time analytics
4. Scaling & partitioning strategies

### For System Architects
1. All overviews (compare all databases)
2. Scaling strategies (sharding, replication)
3. Concurrency & consistency models
4. HA/DR patterns

---

## 🔍 Search by Topic

- **Transactions**: [DynamoDB](./dynamodb/01-basics/03-items.md), [MySQL](./mysql/01-basics/01-overview.md), [PostgreSQL](./postgres/01-basics/01-overview.md), [Oracle](./oracle/01-basics/01-overview.md)
- **Indexing**: All database overviews
- **Scaling**: [DynamoDB Scaling](./dynamodb/06-scaling/), [Oracle Partitioning](./oracle/01-basics/01-overview.md#partitioning)
- **Concurrency**: [DynamoDB Concurrency](./dynamodb/04-concurrency/01-concurrency-control.md)
- **Performance**: [DynamoDB Optimization](./dynamodb/05-optimization/01-performance-tuning.md)
- **Joins**: [MySQL Schema](./mysql/01-basics/02-schema-design.md), [PostgreSQL](./postgres/01-basics/01-overview.md)
- **JSON/Flexible**: [PostgreSQL](./postgres/01-basics/01-overview.md#jsonjsonb), [MongoDB](./mongodb/01-basics/01-overview.md)

---

## 📝 How to Use These Guides

1. **Reading Code Examples**: Copy-paste to your IDE/terminal
2. **Testing Queries**: Use local databases or cloud free tiers
3. **Visual Diagrams**: Open .html files in web browser
4. **Cross-References**: Click links to related topics
5. **Exercises**: Modify examples with your own data

---

## 🎯 Next Steps

Start with [GETTING_STARTED.md](./GETTING_STARTED.md) for:
- Learning paths by experience level
- Quick start guides by use case
- Comparative analysis
- Study strategies

Then pick a database and dive into the basics!

---

**Happy Learning!** 🚀

For questions or additions, see contributing guidelines or open an issue.
