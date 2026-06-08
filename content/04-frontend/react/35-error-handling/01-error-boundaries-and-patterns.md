---
title: Error Boundaries & Error Handling: Building Resilient React Apps
topic: 04-frontend
difficulty: intermediate
time: 45
paths:
  - frontend
---

# Error Boundaries & Error Handling: Building Resilient React Apps

[🎨 Interactive Visualization](../../html/35-error-boundaries-and-patterns-viz.html)

mins | **Interview:** 🔥 Critical

---

## Overview

Error handling in React = preventing one component's crash from breaking the entire app. Error Boundaries catch render errors. Error tracking logs issues to production. Fallback UI keeps app usable. This guide covers Error Boundaries, error recovery patterns, retry logic, and error monitoring strategies.

**Why this matters:**
- Unhandled error = blank screen (users think app is broken)
- Error Boundaries = graceful degradation (show error UI, not crash)
- Interview prep: "How would you handle errors in production?"
- Real-world: 5% of users encounter errors daily; 10% of those leave if handled poorly

---

## 1. Error Boundaries: Catching Render Errors

Error Boundaries are class components that catch JavaScript errors in child components.

### Basic Error Boundary

```javascript
// ✅ GOOD: Catch and display error gracefully
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so next render shows fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log error to service (Sentry, Rollbar, etc.)
    logErrorToService(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>{this.state.error.message}</p>
          <button onClick={() => window.location.reload()}>
            Reload page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Usage
<ErrorBoundary>
  <Dashboard /> {/* If Dashboard renders error, catch it */}
</ErrorBoundary>
```

**What Error Boundaries CATCH:**
- Render errors (during render phase)
- Lifecycle method errors
- Constructor errors
- Child component render errors

**What Error Boundaries DON'T CATCH:**
- Event handler errors (use try/catch)
- Async errors (use async/await try/catch)
- Server-side rendering errors
- Errors in ErrorBoundary itself

---

## 2. Handling Different Error Types

### Error Type 1: Render Error (Caught by Error Boundary)

```javascript
// ❌ WILL CRASH without Error Boundary
function BrokenComponent() {
  const user = null;
  return <div>{user.name}</div>; // Cannot read property 'name' of null
}

// ✅ CAUGHT by Error Boundary
<ErrorBoundary>
  <BrokenComponent />
</ErrorBoundary>

// ✅ FIXED: Add defensive check
function SafeComponent() {
  const user = null;
  return <div>{user?.name || 'Guest'}</div>;
}
```

### Error Type 2: Event Handler Error (NOT Caught by Error Boundary)

```javascript
// ❌ NOT CAUGHT (error happens after render)
function Button() {
  const handleClick = () => {
    throw new Error('Click error');
  };
  return <button onClick={handleClick}>Click</button>;
}

// ✅ CAUGHT: Wrap in try/catch
function Button() {
  const handleClick = () => {
    try {
      // Do something risky
    } catch (err) {
      logError(err);
      showErrorToast('Failed to perform action');
    }
  };
  return <button onClick={handleClick}>Click</button>;
}
```

### Error Type 3: Async Error (NOT Caught by Error Boundary)

```javascript
// ❌ NOT CAUGHT (error in Promise, outside React)
function DataFetcher() {
  useEffect(() => {
    fetch('/api/data')
      .then(r => r.json())
      .then(data => {
        throw new Error('Parse error'); // Not caught by boundary
      });
  }, []);
  return <div>Loading...</div>;
}

// ✅ CAUGHT: Handle in catch block
function DataFetcher() {
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/api/data')
      .then(r => r.json())
      .then(data => {
        // Process data
      })
      .catch(err => {
        setError(err); // Update state to show error UI
      });
  }, []);

  if (error) {
    return <ErrorUI error={error} />;
  }

  return <div>Loading...</div>;
}
```

---

## 3. Advanced Error Boundary: Scoped & Granular

Wrap Error Boundaries around risky sections (not entire app). This pattern is critical for forms and submission errors (see [Advanced Form Patterns](../08-forms/02-advanced-form-patterns.md) for handling async submission failures).

```javascript
function Dashboard() {
  return (
    <div>
      {/* If header breaks, only header shows error */}
      <ErrorBoundary fallback={<HeaderError />}>
        <Header />
      </ErrorBoundary>

      {/* If sidebar breaks, only sidebar shows error */}
      <ErrorBoundary fallback={<SidebarError />}>
        <Sidebar />
      </ErrorBoundary>

      {/* If main content breaks, only main shows error */}
      <ErrorBoundary fallback={<ContentError />}>
        <MainContent />
      </ErrorBoundary>
    </div>
  );
}

// Result: One component breaking doesn't break entire page
```

---

## 4. Error Recovery & Retry Logic

### Pattern 1: Error Recovery with useState

```javascript
function DataDisplay() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [retries, setRetries] = useState(0);
  const MAX_RETRIES = 3;

  useEffect(() => {
    fetch('/api/data')
      .then(r => r.json())
      .then(data => setData(data))
      .catch(err => {
        setError(err);
        if (retries < MAX_RETRIES) {
          // Auto-retry after 2 seconds
          setTimeout(() => {
            setRetries(r => r + 1);
          }, 2000);
        }
      });
  }, [retries]);

  if (error && retries >= MAX_RETRIES) {
    return (
      <div>
        <p>Failed to load data after {MAX_RETRIES} retries</p>
        <button onClick={() => setRetries(0)}>Try again</button>
      </div>
    );
  }

  if (error) {
    return <p>Loading (retry {retries + 1}/{MAX_RETRIES})...</p>;
  }

  return <div>{/* Render data */}</div>;
}
```

### Pattern 2: Exponential Backoff

```javascript
async function fetchWithRetry(url, options = {}) {
  const maxRetries = 3;
  let lastError;

  for (let i = 0; i <= maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      if (response.ok) return response;
      
      // 5xx = server error = retryable
      if (response.status >= 500) {
        throw new Error(`Server error: ${response.status}`);
      }
      
      // 4xx = client error = not retryable
      throw new Error(`Request failed: ${response.status}`);
    } catch (err) {
      lastError = err;
      
      if (i < maxRetries) {
        // Exponential backoff: 1s, 2s, 4s
        const delay = Math.pow(2, i) * 1000;
        await new Promise(r => setTimeout(r, delay));
      }
    }
  }

  throw lastError;
}

// Usage
const data = await fetchWithRetry('/api/data');
```

---

## 5. Error Monitoring & Logging

### Pattern 1: Log Errors to Service

```javascript
// Setup Sentry (error tracking service)
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "https://xxx@sentry.io/xxx",
  environment: process.env.NODE_ENV,
  tracesSampleRate: 0.1 // 10% of requests
});

class ErrorBoundary extends React.Component {
  componentDidCatch(error, errorInfo) {
    // Send to Sentry
    Sentry.captureException(error, {
      contexts: {
        react: {
          errorInfo: errorInfo,
          componentStack: errorInfo.componentStack
        }
      }
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div>
          <h2>Something went wrong</h2>
          <Sentry.ErrorBoundary fallback="An error has occurred" />
        </div>
      );
    }

    return this.props.children;
  }
}
```

### Pattern 2: Custom Error Logger

```javascript
const errorLogger = {
  log: async (error, context) => {
    const payload = {
      message: error.message,
      stack: error.stack,
      context,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    try {
      await fetch('/api/errors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch (err) {
      // Fail silently (don't break app if logging fails)
      console.error('Failed to log error', err);
    }
  }
};

// Usage
class ErrorBoundary extends React.Component {
  componentDidCatch(error, errorInfo) {
    errorLogger.log(error, {
      component: errorInfo.componentStack,
      userId: getCurrentUser()?.id,
      sessionId: getSessionId()
    });
  }
}
```

---

## 6. Graceful Degradation Patterns

### Pattern 1: Feature-Level Error Boundary

```javascript
function CommentSection() {
  return (
    <ErrorBoundary fallback={<p>Comments unavailable</p>}>
      <Comments /> {/* If Comments breaks, show fallback, not whole page broken */}
    </ErrorBoundary>
  );
}

function Dashboard() {
  return (
    <div>
      <Header />
      <CommentSection /> {/* Even if Comments fails, Dashboard still works */}
      <Sidebar />
    </div>
  );
}
```

### Pattern 2: Fallback UI with Retry

```javascript
class ErrorBoundary extends React.Component {
  render() {
    if (this.state.hasError) {
      return (
        <div className="error-ui">
          <h3>⚠️ Something went wrong</h3>
          <p>{this.state.error.message}</p>
          <button onClick={this.handleReset}>
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };
}
```

---

## 7. Testing Error Scenarios

```javascript
import { render, screen } from '@testing-library/react';

// Mock a component that throws
function ThrowError() {
  throw new Error('Test error');
}

test('Error Boundary catches render errors', () => {
  // Suppress console.error for test
  jest.spyOn(console, 'error').mockImplementation(() => {});

  render(
    <ErrorBoundary>
      <ThrowError />
    </ErrorBoundary>
  );

  expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
});

test('Event handler errors are not caught by boundary', async () => {
  const { getByRole } = render(
    <ErrorBoundary>
      <button onClick={() => throw new Error('Click error')}>
        Click me
      </button>
    </ErrorBoundary>
  );

  // Suppress console.error
  jest.spyOn(console, 'error').mockImplementation(() => {});

  // Error should NOT be caught by boundary (happens in event)
  // Instead, test should wrap click in try/catch
  await expect(async () => {
    userEvent.click(getByRole('button'));
  }).rejects.toThrow('Click error');
});
```

---

## 8. Common Mistakes

### Mistake 1: Too Broad Error Boundaries

```javascript
// ❌ BAD: One boundary catches entire app
<ErrorBoundary>
  <App />
</ErrorBoundary>

// Result: Single component error → entire app shows error screen

// ✅ GOOD: Granular error boundaries
<div>
  <ErrorBoundary>
    <Header />
  </ErrorBoundary>
  <ErrorBoundary>
    <MainContent />
  </ErrorBoundary>
  <ErrorBoundary>
    <Sidebar />
  </ErrorBoundary>
</div>

// Result: Single component error → only that component shows error
```

### Mistake 2: Not Logging Errors

```javascript
// ❌ BAD: Error boundary doesn't log
class ErrorBoundary extends React.Component {
  componentDidCatch(error) {
    // Silently fail (never know there was an issue)
  }
}

// ✅ GOOD: Log every error
class ErrorBoundary extends React.Component {
  componentDidCatch(error, errorInfo) {
    logErrorToService(error, errorInfo);
  }
}
```

### Mistake 3: Event Handlers Without Try/Catch

```javascript
// ❌ BAD: Error not caught
const handleClick = () => {
  risky();
};

// ✅ GOOD: Wrap in try/catch
const handleClick = () => {
  try {
    risky();
  } catch (err) {
    logError(err);
    showErrorMessage('Failed to save');
  }
};
```

---

## 9. Production Checklist

- [ ] Error Boundaries wrapped around risky sections
- [ ] Event handlers have try/catch for async operations
- [ ] Async errors handled (fetch catch, Promise.catch)
- [ ] Errors logged to service (Sentry, Rollbar, etc.)
- [ ] User-friendly error messages (not technical)
- [ ] Retry logic for transient failures (network)
- [ ] Fallback UI provided (don't show blank page)
- [ ] Error tracking monitored (alerts on spike)
- [ ] Errors tested in unit & integration tests
- [ ] Source maps uploaded (can see original code in error reports)

---

## Interview Prep Questions

1. **"How do Error Boundaries work?"**
   - Answer: Class components using getDerivedStateFromError + componentDidCatch. Catch render errors from children. Show fallback UI instead of crashing entire app.

2. **"What errors do Error Boundaries NOT catch?"**
   - Answer: Event handlers (use try/catch), async errors (Promise.catch), server-side rendering, errors in boundary itself.

3. **"How would you handle an API call that fails?"**
   - Answer: Wrap in try/catch. Show error message to user. Offer retry button. Log error for monitoring. Set state to error, show fallback UI.

4. **"How do you prevent blank screens from errors?"**
   - Answer: Error Boundaries + granular scoping. Each feature has own boundary. One component breaks, not entire app.

5. **"How would you monitor errors in production?"**
   - Answer: Send errors to Sentry/Rollbar. Include user ID, session ID, page URL. Set up alerts on error spike. Review daily.

---

## See Also

### Phase 7.1 Related Topics

- [XSS/CSRF/CSP](../17-security/02-xss-csrf-csp-deep-dive.md) — Sanitizing error messages
- [Advanced Form Patterns](../08-forms/02-advanced-form-patterns.md) — Async form submission errors
- [React Fiber](../02-react-internals/02-fiber-reconciliation-engine.md) — Where errors occur during render
- [WCAG Accessibility](../16-accessibility/02-wcag-patterns-and-compliance.md) — Accessible error UI

### Additional Resources

- React Error Boundaries: Official docs
- Sentry: Error tracking service
- Rollbar: Alternative error tracking
- Error Tracking Best Practices
- Resilient Component Design
