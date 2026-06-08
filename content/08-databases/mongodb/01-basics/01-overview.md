---
title: MongoDB Overview & Document Model
topic: 08-databases
difficulty: intermediate
time: 30m
paths:
  - backend-junior
  - data
  - backend-senior
---

# MongoDB Overview & Document Model

## What is MongoDB?

MongoDB is a popular document-oriented NoSQL database. Data stored as flexible JSON-like documents in collections instead of rows in tables.

### Key Characteristics

| Aspect | Feature |
|--------|---------|
| Type | Document (NoSQL) |
| Model | Collections of documents (JSON-like) |
| Schema | Flexible, no predefined structure |
| Consistency | Eventual or strong (configurable) |
| Scaling | Horizontal (native sharding) |
| Transactions | Multi-document ACID (4.0+) |
| Indexes | B-tree, text, geospatial, wildcard |
| Replication | Replica sets for HA |

---

## Why MongoDB?

### Advantages

**1. Flexible Schema**
- No rigid table structure
- Documents can have different fields
- Easy to evolve data model
- Perfect for agile development

**2. Developer Friendly**
- JSON-like BSON format
- Natural to application code
- Less impedance mismatch
- No complex joins

**3. Scalability**
- Native horizontal scaling (sharding)
- Automatic data distribution
- Handles TB-scale datasets
- High throughput writes

**4. Performance**
- No expensive joins
- Embedded data (denormalization)
- Efficient querying
- Query optimization

**5. Rich Queries**
- Complex filters
- Aggregation framework
- Full-text search
- Geospatial queries

---

## When to Use MongoDB

### Good Fit ✓
- Web/mobile apps
- Content management
- Real-time analytics
- IoT/sensor data
- User profiles
- Product catalogs
- Event logging
- Semi-structured data
- Rapid prototyping

### Not Ideal ✗
- Complex multi-table joins
- Structured financial data
- Heavy ACID requirements
- Reports requiring normalization
- Fixed schema needed

---

## Documents & Collections

### Document Structure

```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "firstName": "John",
  "lastName": "Doe",
  "email": "john@example.com",
  "age": 30,
  "address": {
    "street": "123 Main St",
    "city": "Boston",
    "state": "MA"
  },
  "tags": ["premium", "verified"],
  "joinDate": ISODate("2026-01-15T10:30:00Z"),
  "metadata": {
    "loginCount": 42,
    "lastLogin": ISODate("2026-05-29T15:45:00Z")
  }
}
```

**Key Points:**
- `_id`: Unique identifier (auto-generated ObjectId)
- Flexible structure (no schema enforcement)
- Nested objects (address, metadata)
- Arrays (tags)
- Data types: String, Number, Object, Array, Date, Null, Boolean, Binary, etc.

---

## Collections

Group of documents (like tables, but flexible).

```javascript
// Collections don't need to be created explicitly
db.users.insertOne({ ... });  // Creates collection if not exists

// Collections have no schema, but indexes improve performance
db.users.createIndex({ email: 1 });

// Query collection
db.users.find({ age: { $gt: 25 } });
```

---

## CRUD Operations

### Create (Insert)

```javascript
// Single document
db.users.insertOne({
  firstName: "Jane",
  email: "jane@example.com",
  age: 28
});

// Multiple documents
db.users.insertMany([
  { firstName: "Alice", email: "alice@example.com", age: 32 },
  { firstName: "Bob", email: "bob@example.com", age: 35 }
]);

// Returns inserted IDs
{
  insertedId: ObjectId("507f1f77bcf86cd799439011"),
  insertedIds: [ ... ]
}
```

### Read (Find)

```javascript
// All documents
db.users.find();

// Specific fields
db.users.find({}, { firstName: 1, email: 1, _id: 0 });

// With conditions
db.users.find({ age: { $gt: 25 } });

// Multiple conditions
db.users.find({
  age: { $gte: 25, $lte: 40 },
  tags: "premium"
});

// Sorting & limiting
db.users.find().sort({ createdAt: -1 }).limit(10);
```

### Update (Update)

```javascript
// Update single document
db.users.updateOne(
  { _id: ObjectId("...") },
  { $set: { email: "newemail@example.com" } }
);

// Update multiple documents
db.users.updateMany(
  { status: "inactive" },
  { $set: { lastActive: new Date() } }
);

// Increment field
db.users.updateOne(
  { _id: ObjectId("...") },
  { $inc: { loginCount: 1 } }
);

// Push to array
db.users.updateOne(
  { _id: ObjectId("...") },
  { $push: { tags: "new-tag" } }
);
```

### Delete (Delete)

```javascript
// Delete single document
db.users.deleteOne({ _id: ObjectId("...") });

// Delete multiple documents
db.users.deleteMany({ status: "inactive" });

// Delete all (be careful!)
db.users.deleteMany({});
```

---

## Query Operators

### Comparison

```javascript
db.users.find({ age: { $eq: 30 } });      // Equal
db.users.find({ age: { $ne: 30 } });      // Not equal
db.users.find({ age: { $gt: 25 } });      // Greater than
db.users.find({ age: { $gte: 25 } });     // Greater or equal
db.users.find({ age: { $lt: 40 } });      // Less than
db.users.find({ age: { $lte: 40 } });     // Less or equal
db.users.find({ age: { $in: [25, 30, 35] } });    // In array
db.users.find({ age: { $nin: [25, 30, 35] } });   // Not in array
```

### Logical

```javascript
// AND (implicit)
db.users.find({ age: 30, status: "active" });

// OR
db.users.find({ $or: [ { age: 30 }, { age: 25 } ] });

// AND with OR
db.users.find({
  $and: [
    { age: { $gt: 25 } },
    { $or: [ { status: "active" }, { status: "premium" } ] }
  ]
});

// NOT
db.users.find({ age: { $not: { $lt: 30 } } });
```

### String/Array

```javascript
// String contains
db.users.find({ email: { $regex: "example" } });

// Array contains
db.users.find({ tags: "premium" });

// Array size
db.users.find({ tags: { $size: 3 } });

// Array element match
db.posts.find({
  comments: { $elemMatch: { userId: 5, rating: { $gte: 4 } } }
});
```

---

## Aggregation Pipeline

Transform and analyze data.

```javascript
// Example: Top 10 users by post count
db.posts.aggregate([
  {
    $group: {
      _id: "$userId",
      postCount: { $sum: 1 },
      avgScore: { $avg: "$score" }
    }
  },
  { $sort: { postCount: -1 } },
  { $limit: 10 },
  {
    $lookup: {
      from: "users",
      localField: "_id",
      foreignField: "_id",
      as: "userInfo"
    }
  }
]);

// Pipeline stages:
// $match    - Filter documents
// $group    - Group & aggregate
// $sort     - Sort results
// $limit    - Limit results
// $skip     - Skip n documents
// $project  - Reshape documents
// $lookup   - Join with another collection
// $unwind   - Flatten arrays
// $count    - Count documents
```

---

## Indexing

```javascript
// Create index
db.users.createIndex({ email: 1 });

// Compound index
db.posts.createIndex({ userId: 1, createdAt: -1 });

// Text index (full-text search)
db.articles.createIndex({ title: "text", content: "text" });

// Geospatial index
db.locations.createIndex({ coordinates: "2dsphere" });

// Unique index
db.users.createIndex({ email: 1 }, { unique: true });

// List indexes
db.users.getIndexes();

// Drop index
db.users.dropIndex("email_1");
```

---

## Replication & Sharding

### Replica Sets (High Availability)

```
Primary (writes) → Secondary (reads) → Secondary (reads)
       ↓
   Auto-failover if primary fails
```

```javascript
// Configure replica set
rs.initiate()
rs.add("replica2:27017")
rs.add("replica3:27017")

// Check status
rs.status()

// Read from secondary
db.setReadPref("secondary")
```

### Sharding (Horizontal Scaling)

```javascript
// Shard collection by userId
sh.shardCollection("app.posts", { userId: 1 })

// Data automatically distributed:
Shard 1: userId 0-1M
Shard 2: userId 1M-2M
Shard 3: userId 2M-3M
```

---

## Transactions (Multi-Document ACID)

```javascript
session = db.getMongo().startSession()

try {
  session.startTransaction()
  
  db.accounts.updateOne(
    { accountId: 1 },
    { $inc: { balance: -100 } },
    { session: session }
  )
  
  db.accounts.updateOne(
    { accountId: 2 },
    { $inc: { balance: 100 } },
    { session: session }
  )
  
  session.commitTransaction()
} catch (error) {
  session.abortTransaction()
  throw error
} finally {
  session.endSession()
}
```

---

## Comparison: MongoDB vs SQL

| Aspect | MongoDB | SQL (MySQL) |
|--------|---------|-----------|
| Schema | Flexible | Rigid |
| Joins | Rare (embedded) | Common |
| Transactions | Limited (4.0+) | Full ACID |
| Scaling | Horizontal | Vertical |
| Consistency | Eventual default | Strong |
| Queries | Filters + agg | Complex SQL |
| Indexes | B-tree, text, geo | B-tree primary |
| Best For | Document data | Relational data |

---

## Summary

- **Flexible Schema**: Documents with varying structures
- **BSON Format**: JSON-like with type support
- **Collections**: Groups of documents
- **Queries**: Flexible filters and operators
- **Aggregation**: Powerful data transformation
- **Indexing**: Multiple index types for performance
- **Scaling**: Native horizontal sharding
- **HA**: Replica sets for redundancy
- **ACID**: Multi-document transactions (4.0+)

Next: [[02-aggregation-advanced.md|Aggregation & Advanced Queries]]

---

**See Also:**
- [[../../mysql/01-basics/01-overview.md|MySQL Overview]]
- [[../../postgres/01-basics/01-overview.md|PostgreSQL Overview]]
- [[../../dynamodb/01-basics/01-overview.md|DynamoDB Overview]]
