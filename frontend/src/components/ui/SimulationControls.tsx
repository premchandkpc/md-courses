import { motion } from 'framer-motion'
import { useSimulationStore } from '../../stores/simulation-store'

export function SimulationControls() {
  const running = useSimulationStore((s) => s.running)
  const speed = useSimulationStore((s) => s.speed)
  const sandboxMode = useSimulationStore((s) => s.sandboxMode)
  const time = useSimulationStore((s) => s.time)
  const setRunning = useSimulationStore((s) => s.setRunning)
  const setSpeed = useSimulationStore((s) => s.setSpeed)
  const setSandboxMode = useSimulationStore((s) => s.setSandboxMode)
  const tick = useSimulationStore((s) => s.tick)
  const reset = useSimulationStore((s) => s.reset)

  return (
    <div className="rounded-xl border border-infra-700 p-4 bg-infra-900">
      <div className="flex items-center gap-3 mb-3">
        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={() => setRunning(!running)}
          className="px-4 py-2 rounded-lg text-xs font-mono font-bold border"
          style={{
            background: running ? '#3fb950' : '#00d4ff',
            borderColor: running ? '#3fb950' : '#00d4ff',
            color: '#0b0e14',
          }}
        >
          {running ? '⏹ STOP' : '▶ PLAY'}
        </motion.button>

        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={tick}
          className="px-3 py-2 rounded-lg text-xs font-mono border border-infra-600 text-infra-300"
          style={{ background: '#1a2332' }}
        >
          ⏭ STEP
        </motion.button>

        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={reset}
          className="px-3 py-2 rounded-lg text-xs font-mono border border-infra-600 text-infra-400"
          style={{ background: '#111620' }}
        >
          ↺ RESET
        </motion.button>

        <div className="flex-1 text-right text-[10px] font-mono text-infra-400">
          t={time.toFixed(1)}s
        </div>
      </div>

      <div className="flex items-center gap-3">
        <span className="text-[10px] font-mono text-infra-400 w-12">Speed</span>
        <input
          type="range"
          min={0.1}
          max={10}
          step={0.1}
          value={speed}
          onChange={(e) => setSpeed(parseFloat(e.target.value))}
          className="flex-1 h-1 rounded-full appearance-none cursor-pointer"
          style={{ background: '#253045', accentColor: '#00d4ff' }}
        />
        <span className="text-[10px] font-mono text-infra-300 w-8">{speed}x</span>
      </div>

      <div className="flex gap-1 mt-3">
        {(['learn', 'observe', 'debug', 'scale', 'chaos'] as const).map((mode) => (
          <motion.button
            key={mode}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setSandboxMode(mode)}
            className="px-2 py-1 rounded text-[9px] font-mono uppercase tracking-wider border transition-colors"
            style={{
              background: sandboxMode === mode ? '#00d4ff' : '#1a2332',
              borderColor: sandboxMode === mode ? '#00d4ff' : '#253045',
              color: sandboxMode === mode ? '#0b0e14' : '#8a9bb8',
            }}
          >
            {mode}
          </motion.button>
        ))}
      </div>
    </div>
  )
}
