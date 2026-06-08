---
title: Interactive Engineering Platform — Implementation Roadmap
time: 30m
---

# Interactive Engineering Platform — Implementation Roadmap

**Status:** Phase 1 ✅ Complete | Phase 2-4 📋 Planned

---

## Overview

Transform 303 markdown course files into an interactive learning platform with embedded animations, simulations, and dynamic visualizations. No new files/repos — enhance existing .md files with `html-live` blocks containing self-contained interactive components.

**Key Constraint:** `<script>` via `innerHTML` doesn't execute. Solution: read.html now extracts `html-live` blocks, reinjects as live DOM, executes scripts via `document.createElement('script')`.

---

## Phase 1: Viewer Foundation ✅

**Status:** COMPLETE

### What was done
1. Modified `/data/read.html` renderContent():
   - Extract `\`\`\`html-live` blocks before markdown processing
   - Reinject as live DOM after innerHTML
   - Execute scripts via createElement('script')
   - Placeholders: `__HTMLLIVE0__`, `__HTMLLIVE1__`, etc.

2. Added to `/data/read.css`:
   - `.html-live-block` styling (dark card, border, padding, overflow)
   - Button styling (neon border #00d4ff, hover glow)
   - Input[type=range] slider styling
   - SVG/Canvas max-width responsive

3. Created test file `/data/test-interactive.md`:
   - Request flow animation (CSS keyframes)
   - Slider with JavaScript interactivity
   - State machine with onclick buttons
   - Proves concept works end-to-end

### How to verify Phase 1
```bash
# Syntax check
grep -c "html-live" /data/read.html  # Should be >0
grep -c "html-live-block" /data/read.css  # Should be >0

# Test in browser:
# 1. Open read.html
# 2. Navigate to test-interactive.md
# 3. Verify:
#    - Request flow arrows pulse
#    - Slider moves and updates value
#    - Buttons change state machine color
#    - No console errors
```

---

## Phase 2: Component Library (6 Reusable Templates)

**Scope:** ~1000 lines vanilla HTML+CSS+JS
**Effort:** 1 developer, 4-6 hours
**Output:** 6 template files in `/data/components/` folder

### Component 1: Request Flow Animator

**File:** `/data/components/request-flow.html-template`

**Pattern:**
```html
<!-- Pure CSS animation, no JS required -->
<div style="display:flex;flex-direction:column;align-items:center;gap:8px">
  <style>
    @keyframes flow-pulse { 0%,100%{opacity:.3} 50%{opacity:1} }
    .flow-node { padding:8px 16px; border-radius:4px; background:#1e3a5f; border:1px solid #00d4ff; color:#e3eaf0; font-family:monospace; font-size:12px }
    .flow-arrow { color:#00d4ff; animation:flow-pulse 1.5s infinite; font-size:16px }
  </style>
  <div class="flow-node">{{node1}}</div>
  <div class="flow-arrow">↓</div>
  <div class="flow-node">{{node2}}</div>
  <!-- repeat for each node -->
</div>
```

**Usage in .md files:**
```markdown
## Request Lifecycle

[existing explanation]

### Visual: Request Flow
\`\`\`html-live
<div style="display:flex;flex-direction:column;align-items:center;gap:8px;padding:16px">
  <!-- insert flow-node template, customize nodes -->
  <div style="background:#1e3a5f;padding:8px 16px;border-radius:4px;border:1px solid #00d4ff;color:#e3eaf0;font-family:monospace;font-size:12px">Client</div>
  <div style="color:#00d4ff;font-size:16px;animation:flow-pulse 1.5s infinite">↓</div>
  <div style="background:#1e3a5f;padding:8px 16px;border-radius:4px;border:1px solid #00d4ff;color:#e3eaf0;font-family:monospace;font-size:12px">Server</div>
</div>
\`\`\`
```

**Customization per topic:**
- Kubernetes: Client → kubelet → container runtime → pod
- Networking: Client → DNS → CDN → load balancer → origin
- Database: App → connection pool → query planner → buffer → disk
- Messaging: Producer → broker → partition → consumer

---

### Component 2: State Machine with Clickable Transitions

**File:** `/data/components/state-machine.html-template`

**Pattern:**
```html
<div style="padding:16px">
  <style>
    .state { padding:12px; text-align:center; font-family:monospace; border-radius:4px; margin:12px 0; font-weight:bold; min-height:40px; display:flex; align-items:center; justify-content:center }
    .state-default { background:#1e3a5f; color:#e3eaf0 }
    .state-active { background:#00d4ff; color:#0b0e14 }
    .state-error { background:#ef4444; color:#ffffff }
    .state-warn { background:#fbbf24; color:#0b0e14 }
  </style>
  <div class="state state-default" id="state-display">INITIAL</div>
  <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap">
    <button onclick="setState('INITIAL')">Reset</button>
    <button onclick="setState('ACTIVE')">Activate</button>
    <button onclick="setState('ERROR')">Error</button>
  </div>
  <script>
    const stateMap = {
      'INITIAL': { bg: 'state-default', text: 'INITIAL' },
      'ACTIVE': { bg: 'state-active', text: 'ACTIVE' },
      'ERROR': { bg: 'state-error', text: 'ERROR' }
    };
    function setState(s) {
      const el = document.getElementById('state-display');
      el.className = 'state ' + stateMap[s].bg;
      el.textContent = stateMap[s].text;
    }
  </script>
</div>
```

**Use cases:**
- Circuit breaker: CLOSED → OPEN → HALF_OPEN → CLOSED
- Pod lifecycle: PENDING → RUNNING → SUCCEEDED/FAILED
- Raft: FOLLOWER → CANDIDATE → LEADER
- Connection: IDLE → ACTIVE → CLOSED

---

### Component 3: Slider Control (Scaling/Tuning)

**File:** `/data/components/slider-control.html-template`

**Pattern:**
```html
<div style="padding:16px">
  <style>
    .slider-container { display:flex; align-items:center; gap:12px }
    .slider-value { font-family:monospace; color:#34d399; min-width:50px; text-align:right }
  </style>
  <label style="color:#e3eaf0;display:block;margin-bottom:8px">{{label}}</label>
  <div class="slider-container">
    <input type="range" min="{{min}}" max="{{max}}" value="{{default}}" id="slider-{{id}}" style="flex:1">
    <span class="slider-value" id="value-{{id}}">{{default}}</span>
  </div>
  <script>
    const slider = document.getElementById('slider-{{id}}');
    const value = document.getElementById('value-{{id}}');
    slider.addEventListener('input', (e) => {
      value.textContent = e.target.value;
      // Optional: trigger custom logic
      onSliderChange('{{id}}', e.target.value);
    });
    function onSliderChange(id, val) {
      // Placeholder for custom behavior
    }
  </script>
</div>
```

**Use cases:**
- Throughput control (10-1000 req/sec)
- Latency injection (0-5000ms)
- Failure rate (0-100%)
- Cache hit rate (0-100%)
- Concurrent connections (1-10000)

---

### Component 4: Failure Cascade Simulator (Button-triggered)

**File:** `/data/components/failure-cascade.html-template`

**Pattern:**
```html
<div style="padding:16px">
  <style>
    .cascade-item { padding:8px; margin:4px 0; border-radius:4px; font-family:monospace; font-size:12px; transition:all 0.3s }
    .cascade-healthy { background:#1e5f3f; color:#34d399 }
    .cascade-warning { background:#5f4a1e; color:#fbbf24 }
    .cascade-failed { background:#5f1e1e; color:#ef4444 }
  </style>
  <div style="margin-bottom:12px">
    <button onclick="injectFailure()">Inject Failure</button>
    <button onclick="resetCascade()">Reset</button>
  </div>
  <div id="cascade-display">
    <div class="cascade-item cascade-healthy">Database: OK</div>
    <div class="cascade-item cascade-healthy">Connection Pool: OK (100/100)</div>
    <div class="cascade-item cascade-healthy">Timeouts: 0</div>
    <div class="cascade-item cascade-healthy">Retries: 0</div>
    <div class="cascade-item cascade-healthy">CPU: 20%</div>
  </div>
  <script>
    let cascadeState = [
      { name: 'Database', el: null, status: 'healthy' },
      { name: 'Connection Pool', el: null, status: 'healthy' },
      { name: 'Timeouts', el: null, status: 'healthy' },
      { name: 'Retries', el: null, status: 'healthy' },
      { name: 'CPU', el: null, status: 'healthy' }
    ];
    
    function injectFailure() {
      const els = document.querySelectorAll('#cascade-display .cascade-item');
      let delay = 300;
      // DB fails
      setTimeout(() => { updateCascade(0, 'failed', 'Database: TIMEOUT'); }, delay); delay += 300;
      // Pool exhausts
      setTimeout(() => { updateCascade(1, 'warning', 'Connection Pool: 98/100'); }, delay); delay += 300;
      setTimeout(() => { updateCascade(1, 'failed', 'Connection Pool: EXHAUSTED'); }, delay); delay += 300;
      // Timeouts spike
      setTimeout(() => { updateCascade(2, 'warning', 'Timeouts: 10'); }, delay); delay += 300;
      setTimeout(() => { updateCascade(2, 'failed', 'Timeouts: 1000+'); }, delay); delay += 300;
      // Retries amplify
      setTimeout(() => { updateCascade(3, 'warning', 'Retries: 500'); }, delay); delay += 300;
      setTimeout(() => { updateCascade(3, 'failed', 'Retries: 5000 (STORM)'); }, delay); delay += 300;
      // CPU spike
      setTimeout(() => { updateCascade(4, 'warning', 'CPU: 80%'); }, delay); delay += 300;
      setTimeout(() => { updateCascade(4, 'failed', 'CPU: 100% (SATURATED)'); }, delay);
    }
    
    function updateCascade(idx, status, text) {
      cascadeState[idx].status = status;
      const els = document.querySelectorAll('#cascade-display .cascade-item');
      els[idx].className = 'cascade-item cascade-' + status;
      els[idx].textContent = text;
    }
    
    function resetCascade() {
      const els = document.querySelectorAll('#cascade-display .cascade-item');
      els[0].className = 'cascade-item cascade-healthy'; els[0].textContent = 'Database: OK';
      els[1].className = 'cascade-item cascade-healthy'; els[1].textContent = 'Connection Pool: OK (100/100)';
      els[2].className = 'cascade-item cascade-healthy'; els[2].textContent = 'Timeouts: 0';
      els[3].className = 'cascade-item cascade-healthy'; els[3].textContent = 'Retries: 0';
      els[4].className = 'cascade-item cascade-healthy'; els[4].textContent = 'CPU: 20%';
    }
  </script>
</div>
```

**Use cases:**
- Database failure → timeout cascade
- Network partition → split brain
- Slow replica → replication lag
- Cache miss → thundering herd

---

### Component 5: 2D Topology Map (SVG)

**File:** `/data/components/topology-map.html-template`

**Pattern:**
```html
<svg width="100%" height="300" style="border:1px solid #1e2a3a;border-radius:4px;background:#0f1520" viewBox="0 0 800 300">
  <!-- Define nodes, connections with hover handlers -->
  <defs>
    <style>
      .topo-node { cursor:pointer; transition:all 0.2s }
      .topo-node:hover { filter:drop-shadow(0 0 8px #00d4ff) }
      .topo-edge { stroke:#1e2a3a; stroke-width:2; transition:stroke 0.2s }
      .topo-edge:hover { stroke:#00d4ff }
    </style>
  </defs>
  <!-- Edges (lines) -->
  <line class="topo-edge" x1="100" y1="150" x2="300" y2="150"/>
  <line class="topo-edge" x1="300" y1="150" x2="500" y2="100"/>
  <line class="topo-edge" x1="300" y1="150" x2="500" y2="200"/>
  <!-- Nodes (circles + text) -->
  <g class="topo-node">
    <circle cx="100" cy="150" r="30" fill="#1e3a5f" stroke="#00d4ff" stroke-width="2"/>
    <text x="100" y="155" text-anchor="middle" fill="#e3eaf0" font-size="12" font-family="monospace">Client</text>
  </g>
  <g class="topo-node">
    <circle cx="300" cy="150" r="30" fill="#1e3a5f" stroke="#00d4ff" stroke-width="2"/>
    <text x="300" y="155" text-anchor="middle" fill="#e3eaf0" font-size="12" font-family="monospace">LB</text>
  </g>
  <g class="topo-node">
    <circle cx="500" cy="100" r="30" fill="#1e3a5f" stroke="#00d4ff" stroke-width="2"/>
    <text x="500" y="105" text-anchor="middle" fill="#e3eaf0" font-size="12" font-family="monospace">A1</text>
  </g>
  <g class="topo-node">
    <circle cx="500" cy="200" r="30" fill="#1e3a5f" stroke="#00d4ff" stroke-width="2"/>
    <text x="500" y="205" text-anchor="middle" fill="#e3eaf0" font-size="12" font-family="monospace">A2</text>
  </g>
</svg>
```

**Use cases:**
- Kubernetes: kubelet → pod → container
- Kafka: producer → broker → partition → consumer
- Microservices: API gateway → service → database
- Distributed systems: node → node → node (with quorum highlighting)

---

### Component 6: Mini Observability Dashboard (CSS-only)

**File:** `/data/components/observability-panel.html-template`

**Pattern:**
```html
<div style="padding:16px;display:grid;grid-template-columns:1fr 1fr;gap:12px">
  <style>
    .metric-card { background:#0f1520; border:1px solid #1e2a3a; border-radius:4px; padding:12px }
    .metric-label { font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px }
    .metric-value { font-size:18px; font-family:monospace; color:#00d4ff; font-weight:bold }
    .metric-unit { font-size:12px; color:#64748b; margin-left:4px }
  </style>
  
  <div class="metric-card">
    <div class="metric-label">Throughput</div>
    <div class="metric-value">2.4K<span class="metric-unit">req/s</span></div>
  </div>
  
  <div class="metric-card">
    <div class="metric-label">Latency (p99)</div>
    <div class="metric-value">245<span class="metric-unit">ms</span></div>
  </div>
  
  <div class="metric-card">
    <div class="metric-label">Error Rate</div>
    <div class="metric-value">0.2<span class="metric-unit">%</span></div>
  </div>
  
  <div class="metric-card">
    <div class="metric-label">Cache Hit</div>
    <div class="metric-value">92.5<span class="metric-unit">%</span></div>
  </div>
</div>
```

**Customization:** Change metric names/values per topic

---

## Phase 2 Implementation Steps

1. **Create template files** (6 files, ~150 LOC each)
   - Write vanilla HTML+CSS+JS
   - Parameterize with `{{placeholders}}`
   - Test each in isolation

2. **Document templates** with examples
   - Show how to customize per topic
   - Provide 2-3 concrete examples per template

3. **Create `/data/components/` folder**
   - Organize: `request-flow.template`, `state-machine.template`, etc.

4. **Test all 6** in test-interactive.md or dedicated test file

---

## Phase 3: Embed Components in All .md Files

**Scope:** 303 files × 2-4 components = 600-1200 `html-live` blocks
**Effort:** 10 parallel agents, batch processing
**Output:** Enhanced .md files with interactive sections

### Agent Batch Strategy

| Agent | Folders | Component Focus | Files |
|-------|---------|---|---|
| B1 | 07-kubernetes, 06-devops | Request flow (pod lifecycle), CI/CD pipeline | 18 |
| B2 | 08-databases, 09-distributed-systems | State machine (WAL, Raft), topology (consistent hashing) | 16 |
| B3 | 11-networking, 10-messaging | Request flow (TCP, Kafka), topology (partition map) | 12 |
| B4 | 01-ai-ml, 02-data-engineering | Request flow (RAG pipeline), topology (Flink DAG) | 19 |
| B5 | 03-backend (go, java, python) | Request lifecycle, state machine (circuit breaker, GC) | 41 |
| B6 | 16-microservices, 17-software-architecture | State machine (service mesh), request flow | 16 |
| B7 | 05-cloud, 04-frontend, 12-operating-systems | Topology (VPC, component tree), request flow | 30 |
| B8 | 13-security, 14-sre-observability, 15-system-design | Slider (latency injection), observability panel | 50 |
| B9 | 18-20 (performance, testing, interviews) | Failure cascade, scaling evolution | 30 |
| B10 | 21-25, arch, cheat-sheets, remaining | Varied components | 71 |

### Per-File Enhancement Pattern

**For each .md file:**

1. **Identify topic** (Kubernetes, Kafka, Circuit Breaker, etc.)
2. **Select 2-4 relevant components** from template library
3. **Add after major sections:**
   - `### Visual: Request Flow` → insert request-flow component
   - `### Visual: State Machine` → insert state-machine component
   - `### Visual: Scaling` → insert slider component
   - `### Visual: Failure Scenario` → insert failure-cascade component

4. **Customize placeholders** for specific topic

5. **Preserve existing content** (only append)

### Example: Kubernetes Pod Lifecycle File

**Current content:**
```markdown
## Pod Lifecycle

Pod progresses through: Pending → Running → Succeeded/Failed.

[detailed explanation]
```

**Enhanced with component:**
```markdown
## Pod Lifecycle

Pod progresses through: Pending → Running → Succeeded/Failed.

[detailed explanation]

### Visual: Pod State Transitions
\`\`\`html-live
[state-machine component: PENDING, RUNNING, SUCCEEDED, FAILED states]
\`\`\`
```

---

## Phase 4: Standalone .html Simulation Files

**Scope:** 8 heavy-interaction worlds
**Effort:** 1-2 hours per file, heavy D3/Canvas usage
**Output:** `.html` files in `/data/` that appear in sidebar

### File 1: kafka-world.html

**Features:**
- Producers (left) sending messages
- Brokers (center) with partitions
- Consumers (right) reading offsets
- Animated message flow
- Lag visualization (distance between produced/consumed)
- Interactive: add producer, add consumer, trigger rebalance
- Tech: D3 + Canvas + SVG

**Interaction:**
- Slider: producer rate (msg/sec)
- Slider: consumer rate (msg/sec)
- Button: add slow consumer (lag buildup)
- Button: trigger rebalance
- Visualization: lag heatmap, partition assignment

---

### File 2: kubernetes-world.html

**Features:**
- Nodes (boxes) with resource bars
- Pods (circles) on nodes
- Scheduler allocating pods
- Rolling deployment visualization
- Autoscaler responding to load
- Tech: D3 force layout + SVG

**Interaction:**
- Slider: desired replicas (1-10)
- Button: trigger failure (random node dies)
- Button: start rolling deployment
- Visualization: pod distribution, node resources

---

### File 3: redis-world.html

**Features:**
- Memory region (left) showing data
- Cache slots with hot keys
- Hit/miss counter
- Eviction algorithm (LRU/LFU)
- Expiration timeline
- Tech: Canvas + SVG

**Interaction:**
- Slider: access pattern (random vs hot)
- Slider: memory size
- Button: trigger eviction
- Visualization: hot key heatmap, eviction decisions

---

### Files 4-8: Similar complexity
- distributed-systems.html (Raft, consensus, partitioning)
- tcp-packet-journey.html (packet flow, retransmission, congestion)
- database-internals.html (B+tree traversal, WAL, MVCC)
- failure-cascade.html (cascading failure simulator)
- request-lifecycle.html (full client-to-DB journey with latency)

---

## Verification Checklist

### Phase 2 Complete
- [ ] 6 template files created in `/data/components/`
- [ ] Each template has 2-3 concrete usage examples
- [ ] All 6 templates tested in test file
- [ ] No syntax errors in HTML/CSS/JS
- [ ] All interactive elements work (clicks, sliders, animations)

### Phase 3 Complete
- [ ] 10 agents run in parallel, no conflicts
- [ ] 303 .md files processed
- [ ] `grep -l 'html-live' data/**/*.md | wc -l` = ~300
- [ ] Spot-check 10 random files: animations work, no broken blocks
- [ ] Test read.html with enhanced files: renders correctly, scripts execute

### Phase 4 Complete
- [ ] 8 .html files in `/data/`
- [ ] Each appears in sidebar file tree
- [ ] Click opens in new tab
- [ ] Full interactivity works (sliders, buttons, D3 animations)
- [ ] No console errors

---

## Resource Estimate

| Phase | Files | Lines | Agents | Time |
|-------|-------|-------|--------|------|
| 1 | 3 (read.html, read.css, test-interactive.md) | 300 | 0 | ✅ Done |
| 2 | 6 templates | 1000 | 1 | 6 hours |
| 3 | 303 .md | ~3000 additions | 10 | 8 hours |
| 4 | 8 .html | 5000 | 2-3 | 16 hours |
| **Total** | **320** | **~9300** | **12-13** | **30 hours** |

---

## Success Criteria

✅ Every .md file has at least 2 interactive visualizations
✅ Animations are smooth (60fps CSS, no lag)
✅ Scripts execute without console errors
✅ Sliders/buttons responsive to interaction
✅ State machines update instantly on click
✅ Topology maps responsive and zoomable
✅ 8 simulators fully playable with rich interaction
✅ Platform feels "alive" — not static markdown

---

## Next Steps

1. **Phase 2 Start:** Create 6 template files
2. **Phase 2 Test:** Verify all templates work
3. **Phase 3 Prepare:** Design agent prompts for batch processing
4. **Phase 3 Execute:** Launch 10 parallel agents
5. **Phase 4:** Build simulation files
6. **Final Verification:** Audit all 303 files + 8 simulators

---

## Files Created So Far

- ✅ `/data/read.html` (modified) — html-live block support
- ✅ `/data/read.css` (modified) — .html-live-block styling
- ✅ `/data/test-interactive.md` (created) — proof of concept
- 📋 `/data/INTERACTIVE_PLATFORM_ROADMAP.md` (this file)

## Next Files to Create

- `/data/components/request-flow.template`
- `/data/components/state-machine.template`
- `/data/components/slider-control.template`
- `/data/components/failure-cascade.template`
- `/data/components/topology-map.template`
- `/data/components/observability-panel.template`
- (8 .html simulation files)

---

**Status:** Ready to proceed to Phase 2. Template creation can begin immediately.
