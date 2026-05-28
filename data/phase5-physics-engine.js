/**
 * Phase 5: Physics Engine for Engineering Simulations
 *
 * Core components:
 * - Tick loop (simulation heartbeat)
 * - Physics: pressure, latency, flow, resources
 * - State machine: transitions with animation
 * - Camera: zoom levels with context switching
 * - Causality tracker: shows what caused what
 * - Sandbox: parameterized experiments
 */

class PhysicsEngine {
  constructor(fps = 60) {
    this.fps = fps;
    this.deltaTime = 1 / fps;
    this.time = 0;
    this.entities = new Map();
    this.queues = new Map();
    this.resources = new Map();
    this.events = [];
    this.causalityChain = [];
    this.running = false;
  }

  // Register entity with position and properties
  registerEntity(id, props = {}) {
    this.entities.set(id, {
      id,
      x: props.x || 0,
      y: props.y || 0,
      vx: props.vx || 0,
      vy: props.vy || 0,
      mass: props.mass || 1,
      pressure: props.pressure || 0,
      health: props.health || 100,
      state: props.state || 'healthy',
      metadata: props.metadata || {}
    });
  }

  // Physics: Pressure propagation (like heat/fluid)
  // Source point spreads pressure to neighbors
  propagatePressure(sourceId, amount, radius, dampening = 0.8) {
    const source = this.entities.get(sourceId);
    if (!source) return;

    this.entities.forEach((entity, id) => {
      const distance = Math.hypot(
        entity.x - source.x,
        entity.y - source.y
      );

      if (distance < radius && id !== sourceId) {
        const factor = 1 - (distance / radius);
        const pressureToApply = amount * factor * dampening;
        entity.pressure += pressureToApply;

        // Pressure causes state changes
        if (entity.pressure > 70) entity.state = 'critical';
        else if (entity.pressure > 40) entity.state = 'warning';
        else if (entity.pressure > 0) entity.state = 'degraded';

        this.recordCausality(`${sourceId} pressure → ${id} state change`);
      }
    });
  }

  // Physics: Latency as gravity (everything "falls" toward it)
  applyLatency(targetId, latencyMs) {
    const target = this.entities.get(targetId);
    if (!target) return;

    // Latency pulls velocity down
    const gravityStrength = latencyMs / 1000;
    target.vy -= gravityStrength * this.deltaTime;

    // Entities slow down (latency drags them)
    target.vx *= (1 - gravityStrength * 0.01);
  }

  // Queue operations: buildup and draining
  queue(queueId, load) {
    if (!this.queues.has(queueId)) {
      this.queues.set(queueId, {
        depth: 0,
        maxDepth: 100,
        drainRate: 10,
        fillRate: 0,
        pressure: 0
      });
    }

    const q = this.queues.get(queueId);
    q.fillRate = load;
    q.depth = Math.min(q.maxDepth, Math.max(0, q.depth + load - q.drainRate));
    q.pressure = (q.depth / q.maxDepth) * 100;

    // Queue pressure cascades to connected entities
    if (q.pressure > 80) {
      this.recordCausality(`Queue ${queueId} full → backpressure`);
    }

    return q;
  }

  // Resource pools (CPU, memory, connections, threads)
  updateResource(resourceId, usage, capacity) {
    if (!this.resources.has(resourceId)) {
      this.resources.set(resourceId, {
        id: resourceId,
        usage: 0,
        capacity: 100,
        utilization: 0,
        state: 'healthy'
      });
    }

    const r = this.resources.get(resourceId);
    r.usage = Math.min(capacity, usage);
    r.capacity = capacity;
    r.utilization = (r.usage / r.capacity) * 100;

    // Resource exhaustion changes state
    if (r.utilization > 95) {
      r.state = 'exhausted';
      this.recordCausality(`${resourceId} exhausted → rejections`);
    } else if (r.utilization > 80) {
      r.state = 'critical';
    } else if (r.utilization > 50) {
      r.state = 'warning';
    } else {
      r.state = 'healthy';
    }

    return r;
  }

  // State machine: track transitions with causality
  transitionState(entityId, newState, reason = '') {
    const entity = this.entities.get(entityId);
    if (!entity) return;

    const oldState = entity.state;
    entity.state = newState;
    this.recordCausality(`${entityId}: ${oldState} → ${newState} (${reason})`);

    return { oldState, newState, reason };
  }

  // Causality: track chains of events
  recordCausality(event) {
    this.causalityChain.push({
      time: this.time,
      event,
      chain: this.causalityChain.length
    });

    // Keep only recent history
    if (this.causalityChain.length > 100) {
      this.causalityChain.shift();
    }
  }

  // Get causality chain for a time window
  getCausalityChain(windowMs = 5000) {
    const threshold = this.time - windowMs;
    return this.causalityChain.filter(c => c.time > threshold);
  }

  // Movement with physics
  update() {
    this.entities.forEach((entity) => {
      // Apply velocity
      entity.x += entity.vx * this.deltaTime;
      entity.y += entity.vy * this.deltaTime;

      // Decay pressure over time
      entity.pressure *= 0.98;
      if (entity.pressure < 1) entity.pressure = 0;

      // Health recovery if not under pressure
      if (entity.pressure === 0 && entity.health < 100) {
        entity.health = Math.min(100, entity.health + 0.5);
      }
    });

    this.time += this.deltaTime;
  }

  tick() {
    if (!this.running) return;
    this.update();
  }

  start() { this.running = true; }
  stop() { this.running = false; }
}

// ============================================
// Camera System: Zoom levels with context
// ============================================

class CameraSystem {
  constructor(width, height) {
    this.width = width;
    this.height = height;
    this.x = width / 2;
    this.y = height / 2;
    this.zoom = 1;
    this.level = 1; // 1=global, 5=microscopic

    this.levels = {
      1: { name: 'Global', zoom: 0.5, context: 'Datacenter overview', radius: 2000 },
      2: { name: 'Cluster', zoom: 1, context: 'Service cluster', radius: 1000 },
      3: { name: 'Component', zoom: 2, context: 'Single service', radius: 400 },
      4: { name: 'Subsystem', zoom: 4, context: 'Internal behavior', radius: 200 },
      5: { name: 'Mechanics', zoom: 8, context: 'Low-level operations', radius: 100 }
    };
  }

  zoomIn() {
    if (this.level < 5) {
      this.level++;
      const levelConfig = this.levels[this.level];
      this.zoom = levelConfig.zoom;
      return levelConfig;
    }
    return null;
  }

  zoomOut() {
    if (this.level > 1) {
      this.level--;
      const levelConfig = this.levels[this.level];
      this.zoom = levelConfig.zoom;
      return levelConfig;
    }
    return null;
  }

  getVisibleEntities(entities) {
    const levelConfig = this.levels[this.level];
    const visibleEntities = [];

    entities.forEach((entity, id) => {
      const distance = Math.hypot(entity.x - this.x, entity.y - this.y);
      if (distance < levelConfig.radius) {
        visibleEntities.push({ id, entity });
      }
    });

    return visibleEntities;
  }

  getContext() {
    return this.levels[this.level];
  }

  worldToScreen(x, y) {
    return {
      x: (x - this.x) * this.zoom + this.width / 2,
      y: (y - this.y) * this.zoom + this.height / 2
    };
  }

  screenToWorld(x, y) {
    return {
      x: (x - this.width / 2) / this.zoom + this.x,
      y: (y - this.height / 2) / this.zoom + this.y
    };
  }
}

// ============================================
// Sandbox: Parameterized experiments
// ============================================

class Sandbox {
  constructor() {
    this.parameters = new Map();
    this.mode = 'observe'; // learn, observe, debug, scale, chaos, replay
    this.history = [];
  }

  // Register tunable parameter
  addParameter(name, min, max, default_val, unit = '') {
    this.parameters.set(name, {
      name,
      min,
      max,
      value: default_val,
      unit,
      history: [default_val]
    });
  }

  // Set parameter value
  setParameter(name, value) {
    const param = this.parameters.get(name);
    if (param) {
      param.value = Math.max(param.min, Math.min(param.max, value));
      param.history.push(param.value);
      if (param.history.length > 1000) param.history.shift();
    }
  }

  // Get all parameters for UI
  getParameters() {
    const result = {};
    this.parameters.forEach((param, name) => {
      result[name] = {
        value: param.value,
        min: param.min,
        max: param.max,
        unit: param.unit
      };
    });
    return result;
  }

  // Record simulation state for replay
  recordFrame(state) {
    this.history.push({
      time: Date.now(),
      state
    });
    if (this.history.length > 10000) this.history.shift();
  }

  // Set mode
  setMode(mode) {
    if (['learn', 'observe', 'debug', 'scale', 'chaos', 'replay'].includes(mode)) {
      this.mode = mode;
    }
  }

  // Get mode info
  getModeInfo() {
    const modes = {
      learn: { description: 'Step-by-step with guidance', speed: 0.1 },
      observe: { description: 'Autonomous simulation', speed: 1 },
      debug: { description: 'Failure analysis with causality', speed: 0.5 },
      scale: { description: 'Parameter tuning with live feedback', speed: 1 },
      chaos: { description: 'Inject failures and observe cascades', speed: 1 },
      replay: { description: 'Playback recorded incidents', speed: 'variable' }
    };
    return modes[this.mode] || {};
  }
}

// ============================================
// Exports
// ============================================

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { PhysicsEngine, CameraSystem, Sandbox };
}
