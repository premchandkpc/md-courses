# Interactive Component Test

This file tests the html-live block support.

## Request Flow Animation

```html-live
<div style="display:flex;flex-direction:column;align-items:center;gap:8px;padding:16px">
  <style>
    @keyframes flow-pulse { 0%,100%{opacity:.3;transform:translateY(0)} 50%{opacity:1;transform:translateY(-2px)} }
    .test-node { display:inline-block;padding:8px 16px;border-radius:4px;font-size:12px;font-family:monospace;color:#e3eaf0;background:#1e3a5f;border:1px solid #00d4ff }
    .test-arrow { color:#00d4ff;font-size:16px;animation:flow-pulse 1.5s infinite }
  </style>
  <div class="test-node">Client Request</div>
  <div class="test-arrow">↓</div>
  <div class="test-node">Load Balancer</div>
  <div class="test-arrow">↓</div>
  <div class="test-node">API Server</div>
  <div class="test-arrow">↓</div>
  <div class="test-node">Database</div>
</div>
```

## Interactive Slider

```html-live
<div style="padding:16px">
  <style>
    .slider-demo { display:flex;align-items:center;gap:12px }
    .slider-value { font-family:monospace;color:#34d399;min-width:40px }
  </style>
  <label style="display:block;margin-bottom:8px;color:#e3eaf0">Throughput (requests/sec):</label>
  <div class="slider-demo">
    <input type="range" min="10" max="1000" value="100" id="throughput-slider" style="flex:1">
    <span class="slider-value" id="throughput-value">100</span>
  </div>
  <script>
    const slider = document.getElementById('throughput-slider');
    const value = document.getElementById('throughput-value');
    slider.addEventListener('input', (e) => {
      value.textContent = e.target.value;
    });
  </script>
</div>
```

## State Machine with Buttons

```html-live
<div style="padding:16px">
  <style>
    .state-demo { text-align:center }
    .state-display { 
      font-size:16px;
      font-family:monospace;
      padding:12px;
      border-radius:4px;
      margin:12px 0;
      color:#0b0e14;
      font-weight:bold;
      min-height:40px;
      display:flex;
      align-items:center;
      justify-content:center
    }
    .state-closed { background:#34d399 }
    .state-open { background:#ef4444 }
    .state-half-open { background:#fbbf24 }
  </style>
  <div class="state-demo">
    <label style="color:#e3eaf0">Circuit Breaker State:</label>
    <div class="state-display state-closed" id="state-display">CLOSED</div>
    <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap">
      <button onclick="setState('CLOSED')">Close</button>
      <button onclick="setState('OPEN')">Open (Error)</button>
      <button onclick="setState('HALF_OPEN')">Half-Open (Retry)</button>
    </div>
  </div>
  <script>
    function setState(state) {
      const display = document.getElementById('state-display');
      const stateMap = {
        'CLOSED': { text: 'CLOSED', class: 'state-closed' },
        'OPEN': { text: 'OPEN', class: 'state-open' },
        'HALF_OPEN': { text: 'HALF-OPEN', class: 'state-half-open' }
      };
      const info = stateMap[state];
      display.textContent = info.text;
      display.className = 'state-display ' + info.class;
    }
  </script>
</div>
```

This is a test file to verify html-live block rendering and interactivity.
