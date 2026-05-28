# 01: Components & JSX — Deep Reference

> **Scope**: JSX transpilation, component lifecycle (functional + class), props vs state, children patterns, composition vs inheritance, refs, portals, fragments, error boundaries, higher-order components, render props, controlled vs uncontrolled, keys reconciliation, synthetic events, dangerouslySetInnerHTML, server components, concurrent mode, suspense boundaries, streaming SSR, hydration failures, large component trees (perf), infinite re-render loops, prop drilling solutions, context vs props, default props patterns, component composition patterns (layout, container/presentational), compound components, slot patterns.

---


## Component Architecture Diagram

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```mermaid
graph TB
    A["React Component"] --> B["Class Component"]
    A --> C["Functional Component"]
    B --> B1["this.state"]
    B --> B2["this.props"]
    B --> B3["Lifecycle Methods"]
    C --> C1["useState Hook"]
    C --> C2["useEffect Hook"]
    C --> C3["Custom Hooks"]
    B1 --> D["Re-render on<br/>state change"]
    C1 --> D
    B2 --> E["Props passed<br/>from parent"]
    C2 --> E
    style A fill:#4a8bc2
    style B fill:#2d5a7b
    style C fill:#2d5a7b
    style D fill:#1a5d3a
    style E fill:#1a5d3a
```


## 1. JSX Transpilation: What Really Happens

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


JSX is syntactic sugar for `React.createElement` calls. Babel compiles it during build.

```jsx
// JSX
const el = <div className="container">Hello</div>;

// Compiled output
const el = React.createElement("div", { className: "container" }, "Hello");
```

```jsx
// JSX with component
<MyComponent prop={value}>Child</MyComponent>

// Compiled
React.createElement(MyComponent, { prop: value }, "Child");
```

**Java equivalent mental model**: JSX is like JSP custom tags or JSF components — declarative UI markup that compiles to imperative creation calls. React.createElement is analogous to `new UIComponent()` in JavaServer Faces, where a component tree is built before rendering.

**Key trivia**: `React.createElement` returns a plain object (`{ type, props, children }`), not a DOM node. This is the "virtual DOM element."

```javascript
// What createElement actually returns
{
  type: 'div',
  props: {
    className: 'container',
    children: 'Hello'
  },
  key: null,
  ref: null
}
```

### JSX Without React (React 17+ / 18)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


In React 17+, the new JSX transform (`react/jsx-runtime`) automatically imports `jsx()` so you don't need `import React from 'react'` in every file.

```javascript
// Modern compiled output (React 17+)
import { jsx as _jsx } from "react/jsx-runtime";
_jsx("div", { className: "container", children: "Hello" });
```

### Step-by-Step

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


1. **Babel parsing**: Babel's parser detects JSX syntax (`<tagName>`)
2. **Token conversion**: JSX elements are tokenized into open tag, content, close tag
3. **CreateElement transformation**: Tokens are converted to `React.createElement()` or `_jsx()` calls
4. **Argument mapping**: Attributes become `props` object, children become additional arguments
5. **Object creation**: Runtime wraps result in a fiber-compatible object with `type`, `props`, `key`, `ref`
6. **Virtual tree building**: Multiple calls build a tree of element objects (not DOM nodes yet)

### Code Example

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```javascript
// Input: JSX with nested elements
const header = (
  <header className="nav">
    <h1>{title}</h1>
    <nav>Links here</nav>
  </header>
);

// Step 1: Babel transpilation
const header = React.createElement(
  "header",
  { className: "nav" },
  React.createElement("h1", null, title),
  React.createElement("nav", null, "Links here")
);

// Step 2: Runtime evaluation creates object tree
// [
//   { type: "header", props: { className: "nav", children: [...] }, key: null, ref: null },
//   [
//     { type: "h1", props: { children: "My App" }, key: null, ref: null },
//     { type: "nav", props: { children: "Links here" }, key: null, ref: null }
//   ]
// ]
```

### Real-World Scenario

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


A team migrated from React 16 to React 17 and removed all `import React from 'react'` statements. Initially, the build failed on older Babel configs that didn't have the new JSX transform enabled. After updating `.babelrc` to use `@babel/preset-react` with `runtime: 'automatic'`, the code worked without changes and bundle size dropped by 8KB (one less React import per file).

### Diagram

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```mermaid
graph LR
    A["JSX Code<br/>&lt;div&gt;Hello&lt;/div&gt;"] -->|Babel| B["createElement Call<br/>React.createElement('div', ..., 'Hello')"]
    B -->|Runtime| C["Element Object<br/>{type: 'div', props: {...}}"]
    C -->|Reconciliation| D["Virtual Tree<br/>(no DOM yet)"]
    D -->|Commit| E["Actual DOM Node<br/>&lt;div&gt;Hello&lt;/div&gt;"]
```

---

## 2. Component Lifecycle — Functional (via Hooks)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


| Phase | Hook | Purpose |
|---|---|---|
| Mount | `useEffect(fn, [])` | Run once after first render |
| Update | `useEffect(fn, [deps])` | Run when deps change |
| Unmount | `useEffect(() => fn, [])` | Return cleanup function |
| Render | function body | Runs on every render |

```jsx
function LifecycleDemo({ id }) {
  // Render phase: runs every render
  console.log("Render", id);

  useEffect(() => {
    console.log("Mounted / deps changed", id);
    return () => console.log("Cleanup / unmount", id);
  }, [id]);

  return <div>{id}</div>;
}
```

### Class Component Lifecycle

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```jsx
class LifecycleDemo extends React.Component {
  constructor(props) {
    super(props);
    this.state = { count: 0 };
  }

  static getDerivedStateFromProps(props, state) {
    // Rarely needed. Returns new state or null.
    return null;
  }

  shouldComponentUpdate(nextProps, nextState) {
    // Performance optimization. Return false to skip render.
    return nextProps.id !== this.props.id;
  }

  render() {
    return <div>{this.props.id}</div>;
  }

  componentDidMount() { /* Side effects, subscriptions */ }
  componentDidUpdate(prevProps) { /* React to prop/state changes */ }
  componentWillUnmount() { /* Cleanup */ }
  componentDidCatch(error, info) { /* Error boundary */ }
  getSnapshotBeforeUpdate(prevProps, prevState) { /* Before DOM update */ }
}
```

### Lifecycle Mapping: Class → Hooks

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


| Class | Hooks Equivalent |
|---|---|
| `constructor` | `useState` initializer (lazy) |
| `componentDidMount` | `useEffect(fn, [])` |
| `componentDidUpdate` | `useEffect(fn, [deps])` |
| `componentWillUnmount` | `useEffect(() => fn, [])` cleanup |
| `shouldComponentUpdate` | `React.memo` or `useMemo` |
| `componentDidCatch` | `ErrorBoundary` class component |
| `getDerivedStateFromProps` | `useState` + conditional set |

### Step-by-Step

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


1. **Render phase**: Function body executes (component logic, JSX creation)
2. **Commit phase begins**: React updates DOM if tree changed
3. **Post-commit (useEffect)**: After browser paint, `useEffect` callbacks run
4. **Dependency check**: On next render, dependencies array is compared to previous
5. **Cleanup phase**: If deps changed or component unmounts, cleanup function runs first
6. **Effect re-run**: New effect runs with new dependencies

### Code Example

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```javascript
// Complete lifecycle example with hooks
import { useState, useEffect, useRef } from 'react';

function DataFetcher({ userId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);

  // 1. Mount + Update on userId change
  useEffect(() => {
    setLoading(true);
    abortRef.current = new AbortController();

    // Async data fetch
    fetch(`/api/users/${userId}`, { signal: abortRef.current.signal })
      .then(res => res.json())
      .then(data => {
        setData(data);
        setLoading(false);
      })
      .catch(err => {
        if (err.name !== 'AbortError') setError(err);
      });

    // 2. Cleanup: abort request if userId changes or unmount
    return () => {
      abortRef.current?.abort();
    };
  }, [userId]); // Dependency: re-run if userId changes

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;
  return <div>{JSON.stringify(data)}</div>;
}
```

#### Real-World Scenario

A chat application had memory leaks when users switched conversations. Each DataFetcher started a WebSocket connection in `useEffect` but didn't clean up. After 100 conversation switches, 100 sockets remained open. Adding the cleanup function (`return () => socket.close()`) fixed the leak. Monitoring showed heap usage dropping from 500MB to 50MB.

#### Diagram

```mermaid
sequenceDiagram
    participant R as React
    participant C as Component
    participant B as Browser
    participant A as API
    
    R->>C: 1. Render function body
    C->>C: Create JSX
    R->>B: 2. Update DOM (commit)
    B->>B: Paint to screen
    R->>C: 3. useEffect callback runs
    C->>A: Fetch data
    Note over C: Dependency array [userId]
    A-->>C: Data returned
    C->>R: setState
    R->>C: 4. New render (data changed)
    C->>C: Render with new data
    R->>B: Update DOM
```

---

## 3. Props vs State

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


| Aspect | Props | State |
|---|---|---|
| Source | Parent component | Component itself |
| Mutability | Immutable (read-only) | Mutable via setter |
| Triggers re-render | Yes (parent re-render) | Yes (setState call) |
| Default | Default props pattern | Initial state value |
| Ownership | Parent "owns" them | Component "owns" it |

```jsx
function Card({ title, children }) {
  // props.title — read-only
  const [expanded, setExpanded] = useState(false); // local state
  return (
    <div>
      <h2 onClick={() => setExpanded(!expanded)}>{title}</h2>
      {expanded && children}
    </div>
  );
}
```

**Java analogy**: Props are like constructor arguments (immutable, injected at creation). State is like private mutable fields with explicit setters that trigger re-render.

---

## 4. Children Patterns

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```jsx
// Direct children
<Card><p>Content</p></Card>

// Render function children (render prop variant)
<DataProvider>
  {data => <List items={data} />}
</DataProvider>

// Fragment children
<Table>
  <React.Fragment>
    <tr><td>A</td></tr>
    <tr><td>B</td></tr>
  </React.Fragment>
</Table>

// Multiple children with names (slots pattern)
<Layout
  header={<Header />}
  sidebar={<Sidebar />}
  footer={<Footer />}
/>
```

**Children reconciliation**: React iterates children array and matches by position + key. See §25 (Keys Reconciliation).

---

## 5. Composition vs Inheritance

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**React favors composition.** Inheritance leads to tight coupling and brittle hierarchies.

```jsx
// ❌ BAD: Inheritance
class BaseButton extends React.Component { /* ... */ }
class RedButton extends BaseButton { /* ... */ }

// ✅ GOOD: Composition
function Button({ variant, children }) {
  return <button className={`btn btn-${variant}`}>{children}</button>;
}
function RedButton(props) {
  return <Button variant="danger" {...props} />;
}
```

**Java parallel**: In Swing/AWT, you extend `JPanel` to create custom components. React flips this — you nest components instead of extending them. This matches modern Java composition patterns (decorator, strategy) over deep class hierarchies.

**Specialization**: Instead of `class Dialog extends Window`, compose:
```jsx
function ConfirmDialog({ message, onConfirm }) {
  return (
    <Dialog>
      <p>{message}</p>
      <Button onClick={onConfirm}>OK</Button>
    </Dialog>
  );
}
```

---

## 6. Refs (useRef, createRef, callback refs)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### useRef

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.

```jsx
function AutoFocus() {
  const inputRef = useRef(null);
  useEffect(() => { inputRef.current?.focus(); }, []);
  return <input ref={inputRef} />;
}
```

### Ref as instance variable (holds value across renders without causing re-render)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.

```jsx
function Timer() {
  const intervalRef = useRef(null);
  const start = () => {
    intervalRef.current = setInterval(() => {}, 1000);
  };
  const stop = () => {
    clearInterval(intervalRef.current);
  };
  // ...
}
```

### Callback ref (ref pattern for dynamic refs)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.

```jsx
function MeasureExample() {
  const [height, setHeight] = useState(0);
  const measuredRef = useCallback(node => {
    if (node !== null) setHeight(node.getBoundingClientRect().height);
  }, []);
  return <div ref={measuredRef}>Measured</div>;
}
```

### Forward ref (passing ref through to child)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.

```jsx
const FancyInput = forwardRef((props, ref) => (
  <input ref={ref} className="fancy" />
));
```

---

## 7. Portals

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


Render a child outside the parent DOM hierarchy (modals, tooltips, dropdowns).

```jsx
import { createPortal } from "react-dom";

function Modal({ children, open }) {
  if (!open) return null;
  return createPortal(
    <div className="modal-overlay">{children}</div>,
    document.getElementById("modal-root")
  );
}
```

**Event bubbling**: Events bubble through React tree, not DOM tree. A click inside a portal can still trigger an `onClick` on a parent React component.

**Production note**: Portal target must exist in DOM before render. Common failure: `document.getElementById('modal-root')` returns null if the element is rendered by React itself in a sibling tree.

---

## 8. Fragments

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


Avoid unnecessary wrapper DOM nodes.

```jsx
// ❌ Adds extra <div> to DOM
function Table() {
  return (
    <div>
      <td>A</td>
      <td>B</td>
    </div>
  );
}

// ✅ No extra DOM node
function Table() {
  return (
    <>
      <td>A</td>
      <td>B</td>
    </>
  );
}
```

**Short syntax** `<>...</>` vs `<Fragment>...</Fragment>`: The short form does not support `key` props. Use `<Fragment key={id}>` for mapped fragments.

---

## 9. Error Boundaries

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


Class component that catches errors during render, in lifecycle, and in constructors.

```jsx
class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    logError(error, errorInfo); // Send to Sentry/Datadog
  }

  render() {
    if (this.state.hasError) {
      return <FallbackUI error={this.state.error} />;
    }
    return this.props.children;
  }
}
```

**Limitations**: Error boundaries do NOT catch errors in:
- Event handlers (use try/catch)
- Async code (use try/catch)
- Server-side rendering
- Errors thrown in the error boundary itself

### Production Failure: Facebook Comment Composer Crash (2017)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**What happened**: A gap in error boundary coverage caused the Facebook comment composer to crash silently. An unhandled error in a nested third-party plugin (emojis) was not caught because:
1. The error boundary was placed too high in the tree
2. The error occurred in event handler code (not covered by boundaries)

**Root cause**: Developers assumed the error boundary would catch all errors, but event handlers are deliberately NOT caught by boundaries.

**Fix**: Add try/catch around third-party integrations + place granular error boundaries per widget.

```jsx
function CommentComposer() {
  return (
    <ErrorBoundary fallback={<BasicCommentBox />}>
      <EmojiPicker /> {/* Third-party, might throw */}
      <RichTextEditor />
    </ErrorBoundary>
  );
}
```

---

## 10. Higher-Order Components (HOC)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


Function that takes a component and returns an enhanced component.

```jsx
function withAuth(WrappedComponent) {
  return function AuthenticatedComponent(props) {
    const { user } = useAuth();
    if (!user) return <Redirect to="/login" />;
    return <WrappedComponent {...props} user={user} />;
  };
}

const DashboardPage = withAuth(Dashboard);
```

**Pitfalls**: 
- Name collisions (prop forwarding)
- Static method loss (need `hoist-non-react-statics`)
- Ref forwarding issues (use `forwardRef`)
- Double wrapping same HOC

---

## 11. Render Props

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


Pass a function as `children` (or any prop) that returns React elements.

```jsx
function MouseTracker({ render }) {
  const [pos, setPos] = useState({ x: 0, y: 0 });
  useEffect(() => {
    const handler = (e) => setPos({ x: e.clientX, y: e.clientY });
    window.addEventListener('mousemove', handler);
    return () => window.removeEventListener('mousemove', handler);
  }, []);
  return render(pos);
}

// Usage
<MouseTracker render={({ x, y }) => <h1>{x}, {y}</h1>} />
```

**Comparison with Hooks**: Most render prop patterns are now replaced by custom hooks. `MouseTracker` → `useMousePosition()`.

---

## 12. Controlled vs Uncontrolled Components

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


| Aspect | Controlled | Uncontrolled |
|---|---|---|
| Value source | React state | DOM node (ref) |
| Updates | Via setState | DOM events + ref.read |
| Predictability | High | Lower |
| Validation | Real-time | Manual |
| Use case | Forms, complex inputs | Simple inputs, file |

```jsx
// Controlled
function ControlledInput() {
  const [value, setValue] = useState('');
  return <input value={value} onChange={e => setValue(e.target.value)} />;
}

// Uncontrolled
function UncontrolledInput() {
  const ref = useRef(null);
  const handleSubmit = () => console.log(ref.current.value);
  return <input ref={ref} defaultValue="initial" />;
}
```

---

## 13. Keys & Reconciliation

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Keys help React identify which items changed, added, or removed.**

```jsx
// ✅ Stable, unique key
{todos.map(todo => <TodoItem key={todo.id} todo={todo} />)}

// ❌ Index as key (problematic with dynamic lists)
{todos.map((todo, idx) => <TodoItem key={idx} todo={todo} />)}
```

### How Reconciliation Works

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


1. React diffs element trees level by level
2. If types differ, teardown + rebuild entire subtree
3. If keys differ, teardown + rebuild
4. Same key + same type → update existing instance

### Interview Trick: Key Reconciliation Causing Duplicate Renders

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Scenario**: A list where items reorder. Using index as key.

```jsx
function List() {
  const [items, setItems] = useState(['A', 'B', 'C']);
  const prepend = () => setItems([`${Date.now()}`, ...items]);

  return (
    <ul>
      {items.map((item, i) => (
        <li key={i}>
          <ExpensiveInput defaultValue={item} />
        </li>
      ))}
    </ul>
  );
}
```

**Problem**: When prepending, `key=0` stays with 'A' (now second item), but React thinks the same component instance stayed. It re-renders `ExpensiveInput` but `defaultValue` only initializes once, so all values shift incorrectly.

**Root cause**: Index keys cause React to misidentify which items changed. After prepend, every existing item gets a new index, forcing React to reconcile every item's children unnecessarily — O(n) extra work.

**Fix**: Use stable unique IDs.

---

## 14. Synthetic Events

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


React wraps native events in `SyntheticEvent` for cross-browser normalization.

```jsx
function ClickHandler() {
  const handleClick = (e) => {
    // e is SyntheticEvent (not native MouseEvent)
    e.preventDefault();
    console.log(e.nativeEvent); // The real event
  };
  return <button onClick={handleClick}>Click</button>;
}
```

**Event pooling** (React <17): SyntheticEvent objects are pooled and reused. Accessing `e.target` asynchronously fails:

```jsx
// ❌ React <17: e.target is null after setTimeout
function Broken() {
  const handle = (e) => {
    setTimeout(() => console.log(e.target), 100); // null!
  };
  return <button onClick={handle}>Click</button>;
}

// ✅ Fix: e.persist()
const handle = (e) => {
  e.persist();
  setTimeout(() => console.log(e.target), 100);
};
```

React 17+ removed event pooling, so this is no longer needed.

---

## 15. dangerouslySetInnerHTML

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


React's equivalent of `innerHTML`. Must be used when rendering raw HTML strings.

```jsx
function RichContent({ html }) {
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}
```

**Risks**:
- XSS vulnerabilities if `html` is unsanitized
- Breaks React's reconciliation (React cannot diff HTML strings)
- All event listeners inside lose React context

**Production rule**: Sanitize with DOMPurify BEFORE passing to component:
```jsx
import DOMPurify from 'dompurify';

function SafeHTML({ html }) {
  const clean = DOMPurify.sanitize(html);
  return <div dangerouslySetInnerHTML={{ __html: clean }} />;
}
```

---

## 16. Server Components (RSC)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


React Server Components run ONCE on the server — zero bundle size, direct DB access.

```jsx
// ServerComponent.server.js — runs on server
import db from 'db';

async function PostList() {
  const posts = await db.query('SELECT * FROM posts');
  return (
    <ul>
      {posts.map(p => <li key={p.id}>{p.title}</li>)}
    </ul>
  );
}
```

**Key differences**:
- Cannot use hooks, state, event handlers
- Can `await` directly
- Zero JS sent to client
- Can seamlessly compose with client components

---

## 17. Concurrent Mode (React 18)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


React can interrupt, pause, resume, or abandon renders.

```jsx
import { startTransition } from 'react';

function SearchResults({ query }) {
  const [results, setResults] = useState([]);

  function handleChange(e) {
    // Urgent: update input
    setQuery(e.target.value);

    // Non-urgent: defer results rendering
    startTransition(() => {
      setResults(fetchResults(e.target.value));
    });
  }
}
```

**Mental model**: Concurrent mode is like a priority queuing system. High-priority updates (user typing) preempt low-priority work (rendering results list). Java's `PriorityBlockingQueue` or `ExecutorService` with thread priorities is analogous — the scheduler can pause lower-priority tasks when higher-priority work arrives.

---

## 18. Suspense Boundaries

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


Wait for something (data, code) before rendering.

```jsx
<Suspense fallback={<Spinner />}>
  <LazyComponent />
  <Await promise={fetchData()}>
    {data => <DataView data={data} />}
  </Await>
</Suspense>
```

**Nested Suspense**: Each boundary is independent. If one suspends, only its fallback shows.

---

## 19. Streaming SSR

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


React 18 can stream HTML as it's generated, improving TTFB.

```jsx
// server.js (Node)
import { renderToPipeableStream } from 'react-dom/server';

app.get('/', (req, res) => {
  const { pipe } = renderToPipeableStream(<App />, {
    bootstrapScripts: ['/main.js'],
    onShellReady() { pipe(res); }
  });
});
```

**How it works**:
1. React renders shell immediately
2. Suspense boundaries that suspend get replaced by fallback HTML
3. When data resolves, React streams replacement HTML + inline `<script>` to swap

---

## 20. Hydration Failures — Production Case

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### GitHub's 2020 React Hydration Bug (27M users affected)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**What happened**: GitHub's server-rendered markup and client-rendered markup differed due to timestamp rendering. React 16 detected mismatch and performed "one-sided" correction — but in some cases this caused entire page to blank.

**Root cause**: A `<RelativeTime date={date} />` component rendered "5 minutes ago" from server time. By the time JS hydrated on client, it was "6 minutes ago". React threw hydration mismatch warning and re-rendered, but the mismatch cascaded through sibling components.

**Impact**: 27M users saw blank pages on github.com for ~4 hours during gradual rollout.

**Fix**: 
```jsx
// ✅ Suppress hydration mismatch for time-sensitive content
function RelativeTime({ date }) {
  const [label, setLabel] = useState('');
  useEffect(() => {
    setLabel(formatRelative(date));
    const interval = setInterval(() => setLabel(formatRelative(date)), 60000);
    return () => clearInterval(interval);
  }, [date]);

  if (!label) return <span suppressHydrationWarning>{formatRelative(date)}</span>;
  return <span>{label}</span>;
}
```

### Backpressure in Streaming SSR Under Load

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Scenario**: A news site streams SSR content. During traffic spike, one Suspense boundary waits for a slow API. The streaming buffer fills up, causing TCP backpressure. Node.js cannot flush more data → client TTFB spikes → CDN 502 errors.

```mermaid
sequenceDiagram
    Client->>Server: Request page
    Server->>Server: Render shell (fast)
    Server->>API: Fetch sidebar data (slow)
    Note over Server: Buffer fills while waiting
    Server-->>Client: Shell HTML (partial)
    Note over Client: Waiting for rest of HTML
    Server->>API: ... still waiting ...
    Note over Server: TCP buffer full → backpressure
    Server-->>Client: ⏳ No data sent (stalled)
    Client->>Client: Timeout after 10s
```

**Mitigation**:
- Set timeouts on all Suspense data fetches
- Use streaming compression (gzip/flush)
- Implement early flush of shell + fallback placeholders
- Load shed when connection count exceeds threshold

---

## 21. Large Component Trees — Performance

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Problem**: 2000+ component tree on a dashboard page causes 300ms+ render times.

**Diagnosis with React DevTools Profiler**:

```mermaid
graph TD
    subgraph "Component Tree Flame Graph"
        A[App] --> B[Sidebar]
        A --> C[MainContent]
        C --> D[ChartWidget]
        C --> E[DataGrid: 1000 rows]
        C --> F[FilterPanel]
        E --> G[Row: 1000x]
        G --> H[Cell: 10 per row]
    end
```

**Optimizations**:
1. `React.memo` on `Row` and `Cell` (check props shallowly)
2. Virtualize `DataGrid` (only render 20 visible rows)
3. `useMemo` on sorted/filtered data
4. Lift state up — avoid re-rendering entire tree when filter changes

---

## 22. Infinite Re-Render Loops

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Classic Pattern

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.

```jsx
// ❌ INFINITE LOOP: setState triggers re-render, which re-runs effect
function Broken() {
  const [count, setCount] = useState(0);
  useEffect(() => {
    setCount(count + 1); // Re-render → effect runs again → infinite
  }); // Missing dependency array
  return <div>{count}</div>;
}
```

### Subtle Pattern

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.

```jsx
function SubtleLoop() {
  const [user, setUser] = useState(null);
  const data = fetchData(user); // Called every render
  // ... unless useMemo'd
}
```

### Detection

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.

- Open DevTools Profiler → look for continuous commits
- React 18 Strict Mode renders twice in dev (catches side effects in render)

---

## 23. Prop Drilling Solutions

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Problem**: Passing `user` through 5+ levels of components.

### Solution 1: Context (see §24)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.

```jsx
const UserContext = createContext(null);
// App → UserContext.Provider → ... → DeepChild uses useContext(UserContext)
```

### Solution 2: Component Composition (Hoisting)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.

```jsx
function Page({ user }) {
  return (
    <Layout
      header={<UserHeader user={user} />}  {/* UserHeader gets user directly */}
      content={<DashboardContent />}        {/* DashboardContent doesn't need user */}
    />
  );
}
```

### Solution 3: State Management (Redux/Zustand)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.

Directly access `user` from store at any depth. See file 04.

---

## 24. Context vs Props

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


| Aspect | Props | Context |
|---|---|---|
| Drilling | Passes through each level | Skips intermediate levels |
| Re-render | Only children receiving changed props | All consumers re-render |
| Debuggability | Easy (trace props) | Harder (magical values) |
| Coupling | Low | Higher |
| Testing | Shallow render with props | Need provider wrapper |

**Rule of thumb**: Props for component-specific config. Context for truly global data (theme, locale, auth).

---

## 25. Default Props Patterns

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```jsx
// Functional: default parameters
function Button({ variant = 'primary', size = 'md', children }) { ... }

// Functional: defaultProps (deprecated)
Button.defaultProps = { variant: 'primary', size: 'md' };

// Class: static defaultProps
class Button extends React.Component {
  static defaultProps = { variant: 'primary' };
  render() { ... }
}

// TypeScript: default via destructuring
interface Props { variant?: string; }
function Button({ variant = 'primary' }: Props) { ... }
```

---

## 26. Component Composition Patterns

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Layout Component

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.

```jsx
function Layout({ header, sidebar, main, footer }) {
  return (
    <div className="layout">
      <header>{header}</header>
      <aside>{sidebar}</aside>
      <main>{main}</main>
      <footer>{footer}</footer>
    </div>
  );
}
```

### Container/Presentational

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.

```jsx
// Container (logic)
function UserContainer() {
  const { data, loading } = useQuery(GET_USERS);
  if (loading) return <Spinner />;
  return <UserList users={data.users} />;
}

// Presentational (pure render)
function UserList({ users }) {
  return users.map(u => <UserCard key={u.id} user={u} />);
}
```

---

## 27. Compound Components

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


Components that work together implicitly via shared state.

```jsx
function Tabs({ children, defaultIndex = 0 }) {
  const [activeIndex, setActiveIndex] = useState(defaultIndex);
  const childrenArray = Children.toArray(children);

  return (
    <div>
      <div className="tab-headers">
        {childrenArray.map((child, i) => (
          <button
            key={i}
            className={i === activeIndex ? 'active' : ''}
            onClick={() => setActiveIndex(i)}
          >
            {child.props.label}
          </button>
        ))}
      </div>
      <div className="tab-panel">
        {childrenArray[activeIndex]}
      </div>
    </div>
  );
}

// Usage
<Tabs>
  <TabPanel label="Profile">Profile content</TabPanel>
  <TabPanel label="Settings">Settings content</TabPanel>
</Tabs>
```

---

## 28. Slot Patterns

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


Named children slots for multiple insertion points.

```jsx
function Card({ children }) {
  const slots = {};
  Children.forEach(children, (child) => {
    slots[child.props.slot] = child;
  });
  return (
    <div className="card">
      <div className="card-header">{slots.header}</div>
      <div className="card-body">{slots.body}</div>
      <div className="card-footer">{slots.footer}</div>
    </div>
  );
}

// Usage
<Card>
  <h2 slot="header">Title</h2>
  <div slot="body">Content</div>
  <div slot="footer">Actions</div>
</Card>
```

---

## 29. Interview Tricky Questions

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Q1: Why does `setState({ count: count + 1 })` not update immediately?

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Answer**: React batches state updates. The new state is enqueued and applied during the next render. Accessing `count` right after `setState` returns the stale value.

```jsx
function Counter() {
  const [count, setCount] = useState(0);
  const handleClick = () => {
    setCount(count + 1);
    console.log(count); // Still 0!
  };
  return <button onClick={handleClick}>{count}</button>;
}
```

**Fix**: Use functional updater `setCount(c => c + 1)` for reliable increment.

### Q2: What happens when render() returns an array?

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


In React 16+, render can return an array (or fragment). This enables returning multiple elements without a wrapper.

### Q3: Can error boundaries catch errors in useEffect?

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


No. Errors in useEffect are considered async and are not caught by error boundaries. Use try/catch inside effects or use a global error handler.

### Q4: How does React know to re-render after setState?

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


React keeps a reference to the component instance (via fiber node). When `setState` is called, React marks the fiber as dirty and schedules a render on the next tick.

### Q5: Why does `key` need to be on the element inside map, not on the component?

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```jsx
// ❌ Wrong
{items.map(item => <Item key={item.id} />)}
// Actually this is CORRECT...

// ❌ Wrong placement
{items.map(item => (
  <div key={item.id}>
    <Item />
  </div>
))}
```

`key` must go on the outermost element returned from `map()`, because that's what React reconciles against.

---

## 30. Simplest Mental Model

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


> **Components = functions that return React elements. JSX = sugar for createElement. Props = inputs. State = memory. Re-render = function re-execution. Reconciliation = diff algorithm. Keys = identity markers.**

| If you want to... | Use... |
|---|---|
| Pass data down | Props |
| Store changing data | State |
| Skip re-render | memo / useMemo |
| Access DOM | useRef |
| Render in different DOM node | createPortal |
| Catch render errors | ErrorBoundary |
| Reuse logic | Custom hooks |
| Share global data | Context |
| Named insertion points | Slot pattern |
| Zero-bundle server code | Server Components |

---

## 31. Quick Reference Table

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


| Concept | Syntax | When to Use |
|---|---|---|
| JSX | `<div>` | Every React file |
| Fragment | `<>...</>` | Multiple root nodes |
| Portal | `createPortal` | Modals, tooltips |
| Error Boundary | Class component | Production error handling |
| HOC | `withX(Component)` | Cross-cutting before hooks |
| Render Prop | `render={fn}` | Code reuse (legacy) |
| Compound Component | Shared context | Related components |
| Slot | `slot="name"` | Multiple insertion points |
| Controlled | `value` + `onChange` | Form inputs |
| Uncontrolled | `ref` + `defaultValue` | Simple inputs |

---

## 32. Mermaid: Component Communication Flow

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```mermaid
graph TB
    A[App State] -->|Props| B[Parent Component]
    A -->|Context| C[Deep Child]
    B -->|Props| D[Child]
    B -->|Callback| E[Child triggers parent]
    D -->|State| F[Local UI state]
    D -->|Ref| G[DOM node access]
    F -->|useEffect| H[Side Effects API/Subscriptions]
    H -->|Cleanup| I[Unmount cleanup]
    C -->|useContext| J[Global data]
    B -->|Error Boundary| K[Error fallback UI]
```

---

## 33. Production Failure: Hydration Mismatch Crash

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Full timeline**:
1. Server renders `<ProfilePage><PostList><Post>...` with `posts` from DB
2. Client loads HTML, React hydrates
3. Third-party analytics script modifies DOM before hydration (adds a `<div>`)
4. React expects exact tree match → mismatch detected
5. React re-renders client-side, but the DOM order is now off
6. In React 16, this triggers full re-render (non-graceful)
7. If a component relied on DOM state (scroll position, focus), it's lost
8. Worst case: blank white screen for users on slow connections

**Prevention checklist**:
- `suppressHydrationWarning` for time-sensitive content
- Avoid third-party DOM mutation before hydration
- Defer analytics/ads to after hydration
- Use React 18's `hydrateRoot` for better mismatch recovery

---

## 34. Mermaid: Hydration Process

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```mermaid
sequenceDiagram
    participant S as Server
    participant C as Client
    participant D as DOM
    S->>C: Send HTML string (SSR)
    Note over C: Browser paints HTML immediately
    C->>D: React loads JS bundles
    C->>D: hydrateRoot() attaches event listeners
    D-->>C: ✅ Match: events bound, interactive
    Note over C: If mismatch → client re-render
    C->>D: Reconciliation (expensive)
```

---

## 35. Controlled vs Uncontrolled — Deep Production View

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Production scenario**: A form with 50 fields built uncontrolled. User submits → validation catches 5 errors → React has no refs to individual fields → you need `document.querySelector` (fragile). 

**Rule**: Use controlled for anything with validation, conditional UI, or complex interactions. Use uncontrolled for:
- File inputs (must be uncontrolled)
- Performance-critical forms with 100+ fields (less state overhead)
- Simple search inputs where you only need value on submit

---

## 36. Class vs Functional Component Decision Matrix

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


| Requirement | Class | Functional + Hooks |
|---|---|---|
| Error boundary | ✅ Required | ❌ Not possible |
| Lifecycle logic | ✅ Explicit methods | ✅ useEffect |
| State complexity | ❌ this.setState merges | ✅ useReducer |
| Reusable logic | ❌ Mixins/HOCs | ✅ Custom hooks |
| Tree shaking | ❌ Prototype methods stay | ✅ Better dead code elimination |
| DevTools naming | ✅ displayName | ✅ Named function |

---

## 37. Mermaid: Reconciliation Decision Tree

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```mermaid
flowchart TD
    A[Next render] --> B{Same element type?}
    B -->|Yes| C{Same key?}
    B -->|No| D[Destroy old subtree<br/>Build new subtree]
    C -->|Yes| E[Update existing instance<br/>New props]
    C -->|No| F[Unmount old<br/>Mount new]
    E --> G[Rerender children recursively]
    D --> H[componentWillUnmount<br/>constructor<br/>componentDidMount]
    F --> H
    G --> I[Commit to DOM]
    H --> I
```

---

## 38. Synthetic Events vs Native Events

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


| | Synthetic Event | Native Event |
|---|---|---|
| Cross-browser | ✅ Normalized | ❌ Vary per browser |
| Pooled (<17) | ✅ Reused | ❌ |
| Memory | Managed by React | Managed by browser |
| Bubble through React tree | ✅ | ❌ (React tree != DOM tree) |
| Performance | Delegated to root | Attached per element |

---

## 39. Backpressure in Component Rendering

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Scenario**: A dashboard re-renders 50 charts on every data update (100ms interval). Each chart re-computes layout, scales, and paths.

```mermaid
graph LR
    subgraph "Backpressure Chain"
        A[WebSocket] -->|100msg/s| B[State Update]
        B -->|batch| C[Render Queue]
        C -->|synchronous| D[Fiber Reconciliation]
        D -->|commit| E[DOM Paint]
        E -->|blocked| F[Input events queued]
        F -->|dropped| G[Frame drop 250ms]
    end
```

**Mitigations**:
- Throttle updates (use `requestAnimationFrame` or `useTransition`)
- Virtualize charts (only render visible ones)
- Use `useMemo` on expensive computations
- Debounce rapid state changes

---

## 40. Interview: Key Reconciliation Causing Duplicate Renders (Deep Dive)

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


**Question**: "I have a list of 1000 items. I prepend one item. Why does my list flash and lose input focus?"

**Answer**: Using index as key causes React to misidentify every item. When prepending:

```javascript
// Before: keys [0, 1, 2, ..., 999]
// After prepend: keys [0, 1, 2, ..., 1000]
// React thinks:
//   - key=0 changed from 'A' to 'NEW' (updated)
//   - key=1 changed from 'B' to 'A' (updated)
//   - key=2 changed from 'C' to 'B' (updated)
//   - ... every single item "changed"
```

Instead of recognizing that items B–1000 are the same, React re-renders all 1000 items. With `key={item.id}`, React would:
- See `key=NEW` (new mount)
- See `keys A–1000` as unchanged (no re-render)

**Performance cost**: Without stable keys, prepend to 1000 items = 1000 reconciliations. With stable keys = 1 mount + 999 no-ops.

---

## 41. Server Components vs Client Components

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```jsx
// Post.server.jsx — 0 KB JS, runs on server, can access DB directly
import db from 'db';
export default async function Post({ id }) {
  const post = await db.post.findUnique({ where: { id } });
  return <article><h1>{post.title}</h1><p>{post.body}</p></article>;
}

// LikeButton.client.jsx — sent to client, has state/effects
'use client';
import { useState } from 'react';
export default function LikeButton({ postId }) {
  const [liked, setLiked] = useState(false);
  return <button onClick={() => setLiked(!liked)}>{liked ? '❤️' : '🤍'}</button>;
}
```

**Java comparison**: Server Components = JSP running on server with full DB access. Client Components = GWT compiled to JS running in browser. RSC bridges both worlds seamlessly.

---

## 42. Conditional Rendering Patterns

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```jsx
// If/else ternary
{isLoggedIn ? <Dashboard /> : <Login />}

// Logical AND (short-circuit)
{error && <ErrorBanner message={error} />}

// Switch pattern (immediately-invoked)
{(() => {
  switch (status) {
    case 'loading': return <Spinner />;
    case 'error': return <Error />;
    case 'success': return <Data />;
    default: return null;
  }
})()}
```

---

## 43. Mermaid: Component Lifecycle Phases

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


```mermaid
stateDiagram-v2
    [*] --> Mount
    Mount --> Update: setState / new props
    Update --> Update: Re-render cycle
    Update --> Unmount: Component removed
    Unmount --> [*]

    state Mount {
        constructor --> render
        render --> componentDidMount
    }
    state Update {
        shouldUpdate --> render
        render --> componentDidUpdate
    }
    state Unmount {
        componentWillUnmount --> [*]
    }
```

---

## 44. Production Checklist for Components

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


- [ ] Every list item has a stable, unique `key`
- [ ] Error boundary wraps at least each top-level route
- [ ] No `dangerouslySetInnerHTML` without DOMPurify
- [ ] No index as key for dynamic lists
- [ ] Event handlers wrapped in `useCallback` if passed to memo'd children
- [ ] No side effects in render function body
- [ ] Cleanup functions in all `useEffect` with subscriptions
- [ ] `defaultProps` not using deprecated class static
- [ ] Portal targets exist before portal renders
- [ ] No direct DOM manipulation that React owns

---

## Related

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


- [Networking](../../11-networking/) — HTTP, performance, optimization
- [Security](../../13-security/) — CORS, authentication, XSS prevention
- [Backend](../../03-backend/) — API design and contracts
- [Performance Engineering](../../18-performance-engineering/) — Browser rendering
- [Testing](../../19-testing/) — E2E and component testing



## Component Composition Patterns

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.


### Pattern 1: Render Props

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.

```jsx
// Flexible component reuse via function prop
<DataFetcher url="/api/users" render={(users) => <UserList users={users} />} />
```

### Pattern 2: Higher-Order Components

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.

```jsx
// Wrap component to add functionality
const withAuth = (Component) => (props) => 
  isLoggedIn ? <Component {...props} /> : <Login />;

export default withAuth(Dashboard);
```

### Pattern 3: Custom Hooks

#### Step-by-Step
1. Process input
2. Validate
3. Execute
4. Return result

#### Code Example
```python
# Example implementation
pass
```

#### Real-World Scenario
This pattern is commonly used in production systems.

```jsx
// Extract logic into reusable hook
const useUserData = (userId) => {
  const [user, setUser] = useState(null);
  useEffect(() => {
    fetch(`/api/users/${userId}`).then(setUser);
  }, [userId]);
  return user;
};
```

