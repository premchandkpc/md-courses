# Interview Preparation — Complete Guide 🎯

Technical interview preparation is a structured skill — combining deep system design knowledge, algorithmic proficiency, behavioral storytelling, and domain-specific expertise (Java, distributed systems).

**Related**: [System Design](../15-system-design/README.md) · [Distributed Systems](../09-distributed-systems/README.md) · [Java](java/README.md) · [Coding](coding/README.md)

---

## Table of Contents

- [Interview Types](#-interview-types)
- [Java Interview Questions](#1-java-interview-questions-)
- [Distributed Systems Deep Dives](#2-distributed-systems-deep-dives-)
- [System Design Framework](#3-system-design-framework-)
- [System Design Problems](#4-system-design-problems-)
- [Coding Patterns](#5-coding-patterns-)
- [Behavioral Interviews](#6-behavioral-interviews-)
- [FAANG-Specific Preparation](#7-faang-specific-preparation-)
- [Mock Interviews](#8-mock-interviews-)
- [Company-Specific Tips](#9-company-specific-tips-)
- [Resume & Strategy](#10-resume--strategy-)
- [Learning Path](#-learning-path)
- [Related Domains](#-related-domains)
- [Simplest Mental Model](#-simplest-mental-model)

---

## 🧭 Interview Types

### The Standard Tech Interview Loop
```
1. Phone Screen (45 min)
   → Resume discussion, basics, LeetCode Easy/Medium

2. Technical Phone / Online Assessment (60 min)
   → Coding problem with shared editor (CoderPad, HackerRank)

3. On-site / Virtual On-site (4-6 hours)
   Coding (1-2 rounds), System Design (1-2), Behavioral (1)
   Domain-specific (varies by company/level)

4. Hiring Committee Review
   → All feedback synthesized into hiring decision
```

### What Interviewers Evaluate
```
Coding:
  - Problem-solving approach (not just solution)
  - Communication (think out loud)
  - Code quality (clean, readable, tested)
  - Optimization awareness (time/space analysis)

System Design:
  - Scope definition (requirements clarity)
  - Architecture thinking (high-level + tradeoffs)
  - Depth (deep dive into one component)
  - Communication (clear diagrams, structured thinking)

Behavioral:
  - Leadership / ownership
  - Conflict resolution
  - Technical decision-making
  - Growth mindset
```

---

## 1. Java Interview Questions ☕

### Core Java (180+ Questions)

**OOP & Language Features**
- Polymorphism, inheritance, encapsulation with examples
- Abstract class vs interface (Java 8+ with default methods)
- `final` with classes, methods, variables
- `static` — methods can't be overridden, why?
- Covariant return types
- Method overloading vs overriding rules

**Collections Framework**
- HashMap internals: `put()` and `get()` mechanics
- HashMap vs ConcurrentHashMap vs Hashtable
- TreeMap vs LinkedHashMap vs HashMap
- ConcurrentHashMap thread-safety (segments → CAS + synchronized)
- CopyOnWriteArrayList: when and why?
- Comparable vs Comparator
- `hashCode()` and `equals()` contract
- ArrayList vs LinkedList performance
- `Arrays.asList()` vs `List.of()`

**Concurrency**
- Thread lifecycle: NEW → RUNNABLE → BLOCKED → WAITING → TIMED_WAITING → TERMINATED
- `synchronized` internals: monitor, mutex, biased locking
- `volatile`: visibility guarantee (happens-before)
- `AtomicInteger` vs `synchronized` vs `volatile`
- `ReentrantLock` vs `synchronized`
- `CountDownLatch` vs `CyclicBarrier` vs `Semaphore`
- `CompletableFuture`: `thenApply`, `thenCompose`, `thenCombine`
- ForkJoinPool and work-stealing
- Thread pool types: Fixed, Cached, Scheduled, SingleThread
- What happens when queue is full + pool is max?

**JVM Internals**
- JVM memory model: Heap (Young/Old/Metaspace), Stack, PC, Native
- Class loading: Bootstrap → Extension → Application
- GC algorithms (Serial, Parallel, CMS, G1, ZGC)
- When does Full GC happen?
- Strong, Soft, Weak, Phantom references
- OutOfMemoryError types
- StackOverflowError causes

**Java 8+ Features**
- Lambda expressions, functional interfaces
- Stream API: `map`, `filter`, `reduce`, `collect`, `flatMap`
- `Optional`: when to use, common pitfalls
- `Collectors.toMap()`, `groupingBy()`, `partitioningBy()`
- `java.time` API (vs `java.util.Date` problems)
- Records (Java 14+), Sealed classes (Java 17+), Pattern matching

**Spring / Spring Boot**
- Dependency injection: constructor vs setter vs field
- Spring Bean lifecycle
- `@Transactional` — how it works (AOP proxy)
- Transaction propagation: REQUIRED, REQUIRES_NEW, NESTED
- Spring AOP: proxies, pointcuts, advice types
- Spring Boot auto-configuration (`@EnableAutoConfiguration`)
- Spring Security filter chain
- Spring Data JPA: N+1 problem, fetch strategies

---

## 2. Distributed Systems Deep Dives 🌐

### 18 Core Topics
1. **CAP Theorem**: Consistency, Availability, Partition Tolerance — choose 2
2. **Consensus**: Paxos, Raft, Zab — how they work in practice
3. **Replication**: Leader-based, multi-leader, leaderless (quorum)
4. **Partitioning**: Range, hash, consistent hashing, rebalancing
5. **Distributed Transactions**: 2PC, Saga, TCC, Outbox pattern
6. **Consistency Models**: Linearizability → Sequential → Causal → Eventual
7. **Time & Ordering**: Lamport clocks, vector clocks, TrueTime (Spanner)
8. **Failure Detection**: Gossip protocol, SWIM, phi-accrual
9. **Leader Election**: Bully algorithm, Raft leader election, ZooKeeper
10. **Distributed ID**: Snowflake, UUID v7, ULID, KSUID
11. **Distributed Caching**: Cache-aside, write-through, write-behind, CDN
12. **Distributed Scheduling**: Schedulers (Airflow, Dagster), rate limiting
13. **Stream Processing**: Kafka Streams, Flink, Samza — exactly-once semantics
14. **Distributed Storage**: LSM trees, SSTables, WAL, Merkle trees
15. **Service Discovery**: DNS, ZooKeeper, etcd, Eureka, Consul
16. **RPC**: gRPC, Thrift, HTTP/2 — protocol differences
17. **Distributed Tracing**: W3C tracecontext, OpenTelemetry, sampling
18. **Chaos Engineering**: Principles, blast radius, GameDays

### Key Papers to Read
- "In Search of an Understandable Consensus Algorithm" (Raft)
- "Dynamo: Amazon's Highly Available Key-value Store"
- "Bigtable: A Distributed Storage System for Structured Data"
- "The Google File System"
- "MapReduce: Simplified Data Processing on Large Clusters"
- "Spanner: Google's Globally Distributed Database"
- "Kafka: a Distributed Messaging System for Log Processing"
- "ZooKeeper: Wait-free Coordination for Internet-scale Systems"
- "Chord: A Scalable Peer-to-peer Lookup Service"
- "Paxos Made Simple"

---

## 3. System Design Framework 📐

### 4-Step Structure
1. **Scope** (5 min): Clarify requirements, agree on features
2. **Estimate** (5 min): Traffic (DAU, QPS), storage, bandwidth
3. **Design** (20 min): High-level architecture + deep dive
4. **Wrap** (5 min): Tradeoffs, failure modes, future improvements

### Template
```markdown
# Design: [System Name]

## 1. Requirements
Functional:
- Feature A
- Feature B

Non-functional:
- Latency < 200ms (p99)
- 99.99% availability
- Scale: 100M DAU, 10K writes/s

## 2. Capacity Estimation
Traffic: 100M DAU, 10 writes/user/day = ~12K QPS avg, 60K peak
Storage: 10KB/user = 1TB/day = 365TB/year (with 3x replication = ~1PB)
Bandwidth: 100KB/response × 100K reads/s × 8 = 80 Gbps

## 3. High-Level Design
[ASCII Diagram / System components]

## 4. Deep Dives
Database: [SQL/NoSQL, schema, partitioning]
Caching: [Redis, CDN, cache strategy]
Data Flow: [Write path, read path]

## 5. Tradeoffs
- Why SQL over NoSQL?
- Why sync over async?
- Why single-region over multi-region for MVP?
```

---

## 4. System Design Problems 🏗️

### 30+ Problems (Ranked by Complexity)

**Tier 1 — Warm Up**
1. Design URL Shortener (tinyurl.com)
2. Design Pastebin
3. Design Rate Limiter
4. Design Consistent Hashing

**Tier 2 — Standard**
5. Design Twitter / News Feed
6. Design Chat System (WhatsApp)
7. Design Search Autocomplete
8. Design Web Crawler
9. Design Key-Value Store
10. Design Instagram
11. Design Dropbox / Google Drive
12. Design YouTube / Netflix

**Tier 3 — Hard**
13. Design Uber / Ride Sharing
14. Design Amazon E-Commerce
15. Design Ticketmaster (flash sales)
16. Design Google Maps / Navigation
17. Design WhatsApp / Messenger
18. Design Zoom / Video Conferencing
19. Design Distributed Message Queue (Kafka)
20. Design Distributed Cache (Redis)
21. Design Distributed Database (Spanner)

**Tier 4 — Expert**
22. Design S3 / Blob Store
23. Design Google Search
24. Design Discord (real-time + voice)
25. Design Slack (real-time messaging + search)
26. Design GitHub (large-scale git operations)
27. Design Airbnb / Booking.com
28. Design Twitter Trending Topics
29. Design Online Judge (LeetCode)
30. Design Collaborative Editor (Google Docs)

---

## 5. Coding Patterns 📝

### Pattern Catalog
- **Sliding Window**: Subarray sum, longest substring
- **Two Pointers**: Palindrome, container with most water
- **Fast & Slow Pointer**: Cycle detection, middle of linked list
- **Binary Search**: Search sorted array, rotated array
- **BFS / DFS**: Tree traversal, graph search, shortest path
- **Backtracking**: Permutations, combinations, N-Queens
- **Dynamic Programming**: Fibonacci, knapsack, LCS, LIS
- **Greedy**: Interval scheduling, coin change
- **Merge Intervals**: Overlap, insertion, meeting rooms
- **Cyclic Sort**: Find missing/duplicate in 1..n
- **Tree BFS/DFS**: Level order, right side view, LCA
- **Topological Sort**: Course schedule, dependency resolution
- **Union Find**: Connected components, redundant connection
- **Trie**: Autocomplete, word search, prefix matching
- **Monotonic Stack**: Next greater element, stock span

### LeetCode Study Plan
```
Week 1-2: Arrays, Strings, Hash Tables
Week 3-4: Linked Lists, Trees, Recursion
Week 5-6: Graphs, BFS/DFS, Backtracking
Week 7-8: Dynamic Programming
Week 9-10: Advanced (Trie, Union Find, Monotonic Stack)
Week 11-12: Mixed revision + timed mock tests
```

---

## 6. Behavioral Interviews 🗣️

### STAR Method
```
Situation: Context of the experience
Task: What needed to be done
Action: What YOU specifically did
Result: Outcome + what you learned
```

### Common Questions (30+)
- Tell me about a time you had to resolve a technical disagreement
- Describe a project where you took ownership beyond your role
- Tell me about a time you made a mistake. What happened?
- Describe a situation where you had to deliver under tight deadline
- How do you handle conflicting priorities?
- Tell me about a time you mentored someone
- Describe a technical decision you made and its tradeoffs
- Tell me about a failure and what you learned

### Amazon Leadership Principles
```
Customer Obsession        → "Work backwards from customer"
Ownership                 → "Never say 'that's not my job'"
Invent and Simplify       → "Find elegant solutions"
Bias for Action           → "80% ready is better than 100% never"
Dive Deep                 → "Understand root cause"
Deliver Results           → "Get it done, no excuses"
Have Backbone             → "Disagree and commit"
Hire and Develop the Best → "Raise the bar"
```

### Google Googleyness
- Comfort with ambiguity
- Collaboration across teams
- Intellectual humility
- Growth mindset
- Bias to action

---

## 7. FAANG-Specific Preparation 🏢

### Amazon
- Leadership Principles are ESSENTIAL — prepare 2 stories per LP
- System Design: Focus on scalability, fault tolerance
- Bar Raiser: Senior engineer evaluates if you raise the bar
- Coding: Usually LeetCode Medium (rarely Hard)
- Work backwards from customer requirements

### Google
- Googleyness + Cognitive ability (structured problem-solving)
- System Design: Very deep dives, multiple rounds
- Coding: LeetCode Medium-Hard, algorithmic focus
- Generalist approach (any language, any domain)
- Known for harder-than-average interviews

### Meta (Facebook)
- Coding: Speed matters — 2 problems per round
- System Design: Focus on product design (News Feed, Messenger)
- Behavioral: "Tell me about yourself" + conflict resolution
- Fast-paced, practical approach

### Netflix
- Focus on judgment and decision-making
- "High performance" culture — no process over results
- System Design: Content delivery, streaming architecture
- Fewer rounds, but each one very deep

### Microsoft
- More structured, less intense than Google/Meta
- Design questions are practical, product-oriented
- ASK (Attributes, Skills, Knowledge) methodology
- "What would you do if..." situational questions

---

## 8. Mock Interviews 🎭

### How to Practice
1. **Peer mocks**: Pair with a friend — 45 min each
2. **Platforms**: Pramp, Interviewing.io, Meetapro
3. **Record yourself**: Audio/video, review playback
4. **Time yourself**: Strict 45 min per session
5. **Rotate roles**: Interviewer + interviewee

### Mock Interview Checklist
```
Before:
  🟢 Set topic (coding / system design / behavioral)
  🟢 Prepare question (or use known problem)
  🟢 Set timer (45 min)

During:
  🟢 Think out loud
  🟢 Clarify requirements
  🟢 Write clean code / draw clear diagrams
  🟢 Consider edge cases
  🟢 Discuss tradeoffs

After:
  🟢 Interviewer gives feedback (5-10 min)
  🟢 What went well?
  🟢 What to improve?
  🟢 Next step (harder problem, different area)
```

---

## 9. Company-Specific Tips 🎯

| Company | Focus | Difficulty | Unique Aspect |
|---------|-------|------------|---------------|
| Amazon | LP stories, scalable design | Medium | Bar Raiser |
| Google | Algorithms, deep design | Hard | Googleyness |
| Meta | Speed coding, product design | Medium | 2 problems/round |
| Netflix | Judgment, culture fit | Medium | Freedom & Responsibility |
| Microsoft | Structured, situational | Medium-Low | ASK methodology |
| Stripe | API design, payments | Medium | Write real code |
| Uber | Real-time, geo systems | Medium-Hard | Dispatch design |
| Airbnb | Product design, full stack | Medium | Host/guest experience |
| Databricks | Spark, distributed systems | Hard | Tech depth |
| Snowflake | Data architecture | Hard | Warehouse design |

---

## 10. Resume & Strategy 📄

### Resume Tips
- **One page** (2 max for senior/staff+)
- **Action-impact format**: "Improved X by Y% by implementing Z"
- **Quantified results**: "Reduced latency by 40%", "Handled 10K QPS"
- **Keywords**: Match job description, include tech stack
- **No fluff**: Remove "Responsible for", "Worked on"

### Application Strategy
```
1. Reach out (referral is best — 10x higher response rate)
2. Apply directly (2-3 companies at a time)
3. Phone screens (keep practicing)
4. On-sites (2-3 weeks of focused prep per batch)
5. Offers (negotiate!)
```

### Timeline
```
4-8 weeks total prep:
  Week 1-2: Coding patterns, system design foundations
  Week 3-4: Mock interviews, behavioral prep
  Week 5-6: Company-specific deep dives
  Week 7-8: Applications + interviews
```

---

## 📚 Learning Path

### Phase 1: Foundation (2 weeks)
1. LeetCode patterns (50 Easy, 50 Medium)
2. System design framework (templates)
3. STAR stories (5-6 stories)

### Phase 2: Deepening (2 weeks)
1. LeetCode (100 Medium, 20 Hard)
2. System design practice (10 problems)
3. Mock interviews (4-6 sessions)

### Phase 3: Reinforcement (1-2 weeks)
1. Timed coding practice (45 min per problem)
2. System design whiteboarding
3. Behavioral refinement
4. Company-specific research

---

## 🔗 Related Domains

| Domain | Connection |
|--------|-----------|
| [System Design](../15-system-design/README.md) | Design problems, case studies |
| [Distributed Systems](../09-distributed-systems/README.md) | Consensus, replication, papers |
| [Java](java/README.md) | Java interview questions, JVM |
| [Coding](coding/README.md) | LeetCode patterns, practice problems |
| [Behavioral](behavioral/README.md) | STAR stories, leadership principles |
| [Low-Level Design](../24-low-level-design/README.md) | OOP design, class/sequence diagrams |

---

## 🧠 Simplest Mental Model

```
Interview = Performance + Signal + Fit

Performance: Can you solve problems under pressure?
  → Practice coding until it's automatic

Signal: Would the team be better with you?
  → Demonstrate depth in system design + distributed systems

Fit: Would the team enjoy working with you?
  → Be humble, curious, and collaborative

The Best Preparation:
  - Explain concepts to others (teach = learn)
  - Write code daily (even 30 min)
  - Read system design case studies
  - Practice mock interviews (10+)
```

**You're not being tested on what you know — you're being tested on how you think when you don't know.**

---

**Next**: [Roadmaps](../21-roadmaps/README.md) · [Low-Level Design](../24-low-level-design/README.md)
