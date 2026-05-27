# Big O Complexity Cheat Sheet

Quick reference for algorithm and data structure complexity analysis.

## Time Complexity Order

From fastest to slowest:
```
O(1) < O(log n) < O(n) < O(n log n) < O(n²) < O(n³) < O(2ⁿ) < O(n!)
```

## Common Complexities

| Notation | Name | Example |
|----------|------|---------|
| **O(1)** | Constant | Array access by index, hash table lookup |
| **O(log n)** | Logarithmic | Binary search, balanced BST operations |
| **O(n)** | Linear | Array iteration, string search |
| **O(n log n)** | Linearithmic | Merge sort, quick sort (avg), heap sort |
| **O(n²)** | Quadratic | Bubble sort, insertion sort, nested loops |
| **O(n³)** | Cubic | Triple nested loops, matrix multiplication (naive) |
| **O(2ⁿ)** | Exponential | Fibonacci (recursive), subset generation |
| **O(n!)** | Factorial | Permutation generation |

## Data Structure Complexities

### Array
| Operation | Average | Worst |
|-----------|---------|-------|
| Access | O(1) | O(1) |
| Search | O(n) | O(n) |
| Insert | O(n) | O(n) |
| Delete | O(n) | O(n) |

### Hash Table
| Operation | Average | Worst |
|-----------|---------|-------|
| Access | O(1) | O(n) |
| Search | O(1) | O(n) |
| Insert | O(1) | O(n) |
| Delete | O(1) | O(n) |

### Binary Search Tree
| Operation | Average | Worst |
|-----------|---------|-------|
| Search | O(log n) | O(n) |
| Insert | O(log n) | O(n) |
| Delete | O(log n) | O(n) |

### Balanced BST (AVL, Red-Black)
| Operation | Average | Worst |
|-----------|---------|-------|
| Search | O(log n) | O(log n) |
| Insert | O(log n) | O(log n) |
| Delete | O(log n) | O(log n) |

### Heap (Min/Max)
| Operation | Complexity |
|-----------|-----------|
| Insert | O(log n) |
| Delete Min/Max | O(log n) |
| Find Min/Max | O(1) |
| Heapify | O(n) |

### Graph (adjacency list)
| Operation | Complexity |
|-----------|-----------|
| DFS | O(V + E) |
| BFS | O(V + E) |
| Dijkstra | O((V + E) log V) |
| Bellman-Ford | O(VE) |
| Floyd-Warshall | O(V³) |
| Kruskal | O(E log E) |
| Prim | O((V + E) log V) |

## Sorting Algorithms

| Algorithm | Best | Average | Worst | Space | Stable |
|-----------|------|---------|-------|-------|--------|
| Bubble Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Insertion Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Selection Sort | O(n²) | O(n²) | O(n²) | O(1) | No |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) | Yes |
| Quick Sort | O(n log n) | O(n log n) | O(n²) | O(log n) | No |
| Heap Sort | O(n log n) | O(n log n) | O(n log n) | O(1) | No |
| Count Sort | O(n + k) | O(n + k) | O(n + k) | O(k) | Yes |
| Radix Sort | O(nk) | O(nk) | O(nk) | O(n + k) | Yes |

## Space Complexity

| Data Structure | Space |
|---|---|
| Array (n elements) | O(n) |
| Linked List (n elements) | O(n) |
| Hash Table (n elements) | O(n) |
| BST (n elements) | O(n) |
| Heap (n elements) | O(n) |

## Rules of Thumb

1. **Drop constants**: O(2n) → O(n), O(3n²) → O(n²)
2. **Drop lower-order terms**: O(n² + n) → O(n²), O(n log n + n) → O(n log n)
3. **Dominant term**: Multiply for nested loops, add for sequential operations
4. **Recursion**: T(n) = T(n-1) + O(1) → O(n), T(n) = 2·T(n/2) + O(n) → O(n log n)

## Quick Estimation

**For n = 1,000,000:**
- O(log n) ≈ 20 operations
- O(n) ≈ 1,000,000 operations (instant)
- O(n log n) ≈ 20,000,000 operations (fast, <1s)
- O(n²) ≈ 10¹² operations (seconds to minutes)
- O(2ⁿ) ≈ impossible to compute

**Time to compute 10⁸ operations ≈ 1 second on modern CPU**

## When to Use

| Goal | Complexity | Example |
|------|-----------|---------|
| Maximum speed | O(1) | Caching, hash tables |
| Very fast | O(log n) | Binary search |
| Fast | O(n) or O(n log n) | Sorting, linear scan |
| Acceptable | O(n log n) | Most problems |
| Slow | O(n²) | Small inputs only |
| Very slow | O(2ⁿ) | Only for small n (<20) |
