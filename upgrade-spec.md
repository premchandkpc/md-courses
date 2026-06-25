# Surgical Upgrade: `back_of_envelope.html`

Audit: 4164 lines, 387KB. 298K chars (86%) = scenario data (don't touch structure).
44K chars (13%) = rendering functions (main refactor target). 326 lines CSS + 17.5K chars HTML.

---

## 1. Scenario Metadata Model (add ~15 lines per scenario)

Add to each of the 20 scenario objects (before `arch:`):

```js
meta: {
  category: 'messaging'|'streaming'|'realtime'|'storage'|'ecommerce'|'infra'|'ml'|'pipeline',
  difficulty: 'senior'|'staff'|'architect',
  pattern: 'read-heavy'|'write-heavy'|'balanced'|'realtime'|'batch',
  consistency: 'strong'|'eventual'|'causal'|'hybrid',
  dominantBottleneck: 'db-writes'|'cache-memory'|'fanout'|'network-egress'|'storage'|'queue-lag'|'hot-partitions',
  storageEngine: 'postgres'|'cassandra'|'kafka'|'s3'|'bigtable'|'redis'|'vitess',
  cacheStrategy: 'write-through'|'cache-aside'|'read-through'|'write-behind'|'none',
}
```

Then render as badges in nav, overview sidebar, and compare cards.

---

## 2. State Management (refactor ~14 globals → one object)

Current globals: `currentScenarioId`, `currentParams`, `peakMult`, `compareOpen`, `cmpScenarioA`, `cmpScenarioB`, `currentFlowIdx`, `favorites`, `archAnimFrames`, plus inline state in `renderCompare`, `getCompareExportText`.

**Target:** single `const state = { ... }` at top of JS.

Changes:
- `currentScenarioId` → `state.scenarioId`
- `currentParams` → `state.params`
- `peakMult` → `state.peakMult`
- `compareOpen` → `state.compareOpen`
- `cmpScenarioA/B` → `state.cmpA` / `state.cmpB`
- `currentFlowIdx` → `state.flowIdx`
- `favorites` → `state.favorites` (keep Set, wrap with getter)
- `archAnimFrames` → `state.animFrames`

Add new state:
- `state.tabId` (current tab)
- `state.searchQuery`
- `state.dirtyParams` (per-scenario saved param values)
- `state.recentScenarios` (MRU list max 5)

---

## 3. Persistence (add 2 functions)

Current: only `saveFavorites()` + `JSON.parse` on load.

Add `saveState()` / `loadState()` that persists:
- `scenarioId`, `tabId`, `peakMult`, `favorites`, `dirtyParams`, `recentScenarios`, `cmpA`, `cmpB`

Single key `'boe-state'` in localStorage. Load on boot, save on every meaningful change (debounced 500ms).

---

## 4. Keyboard Shortcuts (add ~40 lines)

Add `document.addEventListener('keydown', ...)` that handles:

| Key | Action |
|---|---|
| `/` | Focus search input |
| `[` / `]` | Prev / next scenario |
| `1`–`5` | Switch tabs |
| `c` | Toggle compare mode |
| `e` | Export (if compare open) |
| `s` | Star/unstar current scenario |
| `Escape` | Close node detail panel, blur search |

---

## 5. Formula Transparency (add HTML + render)

New collapsible block inside Estimate tab (`#tab-estimate`):

```
[Show formulas ▼]
  writes/day = DAU × actions_per_user = 500M × 40 = 20B
  write_qps = writes/day / 86400 = 20B / 86400 ≈ 231K
  read_qps = write_qps × read_write_ratio = 231K × 2 ≈ 463K
  ...
```

Add to scenario calc function: return `formulas: [{label, expr, result}]` alongside existing outputs.
Add `renderFormulas(r)` function.
Add `#formulas-section` div in estimate tab html.

---

## 6. Scenario Nav Upgrade (~50 lines CSS + HTML + render)

Add category filters as chip row above nav:
```html
<div class="filter-chips" id="filter-chips">
  <button class="chip active" data-cat="all">All</button>
  <button class="chip" data-cat="messaging">Messaging</button>
  ...
</div>
```

Current nav: `renderScenarioNav()` reads `[...SCENARIOS].sort(...)`. Change to filter by `meta.category` when filter active, show difficulty badge, show star.

Add scenario count badge per filter.

---

## 7. Architecture Explain Mode (add ~80 lines JS + HTML)

Below the SVG diagram in `#tab-architecture`, add:
```html
<div id="arch-explain"></div>
```

`renderArchitecture` already renders the SVG, flows, and choices. Add `renderArchExplain(scenario)` that generates text sections from existing data:

- **Request lifecycle**: from arch.flows, build a step-by-step narrative
- **Why this stack**: from arch.choices, explain key decisions
- **Failure modes**: from incidents, produce "what breaks first" 
- **Scale strategy**: use insights array

---

## 8. What-If / Stress Test Panel (add ~60 lines JS + HTML)

New panel in Overview tab (collapsible):

```html
<div id="stress-panel" class="panel">
  <div class="panel-title">What If? <i class="ti ti-arrows-shuffle"></i></div>
  <div class="stress-grid">
    <button data-mult="2">2× traffic</button>
    <button data-mult="5">5× traffic</button>
    <button data-mult="10">10× traffic</button>
    <button data-cache="0.5">Cache miss ×2</button>
    <button data-payload="2">Payload ×2</button>
  </div>
  <div id="stress-results"></div>
</div>
```

Each button clones current params, applies multiplier, runs `scenario.calc()`, shows delta from baseline.

---

## 9. Compare Mode Deltas (modify ~30 lines in `renderCompare`)

Current: shows side-by-side raw values.

Add delta column between A and B columns:
```
  Reads:    463K   │  +23%   │  378K
  Writes:   231K   │  -12%   │  263K
  ...
```

Color green/red based on direction (green = lower/higher depending on metric). Add `renderCompareDeltas(rA, rB)`.

---

## 10. Single-Scenario Export (modify ~20 lines)

Current: `getCompareExportText()` only works in compare mode.

Add `exportScenario(id)` that produces same structured plain-text report for a single scenario.
Wire to a new "Export" button in the overview panel that works independently of compare mode.

---

## 11. Accessibility (add ~30 attributes + event tweaks)

Targets:
- All `<button>` elements → add `aria-label` or `aria-pressed` where stateful
- `#scenario-nav` buttons → `role="tab"` + `aria-selected`
- Tab buttons → `role="tab"` + `aria-controls`
- Canvas → `role="img"` + `aria-label="Traffic chart"`
- Slider `#peak-slider` → already has `aria-label`, add `aria-valuetext`
- Search input → `aria-controls="scenario-nav"` + `role="combobox"`
- Node detail panel → trap focus when open

---

## 12. CSS Additions (target ~100 lines)

Add classes for:
- `.filter-chips` / `.chip` — category filter row
- `.stress-grid` / `.stress-btn` — what-if buttons
- `.formula-block` / `.formula-row` — formula breakdown
- `.delta-pos` / `.delta-neg` — compare deltas
- `.badge-cat` / `.badge-diff` — scenario metadata badges
- `.arch-explain-section` — architecture explain mode
- `.kbd` — keyboard shortcut display (already exists as `kbd-hint`, enhance)
- `.recent-scenarios` — MRU list

---

## Execution Order

1. **State refactor** — `state` object + persistence (foundation for everything else)
2. **Scenario metadata** — add `meta` to all 20 scenarios + render badges
3. **Nav upgrade** — filter chips + difficulty display
4. **Keyboard shortcuts** — event listener (depends on state)
5. **Formula transparency** — add to calc outputs + render
6. **Architecture explain** — text generation from existing data
7. **What-if panel** — stress test buttons + delta display
8. **Compare deltas** — enhance existing compare view
9. **Single export** — independent export
10. **Accessibility** — attributes + focus management
11. **CSS polish** — all new UI classes

Each step must preserve existing functionality (regression guard after each).
