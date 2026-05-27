# 08: Custom Hooks & Patterns — Deep Reference

> **Scope**: Custom hooks, hook composition, testing hooks, HOCs vs render props, compound components, polymorphic components, controlled/uncontrolled, forwardRef, generic components

## 1. Custom Hooks Fundamentals

Custom hooks are functions that use built-in hooks and share stateful logic between components. They must start with `use`.

```jsx
function useWindowSize() {
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    function handleResize() {
      setSize({ width: window.innerWidth, height: window.innerHeight });
    }
    window.addEventListener("resize", handleResize);
    handleResize();
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return size;
}

// Usage
function Dashboard() {
  const { width, height } = useWindowSize();
  return <div>Window: {width}x{height}</div>;
}
```

## 2. Utility Hooks

### useDebounce / useThrottle

```jsx
function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);

  return debounced;
}

function useThrottle(value, interval = 300) {
  const [throttled, setThrottled] = useState(value);
  const last = useRef(0);

  useEffect(() => {
    const now = Date.now();
    if (now >= last.current + interval) {
      last.current = now;
      setThrottled(value);
    }
  }, [value, interval]);

  return throttled;
}
```

### usePrevious / useToggle / useCounter

```jsx
function usePrevious(value) {
  const ref = useRef();
  useEffect(() => { ref.current = value; }, [value]);
  return ref.current;
}

function useToggle(initial = false) {
  const [on, setOn] = useState(initial);
  const toggle = useCallback(() => setOn((v) => !v), []);
  return [on, toggle];
}

function useCounter(initial = 0, step = 1) {
  const [count, setCount] = useState(initial);
  const increment = useCallback(() => setCount((c) => c + step), [step]);
  const decrement = useCallback(() => setCount((c) => c - step), [step]);
  const reset = useCallback(() => setCount(initial), [initial]);
  return { count, increment, decrement, reset };
}
```

### useInterval / useTimeout

```jsx
function useInterval(callback, delay) {
  const saved = useRef(callback);
  useEffect(() => { saved.current = callback; }, [callback]);

  useEffect(() => {
    if (delay === null) return;
    const id = setInterval(() => saved.current(), delay);
    return () => clearInterval(id);
  }, [delay]);
}

function useTimeout(callback, delay) {
  const saved = useRef(callback);
  useEffect(() => { saved.current = callback; }, [callback]);

  useEffect(() => {
    if (delay === null) return;
    const id = setTimeout(() => saved.current(), delay);
    return () => clearTimeout(id);
  }, [delay]);
}
```

## 3. Browser & DOM Hooks

### useIntersectionObserver / useMediaQuery

```jsx
function useIntersectionObserver(ref, options = {}) {
  const [entry, setEntry] = useState(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([e]) => setEntry(e),
      { threshold: 0.1, ...options }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [ref, options]);

  return entry;
}

function useMediaQuery(query) {
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches);

  useEffect(() => {
    const mq = window.matchMedia(query);
    const handler = (e) => setMatches(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, [query]);

  return matches;
}
```

### useOnlineStatus / useClipboard / useIdleTimer

```jsx
function useOnlineStatus() {
  const [online, setOnline] = useState(navigator.onLine);
  useEffect(() => {
    const h = () => setOnline(navigator.onLine);
    window.addEventListener("online", h);
    window.addEventListener("offline", h);
    return () => {
      window.removeEventListener("online", h);
      window.removeEventListener("offline", h);
    };
  }, []);
  return online;
}

function useClipboard() {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }, []);

  return { copy, copied };
}

```

**Edge cases**: useMediaQuery must handle SSR by returning a default (usually false). useOnlineStatus falls back to `navigator.onLine`. useClipboard includes a fallback using `document.execCommand("copy")` for older browsers.

### useKeyPress / useEventListener / useLockBodyScroll

```jsx
function useKeyPress(targetKey) {
  const [pressed, setPressed] = useState(false);

  useEffect(() => {
    const down = ({ key }) => key === targetKey && setPressed(true);
    const up = ({ key }) => key === targetKey && setPressed(false);
    window.addEventListener("keydown", down);
    window.addEventListener("keyup", up);
    return () => {
      window.removeEventListener("keydown", down);
      window.removeEventListener("keyup", up);
    };
  }, [targetKey]);

  return pressed;
}

function useEventListener(event, handler, target = window) {
  useEffect(() => {
    const el = target?.current ?? target;
    if (!el) return;
    el.addEventListener(event, handler);
    return () => el.removeEventListener(event, handler);
  }, [event, handler, target]);
}

function useLockBodyScroll(locked = true) {
  useEffect(() => {
    if (!locked) return;
    const original = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = original; };
  }, [locked]);
}
```

## 4. Storage Hooks

### useLocalStorage / useDarkMode / useCookie

```jsx
function useLocalStorage(key, initial) {
  const [value, setValue] = useState(() => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : initial;
    } catch { return initial; }
  });

  useEffect(() => {
    try { localStorage.setItem(key, JSON.stringify(value)); }
    catch { /* quota exceeded */ }
  }, [key, value]);

  return [value, setValue];
}

function useDarkMode() {
  const [dark, setDark] = useLocalStorage("dark-mode",
    window.matchMedia("(prefers-color-scheme: dark)").matches
  );

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  return [dark, setDark];
}

```

## 5. Async Hooks

```jsx
function useAsync(asyncFn, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null });

  const execute = useCallback(async () => {
    setState(s => ({ ...s, loading: true, error: null }));
    try {
      const data = await asyncFn();
      setState({ data, loading: false, error: null });
      return data;
    } catch (error) {
      setState({ data: null, loading: false, error });
      throw error;
    }
  }, deps);

  useEffect(() => { execute(); }, [execute]);

  return { ...state, execute };
}
```

## 6. State Management Patterns

### useReducer + Context

```jsx
const AuthContext = createContext();

function authReducer(state, action) {
  switch (action.type) {
    case "LOGIN":
      return { ...state, user: action.payload, loading: false };
    case "LOGOUT":
      return { ...state, user: null, loading: false };
    default:
      return state;
  }
}

function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, {
    user: null,
    loading: true,
  });

  const login = useCallback(async (credentials) => {
    const user = await api.login(credentials);
    dispatch({ type: "LOGIN", payload: user });
  }, []);

  const logout = useCallback(async () => {
    await api.logout();
    dispatch({ type: "LOGOUT" });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
}
```

## 8. Controlled / Uncontrolled Pattern

```jsx
function useControllableState({ value: controlled, defaultValue, onChange }) {
  const [internal, setInternal] = useState(defaultValue);
  const isControlled = controlled !== undefined;

  const set = useCallback(
    (next) => {
      if (!isControlled) setInternal(next);
      onChange?.(next);
    },
    [isControlled, onChange]
  );

  return [isControlled ? controlled : internal, set];
}

// Usage — Input that works both ways
function Input({ value, defaultValue, onChange }) {
  const [val, setVal] = useControllableState({
    value,
    defaultValue: defaultValue ?? "",
    onChange,
  });
  return <input value={val} onChange={(e) => setVal(e.target.value)} />;
}
```

## 9. Generic Components & forwardRef

```jsx
type PolymorphicProps<
  T extends React.ElementType,
  P = {}
> = { as?: T } & P & Omit<React.ComponentPropsWithoutRef<T>, keyof P>;

function Box<T extends React.ElementType = "div">({
  as,
  children,
  ...props
}: PolymorphicProps<T>) {
  const Component = as || "div";
  return <Component {...props}>{children}</Component>;
}

// forwardRef with generics
const Select = React.forwardRef(function Select<T extends string>(
  { options, ...props }: { options: T[] } & React.SelectHTMLAttributes<HTMLSelectElement>,
  ref: React.Ref<HTMLSelectElement>
) {
  return (
    <select ref={ref} {...props}>
      {options.map((opt) => (
        <option key={opt} value={opt}>{opt}</option>
      ))}
    </select>
  );
});
```

## 10. Compound Components

```jsx
const TabsContext = createContext();

function Tabs({ defaultIndex = 0, children }) {
  const [active, setActive] = useState(defaultIndex);
  return (
    <TabsContext.Provider value={{ active, setActive }}>
      {children}
    </TabsContext.Provider>
  );
}

function Tab({ index, children }) {
  const { active, setActive } = useContext(TabsContext);
  return (
    <button
      role="tab"
      aria-selected={active === index}
      onClick={() => setActive(index)}
    >
      {children}
    </button>
  );
}

function TabPanel({ index, children }) {
  const { active } = useContext(TabsContext);
  return active === index ? <div role="tabpanel">{children}</div> : null;
}

Tabs.Tab = Tab;
Tabs.Panel = TabPanel;

// Usage
<Tabs>
  <Tabs.Tab index={0}>One</Tabs.Tab>
  <Tabs.Tab index={1}>Two</Tabs.Tab>
  <Tabs.Panel index={0}>Content One</Tabs.Panel>
  <Tabs.Panel index={1}>Content Two</Tabs.Panel>
</Tabs>;
```

## 11. Testing Hooks

```jsx
import { renderHook, act, waitFor } from "@testing-library/react";

test("useCounter", () => {
  const { result } = renderHook(() => useCounter(0, 2));

  expect(result.current.count).toBe(0);

  act(() => result.current.increment());
  expect(result.current.count).toBe(2);

  act(() => result.current.reset());
  expect(result.current.count).toBe(0);
});

test("useDebounce", async () => {
  jest.useFakeTimers();
  const { result, rerender } = renderHook(
    ({ val }) => useDebounce(val, 500),
    { initialProps: { val: "hello" } }
  );

  expect(result.current).toBe("hello");
  rerender({ val: "world" });
  expect(result.current).toBe("hello"); // not updated yet

  act(() => jest.advanceTimersByTime(500));
  expect(result.current).toBe("world");

  jest.useRealTimers();
});


```

**Wrapper pattern**: Pass a `wrapper` option to renderHook for context providers:
```jsx
const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
const { result } = renderHook(() => useAuth(), { wrapper });
```

## 12. Hooks Rules

- **Only call hooks at the top level** — never inside conditions, loops, or nested functions.
- **Only call hooks from React function components or custom hooks**.
- **Dependency arrays must be exhaustive** — use `eslint-plugin-react-hooks` (`exhaustive-deps`).
- **Stale closures** — dependency mismatches cause stale values; include all reactive values.
- **Conditional effects** — use `if (condition)` inside the effect, not around the hook call.
- **Cleanup** — every subscription, timer, or event listener must be cleaned up.


