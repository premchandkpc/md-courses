---
title: Data Structures & Algorithms — Core Reference
topic: 00-foundations
difficulty: beginner
time: 30m
paths:
  - backend-junior
---

# Data Structures & Algorithms — Core Reference

Data structures organize data; algorithms operate on them. Mastery of both is the single highest-leverage skill for technical interviews and writing efficient software.

## Complexity Analysis

| Notation | Name | Meaning |
|----------|------|---------|
| O(1) | Constant | Time independent of input size |
| O(log n) | Logarithmic | Halving the problem (binary search, balanced BST) |
| O(n) | Linear | Single pass through input |
| O(n log n) | Linearithmic | Divide and conquer (merge sort, heapsort) |
| O(n²) | Quadratic | Nested loops (bubble sort, naive matrix multiply) |
| O(2ⁿ) | Exponential | Subset enumeration (TSP brute force) |
| O(n!) | Factorial | Permutation enumeration |

**Amortized Analysis**: average cost over a sequence of operations. Example: dynamic array resizing — occasional O(n) inserts, but amortized O(1).

## Linear Data Structures

| Structure | Access | Search | Insert | Delete | Notes |
|-----------|--------|--------|--------|--------|-------|
| Array | O(1) | O(n) | O(n) | O(n) | Contiguous memory, cache-friendly |
| ArrayList/DynamicArray | O(1) | O(n) | O(n) | O(n) | Amortized O(1) append |
| Linked List (Singly) | O(n) | O(n) | O(1)* | O(1)* | *at head; no random access |
| Linked List (Doubly) | O(n) | O(n) | O(1)* | O(1)* | *if node reference held |
| Stack | O(n) | O(n) | O(1) | O(1) | LIFO; push/pop at top |
| Queue | O(n) | O(n) | O(1) | O(1) | FIFO; enqueue/dequeue |

## Hash-Based Structures

**Hash Table**: key → value mapping via hash function. O(1) average, O(n) worst case.

- **Collision Resolution**: separate chaining (linked list per bucket), open addressing (linear/quadratic probing, double hashing)
- **Load Factor**: `α = n/m`; resizing threshold typically 0.75
- **Consistent Hashing**: minimizes reorganization when the hash table is resized; used in distributed caches (Memcached, DynamoDB)

**Bloom Filter**: probabilistic set membership — false positives possible, false negatives impossible. Uses k hash functions on a bit array of size m. Applications: cache filtering, spell check, duplicate detection.

## Trees

| Tree | Ops | Key Property |
|------|-----|-------------|
| Binary Search Tree (BST) | O(h) | Left < root < right; can degenerate to O(n) |
| AVL Tree | O(log n) | Height-balanced; rotations maintain balance factor ≤ 1 |
| Red-Black Tree | O(log n) | Color constraints; O(1) rotations per insertion |
| B-Tree | O(log n) | Multi-way; high fanout; database index foundation |
| Trie | O(k) | Prefix tree; k = key length; autocomplete, spell check |
| Segment Tree | O(log n) | Range queries (sum, min, max) with point updates |
| Fenwick Tree (BIT) | O(log n) | Prefix sums; simpler than segment tree; less memory |

### Tree Traversals
- **Preorder**: root → left → right (copy tree)
- **Inorder**: left → root → right (sorted order for BST)
- **Postorder**: left → right → root (delete tree)
- **Level-order**: BFS using queue

## Heaps

| Heap | Insert | Extract-Min | Decrease-Key | Merge |
|------|--------|-------------|-------------|-------|
| Binary Heap | O(log n) | O(log n) | O(log n) | O(n) |
| Fibonacci Heap | O(1) | O(log n) | O(1)* | O(1) |
| Binomial Heap | O(log n) | O(log n) | O(log n) | O(log n) |

*amortized. Used in Dijkstra's algorithm for sparse graphs.

## Graph Algorithms

| Algorithm | Complexity | Use Case |
|-----------|-----------|----------|
| BFS | O(V + E) | Shortest path (unweighted), level-order |
| DFS | O(V + E) | Topological sort, connected components, cycles |
| Dijkstra | O((V+E) log V) | Shortest path (non-negative weights) |
| Bellman-Ford | O(VE) | Shortest path (negative weights, cycle detection) |
| Floyd-Warshall | O(V³) | All-pairs shortest path |
| Kruskal (MST) | O(E log E) | Minimum spanning tree via Union-Find |
| Prim (MST) | O(E log V) | Minimum spanning tree via heap |
| Ford-Fulkerson | O(E·max\|f\|) | Maximum flow |
| Topological Sort | O(V + E) | Dependency ordering (DAG) |

## Sorting Algorithms

| Algorithm | Best | Average | Worst | Space | Stable |
|-----------|------|---------|-------|-------|--------|
| Quick Sort | O(n log n) | O(n log n) | O(n²) | O(log n) | No |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) | Yes |
| Heap Sort | O(n log n) | O(n log n) | O(n log n) | O(1) | No |
| Insertion Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Counting Sort | O(n+k) | O(n+k) | O(n+k) | O(k) | Yes |

## Dynamic Programming

**Core Pattern**: optimal substructure + overlapping subproblems.

| Approach | Style | Space |
|----------|-------|-------|
| Top-down (Memoization) | Recursive + cache | O(n) call stack + O(n) cache |
| Bottom-up (Tabulation) | Iterative table | O(n) table (can be optimized) |

**Classic Problems**:
- 0/1 Knapsack, Unbounded Knapsack
- Longest Common Subsequence (LCS)
- Longest Increasing Subsequence (LIS) — O(n log n) with patience sorting
- Edit Distance (Levenshtein)
- Matrix Chain Multiplication
- Subset Sum

## Learning Path

1. Complexity analysis and basic structures (array, linked list, stack, queue)
2. Sorting and searching (binary search, quick/merge sort)
3. Trees and graphs (BST, tree traversals, BFS, DFS)
4. Hash tables and heaps
5. Dynamic programming and greedy algorithms
6. Advanced: segment trees, tries, flow algorithms, string algorithms

## Visualizations

- [Sorting Algorithm Visualizer](sorting-viz.html) — watch Quick, Merge, Heap, and Insertion Sort race with live bar animations
- [Hash Table Collision Visualizer](hash-table-viz.html) — see separate chaining resolve collisions with live load factor tracking
- [BST Traversal Visualizer](tree-traversal-viz.html) — step through Preorder, Inorder, Postorder, and Level-order traversals
- [Big O Growth Curves](complexity-viz.html) — animated comparison of O(1) through O(2ⁿ) scaling

**Practice**: LeetCode (150+ problems), HackerRank, Codility, competitive programming platforms.
