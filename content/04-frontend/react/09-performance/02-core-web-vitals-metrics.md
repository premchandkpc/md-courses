---
title: Core Web Vitals: Metrics, Monitoring & Optimization
topic: 04-frontend
difficulty: intermediate
time: 40
paths:
  - frontend
---

# Core Web Vitals: Metrics, Monitoring & Optimization

mins | **Interview:** 🔥 Critical

---

## Overview

Core Web Vitals measure real user experience. Three metrics dominate: Largest Contentful Paint (LCP), First Input Delay (FID/INP), and Cumulative Layout Shift (CLS). Understanding + optimizing these determines if users stay or bounce.

**Why this matters:**
- Google ranks pages by Core Web Vitals (Page Experience signal)
- Poor metrics = 25-50% bounce rate increase
- Interview prep: **always expect this question**

---

## Core Web Vitals Explained

### 1. LCP (Largest Contentful Paint) — ⏱️ Loading Speed

**What it measures:** Time until largest visible element renders

**Target:** < 2.5 seconds

**Real-world scenario:**
```
0s    ─────────────────────── 2.5s (Good LCP)
      ↑ DOM parsed          ↑ LCP fires (user sees content)

0s    ─────────────────────── 5s (Poor LCP - user leaves)
      ↑ DOM parsed          ↑ LCP fires (too late)
```

**What counts as LCP element:**
- `<img>` tags (most common)
- `<video>` posters
- SVG `<image>` elements
- Text blocks (rendered by CSS)
- Hero images
- Canvas-based backgrounds

**What doesn't count:**
- Below-the-fold images
- SVG text
- Iframes

**Why it matters:**
- Users judge page speed in first 2.5 seconds
- Slower LCP = higher bounce rate
- Each 1-second delay = ~7% conversion loss (typical e-commerce)

---

### 2. INP (Interaction to Next Paint) — 👆 Responsiveness

**Replaced:** First Input Delay (FID) in 2024

**What it measures:** Time from user interaction → visual response

**Target:** < 200ms

**Interactions tracked:**
- Click
- Tap
- Keyboard press (focus, text input)

**Not tracked:**
- Scroll (scrolling is visual by default)
- Hover
- Resize

**Real-world example (React app):**

```javascript
// Bad: INP = 800ms (user waits 0.8s after clicking)
function handleClick() {
  // Heavy CPU work
  const result = expensiveCalculation(data); // 600ms
  setResult(result); // Re-render (200ms)
  // Total: 800ms before paint
}

// Good: INP = 150ms (user sees response immediately)
function handleClick() {
  // Show spinner first (instant paint)
  setLoading(true);
  // Then do work in background
  requestIdleCallback(() => {
    const result = expensiveCalculation(data);
    setResult(result);
    setLoading(false);
  });
}
```

**Why it matters:**
- Slow INP = feels laggy, broken
- Mobile devices = 20-40% slower than desktop
- Developers often miss: heavy JS in event handlers

---

### 3. CLS (Cumulative Layout Shift) — 📐 Visual Stability

**What it measures:** Sum of all unexpected layout shifts during page lifetime

**Target:** < 0.1 (on 0-1 scale)

**Real-world example:**

```
Before optimization:
┌──────────────────┐
│   Ad loads here  │ ← User about to click "Sign Up"
│   (layout shift) │
│   Sign Up ────── │ ← Oops, it moved! User clicks wrong button
└──────────────────┘
CLS = 0.25 (BAD)

After optimization (reserve space):
┌──────────────────┐
│ ┌────────────┐   │
│ │ Ad goes    │   │ ← Space reserved, no shift
│ │ here       │   │
│ │ (skeleton) │   │
│ └────────────┘   │
│ Sign Up ──────── │ ← Stays in place, user clicks correctly
└──────────────────┘
CLS = 0.01 (GOOD)
```

**Common CLS culprits:**
1. **Images without dimensions** — Reserve height
2. **Ads that load late** — Reserve space or lazy-load below fold
3. **Fonts that swap** — Use `font-display: swap` + size hints
4. **Dynamically injected content** — Collapse/expand smoothly

---

## Measuring Core Web Vitals

### Tools

| Tool | Real Users? | Lab? | Setup |
|------|------------|------|-------|
| **Chrome DevTools** | No | Yes | F12 → Lighthouse |
| **Web.dev Measure** | No | Yes | https://web.dev/measure |
| **Google Search Console** | Yes | No | Core Web Vitals report |
| **PageSpeed Insights** | Yes | Yes | Real data + lab |
| **Sentry/Datadog** | Yes | No | SDK integration |
| **Custom Web Vitals API** | Yes | No | JavaScript |

### JavaScript API (Custom Monitoring)

```javascript
// Real User Monitoring (RUM) — production data
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendMetric(metric) {
  // Send to analytics backend
  fetch('/api/metrics', {
    method: 'POST',
    body: JSON.stringify({
      name: metric.name,
      value: metric.value,
      url: window.location.href,
      user_id: getUserId(),
      timestamp: new Date()
    })
  });
}

// Measure in production
getLCP(sendMetric);
getCLS(sendMetric);
getFID(sendMetric); // Deprecated, use INP
getTTFB(sendMetric);
```

### React Implementation

```javascript
// useWebVitals.js — React hook
import { useEffect } from 'react';
import { getCLS, getLCP, getFID } from 'web-vitals';

export function useWebVitals(onMetric) {
  useEffect(() => {
    getLCP(onMetric);
    getCLS(onMetric);
    getFID(onMetric);
  }, [onMetric]);
}

// App.js
function App() {
  const handleMetric = (metric) => {
    console.log(`${metric.name}: ${metric.value}ms`);
    // Send to analytics
    analytics.track('web_vital', {
      name: metric.name,
      value: Math.round(metric.value)
    });
  };

  useWebVitals(handleMetric);

  return <div>Your app</div>;
}
```

---

## Optimization Strategies

### LCP Optimization

#### 1. **Image Optimization** (70% of LCP issues)

```javascript
// ❌ Bad: Large unoptimized image
<img src="hero.jpg" width="1200" height="600" />
// 2.3 MB, renders at 4s

// ✅ Good: Optimized + responsive
<picture>
  <source srcSet="hero-small.webp 400w, hero-med.webp 800w, hero-large.webp 1200w" sizes="100vw" type="image/webp" />
  <img src="hero-large.jpg" alt="Hero" loading="eager" width="1200" height="600" />
</picture>
// 80 KB (webp), renders at 1.8s

// Tools: ImageOptim, TinyPNG, Next.js Image component
```

#### 2. **Eliminate Render-Blocking Resources**

```html
<!-- ❌ Bad: CSS blocks LCP -->
<head>
  <link rel="stylesheet" href="styles.css"> <!-- Blocks rendering -->
</head>

<!-- ✅ Good: Inline critical CSS, defer rest -->
<head>
  <style>
    /* Critical CSS (fold only, ~10KB) */
    body { margin: 0; }
    .hero { background: url(hero.jpg); }
  </style>
  <link rel="preload" href="styles.css" as="style">
  <link rel="stylesheet" href="styles.css" media="print" onload="this.media='all'">
</head>
```

#### 3. **Reduce Server Response Time (TTFB)**

```javascript
// Node.js example: cache headers for fast TTFB
app.use(compression());
app.set('etag', 'strong');

app.get('/', (req, res) => {
  res.set('Cache-Control', 'public, max-age=3600');
  res.set('Content-Encoding', 'gzip');
  res.sendFile('index.html');
});

// Result: TTFB < 200ms (vs 800ms uncached)
```

#### 4. **Font Strategy**

```css
/* ✅ Swap fonts quickly (avoid FOUT) */
@font-face {
  font-family: 'Roboto';
  font-display: swap; /* Show system font first, swap when ready */
  src: url('roboto.woff2') format('woff2');
  font-weight: 400;
}

/* Preload critical font */
<link rel="preload" href="roboto-400.woff2" as="font" type="font/woff2" crossorigin>
```

### INP Optimization

#### 1. **Break Up Long Tasks** (JavaScript execution)

```javascript
// ❌ Bad: 500ms of uninterruptible work
function processLargeDataset() {
  const results = [];
  for (let i = 0; i < 1000000; i++) {
    results.push(expensiveComputation(data[i]));
  }
  updateUI(results); // INP = 500ms
}

// ✅ Good: Yield to browser after 50ms chunks
async function processLargeDataset() {
  const results = [];
  const chunkSize = 1000;
  
  for (let i = 0; i < data.length; i += chunkSize) {
    results.push(...processChunk(data.slice(i, i + chunkSize)));
    
    // Yield to browser (allow input processing)
    await new Promise(resolve => setTimeout(resolve, 0));
  }
  
  updateUI(results); // INP = 50ms
}
```

#### 2. **Use requestIdleCallback for Background Work**

```javascript
// React example: defer non-critical updates
function SearchResults({ query }) {
  const [results, setResults] = useState([]);
  const [highlights, setHighlights] = useState([]);

  useEffect(() => {
    // Critical: search results (visible immediately)
    const results = search(query);
    setResults(results); // INP unaffected

    // Non-critical: syntax highlighting (background)
    requestIdleCallback(() => {
      const highlighted = results.map(r => syntaxHighlight(r));
      setHighlights(highlighted); // User already clicked away, no INP cost
    });
  }, [query]);

  return <>{results}</>;
}
```

#### 3. **Web Workers for Heavy Computation**

```javascript
// Main thread
const worker = new Worker('heavy-computation.js');

function handleClick() {
  setLoading(true); // Show spinner (instant paint, good INP)
  
  worker.postMessage({ data: largeDataset });
  worker.onmessage = (e) => {
    setResults(e.data);
    setLoading(false);
  };
}

// heavy-computation.js (Web Worker - separate thread)
self.onmessage = (e) => {
  const results = expensiveCalculation(e.data);
  self.postMessage(results);
};
```

### CLS Optimization

#### 1. **Reserve Space for Dynamic Content**

```jsx
// ❌ Bad: Ad loads, causes shift
export function ArticleWithAd() {
  const [adLoaded, setAdLoaded] = useState(false);
  
  return (
    <article>
      <h1>Article Title</h1>
      {adLoaded && <Ad />} {/* CLS = 0.15 when loads */}
      <p>Article content...</p>
    </article>
  );
}

// ✅ Good: Reserve space (skeleton)
export function ArticleWithAd() {
  const [adLoaded, setAdLoaded] = useState(false);
  
  return (
    <article>
      <h1>Article Title</h1>
      <div style={{ minHeight: '250px', width: '300px' }}>
        {adLoaded ? <Ad /> : <AdSkeleton />}
      </div>
      <p>Article content...</p>
    </article>
  );
}
```

#### 2. **Lazy Load Below the Fold**

```jsx
// ✅ Good: Only measure CLS for viewport
<img
  src="below-fold.jpg"
  alt="..."
  loading="lazy" // Don't load until visible
  width="800"
  height="600"
/>
```

#### 3. **Font Loading Strategy**

```css
/* ❌ Bad: Font swaps, text shifts */
@font-face {
  font-family: 'CustomFont';
  font-display: auto; /* FOUT + FOIT */
}

/* ✅ Good: Minimize shift with system font */
@font-face {
  font-family: 'CustomFont';
  font-display: swap; /* Show system font first */
  /* Plus: size system font to match custom font */
  font-size-adjust: 0.9;
}
```

---

## Real Production Example: E-Commerce Site

**Before optimization:**
- LCP: 4.2s ❌
- INP: 350ms ❌
- CLS: 0.18 ❌
- Bounce rate: 42%

**Bottlenecks identified:**
1. Hero image unoptimized (2.5 MB)
2. Render-blocking CSS (45 KB)
3. Heavy product list re-renders
4. Ad banner without reserved space

**Optimizations applied:**

```javascript
// 1. Image: WebP + responsive
const heroImage = {
  srcSet: 'hero-small.webp 400w, hero-large.webp 1200w',
  sizes: '100vw',
  loading: 'eager'
};

// 2. CSS: Critical inline, rest deferred
const criticalCSS = `
  body { margin: 0; }
  .hero { background: url(hero-small.webp); }
  .nav { ... }
`;

// 3. JS: Chunk product list rendering
const ChunkedProductList = React.lazy(() => import('./products'));

// 4. Ad space: Reserved with skeleton
<div style={{ minHeight: '300px', width: '100%' }}>
  <Suspense fallback={<AdSkeleton />}>
    <AdBanner />
  </Suspense>
</div>
```

**After optimization:**
- LCP: 1.8s ✅ (-57%)
- INP: 120ms ✅ (-65%)
- CLS: 0.08 ✅ (-55%)
- Bounce rate: 28% ✅ (+33% engagement)
- Revenue impact: +8% (faster = more conversions)

---

## Monitoring in Production

### Setup Analytics Pipeline

```javascript
// Custom monitoring
import { getCLS, getLCP, getFID } from 'web-vitals';

function reportWebVitals(metric) {
  const payload = {
    name: metric.name,
    value: metric.value.toFixed(0),
    rating: metric.rating, // 'good', 'needs-improvement', 'poor'
    url: window.location.href,
    user_agent: navigator.userAgent,
    timestamp: new Date().toISOString()
  };

  // Send to backend (batch for efficiency)
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/api/vitals', JSON.stringify(payload));
  } else {
    fetch('/api/vitals', { method: 'POST', body: JSON.stringify(payload) });
  }
}

getLCP(reportWebVitals);
getCLS(reportWebVitals);
getFID(reportWebVitals);
```

### Dashboard Queries (SQL-style pseudo-code)

```sql
-- Daily Core Web Vitals report
SELECT
  DATE(timestamp) as date,
  PERCENTILE(lcp, 0.75) as p75_lcp,
  PERCENTILE(inp, 0.75) as p75_inp,
  PERCENTILE(cls, 0.75) as p75_cls,
  COUNT(*) as samples
FROM web_vitals
WHERE timestamp > CURRENT_DATE - INTERVAL 7 DAY
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Identify slowest pages
SELECT
  url,
  AVG(lcp) as avg_lcp,
  COUNT(*) as samples
FROM web_vitals
WHERE lcp > 2500 -- Over threshold
GROUP BY url
ORDER BY avg_lcp DESC
LIMIT 10;
```

---

## Interview Questions & Answers

**Q: What's the difference between LCP and First Contentful Paint?**

A: FCP fires when ANY content renders (even 1 pixel). LCP fires when the LARGEST element renders. LCP is more meaningful (what users actually see) but slower. Always optimize for LCP.

**Q: Why did Google replace FID with INP?**

A: FID only measured first interaction. INP measures all interactions. A page could have fast first interaction but slow subsequent ones. INP is more representative.

**Q: How do you debug a 0.25 CLS score?**

A: Use DevTools → Performance → Layout Shift. Identify which elements shifted. Common causes:
1. Images without dimensions
2. Fonts swapping mid-render
3. Ads/embeds loading late

Reserve space (min-height) or lazy-load below fold.

**Q: Core Web Vitals as ranking factor?**

A: Google uses them in Page Experience signal. Not a hard cutoff (no 0.1 CLS = delisting), but affects ranking. Good COREs = slight ranking boost. Poor COREs = slight penalty.

---

## Best Practices Checklist

- [ ] LCP < 2.5s (test on real devices, mobile network)
- [ ] Optimize hero image (WebP, responsive, lazy-load)
- [ ] Inline critical CSS (< 50KB)
- [ ] Defer non-critical JavaScript
- [ ] INP < 200ms (test click handlers, avoid 100ms+ work)
- [ ] CLS < 0.1 (reserve space for ads, fonts, dynamic content)
- [ ] Monitor in production (RUM with web-vitals API)
- [ ] Set up alerting (notify if p75 exceeds threshold)
- [ ] Test on mobile (slow 4G network, mid-range device)

---

## See Also

### Phase 7.1 Related Topics

- [Advanced Form Patterns](../08-forms/02-advanced-form-patterns.md) — Form responsiveness impacts INP
- [Error Boundaries](../35-error-handling/01-error-boundaries-and-patterns.md) — Error UI rendering impacts CLS

### Additional Resources

- **Performance profiling:** `18-performance-engineering/`
- **Real-world scenarios:** `22-production-stories/` (performance incidents)
- **Bundling optimization:** `23-build-tools/01-vite-webpack-turbopack.md`
- **Image optimization:** Frontend image guides
- **Monitoring setup:** `14-sre-observability/` (metrics, dashboards)
