# Java Collections: Complete Reference Guide

## Overview

Java Collections Framework provides reusable data structures. Organized by interface hierarchy:
- **Collection** → List, Set, Queue
- **Map** (standalone hierarchy)

---

## 1. LIST COLLECTIONS

### 1.1 ArrayList

**Purpose:** Resizable array. O(1) random access. O(n) insertions/deletions in middle.

```java
// Basic operations
ArrayList<String> list = new ArrayList<>();
list.add("Apple");
list.add("Banana");
list.add(0, "Avocado");  // Insert at index
System.out.println(list); // [Avocado, Apple, Banana]

// Iteration scenarios
for (String fruit : list) System.out.println(fruit);
for (int i = 0; i < list.size(); i++) System.out.println(list.get(i));
list.forEach(System.out::println);

// Performance characteristics
ArrayList<Integer> numbers = new ArrayList<>();
for (int i = 0; i < 1_000_000; i++) numbers.add(i);
long start = System.nanoTime();
int value = numbers.get(500_000);  // O(1) - nanoseconds
long elapsed = System.nanoTime() - start;
System.out.println("Random access: " + elapsed + "ns");  // ~50-100ns

// Removal scenarios
numbers.remove(500_000);  // O(n) - shifts all elements right
list.removeIf(s -> s.length() > 5);  // Conditional removal

// Capacity management
ArrayList<String> managed = new ArrayList<>(100);  // Initial capacity
managed.ensureCapacity(1000);  // Preallocate
managed.trimToSize();  // Release unused space

// Fail-fast iterator
Iterator<String> iter = list.iterator();
list.add("Cherry");  // Structural modification
try {
    while (iter.hasNext()) {
        System.out.println(iter.next());  // ConcurrentModificationException
    }
} catch (ConcurrentModificationException e) {
    System.out.println("Iterator invalidated by external modification");
}

// Sublist creates view (not copy)
List<String> sublist = list.subList(0, 2);
sublist.clear();
System.out.println(list);  // Changes original list

// Sorting
Collections.sort(list);
list.sort(String::compareTo);
```

**Complexity:**
- Random access: O(1)
- Insert/Delete at end: O(1) amortized
- Insert/Delete middle: O(n)
- Search: O(n)

---

### 1.2 LinkedList

**Purpose:** Doubly-linked list. O(1) insertions/deletions at ends. O(n) random access.

```java
// Deque interface (both ends)
LinkedList<Integer> linked = new LinkedList<>();
linked.addFirst(1);    // Add to head
linked.addLast(2);     // Add to tail
linked.add(3);         // addLast by default
System.out.println(linked);  // [1, 2, 3]

int first = linked.getFirst();  // 1
int last = linked.getLast();    // 3
int removed = linked.removeFirst();  // O(1)

// Queue interface
linked.offer(4);       // enqueue
int head = linked.poll();  // dequeue and remove
int peek = linked.peek();  // peek without removal

// Performance comparison vs ArrayList
LinkedList<Integer> linkPerf = new LinkedList<>();
ArrayList<Integer> arrPerf = new ArrayList<>();
for (int i = 0; i < 100_000; i++) {
    linkPerf.add(i);
    arrPerf.add(i);
}

// Random access comparison
long start = System.nanoTime();
int value = arrPerf.get(50_000);  // O(1) - ~100ns
long arrTime = System.nanoTime() - start;

start = System.nanoTime();
value = linkPerf.get(50_000);  // O(n) - ~1,000,000ns
long linkTime = System.nanoTime() - start;

System.out.println("ArrayList random access: " + arrTime + "ns");
System.out.println("LinkedList random access: " + linkTime + "ns");
System.out.println("Ratio: " + (linkTime / arrTime) + "x slower");

// Insertion at beginning
ArrayList<Integer> arrInsert = new ArrayList<>(Collections.nCopies(10_000, 1));
LinkedList<Integer> linkInsert = new LinkedList<>(arrInsert);

start = System.nanoTime();
for (int i = 0; i < 100; i++) arrInsert.add(0, i);  // O(n) per insertion
long arrInsertTime = System.nanoTime() - start;

start = System.nanoTime();
for (int i = 0; i < 100; i++) linkInsert.addFirst(i);  // O(1) per insertion
long linkInsertTime = System.nanoTime() - start;

System.out.println("ArrayList addFirst: " + arrInsertTime + "ns");
System.out.println("LinkedList addFirst: " + linkInsertTime + "ns");

// Iterator usage (optimal for LinkedList)
long startIter = System.nanoTime();
for (Integer num : linkInsert) {
    int x = num * 2;  // O(1) per iteration
}
long iterTime = System.nanoTime() - startIter;

// Manual index access (pessimal for LinkedList)
start = System.nanoTime();
for (int i = 0; i < linkInsert.size(); i++) {
    int x = linkInsert.get(i) * 2;  // O(n) total, O(n) per get
}
long indexTime = System.nanoTime() - start;

System.out.println("LinkedList iterator: " + iterTime + "ns");
System.out.println("LinkedList index access: " + indexTime + "ns");
System.out.println("Iterator is " + (indexTime / iterTime) + "x faster");
```

**Use LinkedList when:**
- Frequent insertions/deletions at ends
- Use iterator (not random access)
- Implement Stack/Queue/Deque

**Avoid for:**
- Random access patterns
- Memory-constrained (overhead per node)

---

### 1.3 CopyOnWriteArrayList

**Purpose:** Thread-safe list. Writes create full copy. Reads very fast, no locks.

```java
// Thread-safe without explicit synchronization
CopyOnWriteArrayList<String> copyList = new CopyOnWriteArrayList<>();

// Multiple threads reading
ExecutorService executor = Executors.newFixedThreadPool(4);
for (int t = 0; t < 4; t++) {
    executor.submit(() -> {
        // No locks, very fast reads
        for (int i = 0; i < 1_000_000; i++) {
            copyList.forEach(System.out::print);
        }
    });
}

// Single thread modifying
executor.submit(() -> {
    for (int i = 0; i < 10; i++) {
        copyList.add("Item-" + i);
        Thread.sleep(100);
    }
});

executor.shutdown();
executor.awaitTermination(1, TimeUnit.MINUTES);

// Iterator snapshot (safe from concurrent modification)
CopyOnWriteArrayList<Integer> snapshot = new CopyOnWriteArrayList<>(
    Arrays.asList(1, 2, 3, 4, 5)
);
Iterator<Integer> iter = snapshot.iterator();
snapshot.add(6);  // Doesn't affect iterator
while (iter.hasNext()) {
    System.out.println(iter.next());  // Still sees [1,2,3,4,5]
}

// Cost of write operations
long start = System.nanoTime();
for (int i = 0; i < 1000; i++) {
    snapshot.add(i);  // Creates full copy internally - O(n)
}
long writeTime = System.nanoTime() - start;
System.out.println("CopyOnWriteArrayList 1000 writes: " + writeTime + "ns");

// Compare with synchronized ArrayList
List<Integer> syncList = Collections.synchronizedList(
    new ArrayList<>(Arrays.asList(1, 2, 3, 4, 5))
);
start = System.nanoTime();
for (int i = 0; i < 1000; i++) {
    syncList.add(i);  // Lock per operation - O(1)
}
long syncWriteTime = System.nanoTime() - start;
System.out.println("Synchronized ArrayList 1000 writes: " + syncWriteTime + "ns");
System.out.println("CopyOnWrite is " + (writeTime / syncWriteTime) + "x slower for writes");
```

**Trade-offs:**
- **Pros:** Thread-safe, super-fast reads, safe iteration snapshots
- **Cons:** Expensive writes (full copy), memory overhead
- **Use when:** Read-heavy with occasional writes (listener lists, read-mostly caches)

---

### 1.4 Vector (Legacy)

**Purpose:** Synchronized ArrayList (legacy, pre-Java 5). Avoid in new code.

```java
Vector<String> vector = new Vector<>();
vector.add("A");
vector.add("B");

// Synchronized methods
synchronized (vector) {  // Still need explicit sync for iteration
    for (String s : vector) {
        System.out.println(s);
    }
}

// Performance: worse than ArrayList, worse than CopyOnWriteArrayList
ArrayList<String> arr = new ArrayList<>(Collections.nCopies(1000, "x"));
Vector<String> vec = new Vector<>(arr);

long start = System.nanoTime();
for (int i = 0; i < 1_000_000; i++) {
    arr.get(500);
}
long arrTime = System.nanoTime() - start;

start = System.nanoTime();
for (int i = 0; i < 1_000_000; i++) {
    vec.get(500);  // Synchronized - slower
}
long vecTime = System.nanoTime() - start;

System.out.println("ArrayList: " + arrTime + "ns");
System.out.println("Vector: " + vecTime + "ns");
System.out.println("Vector is " + (vecTime / arrTime) + "x slower");
```

**Status:** Deprecated. Use ArrayList + synchronization or CopyOnWriteArrayList.

---

### 1.5 Stack (Legacy)

**Purpose:** LIFO data structure. Extends Vector (poor design, avoid).

```java
// Legacy (extends Vector)
Stack<Integer> legacyStack = new Stack<>();
legacyStack.push(1);
legacyStack.push(2);
legacyStack.push(3);
int top = legacyStack.pop();  // 3
int peek = legacyStack.peek();  // 2

// Better: Use ArrayDeque (no synchronization overhead)
Deque<Integer> stack = new ArrayDeque<>();
stack.push(1);
stack.push(2);
stack.push(3);
top = stack.pop();  // 3
peek = stack.peek();  // 2

// Stack use cases: expression evaluation
String expr = "3+4)*2";
Deque<Character> parenStack = new ArrayDeque<>();
boolean balanced = true;
for (char c : expr.toCharArray()) {
    if (c == '(') parenStack.push(c);
    else if (c == ')') {
        if (parenStack.isEmpty()) {
            balanced = false;
            break;
        }
        parenStack.pop();
    }
}
if (!parenStack.isEmpty()) balanced = false;
System.out.println("Balanced: " + balanced);  // false (extra ')')

// Recursive depth tracking
class RecursiveProcessor {
    private Deque<Integer> callStack = new ArrayDeque<>();
    
    int process(int depth) {
        if (depth == 0) return 1;
        callStack.push(depth);
        int result = process(depth - 1);
        callStack.pop();
        System.out.println("Stack depth: " + callStack.size());
        return result + depth;
    }
}
```

**Recommendation:** Use `Deque<T>` with `ArrayDeque<T>` instead.

---

## 2. SET COLLECTIONS

### 2.1 HashSet

**Purpose:** Unordered unique elements. O(1) average operations (hash table).

```java
// Basic operations
HashSet<String> fruits = new HashSet<>();
fruits.add("Apple");
fruits.add("Banana");
fruits.add("Apple");  // Duplicate ignored
System.out.println(fruits);  // [Apple, Banana] or [Banana, Apple]
System.out.println(fruits.size());  // 2

// Contains check
boolean hasApple = fruits.contains("Apple");  // O(1)

// Removal
fruits.remove("Apple");  // O(1)
fruits.removeIf(s -> s.length() > 5);  // Removes "Banana"

// Null handling
HashSet<String> nullSet = new HashSet<>();
nullSet.add(null);
nullSet.add("value");
System.out.println(nullSet.contains(null));  // true
System.out.println(nullSet.size());  // 2

// Unordered iteration
HashSet<Integer> nums = new HashSet<>(Arrays.asList(5, 1, 3, 2, 4));
for (Integer n : nums) System.out.println(n);  // Random order

// Set operations
HashSet<Integer> set1 = new HashSet<>(Arrays.asList(1, 2, 3, 4));
HashSet<Integer> set2 = new HashSet<>(Arrays.asList(3, 4, 5, 6));

// Union
HashSet<Integer> union = new HashSet<>(set1);
union.addAll(set2);
System.out.println("Union: " + union);  // [1, 2, 3, 4, 5, 6]

// Intersection
HashSet<Integer> intersection = new HashSet<>(set1);
intersection.retainAll(set2);
System.out.println("Intersection: " + intersection);  // [3, 4]

// Difference
HashSet<Integer> difference = new HashSet<>(set1);
difference.removeAll(set2);
System.out.println("Difference: " + difference);  // [1, 2]

// Custom object with hashCode/equals
class User {
    int id;
    String name;
    
    User(int id, String name) { this.id = id; this.name = name; }
    
    @Override
    public boolean equals(Object o) {
        if (!(o instanceof User)) return false;
        User user = (User) o;
        return id == user.id;  // Only ID matters
    }
    
    @Override
    public int hashCode() {
        return Integer.hashCode(id);
    }
}

HashSet<User> users = new HashSet<>();
users.add(new User(1, "Alice"));
users.add(new User(1, "Alice2"));  // Same ID, ignored
users.add(new User(2, "Bob"));
System.out.println(users.size());  // 2

// Hash collision handling
HashSet<Integer> collisions = new HashSet<>();
for (int i = 0; i < 1_000_000; i++) {
    collisions.add(i);
}
long start = System.nanoTime();
boolean found = collisions.contains(999_999);  // O(1) even with 1M elements
long time = System.nanoTime() - start;
System.out.println("Contains check 1M elements: " + time + "ns");  // ~100-200ns

// Performance degradation with bad hashCode
class BadHash {
    int value;
    BadHash(int value) { this.value = value; }
    
    @Override
    public int hashCode() {
        return 1;  // All hash same bucket - O(n) lookups
    }
    
    @Override
    public boolean equals(Object o) {
        return this == o;
    }
}

HashSet<BadHash> badSet = new HashSet<>();
for (int i = 0; i < 10_000; i++) {
    badSet.add(new BadHash(i));
}
BadHash target = badSet.iterator().next();
start = System.nanoTime();
badSet.contains(target);  // O(n) due to collision chain
long badTime = System.nanoTime() - start;
System.out.println("Bad hashCode lookup time: " + badTime + "ns");  // ~10,000x slower
```

**Complexity:**
- Add/Remove/Contains: O(1) average, O(n) worst case (hash collisions)
- Iteration: O(n)
- Space: O(n)

---

### 2.2 LinkedHashSet

**Purpose:** Like HashSet but maintains insertion order. O(1) operations with ordering.

```java
// Insertion order preserved
LinkedHashSet<String> linked = new LinkedHashSet<>();
linked.add("Zebra");
linked.add("Apple");
linked.add("Banana");
for (String s : linked) System.out.println(s);  // Zebra, Apple, Banana

// Access order variant (for caching)
LinkedHashSet<Integer> accessOrder = new LinkedHashSet<Integer>(16, 0.75f, true) {
    @Override
    protected boolean removeEldestEntry(Map.Entry eldest) {
        return size() > 5;  // LRU eviction
    }
};

for (int i = 1; i <= 10; i++) {
    accessOrder.add(i);
}
System.out.println(accessOrder);  // [6, 7, 8, 9, 10]

// Memory overhead vs HashSet
HashSet<String> hash = new HashSet<>(10_000);
LinkedHashSet<String> lhash = new LinkedHashSet<>(10_000);
for (int i = 0; i < 10_000; i++) {
    String s = "item-" + i;
    hash.add(s);
    lhash.add(s);
}

long start = System.nanoTime();
for (int i = 0; i < 1_000_000; i++) {
    hash.contains("item-5000");
}
long hashTime = System.nanoTime() - start;

start = System.nanoTime();
for (int i = 0; i < 1_000_000; i++) {
    lhash.contains("item-5000");
}
long lhashTime = System.nanoTime() - start;

System.out.println("HashSet: " + hashTime + "ns");
System.out.println("LinkedHashSet: " + lhashTime + "ns");
System.out.println("Overhead: " + ((double)lhashTime / hashTime) + "x");
```

**Use when:** Need insertion order + O(1) operations (e.g., tracking first-seen items).

---

### 2.3 TreeSet

**Purpose:** Sorted unique elements. O(log n) operations. Backed by TreeMap.

```java
// Sorted naturally
TreeSet<Integer> sorted = new TreeSet<>();
sorted.add(5);
sorted.add(1);
sorted.add(3);
sorted.add(2);
sorted.add(4);
for (Integer n : sorted) System.out.println(n);  // 1, 2, 3, 4, 5

// Custom comparator
TreeSet<String> byLength = new TreeSet<>(
    (a, b) -> {
        if (a.length() != b.length()) return a.length() - b.length();
        return a.compareTo(b);  // Tie-breaker
    }
);
byLength.add("apple");
byLength.add("a");
byLength.add("banana");
byLength.add("be");
for (String s : byLength) System.out.println(s);  // a, be, apple, banana

// Range queries
TreeSet<Integer> range = new TreeSet<>(Arrays.asList(1, 2, 3, 4, 5, 6, 7, 8, 9, 10));
System.out.println(range.headSet(5));  // [1, 2, 3, 4]
System.out.println(range.tailSet(5));  // [5, 6, 7, 8, 9, 10]
System.out.println(range.subSet(3, 7));  // [3, 4, 5, 6]

// Navigation methods
Integer lower = range.lower(5);  // Largest < 5 → 4
Integer floor = range.floor(5);  // Largest <= 5 → 5
Integer ceiling = range.ceiling(5);  // Smallest >= 5 → 5
Integer higher = range.higher(5);  // Smallest > 5 → 6
System.out.println("lower(5): " + lower);
System.out.println("floor(5): " + floor);
System.out.println("ceiling(5): " + ceiling);
System.out.println("higher(5): " + higher);

// Reverse order
TreeSet<Integer> reverse = new TreeSet<>(Collections.reverseOrder());
reverse.addAll(Arrays.asList(1, 2, 3, 4, 5));
for (Integer n : reverse) System.out.println(n);  // 5, 4, 3, 2, 1

// Performance vs HashSet (for sorted operations)
ArrayList<Integer> data = new ArrayList<>();
for (int i = 0; i < 100_000; i++) data.add((int)(Math.random() * 1_000_000));

long start = System.nanoTime();
HashSet<Integer> hashSet = new HashSet<>(data);
long hashCreateTime = System.nanoTime() - start;

start = System.nanoTime();
TreeSet<Integer> treeSet = new TreeSet<>(data);
long treeCreateTime = System.nanoTime() - start;

System.out.println("HashSet creation: " + hashCreateTime + "ns");
System.out.println("TreeSet creation: " + treeCreateTime + "ns");
System.out.println("TreeSet overhead: " + ((double)treeCreateTime / hashCreateTime) + "x");

// But TreeSet gives sorted iteration for free
start = System.nanoTime();
for (Integer n : hashSet) {
    int x = n;
}
long hashIterTime = System.nanoTime() - start;

start = System.nanoTime();
for (Integer n : treeSet) {
    int x = n;
}
long treeIterTime = System.nanoTime() - start;

System.out.println("HashSet iteration: " + hashIterTime + "ns");
System.out.println("TreeSet iteration: " + treeIterTime + "ns");
System.out.println("If you'd sort HashSet (nlogn), TreeSet is faster");
```

**Complexity:**
- Add/Remove/Contains: O(log n)
- First/Last: O(1)
- Iteration: O(n)
- Range operations: O(log n + k) where k = result size

---

### 2.4 ConcurrentSkipListSet

**Purpose:** Thread-safe sorted set. Lock-free, better than synchronized TreeSet.

```java
// Concurrent sorted set
ConcurrentSkipListSet<Integer> concurrent = new ConcurrentSkipListSet<>();

// Multiple threads writing concurrently (no explicit sync needed)
ExecutorService executor = Executors.newFixedThreadPool(4);
for (int t = 0; t < 4; t++) {
    final int threadId = t;
    executor.submit(() -> {
        for (int i = threadId; i < 1000; i += 4) {
            concurrent.add(i);
        }
    });
}
executor.shutdown();
executor.awaitTermination(10, TimeUnit.SECONDS);

System.out.println(concurrent.size());  // 1000
System.out.println(concurrent.first());  // 0
System.out.println(concurrent.last());  // 999

// Range queries thread-safe
NavigableSet<Integer> subset = concurrent.subSet(100, 200);
System.out.println("Range [100, 200): " + subset.size());

// Compare with Collections.synchronizedSortedSet (bad)
SortedSet<Integer> syncTreeSet = Collections.synchronizedSortedSet(
    new TreeSet<>(Arrays.asList(1, 2, 3, 4, 5))
);

// Still need explicit sync for iteration (!)
synchronized (syncTreeSet) {  // Surprising requirement
    for (Integer n : syncTreeSet) {
        System.out.println(n);
    }
}

// Performance under contention
long start = System.nanoTime();
int threadCount = 4;
executor = Executors.newFixedThreadPool(threadCount);
for (int t = 0; t < threadCount; t++) {
    executor.submit(() -> {
        ConcurrentSkipListSet<Integer> skipSet = new ConcurrentSkipListSet<>();
        for (int i = 0; i < 100_000; i++) {
            skipSet.add((int)(Math.random() * 1_000_000));
        }
    });
}
executor.shutdown();
executor.awaitTermination(1, TimeUnit.MINUTES);
long skipTime = System.nanoTime() - start;

start = System.nanoTime();
executor = Executors.newFixedThreadPool(threadCount);
for (int t = 0; t < threadCount; t++) {
    executor.submit(() -> {
        SortedSet<Integer> syncSet = Collections.synchronizedSortedSet(
            new TreeSet<>()
        );
        for (int i = 0; i < 100_000; i++) {
            syncSet.add((int)(Math.random() * 1_000_000));
        }
    });
}
executor.shutdown();
executor.awaitTermination(1, TimeUnit.MINUTES);
long syncTime = System.nanoTime() - start;

System.out.println("ConcurrentSkipListSet: " + skipTime + "ns");
System.out.println("Synchronized TreeSet: " + syncTime + "ns");
System.out.println("ConcurrentSkipListSet is " + ((double)skipTime / syncTime) + "x");
```

**Use when:** Need concurrent sorted set (better than synchronized TreeSet).

---

### 2.5 CopyOnWriteArraySet

**Purpose:** Thread-safe set via CopyOnWriteArrayList. Good for listener collections.

```java
CopyOnWriteArraySet<String> listeners = new CopyOnWriteArraySet<>();
listeners.add("Listener1");
listeners.add("Listener2");

// Multiple readers
ExecutorService executor = Executors.newFixedThreadPool(8);
for (int t = 0; t < 8; t++) {
    executor.submit(() -> {
        for (int i = 0; i < 1_000_000; i++) {
            listeners.contains("Listener1");
        }
    });
}

// Single writer
executor.submit(() -> {
    for (int i = 0; i < 100; i++) {
        listeners.add("Listener-" + i);
        Thread.sleep(1);
    }
});

executor.shutdown();
executor.awaitTermination(1, TimeUnit.MINUTES);

System.out.println("Final size: " + listeners.size());

// Duplicate handling
CopyOnWriteArraySet<Integer> set = new CopyOnWriteArraySet<>();
set.add(1);
set.add(1);  // Ignored
System.out.println(set.size());  // 1
```

**Trade-off:** Cheap reads, expensive writes (like CopyOnWriteArrayList).

---

## 3. QUEUE COLLECTIONS

### 3.1 PriorityQueue

**Purpose:** Min-heap by default. O(log n) add/remove, O(1) peek min.

```java
// Min-heap (natural order)
PriorityQueue<Integer> minHeap = new PriorityQueue<>();
minHeap.add(5);
minHeap.add(1);
minHeap.add(3);
minHeap.add(2);
System.out.println(minHeap.peek());  // 1 (minimum)
while (!minHeap.isEmpty()) {
    System.out.print(minHeap.poll() + " ");  // 1 2 3 5
}

// Max-heap
PriorityQueue<Integer> maxHeap = new PriorityQueue<>(Collections.reverseOrder());
maxHeap.addAll(Arrays.asList(5, 1, 3, 2));
System.out.println(maxHeap.peek());  // 5 (maximum)
while (!maxHeap.isEmpty()) {
    System.out.print(maxHeap.poll() + " ");  // 5 3 2 1
}

// Custom comparator for complex objects
class Task {
    int priority;
    String name;
    
    Task(int priority, String name) {
        this.priority = priority;
        this.name = name;
    }
    
    @Override
    public String toString() { return name + "(" + priority + ")"; }
}

PriorityQueue<Task> taskQueue = new PriorityQueue<>(
    Comparator.comparingInt(t -> t.priority)
);
taskQueue.add(new Task(5, "Low"));
taskQueue.add(new Task(1, "Critical"));
taskQueue.add(new Task(3, "Medium"));
while (!taskQueue.isEmpty()) {
    System.out.println(taskQueue.poll());  // Critical, Medium, Low
}

// Dijkstra's algorithm (typical use)
class Node implements Comparable<Node> {
    int id;
    int distance;
    
    Node(int id, int distance) {
        this.id = id;
        this.distance = distance;
    }
    
    @Override
    public int compareTo(Node o) {
        return Integer.compare(this.distance, o.distance);
    }
}

PriorityQueue<Node> dijkstra = new PriorityQueue<>();
dijkstra.add(new Node(1, 0));
dijkstra.add(new Node(2, 5));
dijkstra.add(new Node(3, 2));

while (!dijkstra.isEmpty()) {
    Node current = dijkstra.poll();
    System.out.println("Visit node " + current.id + " at distance " + current.distance);
}

// Not thread-safe
PriorityQueue<Integer> pq = new PriorityQueue<>();
pq.add(1);

// Multiple threads will corrupt heap (DO NOT USE)
ExecutorService executor = Executors.newFixedThreadPool(2);
executor.submit(() -> {
    for (int i = 0; i < 10_000; i++) pq.add(i);
});
executor.submit(() -> {
    for (int i = 0; i < 10_000; i++) pq.poll();
});
executor.shutdown();
executor.awaitTermination(1, TimeUnit.MINUTES);
// Result: corrupted heap, missing elements

// Performance: heap operations
ArrayList<Integer> data = new ArrayList<>();
for (int i = 0; i < 100_000; i++) {
    data.add((int)(Math.random() * Integer.MAX_VALUE));
}

long start = System.nanoTime();
PriorityQueue<Integer> heap = new PriorityQueue<>(data);
for (int i = 0; i < 10_000; i++) {
    heap.add((int)(Math.random() * Integer.MAX_VALUE));
    heap.poll();
}
long heapTime = System.nanoTime() - start;

start = System.nanoTime();
Collections.sort(data);
long sortTime = System.nanoTime() - start;

System.out.println("Heap insert/remove 10k ops: " + heapTime + "ns");
System.out.println("Sort for single pass: " + sortTime + "ns");
```

**Complexity:**
- add: O(log n)
- poll: O(log n)
- peek: O(1)
- Construction: O(n)

**Caution:** Not thread-safe. Use PriorityBlockingQueue for concurrent access.

---

### 3.2 Deque (ArrayDeque)

**Purpose:** Double-ended queue. O(1) operations at both ends. Better Stack/Queue than LinkedList.

```java
// Better than Stack
Deque<Integer> deque = new ArrayDeque<>();
deque.push(1);  // Add to head
deque.push(2);
deque.push(3);
System.out.println(deque.pop());  // 3 (LIFO)

// Better than Queue
deque = new ArrayDeque<>();
deque.offer(1);  // Add to tail
deque.offer(2);
deque.offer(3);
System.out.println(deque.poll());  // 1 (FIFO)

// Double-ended operations
deque = new ArrayDeque<>();
deque.addFirst(1);
deque.addLast(2);
deque.addFirst(0);
System.out.println(deque);  // [0, 1, 2]

// Sliding window (common pattern)
int[] arr = {1, 2, 3, 4, 5};
int windowSize = 3;
Deque<Integer> window = new ArrayDeque<>();

for (int i = 0; i < arr.length; i++) {
    // Remove elements outside window
    while (!window.isEmpty() && window.peekFirst() < i - windowSize + 1) {
        window.pollFirst();
    }
    window.addLast(i);
}
System.out.println("Window indices: " + window);  // [2, 3, 4]

// LRU Cache implementation
class LRUCache<K, V> {
    private int capacity;
    private LinkedHashMap<K, V> cache;
    
    LRUCache(int capacity) {
        this.capacity = capacity;
        this.cache = new LinkedHashMap<K, V>(capacity, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry eldest) {
                return size() > capacity;
            }
        };
    }
    
    V get(K key) {
        return cache.getOrDefault(key, null);
    }
    
    void put(K key, V value) {
        cache.put(key, value);
    }
}

LRUCache<Integer, String> lru = new LRUCache<>(3);
lru.put(1, "A");
lru.put(2, "B");
lru.put(3, "C");
System.out.println(lru.get(1));  // Access 1, move to end
lru.put(4, "D");  // Evicts 2

// Performance: ArrayDeque vs LinkedList
ArrayList<Integer> data = new ArrayList<>();
for (int i = 0; i < 1_000_000; i++) {
    data.add(i);
}

long start = System.nanoTime();
Deque<Integer> arrayDeque = new ArrayDeque<>(data);
for (int i = 0; i < 10_000; i++) {
    arrayDeque.pollFirst();
    arrayDeque.addLast(i);
}
long arrayTime = System.nanoTime() - start;

LinkedList<Integer> linkedDeque = new LinkedList<>(data);
start = System.nanoTime();
for (int i = 0; i < 10_000; i++) {
    linkedDeque.pollFirst();
    linkedDeque.addLast(i);
}
long linkedTime = System.nanoTime() - start;

System.out.println("ArrayDeque: " + arrayTime + "ns");
System.out.println("LinkedList: " + linkedTime + "ns");
System.out.println("ArrayDeque is " + ((double)linkedTime / arrayTime) + "x faster");
```

**Complexity:** O(1) for all operations at ends.

---

### 3.3 PriorityBlockingQueue

**Purpose:** Thread-safe priority queue. Unbounded, blocking operations.

```java
PriorityBlockingQueue<Integer> pq = new PriorityBlockingQueue<>();

// Producer thread
ExecutorService executor = Executors.newFixedThreadPool(2);
executor.submit(() -> {
    for (int i = 0; i < 100; i++) {
        try {
            pq.put(i);  // Never blocks (unbounded)
            Thread.sleep(10);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
    pq.put(-1);  // Sentinel for end
    System.out.println("Producer done");
});

// Consumer thread
executor.submit(() -> {
    try {
        while (true) {
            Integer item = pq.take();  // Blocks until available
            if (item == -1) break;
            System.out.println("Consumed: " + item);
        }
        System.out.println("Consumer done");
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
    }
});

executor.shutdown();
executor.awaitTermination(1, TimeUnit.MINUTES);

// Work stealing with multiple consumers
pq = new PriorityBlockingQueue<>();
int[] completed = {0};

Runnable producer = () -> {
    try {
        for (int i = 1; i <= 50; i++) {
            pq.put(i);
            Thread.sleep(5);
        }
    } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
};

Runnable consumer = () -> {
    try {
        while (true) {
            Integer item = pq.poll(100, TimeUnit.MILLISECONDS);
            if (item == null) break;  // Timeout
            completed[0]++;
            Thread.sleep(10);  // Process item
        }
    } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
};

executor = Executors.newFixedThreadPool(4);
executor.submit(producer);
for (int i = 0; i < 3; i++) executor.submit(consumer);
executor.shutdown();
executor.awaitTermination(1, TimeUnit.MINUTES);
System.out.println("Items processed: " + completed[0]);
```

**Use when:** Thread-safe priority queue needed for producer-consumer.

---

### 3.4 ConcurrentLinkedQueue

**Purpose:** Lock-free unbounded concurrent queue. Non-blocking.

```java
ConcurrentLinkedQueue<String> queue = new ConcurrentLinkedQueue<>();

// Multiple producers
ExecutorService executor = Executors.newFixedThreadPool(4);
for (int p = 0; p < 4; p++) {
    final int producerId = p;
    executor.submit(() -> {
        for (int i = 0; i < 25; i++) {
            queue.offer("Producer-" + producerId + "-Item-" + i);
        }
    });
}

// Multiple consumers
for (int c = 0; c < 2; c++) {
    final int consumerId = c;
    executor.submit(() -> {
        int count = 0;
        String item;
        while ((item = queue.poll()) != null) {
            count++;
        }
        System.out.println("Consumer-" + consumerId + " processed: " + count);
    });
}

executor.shutdown();
executor.awaitTermination(1, TimeUnit.MINUTES);

// Non-blocking: poll() returns null instead of blocking
queue = new ConcurrentLinkedQueue<>(Arrays.asList("A", "B", "C"));
String item = queue.poll();  // "A" - doesn't block
item = queue.poll();  // "B"
item = queue.poll();  // "C"
item = queue.poll();  // null - no blocking, no exception

// Compare with BlockingQueue semantics
BlockingQueue<String> bq = new LinkedBlockingQueue<>();
executor = Executors.newFixedThreadPool(2);

executor.submit(() -> {
    try {
        bq.put("Item");
        System.out.println("Put done");
    } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
});

executor.submit(() -> {
    try {
        String item2 = bq.take();  // Blocks until available
        System.out.println("Got: " + item2);
    } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
});

executor.shutdown();
executor.awaitTermination(10, TimeUnit.SECONDS);

// Performance: lock-free vs BlockingQueue
long start = System.nanoTime();
executor = Executors.newFixedThreadPool(2);

ConcurrentLinkedQueue<Integer> clq = new ConcurrentLinkedQueue<>();
executor.submit(() -> {
    for (int i = 0; i < 500_000; i++) clq.offer(i);
});
executor.submit(() -> {
    int count = 0;
    while (true) {
        if (clq.poll() != null) count++;
        if (count == 500_000) break;
    }
});
executor.shutdown();
executor.awaitTermination(10, TimeUnit.SECONDS);
long lockFreeTime = System.nanoTime() - start;

start = System.nanoTime();
executor = Executors.newFixedThreadPool(2);
BlockingQueue<Integer> bq2 = new LinkedBlockingQueue<>();
executor.submit(() -> {
    try {
        for (int i = 0; i < 500_000; i++) bq2.put(i);
    } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
});
executor.submit(() -> {
    try {
        for (int i = 0; i < 500_000; i++) bq2.take();
    } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
});
executor.shutdown();
executor.awaitTermination(10, TimeUnit.SECONDS);
long blockingTime = System.nanoTime() - start;

System.out.println("ConcurrentLinkedQueue: " + lockFreeTime + "ns");
System.out.println("LinkedBlockingQueue: " + blockingTime + "ns");
```

**Use when:** High-throughput producer-consumer, don't need blocking semantics.

---

## 4. MAP COLLECTIONS

### 4.1 HashMap

**Purpose:** Hash table map. O(1) average operations. Unordered.

```java
// Basic operations
HashMap<String, Integer> map = new HashMap<>();
map.put("Alice", 95);
map.put("Bob", 87);
map.put("Charlie", 92);

int aliceScore = map.get("Alice");  // 95
boolean hasAlice = map.containsKey("Alice");  // true
boolean has100 = map.containsValue(100);  // false

// Null handling
map.put(null, 0);  // One null key allowed
map.put("David", null);  // Multiple null values allowed
System.out.println(map.get(null));  // 0

// Default value pattern
int charlieSafe = map.getOrDefault("Eve", 0);  // 0

// Iteration
for (String name : map.keySet()) System.out.println(name);
for (Integer score : map.values()) System.out.println(score);
for (Map.Entry<String, Integer> entry : map.entrySet()) {
    System.out.println(entry.getKey() + " -> " + entry.getValue());
}

// Compute patterns
map.compute("Frank", (k, v) -> v == null ? 50 : v + 5);  // Insert or update
map.computeIfAbsent("Grace", k -> 85);  // Insert if absent
map.computeIfPresent("Alice", (k, v) -> v + 2);  // Update if present
map.putIfAbsent("Helen", 88);  // Upsert

// Merge
map.merge("Alice", 10, (oldScore, newScore) -> oldScore + newScore);  // Alice: 95+10=105

// Performance with hash collisions
HashMap<Integer, String> perf = new HashMap<>();
class BadHashCode {
    int value;
    BadHashCode(int v) { value = v; }
    @Override
    public int hashCode() { return value % 100;  }  // Collisions!
    @Override
    public boolean equals(Object o) { return value == ((BadHashCode)o).value; }
}

for (int i = 0; i < 10_000; i++) {
    perf.put(i, "val-" + i);
}

long start = System.nanoTime();
for (int i = 0; i < 100_000; i++) {
    perf.get(5000);
}
long normalTime = System.nanoTime() - start;
System.out.println("Normal hashCode: " + normalTime + "ns");

// Removal during iteration (fail-fast)
HashMap<String, Integer> mutable = new HashMap<>(map);
Iterator<String> iter = mutable.keySet().iterator();
while (iter.hasNext()) {
    String key = iter.next();
    if (key.length() > 3) {
        iter.remove();  // Safe removal
    }
}
System.out.println(mutable);  // "Bob" gone

// Unsafe removal (external modification)
mutable = new HashMap<>(map);
iter = mutable.keySet().iterator();
mutable.put("Eve", 80);  // External modification
try {
    while (iter.hasNext()) {
        System.out.println(iter.next());  // ConcurrentModificationException
    }
} catch (ConcurrentModificationException e) {
    System.out.println("Iterator invalidated");
}

// ConcurrentHashMap for multi-threaded access
ConcurrentHashMap<String, Integer> concurrent = new ConcurrentHashMap<>();
ExecutorService executor = Executors.newFixedThreadPool(4);
for (int t = 0; t < 4; t++) {
    final int threadId = t;
    executor.submit(() -> {
        for (int i = threadId; i < 1000; i += 4) {
            concurrent.put("key-" + i, i);
        }
    });
}
executor.shutdown();
executor.awaitTermination(10, TimeUnit.SECONDS);
System.out.println("Concurrent size: " + concurrent.size());  // 1000

// Frequency counting
String text = "the quick brown fox jumps over the lazy dog";
HashMap<String, Integer> freq = new HashMap<>();
for (String word : text.split(" ")) {
    freq.merge(word, 1, Integer::sum);
}
freq.forEach((word, count) -> System.out.println(word + ":" + count));
```

**Complexity:**
- Get/Put/Remove: O(1) average
- Iteration: O(n + capacity)
- Space: O(n)

---

### 4.2 LinkedHashMap

**Purpose:** Like HashMap but maintains insertion order (or access order for LRU).

```java
// Insertion order
LinkedHashMap<String, Integer> insertion = new LinkedHashMap<>();
insertion.put("C", 3);
insertion.put("A", 1);
insertion.put("B", 2);
for (String key : insertion.keySet()) System.out.println(key);  // C, A, B

// Access order (for LRU implementation)
LinkedHashMap<String, Integer> lru = new LinkedHashMap<String, Integer>(16, 0.75f, true) {
    @Override
    protected boolean removeEldestEntry(Map.Entry eldest) {
        return size() > 3;  // Keep only 3 items
    }
};

lru.put("A", 1);
lru.put("B", 2);
lru.put("C", 3);
System.out.println(lru.keySet());  // [A, B, C]

lru.get("A");  // Access A, move to end
System.out.println(lru.keySet());  // [B, C, A]

lru.put("D", 4);  // Evicts B (oldest)
System.out.println(lru.keySet());  // [C, A, D]

// LRU Cache for HTTP responses
class ResponseCache {
    private LinkedHashMap<String, String> cache;
    
    ResponseCache(int capacity) {
        cache = new LinkedHashMap<String, String>(capacity, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry eldest) {
                return size() > capacity;
            }
        };
    }
    
    synchronized String getOrFetch(String url) throws Exception {
        return cache.computeIfAbsent(url, k -> {
            try {
                return "Response from " + k;  // Simulated fetch
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });
    }
}

ResponseCache cache = new ResponseCache(2);
System.out.println(cache.getOrFetch("http://api/users"));
System.out.println(cache.getOrFetch("http://api/posts"));
System.out.println(cache.getOrFetch("http://api/comments"));  // Evicts /users

// Performance vs HashMap (small difference)
ArrayList<String> keys = new ArrayList<>();
for (int i = 0; i < 100_000; i++) keys.add("key-" + i);

long start = System.nanoTime();
HashMap<String, Integer> hm = new HashMap<>();
for (int i = 0; i < keys.size(); i++) hm.put(keys.get(i), i);
for (String key : keys) hm.get(key);
long hmTime = System.nanoTime() - start;

start = System.nanoTime();
LinkedHashMap<String, Integer> lhm = new LinkedHashMap<>();
for (int i = 0; i < keys.size(); i++) lhm.put(keys.get(i), i);
for (String key : keys) lhm.get(key);
long lhmTime = System.nanoTime() - start;

System.out.println("HashMap: " + hmTime + "ns");
System.out.println("LinkedHashMap: " + lhmTime + "ns");
System.out.println("Overhead: " + ((double)lhmTime / hmTime) + "x");
```

**Use when:** Need insertion order + O(1) operations, or implement LRU cache.

---

### 4.3 TreeMap

**Purpose:** Sorted map. O(log n) operations. Backed by Red-Black Tree.

```java
// Sorted keys
TreeMap<Integer, String> sorted = new TreeMap<>();
sorted.put(5, "Five");
sorted.put(1, "One");
sorted.put(3, "Three");
sorted.put(2, "Two");
for (Integer key : sorted.keySet()) System.out.println(key);  // 1, 2, 3, 5

// Custom comparator
TreeMap<String, Integer> byLength = new TreeMap<>(
    (a, b) -> {
        if (a.length() != b.length()) return a.length() - b.length();
        return a.compareTo(b);
    }
);
byLength.put("apple", 5);
byLength.put("a", 1);
byLength.put("banana", 6);
byLength.put("be", 2);
for (String key : byLength.keySet()) System.out.println(key);  // a, be, apple, banana

// Range queries
TreeMap<Integer> range = new TreeMap<>(
    Arrays.asList(1,2,3,4,5,6,7,8,9,10).stream()
    .collect(Collectors.toMap(k -> k, k -> "val-" + k))
);

System.out.println(range.headMap(5));  // Keys < 5
System.out.println(range.tailMap(5));  // Keys >= 5
System.out.println(range.subMap(3, 7));  // Keys in [3, 7)

// Navigation
Integer lower = range.lowerKey(5);  // Largest < 5 → 4
Integer floor = range.floorKey(5);  // Largest <= 5 → 5
Integer ceiling = range.ceilingKey(5);  // Smallest >= 5 → 5
Integer higher = range.higherKey(5);  // Smallest > 5 → 6
System.out.println("lower: " + lower + ", floor: " + floor);

// Views over subranges
NavigableMap<Integer, String> subrange = range.subMap(3, 7);
subrange.put(6, "new-6");  // Modifies original map
System.out.println(range.get(6));  // "new-6"

// Interval scheduling problem
class Interval implements Comparable<Interval> {
    int start, end;
    Interval(int start, int end) { this.start = start; this.end = end; }
    @Override
    public int compareTo(Interval o) { return this.start - o.start; }
}

TreeMap<Interval, String> schedule = new TreeMap<>();
schedule.put(new Interval(1, 3), "Meeting1");
schedule.put(new Interval(5, 7), "Meeting2");
schedule.put(new Interval(6, 8), "Meeting3");  // Overlap!

for (Map.Entry<Interval, String> entry : schedule.entrySet()) {
    System.out.println(entry.getKey().start + "-" + entry.getKey().end + ": " + entry.getValue());
}

// Performance vs HashMap (for range queries)
TreeMap<Integer, String> tm = new TreeMap<>();
HashMap<Integer, String> hm = new HashMap<>();
for (int i = 0; i < 100_000; i++) {
    tm.put(i, "val-" + i);
    hm.put(i, "val-" + i);
}

long start = System.nanoTime();
Map<Integer, String> range1 = tm.subMap(40_000, 60_000);  // O(log n)
long tmTime = System.nanoTime() - start;

start = System.nanoTime();
Map<Integer, String> range2 = hm.entrySet().stream()
    .filter(e -> e.getKey() >= 40_000 && e.getKey() < 60_000)
    .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));  // O(n)
long hmTime = System.nanoTime() - start;

System.out.println("TreeMap range query: " + tmTime + "ns");
System.out.println("HashMap range query: " + hmTime + "ns");
```

**Complexity:**
- Get/Put/Remove: O(log n)
- First/Last key: O(1)
- Range queries: O(log n)

---

### 4.4 ConcurrentHashMap

**Purpose:** High-performance concurrent map. Segment-based locking (Java 7) or bucket-level (Java 8+).

```java
// Multi-threaded updates
ConcurrentHashMap<String, Integer> concurrent = new ConcurrentHashMap<>();

ExecutorService executor = Executors.newFixedThreadPool(4);
for (int t = 0; t < 4; t++) {
    final int threadId = t;
    executor.submit(() -> {
        for (int i = threadId; i < 10_000; i += 4) {
            concurrent.put("key-" + i, i);
        }
    });
}
executor.shutdown();
executor.awaitTermination(10, TimeUnit.SECONDS);
System.out.println("Size: " + concurrent.size());  // 10_000

// Atomic compound operations
ConcurrentHashMap<String, Integer> counters = new ConcurrentHashMap<>();

// Multiple threads incrementing concurrently
executor = Executors.newFixedThreadPool(4);
for (int t = 0; t < 4; t++) {
    executor.submit(() -> {
        for (int i = 0; i < 250_000; i++) {
            counters.merge("count", 1, Integer::sum);
        }
    });
}
executor.shutdown();
executor.awaitTermination(10, TimeUnit.SECONDS);
System.out.println("Total count: " + counters.get("count"));  // 1_000_000

// Compare with regular HashMap (unsafe)
HashMap<String, Integer> unsafe = new HashMap<>();
executor = Executors.newFixedThreadPool(4);
for (int t = 0; t < 4; t++) {
    executor.submit(() -> {
        for (int i = 0; i < 250_000; i++) {
            Integer current = unsafe.getOrDefault("count", 0);
            unsafe.put("count", current + 1);  // Race condition
        }
    });
}
executor.shutdown();
executor.awaitTermination(10, TimeUnit.SECONDS);
System.out.println("Unsafe count: " + unsafe.get("count"));  // Less than 1_000_000

// Iteration safety
ConcurrentHashMap<Integer, String> iter = new ConcurrentHashMap<>();
for (int i = 0; i < 1000; i++) iter.put(i, "val-" + i);

// Iterator is weakly consistent (doesn't throw CME)
Iterator<Integer> it = iter.keySet().iterator();
new Thread(() -> {
    try {
        for (int i = 1000; i < 2000; i++) {
            iter.put(i, "val-" + i);
            Thread.sleep(1);
        }
    } catch (InterruptedException e) {}
}).start();

// Iterator continues despite concurrent modifications
int count = 0;
while (it.hasNext()) {
    it.next();
    count++;
}
System.out.println("Iterated: " + count);  // Between 1000 and 2000

// Performance comparison under contention
long start = System.nanoTime();
executor = Executors.newFixedThreadPool(8);
ConcurrentHashMap<String, Integer> chm = new ConcurrentHashMap<>();
for (int t = 0; t < 8; t++) {
    executor.submit(() -> {
        for (int i = 0; i < 100_000; i++) {
            chm.put("key-" + (i % 1000), i);
        }
    });
}
executor.shutdown();
executor.awaitTermination(1, TimeUnit.MINUTES);
long chmTime = System.nanoTime() - start;

start = System.nanoTime();
executor = Executors.newFixedThreadPool(8);
Map<String, Integer> syncMap = Collections.synchronizedMap(new HashMap<>());
for (int t = 0; t < 8; t++) {
    executor.submit(() -> {
        for (int i = 0; i < 100_000; i++) {
            syncMap.put("key-" + (i % 1000), i);
        }
    });
}
executor.shutdown();
executor.awaitTermination(1, TimeUnit.MINUTES);
long syncTime = System.nanoTime() - start;

System.out.println("ConcurrentHashMap: " + chmTime + "ns");
System.out.println("Synchronized Map: " + syncTime + "ns");
System.out.println("ConcurrentHashMap is " + ((double)syncTime / chmTime) + "x faster");

// Segment isolation (visible in old code)
ConcurrentHashMap<Integer, String> segments = new ConcurrentHashMap<>(16);  // 16 segments
ExecutorService ex = Executors.newFixedThreadPool(16);
long startPerf = System.nanoTime();
for (int t = 0; t < 16; t++) {
    final int threadId = t;
    ex.submit(() -> {
        for (int i = 0; i < 100_000; i++) {
            segments.put(threadId * 100_000 + i, "val");
        }
    });
}
ex.shutdown();
ex.awaitTermination(1, TimeUnit.MINUTES);
System.out.println("16 threads in isolation: " + (System.nanoTime() - startPerf) + "ns");

// Now contending on same keys
startPerf = System.nanoTime();
ex = Executors.newFixedThreadPool(16);
for (int t = 0; t < 16; t++) {
    ex.submit(() -> {
        for (int i = 0; i < 100_000; i++) {
            segments.put(i % 100, "val");  // All contend on same 100 keys
        }
    });
}
ex.shutdown();
ex.awaitTermination(1, TimeUnit.MINUTES);
System.out.println("16 threads on 100 keys: " + (System.nanoTime() - startPerf) + "ns");
```

**Use when:** Multi-threaded access to shared map (much faster than synchronized).

---

### 4.5 Hashtable (Legacy)

**Purpose:** Synchronized HashMap (pre-Java 5). Avoid in new code.

```java
// Every method synchronized
Hashtable<String, Integer> ht = new Hashtable<>();
ht.put("A", 1);
ht.put("B", 2);

// Even iteration needs explicit sync
synchronized (ht) {
    for (String key : ht.keySet()) {
        System.out.println(key);
    }
}

// Performance worse than alternatives
Hashtable<String, Integer> table = new Hashtable<>();
for (int i = 0; i < 100_000; i++) table.put("key-" + i, i);

long start = System.nanoTime();
for (int i = 0; i < 1_000_000; i++) {
    table.get("key-50000");  // Synchronized, slower
}
long tableTime = System.nanoTime() - start;

ConcurrentHashMap<String, Integer> chm = new ConcurrentHashMap<>(table);
start = System.nanoTime();
for (int i = 0; i < 1_000_000; i++) {
    chm.get("key-50000");  // Lock-free/fine-grained
}
long chmTime = System.nanoTime() - start;

System.out.println("Hashtable: " + tableTime + "ns");
System.out.println("ConcurrentHashMap: " + chmTime + "ns");
System.out.println("ConcurrentHashMap is " + ((double)tableTime / chmTime) + "x faster");
```

**Status:** Deprecated. Use ConcurrentHashMap or synchronizedMap.

---

## 5. COMPREHENSIVE COMPARISON TABLE

```java
// Comparison by use case
class ComparisonDemo {
    public static void main(String[] args) throws Exception {
        System.out.println("=== Collection Selection Guide ===\n");
        
        // 1. Simple list with random access
        System.out.println("1. List with random access:");
        ArrayList<Integer> list = new ArrayList<>(Arrays.asList(1,2,3,4,5));
        System.out.println("   ✓ ArrayList: " + list.get(2));  // O(1)
        System.out.println("   ✗ LinkedList: O(n) random access\n");
        
        // 2. Frequent insertions/deletions at ends
        System.out.println("2. Deque operations:");
        Deque<String> deque = new ArrayDeque<>();
        deque.addFirst("head");
        deque.addLast("tail");
        System.out.println("   ✓ ArrayDeque: " + deque);
        System.out.println("   ✗ ArrayList: O(n) for insertions at head\n");
        
        // 3. Multi-threaded read-heavy
        System.out.println("3. Read-heavy concurrent:");
        CopyOnWriteArrayList<String> cow = new CopyOnWriteArrayList<>(
            Arrays.asList("a", "b", "c")
        );
        System.out.println("   ✓ CopyOnWriteArrayList: safe, fast reads");
        System.out.println("   ✗ Slow writes (full copy)\n");
        
        // 4. Unique elements, O(1) operations
        System.out.println("4. Unique elements (unordered):");
        HashSet<Integer> set = new HashSet<>(Arrays.asList(1,2,3,2,1));
        System.out.println("   ✓ HashSet: " + set);
        System.out.println("   ✗ TreeSet: O(log n) for sorted\n");
        
        // 5. Sorted unique elements
        System.out.println("5. Sorted unique elements:");
        TreeSet<Integer> ts = new TreeSet<>(Arrays.asList(5,1,3));
        System.out.println("   ✓ TreeSet: " + ts);
        System.out.println("   ✗ HashSet: no order\n");
        
        // 6. Multi-threaded concurrent access
        System.out.println("6. Concurrent sorted set:");
        ConcurrentSkipListSet<Integer> skip = new ConcurrentSkipListSet<>(
            Arrays.asList(5,1,3)
        );
        System.out.println("   ✓ ConcurrentSkipListSet: lock-free");
        System.out.println("   ✗ Collections.synchronizedSortedSet: needs sync for iteration\n");
        
        // 7. Priority queue (min-heap)
        System.out.println("7. Priority queue:");
        PriorityQueue<Integer> pq = new PriorityQueue<>();
        pq.addAll(Arrays.asList(5,1,3));
        System.out.println("   ✓ PriorityQueue: " + pq.peek());  // 1
        System.out.println("   ✗ Not thread-safe, use PriorityBlockingQueue\n");
        
        // 8. Multi-threaded priority queue
        System.out.println("8. Concurrent priority queue:");
        System.out.println("   ✓ PriorityBlockingQueue: blocking, thread-safe");
        System.out.println("   ✗ Non-blocking: use ConcurrentLinkedQueue\n");
        
        // 9. Key-value lookup
        System.out.println("9. Key-value pairs (unordered):");
        HashMap<String, Integer> map = new HashMap<>();
        map.put("Alice", 95);
        System.out.println("   ✓ HashMap: " + map.get("Alice"));
        System.out.println("   ✗ TreeMap: O(log n), overhead\n");
        
        // 10. Sorted key-value pairs
        System.out.println("10. Sorted key-value pairs:");
        TreeMap<String, Integer> tm = new TreeMap<>();
        tm.put("Charlie", 92);
        tm.put("Alice", 95);
        tm.put("Bob", 87);
        System.out.println("   ✓ TreeMap: " + tm.keySet());
        System.out.println("   ✗ HashMap: no order\n");
        
        // 11. LRU Cache
        System.out.println("11. LRU Cache:");
        LinkedHashMap<String, String> lru = new LinkedHashMap<String, String>(2, 0.75f, true) {
            protected boolean removeEldestEntry(Map.Entry e) { return size() > 2; }
        };
        lru.put("A", "1");
        lru.put("B", "2");
        lru.put("C", "3");  // Evicts A
        System.out.println("   ✓ LinkedHashMap: " + lru.keySet());
        System.out.println("   ✗ HashMap: no order\n");
        
        // 12. Concurrent map
        System.out.println("12. Multi-threaded map:");
        ConcurrentHashMap<String, Integer> chm = new ConcurrentHashMap<>();
        System.out.println("   ✓ ConcurrentHashMap: lock-free");
        System.out.println("   ✗ synchronized Map: full lock overhead\n");
        
        // Summary table
        System.out.println("\n=== Quick Reference ===");
        System.out.println("Use ArrayList:          Random access lists");
        System.out.println("Use LinkedList:         Deque via iterator");
        System.out.println("Use ArrayDeque:         Stack/Queue (faster than LinkedList)");
        System.out.println("Use CopyOnWriteList:    Read-heavy concurrent, listener lists");
        System.out.println("Use HashSet:            Unique elements, O(1) operations");
        System.out.println("Use TreeSet:            Sorted unique elements, range queries");
        System.out.println("Use ConcurrentSkipList: Concurrent sorted set");
        System.out.println("Use PriorityQueue:      Min-heap (single-threaded)");
        System.out.println("Use PriorityBlocking:   Min-heap (multi-threaded, blocking)");
        System.out.println("Use ConcurrentLinked:   Producer-consumer (non-blocking)");
        System.out.println("Use HashMap:            Key-value lookup, O(1)");
        System.out.println("Use TreeMap:            Sorted map, range queries");
        System.out.println("Use LinkedHashMap:      Insertion order, LRU cache");
        System.out.println("Use ConcurrentHashMap:  Multi-threaded map");
    }
}
```

---

## 6. THREAD-SAFETY MATRIX

```java
// Thread-safety summary
class ThreadSafetyMatrix {
    public static void main(String[] args) {
        System.out.println("=== THREAD-SAFETY MATRIX ===\n");
        
        System.out.println("NOT THREAD-SAFE:");
        System.out.println("  ArrayList, LinkedList, HashMap, TreeMap, HashSet, TreeSet");
        System.out.println("  PriorityQueue, ArrayDeque");
        System.out.println("  → Requires explicit synchronization or Collections.synchronized*\n");
        
        System.out.println("THREAD-SAFE (Concurrent):");
        System.out.println("  ConcurrentHashMap        - Lock-free map");
        System.out.println("  CopyOnWriteArrayList     - Snapshot iteration");
        System.out.println("  CopyOnWriteArraySet      - Snapshot iteration");
        System.out.println("  ConcurrentLinkedQueue    - Lock-free queue");
        System.out.println("  PriorityBlockingQueue    - Blocking priority queue");
        System.out.println("  ConcurrentSkipListSet    - Lock-free sorted set");
        System.out.println("  ConcurrentSkipListMap    - Lock-free sorted map\n");
        
        System.out.println("THREAD-SAFE (Synchronized - AVOID):");
        System.out.println("  Vector                   - Synchronized ArrayList");
        System.out.println("  Hashtable                - Synchronized HashMap");
        System.out.println("  Collections.synchronized* - Wrapped collections\n");
        
        System.out.println("BEST PRACTICES:");
        System.out.println("  ✓ Multi-read, rare write: CopyOnWriteArrayList");
        System.out.println("  ✓ High-contention map: ConcurrentHashMap");
        System.out.println("  ✓ Producer-consumer: PriorityBlockingQueue, ConcurrentLinkedQueue");
        System.out.println("  ✗ Never: Hashtable, Vector, Stack (use ArrayDeque)");
        System.out.println("  ✗ Avoid: Collections.synchronizedMap (full lock)");
    }
}
```

---

## 7. PERFORMANCE BENCHMARKS (Relative)

```
List Operations (100k elements):
  ArrayList.get(random):        1x          (O(1) baseline)
  LinkedList.get(random):       1000x       (O(n))
  ArrayList.add(0, item):       1500x       (O(n) shift)
  LinkedList.add(0, item):      2x          (O(1))
  CopyOnWriteArrayList.add():   5000x       (full copy)

Set Operations (100k elements):
  HashSet.contains():           1x          (O(1))
  TreeSet.contains():           15x         (O(log n))
  CopyOnWriteArraySet.add():    500x        (full copy)

Queue Operations:
  ArrayDeque.poll():            1x
  LinkedList.poll():            3x          (dereference cost)
  PriorityQueue.poll():         50x         (heap maintenance)

Map Operations (100k entries):
  HashMap.get():                1x          (O(1))
  TreeMap.get():                20x         (O(log n))
  ConcurrentHashMap.get():      1.5x        (thread-safe overhead)
  Hashtable.get():              3x          (full synchronization)
  LinkedHashMap.get():          1.2x        (linked list overhead)

Concurrent (8 threads, 1M ops):
  ConcurrentHashMap:            1x          (lock-free, scales)
  Collections.synchronizedMap:  40x         (bottleneck on lock)
  Hashtable:                    45x         (global lock)
```

---

## Summary

**Collections Quick Pick:**
- **List:** ArrayList (default), LinkedList (Deque), CopyOnWriteArrayList (concurrent read-heavy)
- **Set:** HashSet (default), TreeSet (sorted), ConcurrentSkipListSet (concurrent sorted)
- **Queue:** ArrayDeque (Stack/Queue), PriorityQueue (heap), PriorityBlockingQueue (concurrent)
- **Map:** HashMap (default), TreeMap (sorted), ConcurrentHashMap (concurrent), LinkedHashMap (LRU)

**Concurrency:** Prefer `java.util.concurrent.*` over `Collections.synchronized*`.

**Avoid:** Vector, Hashtable, Stack (pre-Java 5 legacy).
