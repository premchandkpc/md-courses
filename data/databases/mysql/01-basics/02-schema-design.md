# MySQL Schema Design & Normalization

## Database Normalization

Organize data to eliminate redundancy and improve efficiency.

### First Normal Form (1NF)

Each cell contains single value (no arrays/lists in columns).

```sql
-- ❌ Bad: Multiple values in one cell
CREATE TABLE orders (
    orderId INT PRIMARY KEY,
    customerName VARCHAR(100),
    itemIds VARCHAR(255)  -- "1,2,3" - NOT atomic!
);

-- ✓ Good: Separate table for items
CREATE TABLE orders (
    orderId INT PRIMARY KEY,
    customerId INT
);

CREATE TABLE orderItems (
    orderItemId INT PRIMARY KEY,
    orderId INT,
    itemId INT,
    quantity INT
);
```

### Second Normal Form (2NF)

All non-key attributes depend on entire primary key (no partial dependencies).

```sql
-- ❌ Bad: departmentName depends only on departmentId, not employeeId
CREATE TABLE employees (
    employeeId INT PRIMARY KEY,
    firstName VARCHAR(100),
    departmentId INT,
    departmentName VARCHAR(100)  -- Depends on dept, not employee!
);

-- ✓ Good: Separate department table
CREATE TABLE employees (
    employeeId INT PRIMARY KEY,
    firstName VARCHAR(100),
    departmentId INT,
    FOREIGN KEY (departmentId) REFERENCES departments(departmentId)
);

CREATE TABLE departments (
    departmentId INT PRIMARY KEY,
    departmentName VARCHAR(100)
);
```

### Third Normal Form (3NF)

Non-key attributes depend only on primary key (eliminate transitive dependencies).

```sql
-- ❌ Bad: cityName depends on stateId, not customerId
CREATE TABLE customers (
    customerId INT PRIMARY KEY,
    email VARCHAR(100),
    stateId INT,
    stateName VARCHAR(50)  -- Depends on state, not customer!
);

-- ✓ Good: Separate states table
CREATE TABLE customers (
    customerId INT PRIMARY KEY,
    email VARCHAR(100),
    stateId INT,
    FOREIGN KEY (stateId) REFERENCES states(stateId)
);

CREATE TABLE states (
    stateId INT PRIMARY KEY,
    stateName VARCHAR(50)
);
```

---

## Entity-Relationship Design

### One-to-One

```sql
-- User has exactly one profile
CREATE TABLE users (
    userId INT PRIMARY KEY,
    email VARCHAR(255) UNIQUE
);

CREATE TABLE profiles (
    profileId INT PRIMARY KEY,
    userId INT UNIQUE,  -- One-to-one
    biography TEXT,
    FOREIGN KEY (userId) REFERENCES users(userId)
);
```

### One-to-Many

```sql
-- Author has many books
CREATE TABLE authors (
    authorId INT PRIMARY KEY,
    firstName VARCHAR(100),
    lastName VARCHAR(100)
);

CREATE TABLE books (
    bookId INT PRIMARY KEY,
    title VARCHAR(255),
    authorId INT,  -- Many books per author
    FOREIGN KEY (authorId) REFERENCES authors(authorId)
);
```

### Many-to-Many

```sql
-- Students have many courses, courses have many students
CREATE TABLE students (
    studentId INT PRIMARY KEY,
    firstName VARCHAR(100)
);

CREATE TABLE courses (
    courseId INT PRIMARY KEY,
    courseName VARCHAR(100)
);

-- Junction table
CREATE TABLE enrollments (
    enrollmentId INT PRIMARY KEY,
    studentId INT,
    courseId INT,
    grade CHAR(1),
    FOREIGN KEY (studentId) REFERENCES students(studentId),
    FOREIGN KEY (courseId) REFERENCES courses(courseId),
    UNIQUE(studentId, courseId)  -- Prevent duplicate enrollments
);
```

---

## Schema Design Patterns

### User & Posts System

```sql
CREATE TABLE users (
    userId INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    firstName VARCHAR(100) NOT NULL,
    lastName VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    profilePicture LONGBLOB,
    bio TEXT,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email)
);

CREATE TABLE posts (
    postId INT AUTO_INCREMENT PRIMARY KEY,
    userId INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content LONGTEXT NOT NULL,
    publishedAt DATETIME,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (userId) REFERENCES users(userId) ON DELETE CASCADE,
    INDEX idx_userId (userId),
    INDEX idx_publishedAt (publishedAt)
);

CREATE TABLE comments (
    commentId INT AUTO_INCREMENT PRIMARY KEY,
    postId INT NOT NULL,
    userId INT NOT NULL,
    content TEXT NOT NULL,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (postId) REFERENCES posts(postId) ON DELETE CASCADE,
    FOREIGN KEY (userId) REFERENCES users(userId) ON DELETE CASCADE,
    INDEX idx_postId (postId),
    INDEX idx_userId (userId)
);

CREATE TABLE likes (
    likeId INT AUTO_INCREMENT PRIMARY KEY,
    postId INT NOT NULL,
    userId INT NOT NULL,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (postId) REFERENCES posts(postId) ON DELETE CASCADE,
    FOREIGN KEY (userId) REFERENCES users(userId) ON DELETE CASCADE,
    UNIQUE(postId, userId)  -- One like per user per post
);
```

### E-commerce System

```sql
CREATE TABLE products (
    productId INT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description LONGTEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    categoryId INT,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoryId) REFERENCES categories(categoryId),
    INDEX idx_categoryId (categoryId),
    INDEX idx_sku (sku)
);

CREATE TABLE orders (
    orderId INT AUTO_INCREMENT PRIMARY KEY,
    userId INT NOT NULL,
    orderDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'processing', 'shipped', 'delivered') DEFAULT 'pending',
    totalAmount DECIMAL(10, 2),
    FOREIGN KEY (userId) REFERENCES users(userId),
    INDEX idx_userId (userId),
    INDEX idx_status (status)
);

CREATE TABLE orderItems (
    orderItemId INT AUTO_INCREMENT PRIMARY KEY,
    orderId INT NOT NULL,
    productId INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,  -- Price at time of order
    FOREIGN KEY (orderId) REFERENCES orders(orderId) ON DELETE CASCADE,
    FOREIGN KEY (productId) REFERENCES products(productId),
    INDEX idx_orderId (orderId)
);
```

---

## Denormalization (When Needed)

Sometimes duplicate data for performance.

```sql
-- Normalized: Join required
SELECT u.email, COUNT(p.postId) AS postCount
FROM users u
LEFT JOIN posts p ON u.userId = p.userId
GROUP BY u.userId;

-- Denormalized: Direct field (faster, but must update together)
CREATE TABLE users (
    userId INT PRIMARY KEY,
    email VARCHAR(255),
    postCount INT DEFAULT 0  -- Cache, update with trigger
);

-- Keep in sync with trigger
DELIMITER //
CREATE TRIGGER updatePostCount AFTER INSERT ON posts
FOR EACH ROW
BEGIN
    UPDATE users SET postCount = postCount + 1 WHERE userId = NEW.userId;
END //
DELIMITER ;
```

---

## Composite Keys vs Surrogate Keys

### Surrogate Key (Recommended)

```sql
-- Use auto-increment ID
CREATE TABLE enrollments (
    enrollmentId INT AUTO_INCREMENT PRIMARY KEY,  -- Surrogate
    studentId INT NOT NULL,
    courseId INT NOT NULL,
    FOREIGN KEY (studentId) REFERENCES students(studentId),
    FOREIGN KEY (courseId) REFERENCES courses(courseId)
);
```

**Advantages:**
- Simple, unchanging
- Efficient joins
- Flexible to modify business logic

### Composite Key (When Natural)

```sql
-- Use business key
CREATE TABLE enrollments (
    studentId INT NOT NULL,
    courseId INT NOT NULL,
    PRIMARY KEY (studentId, courseId),
    FOREIGN KEY (studentId) REFERENCES students(studentId),
    FOREIGN KEY (courseId) REFERENCES courses(courseId)
);
```

**Use only when:**
- Key naturally exists in data
- Not likely to change
- Small key size

---

## Soft Deletes

Keep historical data instead of hard deleting.

```sql
-- Add deletedAt column
CREATE TABLE users (
    userId INT PRIMARY KEY,
    email VARCHAR(255),
    deletedAt DATETIME DEFAULT NULL
);

-- Soft delete: set timestamp
UPDATE users SET deletedAt = NOW() WHERE userId = 1;

-- Query active users only
SELECT * FROM users WHERE deletedAt IS NULL;

-- Restore deleted user
UPDATE users SET deletedAt = NULL WHERE userId = 1;

-- Hard delete when really needed
DELETE FROM users WHERE deletedAt < DATE_SUB(NOW(), INTERVAL 1 YEAR);
```

---

## Summary

- **1NF**: Atomic values only
- **2NF**: No partial dependencies
- **3NF**: No transitive dependencies
- **One-to-Many**: Foreign key in many table
- **Many-to-Many**: Junction table
- **Surrogate Keys**: Usually better
- **Soft Deletes**: Keep history
- **Indexes**: On foreign keys, frequently queried

Next: [[03-queries-optimization.md|Queries & Optimization]]

---

**See Also:**
- [[01-overview.md|MySQL Overview]]
- [[../../postgresql/01-basics/02-schema-design.md|PostgreSQL Schema Design]]
