export type EntityState = 'healthy' | 'degraded' | 'warning' | 'critical' | 'exhausted' | 'dead'

export interface SimEntity {
  id: string
  x: number
  y: number
  vx: number
  vy: number
  mass: number
  pressure: number
  health: number
  state: EntityState
  metadata: Record<string, unknown>
}

export interface QueueState {
  depth: number
  maxDepth: number
  drainRate: number
  fillRate: number
  pressure: number
}

export interface ResourcePool {
  id: string
  usage: number
  capacity: number
  utilization: number
  state: EntityState
}

export interface SimulationState {
  time: number
  running: boolean
  speed: number
  entities: Record<string, SimEntity>
  queues: Record<string, QueueState>
  resources: Record<string, ResourcePool>
  causalityChain: CausalityEvent[]
}

export interface CausalityEvent {
  time: number
  event: string
  chain: number
}

export type CameraLevel = 1 | 2 | 3 | 4 | 5

export interface CameraConfig {
  name: string
  zoom: number
  context: string
  radius: number
}

export type SandboxMode = 'learn' | 'observe' | 'debug' | 'scale' | 'chaos' | 'replay'

export interface SandboxParam {
  name: string
  min: number
  max: number
  value: number
  unit: string
}

export type ThemeMode = 'dark' | 'light'

export interface AppState {
  theme: ThemeMode
  activeDomain: string | null
  activeSimulator: string | null
  sidebarOpen: boolean
}

export interface FileNode {
  name: string
  path: string
  type: 'file' | 'dir'
  children?: FileNode[]
  size?: number
  open?: boolean
}

export interface TopologyNode {
  id: string
  label: string
  type: 'service' | 'gateway' | 'cache' | 'queue' | 'database' | 'client' | 'loadbalancer'
  status?: EntityState
  metrics?: { latency?: number; throughput?: number; errorRate?: number }
}
