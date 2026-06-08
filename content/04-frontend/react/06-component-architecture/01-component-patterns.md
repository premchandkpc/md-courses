---
title: Component Architecture Patterns
topic: 04-frontend
difficulty: intermediate
time: 30m
paths:
  - frontend
---

# Component Architecture Patterns

## WHAT
Patterns for composing React components — from render props to compound components — that determine how components share state, behavior, and appearance.

## WHY
Without intentional architecture: prop drilling, coupled components, impossible-to-reuse logic, 500-line components.

## PATTERN COMPARISON

| Pattern | Coupling | Reuse | Bundle | When |
|---|---|---|---|---|
| **Children prop** | None | Max | 0KB | Layout shells |
| **Render props** | Low | High | 0KB | Shared behavior |
| **HOC** | Medium | Medium | 0KB | Cross-cutting (auth, logging) |
| **Compound** | Tight (parent-child API) | Medium | Varies | Related UI (Tabs, Select) |
| **Slots** | None | High | 0KB | Design systems |

## CHILDREN PROP

```typescript
function Layout({ header, sidebar, children }: {
  header: React.ReactNode;
  sidebar: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="layout">
      <header>{header}</header>
      <aside>{sidebar}</aside>
      <main>{children}</main>
    </div>
  );
}

// Usage — parent controls content, Layout controls structure
<Layout
  header={<Nav />}
  sidebar={<Sidebar />}
>
  <PageContent />
</Layout>
```

## COMPOUND COMPONENTS

```typescript
"use client";
import { createContext, useContext, useState } from 'react';

// Shared state via context (hidden from consumer)
const SelectContext = createContext<{
  value: string;
  onChange: (v: string) => void;
  isOpen: boolean;
  toggle: () => void;
} | null>(null);

function Select({ value, onChange, children }: {
  value: string;
  onChange: (v: string) => void;
  children: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <SelectContext.Provider value={{ value, onChange, isOpen, toggle: () => setIsOpen(o => !o) }}>
      <div className="select">{children}</div>
    </SelectContext.Provider>
  );
}

Select.Trigger = function Trigger({ children }: { children: React.ReactNode }) {
  const ctx = useContext(SelectContext)!;
  return <button onClick={ctx.toggle}>{children || ctx.value}</button>;
};

Select.Options = function Options({ children }: { children: React.ReactNode }) {
  const ctx = useContext(SelectContext)!;
  return ctx.isOpen ? <div className="options">{children}</div> : null;
};

Select.Option = function Option({ value, children }: { value: string; children: React.ReactNode }) {
  const ctx = useContext(SelectContext)!;
  return (
    <div className="option" onClick={() => { ctx.onChange(value); ctx.toggle(); }}>
      {children}
    </div>
  );
};

// Usage — implicit state sharing, no prop drilling
<Select value={lang} onChange={setLang}>
  <Select.Trigger />
  <Select.Options>
    <Select.Option value="js">JavaScript</Select.Option>
    <Select.Option value="ts">TypeScript</Select.Option>
  </Select.Options>
</Select>
```

## SLOTS PATTERN

```typescript
// Design system: Button with variant slots
function Button({ children, leftIcon, rightIcon, variant = 'primary' }: {
  children: React.ReactNode;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  variant?: 'primary' | 'secondary';
}) {
  return (
    <button className={`btn btn-${variant}`}>
      {leftIcon && <span className="btn-icon-left">{leftIcon}</span>}
      {children}
      {rightIcon && <span className="btn-icon-right">{rightIcon}</span>}
    </button>
  );
}

// Usage
<Button leftIcon={<SearchIcon />} rightIcon={<ShortcutBadge>⌘K</ShortcutBadge>}>
  Search
</Button>
```

## RENDER PROPS

```typescript
function MouseTracker({ render }: {
  render: (pos: { x: number; y: number }) => React.ReactNode;
}) {
  const [pos, setPos] = useState({ x: 0, y: 0 });
  useEffect(() => {
    const handler = (e: MouseEvent) => setPos({ x: e.clientX, y: e.clientY });
    window.addEventListener('mousemove', handler);
    return () => window.removeEventListener('mousemove', handler);
  }, []);
  return <>{render(pos)}</>;
}

// Usage — behavior injected, rendering controlled by consumer
<MouseTracker render={({ x, y }) => (
  <div>Mouse at ({x}, {y})</div>
)}/>
```

## PRODUCTION USAGE

- **Radix UI**: compound components (Tabs, Select, Dialog) — hidden context + slots
- **Shadcn**: clones Radix primitives, custom styling via className
- **Tailwind CSS + Headless UI**: render props for behavior, no styles
- **Palantir Blueprint**: HOCs for toggling, focus management
