import { create } from 'zustand'
import type { SimEntity, QueueState, ResourcePool, CameraLevel, SandboxMode, EntityState } from '../types'

interface SimulationStore {
  time: number
  running: boolean
  speed: number
  entities: Record<string, SimEntity>
  queues: Record<string, QueueState>
  resources: Record<string, ResourcePool>
  causalityChain: Array<{ time: number; event: string; chain: number }>

  cameraLevel: CameraLevel
  sandboxMode: SandboxMode

  registerEntity: (id: string, props?: Partial<SimEntity>) => void
  removeEntity: (id: string) => void
  updateEntity: (id: string, updates: Partial<SimEntity>) => void
  propagatePressure: (sourceId: string, amount: number, radius: number, dampening?: number) => void
  queue: (queueId: string, load: number) => QueueState
  updateResource: (resourceId: string, usage: number, capacity: number) => ResourcePool
  transitionState: (entityId: string, newState: EntityState, reason?: string) => void
  tick: () => void
  setRunning: (running: boolean) => void
  setSpeed: (speed: number) => void
  setCameraLevel: (level: CameraLevel) => void
  setSandboxMode: (mode: SandboxMode) => void
  reset: () => void
}

export const useSimulationStore = create<SimulationStore>((set, get) => ({
  time: 0,
  running: false,
  speed: 1,
  entities: {},
  queues: {},
  resources: {},
  causalityChain: [],
  cameraLevel: 2 as CameraLevel,
  sandboxMode: 'observe',

  registerEntity: (id, props = {}) =>
    set((s) => ({
      entities: {
        ...s.entities,
        [id]: {
          id,
          x: props.x ?? 0,
          y: props.y ?? 0,
          vx: props.vx ?? 0,
          vy: props.vy ?? 0,
          mass: props.mass ?? 1,
          pressure: props.pressure ?? 0,
          health: props.health ?? 100,
          state: props.state ?? 'healthy',
          metadata: props.metadata ?? {},
        },
      },
    })),

  removeEntity: (id) =>
    set((s) => {
      const entities = { ...s.entities }
      delete entities[id]
      return { entities }
    }),

  updateEntity: (id, updates) =>
    set((s) => ({
      entities: s.entities[id]
        ? { ...s.entities, [id]: { ...s.entities[id], ...updates } }
        : s.entities,
    })),

  propagatePressure: (sourceId, amount, radius, dampening = 0.8) => {
    const state = get()
    const source = state.entities[sourceId]
    if (!source) return

    const updates: Record<string, Partial<SimEntity>> = {}
    const events: Array<{ time: number; event: string; chain: number }> = []

    for (const [id, entity] of Object.entries(state.entities)) {
      if (id === sourceId) continue
      const distance = Math.hypot(entity.x - source.x, entity.y - source.y)
      if (distance < radius) {
        const factor = 1 - distance / radius
        const pressureToApply = amount * factor * dampening
        const newPressure = entity.pressure + pressureToApply
        let newState: EntityState = entity.state
        if (newPressure > 70) newState = 'critical'
        else if (newPressure > 40) newState = 'warning'
        else if (newPressure > 0) newState = 'degraded'
        updates[id] = { pressure: newPressure, state: newState }
        events.push({
          time: state.time,
          event: `${sourceId} pressure → ${id} (${newState})`,
          chain: state.causalityChain.length,
        })
      }
    }

    set((s) => ({
      entities: Object.fromEntries(
        Object.entries(s.entities).map(([id, e]) =>
          updates[id] ? [id, { ...e, ...updates[id] } as SimEntity] : [id, e]
        )
      ),
      causalityChain: [...s.causalityChain, ...events].slice(-100),
    }))
  },

  queue: (queueId, load) => {
    const state = get()
    const existing = state.queues[queueId]
    const q: QueueState = existing ?? { depth: 0, maxDepth: 100, drainRate: 10, fillRate: 0, pressure: 0 }
    q.fillRate = load
    q.depth = Math.min(q.maxDepth, Math.max(0, q.depth + load - q.drainRate))
    q.pressure = (q.depth / q.maxDepth) * 100

    const events = q.pressure > 80
      ? [{ time: state.time, event: `Queue ${queueId} full → backpressure`, chain: state.causalityChain.length }]
      : []

    set((s) => ({
      queues: { ...s.queues, [queueId]: { ...q } },
      causalityChain: [...s.causalityChain, ...events].slice(-100),
    }))
    return q
  },

  updateResource: (resourceId, usage, capacity) => {
    const state = get()
    const existing = state.resources[resourceId]
    const r: ResourcePool = existing ?? { id: resourceId, usage: 0, capacity: 100, utilization: 0, state: 'healthy' }
    r.usage = Math.min(capacity, usage)
    r.capacity = capacity
    r.utilization = (r.usage / r.capacity) * 100
    if (r.utilization > 95) r.state = 'exhausted'
    else if (r.utilization > 80) r.state = 'critical'
    else if (r.utilization > 50) r.state = 'warning'
    else r.state = 'healthy'

    const events = r.state === 'exhausted'
      ? [{ time: state.time, event: `${resourceId} exhausted → rejections`, chain: state.causalityChain.length }]
      : []

    set((s) => ({
      resources: { ...s.resources, [resourceId]: { ...r } },
      causalityChain: [...s.causalityChain, ...events].slice(-100),
    }))
    return r
  },

  transitionState: (entityId, newState, reason = '') =>
    set((s) => {
      const entity = s.entities[entityId]
      if (!entity) return s
      return {
        entities: { ...s.entities, [entityId]: { ...entity, state: newState } },
        causalityChain: [
          ...s.causalityChain,
          { time: s.time, event: `${entityId}: ${entity.state} → ${newState}${reason ? ` (${reason})` : ''}`, chain: s.causalityChain.length },
        ].slice(-100),
      }
    }),

  tick: () =>
    set((s) => {
      if (!s.running) return s
      const updatedEntities = Object.fromEntries(
        Object.entries(s.entities).map(([id, e]) => {
          let { pressure, health } = e
          pressure *= 0.98
          if (pressure < 1) pressure = 0
          if (pressure === 0 && health < 100) health = Math.min(100, health + 0.5)
          const state = pressure > 70 ? 'critical' as EntityState
            : pressure > 40 ? 'warning' as EntityState
            : pressure > 0 ? 'degraded' as EntityState
            : 'healthy' as EntityState
          return [id, { ...e, x: e.x + e.vx * 0.016, y: e.y + e.vy * 0.016, pressure, health, state } as SimEntity]
        })
      )
      return { time: s.time + 0.016 * s.speed, entities: updatedEntities }
    }),

  setRunning: (running) => set({ running }),
  setSpeed: (speed) => set({ speed }),
  setCameraLevel: (cameraLevel) => set({ cameraLevel }),
  setSandboxMode: (sandboxMode) => set({ sandboxMode }),
  reset: () =>
    set({
      time: 0,
      running: false,
      entities: {},
      queues: {},
      resources: {},
      causalityChain: [],
    }),
}))
