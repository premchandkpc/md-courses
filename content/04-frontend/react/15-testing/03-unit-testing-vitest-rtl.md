# Unit Testing React with Vitest & React Testing Library

**Level:** Intermediate | **Time:** 40 mins | **Interview:** 🔥 Critical

---

## Overview

Vitest (Vite native test runner) + React Testing Library (RTL) = modern React testing. RTL forces you to test user behavior, not implementation. Vitest runs tests 10-50x faster than Jest in most projects (no Node.js overhead, native ES modules).

**Why this matters:**
- Tests catch bugs before production
- RTL prevents brittle implementation-dependent tests
- Interview: always expect testing questions
- Business: faster CI/CD = faster deploys

---

## The Testing Pyramid

```
        /\
       /  \     E2E (Cypress, Playwright)
      /    \    5-10% of tests
     /______\
     /      \
    /        \   Integration
   /          \  15-20% of tests
  /____________\
  /            \
 /              \ Unit (Vitest + RTL)
/________________\ 70-80% of tests

Ideal ratio: 70% unit / 20% integration / 10% E2E
```

---

## Vitest Setup

### Installation

```bash
npm install -D vitest @vitest/ui
npm install -D @testing-library/react @testing-library/jest-dom
npm install -D jsdom  # DOM simulation for tests
```

### Configuration (vitest.config.ts)

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,           // describe, it, expect global
    environment: 'jsdom',    // browser-like environment
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      lines: 80,             // Enforce 80% line coverage
      functions: 80,
      branches: 75,
      statements: 80,
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

### Setup File (src/test/setup.ts)

```typescript
import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom'; // Matchers: toBeInTheDocument, etc

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock window.matchMedia (for responsive tests)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
```

---

## React Testing Library: Core Concepts

### The Philosophy

**❌ DON'T test:**
- Component internals (state, props)
- Implementation details
- How it renders

**✅ DO test:**
- User behavior (click, type, submit)
- What users see (text, buttons, forms)
- User workflows (login → dashboard → logout)

### Query Hierarchy (Use In Order)

```
1. getByRole       ← BEST (accessibility-first)
2. getByLabelText  ← Form inputs
3. getByPlaceholder
4. getByText       ← Content
5. getByTestId     ← Last resort
```

**Why?** getByRole tests accessibility. If button isn't findable by role, screen readers can't use it either.

---

## Testing Patterns

### Pattern 1: Simple Component (Button)

```typescript
// ❌ BAD: Tests implementation, not behavior
it('sets state to true when clicked', () => {
  const { container } = render(<ToggleButton />);
  const state = container.querySelector('[data-testid="state"]');
  expect(state).toHaveTextContent('false');
  
  const button = container.querySelector('button');
  fireEvent.click(button);
  expect(state).toHaveTextContent('true');
});

// ✅ GOOD: Tests user behavior
it('toggles visibility when user clicks', () => {
  render(<ToggleButton />);
  
  const button = screen.getByRole('button', { name: /show details/i });
  expect(screen.queryByText('Secret info')).not.toBeInTheDocument();
  
  await userEvent.click(button);
  expect(screen.getByText('Secret info')).toBeInTheDocument();
});
```

### Pattern 2: Form Submission

```typescript
it('submits form with user input', async () => {
  const handleSubmit = vi.fn();
  render(<LoginForm onSubmit={handleSubmit} />);
  
  // User types email
  const emailInput = screen.getByLabelText(/email/i);
  await userEvent.type(emailInput, 'user@example.com');
  
  // User types password
  const passwordInput = screen.getByLabelText(/password/i);
  await userEvent.type(passwordInput, 'password123');
  
  // User clicks submit
  const submitButton = screen.getByRole('button', { name: /sign in/i });
  await userEvent.click(submitButton);
  
  // Assert handler called
  expect(handleSubmit).toHaveBeenCalledWith({
    email: 'user@example.com',
    password: 'password123'
  });
});
```

### Pattern 3: Async Data Loading

```typescript
it('loads and displays user data', async () => {
  // Mock API
  vi.mock('@/api/users', () => ({
    fetchUser: vi.fn(() => 
      Promise.resolve({ id: 1, name: 'Alice', role: 'admin' })
    )
  }));
  
  render(<UserProfile userId={1} />);
  
  // Show loading state initially
  expect(screen.getByText(/loading/i)).toBeInTheDocument();
  
  // Wait for data
  expect(await screen.findByText('Alice')).toBeInTheDocument();
  expect(screen.getByText('admin')).toBeInTheDocument();
});
```

### Pattern 4: Testing Hooks

```typescript
import { renderHook, act } from '@testing-library/react';
import { useCounter } from '@/hooks/useCounter';

it('increments count on button click', () => {
  const { result } = renderHook(() => useCounter());
  
  expect(result.current.count).toBe(0);
  
  act(() => {
    result.current.increment();
  });
  
  expect(result.current.count).toBe(1);
});
```

### Pattern 5: Context Provider Testing

```typescript
it('reads theme from context', () => {
  const TestWrapper = ({ children }) => (
    <ThemeProvider theme="dark">
      {children}
    </ThemeProvider>
  );
  
  render(<ThemedButton />, { wrapper: TestWrapper });
  
  const button = screen.getByRole('button');
  expect(button).toHaveClass('dark-theme');
});
```

---

## Real Production Example: Product Search

```typescript
// ProductSearch.test.tsx
describe('ProductSearch', () => {
  it('searches products on user input', async () => {
    const mockSearch = vi.fn(() =>
      Promise.resolve([
        { id: 1, name: 'Laptop', price: 999 },
        { id: 2, name: 'Laptop Stand', price: 49 }
      ])
    );

    render(<ProductSearch onSearch={mockSearch} />);

    // User types in search
    const input = screen.getByPlaceholderText(/search products/i);
    await userEvent.type(input, 'laptop');

    // Wait for results (debounced search)
    expect(await screen.findByText('Laptop')).toBeInTheDocument();
    expect(screen.getByText('Laptop Stand')).toBeInTheDocument();

    // Verify search called with query
    expect(mockSearch).toHaveBeenCalledWith('laptop');
  });

  it('shows no results message when empty', async () => {
    const mockSearch = vi.fn(() => Promise.resolve([]));

    render(<ProductSearch onSearch={mockSearch} />);

    const input = screen.getByPlaceholderText(/search products/i);
    await userEvent.type(input, 'xyz123xyz');

    expect(await screen.findByText(/no products found/i)).toBeInTheDocument();
  });

  it('handles search errors gracefully', async () => {
    const mockSearch = vi.fn(() =>
      Promise.reject(new Error('Network error'))
    );

    render(<ProductSearch onSearch={mockSearch} />);

    const input = screen.getByPlaceholderText(/search products/i);
    await userEvent.type(input, 'laptop');

    expect(await screen.findByText(/failed to load products/i)).toBeInTheDocument();
  });
});
```

---

## Mocking Patterns

### Mock Functions (vi.fn)

```typescript
const mockHandler = vi.fn();
mockHandler('arg1');
expect(mockHandler).toHaveBeenCalledWith('arg1');
expect(mockHandler).toHaveBeenCalledTimes(1);
expect(mockHandler.mock.calls[0]).toEqual(['arg1']);
```

### Mock Modules

```typescript
// ❌ Harder to read
vi.mock('@/api', () => ({
  fetchUser: vi.fn()
}));

// ✅ Better: explicit return
vi.mock('@/api', () => ({
  fetchUser: vi.fn(() => Promise.resolve({ id: 1, name: 'Alice' }))
}));
```

### Mock Window Methods

```typescript
it('scrolls to element', async () => {
  const scrollIntoViewMock = vi.fn();
  Element.prototype.scrollIntoView = scrollIntoViewMock;

  render(<ScrollToButton />);
  
  await userEvent.click(screen.getByRole('button'));
  
  expect(scrollIntoViewMock).toHaveBeenCalled();
});
```

---

## Common Testing Mistakes

### ❌ Mistake 1: Testing Implementation Details

```typescript
// BAD: Brittle, breaks on refactor
it('sets state to loading', () => {
  render(<DataLoader />);
  expect(container.querySelector('[data-testid="loading-state"]')).toBeTruthy();
});

// GOOD: User-facing
it('shows loading message while fetching', () => {
  render(<DataLoader />);
  expect(screen.getByText(/loading/i)).toBeInTheDocument();
});
```

### ❌ Mistake 2: Not Waiting for Async Operations

```typescript
// BAD: Doesn't wait for render
it('loads data', () => {
  render(<UserProfile id={1} />);
  expect(screen.getByText('Alice')).toBeInTheDocument(); // Fails, not loaded yet
});

// GOOD: Uses findBy (waits)
it('loads data', async () => {
  render(<UserProfile id={1} />);
  expect(await screen.findByText('Alice')).toBeInTheDocument();
});
```

### ❌ Mistake 3: Over-Testing (Testing Framework Internals)

```typescript
// BAD: Tests React internals, not user experience
it('calls setState', () => {
  const spy = vi.spyOn(Component.prototype, 'setState');
  // ...
});

// GOOD: Tests behavior
it('shows updated data after user clicks', async () => {
  render(<Component />);
  await userEvent.click(screen.getByRole('button'));
  expect(screen.getByText(/updated/i)).toBeInTheDocument();
});
```

---

## Running Tests

```bash
# Run all tests
npm run test

# Watch mode (re-run on file change)
npm run test:watch

# Coverage report
npm run test:coverage

# UI mode (interactive dashboard)
npm run test:ui
```

### CI/CD Integration (GitHub Actions)

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run test:coverage
      - run: npm run test:ui -- --reporter=verbose
```

---

## Performance Tips

### 1. Isolate Components

```typescript
// ✅ Test Button in isolation, not full page
it('shows pressed state', async () => {
  render(<Button>Click me</Button>);
  await userEvent.click(screen.getByRole('button'));
  expect(screen.getByRole('button')).toHaveAttribute('aria-pressed', 'true');
});
```

### 2. Use within() for Scoped Queries

```typescript
it('fills form correctly', async () => {
  render(<MultiFormPage />);
  
  const form1 = screen.getByRole('region', { name: /form 1/i });
  const input1 = within(form1).getByLabelText(/email/i); // Only searches form1
  
  await userEvent.type(input1, 'test@example.com');
});
```

### 3. Parallel Test Execution

```bash
# Vitest runs tests in parallel by default
npm run test -- --threads
```

---

## Best Practices Checklist

- [ ] Test user behavior, not implementation
- [ ] Use getByRole first (accessibility-focused)
- [ ] Use userEvent, not fireEvent (more realistic)
- [ ] Use findBy for async queries (not getBy)
- [ ] Keep tests focused (one assertion per test if possible)
- [ ] Mock external dependencies (APIs, third-party libs)
- [ ] Aim for 80%+ coverage
- [ ] Tests should be readable (describe what they do)
- [ ] Clean up after tests (mocks, timers)
- [ ] Use test.skip for WIP, test.only for debugging

---

## Interview Q&A

**Q: What's the difference between fireEvent and userEvent?**

A: fireEvent triggers DOM events directly (unrealistic). userEvent simulates user interactions (click, type, etc.) with proper delays + behavior. Always prefer userEvent.

**Q: How do you test async components?**

A: Use `findBy` (waits for element) instead of `getBy`. Or wrap async code in `waitFor(() => { expect(...) })`.

**Q: Should you test component state?**

A: No. State is implementation detail. Test behavior (what user sees after clicking). RTL enforces this.

---

## See Also

### Phase 7.1 Related Topics

- [Redux/Zustand Patterns](../05-state-management/02-redux-zustand-patterns.md) — Testing state management
- [Advanced Form Patterns](../08-forms/02-advanced-form-patterns.md) — Testing form submission
- [Compound Components](../06-component-architecture/02-compound-components-pattern.md) — Testing component composition

### Additional Resources

- **E2E testing:** Playwright, Cypress (full workflows)
- **Integration testing:** Testing multiple components together
- **Snapshot testing:** `toMatchSnapshot()` (use sparingly)
- **Testing strategies:** `19-testing/`
