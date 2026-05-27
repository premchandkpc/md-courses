# 09: Performance Optimization — Deep Reference

> **Scope**: Profiling, rendering optimization, bundle optimization, code splitting, lazy loading, virtualization, memoization, CWV, Lighthouse, perf budgets


## Performance Optimization Checklist

```mermaid
graph TD
    A["Find bottleneck"] --> B{Type?}
    B -->|Render slow| C["React.memo<br/>useMemo<br/>useCallback"]
    B -->|Bundle big| D["Code split<br/>Lazy load<br/>Tree shake"]
    B -->|Runtime slow| E["Virtual lists<br/>Windowing<br/>Defer"]
    B -->|Network slow| F["Cache<br/>Compress<br/>CDN"]
    
    C --> G["Measure"]
    D --> G
    E --> G
    F --> G
    G --> H["Verify"]
    
    style A fill:#4a8bc2
    style B fill:#c73e1d
    style H fill:#1a5d3a
```


## 1. React Profiler

### DevTools Profiler

The React DevTools Profiler records render timing per component as an interactive flamegraph. Each bar represents a commit; bar width = render duration. Components in gray did not re-render.

```jsx
// Programmatic Profiler — wrap树上 to measure
import { Profiler } from "react";

function onRender(
  id,            // "TreeList"
  phase,         // "mount" | "update"
  actualTime,    // ms spent rendering this tree
  baseTime,      // ms for subtree without memoization
  startTime,     // when React began this render
  commitTime     // when React committed
) {
  console.log(`${id} ${phase}: ${actualTime.toFixed(2)}ms`);
}

<Profiler id="TreeList" onRender={onRender}>
  <TreeList data={items} />
</Profiler>
```

### Flamegraph Interpretation

- Wide bars = slow components → memoize or restructure.
- Narrow bars between commits = wasted renders → check memo deps.
- Renders appearing when props/state haven't changed → stale references.
- "Why did this render?" — use `useWhyDidYouUpdate` debug hook during development.

### Flame Graph — Component-Level Breakdown

```mermaid
gantt
    title React Profiler Flame Graph (Commit)
    dateFormat X
    axisFormat %ms
    section App
    App render      :0, 2
    section Sidebar
    Sidebar render  :2, 5
    section Main
    MainContent     :7, 8
    section Chart
    Chart render    :8, 35
    section Table
    Table render    :35, 45
    section Footer
    Footer render   :45, 46
```

**Reading the flame graph**:
- **X-axis**: Time within the commit (total render time)
- **Y-axis**: Component tree depth
- **Bar width**: Time spent rendering that component + its children
- **Grey bars**: Components that didn't re-render
- **Ranked by time**: The widest bar at each level is the most expensive

### Identifying Wasted Renders in Profiler

1. Open React DevTools → Profiler tab → Record
2. Perform the action you want to optimize
3. Look at the commit list in the right sidebar
4. Click a commit → click a component in the flame graph
5. Check "Why did this render?" in the right panel

**Common findings**:
```
<ExpensiveList> rendered because:
  Props changed: { onSelect: function () }
  • onSelect: reference changed (new function every render)
  → Fix: wrap in useCallback
```

### The "Why Did You Render" Pattern

```jsx
// Drop-in hook for development — logs unnecessary re-renders
function useWhyDidYouUpdate(name, props) {
  const previousProps = useRef();

  useEffect(() => {
    if (previousProps.current) {
      const allKeys = Object.keys({ ...previousProps.current, ...props });
      const changes = {};

      allKeys.forEach(key => {
        if (previousProps.current[key] !== props[key]) {
          changes[key] = {
            from: previousProps.current[key],
            to: props[key],
          };
        }
      });

      if (Object.keys(changes).length) {
        console.log(`[why-did-you-update] ${name}:`, changes);
      }
    }
    previousProps.current = props;
  });
}

// Usage
function Parent() {
  const [count, setCount] = useState(0);
  useWhyDidYouUpdate('Parent', { count, setCount });
  return <Child onClick={() => setCount(c => c + 1)} />;
}
```

### Why Did You Render (wdyr) Library

For systematic detection across the entire app:

```bash
npm install @welldone-software/why-did-you-render
```

```jsx
import whyDidYouRender from '@welldone-software/why-did-you-render';

// Enable in development only
if (process.env.NODE_ENV === 'development') {
  whyDidYouRender(React, {
    trackAllPureComponents: true,
    trackExtraHooks: [
      [useMemo, 'useMemo'],
      [useCallback, 'useCallback'],
    ],
    logOnDifferentValues: true,
  });
}

// Mark components to track
ExpensiveList.whyDidYouRender = true;
```

### React.memo Debugging

**Pattern**: `memo` appears to work but component still re-renders:

```jsx
const Child = memo(({ config, onClick }) => {
  console.log('Child rendered');
  return <button onClick={onClick}>Click</button>;
});

function Parent() {
  const [count, setCount] = useState(0);

  // ❌ Problem: onClick is a new function every render
  // Even with memo, Child re-renders because onClick reference changes
  return <Child config={{ theme: 'dark' }} onClick={() => setCount(c => c + 1)} />;
}
```

**Debugging memo failures**:

```javascript
// Step 1: Check if memo is receiving unchanged props
// Use custom comparison function to debug
const Child = memo(
  (props) => { /* ... */ },
  (prev, next) => {
    // Log what's changing
    Object.keys(next).forEach(key => {
      if (prev[key] !== next[key]) {
        console.log(`Prop "${key}" changed:`, prev[key], '→', next[key]);
      }
    });
    return false; // Force re-render for debugging
  }
);

// Step 2: Check for inline objects/arrays
// ❌ New object every render
<Child config={{ theme: 'dark' }} />

// ✅ Stable reference
const config = useMemo(() => ({ theme: 'dark' }), []);
<Child config={config} />

// Step 3: Check for callback identity
// ❌ New function every render
<Child onClick={() => handleClick(id)} />

// ✅ Stable callback
const handleClick = useCallback(() => {
  setCount(c => c + 1);
}, []);
<Child onClick={handleClick} />
```

### React DevTools Profiler — Ranked View

The "Ranked" view shows components sorted by render time within a commit:

```
Ranked commit #3 (12ms)
  ─────────────────────────────
  App             0.5ms  (1.2%)
  Sidebar         0.3ms  (0.8%)
  MainContent     0.2ms  (0.5%)
  ExpensiveChart  8.0ms  (66.7%)  ← FOCUS HERE
  DataGrid        2.5ms  (20.8%)
  Footer          0.1ms  (0.3%)
```

**Action**: If `ExpensiveChart` takes 66% of render time:
1. Does it need to re-render? Check `memo` / `useMemo`
2. Can the computation be deferred? `useDeferredValue`
3. Can it be virtualized? Only render visible portion

### Component Rendering Timelines

The Profiler's "Timeline" view (React 18+) shows **when** each component rendered across commits:

```mermaid
gantt
    title Component Render Timeline
    dateFormat X
    axisFormat %s

    section Commit 1
    App         :0, 2
    Header      :2, 4
    Footer      :4, 5

    section Commit 2 (data refresh)
    App         :10, 11
    Header      :11, 12
    DataGrid    :12, 35
    Footer      :35, 36

    section Commit 3 (filter change)
    App         :50, 51
    Header      :51, 52
    DataGrid    :52, 60
    Footer      :60, 61
```

### Profiling in Production

```jsx
// React Profiler component — works in production
import { Profiler, useState } from 'react';

function onRenderCallback(
  id,             // Profiler id
  phase,          // "mount" or "update"
  actualDuration, // Time spent rendering this tree
  baseDuration,   // Estimated time without memoization
  startTime,      // When React started rendering
  commitTime,     // When React committed
  interactions    // Set of interactions (e.g., setState calls)
) {
  // Send to analytics in production
  if (actualDuration > 16) { // >1 frame at 60fps
    analytics.track('slow-render', {
      component: id,
      duration: actualDuration,
      phase,
    });
  }
}

function App() {
  return (
    <Profiler id="App" onRender={onRenderCallback}>
      <MainContent />
    </Profiler>
  );
}
```

### Performance Debugging Workflow

```mermaid
flowchart TD
    A[Start profiling] --> B[Perform slow interaction]
    B --> C[Check Profiler commits]
    C --> D{Any commit > 16ms?}
    D -->|No| E[✅ Performance OK]
    D -->|Yes| F[Click slow commit → flame graph]
    F --> G[Identify widest bar]
    G --> H{Why did it render?}
    H --> I[Props changed? Check "why did this render"]
    I --> J[Stabilize props: useMemo/useCallback]
    H --> K[Computation heavy? Check useMemo]
    K --> L[Wrap expensive computation]
    H --> M[Large list? Check virtualization]
    M --> N[Virtualize with react-window]
    J --> A
    L --> A
    N --> A
```

### Production Debugging Checklist

- [ ] React DevTools Profiler used to identify slow components
- [ ] "Why did this render?" checked for all unexpectedly re-rendering components
- [ ] `React.memo` applied to components with stable props
- [ ] `useCallback` applied to callbacks passed to memo'd children
- [ ] `useMemo` applied to expensive computations
- [ ] Inline objects/arrays extracted with `useMemo` for stable references
- [ ] wdyr (why-did-you-render) used in development to catch unnecessary renders
- [ ] Profiler `onRender` callback used in production to track slow commits
- [ ] Bundle size analyzed and compared against performance budget
- [ ] Flame graph reviewed for deep component trees causing cascading renders

**Cross-reference**: See [Production Issues](./07-production-issues.md) for error tracking and monitoring. See [Rendering Performance](./03-rendering-performance.md) for Fiber architecture and reconciliation optimizations.

## 2. Reconciliation & Fiber

React maintains a **Fiber tree** (linked list of fiber nodes). During reconciliation:

1. **Diffing** — React compares the returned element tree against the current fiber tree.
2. **Key** — `key` props help React identify list items across renders. Never use index as key if order can change.
3. **Double-buffering** — React builds the "work-in-progress" fiber tree, then swaps (`commitRoot`) on completion. This enables interruption for concurrent features.

```jsx
// Bad — index as key breaks animations + causes unnecessary remounts
{items.map((item, i) => <Item key={i} {...item} />)}

// Good — stable unique key
{items.map((item) => <Item key={item.id} {...item} />)}
```

## 3. Memoization

### React.memo

Prevents re-render when props are shallow-equal. Always pair with `useMemo`/`useCallback` for reference-type props.

```jsx
const ExpensiveList = React.memo(function ExpensiveList({ items, onSelect }) {
  return items.map((item) => (
    <div key={item.id} onClick={() => onSelect(item.id)}>
      {item.name}
    </div>
  ));
});

// Without useCallback, onSelect is a new function every render → React.memo is useless
function Parent() {
  const [items, setItems] = useState([]);
  const onSelect = useCallback((id) => {
    console.log("selected", id);
  }, []);
  return <ExpensiveList items={items} onSelect={onSelect} />;
}
```

### useMemo / useCallback Trade-offs

```jsx
// Expensive computation — cache with useMemo
const sorted = useMemo(
  () => items.slice().sort((a, b) => a.name.localeCompare(b.name)),
  [items]
);

// Stable callback — needed for child memoization
const handleClick = useCallback(
  (id) => dispatch({ type: "SELECT", payload: id }),
  [dispatch]
);
```

**When not to memoize**: primitive props, small lists, components that always re-render anyway. The comparison itself has cost. Profile before optimizing.

## 4. Code Splitting

### React.lazy + Suspense

```jsx
import { lazy, Suspense } from "react";

const Dashboard = lazy(() => import("./Dashboard"));
const Settings = lazy(() => import("./Settings"));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}
```

### Webpack / Vite Configuration

```jsx
// webpack splitChunks — separate vendor + shared chunks
// optimization: {
//   splitChunks: {
//     chunks: "all",
//     cacheGroups: {
//       vendor: { test: /[\\/]node_modules[\\/]/, chunks: "all" },
//     },
//   },
// }

// React.lazy + named exports
const Admin = lazy(() => import("./Admin").then((m) => ({ default: m.Admin })));

// loadable-components for SSR
import loadable from "@loadable/component";
const Heavy = loadable(() => import("./Heavy"), { fallback: <Spinner /> });
```

## 5. Tree Shaking

Ensure bundler can eliminate dead code:

- Use ES module imports (`import { debounce } from "lodash-es"` not `import _ from "lodash"`).
- Set `"sideEffects": false` in `package.json` (unless CSS/global polyfills).
- Avoid barrel files (`index.ts` re-exporting everything) — they prevent tree shaking.

## 6. Virtualization

Render only visible items. react-window and react-virtuoso are the primary options.

```jsx
import { FixedSizeList } from "react-window";

function VirtualList({ items }) {
  const Row = ({ index, style }) => (
    <div style={style}>{items[index].name}</div>
  );

  return (
    <FixedSizeList
      height={600}
      itemCount={items.length}
      itemSize={50}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
}
```

For variable heights, use `VariableSizeList` or react-virtuoso (auto-measures). Infinite scroll:

```jsx
import { Virtuoso } from "react-virtuoso";

function InfiniteFeed() {
  const [items, setItems] = useState([]);

  const loadMore = useCallback(async () => {
    const more = await fetchMore();
    setItems((prev) => [...prev, ...more]);
  }, []);

  return (
    <Virtuoso
      data={items}
      itemContent={(_, item) => <div>{item.title}</div>}
      endReached={loadMore}
    />
  );
}
```

## 7. Context Optimization

Context re-renders all consumers on any value change. Solutions:

```jsx
// 1. Split contexts
const UserContext = createContext();
const ThemeContext = createContext();

// 2. Split values never change together
function App() {
  return (
    <ThemeContext.Provider value={theme}>
      <UserContext.Provider value={user}>
        <Layout />
      </UserContext.Provider>
    </ThemeContext.Provider>
  );
}

// 3. Atom state (zustand/jotai) — subscribe to slices
import { create } from "zustand";

const useStore = create((set) => ({
  user: null,
  notifications: [],
  setUser: (user) => set({ user }),
}));

// Only re-renders when `user` changes
function Avatar() {
  const user = useStore((s) => s.user);
  return <img src={user?.avatar} />;
}
```

## 8. Asset Optimization

### Images

```jsx
// next/image — automatic optimization, lazy loading, srcset
import Image from "next/image";

<Image
  src="/hero.webp"
  alt="Hero"
  width={1200}
  height={600}
  priority          // above-the-fold — skip lazy loading
  placeholder="blur" // show blur-up while loading
  blurDataURL="data:image/webp;base64,..."
/>

// Native lazy loading fallback
<img src="photo.jpg" loading="lazy" decoding="async" />
```

Use WebP/AVIF with `<picture>` for universal browser support. Serve responsive `srcset` sizes.

### Fonts

```jsx
// next/font — self-hosted, subset, no layout shift
import { Inter } from "next/font/google";
const inter = Inter({ subsets: ["latin"] });
// → injects <link> with font-display: swap, preloads
```

## 9. Rendering Optimizations

### Automatic Batching (React 18)

React 18 batches state updates inside promises, timeouts, and native events automatically:

```jsx
// Before React 18 — two renders
fetch("/data").then(() => {
  setLoading(false);  // render 1
  setData(result);    // render 2
});

// React 18 — one render (auto-batched)
fetch("/data").then(() => {
  setLoading(false);
  setData(result);    // single batch → one commit
});
```

### Layout Thrashing

Avoid repeated forced synchronous reflows. Batch DOM reads before writes:

```jsx
// BAD — read → write → read → write (thrashing)
const h1 = el.clientHeight;
el.style.height = `${h1 + 10}px`;
const h2 = el2.clientHeight;
el2.style.height = `${h2 + 10}px`;

// GOOD — reads first, then writes
const h1 = el.clientHeight;
const h2 = el2.clientHeight;
el.style.height = `${h1 + 10}px`;
el2.style.height = `${h2 + 10}px`;
```

### Passive Events

Use `{ passive: true }` for scroll/touch listeners to prevent the browser from waiting for `preventDefault`:

```jsx
useEffect(() => {
  window.addEventListener("touchstart", handler, { passive: true });
  window.addEventListener("scroll", handler, { passive: true });
  return () => {
    window.removeEventListener("touchstart", handler);
    window.removeEventListener("scroll", handler);
  };
}, []);
```

### Web Workers (comlink)

Offload heavy computation off the main thread:

```jsx
// worker.js
import { expose } from "comlink";
export const heavyCompute = (data) => data.map(expensiveOp);
expose({ heavyCompute });

// main.js
import { wrap } from "comlink";
const worker = wrap(new Worker("./worker.js"));
const result = await worker.heavyCompute(largeArray);
```

## 10. Performance Monitoring

### Core Web Vitals

```jsx
import { onCLS, onFID, onLCP, onINP } from "web-vitals";

function reportVitals(metric) {
  // Send to analytics
  navigator.sendBeacon("/analytics", JSON.stringify(metric));
}

onCLS(reportVitals); // Cumulative Layout Shift — < 0.1
onFID(reportVitals); // First Input Delay — < 100ms (replaced by INP)
onLCP(reportVitals); // Largest Contentful Paint — < 2.5s
onINP(reportVitals); // Interaction to Next Paint — < 200ms
```

### PerformanceObserver API

```jsx
const obs = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (entry.entryType === "longtask") {
      console.warn("Long task:", entry.duration, "ms");
    }
  }
});
obs.observe({ entryTypes: ["longtask", "measure", "navigation"] });
```

### Lighthouse & Perf Budgets

```json
{
  "ci": {
    "assertions": {
      "largest-contentful-paint": ["warn", { "maxNumericValue": 2500 }],
      "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }],
      "total-blocking-time": ["error", { "maxNumericValue": 200 }],
      "unused-javascript": ["warn", { "maxNumericValue": 50 }]
    }
  }
}
```

### Bundle Analysis

```bash
# webpack
ANALYZE=true webpack --mode production

# vite
vite build --mode analyze

# Import cost (VS Code extension) — shows gzip size inline
```

Track bundle size per commit with `bundlesize` or `size-limit` in CI.

## 11. Summary Checklist

| Concern | Technique | Key API |
|---------|-----------|---------|
| Re-renders | React.memo + useMemo + useCallback | `React.memo`, `useMemo`, `useCallback` |
| Bundle size | Lazy loading + code splitting | `React.lazy`, `Suspense` |
| Dead code | Tree shaking | ES modules, `sideEffects: false` |
| Large lists | Virtualization | `react-window`, `react-virtuoso` |
| Images | Optimization + lazy loading | `next/image`, `loading="lazy"` |
| Fonts | Self-host + subset | `next/font`, `font-display: swap` |
| Context | Split or atom state | `zustand`, `jotai`, split contexts |
| Heavy CPU | Web Workers | `comlink`, `Worker` |
| Monitoring | Web Vitals + PerformanceObserver | `web-vitals`, `PerformanceObserver` |

---

## Related

- [Networking](../../11-networking/) — HTTP, performance, optimization
- [Security](../../13-security/) — CORS, authentication, XSS prevention
- [Backend](../../03-backend/) — API design and contracts
- [Performance Engineering](../../18-performance-engineering/) — Browser rendering
- [Testing](../../19-testing/) — E2E and component testing


## Practical Example

See code examples above for practical usage patterns.