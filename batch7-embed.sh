#!/bin/bash

# Phase 3 Batch 7: Add interactive components to frontend and cloud markdown files

cd /Users/ramyachowdary/Documents/prem-work/md-courses

# Component templates
STATE_MACHINE_LC='<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.state-machine-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px;letter-spacing:1px}.state-demo{text-align:center}.state-display{font-size:18px;font-family:monospace;padding:16px;border-radius:4px;margin:16px 0;color:#0b0e14;font-weight:bold;min-height:50px;display:flex;align-items:center;justify-content:center;border:2px solid currentColor}.state-mount{background:#60a5fa;border-color:#3b82f6}.state-update{background:#fbbf24;border-color:#f59e0b}.state-unmount{background:#ef4444;border-color:#dc2626}.state-buttons{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:16px}.state-button{padding:8px 16px;border:1px solid #00d4ff;background:#1e3a5f;color:#00d4ff;border-radius:4px;cursor:pointer;font-family:monospace;font-size:12px;transition:all 0.2s}.state-button:hover{background:#2a5a8f;box-shadow:0 0 8px #00d4ff}</style>
  <div class="state-machine-title">React Component Lifecycle</div>
  <div class="state-demo">
    <div class="state-display state-mount" id="lc-display">MOUNT</div>
    <div class="state-buttons">
      <button class="state-button" onclick="setLcState('\''MOUNT'\'', lcMap)">Mount</button>
      <button class="state-button" onclick="setLcState('\''UPDATE'\'', lcMap)">Update</button>
      <button class="state-button" onclick="setLcState('\''UNMOUNT'\'', lcMap)">Unmount</button>
    </div>
  </div>
  <script>
    const lcMap = {
      '\''MOUNT'\'': { label: '\''MOUNT'\'', class: '\''state-mount'\'' },
      '\''UPDATE'\'': { label: '\''UPDATE'\'', class: '\''state-update'\'' },
      '\''UNMOUNT'\'': { label: '\''UNMOUNT'\'', class: '\''state-unmount'\'' }
    };
    function setLcState(state, sm) {
      const display = document.getElementById('\''lc-display'\'');
      const info = sm[state];
      display.textContent = info.label;
      display.className = '\''state-display '\'' + info.class;
    }
  </script>
</div>'

STATE_MACHINE_CB='<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.state-machine-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px;letter-spacing:1px}.state-demo{text-align:center}.state-display{font-size:18px;font-family:monospace;padding:16px;border-radius:4px;margin:16px 0;color:#0b0e14;font-weight:bold;min-height:50px;display:flex;align-items:center;justify-content:center;border:2px solid currentColor}.state-closed{background:#34d399;border-color:#22c55e}.state-open{background:#ef4444;border-color:#dc2626}.state-half-open{background:#fbbf24;border-color:#f59e0b}.state-buttons{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:16px}.state-button{padding:8px 16px;border:1px solid #00d4ff;background:#1e3a5f;color:#00d4ff;border-radius:4px;cursor:pointer;font-family:monospace;font-size:12px;transition:all 0.2s}.state-button:hover{background:#2a5a8f;box-shadow:0 0 8px #00d4ff}</style>
  <div class="state-machine-title">Service State Machine</div>
  <div class="state-demo">
    <div class="state-display state-closed" id="state-display">CLOSED</div>
    <div class="state-buttons">
      <button class="state-button" onclick="setState('\''CLOSED'\'', stateMap)">Healthy</button>
      <button class="state-button" onclick="setState('\''OPEN'\'', stateMap)">Failing</button>
      <button class="state-button" onclick="setState('\''HALF_OPEN'\'', stateMap)">Recovery</button>
    </div>
  </div>
  <script>
    const stateMap = {
      '\''CLOSED'\'': { label: '\''CLOSED'\'', class: '\''state-closed'\'' },
      '\''OPEN'\'': { label: '\''OPEN'\'', class: '\''state-open'\'' },
      '\''HALF_OPEN'\'': { label: '\''HALF-OPEN'\'', class: '\''state-half-open'\'' }
    };
    function setState(state, sm) {
      const display = document.getElementById('\''state-display'\'');
      const info = sm[state];
      display.textContent = info.label;
      display.className = '\''state-display '\'' + info.class;
    }
  </script>
</div>'

echo "Phase 3 Batch 7: Embedding Interactive Components"
echo "=================================================="
echo ""

# Count processed files
TOTAL=0

# Process a few key frontend files
for file in \
    "data/04-frontend/react/02-react-internals/01-fiber-architecture.md" \
    "data/04-frontend/react/03-rendering-pipeline/01-rendering-performance.md" \
    "data/04-frontend/react/04-hooks-deep-dive/01-hooks-state.md" \
    "data/04-frontend/react/05-state-management/01-state-management.md" \
    "data/04-frontend/react/09-performance/01-performance-optimization.md"
do
    if [ -f "$file" ] && ! grep -q "Interactive Component" "$file"; then
        echo "Processing: $file"
        TOTAL=$((TOTAL+1))
    fi
done

# Process a few key cloud files
for file in \
    "data/05-cloud/aws/lambda/01-lambda-deep-dive.md" \
    "data/05-cloud/aws/lambda/02-lambda-advanced-patterns.md" \
    "data/05-cloud/aws/rds/01-rds-deep-dive.md" \
    "data/05-cloud/aws/ec2/01-ec2-deep-dive.md" \
    "data/05-cloud/aws/cloudwatch/01-cloudwatch-deep-dive.md"
do
    if [ -f "$file" ] && ! grep -q "Interactive Component" "$file"; then
        echo "Processing: $file"
        TOTAL=$((TOTAL+1))
    fi
done

echo ""
echo "Files to process: $TOTAL"
echo ""
echo "Running Python embedder..."

python3 /Users/ramyachowdary/Documents/prem-work/md-courses/batch7-embedder.py
