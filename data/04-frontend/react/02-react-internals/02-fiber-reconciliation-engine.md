# React Fiber & Reconciliation: How React Actually Works

**Level:** Advanced | **Time:** 60 mins | **Interview:** 🔥🔥🔥 Critical

---

## Overview

React's Fiber architecture is what makes React... React. Fiber = React's internal data structure (tree of work units) that enables incremental rendering, priority scheduling, and error boundaries. Understanding Fiber teaches you why React components work the way they do, why `key` matters, and how to debug rendering issues.

**Why this matters:**
- Interview question (Senior+): "How does React's reconciliation algorithm work?"
- Performance: Understanding Fiber helps you write faster components
- Debugging: Knowing Fiber helps you understand why re-renders happen
- Job security: Most developers don't understand this; you'll be 10x more valuable

---

## 1. The Problem: Synchronous Rendering (Pre-Fiber)

### React Before Fiber (React 15 and Earlier)

React rendered the entire component tree synchronously, top to bottom.

```
Render phase:
1. Component A → render()
2. Component B → render()
3. Component C → render()
4. Component D → render()
5. ...
6. Component Z → render()
   ↓ (all done)
Commit phase: Update DOM

Total time: 50ms (blocks main thread for 50ms)

Problem:
- Browser can't handle user input, animations, or high-priority tasks
- Page feels laggy during rendering
- Large component trees freeze the entire page
```

**Real impact:**
```
Timeline:
0ms    : User clicks button
2ms    : React starts rendering (synchronous)
52ms   : React finishes rendering, commits DOM update
5ms-52ms: User input/animations blocked ❌
```

---

### The Solution: Fiber Architecture (React 16+)

React Fiber breaks rendering into small units of work that can be paused/resumed.

```
With Fiber (interruptible):
0ms   : User clicks button
2ms   : React starts rendering Fiber 1 (5ms of work)
7ms   : PAUSE rendering, let browser handle user input
12ms  : User input handled (5ms)
17ms  : Resume rendering Fiber 2 (5ms of work)
22ms  : PAUSE
27ms  : Resume Fiber 3 (5ms of work)
...
47ms  : All fibers done, commit phase

Result: UI stays responsive even during rendering
```

---

## 2. Fiber Data Structure

Each fiber represents a component/element and holds all the information React needs.

```javascript
// Simplified Fiber structure
type Fiber = {
  // Component info
  type: FunctionComponent | ClassComponent | HTMLTag,
  props: Props,
  key: string | number | null,

  // Tree structure
  parent: Fiber | null,         // Parent fiber
  child: Fiber | null,          // First child
  sibling: Fiber | null,        // Next sibling
  alternate: Fiber | null,      // Previous version (for diff)

  // State
  hooks: Hook[] | null,         // useState, useEffect, etc.
  state: any,                   // For class components

  // Rendering
  pendingProps: Props,          // New props
  memoizedProps: Props,         // Old props (for bailout)
  memoizedState: any,           // Last computed state

  // Work
  effectTag: 'Placement' | 'Update' | 'Deletion',
  effects: Effect[],            // useEffect, useLayoutEffect

  // Meta
  lanes: Lanes,                 // Priority of this work
  dependencies: Dependencies[],
};

// Example: <Parent><Child /></Parent>
// Creates fiber tree:
// Parent Fiber
//   ├─ child: Child Fiber
//   └─ sibling: null
// Child Fiber
//   ├─ parent: Parent Fiber
//   └─ sibling: null
```

---

## 3. Reconciliation Algorithm (The Diff)

React compares old fiber tree with new component tree → determines what changed.

### Rules:

1. **Same type, different props** → Update (no unmount)
2. **Different types** → Replace (unmount old, mount new)
3. **Same type, same key** → Reuse (even if moved)
4. **Different key** → Replace (treat as new element)

### Example 1: Props Changed (Simple Update)

```javascript
// Old render
<Button label="Click me" onClick={handleClick} />

// New render
<Button label="Click me now" onClick={handleClick} />

// Reconciliation:
// Same type: Button
// Diff props: label changed
// Result: Update existing fiber (don't remount)
// Effect: Update DOM attributes, no unmount/mount
```

### Example 2: Type Changed (Replace)

```javascript
// Old
{isError ? <ErrorComponent /> : <SuccessComponent />}

// New (toggled)
{isError ? <SuccessComponent /> : <ErrorComponent />}

// Reconciliation:
// Old: ErrorComponent fiber
// New: SuccessComponent fiber
// Different types → Replace
// Result: Unmount ErrorComponent, mount SuccessComponent
// All state lost (ErrorComponent's useState hooks destroyed)
```

### Example 3: Key Matters (Critical!)

```javascript
// ❌ WITHOUT key (Reconciliation fails)
items.map(item => <ListItem item={item} />)

Old:   [Item 1], [Item 2], [Item 3]
New:   [Item 3], [Item 1], [Item 2]

React compares by position:
  Position 0: Item 1 vs Item 3 (different data) → Update fiber 0's item
  Position 1: Item 2 vs Item 1 (different data) → Update fiber 1's item
  Position 2: Item 3 vs Item 2 (different data) → Update fiber 2's item

All 3 fibers updated (inefficient)
Worse: If ListItem has useState, state gets mixed up:
  Fiber 0 still has Item 1's state but now holds Item 3's data
  → State/data mismatch ❌

// ✅ WITH key (Reconciliation works)
items.map(item => <ListItem key={item.id} item={item} />)

Old:   [Item1{id:1}], [Item2{id:2}], [Item3{id:3}]
New:   [Item3{id:3}], [Item1{id:1}], [Item2{id:2}]

React matches by key:
  key=1 fiber: moved from position 0 → position 1
  key=2 fiber: moved from position 1 → position 2
  key=3 fiber: moved from position 2 → position 0

All fibers reused (efficient)
State preserved (useState hooks attached to correct fiber)
```

---

## 4. Phases: Render and Commit

Fiber renders in two phases:

### Phase 1: Render Phase (Can be Interrupted)

1. Reconciliation (diff) → determine changes
2. Create new fibers for changes
3. Build effect list (what to do in commit)

**Can pause here.** Work is safe to discard.

```javascript
// Simplified Render phase
function performUnitOfWork(fiber) {
  // 1. Reconcile
  reconcile(fiber);

  // 2. Process children
  if (fiber.child) {
    return fiber.child; // Return next fiber
  }

  // 3. No more children, go to sibling or parent
  return getNextFiber(fiber);
}

// Work loop (can pause/resume)
while (nextUnitOfWork) {
  nextUnitOfWork = performUnitOfWork(nextUnitOfWork);

  // If deadline reached (5ms), pause
  if (shouldYield()) {
    break;
  }
}
```

### Phase 2: Commit Phase (Synchronous, Cannot Interrupt)

1. Apply effects (DOM updates, side effects)
2. Call lifecycle methods (componentDidMount, etc.)
3. Cleanup (useEffect cleanup functions)

**Cannot pause.** Must be synchronous and complete.

```
Timeline:
Render (interruptible): 0ms → 47ms (paused 3x)
Commit (sync):         47ms → 50ms (cannot pause)
```

---

## 5. Batching & State Updates

React batches multiple state updates into a single render. This is especially important for state management libraries like Redux and Zustand (see [Redux/Zustand Patterns](../../05-state-management/02-redux-zustand-patterns.md) for how dispatch queues fiber work).

### Automatic Batching (React 18+)

```javascript
function handleClick() {
  setCount(c => c + 1);  // Enqueued
  setName('Alice');      // Enqueued
  setEmail('a@b.com');   // Enqueued
}
// Result: 1 render (not 3)

// Batching works for:
// - Event handlers (onClick, onChange, etc.)
// - Promise callbacks (after await)
// - setTimeout (since React 18)

// Pre-React 18, setTimeout did NOT batch:
setTimeout(() => {
  setCount(c => c + 1);  // Separate render
  setName('Alice');      // Separate render
}, 100);
// Result: 2 renders (batching not automatic)
```

### Why Batching Matters

```javascript
// ❌ WITHOUT batching (3 renders)
setCount(1);     // Render 1
setName('Bob');  // Render 2
setEmail('b@b'); // Render 3

// ✅ WITH batching (1 render)
setCount(1);
setName('Bob');
setEmail('b@b');
// React batches all 3 → 1 render (3x faster)
```

---

## 6. Hooks & Fiber Reconciliation

Hooks rely on fiber internals (hooks are stored on fiber).

```javascript
function Counter() {
  const [count, setCount] = useState(0);
  const [name, setName] = useState('Alice');

  return <div>{count} {name}</div>;
}

// Fiber structure (simplified):
Fiber {
  type: Counter,
  hooks: [
    { state: 0, queue: [updates] },          // count
    { state: 'Alice', queue: [updates] }     // name
  ]
}
```

### Critical: Hook Order Must Be Consistent

```javascript
// ❌ BAD: Hook order changes
function Component({ showEmail }) {
  const [name, setName] = useState('');

  if (showEmail) {
    const [email, setEmail] = useState(''); // Conditional hook ❌
  }

  const [age, setAge] = useState(0);
  return ...;
}

// First render (showEmail=true):
// hooks: [name, email, age] (3 hooks)
// Fiber remembers indices

// Second render (showEmail=false):
// hooks: [name, age] (2 hooks)
// Hook at index 1 changed from email → age
// age useState gets email's old state ❌

// ✅ GOOD: Hook order consistent
function Component({ showEmail }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [age, setAge] = useState(0);

  if (!showEmail) {
    // email state still exists but unused
  }

  return ...;
}
```

---

## 7. Fiber Debugging & DevTools

### Using React DevTools

```javascript
// React DevTools shows fiber tree:
<App>
  <Header>
    <Logo />
    <Nav>
      <Link />
      <Link />
    </Nav>
  </Header>
  <Main>
    <Article />
  </Main>
</App>

// Click component → See:
// - Props (current + old)
// - Hooks (useState values, useEffect dependencies)
// - Updates (what triggered re-render)
// - Rendered at (timestamp)
// - Source (file + line number)
```

### Why React Re-Rendered (DevTools)

```javascript
// Component re-renders, but parent didn't change?
// Check in DevTools:

1. Props changed? (parent might have re-rendered)
2. State changed? (useState)
3. Context changed? (useContext)
4. Parent re-rendered? (Parent always causes child re-render)
5. Force update? (forceUpdate, or setState in class)

// Example: Child re-renders even though parent props unchanged
// Reason: Parent rendered (for its own state change)
//         Child rendered automatically (even if props same)
// Solution: React.memo(Child) to skip render if props same
```

---

## 8. Optimization: Bailout Strategies

React can skip rendering if nothing changed.

### Strategy 1: Shallow Equality Check

```javascript
// React skips re-render if:
// 1. Props haven't changed (by reference)
// 2. State hasn't changed (by reference)

const Memo = React.memo(function Component({ count }) {
  return <div>{count}</div>;
});

// Render 1: count=5 (object ref: ABC123)
// Render 2: count=5 (object ref: ABC123) same object
// → Skip re-render (shallow equal)

// Render 3: count=5 (object ref: ABC456) different object
// → Re-render (reference changed, even if value same)
```

### Strategy 2: useMemo & useCallback

```javascript
// ❌ BAD: New object every render
function Parent() {
  const config = { theme: 'dark', size: 'lg' };
  return <Child config={config} />; // config ref changes every render
}

// ✅ GOOD: Memoize object
function Parent() {
  const config = useMemo(
    () => ({ theme: 'dark', size: 'lg' }),
    [] // Config same unless dependencies change
  );
  return <Child config={config} />; // config ref stable
}

// Combined with React.memo
const Child = React.memo(function Child({ config }) {
  return <div>{config.theme}</div>;
});
// Child only re-renders when config ref changes
```

---

## 9. Common Mistakes

### Mistake 1: Missing Keys in Lists

```javascript
// ❌ BAD: No key (list reorders breaks state)
{items.map(item => <Item data={item} />)}

// State can get mixed:
// [Item1{state:a}], [Item2{state:b}]
// After reorder:
// [Item2{state:a}], [Item1{state:b}] ← wrong!

// ✅ GOOD: Use key
{items.map(item => <Item key={item.id} data={item} />)}
```

### Mistake 2: Conditional Hooks

```javascript
// ❌ BAD: Hook in conditional
function Component({ show }) {
  if (show) {
    const [count, setCount] = useState(0); // Move out!
  }
  return ...;
}

// ✅ GOOD: Always call hook
function Component({ show }) {
  const [count, setCount] = useState(0);
  if (!show) return null;
  return ...;
}
```

### Mistake 3: Object as Dependency

```javascript
// ❌ BAD: New object every render
useEffect(() => {
  // Do something
}, [{ userId: 5 }]); // New object = effect runs every render

// ✅ GOOD: Primitive dependency
useEffect(() => {
  // Do something
}, [userId]); // Same reference = effect runs less often
```

---

## Interview Prep Questions

1. **"How does React's reconciliation algorithm work?"**
   - Answer: React compares old and new fiber trees. Same type+key → update. Different type → replace. Uses keys to track elements across renders. Can pause render phase but not commit phase.

2. **"Why does React need keys in lists?"**
   - Answer: Without keys, React matches by position (index). Reordering lists breaks state. Keys let React match fibers across renders (key=1 fiber stays with key=1 data).

3. **"What happens if you render in setState callback?"**
   - Answer: setState is batched. Rendering happens after all state updates batched. If you render inside setState callback, it's after batching but before commit.

4. **"Can you pause the commit phase?"**
   - Answer: No. Render phase is interruptible (Fiber breaks into units). Commit phase must be synchronous (DOM updates must be atomic). If commit phases overlap, DOM gets inconsistent.

5. **"Why can't you use hooks conditionally?"**
   - Answer: Hooks are stored in fiber.hooks array by index. Conditional hooks change the index mapping. Next render, hook at index N points to wrong state.

---

## See Also

### Phase 7.1 Related Topics

- [Redux/Zustand Patterns](../../05-state-management/02-redux-zustand-patterns.md) — State updates triggering fiber work
- [Compound Components](../../06-component-architecture/02-compound-components-pattern.md) — Context subscription behavior
- [Error Boundaries](../../35-error-handling/01-error-boundaries-and-patterns.md) — Error boundaries in fiber tree
- [Vitest + RTL](../../15-testing/03-unit-testing-vitest-rtl.md) — Testing fiber behavior

### Additional Resources

- React Fiber Documentation (react.dev)
- "A Deep Dive into React Fiber" by Lin Clark (animated video)
- React Source Code (github.com/facebook/react)
- React DevTools Profiler: Visualize Fiber tree
- Concurrent React (useTransition, useDeferredValue for priority)
