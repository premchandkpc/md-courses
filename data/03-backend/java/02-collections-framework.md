# 📚 Java Collections Framework — Complete Deep Dive

**Related**: [OOP Concepts](01-oop-concepts.md) · [Generics](08-generics.md) · [Streams & Lambda](07-streams-lambda.md) · [Exception Handling](03-exception-handling.md)

---

## Table of Contents

- [Collection Hierarchy](#-collection-hierarchy)
- [1. List Interface](#1-list-interface)
- [2. Set Interface](#2-set-interface)
- [3. Queue Interface](#3-queue-interface)
- [4. Map Interface](#4-map-interface)
- [5. Comparable vs Comparator](#5-comparable-vs-comparator)
- [6. Utility Methods (Collections & Arrays)](#6-utility-methods)
- [7. Synchronized vs Concurrent Collections](#7-synchronized-vs-concurrent-collections)
- [8. Immutable Collections](#8-immutable-collections)
- [9. Performance Comparison](#9-performance-comparison)
- [10. Internal Working Flows](#10-internal-working-flows)
- [Common Pitfalls](#-common-pitfalls)
- [Simplest Mental Model](#-simplest-mental-model)

---

## 🧭 Collection Hierarchy

```text
                    ┌────────────────────────────────┐
                    │     Iterable (interface)       │
                    └────────────┬───────────────────┘
                                 │
                    ┌────────────┴───────────────────┐
                    │     Collection (interface)     │
                    └──────┬─────────┬───────┬───────┘
                           │         │       │
              ┌────────────┘         │       └────────────┐
              ▼                      ▼                    ▼
      ┌──────────────┐      ┌──────────────┐     ┌──────────────┐
      │    List      │      │     Set      │     │    Queue     │
      │ (interface)  │      │ (interface)  │     │ (interface)  │
      ├──────────────┤      ├──────────────┤     ├──────────────┤
      │ ArrayList    │      │ HashSet      │     │ LinkedList   │
      │ LinkedList   │      │ LinkedHashSet│     │ PriorityQueue│
      │ Vector       │      │ TreeSet      │     │ ArrayDeque   │
      │ Stack        │      │ EnumSet      │     │              │
      └──────────────┘      └──────────────┘     └──────────────┘

                           ┌──────────────────┐
                           │   Map (interface) │ (separate hierarchy!)
                           ├──────────────────┤
                           │ HashMap          │
                           │ LinkedHashMap    │
                           │ TreeMap          │
                           │ ConcurrentHashMap│
                           │ EnumMap          │
                           │ IdentityHashMap  │
                           │ WeakHashMap      │
                           └──────────────────┘
```

```mermaid
mindmap
  root((Collections))
    List
      ArrayList
        Fast random access
        Backed by array
      LinkedList
        Fast insert/delete
        Doubly linked
    Set
      HashSet
        O(1) operations
        Hash table backed
      TreeSet
        Sorted order
        Red-Black tree
      LinkedHashSet
        Insertion order
        Hash + linked list
    Queue
      LinkedList
        FIFO queue
      PriorityQueue
        Min-heap
      ArrayDeque
        Resizable array
    Map
      HashMap
        O(1) get/put
      TreeMap
        Sorted keys
        Red-Black tree
      LinkedHashMap
        Insertion/access order
      ConcurrentHashMap
        Thread-safe
```

---

## 1. List Interface

**Definition**: Ordered collection (sequence). Allows duplicates. Index-based access.

### ArrayList

```java
// Internal: resizable array (Object[])
List<String> list = new ArrayList<>();

list.add("Apple");       // [Apple]
list.add("Banana");      // [Apple, Banana]
list.add(0, "Apricot");  // [Apricot, Apple, Banana]
String fruit = list.get(1);  // "Apple"
list.remove(0);          // [Apple, Banana]
list.contains("Apple");  // true
list.size();             // 2
```

### ArrayList Internal Working

```text
Initial: Object[] DEFAULTCAPACITY_EMPTY_ELEMENTDATA = {}
                                   │
         add("Apple")              │
                                   ▼
                    ┌─────────────────────┐
                    │ ensureCapacity()    │
                    │ size == 0, create   │
                    │ new Object[10]      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ elementData[0] =    │
                    │ "Apple"             │
                    │ size = 1            │
                    └─────────────────────┘

         add("Banana", "Cherry"... up to 10)
                                   │
         add("Date")  (11th element) │
                                   ▼
                    ┌─────────────────────┐
                    │ grow()              │
                    │ newCapacity = 10 +  │
                    │ 10 >> 1 = 15       │
                    │ new Object[15]      │
                    │ arraycopy(old, new) │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ elementData[10] =   │
                    │ "Date"              │
                    │ size = 11           │
                    └─────────────────────┘
```

### LinkedList

```java
// Internal: doubly-linked list (Node objects)
List<String> list = new LinkedList<>();

list.add("First");
list.add("Last");
list.add(1, "Middle");
String first = list.getFirst();   // "First"
String last = list.getLast();     // "Last"
list.removeFirst();               // remove "First"
```

### LinkedList Node Structure

```text
LinkedList<String> list = new LinkedList<>();

add("A") →  [null ◄──► "A" ◄──► null]   ← first = last = nodeA

add("B") →  [null ◄──► "A" ◄──► "B" ◄──► null]
                         ↑ first    ↑ last

add("C") →  [null ◄──► "A" ◄──► "B" ◄──► "C" ◄──► null]
                         ↑ first             ↑ last

Node structure:
┌──────────────────────────────┐
│         Node<String>         │
├──────────────────────────────┤
│   Node prev                  │
│   String item                │
│   Node next                  │
└──────────────────────────────┘
```

### ArrayList vs LinkedList

| Operation | ArrayList | LinkedList |
|-----------|-----------|------------|
| `add(E)` at end | O(1)* amortized | O(1) |
| `add(i, E)` insert | O(n) shift | O(n) traverse + O(1) link |
| `get(i)` | O(1) random access | O(n) traverse |
| `remove(i)` | O(n) shift | O(n) traverse + O(1) unlink |
| `remove(0)` | O(n) shift | O(1) unlink first |
| Memory overhead | Low (array) | High (3 pointers per node) |
| Iterator.remove | O(n) shift | O(1) |
| Best for | Random access, read-heavy | Frequent insert/remove at head/tail |

---

## 2. Set Interface

**Definition**: Collection with no duplicates. At most one null.

### HashSet

```java
// Internal: backed by HashMap (uses PRESENT dummy value)
Set<String> set = new HashSet<>();

set.add("Apple");     // true
set.add("Banana");    // true
set.add("Apple");     // false (duplicate)
set.contains("Apple"); // true
set.size();           // 2
```

### HashSet Internal Flow

```text
set.add("Apple")

    │
    ▼
┌─────────────────────────┐
│ "Apple".hashCode()      │
│ → h = 42 (example)      │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ index = (n-1) & hash    │
│ → bucket 2              │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Check bucket 2:         │
│   null? → insert new    │
│   Node(key="Apple",     │
│        value=PRESENT)   │
│   size++                │
│   return true           │
└─────────────────────────┘

set.add("Banana") where Banana.hashCode() also → bucket 2

    │
    ▼
┌─────────────────────────┐
│ "Banana".hashCode()      │
│ → index = 2 (collision)  │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Check bucket 2:         │
│   Node("Apple")         │
│   Compare keys:         │
│   "Apple".equals("Banana") │
│   → false → different   │
│   → chain: Node("Banana") │
│   → next of Apple       │
│   size++                │
│   return true           │
└─────────────────────────┘
```

### TreeSet

```java
// Internal: Red-Black tree. Elements sorted by Comparator or natural order.
Set<Integer> set = new TreeSet<>();

set.add(5);
set.add(1);
set.add(3);

// Always sorted
System.out.println(set);  // [1, 3, 5]

// Navigation methods (NavigableSet)
TreeSet<Integer> tree = new TreeSet<>(Set.of(1, 3, 5, 7, 9));
tree.first();    // 1
tree.last();     // 9
tree.lower(5);   // 3 (greatest < 5)
tree.higher(5);  // 7 (least > 5)
tree.floor(4);   // 3 (greatest ≤ 4)
tree.ceiling(4); // 5 (least ≥ 4)
tree.subSet(3, 8);   // [3, 5, 7] (range view)
```

### LinkedHashSet

```java
// Hash table + linked list → insertion order preserved
Set<String> set = new LinkedHashSet<>();

set.add("Z");
set.add("A");
set.add("M");
System.out.println(set);  // [Z, A, M] — insertion order
```

### Set Comparison

| Set | Order | Null | Performance | Internal |
|-----|-------|------|-------------|----------|
| HashSet | None | One null | O(1) | HashMap |
| LinkedHashSet | Insertion | One null | O(1) | HashMap + LinkedList |
| TreeSet | Sorted (Comparable/Comparator) | No null | O(log n) | Red-Black Tree |
| EnumSet | Enum ordinal | No null | O(1) bit vector | Bit flags |

---

## 3. Queue Interface

### LinkedList (as Queue)

```java
Queue<String> queue = new LinkedList<>();

queue.offer("First");    // add to tail — [First]
queue.offer("Second");   // [First, Second]
queue.offer("Third");    // [First, Second, Third]

queue.peek();    // "First" (head, don't remove)
queue.poll();    // "First" (remove head) → [Second, Third]
queue.element(); // "Second" (throws if empty)
```

### PriorityQueue (Min-Heap)

```java
// Natural ordering (min-heap)
Queue<Integer> pq = new PriorityQueue<>();
pq.offer(5);
pq.offer(1);
pq.offer(3);

pq.peek();  // 1 (smallest)
pq.poll();  // 1 → [3, 5]
pq.poll();  // 3 → [5]

// Custom comparator (max-heap)
Queue<Integer> maxPq = new PriorityQueue<>(Comparator.reverseOrder());
```

### PriorityQueue Internal (Heap)

```text
Initial: empty array
             │
pq.add(5)    │
             ▼
        ┌─────────┐
        │    5    │  index 0
        └─────────┘

pq.add(1)
             │
             ▼
        ┌─────────┐
        │    5    │  index 0
        │    1    │  index 1
        └─────────┘
             │  siftUp(1): 1 < 5 → swap
             ▼
        ┌─────────┐
        │    1    │  index 0  ← min (root)
        │    5    │  index 1
        └─────────┘

pq.add(3)
             │
             ▼
        ┌─────────┐
        │    1    │  index 0
        │    5    │  index 1
        │    3    │  index 2
        └─────────┘
             │  siftUp(2): 3 < 5? yes, swap
             ▼
        ┌─────────┐
        │    1    │  index 0
        │    3    │  index 1
        │    5    │  index 2
        └─────────┘
```

### Deque (Double-Ended Queue)

```java
Deque<String> deque = new ArrayDeque<>();

deque.addFirst("First");
deque.addLast("Last");
deque.addFirst("NewFirst");

// [NewFirst, First, Last]
deque.getFirst();  // "NewFirst"
deque.getLast();   // "Last"
deque.removeFirst();  // "NewFirst"
deque.removeLast();   // "Last"

// Stack operations
deque.push("A");    // addFirst
deque.pop();        // removeFirst
```

### Queue Comparison

| Queue | Order | Thread-safe? | Structure |
|-------|-------|-------------|-----------|
| LinkedList (as Queue) | FIFO | No | Doubly-linked list |
| PriorityQueue | Priority (heap) | No | Object[] binary heap |
| ArrayDeque | FIFO / LIFO | No | Resizable array |
| ConcurrentLinkedQueue | FIFO | Yes (non-blocking) | Lock-free linked list |
| LinkedBlockingQueue | FIFO | Yes (blocking) | Linked list + locks |
| ArrayBlockingQueue | FIFO | Yes (blocking) | Circular array + locks |
| DelayQueue | delayed expiry | Yes | PriorityQueue + lock |
| SynchronousQueue | handoff | Yes | No capacity (rendezvous) |

---

## 4. Map Interface

### HashMap

```java
Map<String, Integer> map = new HashMap<>();

map.put("Apple", 10);
map.put("Banana", 5);
map.put("Apple", 15);  // overwrite → {Apple=15, Banana=5}

map.get("Apple");     // 15
map.getOrDefault("Cherry", 0);  // 0
map.containsKey("Banana");  // true
map.containsValue(5);       // true

// Iteration
for (Map.Entry<String, Integer> entry : map.entrySet()) {
    System.out.println(entry.getKey() + " → " + entry.getValue());
}

// Java 8+ useful methods
map.putIfAbsent("Date", 3);
map.computeIfAbsent("Elderberry", k -> k.length());
map.merge("Apple", 5, Integer::sum);  // Apple = 20
```

### HashMap Internal (Java 8+)

```text
                    ┌─────────────────────────┐
                    │  HashMap<K,V>           │
                    │  Node<K,V>[] table      │
                    │  (power of 2 size)      │
                    │  default: 16 buckets    │
                    └─────────────────────────┘

put("key", value) flow:
    │
    ▼
┌───────────────────────┐
│ hash = (h = key.hashCode()) ^ (h >>> 16)
│ → spread high bits    │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ index = (n - 1) & hash│
│ → bucket position     │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ table[index] == null? │
│   YES → new Node(hash,│
│          key, value,  │
│          null)        │
│   NO  → collision     │
│          │            │
│          ▼            │
│   ┌───────────────┐   │
│   │ equals check  │   │
│   │ on each node  │   │
│   │ in chain/tree │   │
│   └───────┬───────┘   │
│           │           │
│   found?  ├──YES→ overwrite value
│           │           │
│           └──NO → append node
│                   or tree node
└───────────────────────┘

Tree Thresholds:
  TREEIFY_THRESHOLD = 8   (convert list → tree)
  UNTREEIFY_THRESHOLD = 6 (convert tree → list)
  MIN_TREEIFY_CAPACITY = 64

Resizing:
  loadFactor = 0.75 (default)
  threshold = capacity * loadFactor
  When size > threshold:
    newCap = oldCap << 1  (double)
    redistribute nodes to new buckets
```

### LinkedHashMap

```java
// Insertion order (default)
Map<String, Integer> map = new LinkedHashMap<>();
map.put("Z", 1);
map.put("A", 2);
map.put("M", 3);
System.out.println(map);  // {Z=1, A=2, M=3}

// Access order (useful for LRU cache)
LinkedHashMap<String, Integer> lru = new LinkedHashMap<>(16, 0.75f, true) {
    @Override
    protected boolean removeEldestEntry(Map.Entry eldest) {
        return size() > 100;  // auto-evict oldest
    }
};
```

### TreeMap

```java
// Sorted map — Red-Black tree
TreeMap<String, Integer> map = new TreeMap<>();
map.put("Z", 1);
map.put("A", 2);
map.put("M", 3);

System.out.println(map);  // {A=2, M=3, Z=1}

// Navigation
map.firstKey();       // "A"
map.lastKey();        // "Z"
map.lowerKey("M");    // "A" (greatest < M)
map.higherKey("M");   // "Z" (least > M)
map.subMap("A", "Z"); // {A=2, M=3} (half-open)

// Custom comparator
TreeMap<Integer, String> custom = new TreeMap<>(Comparator.reverseOrder());
```

### Map Comparison

| Map | Order | Null keys | Null values | Performance | Internal |
|-----|-------|-----------|-------------|-------------|----------|
| HashMap | None | One | Many | O(1) avg | Node[] array |
| LinkedHashMap | Insertion/Access | One | Many | O(1) avg | HashMap + DLL |
| TreeMap | Sorted | No | Yes | O(log n) | Red-Black tree |
| ConcurrentHashMap | None | No | No | O(1) avg | CAS + synchronized |
| Hashtable | None | No | No | O(1) avg | Synchronized array |
| EnumMap | Enum ordinal | No | Yes | O(1) | Array |
| WeakHashMap | None | Yes | Yes | O(1) avg | WeakReference keys |
| IdentityHashMap | Identity (==) | Yes | Yes | O(1) avg | Linear probing |

---

## 5. Comparable vs Comparator

### Comparable (Natural Ordering)

```java
class Student implements Comparable<Student> {
    private String name;
    private int grade;

    public Student(String name, int grade) {
        this.name = name;
        this.grade = grade;
    }

    // Natural ordering by grade
    @Override
    public int compareTo(Student other) {
        return Integer.compare(this.grade, other.grade);
    }

    @Override
    public String toString() {
        return name + ":" + grade;
    }
}

// Usage
List<Student> students = Arrays.asList(
    new Student("Alice", 85),
    new Student("Bob", 92),
    new Student("Charlie", 78)
);

Collections.sort(students);  // sorted by grade: [Charlie:78, Alice:85, Bob:92]
```

### Comparator (Custom Ordering)

```java
// Multiple comparators for different sort criteria
class StudentComparators {
    // By name (ascending)
    static final Comparator<Student> BY_NAME =
        Comparator.comparing(Student::getName);

    // By grade (descending)
    static final Comparator<Student> BY_GRADE_DESC =
        Comparator.comparingInt(Student::getGrade).reversed();

    // By grade then by name
    static final Comparator<Student> BY_GRADE_THEN_NAME =
        Comparator.comparingInt(Student::getGrade)
                  .thenComparing(Student::getName);

    // Null-safe
    static final Comparator<Student> NULL_SAFE =
        Comparator.nullsLast(BY_NAME);
}

// Usage
students.sort(StudentComparators.BY_NAME);
students.sort(StudentComparators.BY_GRADE_THEN_NAME);
```

### Comparable vs Comparator

| Aspect | Comparable | Comparator |
|--------|------------|------------|
| Package | `java.lang` | `java.util` |
| Method | `compareTo(T o)` | `compare(T o1, T o2)` |
| Returns | `int` (negative, zero, positive) | Same |
| Modifying class | Requires changing the class | External — no class change |
| Single vs Multiple | Single natural order | Many custom orders |
| Functional interface | Yes | Yes |
| Common pattern | `implements Comparable<MyClass>` | Anonymous class / lambda |

---

## 6. Utility Methods

### Collections Class

```java
List<Integer> list = new ArrayList<>(Arrays.asList(3, 1, 4, 1, 5));

// Sorting
Collections.sort(list);                          // [1, 1, 3, 4, 5]
Collections.sort(list, Comparator.reverseOrder()); // [5, 4, 3, 1, 1]

// Searching (must be sorted first)
Collections.binarySearch(list, 3);  // index of 3

// Shuffle
Collections.shuffle(list);

// Reverse
Collections.reverse(list);

// Fill
Collections.fill(list, 0);  // [0, 0, 0, 0, 0]

// Copy
List<Integer> dest = new ArrayList<>(Collections.nCopies(5, 0));
Collections.copy(dest, source);  // source into dest

// Min/Max
Collections.min(list);
Collections.max(list);

// Frequency
Collections.frequency(list, 1);

// Disjoint (no common elements?)
Collections.disjoint(listA, listB);

// Unmodifiable wrappers
Collections.unmodifiableList(list);
Collections.unmodifiableSet(set);
Collections.unmodifiableMap(map);

// Synchronized wrappers
Collections.synchronizedList(new ArrayList<>());
Collections.synchronizedMap(new HashMap<>());
```

### Arrays Class

```java
int[] arr = {3, 1, 4, 1, 5};

// Sort
Arrays.sort(arr);  // [1, 1, 3, 4, 5]
Arrays.sort(arr, 0, 3);  // sort partial range

// Binary search (sorted array)
Arrays.binarySearch(arr, 3);

// Fill
Arrays.fill(arr, 0);

// Copy
int[] copy = Arrays.copyOf(arr, arr.length);
int[] range = Arrays.copyOfRange(arr, 1, 4);

// Compare
Arrays.equals(arr1, arr2);
Arrays.deepEquals(objArr1, objArr2);  // for nested arrays

// Convert to List (fixed-size)
List<Integer> list = Arrays.asList(1, 2, 3);

// Stream
Arrays.stream(arr).sum();

// Parallel prefix
Arrays.parallelPrefix(arr, Integer::sum);

// Set all in parallel
Arrays.parallelSetAll(arr, i -> i * i);
```

---

## 7. Synchronized vs Concurrent Collections

### Legacy Synchronized Wrappers

```java
// Collections.synchronized* — every method is synchronized
List<String> syncList = Collections.synchronizedList(new ArrayList<>());
Map<String, Integer> syncMap = Collections.synchronizedMap(new HashMap<>());

// Must manually synchronize iteration!
synchronized (syncList) {
    for (String s : syncList) {
        // safe iteration
    }
}
```

### Modern Concurrent Collections

```java
// ConcurrentHashMap — fine-grained locking (Java 8+: CAS + synchronized)
Map<String, Integer> concMap = new ConcurrentHashMap<>();
concMap.put("A", 1);
concMap.get("A");   // non-blocking reads
concMap.putIfAbsent("A", 2);  // atomic

// ConcurrentLinkedQueue — lock-free (CAS)
Queue<String> concQueue = new ConcurrentLinkedQueue<>();

// CopyOnWriteArrayList — snapshot iteration (best for read-heavy)
List<String> cowList = new CopyOnWriteArrayList<>();
cowList.add("A");  // creates new copy of array

// CopyOnWriteArraySet
Set<String> cowSet = new CopyOnWriteArraySet<>();

// BlockingQueue — producer-consumer
BlockingQueue<String> bq = new LinkedBlockingQueue<>(100);
bq.put("item");      // blocks if full
String item = bq.take();  // blocks if empty
```

### Synchronized vs Concurrent

| Aspect | Synchronized Wrapper | Concurrent Collection |
|--------|---------------------|----------------------|
| Lock | Coarse (whole collection) | Fine-grained / CAS |
| Read concurrency | Blocked | Non-blocking |
| Iteration | Fail-fast, needs external sync | Weakly consistent (no ConcurrentModificationException) |
| Throughput | Lower (contention) | Higher |
| `null` | Allowed | Not allowed (CQ, CHM, etc.) |
| Composite ops | Need external sync | `putIfAbsent`, `replace`, `compute` are atomic |
| Memory overhead | Low | Moderate |

---

## 8. Immutable Collections

### Java 9+ Factory Methods

```java
// Unmodifiable (immutable) collections
List<String> list = List.of("A", "B", "C");
Set<Integer> set = Set.of(1, 2, 3);
Map<String, Integer> map = Map.of("A", 1, "B", 2);
Map<String, Integer> entryMap = Map.ofEntries(
    Map.entry("A", 1),
    Map.entry("B", 2)
);

// Cannot modify — throws UnsupportedOperationException
list.add("D");  // ❌
```

### Immutable via Collections.unmodifiable*

```java
List<String> mutable = new ArrayList<>(Arrays.asList("A", "B"));
List<String> immutable = Collections.unmodifiableList(mutable);

// But original reference still mutable!
mutable.add("C");  // immutable also changes! (view)

// True immutability: copy first then wrap
List<String> trulyImmutable = Collections.unmodifiableList(
    new ArrayList<>(Arrays.asList("A", "B"))
);
```

### Immutable vs Unmodifiable

| Aspect | `List.of()` | `Collections.unmodifiableList()` |
|--------|-------------|----------------------------------|
| Mutability | Deeply immutable | View — changes if source changes |
| Null | ❌ NullPointerException | Allowed |
| Memory | Compact (field-based for small sizes) | Normal wrapper |
| Serialization | Preserves immutability | Wrapper serialized |
| Since | Java 9 | Java 1.2 |

---

## 9. Performance Comparison

### Big-O Complexity

| Collection | Add | Get | Contains | Next | Remove |
|------------|-----|-----|----------|------|--------|
| ArrayList | O(1)* | O(1) | O(n) | O(1) | O(n) |
| LinkedList | O(1) | O(n) | O(n) | O(1) | O(1) |
| CopyOnWriteArrayList | O(n) | O(1) | O(n) | O(1) | O(n) |
| HashSet | O(1)* | - | O(1)* | O(h/n) | O(1)* |
| LinkedHashSet | O(1)* | - | O(1)* | O(1) | O(1)* |
| TreeSet | O(log n) | - | O(log n) | O(log n) | O(log n) |
| PriorityQueue | O(log n) | O(1)* | O(n) | - | O(log n) |
| ArrayDeque | O(1) | O(1) | O(n) | O(1) | O(1) |
| HashMap | O(1)* | O(1)* | O(1)* | O(h/n) | O(1)* |
| TreeMap | O(log n) | O(log n) | O(log n) | O(log n) | O(log n) |
| ConcurrentHashMap | O(1)* | O(1)* | O(1)* | O(h/n) | O(1)* |

* * = with good hash distribution. Worst case O(n) for hash-based.

### Memory Footprint

| Collection | Per-Element Overhead | Notes |
|------------|---------------------|-------|
| ArrayList | 4 bytes (reference) | Underlying Object[] |
| LinkedList | ~24 bytes (prev + next + item) | Node objects |
| HashSet | ~32 bytes (HashMap.Node) | HashMap$Node |
| HashMap | ~32 bytes (Node) | hash + key + value + next |
| TreeSet/TreeMap | ~40 bytes (Entry) | parent + left + right + color |
| ConcurrentHashMap | ~40 bytes (Node) | hash + key + value + next (+ CAS) |
| ArrayDeque | 4 bytes (reference) | Circular Object[] |
| PriorityQueue | 4 bytes (reference) | Object[] backing |

---

## 10. Internal Working Flows

### HashMap Resize Flow

```text
HashMap: initial capacity = 16, loadFactor = 0.75
threshold = 16 * 0.75 = 12

put() 1..12 → no resize
put() 13   → threshold exceeded!
             │
             ▼
┌─────────────────────────────────┐
│ resize()                        │
│ newCap = oldCap << 1 = 32       │
│ newThr = oldThr << 1 = 24       │
│ Node<K,V>[] newTab = new Node[32]│
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ Rehash each node:               │
│                                 │
│ For each bucket:                │
│   (e.hash & oldCap) == 0?       │
│   → stays at same index         │
│   else → moves to index + oldCap│
│                                 │
│ Why? Since newCap = oldCap * 2, │
│ the bit we test is the new MSB  │
└─────────────────────────────────┘

Example:
  oldCap=16 (10000 binary)
  hash of key:    10101  (21)
  old index:      10101 & 01111 = 5
  new MSB test:   10101 & 10000 = 1 → move
  new index:      5 + 16 = 21
```

### ArrayList Growth Flow

```text
ArrayList list = new ArrayList();  // DEFAULTCAPACITY_EMPTY_ELEMENTDATA

add 1st element → ensureCapacityInternal(1)
    │
    ▼
┌─────────────────────┐
│ calculateCapacity   │
│ = Math.max(10, 1)  │
│ = 10               │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ ensureExplicitCapacity(10) │
│ modCount++          │
│ 10 > 0 → grow()    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ grow()              │
│ oldCapacity = 0     │
│ newCapacity = 0 +   │
│ max(0 >> 1, minGrowth)│
│ = max(0, 10) = 10   │
│ new Object[10]      │
└─────────────────────┘

Add 11th element → grow()
    │
    ▼
┌─────────────────────┐
│ oldCapacity = 10    │
│ newCapacity = 10 +  │
│ (10 >> 1) = 15     │
│ new Object[15]      │
│ Arrays.copyOf()    │
└─────────────────────┘

Growth formula: new = old + (old >> 1) = 1.5x
```

### TreeMap Put Flow (Red-Black Tree)

```text
put(K key, V value)
    │
    ▼
┌─────────────────────────────┐
│ root == null?               │
│   YES → root = new Node()  │
│   NO  → compare key        │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Traverse tree:              │
│ cmp < 0 → go left          │
│ cmp > 0 → go right         │
│ cmp == 0 → replace value   │
└──────────┬──────────────────┘
           │
           ▼ (inserted as leaf)
┌─────────────────────────────┐
│ fixAfterInsertion()         │
│ 1. Color new node RED       │
│ 2. While violations:        │
│    - Uncle RED? → recolor   │
│    - Uncle BLACK? → rotate  │
│ 3. Root always BLACK        │
└─────────────────────────────┘

Rotation Types:
  Left rotate    ──  Right rotate
  Left-Right     ──  Right-Left (double)
```

---

## ⚠️ Common Pitfalls

| Pitfall | Issue | Fix |
|---------|-------|-----|
| `==` on keys in HashMap | Wrong object used | Proper `equals()` + `hashCode()` |
| Modify during foreach | `ConcurrentModificationException` | Use Iterator or concurrent collection |
| Forgetting initial capacity | Frequent resize overhead | `new HashMap<>(expectedSize / 0.75f + 1)` |
| `ArrayList.toArray()` | Returns `Object[]` — cast fails | Use `toArray(new T[0])` |
| `Arrays.asList()` is fixed-size | `add()`/`remove()` throws | `new ArrayList<>(Arrays.asList(...))` |
| `List.of()` elements are immutable | `set()` throws | Use mutable list if needed |
| `Comparator` inconsistent with `equals` | TreeSet/TreeMap misbehavior | Ensure consistency |
| Mutable fields in `hashCode()` | Broken after map insertion | Use immutable keys |
| `null` in TreeSet/TreeMap | NPE | Check nulls first |
| Iterating synchronized collection without sync | Race condition | Synchronize on collection during iteration |

---

## 🧠 Simplest Mental Model

```text
ARRAYLIST      =  A filing cabinet. You can grab any file by its number instantly (O(1)).
                  But adding a new file at the front means shuffling everything (O(n)).

LINKEDLIST     =  A treasure hunt with clues. Each clue points to the next.
                  Adding in the middle is easy (just change a clue).
                  But finding item #100 means following 99 clues (O(n)).

HASHSET        =  Coat check room. You give them your coat, they give you a number.
                  When you return, you give the number, get the coat instantly.
                  No two people get the same number.

HASHMAP        =  Dictionary. Word (key) → Definition (value).
                  Hash function tells you which page to look at instantly.

TREESET/MAP    =  Library sorted by Dewey Decimal. Always in order.
                  Finding any book takes log(n) steps.
                  You can ask: what's the next book? what books are between X and Y?

PRIORITYQUEUE  =  Hospital ER triage. The most critical patient is treated first,
                  regardless of when they arrived.
```

---

**Next**: [Exception Handling](03-exception-handling.md) — try-catch-finally, checked/unchecked, best practices
