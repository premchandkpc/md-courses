# Bundlers

## Tree Shaking

Tree shaking (dead code elimination) removes unused exports from the final bundle. Webpack and Rollup both perform tree shaking at the module boundary level.

### How It Works

1. **ESM static analysis**: `import`/`export` are statically analyzable (unlike CommonJS `require()`), so the bundler builds a dependency graph and marks used/unused symbols.
2. **Rollup** performs live binding analysis — it traces exactly which bindings are used and elides the rest.
3. **Webpack** delegates tree shaking to TerserWebpackPlugin (via Terser) after marking modules as "harmony" (ESM). It uses `/*#__PURE__*/` annotations and `sideEffects` flags.

### The `sideEffects` Flag

In `package.json`, the `sideEffects` field tells the bundler whether a module has side effects when imported:

```json
{
  "sideEffects": false
}
```

- `false` — safe to tree-shake everything
- Array of paths — only those files have side effects

```json
{
  "sideEffects": ["./src/polyfills.ts", "*.css"]
}
```

### Why Tree Shaking Fails

| Reason | Example | Mitigation |
|---|---|---|
| Dynamic imports | `import(path)` | Static analysis impossible; use static imports where possible |
| CSS imports | `import './styles.css'` | Mark CSS as side-effecting explicitly |
| Barrel files | `export { a } from './utils'` | Re-exports can't be fully shaken; import directly |
| Side effects in entry | `import './init'` | The bundler assumes entry modules have side effects |
| Babel transforms ESM to CJS | `@babel/preset-env` with `modules: 'commonjs'` | Set `modules: false` |
| IIFE/UMD wrappers | Library ships as UMD | Use ESM-only builds |
| Decorators / class properties | TC39 proposals | `/*#__PURE__*/` annotation helps |

### `/*#__PURE__*/` Annotation

Tells the bundler a function call has no side effects and can be dropped if unused:

```js
const result = /*#__PURE__*/ heavyComputation();
```

---

## Code Splitting

Splitting the bundle into smaller chunks loaded on demand.

### Dynamic `import()`

```js
// Static import (bundled eagerly)
import { format } from 'date-fns';

// Dynamic import (separate chunk, loaded on demand)
const { format } = await import('date-fns');
```

The dynamic `import()` returns a `Promise<Module>`. Webpack/Rollup create a separate chunk automatically.

### `React.lazy` + `Suspense`

```jsx
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./Dashboard'));
const Settings = lazy(() => import('./Settings'));

function App() {
  return (
    <Suspense fallback={<Spinner />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}
```

`React.lazy` wraps the dynamic import — the chunk loads when the component renders for the first time. `Suspense` shows a fallback until the chunk resolves.

### Route-Based Splitting

Most common and effective strategy — split at route boundaries:

```jsx
const Home = lazy(() => import('./routes/Home'));
const About = lazy(() => import('./routes/About'));
const Contact = lazy(() => import('./routes/Contact'));
```

### Component-Level Splitting

Split heavy components that aren't immediately visible (modals, tabs, accordion panels):

```jsx
function ProductPage() {
  const [showGallery, setShowGallery] = useState(false);

  return (
    <>
      <button onClick={() => setShowGallery(true)}>View Gallery</button>
      {showGallery && (
        <Suspense fallback={null}>
          <ImageGallery />
        </Suspense>
      )}
    </>
  );
}
```

---

## Chunking Strategies

### `optimization.splitChunks` (Webpack)

```js
// webpack.config.js
module.exports = {
  optimization: {
    splitChunks: {
      chunks: 'all',
      minSize: 20000,
      maxSize: 244000,
      minChunks: 1,
      maxAsyncRequests: 30,
      maxInitialRequests: 30,
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
          priority: 10,
          reuseExistingChunk: true,
        },
        common: {
          minChunks: 2,
          priority: 5,
          reuseExistingChunk: true,
        },
        styles: {
          name: 'styles',
          type: 'css/mini-extract',
          chunks: 'all',
          enforce: true,
        },
      },
    },
  },
};
```

### Chunk Types

| Chunk Type | Description | Example |
|---|---|---|
| **Vendor chunk** | Third-party libraries (react, lodash) | `vendors~main.abc123.js` |
| **Shared chunk** | Modules used across >1 entry point | `common~main~admin.def456.js` |
| **Async chunk** | Dynamically imported module | `src_components_Dashboard_js.ghi789.js` |
| **Entry chunk** | Entry point runtime | `main.jkl012.js` |
| **Runtime chunk** | Webpack runtime + manifest | `runtime.mno345.js` |

### Manual Chunks (Vite/Rollup)

```js
// vite.config.js
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('react')) return 'vendor-react';
            if (id.includes('lodash')) return 'vendor-lodash';
            return 'vendor-other';
          }
        },
      },
    },
  },
});
```

### Chunking Decision Tree

```mermaid
flowchart TD
    A[Module] --> B{Imported via\ndynamic import()?}
    B -->|Yes| C[Async chunk]
    B -->|No| D{Used in >1 entry?}
    D -->|Yes| E[Shared chunk]
    D -->|No| F{From node_modules?}
    F -->|Yes| G[Vendor chunk]
    F -->|No| H[Entry chunk]
    C --> I{Size > maxSize?}
    I -->|Yes| J[Split into smaller chunks]
    I -->|No| K{Requests > limit?}
    K -->|Yes| L[Aggregate into fewer chunks]
    K -->|No| M[Finalize]
    J --> M
    L --> M
    G --> I
    E --> I
    H --> I
```

---

## Bundle Analysis

### webpack-bundle-analyzer

```js
// webpack.config.js
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');

module.exports = {
  plugins: [
    new BundleAnalyzerPlugin({
      analyzerMode: 'server', // 'server' | 'static' | 'json'
      analyzerPort: 8888,
      openAnalyzer: true,
      generateStatsFile: true,
      statsFilename: 'bundle-stats.json',
    }),
  ],
};
```

### source-map-explorer

```sh
npx source-map-explorer dist/*.js
```

Visualizes which modules contribute to bundle size using source maps. Useful when bundle-analyzer isn't available (e.g., non-webpack builds).

### BundlePhobia

CLI to check npm package cost before installing:

```sh
npx bundle-phobia check react react-dom lodash
```

### why-did-you-render

Not a bundle size tool, but prevents unnecessary re-renders that degrade perceived performance:

```js
import whyDidYouRender from '@welldone-software/why-did-you-render';

whyDidYouRender(React, {
  trackAllPureComponents: true,
  trackHooks: true,
});
```

---

## Bundle Budgets

Enforce size limits in CI. Fail the build if the bundle exceeds thresholds.

### Webpack Performance Budget

```js
// webpack.config.js
module.exports = {
  performance: {
    maxAssetSize: 244000, // 244 KB
    maxEntrypointSize: 400000, // 400 KB
    hints: 'error', // 'warning' | 'error' | false
    assetFilter(assetFilename) {
      return !assetFilename.endsWith('.map');
    },
  },
};
```

### CI with `bundlesize`

```json
// package.json
{
  "scripts": {
    "check-bundle": "bundlesize"
  },
  "bundlesize": [
    { "path": "./dist/main-*.js", "maxSize": "200 KB" },
    { "path": "./dist/vendors-*.js", "maxSize": "300 KB" },
    { "path": "./dist/*.css", "maxSize": "50 KB" }
  ]
}
```

### CI GitHub Action

```yaml
# .github/workflows/bundle-size.yml
name: Check Bundle Size
on: [pull_request]
jobs:
  bundle-size:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm run build
      - run: npx bundlesize
      - name: Size Limit
        uses: posva/size-limit-action@v2
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

### size-limit

```sh
npm install -D size-limit @size-limit/webpack
```

```json
// package.json
{
  "size-limit": [
    {
      "name": "Main JS",
      "path": "dist/main-*.js",
      "limit": "200 KB"
    },
    {
      "name": "Vendors",
      "path": "dist/vendors-*.js",
      "limit": "300 KB"
    },
    {
      "name": "Total CSS",
      "path": "dist/*.css",
      "limit": "50 KB",
      "running": false
    }
  ]
}
```

---

## CSS Bundling

### CSS Modules

Scoped class names via hash suffixes. Tree-shaken automatically:

```css
/* Button.module.css */
.root { background: blue; }
.icon { margin-right: 8px; }
```

```jsx
import styles from './Button.module.css';

function Button({ icon, children }) {
  return (
    <button className={styles.root}>
      <span className={styles.icon}>{icon}</span>
      {children}
    </button>
  );
}
```

Webpack resolves `.module.css` files and generates unique class names. Unused CSS class names are still emitted because they might be used dynamically (but PurgeCSS can remove them).

### CSS-in-JS Extraction

Libraries like Linaria, Vanilla Extract, and compiled CSS-in-JS (StylesX, Astro) extract styles at build time:

```ts
// Vanilla Extract — zero-runtime CSS-in-JS
import { style } from '@vanilla-extract/css';

export const button = style({
  background: 'blue',
  padding: 12,
});
```

This outputs a static `.css` file — no runtime cost. The bundler can split and tree-shake it normally.

### Critical CSS Inlining

Inline above-the-fold CSS in `<head>` to eliminate render-blocking CSS:

```js
// Critters webpack plugin
const Critters = require('critters-webpack-plugin');

module.exports = {
  plugins: [
    new Critters({
      preload: 'swap',
      noscriptFallback: true,
    }),
  ],
};
```

### PostCSS + PurgeCSS

Remove unused CSS classes:

```js
// postcss.config.js
module.exports = {
  plugins: [
    require('@fullhuman/postcss-purgecss')({
      content: ['./src/**/*.{js,jsx,ts,tsx}'],
      defaultExtractor: (content) => content.match(/[\w-/:]+(?<!:)/g) || [],
      safelist: ['html', 'body'],
    }),
  ],
};
```
