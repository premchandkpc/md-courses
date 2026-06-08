# MongoDB Aggregation Pipeline & Advanced Queries

## Aggregation Pipeline Stages

Transform data through sequential stages.

### $match (Filter)

```javascript
// Filter documents (like WHERE in SQL)
db.orders.aggregate([
  {
    $match: {
      status: "completed",
      totalAmount: { $gte: 100 }
    }
  }
]);

// Complex matching
db.orders.aggregate([
  {
    $match: {
      $or: [
        { status: "completed" },
        { priority: "high" }
      ]
    }
  }
]);
```

### $group (Aggregation)

```javascript
// Group and aggregate
db.orders.aggregate([
  {
    $group: {
      _id: "$customerId",
      totalSpent: { $sum: "$totalAmount" },
      orderCount: { $sum: 1 },
      avgOrderValue: { $avg: "$totalAmount" },
      latestOrder: { $max: "$orderDate" }
    }
  }
]);

// Group by null (entire collection)
db.orders.aggregate([
  {
    $group: {
      _id: null,
      totalRevenue: { $sum: "$totalAmount" },
      avgOrder: { $avg: "$totalAmount" },
      maxOrder: { $max: "$totalAmount" }
    }
  }
]);

// Accumulator operators
$sum      // Sum values
$avg      // Average
$min      // Minimum
$max      // Maximum
$count    // Count documents
$first    // First document value
$last     // Last document value
$push     // Array of values
$addToSet // Array of unique values
```

### $sort

```javascript
// Sort before limiting for efficiency
db.orders.aggregate([
  {
    $match: { status: "completed" }
  },
  {
    $sort: { totalAmount: -1 }  // Descending
  },
  {
    $limit: 10
  }
]);

// Multiple sort criteria
db.orders.aggregate([
  {
    $sort: {
      orderDate: -1,
      totalAmount: -1
    }
  }
]);
```

### $limit & $skip

```javascript
// Get top 10
db.orders.aggregate([
  { $match: { status: "completed" } },
  { $sort: { totalAmount: -1 } },
  { $limit: 10 }
]);

// Pagination: skip 20, get 10
db.orders.aggregate([
  { $skip: 20 },
  { $limit: 10 }
]);
```

### $project (Reshape)

```javascript
// Select fields + calculate
db.orders.aggregate([
  {
    $project: {
      orderId: 1,           // Include
      total: 1,
      tax: { $multiply: ["$total", 0.08] },  // Calculate
      afterTax: { $add: ["$total", { $multiply: ["$total", 0.08] }] },
      year: { $year: "$orderDate" },
      isHighValue: { $gte: ["$total", 500] }
    }
  }
]);
```

### $lookup (JOIN)

```javascript
// Join with another collection
db.orders.aggregate([
  {
    $lookup: {
      from: "customers",
      localField: "customerId",
      foreignField: "_id",
      as: "customerInfo"
    }
  }
]);

// Results: customerInfo array added to each order

// Nested lookup
db.orders.aggregate([
  {
    $lookup: {
      from: "customers",
      localField: "customerId",
      foreignField: "_id",
      as: "customer"
    }
  },
  {
    $lookup: {
      from: "products",
      localField: "productIds",
      foreignField: "_id",
      as: "products"
    }
  }
]);
```

### $unwind (Flatten Arrays)

```javascript
// Explode array to separate documents
db.orders.aggregate([
  {
    $match: { orderId: 1 }
  },
  {
    $unwind: "$items"  // One document per item
  }
]);

// With index and preserving empty arrays
db.orders.aggregate([
  {
    $unwind: {
      path: "$items",
      includeArrayIndex: "itemIndex",
      preserveNullAndEmptyArrays: true
    }
  }
]);
```

### $facet (Multiple Aggregations)

```javascript
// Multiple aggregations in parallel
db.products.aggregate([
  {
    $facet: {
      categoryStats: [
        { $group: { _id: "$category", count: { $sum: 1 } } },
        { $sort: { count: -1 } }
      ],
      priceStats: [
        {
          $group: {
            _id: null,
            avgPrice: { $avg: "$price" },
            minPrice: { $min: "$price" },
            maxPrice: { $max: "$price" }
          }
        }
      ],
      topProducts: [
        { $sort: { sales: -1 } },
        { $limit: 5 },
        { $project: { name: 1, sales: 1 } }
      ]
    }
  }
]);

// Results: Single doc with categoryStats, priceStats, topProducts arrays
```

---

## Real-World Examples

### Example 1: Customer Lifetime Value

```javascript
db.orders.aggregate([
  {
    $match: { orderDate: { $gte: new Date("2024-01-01") } }
  },
  {
    $group: {
      _id: "$customerId",
      totalSpent: { $sum: "$totalAmount" },
      orderCount: { $sum: 1 },
      avgOrderValue: { $avg: "$totalAmount" },
      firstOrder: { $min: "$orderDate" },
      lastOrder: { $max: "$orderDate" }
    }
  },
  {
    $lookup: {
      from: "customers",
      localField: "_id",
      foreignField: "_id",
      as: "customer"
    }
  },
  {
    $unwind: "$customer"
  },
  {
    $project: {
      customerId: "$_id",
      customerEmail: "$customer.email",
      totalSpent: 1,
      orderCount: 1,
      avgOrderValue: { $round: ["$avgOrderValue", 2] },
      daysSinceLastOrder: {
        $divide: [
          { $subtract: [new Date(), "$lastOrder"] },
          86400000
        ]
      }
    }
  },
  {
    $sort: { totalSpent: -1 }
  }
]);
```

### Example 2: User Engagement Score

```javascript
db.users.aggregate([
  {
    $lookup: {
      from: "posts",
      localField: "_id",
      foreignField: "userId",
      as: "userPosts"
    }
  },
  {
    $lookup: {
      from: "comments",
      localField: "_id",
      foreignField: "userId",
      as: "userComments"
    }
  },
  {
    $project: {
      username: 1,
      email: 1,
      postCount: { $size: "$userPosts" },
      commentCount: { $size: "$userComments" },
      totalLikes: {
        $add: [
          { $sum: "$userPosts.likes" },
          { $sum: "$userComments.likes" }
        ]
      },
      engagementScore: {
        $add: [
          { $multiply: [{ $size: "$userPosts" }, 10] },
          { $multiply: [{ $size: "$userComments" }, 5] },
          { $sum: "$userPosts.likes" },
          { $sum: "$userComments.likes" }
        ]
      }
    }
  },
  {
    $sort: { engagementScore: -1 }
  },
  {
    $limit: 100
  }
]);
```

### Example 3: Sales by Region & Category

```javascript
db.sales.aggregate([
  {
    $match: {
      saleDate: { $gte: new Date("2026-01-01") }
    }
  },
  {
    $facet: {
      byRegion: [
        {
          $group: {
            _id: "$region",
            totalSales: { $sum: "$amount" },
            count: { $sum: 1 }
          }
        },
        { $sort: { totalSales: -1 } }
      ],
      byCategory: [
        {
          $group: {
            _id: "$category",
            totalSales: { $sum: "$amount" },
            avgPrice: { $avg: "$price" }
          }
        },
        { $sort: { totalSales: -1 } }
      ],
      topProducts: [
        {
          $group: {
            _id: "$productId",
            totalSales: { $sum: "$amount" },
            quantity: { $sum: "$quantity" }
          }
        },
        { $sort: { totalSales: -1 } },
        { $limit: 10 }
      ],
      summary: [
        {
          $group: {
            _id: null,
            totalRevenue: { $sum: "$amount" },
            avgTransaction: { $avg: "$amount" },
            totalItems: { $sum: "$quantity" }
          }
        }
      ]
    }
  }
]);
```

### Example 4: Time-Series Analysis

```javascript
db.metrics.aggregate([
  {
    $match: {
      timestamp: { $gte: new Date("2026-05-01") },
      serverId: "server-001"
    }
  },
  {
    $group: {
      _id: {
        $dateToString: {
          format: "%Y-%m-%d %H:00",
          date: "$timestamp"
        }
      },
      avgCpu: { $avg: "$cpuUsage" },
      maxCpu: { $max: "$cpuUsage" },
      minCpu: { $min: "$cpuUsage" },
      avgMemory: { $avg: "$memoryUsage" },
      maxMemory: { $max: "$memoryUsage" },
      sampleCount: { $sum: 1 }
    }
  },
  {
    $sort: { _id: 1 }
  }
]);
```

---

## Query Operators (Advanced)

### Comparison in Aggregation

```javascript
// Conditional logic
db.orders.aggregate([
  {
    $project: {
      orderId: 1,
      totalAmount: 1,
      tier: {
        $cond: [
          { $gte: ["$totalAmount", 500] },
          "premium",
          {
            $cond: [
              { $gte: ["$totalAmount", 100] },
              "standard",
              "basic"
            ]
          }
        ]
      }
    }
  }
]);
```

### String Operations

```javascript
// String concatenation
db.users.aggregate([
  {
    $project: {
      fullName: { $concat: ["$firstName", " ", "$lastName"] },
      emailLower: { $toLower: "$email" }
    }
  }
]);

// String search in aggregation
db.posts.aggregate([
  {
    $match: {
      $expr: {
        $gt: [
          { $strLenCP: "$title" },
          10
        ]
      }
    }
  }
]);
```

### Date Operations

```javascript
// Extract date components
db.orders.aggregate([
  {
    $project: {
      orderId: 1,
      year: { $year: "$orderDate" },
      month: { $month: "$orderDate" },
      dayOfWeek: { $dayOfWeek: "$orderDate" },
      hour: { $hour: "$orderDate" },
      dayOfYear: { $dayOfYear: "$orderDate" }
    }
  }
]);

// Date arithmetic
db.orders.aggregate([
  {
    $project: {
      orderId: 1,
      daysSinceOrder: {
        $divide: [
          { $subtract: [new Date(), "$orderDate"] },
          86400000  // ms per day
        ]
      }
    }
  }
]);
```

---

## Performance Optimization

### Index Aggregation Stages

```javascript
// Create indexes for $match stage
db.orders.createIndex({ status: 1 });
db.orders.createIndex({ customerId: 1, orderDate: -1 });

// Efficient pipeline: $match early
db.orders.aggregate([
  { $match: { status: "completed" } },  // Uses index!
  { $lookup: { ... } },                  // After filtering
  { $group: { ... } }
]);
```

### Explain Plan

```javascript
// See query plan
db.orders.aggregate([
  { $match: { status: "completed" } },
  { $sort: { totalAmount: -1 } }
], { explain: true });

// Check if index used
// Look for "stage": "COLLSCAN" (bad) vs "IXSCAN" (good)
```

---

## Summary

- **$match**: Filter early for performance
- **$group**: Aggregate with accumulators
- **$project**: Reshape and calculate
- **$lookup**: JOIN with other collections
- **$unwind**: Flatten arrays
- **$facet**: Multiple aggregations
- **$sort + $limit**: Top N efficiently
- **Indexing**: Create on match fields
- **Real-world**: CLV, engagement, analytics

Next: [[../02-intermediate/01-replication-sharding.md|Replication & Sharding]]

---

**See Also:**
- [[01-overview.md|MongoDB Overview]]
- [[../../postgres/01-basics/02-json-arrays-advanced.md|PostgreSQL Advanced Features]]
- [[../../dynamodb/02-intermediate/01-advanced-queries.md|DynamoDB Advanced Queries]]
