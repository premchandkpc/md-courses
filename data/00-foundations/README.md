# 00 — Foundations

The bedrock of all software engineering. This domain covers the essential computer science theory, mathematical underpinnings, and core programming concepts that every engineer—regardless of specialization—must master. Without these foundations, higher-level topics (distributed systems, AI, compilers) rest on sand.

## Table of Contents

- [Computer Science Core](#computer-science-core)
  - [Data Structures & Algorithms](#data-structures--algorithms)
  - [Computational Complexity](#computational-complexity)
  - [Boolean Algebra & Logic](#boolean-algebra--logic)
  - [Automata Theory](#automata-theory)
  - [Discrete Mathematics](#discrete-mathematics)
- [Programming Paradigms](#programming-paradigms)
  - [Imperative & Procedural](#imperative--procedural)
  - [Object-Oriented Programming](#object-oriented-programming)
  - [Functional Programming](#functional-programming)
  - [Declarative Programming](#declarative-programming)
  - [Concurrent & Parallel Programming](#concurrent--parallel-programming)
- [Core CS Topics](#core-cs-topics)
  - [Computer Architecture](#computer-architecture)
  - [Operating Systems Concepts](#operating-systems-concepts)
  - [Compilers & Interpreters](#compilers--interpreters)
  - [Memory Management](#memory-management)
- [Learning Path](#learning-path)
- [Cross-References](#cross-references)

---

## Computer Science Core

### Data Structures & Algorithms

Fundamental data organizations and the algorithms that operate on them. Topics include:

- **Arrays & Strings** — contiguous memory, dynamic arrays, string algorithms (KMP, Rabin-Karp, Trie)
- **Linked Lists** — singly, doubly, circular; pointer manipulation, Floyd's cycle detection
- **Stacks & Queues** — LIFO/FIFO, monotonic stack, deque, priority queue
- **Hash Tables** — hash functions, collision resolution (chaining, open addressing), load factor, consistent hashing
- **Trees** — binary trees, BST, AVL, red-black, B-trees, segment trees, Fenwick trees
- **Heaps** — binary heap, Fibonacci heap, heap operations, heap sort
- **Graphs** — representation (adjacency matrix/list), BFS, DFS, topological sort, shortest paths (Dijkstra, Bellman-Ford, Floyd-Warshall), MST (Kruskal, Prim), max flow (Ford-Fulkerson)
- **Searching & Sorting** — binary search, quicksort, mergesort, heapsort, counting sort, radix sort
- **Dynamic Programming** — memoization, tabulation, knapSack, LCS, LIS, DP on trees/graphs
- **Greedy Algorithms** — interval scheduling, Huffman coding, minimum spanning trees
- **Bit Manipulation** — bitwise operators, XOR tricks, bit masks, population count

### Computational Complexity

- **Big-O Notation** — upper/lower/tight bounds, amortized analysis
- **P vs NP** — complexity classes, NP-completeness, reductions
- **Space Complexity** — memory usage analysis, in-place algorithms
- **Master Theorem** — solving recurrences, divide-and-conquer analysis

### Boolean Algebra & Logic

- **Boolean Operators** — AND, OR, NOT, XOR, NAND, NOR; truth tables
- **Logic Gates** — combinational vs sequential, flip-flops, adders, multiplexers
- **Karnaugh Maps** — logic minimization, don't-care conditions
- **Propositional & Predicate Logic** — quantifiers, inference rules, resolution
- **Digital Logic Design** — half/full adders, ALU, registers, memory cells

### Automata Theory

- **Finite Automata** — DFA, NFA, epsilon-NFA; subset construction; DFA minimization
- **Regular Languages** — regular expressions, pumping lemma, Myhill-Nerode
- **Context-Free Grammars** — CFG, parse trees, Chomsky normal form, CYK algorithm
- **Pushdown Automata** — PDA, equivalence with CFGs
- **Turing Machines** — decidability, halting problem, undecidability
- **Computability** — recursive and recursively enumerable languages, Church-Turing thesis

### Discrete Mathematics

- **Set Theory** — unions, intersections, cartesian products, power sets
- **Combinatorics** — permutations, combinations, pigeonhole principle, inclusion-exclusion
- **Graph Theory** — vertices, edges, paths, cycles, Eulerian/Hamiltonian, coloring
- **Number Theory** — modular arithmetic, GCD, primes, RSA foundations
- **Probability** — sample spaces, conditional probability, Bayes theorem, random variables

---

## Programming Paradigms

### Imperative & Procedural

Statements that change program state. C, Fortran, Pascal. The foundational model of most modern languages. Key concepts: variables, loops, conditionals, subroutines, scope.

### Object-Oriented Programming

Encapsulation, inheritance, polymorphism, abstraction. SOLID principles, design patterns (GoF), composition vs inheritance. Languages: Java, C++, Python, TypeScript, C#.

### Functional Programming

Pure functions, immutability, referential transparency, higher-order functions, closures, currying, monads, functors. Languages: Haskell, Scala, Clojure, Elixir, F#. Functional features now appear in most mainstream languages (lambdas in Java, Python, JS).

### Declarative Programming

SQL, Prolog, HTML, CSS, configuration languages. Express *what* to do, not *how*. Domain-specific languages, logic programming, constraint programming.

### Concurrent & Parallel Programming

Threads, processes, async/await, coroutines, actors (Akka, Erlang), CSP (Go channels), data parallelism, SIMD, GPU programming (CUDA, OpenCL). Race conditions, deadlocks, livelocks, lock-free data structures.

---

## Core CS Topics

### Computer Architecture

- CPU pipelines, hazards, branch prediction
- Cache hierarchy (L1/L2/L3), cache coherency (MESI)
- Memory hierarchy, NUMA, virtual memory, TLB
- Instruction set architectures (x86, ARM, RISC-V)
- SIMD, vectorization, out-of-order execution

### Operating Systems Concepts

- Processes and threads, context switching, scheduling
- Virtual memory, paging, segmentation
- File systems, I/O models (blocking, non-blocking, async, io_uring)
- Inter-process communication (pipes, sockets, shared memory, signals)
- Synchronization primitives (mutex, semaphore, spinlock, futex)

### Compilers & Interpreters

- Lexical analysis, parsing (recursive descent, LR, LALR)
- Abstract syntax trees, intermediate representations
- Optimization passes (constant folding, loop unrolling, inlining)
- Code generation, register allocation
- JIT compilation, AOT compilation, interpretation

### Memory Management

- Stack vs heap allocation
- Manual memory management (malloc/free)
- Garbage collection (mark-sweep, copying, generational, reference counting)
- RAII, ownership (Rust), ARC (Swift)
- Memory pools, arena allocators, slab allocators
- Fragmentation (internal/external), compaction

---

## Learning Path

1. **Stage 1** — Discrete math, basic data structures (arrays, linked lists, stacks, queues), sorting/searching, Big-O analysis
2. **Stage 2** — Trees, graphs, hash tables, recursion, dynamic programming, greedy algorithms
3. **Stage 3** — Boolean algebra, digital logic, automata theory, computability
4. **Stage 4** — Programming paradigms (OOP, FP, concurrent), design patterns
5. **Stage 5** — Computer architecture, OS concepts, compilers, memory management

Study resources: CLRS (Introduction to Algorithms), SICP, Structure and Interpretation of Computer Programs, The Art of Computer Programming (Knuth), Computer Systems: A Programmer's Perspective (CS:APP).

---

## Cross-References

| Domain | Connection |
|--------|-----------|
| [01 — AI/ML](../01-ai-ml/) | Linear algebra, probability, optimization underpin all ML; algorithmic thinking critical for model design |
| [08 — Databases](../08-databases/) | B-trees, hash indexes, sorting algorithms are database internals; complexity analysis drives query optimization |
| [09 — Distributed Systems](../09-distributed-systems/) | Consensus algorithms, distributed computing theory build on automata and complexity foundations |
| [11 — Networking](../11-networking/) | Packet flow, TCP congestion control, routing algorithms apply queueing theory and graph algorithms |
| [12 — Operating Systems](../12-operating-systems/) | OS concepts (processes, memory, scheduling) are applied foundations; directly extends architecture topics |
| [17 — Software Architecture](../17-software-architecture/) | Design patterns, architectural styles, and system decomposition are applied OOP and modularity principles |
| [18 — Performance Engineering](../18-performance-engineering/) | Complexity analysis, memory hierarchy, cache behavior, algorithmic optimization all rooted here |
| [24 — Low Level Design](../24-low-level-design/) | LLD applies OOP, design patterns, and data structure selection to real-world component design |
