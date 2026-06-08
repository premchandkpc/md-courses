import { useMachine } from '@xstate/react'
import { motion } from 'framer-motion'
import type { AnyStateMachine } from 'xstate'

interface Props {
  machine: AnyStateMachine
  title: string
  events: Array<{ label: string; event: Record<string, unknown> }>
}

const stateColors: Record<string, string> = {
  stopped: '#5a6e91',
  pending: '#fbbf24',
  scheduled: '#a78bfa',
  imagePulling: '#f0883e',
  containerCreating: '#f0883e',
  running: '#3fb950',
  healthy: '#3fb950',
  degraded: '#f0883e',
  warning: '#fbbf24',
  critical: '#f85149',
  dead: '#f85149',
  failed: '#f85149',
  crashLoopBackoff: '#f85149',
  imagePullBackoff: '#f85149',
  evicted: '#f85149',
  terminated: '#5a6e91',
  closed: '#5a6e91',
  synSent: '#a78bfa',
  established: '#3fb950',
  finWait1: '#fbbf24',
  finWait2: '#f0883e',
  timeWait: '#5a6e91',
  rebalancing: '#a78bfa',
}

export function StateMachineViewer({ machine, title, events }: Props) {
  const [state, send] = useMachine(machine)

  const currentState = state.value
  const stateStr = typeof currentState === 'object'
    ? Object.values(currentState as Record<string, unknown>)[0] as string
    : String(currentState)

  return (
    <div className="rounded-xl border border-infra-700 overflow-hidden">
      <div className="px-4 py-2 text-xs font-mono text-infra-300 border-b border-infra-700 flex items-center gap-3">
        <span>{title}</span>
        <motion.span
          key={stateStr}
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="px-2 py-0.5 rounded text-[10px] font-bold"
          style={{
            background: stateColors[stateStr] || '#5a6e91',
            color: '#0b0e14',
          }}
        >
          {stateStr}
        </motion.span>
      </div>
      <div className="p-4 bg-infra-900 flex flex-wrap gap-2">
        {events.map((evt, i) => (
          <motion.button
            key={i}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => send(evt.event)}
            className="px-3 py-1.5 rounded text-xs font-mono border transition-colors bg-infra-800 border-infra-600 text-infra-200 hover:border-accent-cyan hover:text-accent-cyan"
          >
            {evt.label}
          </motion.button>
        ))}
      </div>
      <div className="px-4 py-2 text-[10px] font-mono text-infra-400 border-t border-infra-700">
        {state.context ? JSON.stringify(state.context).substring(0, 120) : ''}
      </div>
    </div>
  )
}
