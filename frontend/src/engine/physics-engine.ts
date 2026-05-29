import type { SandboxParam, CameraConfig, CameraLevel } from '../types'

export class PhysicsEngine {
  fps: number
  deltaTime: number
  time: number
  entities: Map<string, {
    id: string
    x: number
    y: number
    vx: number
    vy: number
    mass: number
    pressure: number
    health: number
    state: string
  }>
  queues: Map<string, { depth: number; maxDepth: number; drainRate: number; fillRate: number; pressure: number }>
  resources: Map<string, { id: string; usage: number; capacity: number; utilization: number; state: string }>
  causalityChain: Array<{ time: number; event: string; chain: number }>
  running: boolean

  constructor(fps = 60) {
    this.fps = fps
    this.deltaTime = 1 / fps
    this.time = 0
    this.entities = new Map()
    this.queues = new Map()
    this.resources = new Map()
    this.causalityChain = []
    this.running = false
  }

  registerEntity(id: string, props: Record<string, unknown> = {}) {
    this.entities.set(id, {
      id,
      x: (props.x as number) || 0,
      y: (props.y as number) || 0,
      vx: (props.vx as number) || 0,
      vy: (props.vy as number) || 0,
      mass: (props.mass as number) || 1,
      pressure: (props.pressure as number) || 0,
      health: (props.health as number) || 100,
      state: (props.state as string) || 'healthy',
    })
  }

  propagatePressure(sourceId: string, amount: number, radius: number, dampening = 0.8) {
    const source = this.entities.get(sourceId)
    if (!source) return
    this.entities.forEach((entity, id) => {
      if (id === sourceId) return
      const distance = Math.hypot(entity.x - source.x, entity.y - source.y)
      if (distance < radius) {
        const factor = 1 - distance / radius
        entity.pressure += amount * factor * dampening
        if (entity.pressure > 70) entity.state = 'critical'
        else if (entity.pressure > 40) entity.state = 'warning'
        else if (entity.pressure > 0) entity.state = 'degraded'
        this.recordCausality(`${sourceId} pressure → ${id} state change`)
      }
    })
  }

  queue(queueId: string, load: number) {
    if (!this.queues.has(queueId)) {
      this.queues.set(queueId, { depth: 0, maxDepth: 100, drainRate: 10, fillRate: 0, pressure: 0 })
    }
    const q = this.queues.get(queueId)!
    q.fillRate = load
    q.depth = Math.min(q.maxDepth, Math.max(0, q.depth + load - q.drainRate))
    q.pressure = (q.depth / q.maxDepth) * 100
    if (q.pressure > 80) this.recordCausality(`Queue ${queueId} full → backpressure`)
    return q
  }

  updateResource(resourceId: string, usage: number, capacity: number) {
    if (!this.resources.has(resourceId)) {
      this.resources.set(resourceId, { id: resourceId, usage: 0, capacity: 100, utilization: 0, state: 'healthy' })
    }
    const r = this.resources.get(resourceId)!
    r.usage = Math.min(capacity, usage)
    r.capacity = capacity
    r.utilization = (r.usage / r.capacity) * 100
    if (r.utilization > 95) { r.state = 'exhausted'; this.recordCausality(`${resourceId} exhausted → rejections`) }
    else if (r.utilization > 80) r.state = 'critical'
    else if (r.utilization > 50) r.state = 'warning'
    else r.state = 'healthy'
    return r
  }

  transitionState(entityId: string, newState: string, reason = '') {
    const entity = this.entities.get(entityId)
    if (!entity) return
    const oldState = entity.state
    entity.state = newState
    this.recordCausality(`${entityId}: ${oldState} → ${newState}${reason ? ` (${reason})` : ''}`)
  }

  recordCausality(event: string) {
    this.causalityChain.push({ time: this.time, event, chain: this.causalityChain.length })
    if (this.causalityChain.length > 100) this.causalityChain.shift()
  }

  tick() {
    if (!this.running) return
    this.entities.forEach((entity) => {
      entity.x += entity.vx * this.deltaTime
      entity.y += entity.vy * this.deltaTime
      entity.pressure *= 0.98
      if (entity.pressure < 1) entity.pressure = 0
      if (entity.pressure === 0 && entity.health < 100) entity.health = Math.min(100, entity.health + 0.5)
    })
    this.time += this.deltaTime
  }

  start() { this.running = true }
  stop() { this.running = false }
  getState() {
    return {
      time: this.time,
      entities: Object.fromEntries(this.entities),
      queues: Object.fromEntries(this.queues),
      resources: Object.fromEntries(this.resources),
    }
  }
}

export class CameraSystem {
  x: number
  y: number
  zoom: number
  level: number
  levels: Record<number, CameraConfig>

  constructor(width: number, height: number) {
    this.x = width / 2
    this.y = height / 2
    this.zoom = 1
    this.level = 2
    this.levels = {
      1: { name: 'Global', zoom: 0.5, context: 'Datacenter overview', radius: 2000 },
      2: { name: 'Cluster', zoom: 1, context: 'Service cluster', radius: 1000 },
      3: { name: 'Component', zoom: 2, context: 'Single service', radius: 400 },
      4: { name: 'Subsystem', zoom: 4, context: 'Internal behavior', radius: 200 },
      5: { name: 'Mechanics', zoom: 8, context: 'Low-level operations', radius: 100 },
    }
  }

  setLevel(level: CameraLevel) {
    this.level = level
    this.zoom = this.levels[level].zoom
  }

  getContext() { return this.levels[this.level] }
}

export class SandboxEngine {
  parameters: Map<string, SandboxParam> = new Map()
  mode: string = 'observe'
  history: Array<{ time: number; state: Record<string, unknown> }> = []

  addParameter(name: string, min: number, max: number, defaultValue: number, unit = '') {
    this.parameters.set(name, { name, min, max, value: defaultValue, unit })
  }

  setParameter(name: string, value: number) {
    const param = this.parameters.get(name)
    if (param) param.value = Math.max(param.min, Math.min(param.max, value))
  }

  getParameters(): Record<string, { value: number; min: number; max: number; unit: string }> {
    const result: Record<string, { value: number; min: number; max: number; unit: string }> = {}
    this.parameters.forEach((p) => { result[p.name] = { value: p.value, min: p.min, max: p.max, unit: p.unit } })
    return result
  }

  setMode(mode: string) {
    if (['learn', 'observe', 'debug', 'scale', 'chaos', 'replay'].includes(mode)) this.mode = mode
  }
}
