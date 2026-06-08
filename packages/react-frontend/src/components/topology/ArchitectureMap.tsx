import { useMemo, useCallback } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  type NodeTypes,
  useNodesState,
  useEdgesState,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { motion } from 'framer-motion'
import type { TopologyNode } from '../../types'

interface Props {
  nodes: TopologyNode[]
  edges: Array<{ source: string; target: string; label?: string }>
  title?: string
}

const nodeColorMap: Record<string, string> = {
  client: '#00d4ff',
  gateway: '#f0883e',
  service: '#3fb950',
  cache: '#a78bfa',
  queue: '#fbbf24',
  database: '#f85149',
  loadbalancer: '#f0883e',
}

function TopologyNodeComponent({ data }: { data: { label: string; status?: string; metrics?: Record<string, number | undefined> } }) {
  const statusColor = data.status === 'critical' ? '#f85149'
    : data.status === 'warning' ? '#fbbf24'
    : data.status === 'degraded' ? '#f0883e'
    : '#3fb950'

  return (
    <motion.div
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      className="px-4 py-2 rounded-lg border text-center min-w-[120px]"
      style={{
        background: '#1a2332',
        borderColor: statusColor,
        borderWidth: 2,
      }}
    >
      <div className="text-xs font-mono" style={{ color: statusColor }}>{data.label}</div>
      {data.metrics?.latency && (
        <div className="text-[10px] mt-1 text-infra-400">
          {data.metrics.latency}ms
        </div>
      )}
    </motion.div>
  )
}

const nodeTypes: NodeTypes = {
  topologyNode: TopologyNodeComponent,
}

export function ArchitectureMap({ nodes: inputNodes, edges: inputEdges, title }: Props) {
  const initialNodes: Node[] = useMemo(() =>
    inputNodes.map((n, i) => ({
      id: n.id,
      type: 'topologyNode',
      position: { x: 100 + (i % 4) * 180, y: 80 + Math.floor(i / 4) * 140 },
      data: { label: n.label, status: n.status, metrics: n.metrics },
    })), [inputNodes])

  const initialEdges: Edge[] = useMemo(() =>
    inputEdges.map((e, i) => ({
      id: `e-${i}`,
      source: e.source,
      target: e.target,
      label: e.label,
      animated: true,
      style: { stroke: '#3a4a66', strokeWidth: 2 },
      labelStyle: { fill: '#8a9bb8', fontSize: 10 },
    })), [inputEdges])

  const [nodes, , onNodesChange] = useNodesState(initialNodes)
  const [edges, , onEdgesChange] = useEdgesState(initialEdges)

  return (
    <div className="rounded-xl overflow-hidden border border-infra-700" style={{ height: 500, background: '#0b0e14' }}>
      {title && (
        <div className="px-4 py-2 text-xs font-mono text-infra-300 border-b border-infra-700">
          {title}
        </div>
      )}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        colorMode="dark"
      >
        <Background color="#1a2332" gap={20} />
        <Controls className="bg-infra-800 border-infra-600 rounded-lg" />
        <MiniMap
          style={{ background: '#111620' }}
          nodeColor="#3a4a66"
          maskColor="rgba(11, 14, 16, 0.7)"
        />
      </ReactFlow>
    </div>
  )
}
