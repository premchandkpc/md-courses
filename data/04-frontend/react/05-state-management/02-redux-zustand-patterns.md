# Redux & Zustand: Patterns, Optimization & When to Use

**Level:** Intermediate-Advanced | **Time:** 50 mins | **Interview:** 🔥 Critical

---

## Overview

Redux and Zustand solve the same problem — managing global state without prop drilling. Redux dominates in large teams (predictable, time-travel debugging, middleware). Zustand wins in smaller codebases (minimal boilerplate, great DX). This guide covers both, with patterns to avoid common pitfalls.

**Why this matters:**
- Interview question: "Redux vs Zustand — when would you choose each?"
- Production decision: Wrong choice = painful refactoring later
- Performance: Bad state design causes 100s of unnecessary re-renders

---

## Redux: The Deep Dive

### 1. Store Architecture

Redux = single source of truth (immutable state tree).

```javascript
// ❌ BAD: Large monolithic reducer
const initialState = {
  user: null,
  cart: [],
  filters: {},
  notifications: [],
  loading: false,
  errors: []
};

function appReducer(state = initialState, action) {
  switch(action.type) {
    case 'SET_USER': return { ...state, user: action.payload };
    case 'ADD_TO_CART': return { ...state, cart: [...state.cart, action.payload] };
    // ... 50 more cases
    default: return state;
  }
}
```

**Problem:** Single reducer = hard to test, maintain, extend. Bugs in one domain affect entire state.

```javascript
// ✅ GOOD: Domain-based slices (modern Redux Toolkit pattern)
import { createSlice, configureStore } from '@reduxjs/toolkit';

const userSlice = createSlice({
  name: 'user',
  initialState: null,
  reducers: {
    setUser: (state, action) => action.payload,
    logout: () => null
  }
});

const cartSlice = createSlice({
  name: 'cart',
  initialState: [],
  reducers: {
    addItem: (state, action) => {
      state.push(action.payload); // Immer handles mutation
    },
    removeItem: (state, action) => {
      return state.filter(item => item.id !== action.payload);
    }
  }
});

const store = configureStore({
  reducer: {
    user: userSlice.reducer,
    cart: cartSlice.reducer
  }
});

export const { setUser, logout } = userSlice.actions;
export const { addItem, removeItem } = cartSlice.actions;
```

**Why this works:** Each domain isolated, Immer handles immutability, auto-generates action creators.

---

### 2. Selectors: Memoization is Critical

Redux connects cause unnecessary re-renders if selectors don't memoize.

```javascript
// ❌ BAD: New object every render
const CartPage = () => {
  const cart = useSelector(state => state.cart); // New array object each time
  return <CartList items={cart} />;
};
// CartList re-renders even if cart hasn't changed (new reference!)

// ✅ GOOD: Memoized selector
import { createSelector } from '@reduxjs/toolkit';

const selectCart = state => state.cart;
const selectCartCount = createSelector(
  selectCart,
  (cart) => cart.length
);

const CartPage = () => {
  const count = useSelector(selectCartCount); // Same object reference if cart unchanged
  return <CartList count={count} />;
};

// ✅ ALSO GOOD: Structural sharing (RC >= 8)
const CartPage = () => {
  const cart = useSelector(state => state.cart, shallowEqual);
  return <CartList items={cart} />;
};
```

**Why it matters:** Without memoization, every store update triggers re-render (even if this component's data unchanged). Memoized selectors prevent this.

---

### 3. Async Thunks: Handling Side Effects

Redux doesn't handle async by default. Thunks intercept actions → run side effects → dispatch new actions.

```javascript
// ❌ BAD: Doing async in component
const UserProfile = () => {
  const user = useSelector(state => state.user);
  
  useEffect(() => {
    // Mixing component + async logic
    fetch('/api/user')
      .then(res => res.json())
      .then(data => dispatch(setUser(data)))
      .catch(err => dispatch(setError(err)));
  }, [dispatch]);
  
  return <div>{user.name}</div>;
};

// ✅ GOOD: Thunk encapsulates async
import { createAsyncThunk } from '@reduxjs/toolkit';

export const fetchUser = createAsyncThunk(
  'user/fetchUser',
  async (userId, { rejectWithValue }) => {
    try {
      const res = await fetch(`/api/users/${userId}`);
      if (!res.ok) throw new Error('Failed to fetch');
      return res.json();
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

const userSlice = createSlice({
  name: 'user',
  initialState: { data: null, loading: false, error: null },
  extraReducers: (builder) => {
    builder
      .addCase(fetchUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUser.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(fetchUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  }
});

// Component stays clean
const UserProfile = ({ userId }) => {
  const dispatch = useDispatch();
  const { data, loading, error } = useSelector(state => state.user);
  
  useEffect(() => {
    dispatch(fetchUser(userId));
  }, [userId, dispatch]);
  
  if (loading) return <Spinner />;
  if (error) return <Error msg={error} />;
  return <div>{data.name}</div>;
};
```

**Why it matters:** Thunks keep async logic testable, reusable, separate from components.

---

### 4. Real Production Pattern: Cart with Optimistic Updates

```javascript
const cartSlice = createSlice({
  name: 'cart',
  initialState: {
    items: [],
    syncing: false,
    lastSyncError: null
  },
  reducers: {
    // Optimistic: update locally immediately
    addItemOptimistic: (state, action) => {
      state.items.push({
        ...action.payload,
        id: `temp-${Date.now()}`
      });
    },
    // Rollback if sync fails
    rollbackAdd: (state, action) => {
      state.items = state.items.filter(item => item.id !== action.payload);
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(syncCart.pending, (state) => {
        state.syncing = true;
        state.lastSyncError = null;
      })
      .addCase(syncCart.fulfilled, (state, action) => {
        state.syncing = false;
        state.items = action.payload; // Server canonical state
      })
      .addCase(syncCart.rejected, (state, action) => {
        state.syncing = false;
        state.lastSyncError = action.payload;
      });
  }
});

export const syncCart = createAsyncThunk(
  'cart/sync',
  async (_, { getState, rejectWithValue }) => {
    try {
      const { items } = getState().cart;
      const res = await fetch('/api/cart', {
        method: 'POST',
        body: JSON.stringify({ items })
      });
      if (!res.ok) throw new Error('Sync failed');
      return res.json(); // Server returns canonical cart
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

// Component: add to cart with optimistic update
const AddToCart = ({ product }) => {
  const dispatch = useDispatch();
  const handleClick = () => {
    // 1. Update locally (user sees immediate feedback)
    dispatch(addItemOptimistic(product));
    // 2. Sync with server
    dispatch(syncCart())
      .unwrap()
      .catch(() => {
        // Rollback if sync fails
        dispatch(rollbackAdd(`temp-${Date.now()}`));
      });
  };
  return <button onClick={handleClick}>Add to Cart</button>;
};
```

**Interview tip:** "Optimistic updates improve perceived performance — user sees change instantly, server confirms/rolls back async."

---

## Zustand: The Lightweight Alternative

### 1. Basic Store Setup

Zustand: minimal, no boilerplate, direct state mutation syntax (via Immer under hood).

```javascript
// ❌ BAD: Plain React useState for global state
const [user, setUser] = useState(null);
// Problem: useState is component-scoped, requires Context + Provider wrapping all children

// ✅ GOOD: Zustand store
import { create } from 'zustand';

const useUserStore = create((set) => ({
  user: null,
  login: (userData) => set({ user: userData }),
  logout: () => set({ user: null }),
  updateProfile: (changes) =>
    set((state) => ({
      user: { ...state.user, ...changes }
    }))
}));

// Use anywhere (no Provider needed)
const UserCard = () => {
  const { user, logout } = useUserStore();
  return (
    <div>
      {user?.name} <button onClick={logout}>Logout</button>
    </div>
  );
};
```

**Why Zustand:** No Provider boilerplate, smaller bundle (2.9KB vs Redux 70KB), great DX.

---

### 2. Selector Optimization (Prevent Re-renders)

```javascript
// ❌ BAD: Entire state subscribed
const { user, cart, filters } = useUserStore();
// Component re-renders if ANY field changes (user, cart, filters)

// ✅ GOOD: Subscribe to specific fields
const user = useUserStore((state) => state.user);
const cart = useUserStore((state) => state.cart);

// ✅ EVEN BETTER: Object equality check
const { user, filters } = useUserStore(
  (state) => ({ user: state.user, filters: state.filters }),
  (prev, next) => prev.user === next.user && prev.filters === next.filters
);
```

---

### 3. Async Actions with Zustand

```javascript
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';

const useCartStore = create(
  immer((set, get) => ({
    items: [],
    loading: false,
    error: null,
    
    // Sync action
    addItem: (item) => {
      set((state) => {
        state.items.push(item);
      });
    },
    
    // Async action
    fetchCart: async () => {
      set((state) => {
        state.loading = true;
        state.error = null;
      });
      
      try {
        const res = await fetch('/api/cart');
        const data = await res.json();
        set((state) => {
          state.items = data;
          state.loading = false;
        });
      } catch (err) {
        set((state) => {
          state.error = err.message;
          state.loading = false;
        });
      }
    },
    
    // Access other state in actions
    applyDiscount: async (code) => {
      const { items } = get();
      const res = await fetch('/api/discount', {
        method: 'POST',
        body: JSON.stringify({ items, code })
      });
      const discounted = await res.json();
      set((state) => {
        state.items = discounted;
      });
    }
  }))
);

// Component
const Cart = () => {
  const { items, fetchCart } = useCartStore();
  
  useEffect(() => {
    fetchCart();
  }, [fetchCart]);
  
  return <CartList items={items} />;
};
```

---

### 4. Real Production Pattern: Multi-tab Sync

```javascript
const useSharedStore = create(
  persist(
    (set) => ({
      theme: 'light',
      setTheme: (theme) => set({ theme })
    }),
    {
      name: 'app-state', // localStorage key
      storage: localStorage
    }
  )
);

// Automatically syncs across browser tabs via storage events
// Open 2 tabs: change theme in tab 1 → tab 2 updates automatically
```

---

## Redux vs Zustand: Decision Matrix

| Factor | Redux | Zustand |
|--------|-------|---------|
| **Bundle size** | 70KB | 2.9KB |
| **Learning curve** | Steep (actions, reducers) | Gentle |
| **DevTools/debugging** | Excellent (time-travel) | Good (DevTools plugin) |
| **Middleware** | Rich (thunks, sagas) | Minimal (custom) |
| **Team scalability** | Large teams (enforced patterns) | Small → medium |
| **Async handling** | Thunks/sagas (verbose) | Built-in async support |
| **Boilerplate** | High | Low |
| **TypeScript** | Great | Great |

**Choose Redux if:**
- Large app (50+ features, 10+ people)
- Complex async workflows (Thunks, Sagas)
- Team needs predictable patterns
- Debugging/time-travel required

**Choose Zustand if:**
- Small-medium app (< 50 features)
- Team values simplicity
- Bundle size matters (mobile)
- Learning curve important

---

## Common Mistakes & Fixes

### Mistake 1: Mutating State Directly in Redux

```javascript
// ❌ BAD: Direct mutation (breaks Redux)
const reducer = (state, action) => {
  state.user.name = action.payload; // Doesn't trigger re-render!
  return state;
};

// ✅ GOOD: Create new object
const reducer = (state, action) => {
  return {
    ...state,
    user: { ...state.user, name: action.payload }
  };
};

// ✅ ALSO GOOD: Redux Toolkit handles this with Immer
const userSlice = createSlice({
  reducers: {
    setName: (state, action) => {
      state.user.name = action.payload; // Immer makes this safe
    }
  }
});
```

**Why it matters:** Redux compares old state === new state. Mutation fails the check → no re-render.

---

### Mistake 2: Subscribing to Entire State in Zustand

```javascript
// ❌ BAD: Re-renders on ANY state change
const Component = () => {
  const store = useUserStore(); // Whole store
  return <div>{store.user.name}</div>;
};

// ✅ GOOD: Subscribe to specific field only
const Component = () => {
  const name = useUserStore((state) => state.user.name);
  return <div>{name}</div>;
};
```

---

### Mistake 3: Putting Server State in Redux/Zustand

```javascript
// ❌ BAD: Duplicating server state
const userSlice = createSlice({
  initialState: { user: null, posts: [], comments: [] },
  // ... manually managing cache invalidation
});

// ✅ GOOD: Use TanStack Query for server state, Redux/Zustand for client state only
import { useQuery } from '@tanstack/react-query';
import { create } from 'zustand';

const useUserStore = create((set) => ({
  selectedUserId: null,
  setSelectedUserId: (id) => set({ selectedUserId: id })
}));

const UserProfile = ({ userId }) => {
  const { data: user } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetch(`/api/users/${userId}`).then(r => r.json())
  });
  return <div>{user.name}</div>;
};
```

**Why it matters:** Server state changes independently. TanStack Query handles caching/invalidation. Redux/Zustand should only manage UI state (filters, modals, selections).

---

## Performance Checklist

- [ ] Use `createSelector` (Redux) or field selectors (Zustand) — avoid entire state subscriptions
- [ ] Memoize component selectors with `reselect` to prevent recalculation
- [ ] Separate server state (TanStack Query) from client state (Redux/Zustand)
- [ ] Slice store by domain (user, cart, UI, etc.) — avoid monolithic reducer
- [ ] Use React.memo + Redux to prevent unnecessary child re-renders
- [ ] Profile with React DevTools Profiler before optimizing (see [React Fiber](../02-react-internals/02-fiber-reconciliation-engine.md) for render phases)
- [ ] For Zustand, use `subscribe` for non-React consumers (services, workers)
- [ ] Avoid store state for frequently-changing values (see [Advanced Form Patterns](../08-forms/02-advanced-form-patterns.md) for form state management)

---

## Interview Prep Questions

1. **"When would you choose Redux over Zustand?"**
   - Answer: Large team, complex async, need time-travel debugging. Zustand for simpler apps.

2. **"Why do Redux selectors need memoization?"**
   - Answer: Without memoization, selector returns new object reference each time → component re-renders. Memoization ensures same reference if data unchanged.

3. **"What's the difference between Redux Thunks and Sagas?"**
   - Answer: Thunks are simple functions that dispatch actions. Sagas are generators (more complex) for complex async flows. Thunks sufficient for 95% of apps.

4. **"How would you sync cart state across browser tabs?"**
   - Answer: Zustand with localStorage + listen to storage events. Redux would use custom middleware.

5. **"Should form state live in Redux/Zustand?"**
   - Answer: No. Forms have frequent updates → performance hit. Use local useState or React Hook Form. Only sync final values to store.

---

## See Also

### Phase 7.1 Related Topics

- [Compound Components](../06-component-architecture/02-compound-components-pattern.md) — State composition patterns
- [Error Boundaries](../35-error-handling/01-error-boundaries-and-patterns.md) — Error state management
- [Advanced Form Patterns](../08-forms/02-advanced-form-patterns.md) — Form state alternatives
- [Vitest + RTL](../15-testing/03-unit-testing-vitest-rtl.md) — Testing Redux/Zustand

### Additional Resources

- Redux Toolkit: Simplified Redux API with Immer
- TanStack Query: Server state management
- Recoil: Atom-based state (alternative to Redux/Zustand)
- Jotai: Primitive-based state management
- XState: Finite state machines for complex UI logic
