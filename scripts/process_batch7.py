#!/usr/bin/env python3
"""
Phase 3 Batch 7: Process and embed interactive components
This script is self-contained and will be invoked directly.
"""
import os
import re
from pathlib import Path

def append_to_file(file_path, content):
    """Append content to file"""
    with open(file_path, 'a') as f:
        f.write('\n' + content)

# Component HTML snippets
COMPONENTS = {
    'state_machine_lc': '''## Interactive Component: Component Lifecycle State Machine

```html-live
<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.state-machine-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px;letter-spacing:1px}.state-demo{text-align:center}.state-display{font-size:18px;font-family:monospace;padding:16px;border-radius:4px;margin:16px 0;color:#0b0e14;font-weight:bold;min-height:50px;display:flex;align-items:center;justify-content:center;border:2px solid currentColor}.state-mount{background:#60a5fa;border-color:#3b82f6}.state-update{background:#fbbf24;border-color:#f59e0b}.state-unmount{background:#ef4444;border-color:#dc2626}.state-buttons{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:16px}.state-button{padding:8px 16px;border:1px solid #00d4ff;background:#1e3a5f;color:#00d4ff;border-radius:4px;cursor:pointer;font-family:monospace;font-size:12px;transition:all 0.2s}.state-button:hover{background:#2a5a8f;box-shadow:0 0 8px #00d4ff}</style>
  <div class="state-machine-title">React Component Lifecycle</div>
  <div class="state-demo">
    <div class="state-display state-mount" id="lc-display">MOUNT</div>
    <div class="state-buttons">
      <button class="state-button" onclick="setLcState('MOUNT', lcMap)">Mount</button>
      <button class="state-button" onclick="setLcState('UPDATE', lcMap)">Update</button>
      <button class="state-button" onclick="setLcState('UNMOUNT', lcMap)">Unmount</button>
    </div>
  </div>
  <script>
    const lcMap = {
      'MOUNT': { label: 'MOUNT', class: 'state-mount' },
      'UPDATE': { label: 'UPDATE', class: 'state-update' },
      'UNMOUNT': { label: 'UNMOUNT', class: 'state-unmount' }
    };
    function setLcState(state, sm) {
      const display = document.getElementById('lc-display');
      const info = sm[state];
      display.textContent = info.label;
      display.className = 'state-display ' + info.class;
    }
  </script>
</div>
```''',

    'request_flow_api': '''## Interactive Component: API Request Flow

```html-live
<div style="display:flex;flex-direction:column;align-items:center;gap:8px;padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>@keyframes flow-pulse{0%,100%{opacity:.3;transform:translateY(0)}50%{opacity:1;transform:translateY(-2px)}}.flow-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:8px;letter-spacing:1px}.flow-node{display:inline-block;padding:8px 16px;border-radius:4px;font-size:12px;font-family:monospace;color:#e3eaf0;background:#1e3a5f;border:1px solid #00d4ff}.flow-arrow{color:#00d4ff;font-size:16px;animation:flow-pulse 1.5s infinite;font-weight:bold}</style>
  <div class="flow-title">HTTP Request Flow</div>
  <div style="display:flex;flex-direction:column;align-items:center;gap:6px">
    <div class="flow-node">Client Browser</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">DNS Resolver</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Load Balancer</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">API Server</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Database</div>
  </div>
</div>
```''',

    'observability_panel': '''## Interactive Component: Performance Metrics

```html-live
<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.obs-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px;letter-spacing:1px}.obs-grid{display:grid;grid-template-columns:repeat(auto-fit, minmax(150px, 1fr));gap:12px}.obs-card{padding:12px;background:#1a2332;border:1px solid #1e3a5f;border-radius:4px;display:flex;flex-direction:column;align-items:center;transition:all 0.3s}.obs-card:hover{border-color:#00d4ff;box-shadow:0 0 8px rgba(0, 212, 255, 0.3)}.obs-label{color:#a3aab8;font-family:monospace;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px}.obs-value{font-family:monospace;font-size:20px;font-weight:bold;margin-bottom:4px;letter-spacing:0.5px}.obs-unit{color:#a3aab8;font-family:monospace;font-size:10px;text-transform:uppercase}.metric-healthy{color:#34d399}.metric-warning{color:#fbbf24}.metric-critical{color:#ef4444}</style>
  <div class="obs-title">Component Render Metrics</div>
  <div class="obs-grid">
    <div class="obs-card"><div class="obs-label">Renders/sec</div><div class="obs-value metric-healthy">24</div><div class="obs-unit">renders</div></div>
    <div class="obs-card"><div class="obs-label">Avg Render</div><div class="obs-value metric-healthy">3.2</div><div class="obs-unit">ms</div></div>
    <div class="obs-card"><div class="obs-label">Components</div><div class="obs-value metric-healthy">145</div><div class="obs-unit">mounted</div></div>
    <div class="obs-card"><div class="obs-label">Memory</div><div class="obs-value metric-healthy">24</div><div class="obs-unit">MB</div></div>
  </div>
</div>
```''',

    'failure_cascade': '''## Interactive Component: Error Propagation Chain

```html-live
<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.cascade-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px;letter-spacing:1px}.cascade-stages{display:flex;flex-direction:column;gap:12px;margin-bottom:16px}.cascade-stage{display:flex;align-items:center;gap:12px}.cascade-label{color:#e3eaf0;font-family:monospace;font-size:12px;min-width:140px}.cascade-indicator{width:24px;height:24px;border-radius:4px;background:#34d399;border:2px solid #22c55e;transition:all 0.3s}.cascade-indicator.failing{background:#ef4444;border-color:#dc2626;box-shadow:0 0 12px #ef4444;animation:cascade-fail 0.6s ease-out}@keyframes cascade-fail{0%{transform:scale(1);opacity:1}100%{transform:scale(1.2);opacity:0.8}}.cascade-controls{display:flex;gap:8px;flex-wrap:wrap}.cascade-button{padding:8px 16px;border:1px solid #00d4ff;background:#1e3a5f;color:#00d4ff;border-radius:4px;cursor:pointer;font-family:monospace;font-size:12px;transition:all 0.2s}.cascade-button:hover{background:#2a5a8f;box-shadow:0 0 8px #00d4ff}</style>
  <div class="cascade-title">Error Cascade in React</div>
  <div class="cascade-stages">
    <div class="cascade-stage"><span class="cascade-label">Component Throws</span><div class="cascade-indicator" data-stage="throw"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Error Boundary</span><div class="cascade-indicator" data-stage="boundary"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Children Unmount</span><div class="cascade-indicator" data-stage="unmount"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Fallback Render</span><div class="cascade-indicator" data-stage="fallback"></div></div>
  </div>
  <div class="cascade-controls">
    <button class="cascade-button" onclick="startCascade()">Inject Error</button>
    <button class="cascade-button" onclick="resetCascade()">Reset</button>
  </div>
  <script>
    function startCascade() {
      const stages = document.querySelectorAll('[data-stage]');
      let delay = 0;
      stages.forEach((stage) => {
        setTimeout(() => { stage.classList.add('failing'); }, delay);
        delay += 300;
      });
    }
    function resetCascade() {
      document.querySelectorAll('[data-stage]').forEach((stage) => {
        stage.classList.remove('failing');
      });
    }
  </script>
</div>
```''',

    'slider_control': '''## Interactive Component: Performance Tuning

```html-live
<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.slider-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:12px;letter-spacing:1px}.slider-container{display:flex;flex-direction:column;gap:12px}.slider-label{color:#e3eaf0;font-family:monospace;font-size:12px}.slider-wrapper{display:flex;align-items:center;gap:12px}.slider-input{flex:1;height:6px;border-radius:3px;background:#1e3a5f;outline:none;-webkit-appearance:none;appearance:none}.slider-input::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:18px;height:18px;border-radius:50%;background:#00d4ff;cursor:pointer;box-shadow:0 0 8px #00d4ff;border:2px solid #0b0e14}.slider-input::-moz-range-thumb{width:18px;height:18px;border-radius:50%;background:#00d4ff;cursor:pointer;box-shadow:0 0 8px #00d4ff;border:2px solid #0b0e14}.slider-value{font-family:monospace;color:#34d399;min-width:80px;text-align:right;font-size:12px;font-weight:bold}</style>
  <div class="slider-title">Render Batch Configuration</div>
  <div class="slider-container">
    <label class="slider-label">Batch Size (items per frame):</label>
    <div class="slider-wrapper">
      <input type="range" min="1" max="100" value="10" class="slider-input" id="batch-slider">
      <span class="slider-value" id="batch-value">10 items</span>
    </div>
  </div>
  <script>
    const slider = document.getElementById('batch-slider');
    const value = document.getElementById('batch-value');
    slider.addEventListener('input', (e) => { value.textContent = e.target.value + ' items'; });
  </script>
</div>
```'''
}

CLOUD_COMPONENTS = {
    'state_machine_cb': '''## Interactive Component: Service State Machine

```html-live
<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.state-machine-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px;letter-spacing:1px}.state-demo{text-align:center}.state-display{font-size:18px;font-family:monospace;padding:16px;border-radius:4px;margin:16px 0;color:#0b0e14;font-weight:bold;min-height:50px;display:flex;align-items:center;justify-content:center;border:2px solid currentColor}.state-closed{background:#34d399;border-color:#22c55e}.state-open{background:#ef4444;border-color:#dc2626}.state-half-open{background:#fbbf24;border-color:#f59e0b}.state-buttons{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:16px}.state-button{padding:8px 16px;border:1px solid #00d4ff;background:#1e3a5f;color:#00d4ff;border-radius:4px;cursor:pointer;font-family:monospace;font-size:12px;transition:all 0.2s}.state-button:hover{background:#2a5a8f;box-shadow:0 0 8px #00d4ff}</style>
  <div class="state-machine-title">Lambda Container State</div>
  <div class="state-demo">
    <div class="state-display state-closed" id="state-display">CLOSED</div>
    <div class="state-buttons">
      <button class="state-button" onclick="setState('CLOSED', stateMap)">Healthy</button>
      <button class="state-button" onclick="setState('OPEN', stateMap)">Failing</button>
      <button class="state-button" onclick="setState('HALF_OPEN', stateMap)">Recovery</button>
    </div>
  </div>
  <script>
    const stateMap = {
      'CLOSED': { label: 'CLOSED', class: 'state-closed' },
      'OPEN': { label: 'OPEN', class: 'state-open' },
      'HALF_OPEN': { label: 'HALF-OPEN', class: 'state-half-open' }
    };
    function setState(state, sm) {
      const display = document.getElementById('state-display');
      const info = sm[state];
      display.textContent = info.label;
      display.className = 'state-display ' + info.class;
    }
  </script>
</div>
```''',

    'cloud_request_flow': '''## Interactive Component: Lambda Invocation Path

```html-live
<div style="display:flex;flex-direction:column;align-items:center;gap:8px;padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>@keyframes flow-pulse{0%,100%{opacity:.3;transform:translateY(0)}50%{opacity:1;transform:translateY(-2px)}}.flow-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:8px;letter-spacing:1px}.flow-node{display:inline-block;padding:8px 16px;border-radius:4px;font-size:12px;font-family:monospace;color:#e3eaf0;background:#1e3a5f;border:1px solid #00d4ff}.flow-arrow{color:#00d4ff;font-size:16px;animation:flow-pulse 1.5s infinite;font-weight:bold}</style>
  <div class="flow-title">Lambda Invocation Path</div>
  <div style="display:flex;flex-direction:column;align-items:center;gap:6px">
    <div class="flow-node">Request Event</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Cold Start Check</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Container Init</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Handler Invocation</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Warm Container Reuse</div>
  </div>
</div>
```''',

    'cloud_observability': '''## Interactive Component: Lambda Performance Metrics

```html-live
<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.obs-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px;letter-spacing:1px}.obs-grid{display:grid;grid-template-columns:repeat(auto-fit, minmax(150px, 1fr));gap:12px}.obs-card{padding:12px;background:#1a2332;border:1px solid #1e3a5f;border-radius:4px;display:flex;flex-direction:column;align-items:center;transition:all 0.3s}.obs-card:hover{border-color:#00d4ff;box-shadow:0 0 8px rgba(0, 212, 255, 0.3)}.obs-label{color:#a3aab8;font-family:monospace;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px}.obs-value{font-family:monospace;font-size:20px;font-weight:bold;margin-bottom:4px;letter-spacing:0.5px}.obs-unit{color:#a3aab8;font-family:monospace;font-size:10px;text-transform:uppercase}.metric-healthy{color:#34d399}.metric-warning{color:#fbbf24}.metric-critical{color:#ef4444}</style>
  <div class="obs-title">Lambda Performance</div>
  <div class="obs-grid">
    <div class="obs-card"><div class="obs-label">Invocations/sec</div><div class="obs-value metric-healthy">345</div><div class="obs-unit">inv/s</div></div>
    <div class="obs-card"><div class="obs-label">Cold Start %</div><div class="obs-value metric-warning">8.2</div><div class="obs-unit">%</div></div>
    <div class="obs-card"><div class="obs-label">Avg Duration</div><div class="obs-value metric-healthy">187</div><div class="obs-unit">ms</div></div>
    <div class="obs-card"><div class="obs-label">Error Rate</div><div class="obs-value metric-healthy">0.1</div><div class="obs-unit">%</div></div>
  </div>
</div>
```'''
}

# Frontend file mappings
FE_MAPPINGS = [
    ('fiber-architecture', ['state_machine_lc', 'request_flow_api']),
    ('rendering-performance', ['state_machine_lc', 'observability_panel', 'slider_control']),
    ('hooks-state', ['state_machine_lc', 'request_flow_api']),
    ('state-management', ['state_machine_lc', 'request_flow_api', 'failure_cascade']),
    ('component-patterns', ['state_machine_lc', 'request_flow_api']),
    ('routing-data-fetching', ['request_flow_api', 'observability_panel']),
    ('performance-optimization', ['slider_control', 'observability_panel']),
    ('concurrent', ['state_machine_lc', 'request_flow_api']),
    ('rsc', ['request_flow_api', 'observability_panel']),
    ('ssr', ['request_flow_api', 'failure_cascade']),
    ('animation', ['state_machine_lc', 'observability_panel']),
    ('design-system', ['state_machine_lc', 'observability_panel']),
    ('testing', ['failure_cascade', 'observability_panel']),
    ('accessibility', ['state_machine_lc', 'request_flow_api']),
    ('security', ['failure_cascade', 'request_flow_api']),
    ('websocket', ['request_flow_api', 'failure_cascade']),
    ('observability', ['observability_panel', 'request_flow_api']),
    ('build', ['state_machine_lc', 'observability_panel']),
    ('bundler', ['state_machine_lc', 'observability_panel']),
    ('browser-internals', ['state_machine_lc', 'request_flow_api']),
    ('networking', ['request_flow_api', 'observability_panel']),
    ('pwa', ['failure_cascade', 'observability_panel']),
    ('ai-powered', ['request_flow_api', 'observability_panel']),
    ('system-design', ['observability_panel', 'failure_cascade']),
]

# Cloud file mappings
CLOUD_MAPPINGS = [
    ('lambda', ['state_machine_cb', 'cloud_request_flow', 'slider_control', 'cloud_observability']),
    ('rds', ['failure_cascade', 'cloud_observability', 'slider_control']),
    ('ec2', ['state_machine_cb', 'cloud_observability']),
    ('ecs', ['state_machine_cb', 'cloud_observability']),
    ('eks', ['state_machine_cb', 'cloud_observability']),
    ('elasticache', ['slider_control', 'cloud_observability']),
    ('cloudwatch', ['cloud_observability', 'cloud_request_flow']),
]

def process_frontend():
    base = Path('/Users/ramyachowdary/Documents/prem-work/md-courses/data/04-frontend')
    count = 0

    for md_file in base.rglob('*.md'):
        filename = md_file.name.lower()

        if 'README' in md_file.name and str(md_file).count('/') > 5:
            continue

        # Check if already processed
        with open(md_file, 'r') as f:
            content = f.read()
            if 'Interactive Component' in content:
                continue

        # Find matching pattern
        for pattern, components in FE_MAPPINGS:
            if pattern in filename:
                # Append components
                for comp_key in components[:2]:
                    append_to_file(md_file, COMPONENTS[comp_key])

                count += 1
                print(f'✓ {md_file.name} ({", ".join(components[:2])})')
                break

    return count

def process_cloud():
    base = Path('/Users/ramyachowdary/Documents/prem-work/md-courses/data/05-cloud')
    count = 0

    for md_file in base.rglob('*.md'):
        filename = md_file.name.lower()

        if 'README' in md_file.name and str(md_file).count('/') > 5:
            continue

        # Check if already processed
        with open(md_file, 'r') as f:
            content = f.read()
            if 'Interactive Component' in content:
                continue

        # Find matching pattern
        for pattern, components in CLOUD_MAPPINGS:
            if pattern in filename:
                # Append components
                for comp_key in components[:2]:
                    append_to_file(md_file, CLOUD_COMPONENTS.get(comp_key, COMPONENTS.get(comp_key)))

                count += 1
                print(f'✓ {md_file.name} ({", ".join(components[:2])})')
                break

    return count

if __name__ == '__main__':
    print('Phase 3 Batch 7: Embedding Interactive Components\n')
    print('=' * 60)
    print('\nFRONTEND FILES:')
    print('-' * 60)
    fe = process_frontend()

    print('\nCLOUD FILES:')
    print('-' * 60)
    cl = process_cloud()

    print('\n' + '=' * 60)
    print(f'\nProcessed: {fe} frontend + {cl} cloud = {fe + cl} total')
    print('Ready for commit!')
