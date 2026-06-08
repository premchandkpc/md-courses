import { ArchitectureMap } from './ArchitectureMap'
import type { TopologyNode } from '../../types'

const serviceNodes: TopologyNode[] = [
  { id: 'client', label: 'Client', type: 'client' },
  { id: 'gateway', label: 'API Gateway', type: 'gateway', metrics: { latency: 5 } },
  { id: 'service-a', label: 'Service A', type: 'service', metrics: { latency: 45 } },
  { id: 'service-b', label: 'Service B', type: 'service', metrics: { latency: 120 } },
  { id: 'cache', label: 'Redis Cache', type: 'cache', metrics: { latency: 2 } },
  { id: 'queue', label: 'Kafka', type: 'queue', status: 'degraded', metrics: { latency: 30 } },
  { id: 'db', label: 'PostgreSQL', type: 'database', metrics: { latency: 150 } },
]

const serviceEdges = [
  { source: 'client', target: 'gateway', label: 'HTTP' },
  { source: 'gateway', target: 'service-a', label: 'gRPC' },
  { source: 'gateway', target: 'service-b', label: 'gRPC' },
  { source: 'service-a', target: 'cache', label: 'Redis' },
  { source: 'service-a', target: 'queue', label: 'Produce' },
  { source: 'service-b', target: 'queue', label: 'Consume' },
  { source: 'service-a', target: 'db', label: 'SQL' },
]

export function ServiceTopology() {
  return (
    <ArchitectureMap
      nodes={serviceNodes}
      edges={serviceEdges}
      title="Service Architecture Topology"
    />
  )
}
