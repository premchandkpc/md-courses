import { ArchitectureMap } from './ArchitectureMap'
import type { TopologyNode } from '../../types'

const kafkaNodes: TopologyNode[] = [
  { id: 'producer', label: 'Producer', type: 'client' },
  { id: 'broker-1', label: 'Broker 1', type: 'service', status: 'healthy', metrics: { latency: 3 } },
  { id: 'broker-2', label: 'Broker 2', type: 'service', status: 'degraded', metrics: { latency: 45 } },
  { id: 'broker-3', label: 'Broker 3', type: 'service', status: 'critical', metrics: { latency: 200 } },
  { id: 'zk', label: 'ZooKeeper', type: 'database', status: 'healthy' },
  { id: 'consumer', label: 'Consumer', type: 'client' },
]

const kafkaEdges = [
  { source: 'producer', target: 'broker-1', label: 'acks=all' },
  { source: 'producer', target: 'broker-2', label: 'partition 0' },
  { source: 'producer', target: 'broker-3', label: 'partition 1' },
  { source: 'broker-1', target: 'zk', label: 'metadata' },
  { source: 'broker-2', target: 'zk', label: 'metadata' },
  { source: 'broker-3', target: 'zk', label: 'metadata' },
  { source: 'consumer', target: 'broker-1', label: 'poll offset' },
  { source: 'broker-1', target: 'broker-2', label: 'replication' },
  { source: 'broker-1', target: 'broker-3', label: 'replication' },
]

export function KafkaTopology() {
  return (
    <ArchitectureMap
      nodes={kafkaNodes}
      edges={kafkaEdges}
      title="Kafka Cluster Topology"
    />
  )
}
