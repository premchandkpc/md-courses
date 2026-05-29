#!/usr/bin/env python3
"""
Phase 3 Batch 7: Embed interactive components in Cloud + Frontend files
"""

import os
import re
from pathlib import Path

# Component template mappings
COMPONENTS_DIR = "/Users/ramyachowdary/Documents/prem-work/md-courses/data/components"

# Read all templates
def read_template(name):
    path = f"{COMPONENTS_DIR}/{name}.template"
    with open(path) as f:
        content = f.read()
    return content

# Extract just the HTML examples from templates
def get_component_examples():
    examples = {}

    # REQUEST FLOW examples
    examples['request-flow'] = '''<div style="display:flex;flex-direction:column;align-items:center;gap:8px;padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>@keyframes flow-pulse{0%,100%{opacity:.3;transform:translateY(0)}50%{opacity:1;transform:translateY(-2px)}}.flow-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:8px;letter-spacing:1px}.flow-node{display:inline-block;padding:8px 16px;border-radius:4px;font-size:12px;font-family:monospace;color:#e3eaf0;background:#1e3a5f;border:1px solid #00d4ff}.flow-arrow{color:#00d4ff;font-size:16px;animation:flow-pulse 1.5s infinite;font-weight:bold}</style>
  <div class="flow-title">${TITLE}</div>
  <div style="display:flex;flex-direction:column;align-items:center;gap:6px">
    ${STEPS}
  </div>
</div>'''

    # STATE MACHINE examples
    examples['state-machine-circuit-breaker'] = '''<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.state-machine-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px;letter-spacing:1px}.state-demo{text-align:center}.state-display{font-size:18px;font-family:monospace;padding:16px;border-radius:4px;margin:16px 0;color:#0b0e14;font-weight:bold;min-height:50px;display:flex;align-items:center;justify-content:center;border:2px solid currentColor}.state-closed{background:#34d399;border-color:#22c55e}.state-open{background:#ef4444;border-color:#dc2626}.state-half-open{background:#fbbf24;border-color:#f59e0b}.state-buttons{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:16px}.state-button{padding:8px 16px;border:1px solid #00d4ff;background:#1e3a5f;color:#00d4ff;border-radius:4px;cursor:pointer;font-family:monospace;font-size:12px;transition:all 0.2s}.state-button:hover{background:#2a5a8f;box-shadow:0 0 8px #00d4ff}</style>
  <div class="state-machine-title">${TITLE}</div>
  <div class="state-demo">
    <div class="state-display state-closed" id="state-display">${INITIAL_STATE}</div>
    <div class="state-buttons">
      ${BUTTONS}
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
</div>'''

    # STATE MACHINE - Component Lifecycle
    examples['state-machine-lifecycle'] = '''<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.state-machine-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px;letter-spacing:1px}.state-demo{text-align:center}.state-display{font-size:16px;font-family:monospace;padding:14px;border-radius:4px;margin:16px 0;color:#0b0e14;font-weight:bold;min-height:45px;display:flex;align-items:center;justify-content:center;border:2px solid currentColor}.state-mount{background:#60a5fa;border-color:#3b82f6}.state-update{background:#fbbf24;border-color:#f59e0b}.state-unmount{background:#ef4444;border-color:#dc2626}.state-buttons{display:flex;gap:6px;justify-content:center;flex-wrap:wrap;margin-top:14px}.state-button{padding:6px 12px;border:1px solid #00d4ff;background:#1e3a5f;color:#00d4ff;border-radius:4px;cursor:pointer;font-family:monospace;font-size:11px;transition:all 0.2s}.state-button:hover{background:#2a5a8f;box-shadow:0 0 8px #00d4ff}</style>
  <div class="state-machine-title">${TITLE}</div>
  <div class="state-demo">
    <div class="state-display state-mount" id="lc-display">${INITIAL_STATE}</div>
    <div class="state-buttons">
      ${BUTTONS}
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
</div>'''

    # FAILURE CASCADE
    examples['failure-cascade'] = '''<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.cascade-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px;letter-spacing:1px}.cascade-stages{display:flex;flex-direction:column;gap:12px;margin-bottom:16px}.cascade-stage{display:flex;align-items:center;gap:12px}.cascade-label{color:#e3eaf0;font-family:monospace;font-size:12px;min-width:140px}.cascade-indicator{width:24px;height:24px;border-radius:4px;background:#34d399;border:2px solid #22c55e;transition:all 0.3s}.cascade-indicator.failing{background:#ef4444;border-color:#dc2626;box-shadow:0 0 12px #ef4444;animation:cascade-fail 0.6s ease-out}@keyframes cascade-fail{0%{transform:scale(1);opacity:1}100%{transform:scale(1.2);opacity:0.8}}.cascade-controls{display:flex;gap:8px;flex-wrap:wrap}.cascade-button{padding:8px 16px;border:1px solid #00d4ff;background:#1e3a5f;color:#00d4ff;border-radius:4px;cursor:pointer;font-family:monospace;font-size:12px;transition:all 0.2s}.cascade-button:hover{background:#2a5a8f;box-shadow:0 0 8px #00d4ff}</style>
  <div class="cascade-title">${TITLE}</div>
  <div class="cascade-stages">
    ${STAGES}
  </div>
  <div class="cascade-controls">
    <button class="cascade-button" onclick="startCascade()">Inject Failure</button>
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
</div>'''

    # TOPOLOGY MAP
    examples['topology-map'] = '''<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.topology-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:12px;letter-spacing:1px}.topology-svg{width:100%;max-width:600px;height:300px;background:#1a2332;border:1px solid #1e3a5f;border-radius:4px}.topo-edge{stroke:#1e3a5f;stroke-width:2}.topo-edge.active{stroke:#00d4ff;opacity:0.8}.topo-legend{display:flex;gap:16px;margin-top:12px;font-size:12px;color:#e3eaf0;font-family:monospace;flex-wrap:wrap}.legend-item{display:flex;align-items:center;gap:6px}.legend-color{width:16px;height:16px;border-radius:2px}</style>
  <div class="topology-title">${TITLE}</div>
  <svg class="topology-svg" viewBox="0 0 600 300">
    <defs>
      <marker id="arrow${ID}" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
        <polygon points="0 0, 10 3, 0 6" fill="#1e3a5f"/>
      </marker>
    </defs>
    ${SVG_CONTENT}
  </svg>
  <div class="topo-legend">
    ${LEGEND}
  </div>
</div>'''

    # OBSERVABILITY PANEL
    examples['observability-panel'] = '''<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.obs-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px;letter-spacing:1px}.obs-grid{display:grid;grid-template-columns:repeat(auto-fit, minmax(150px, 1fr));gap:12px}.obs-card{padding:12px;background:#1a2332;border:1px solid #1e3a5f;border-radius:4px;display:flex;flex-direction:column;align-items:center;transition:all 0.3s}.obs-card:hover{border-color:#00d4ff;box-shadow:0 0 8px rgba(0, 212, 255, 0.3)}.obs-label{color:#a3aab8;font-family:monospace;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px}.obs-value{font-family:monospace;font-size:20px;font-weight:bold;margin-bottom:4px;letter-spacing:0.5px}.obs-unit{color:#a3aab8;font-family:monospace;font-size:10px;text-transform:uppercase}.metric-healthy{color:#34d399}.metric-warning{color:#fbbf24}.metric-critical{color:#ef4444}</style>
  <div class="obs-title">${TITLE}</div>
  <div class="obs-grid">
    ${METRICS}
  </div>
</div>'''

    # SLIDER CONTROL
    examples['slider-control'] = '''<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.slider-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:12px;letter-spacing:1px}.slider-container{display:flex;flex-direction:column;gap:12px}.slider-label{color:#e3eaf0;font-family:monospace;font-size:12px}.slider-wrapper{display:flex;align-items:center;gap:12px}.slider-input{flex:1;height:6px;border-radius:3px;background:#1e3a5f;outline:none;-webkit-appearance:none;appearance:none}.slider-input::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:18px;height:18px;border-radius:50%;background:#00d4ff;cursor:pointer;box-shadow:0 0 8px #00d4ff;border:2px solid #0b0e14}.slider-input::-moz-range-thumb{width:18px;height:18px;border-radius:50%;background:#00d4ff;cursor:pointer;box-shadow:0 0 8px #00d4ff;border:2px solid #0b0e14}.slider-value{font-family:monospace;color:#34d399;min-width:80px;text-align:right;font-size:12px;font-weight:bold}</style>
  <div class="slider-title">${TITLE}</div>
  <div class="slider-container">
    <label class="slider-label">${LABEL}</label>
    <div class="slider-wrapper">
      <input type="range" min="${MIN}" max="${MAX}" value="${VALUE}" class="slider-input" id="param-${ID}">
      <span class="slider-value" id="val-${ID}">${VALUE} ${UNIT}</span>
    </div>
  </div>
  <script>
    const slider = document.getElementById('param-${ID}');
    const valueDisplay = document.getElementById('val-${ID}');
    slider.addEventListener('input', (e) => {
      valueDisplay.textContent = e.target.value + ' ${UNIT}';
    });
  </script>
</div>'''

    return examples

# File-to-component mapping
FRONTEND_MAPPINGS = {
    # Component Lifecycle
    r'components-jsx|fiber-architecture|lifecycle': ['state-machine-lifecycle', 'request-flow'],
    r'rendering-performance': ['state-machine-lifecycle', 'observability-panel', 'slider-control'],
    r'hooks-state': ['state-machine-lifecycle', 'request-flow', 'observability-panel'],
    r'hooks.*patterns|custom-hooks': ['state-machine-lifecycle', 'request-flow'],
    r'state-management': ['state-machine-lifecycle', 'request-flow', 'failure-cascade'],
    r'component-patterns': ['state-machine-lifecycle', 'request-flow'],
    r'routing|data-fetching': ['request-flow', 'observability-panel'],
    r'form.*validation|testing.*form': ['state-machine-lifecycle', 'failure-cascade'],
    r'performance-optimization|render-optimization': ['slider-control', 'observability-panel'],
    r'concurrent|streaming': ['state-machine-lifecycle', 'request-flow'],
    r'rsc|server.*component': ['request-flow', 'observability-panel'],
    r'ssr|nextjs|app-router|hydration': ['request-flow', 'failure-cascade'],
    r'animation': ['state-machine-lifecycle', 'observability-panel'],
    r'design-system': ['state-machine-lifecycle', 'observability-panel'],
    r'testing': ['failure-cascade', 'observability-panel'],
    r'accessibility': ['state-machine-lifecycle', 'request-flow'],
    r'security': ['failure-cascade', 'request-flow'],
    r'websocket|realtime': ['request-flow', 'failure-cascade'],
    r'microfrontend': ['topology-map', 'request-flow'],
    r'system-design': ['topology-map', 'request-flow', 'observability-panel'],
    r'observability': ['observability-panel', 'request-flow'],
    r'build|bundler': ['state-machine-lifecycle', 'observability-panel', 'slider-control'],
    r'browser-internals|javascript-engine': ['state-machine-lifecycle', 'request-flow'],
    r'networking': ['request-flow', 'observability-panel'],
    r'pwa|offline': ['failure-cascade', 'observability-panel'],
    r'ai-powered|streaming-llm|agentic': ['request-flow', 'observability-panel'],
    r'ml|frontend-ml': ['state-machine-lifecycle', 'observability-panel'],
    r'architecture-pattern': ['topology-map', 'state-machine-lifecycle'],
    r'case-study|production|scaling': ['observability-panel', 'failure-cascade'],
    r'debugging|interview': ['state-machine-lifecycle', 'request-flow'],
}

CLOUD_MAPPINGS = {
    # Lambda/Serverless
    r'lambda': ['request-flow', 'state-machine-circuit-breaker', 'slider-control', 'observability-panel'],
    # VPC/Networking
    r'networking|vpc': ['topology-map', 'failure-cascade'],
    # EC2
    r'ec2': ['topology-map', 'observability-panel', 'state-machine-circuit-breaker'],
    # RDS/Database
    r'rds|database': ['failure-cascade', 'observability-panel', 'slider-control'],
    # Cache/ElastiCache
    r'elasticache|cache': ['slider-control', 'observability-panel'],
    # S3/Storage
    r's3|storage': ['observability-panel', 'slider-control'],
    # CloudWatch/Monitoring
    r'cloudwatch|observability|monitoring': ['observability-panel', 'request-flow'],
    # ECS/Container
    r'ecs|container': ['topology-map', 'state-machine-circuit-breaker', 'observability-panel'],
    # EKS/Kubernetes
    r'eks|kubernetes': ['topology-map', 'state-machine-circuit-breaker', 'observability-panel'],
    # IAM/Auth
    r'iam|auth|security': ['failure-cascade', 'state-machine-circuit-breaker'],
    # Load Balancing
    r'load-balanc': ['topology-map', 'observability-panel', 'slider-control'],
    # Auto Scaling
    r'auto.*scal|scaling': ['slider-control', 'failure-cascade', 'observability-panel'],
    # CI/CD
    r'cicd|deployment|pipeline': ['request-flow', 'state-machine-circuit-breaker'],
}

def match_file_to_components(filename, is_cloud=False):
    """Match file to appropriate components"""
    mappings = CLOUD_MAPPINGS if is_cloud else FRONTEND_MAPPINGS

    for pattern, components in mappings.items():
        if re.search(pattern, filename.lower()):
            return components[:2]  # Return top 2-3

    # Default fallback
    if is_cloud:
        return ['observability-panel', 'request-flow']
    else:
        return ['state-machine-lifecycle', 'observability-panel']

def generate_frontend_component(component_type, filename):
    """Generate context-specific frontend components"""
    examples = get_component_examples()

    if component_type == 'state-machine-lifecycle':
        buttons = '''<button class="state-button" onclick="setLcState('MOUNT', lcMap)">Mount</button>
      <button class="state-button" onclick="setLcState('UPDATE', lcMap)">Update</button>
      <button class="state-button" onclick="setLcState('UNMOUNT', lcMap)">Unmount</button>'''

        html = examples['state-machine-lifecycle']
        html = html.replace('${TITLE}', 'React Component Lifecycle')
        html = html.replace('${INITIAL_STATE}', 'MOUNT')
        html = html.replace('${BUTTONS}', buttons)
        return html

    elif component_type == 'request-flow':
        if 'routing' in filename.lower() or 'data-fetch' in filename.lower():
            steps = '''<div class="flow-node">User Navigates</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Router Match</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Component Render</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">useEffect Trigger</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">API Fetch</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">State Update</div>'''
            title = 'Route to Data Flow'
        elif 'event' in filename.lower():
            steps = '''<div class="flow-node">User Event</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Event Handler</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">State Update</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Re-render</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">DOM Update</div>'''
            title = 'Event Flow (React)'
        else:
            steps = '''<div class="flow-node">Component Mount</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Render Phase</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Commit Phase</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">DOM Mutation</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">useLayoutEffect</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">useEffect Cleanup</div>'''
            title = 'Component Initialization Flow'

        html = examples['request-flow']
        html = html.replace('${TITLE}', title)
        html = html.replace('${STEPS}', steps)
        return html

    elif component_type == 'observability-panel':
        if 'performance' in filename.lower() or 'render' in filename.lower():
            metrics = '''<div class="obs-card">
      <div class="obs-label">FCP</div>
      <div class="obs-value metric-healthy">1.2</div>
      <div class="obs-unit">sec</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">LCP</div>
      <div class="obs-value metric-healthy">2.1</div>
      <div class="obs-unit">sec</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">CLS</div>
      <div class="obs-value metric-healthy">0.08</div>
      <div class="obs-unit">score</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">TTI</div>
      <div class="obs-value metric-healthy">3.4</div>
      <div class="obs-unit">sec</div>
    </div>'''
            title = 'Web Vitals Metrics'
        elif 'bundle' in filename.lower() or 'build' in filename.lower():
            metrics = '''<div class="obs-card">
      <div class="obs-label">Bundle Size</div>
      <div class="obs-value metric-healthy">242</div>
      <div class="obs-unit">KB</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Gzip Size</div>
      <div class="obs-value metric-healthy">68</div>
      <div class="obs-unit">KB</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Parse Time</div>
      <div class="obs-value metric-healthy">145</div>
      <div class="obs-unit">ms</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Build Time</div>
      <div class="obs-value metric-warning">8.2</div>
      <div class="obs-unit">sec</div>
    </div>'''
            title = 'Build & Bundle Metrics'
        else:
            metrics = '''<div class="obs-card">
      <div class="obs-label">Renders/sec</div>
      <div class="obs-value metric-healthy">24</div>
      <div class="obs-unit">renders</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Avg Render Time</div>
      <div class="obs-value metric-healthy">3.2</div>
      <div class="obs-unit">ms</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Mounted Components</div>
      <div class="obs-value metric-healthy">145</div>
      <div class="obs-unit">comps</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Memory Used</div>
      <div class="obs-value metric-healthy">24</div>
      <div class="obs-unit">MB</div>
    </div>'''
            title = 'Component Render Metrics'

        html = examples['observability-panel']
        html = html.replace('${TITLE}', title)
        html = html.replace('${METRICS}', metrics)
        return html

    elif component_type == 'slider-control':
        slider_id = 'perf'
        if 'performance' in filename.lower():
            label = 'Batch Size (for rendering):'
            min_val = '1'
            max_val = '100'
            value = '10'
            unit = 'items'
            title = 'Render Batch Configuration'
            slider_id = 'batch'
        elif 'bundle' in filename.lower():
            label = 'Bundle Optimization Level:'
            min_val = '0'
            max_val = '5'
            value = '3'
            unit = 'level'
            title = 'Build Optimization'
            slider_id = 'optim'
        else:
            label = 'Component Tree Depth:'
            min_val = '1'
            max_val = '50'
            value = '10'
            unit = 'levels'
            title = 'Hierarchy Configuration'
            slider_id = 'depth'

        html = examples['slider-control']
        html = html.replace('${TITLE}', title)
        html = html.replace('${LABEL}', label)
        html = html.replace('${MIN}', min_val)
        html = html.replace('${MAX}', max_val)
        html = html.replace('${VALUE}', value)
        html = html.replace('${UNIT}', unit)
        html = html.replace('${ID}', slider_id)
        return html

    elif component_type == 'failure-cascade':
        if 'error' in filename.lower() or 'test' in filename.lower():
            stages = '''<div class="cascade-stage"><span class="cascade-label">Component Throws</span><div class="cascade-indicator" data-stage="throw"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Error Boundary</span><div class="cascade-indicator" data-stage="boundary"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Children Unmount</span><div class="cascade-indicator" data-stage="unmount"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Fallback Render</span><div class="cascade-indicator" data-stage="fallback"></div></div>'''
            title = 'Error Propagation Chain'
        else:
            stages = '''<div class="cascade-stage"><span class="cascade-label">Parent Error</span><div class="cascade-indicator" data-stage="parent"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Child Updates Stop</span><div class="cascade-indicator" data-stage="children"></div></div>
    <div class="cascade-stage"><span class="cascade-label">State Rollback</span><div class="cascade-indicator" data-stage="state"></div></div>
    <div class="cascade-stage"><span class="cascade-label">UI Frozen</span><div class="cascade-indicator" data-stage="ui"></div></div>'''
            title = 'Error Cascade in React'

        html = examples['failure-cascade']
        html = html.replace('${TITLE}', title)
        html = html.replace('${STAGES}', stages)
        return html

    return ''

def generate_cloud_component(component_type, filename):
    """Generate context-specific cloud components"""
    examples = get_component_examples()

    if component_type == 'state-machine-circuit-breaker':
        buttons = '''<button class="state-button" onclick="setState('CLOSED', stateMap)">Healthy</button>
      <button class="state-button" onclick="setState('OPEN', stateMap)">Failing</button>
      <button class="state-button" onclick="setState('HALF_OPEN', stateMap)">Recovery</button>'''

        title = 'Service State Machine'
        if 'lambda' in filename.lower():
            title = 'Lambda Container State'
        elif 'ec2' in filename.lower():
            title = 'EC2 Instance State'
        elif 'ecs' in filename.lower():
            title = 'ECS Task State'

        html = examples['state-machine-circuit-breaker']
        html = html.replace('${TITLE}', title)
        html = html.replace('${INITIAL_STATE}', 'CLOSED')
        html = html.replace('${BUTTONS}', buttons)
        return html

    elif component_type == 'request-flow':
        if 'lambda' in filename.lower():
            steps = '''<div class="flow-node">Request Event</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Lambda Cold Start</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Container Init</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Handler Invocation</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Warm Container Reuse</div>'''
            title = 'Lambda Invocation Path'
        elif 'cicd' in filename.lower() or 'deploy' in filename.lower() or 'pipeline' in filename.lower():
            steps = '''<div class="flow-node">Code Commit</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Build Phase</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Test Phase</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Push to Registry</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Deploy to Cluster</div>'''
            title = 'CI/CD Pipeline Flow'
        elif 'load' in filename.lower() or 'balancl' in filename.lower():
            steps = '''<div class="flow-node">Client Request</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Load Balancer</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Health Check</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Route to Instance</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Response Return</div>'''
            title = 'Load Balancer Request Flow'
        else:
            steps = '''<div class="flow-node">API Request</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Security Group</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Target Service</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Database Query</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Response</div>'''
            title = 'Cloud Request Flow'

        html = examples['request-flow']
        html = html.replace('${TITLE}', title)
        html = html.replace('${STEPS}', steps)
        return html

    elif component_type == 'observability-panel':
        if 'lambda' in filename.lower():
            metrics = '''<div class="obs-card">
      <div class="obs-label">Invocations/sec</div>
      <div class="obs-value metric-healthy">345</div>
      <div class="obs-unit">inv/s</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Cold Start %</div>
      <div class="obs-value metric-warning">8.2</div>
      <div class="obs-unit">%</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Avg Duration</div>
      <div class="obs-value metric-healthy">187</div>
      <div class="obs-unit">ms</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Error Rate</div>
      <div class="obs-value metric-healthy">0.1</div>
      <div class="obs-unit">%</div>
    </div>'''
            title = 'Lambda Performance'
        elif 'rds' in filename.lower():
            metrics = '''<div class="obs-card">
      <div class="obs-label">Queries/sec</div>
      <div class="obs-value metric-healthy">2,847</div>
      <div class="obs-unit">q/s</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Latency p99</div>
      <div class="obs-value metric-healthy">12.3</div>
      <div class="obs-unit">ms</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Connections</div>
      <div class="obs-value metric-warning">285</div>
      <div class="obs-unit">active</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Replication Lag</div>
      <div class="obs-value metric-healthy">0.8</div>
      <div class="obs-unit">sec</div>
    </div>'''
            title = 'RDS Metrics'
        elif 'cache' in filename.lower() or 'elasticache' in filename.lower():
            metrics = '''<div class="obs-card">
      <div class="obs-label">Hit Rate</div>
      <div class="obs-value metric-healthy">94.2</div>
      <div class="obs-unit">%</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Ops/sec</div>
      <div class="obs-value metric-healthy">56K</div>
      <div class="obs-unit">ops</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Memory Used</div>
      <div class="obs-value metric-warning">6.8</div>
      <div class="obs-unit">GB</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Evictions/sec</div>
      <div class="obs-value metric-healthy">2</div>
      <div class="obs-unit">evt/s</div>
    </div>'''
            title = 'Redis Cache Metrics'
        else:
            metrics = '''<div class="obs-card">
      <div class="obs-label">CPU Usage</div>
      <div class="obs-value metric-warning">68</div>
      <div class="obs-unit">%</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Memory Usage</div>
      <div class="obs-value metric-healthy">52</div>
      <div class="obs-unit">%</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Network I/O</div>
      <div class="obs-value metric-healthy">234</div>
      <div class="obs-unit">Mbps</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Availability</div>
      <div class="obs-value metric-healthy">99.99</div>
      <div class="obs-unit">%</div>
    </div>'''
            title = 'Cloud Service Metrics'

        html = examples['observability-panel']
        html = html.replace('${TITLE}', title)
        html = html.replace('${METRICS}', metrics)
        return html

    elif component_type == 'failure-cascade':
        if 'az' in filename.lower() or 'zone' in filename.lower():
            stages = '''<div class="cascade-stage"><span class="cascade-label">AZ-1 Failure</span><div class="cascade-indicator" data-stage="az1"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Health Check Fail</span><div class="cascade-indicator" data-stage="health"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Load Shift to AZ-2</span><div class="cascade-indicator" data-stage="shift"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Capacity Warning</span><div class="cascade-indicator" data-stage="cap"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Auto-Scale Trigger</span><div class="cascade-indicator" data-stage="scale"></div></div>'''
            title = 'Availability Zone Failure'
        else:
            stages = '''<div class="cascade-stage"><span class="cascade-label">Primary Service Down</span><div class="cascade-indicator" data-stage="primary"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Circuit Breaker Opens</span><div class="cascade-indicator" data-stage="circuit"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Retries Exhausted</span><div class="cascade-indicator" data-stage="retries"></div></div>
    <div class="cascade-stage"><span class="cascade-label">Dependent Services Error</span><div class="cascade-indicator" data-stage="depend"></div></div>
    <div class="cascade-stage"><span class="cascade-label">User Requests Fail</span><div class="cascade-indicator" data-stage="user"></div></div>'''
            title = 'Service Failure Cascade'

        html = examples['failure-cascade']
        html = html.replace('${TITLE}', title)
        html = html.replace('${STAGES}', stages)
        return html

    elif component_type == 'topology-map':
        if 'lambda' in filename.lower():
            svg_content = '''<!-- Lambda Invocation Sources -->
    <g><circle cx="100" cy="50" r="20" fill="#ff9900" stroke="#ff9900" stroke-width="1"/><text x="100" y="55" text-anchor="middle" fill="#0b0e14" font-size="10" font-family="monospace" font-weight="bold">API GW</text></g>
    <g><circle cx="300" cy="50" r="20" fill="#ff9900" stroke="#ff9900" stroke-width="1"/><text x="300" y="55" text-anchor="middle" fill="#0b0e14" font-size="10" font-family="monospace" font-weight="bold">S3</text></g>
    <g><circle cx="500" cy="50" r="20" fill="#ff9900" stroke="#ff9900" stroke-width="1"/><text x="500" y="55" text-anchor="middle" fill="#0b0e14" font-size="10" font-family="monospace" font-weight="bold">SNS</text></g>
    <!-- Lambda -->
    <g><rect x="200" y="130" width="200" height="60" rx="4" fill="#1e3a5f" stroke="#ff9900" stroke-width="2"/><text x="300" y="150" text-anchor="middle" fill="#e3eaf0" font-size="12" font-family="monospace" font-weight="bold">Lambda Handler</text><text x="300" y="170" text-anchor="middle" fill="#a3aab8" font-size="10" font-family="monospace">~128MB-10GB</text></g>
    <!-- Downstream -->
    <g><rect x="100" y="240" width="80" height="40" rx="4" fill="#1e3a5f" stroke="#00d4ff" stroke-width="1"/><text x="140" y="265" text-anchor="middle" fill="#e3eaf0" font-size="10" font-family="monospace">DynamoDB</text></g>
    <g><rect x="260" y="240" width="80" height="40" rx="4" fill="#1e3a5f" stroke="#00d4ff" stroke-width="1"/><text x="300" y="265" text-anchor="middle" fill="#e3eaf0" font-size="10" font-family="monospace">RDS</text></g>
    <g><rect x="420" y="240" width="80" height="40" rx="4" fill="#1e3a5f" stroke="#00d4ff" stroke-width="1"/><text x="460" y="265" text-anchor="middle" fill="#e3eaf0" font-size="10" font-family="monospace">S3</text></g>
    <!-- Edges -->
    <line stroke="#ff9900" stroke-width="1.5" x1="100" y1="70" x2="240" y2="130"/>
    <line stroke="#ff9900" stroke-width="1.5" x1="300" y1="70" x2="300" y2="130"/>
    <line stroke="#ff9900" stroke-width="1.5" x1="500" y1="70" x2="360" y2="130"/>
    <line stroke="#00d4ff" stroke-width="1.5" x1="240" y1="190" x2="140" y2="240"/>
    <line stroke="#00d4ff" stroke-width="1.5" x1="300" y1="190" x2="300" y2="240"/>
    <line stroke="#00d4ff" stroke-width="1.5" x1="360" y1="190" x2="460" y2="240"/>'''
            title = 'Lambda Topology'
            legend = '''<div class="legend-item"><div style="width:14px;height:14px;background:#ff9900;border-radius:50%"></div><span>Trigger Source</span></div>
    <div class="legend-item"><div style="width:14px;height:14px;background:#1e3a5f;border:1px solid #ff9900"></div><span>Lambda</span></div>
    <div class="legend-item"><div style="width:14px;height:14px;background:#1e3a5f;border:1px solid #00d4ff"></div><span>Resource</span></div>'''
        elif 'vpc' in filename.lower():
            svg_content = '''<!-- Internet Gateway -->
    <rect x="200" y="10" width="200" height="35" rx="4" fill="#1e3a5f" stroke="#34d399" stroke-width="2"/>
    <text x="300" y="35" text-anchor="middle" fill="#e3eaf0" font-size="11" font-family="monospace" font-weight="bold">Internet Gateway</text>
    <!-- VPC -->
    <rect x="50" y="70" width="500" height="220" rx="4" fill="none" stroke="#00d4ff" stroke-width="2" stroke-dasharray="5,5"/>
    <text x="60" y="90" fill="#00d4ff" font-size="11" font-family="monospace" font-weight="bold">VPC (10.0.0.0/16)</text>
    <!-- Subnets -->
    <rect x="70" y="110" width="210" height="160" rx="3" fill="none" stroke="#60a5fa" stroke-width="1"/>
    <text x="80" y="125" fill="#60a5fa" font-size="10" font-family="monospace">Public Subnet (AZ-A)</text>
    <rect x="320" y="110" width="210" height="160" rx="3" fill="none" stroke="#60a5fa" stroke-width="1"/>
    <text x="330" y="125" fill="#60a5fa" font-size="10" font-family="monospace">Private Subnet (AZ-B)</text>
    <!-- Instances -->
    <circle cx="175" cy="180" r="20" fill="#fbbf24" stroke="#fbbf24" stroke-width="1"/>
    <text x="175" y="185" text-anchor="middle" fill="#0b0e14" font-size="9" font-family="monospace" font-weight="bold">EC2-A1</text>
    <circle cx="175" cy="240" r="20" fill="#fbbf24" stroke="#fbbf24" stroke-width="1"/>
    <text x="175" y="245" text-anchor="middle" fill="#0b0e14" font-size="9" font-family="monospace" font-weight="bold">EC2-A2</text>
    <circle cx="425" cy="180" r="20" fill="#fbbf24" stroke="#fbbf24" stroke-width="1"/>
    <text x="425" y="185" text-anchor="middle" fill="#0b0e14" font-size="9" font-family="monospace" font-weight="bold">EC2-B1</text>
    <circle cx="425" cy="240" r="20" fill="#fbbf24" stroke="#fbbf24" stroke-width="1"/>
    <text x="425" y="245" text-anchor="middle" fill="#0b0e14" font-size="9" font-family="monospace" font-weight="bold">EC2-B2</text>
    <!-- Edges -->
    <line stroke="#34d399" stroke-width="1.5" x1="300" y1="45" x2="300" y2="70"/>
    <line stroke="#60a5fa" stroke-width="1" x1="300" y1="70" x2="175" y2="110"/>
    <line stroke="#60a5fa" stroke-width="1" x1="300" y1="70" x2="425" y2="110"/>'''
            title = 'VPC Topology with AZs'
            legend = '''<div class="legend-item"><div style="width:14px;height:14px;background:#34d399;border-radius:50%"></div><span>IGW</span></div>
    <div class="legend-item"><div style="width:14px;height:14px;background:#00d4ff;border:1px dashed #00d4ff"></div><span>VPC</span></div>
    <div class="legend-item"><div style="width:14px;height:14px;background:#60a5fa;border:1px solid #60a5fa"></div><span>Subnet</span></div>
    <div class="legend-item"><div style="width:14px;height:14px;background:#fbbf24;border-radius:50%"></div><span>EC2</span></div>'''
        elif 'ecs' in filename.lower():
            svg_content = '''<!-- ECS Cluster -->
    <rect x="50" y="10" width="500" height="280" rx="4" fill="none" stroke="#00d4ff" stroke-width="2" stroke-dasharray="5,5"/>
    <text x="60" y="30" fill="#00d4ff" font-size="11" font-family="monospace" font-weight="bold">ECS Cluster</text>
    <!-- EC2 Instance 1 -->
    <rect x="70" y="50" width="180" height="110" rx="3" fill="none" stroke="#fbbf24" stroke-width="1"/>
    <text x="80" y="70" fill="#fbbf24" font-size="10" font-family="monospace">EC2 Instance (AZ-A)</text>
    <g><rect x="85" y="85" width="70" height="35" rx="2" fill="#1e3a5f" stroke="#00d4ff" stroke-width="1"/><text x="120" y="107" text-anchor="middle" fill="#e3eaf0" font-size="9" font-family="monospace">Task-1</text></g>
    <g><rect x="165" y="85" width="70" height="35" rx="2" fill="#1e3a5f" stroke="#00d4ff" stroke-width="1"/><text x="200" y="107" text-anchor="middle" fill="#e3eaf0" font-size="9" font-family="monospace">Task-2</text></g>
    <!-- EC2 Instance 2 -->
    <rect x="300" y="50" width="180" height="110" rx="3" fill="none" stroke="#fbbf24" stroke-width="1"/>
    <text x="310" y="70" fill="#fbbf24" font-size="10" font-family="monospace">EC2 Instance (AZ-B)</text>
    <g><rect x="315" y="85" width="70" height="35" rx="2" fill="#1e3a5f" stroke="#00d4ff" stroke-width="1"/><text x="350" y="107" text-anchor="middle" fill="#e3eaf0" font-size="9" font-family="monospace">Task-3</text></g>
    <g><rect x="395" y="85" width="70" height="35" rx="2" fill="#1e3a5f" stroke="#00d4ff" stroke-width="1"/><text x="430" y="107" text-anchor="middle" fill="#e3eaf0" font-size="9" font-family="monospace">Task-4</text></g>
    <!-- Load Balancer -->
    <rect x="200" y="200" width="160" height="40" rx="3" fill="#1e3a5f" stroke="#34d399" stroke-width="2"/>
    <text x="280" y="225" text-anchor="middle" fill="#e3eaf0" font-size="11" font-family="monospace" font-weight="bold">ALB</text>
    <!-- Service -->
    <rect x="180" y="270" width="200" height="35" rx="3" fill="none" stroke="#60a5fa" stroke-width="1"/>
    <text x="280" y="293" text-anchor="middle" fill="#60a5fa" font-size="10" font-family="monospace">ECS Service</text>
    <!-- Edges -->
    <line stroke="#34d399" stroke-width="1.5" x1="280" y1="240" x2="280" y2="270"/>
    <line stroke="#60a5fa" stroke-width="1" x1="120" y1="160" x2="250" y2="200"/>
    <line stroke="#60a5fa" stroke-width="1" x1="380" y1="160" x2="310" y2="200"/>'''
            title = 'ECS Cluster Topology'
            legend = '''<div class="legend-item"><div style="width:14px;height:14px;background:#00d4ff;border:1px dashed #00d4ff"></div><span>Cluster</span></div>
    <div class="legend-item"><div style="width:14px;height:14px;background:#fbbf24;border:1px solid #fbbf24"></div><span>EC2</span></div>
    <div class="legend-item"><div style="width:14px;height:14px;background:#1e3a5f;border:1px solid #00d4ff"></div><span>Task</span></div>
    <div class="legend-item"><div style="width:14px;height:14px;background:#34d399;border-radius:2px"></div><span>LB</span></div>'''
        else:
            svg_content = '''<!-- Generic Cloud Architecture -->
    <rect x="200" y="10" width="200" height="40" rx="3" fill="#1e3a5f" stroke="#34d399" stroke-width="2"/>
    <text x="300" y="35" text-anchor="middle" fill="#e3eaf0" font-size="11" font-family="monospace">Load Balancer</text>
    <g><rect x="80" y="90" width="100" height="60" rx="3" fill="#1e3a5f" stroke="#00d4ff" stroke-width="1"/><text x="130" y="125" text-anchor="middle" fill="#e3eaf0" font-size="10" font-family="monospace">Service-A</text></g>
    <g><rect x="250" y="90" width="100" height="60" rx="3" fill="#1e3a5f" stroke="#00d4ff" stroke-width="1"/><text x="300" y="125" text-anchor="middle" fill="#e3eaf0" font-size="10" font-family="monospace">Service-B</text></g>
    <g><rect x="420" y="90" width="100" height="60" rx="3" fill="#1e3a5f" stroke="#00d4ff" stroke-width="1"/><text x="470" y="125" text-anchor="middle" fill="#e3eaf0" font-size="10" font-family="monospace">Service-C</text></g>
    <circle cx="130" cy="210" r="25" fill="#1e3a5f" stroke="#60a5fa" stroke-width="1"/>
    <text x="130" y="215" text-anchor="middle" fill="#e3eaf0" font-size="9" font-family="monospace">DB</text>
    <circle cx="300" cy="210" r="25" fill="#1e3a5f" stroke="#60a5fa" stroke-width="1"/>
    <text x="300" y="215" text-anchor="middle" fill="#e3eaf0" font-size="9" font-family="monospace">Cache</text>
    <circle cx="470" cy="210" r="25" fill="#1e3a5f" stroke="#60a5fa" stroke-width="1"/>
    <text x="470" y="215" text-anchor="middle" fill="#e3eaf0" font-size="9" font-family="monospace">Queue</text>
    <line stroke="#34d399" stroke-width="1.5" x1="300" y1="50" x2="130" y2="90"/>
    <line stroke="#34d399" stroke-width="1.5" x1="300" y1="50" x2="300" y2="90"/>
    <line stroke="#34d399" stroke-width="1.5" x1="300" y1="50" x2="470" y2="90"/>'''
            title = 'Cloud Architecture'
            legend = '''<div class="legend-item"><div style="width:14px;height:14px;background:#1e3a5f;border:1px solid #34d399"></div><span>LB</span></div>
    <div class="legend-item"><div style="width:14px;height:14px;background:#1e3a5f;border:1px solid #00d4ff"></div><span>Service</span></div>
    <div class="legend-item"><div style="width:14px;height:14px;background:#1e3a5f;border:1px solid #60a5fa"></div><span>Resource</span></div>'''

        html = examples['topology-map']
        html = html.replace('${TITLE}', title)
        html = html.replace('${SVG_CONTENT}', svg_content)
        html = html.replace('${LEGEND}', legend)
        html = html.replace('${ID}', str(hash(title) % 10000))
        return html

    elif component_type == 'slider-control':
        if 'lambda' in filename.lower():
            label = 'Memory Allocation (Lambda):'
            min_val = '128'
            max_val = '10240'
            value = '1024'
            unit = 'MB'
            title = 'Lambda Configuration'
            slider_id = 'lambda-mem'
        elif 'rds' in filename.lower():
            label = 'Max Connections:'
            min_val = '20'
            max_val = '1000'
            value = '100'
            unit = 'conns'
            title = 'Database Tuning'
            slider_id = 'rds-conn'
        elif 'cache' in filename.lower():
            label = 'Cache Node Memory:'
            min_val = '256'
            max_val = '256000'
            value = '512'
            unit = 'MB'
            title = 'ElastiCache Settings'
            slider_id = 'cache-mem'
        elif 'scal' in filename.lower():
            label = 'Min ↔ Max Instances:'
            min_val = '1'
            max_val = '100'
            value = '3'
            unit = 'inst'
            title = 'Auto Scaling Configuration'
            slider_id = 'asg-cap'
        else:
            label = 'Throughput Limit:'
            min_val = '100'
            max_val = '100000'
            value = '1000'
            unit = 'req/s'
            title = 'Service Configuration'
            slider_id = 'throughput'

        html = examples['slider-control']
        html = html.replace('${TITLE}', title)
        html = html.replace('${LABEL}', label)
        html = html.replace('${MIN}', min_val)
        html = html.replace('${MAX}', max_val)
        html = html.replace('${VALUE}', value)
        html = html.replace('${UNIT}', unit)
        html = html.replace('${ID}', slider_id)
        return html

    return ''

def process_files(base_dir, is_cloud=False):
    """Process all markdown files in directory"""
    md_files = list(Path(base_dir).rglob('*.md'))

    count = 0
    for md_file in md_files:
        filename = md_file.name

        # Skip README files (except main ones)
        if filename == 'README.md' and str(md_file).count('/') > 5:
            continue

        # Get matched components
        components = match_file_to_components(filename, is_cloud)

        # Read current file
        with open(md_file, 'r') as f:
            content = f.read()

        # Check if already embedded (look for html-live marker)
        if 'html-live' in content or 'Interactive' in content or 'state-machine-title' in content:
            continue

        # Generate components
        component_htmls = []
        for comp_type in components:
            if is_cloud:
                html = generate_cloud_component(comp_type, filename)
            else:
                html = generate_frontend_component(comp_type, filename)

            if html:
                component_htmls.append(html)

        # Append components to file
        if component_htmls:
            new_content = content.rstrip() + '\n\n'
            for idx, html in enumerate(component_htmls, 1):
                new_content += f'\n## Interactive Component {idx}\n\n```html-live\n{html}\n```\n'

            # Write back
            with open(md_file, 'w') as f:
                f.write(new_content)

            count += 1
            print(f"✓ {md_file.relative_to(base_dir)} ({', '.join(components)})")

    return count

if __name__ == '__main__':
    print("Phase 3 Batch 7: Embedding Interactive Components\n")
    print("=" * 60)

    # Process frontend files
    print("\nFRONTEND FILES (React):")
    print("-" * 60)
    fe_count = process_files('/Users/ramyachowdary/Documents/prem-work/md-courses/data/04-frontend', is_cloud=False)

    # Process cloud files
    print("\nCLOUD FILES (AWS):")
    print("-" * 60)
    cl_count = process_files('/Users/ramyachowdary/Documents/prem-work/md-courses/data/05-cloud', is_cloud=True)

    print("\n" + "=" * 60)
    print(f"\nSummary:")
    print(f"  Frontend files processed: {fe_count}")
    print(f"  Cloud files processed: {cl_count}")
    print(f"  Total: {fe_count + cl_count}")
    print("\nReady for commit: Phase 3 Batch 7")
