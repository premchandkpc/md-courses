# Compound Components Pattern: Building Flexible Component APIs

**Level:** Intermediate-Advanced | **Time:** 45 mins | **Interview:** 🔥 Critical

---

## Overview

Compound components = components that work together, sharing implicit state. Instead of a monolithic component with 20 props, you compose smaller pieces that communicate via Context. This pattern powers UI libraries: `<Select><Select.Option><Select.Option.Group>`. Building with this pattern teaches you how real libraries (Headless UI, Radix) work.

**Why this matters:**
- Interview prep: "How would you design a flexible `<Tabs>` component?"
- Real-world: Every production UI library uses this
- Flexibility: Same component API works for 10 different use cases (without new props)
- Maintainability: Logic split across components (easier to reason about)

---

## 1. The Problem: Rigid Component APIs

### Monolithic Approach (Inflexible)

```javascript
// ❌ BAD: Every feature is a prop
function Select({
  options,
  value,
  onChange,
  disabled = false,
  searchable = false,
  clearable = false,
  multi = false,
  groupBy = null,
  maxHeight = 300,
  onOpen,
  onClose,
  renderOption,
  renderValue,
  // ... 15 more props
}) {
  // 400 lines of logic (DOM structure, state, handlers hardcoded)
  return (
    <div className="select">
      <input value={value} onChange={onChange} />
      <div className="options">
        {options.map(opt => (
          <div key={opt.id}>{opt.label}</div>
        ))}
      </div>
    </div>
  );
}

// Usage: Limited structure
<Select
  options={options}
  value={value}
  onChange={onChange}
  renderOption={(opt) => <strong>{opt.label}</strong>}
/>
```

**Problems:**
- 50+ props (API explosion)
- Hard to extend (new use case = new prop)
- Logic tightly coupled (can't separate concerns)
- Large bundle (all features included, used or not)

---

### Compound Component Approach (Flexible)

```javascript
// ✅ GOOD: Flexible composition
<Select value={value} onChange={onChange}>
  <Select.Input placeholder="Pick option..." />
  <Select.Options>
    <Select.Group label="Fruits">
      <Select.Option value="apple">🍎 Apple</Select.Option>
      <Select.Option value="banana">🍌 Banana</Select.Option>
    </Select.Group>
    <Select.Group label="Vegetables">
      <Select.Option value="carrot">🥕 Carrot</Select.Option>
    </Select.Group>
  </Select.Options>
</Select>
```

**Benefits:**
- Minimal props (only what you use)
- Composable (swap components, reorder, customize)
- Extensible (add new behavior without modifying component)
- Smaller bundle (tree-shake unused subcomponents)

---

## 2. Building a Compound Component: `<Tabs>`

### Step 1: Context for Shared State

```javascript
import React, { createContext, useContext, useState } from 'react';

const TabsContext = createContext();

function Tabs({ value, onValueChange, children }) {
  const [internalValue, setInternalValue] = useState(value || null);
  
  const activeValue = value !== undefined ? value : internalValue;
  
  const handleValueChange = (newValue) => {
    if (value === undefined) {
      setInternalValue(newValue);
    }
    onValueChange?.(newValue);
  };

  return (
    <TabsContext.Provider value={{ activeValue, onValueChange: handleValueChange }}>
      <div className="tabs">{children}</div>
    </TabsContext.Provider>
  );
}

// Hook to access context (other components use this)
function useTabsContext() {
  const context = useContext(TabsContext);
  if (!context) {
    throw new Error('Tabs.* must be used inside <Tabs>');
  }
  return context;
}
```

---

### Step 2: Tab List Component

```javascript
function TabsList({ children }) {
  return (
    <div className="tabs-list" role="tablist">
      {children}
    </div>
  );
}

function TabsTrigger({ value, children }) {
  const { activeValue, onValueChange } = useTabsContext();
  const isActive = value === activeValue;

  return (
    <button
      role="tab"
      aria-selected={isActive}
      onClick={() => onValueChange(value)}
      className={`tabs-trigger ${isActive ? 'active' : ''}`}
    >
      {children}
    </button>
  );
}
```

---

### Step 3: Tab Content Component

```javascript
function TabsContent({ value, children }) {
  const { activeValue } = useTabsContext();

  if (value !== activeValue) {
    return null; // Hidden when not active
  }

  return (
    <div className="tabs-content" role="tabpanel">
      {children}
    </div>
  );
}

// Attach subcomponents to main component
Tabs.List = TabsList;
Tabs.Trigger = TabsTrigger;
Tabs.Content = TabsContent;

// Note: This pattern uses Context for state sharing (see [Redux/Zustand Patterns](../../05-state-management/02-redux-zustand-patterns.md)
// for comparison when compound components need global state or [React Fiber](../../02-react-internals/02-fiber-reconciliation-engine.md) for
// understanding how context changes trigger re-renders).
```

---

### Step 4: Usage

```javascript
function App() {
  const [activeTab, setActiveTab] = useState('profile');

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab}>
      <Tabs.List>
        <Tabs.Trigger value="profile">Profile</Tabs.Trigger>
        <Tabs.Trigger value="settings">Settings</Tabs.Trigger>
        <Tabs.Trigger value="billing">Billing</Tabs.Trigger>
      </Tabs.List>

      <Tabs.Content value="profile">
        <h2>Profile Information</h2>
        {/* Profile content */}
      </Tabs.Content>

      <Tabs.Content value="settings">
        <h2>Settings</h2>
        {/* Settings content */}
      </Tabs.Content>

      <Tabs.Content value="billing">
        <h2>Billing & Plan</h2>
        {/* Billing content */}
      </Tabs.Content>
    </Tabs>
  );
}
```

---

## 3. Real-World Example: Dropdown Menu

```javascript
// Context: shared state (open/closed, selected)
const DropdownContext = createContext();

function Dropdown({ children, onSelect }) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedValue, setSelectedValue] = useState(null);

  const handleSelect = (value) => {
    setSelectedValue(value);
    setIsOpen(false);
    onSelect?.(value);
  };

  return (
    <DropdownContext.Provider value={{ isOpen, setIsOpen, selectedValue, handleSelect }}>
      <div className="dropdown">{children}</div>
    </DropdownContext.Provider>
  );
}

// Trigger: button to open/close
function DropdownTrigger({ children }) {
  const { isOpen, setIsOpen } = useContext(DropdownContext);

  return (
    <button
      onClick={() => setIsOpen(!isOpen)}
      aria-haspopup="menu"
      aria-expanded={isOpen}
    >
      {children}
    </button>
  );
}

// Menu: list of options (only shown if open)
function DropdownMenu({ children }) {
  const { isOpen } = useContext(DropdownContext);

  if (!isOpen) return null;

  return (
    <ul className="dropdown-menu" role="menu">
      {children}
    </ul>
  );
}

// Item: individual option
function DropdownItem({ value, children }) {
  const { handleSelect } = useContext(DropdownContext);

  return (
    <li
      className="dropdown-item"
      role="menuitem"
      onClick={() => handleSelect(value)}
    >
      {children}
    </li>
  );
}

// Group separator (optional)
function DropdownGroup({ label, children }) {
  return (
    <li className="dropdown-group">
      <span className="dropdown-group-label">{label}</span>
      <ul>{children}</ul>
    </li>
  );
}

Dropdown.Trigger = DropdownTrigger;
Dropdown.Menu = DropdownMenu;
Dropdown.Item = DropdownItem;
Dropdown.Group = DropdownGroup;

// Usage: Flexible and clean
<Dropdown onSelect={(value) => console.log('Selected:', value)}>
  <Dropdown.Trigger>
    Actions <ChevronDown />
  </Dropdown.Trigger>
  
  <Dropdown.Menu>
    <Dropdown.Group label="Edit">
      <Dropdown.Item value="edit">Edit item</Dropdown.Item>
      <Dropdown.Item value="duplicate">Duplicate</Dropdown.Item>
    </Dropdown.Group>
    
    <Dropdown.Group label="Danger">
      <Dropdown.Item value="delete">Delete (irreversible)</Dropdown.Item>
    </Dropdown.Group>
  </Dropdown.Menu>
</Dropdown>
```

---

## 4. Advanced Patterns

### Pattern 1: Render Props Alternative

If you don't like context, use render props:

```javascript
function Tabs({ value, onValueChange, children }) {
  // Pass state down to children as function argument
  return children({ activeValue: value, onValueChange });
}

// Usage (less common now, but valid)
<Tabs value={tab} onValueChange={setTab}>
  {({ activeValue, onValueChange }) => (
    <>
      <Tabs.List activeValue={activeValue} onValueChange={onValueChange} />
      <Tabs.Content activeValue={activeValue} />
    </>
  )}
</Tabs>
```

---

### Pattern 2: Controlled vs Uncontrolled

Support both:

```javascript
function Tabs({ value, onValueChange, defaultValue = null, children }) {
  const [internalValue, setInternalValue] = useState(defaultValue);

  // Controlled: value prop provided
  const isControlled = value !== undefined;
  const activeValue = isControlled ? value : internalValue;

  const handleChange = (newValue) => {
    if (!isControlled) {
      setInternalValue(newValue);
    }
    onValueChange?.(newValue);
  };

  return (
    <TabsContext.Provider value={{ activeValue, onValueChange: handleChange }}>
      <div>{children}</div>
    </TabsContext.Provider>
  );
}

// Usage 1: Controlled (parent manages state)
const [tab, setTab] = useState('profile');
<Tabs value={tab} onValueChange={setTab}>...</Tabs>

// Usage 2: Uncontrolled (component manages itself)
<Tabs defaultValue="profile">...</Tabs>
```

---

### Pattern 3: Custom Hooks for Consumers

Allow consumers to access context hooks:

```javascript
// Hook: Expose context to anyone
export function useTabs() {
  const context = useContext(TabsContext);
  if (!context) {
    throw new Error('useTabs must be inside <Tabs>');
  }
  return context;
}

// Custom component using hook
function TabIndicator() {
  const { activeValue, triggers } = useTabs();
  
  return (
    <div className="indicator">
      Active: {activeValue}
    </div>
  );
}

// Usage: Can embed custom component anywhere inside <Tabs>
<Tabs>
  <Tabs.List>...</Tabs.List>
  <TabIndicator /> {/* Uses hook to access context */}
  <Tabs.Content>...</Tabs.Content>
</Tabs>
```

---

## 5. Performance Optimization

### Problem: Re-renders on Context Change

Every subcomponent re-renders when context changes (even if it doesn't use that value).

```javascript
// ❌ PROBLEM: All children re-render
function Tabs({ value, onValueChange, children }) {
  // Context changes every time activeValue changes
  return (
    <TabsContext.Provider value={{ activeValue: value, onValueChange }}>
      {children} {/* All children re-render */}
    </TabsContext.Provider>
  );
}
```

### Solution: Memoization

```javascript
// ✅ GOOD: Memoize context value
function Tabs({ value, onValueChange, children }) {
  const contextValue = useMemo(
    () => ({ activeValue: value, onValueChange }),
    [value, onValueChange]
  );

  return (
    <TabsContext.Provider value={contextValue}>
      {children}
    </TabsContext.Provider>
  );
}

// ✅ ALSO GOOD: Memoize subcomponents
const TabsTrigger = React.memo(function TabsTrigger({ value, children }) {
  const { activeValue, onValueChange } = useTabsContext();
  // Only re-renders if value or children change
  return (
    <button
      onClick={() => onValueChange(value)}
      className={value === activeValue ? 'active' : ''}
    >
      {children}
    </button>
  );
});
```

---

## 6. Accessibility (a11y)

Compound components give you flexibility to implement a11y correctly:

```javascript
function TabsList({ children }) {
  return (
    <div
      className="tabs-list"
      role="tablist" // Semantic: screen reader announces as tab list
      onKeyDown={(e) => {
        // Arrow keys: move between tabs
        if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
          e.preventDefault();
          // Handle arrow navigation
        }
      }}
    >
      {children}
    </div>
  );
}

function TabsTrigger({ value, children }) {
  const { activeValue, onValueChange } = useTabsContext();
  const isActive = value === activeValue;

  return (
    <button
      role="tab"
      aria-selected={isActive}
      aria-controls={`panel-${value}`}
      id={`tab-${value}`}
      tabIndex={isActive ? 0 : -1} // Only active tab in tab order
      onClick={() => onValueChange(value)}
    >
      {children}
    </button>
  );
}

function TabsContent({ value, children }) {
  const { activeValue } = useTabsContext();

  return (
    <div
      role="tabpanel"
      id={`panel-${value}`}
      aria-labelledby={`tab-${value}`}
      hidden={value !== activeValue}
    >
      {children}
    </div>
  );
}
```

---

## 7. Common Mistakes

### Mistake 1: Over-Splitting Components

```javascript
// ❌ BAD: Too many tiny components (hard to use)
<Select>
  <SelectWrapper>
    <SelectTriggerWrapper>
      <SelectTrigger>
        <SelectValue />
      </SelectTrigger>
    </SelectTriggerWrapper>
  </SelectWrapper>
</Select>

// ✅ GOOD: Right level of granularity
<Select>
  <Select.Trigger />
  <Select.Content>
    <Select.Item value="a">Item A</Select.Item>
  </Select.Content>
</Select>
```

---

### Mistake 2: Not Memoizing Context

```javascript
// ❌ BAD: Context value created every render
function Tabs({ children }) {
  return (
    <TabsContext.Provider value={{ activeValue, onValueChange }}>
      {children} {/* All children re-render */}
    </TabsContext.Provider>
  );
}

// ✅ GOOD: Memoize value
function Tabs({ children }) {
  const value = useMemo(() => ({ activeValue, onValueChange }), [activeValue, onValueChange]);
  return (
    <TabsContext.Provider value={value}>
      {children}
    </TabsContext.Provider>
  );
}
```

---

### Mistake 3: Forgetting to Export Subcomponents

```javascript
// ❌ BAD: Users can't import subcomponents
function Tabs({ children }) { ... }
function TabsContent({ children }) { ... } // Not exported!
export default Tabs;

// Usage fails: Tabs.Content is undefined
<Tabs.Content /> // Error!

// ✅ GOOD: Attach and export
Tabs.Content = TabsContent;
export default Tabs;

// Usage works
<Tabs.Content />
```

---

## Interview Prep Questions

1. **"Design a `<Tabs>` component. How would you structure it?"**
   - Answer: Use Context for shared state (activeTab). Subcomponents: `<Tabs.List>`, `<Tabs.Trigger>`, `<Tabs.Content>`. Context holds active value + setter, triggers dispatch actions, content conditionally renders.

2. **"What's an advantage of compound components over props?"**
   - Answer: Flexibility. Monolithic component has 50 props. Compound components let users compose only what they need. Less bundle, cleaner API, easier to extend.

3. **"How do you handle accessibility in compound components?"**
   - Answer: Use semantic roles (role="tab"), aria attributes (aria-selected, aria-controls), keyboard navigation (arrow keys), and focus management.

4. **"What happens if context value changes every render? How do you fix it?"**
   - Answer: All children re-render unnecessarily. Fix: Memoize the context value with `useMemo` so it only changes when dependencies change.

5. **"Can compound components work with prop drilling, or must they use Context?"**
   - Answer: Could use prop drilling (pass value through all children), but Context is cleaner. Render props is an alternative. Context scales better (5+ levels of nesting).

---

## See Also

### Phase 7.1 Related Topics

- [WCAG Accessibility](../../16-accessibility/02-wcag-patterns-and-compliance.md) — Accessible compound components
- [Redux/Zustand Patterns](../../05-state-management/02-redux-zustand-patterns.md) — State in compound components
- [React Fiber](../../02-react-internals/02-fiber-reconciliation-engine.md) — Understanding re-renders

### Additional Resources

- Headless UI: Compound component implementation (React/Vue/etc)
- Radix UI: Advanced compound components with a11y
- Recharts: Charts built with compound component pattern
- Framer Motion: Animation with compound components
- Material-UI: Both monolithic props AND compound approaches
