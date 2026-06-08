import { useState, useEffect, useCallback } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ServiceTopology } from './components/topology/ServiceTopology'
import { KafkaTopology } from './components/topology/KafkaTopology'
import { InfrastructureCanvas } from './components/simulation/InfrastructureCanvas'
import { LatencyChart, ThroughputGauge, CausalityTimeline } from './components/dashboard/MetricsPanel'
import { StateMachineViewer } from './components/state-machine/StateMachineViewer'
import { SimulationControls } from './components/ui/SimulationControls'
import { FileTree } from './components/ui/FileTree'
import { FileContentViewer } from './components/content/FileContentViewer'
import { VisualizationGallery } from './components/content/VisualizationGallery'
import { ErrorBoundary } from './components/ui/ErrorBoundary'
import { useSimulationStore } from './stores/simulation-store'
import { searchFiles } from './lib/api'
import { kafkaBrokerMachine } from './machines/kafka-broker'
import { kubernetesPodMachine } from './machines/kubernetes-pod'
import { tcpConnectionMachine } from './machines/tcp-connection'

type Tab = 'explorer' | 'topology' | 'simulation' | 'dashboard' | 'machines'

const tabs: { id: Tab; label: string }[] = [
  { id: 'explorer', label: 'Explorer' },
  { id: 'topology', label: 'Topology' },
  { id: 'simulation', label: 'Simulation' },
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'machines', label: 'State Machines' },
]

function SearchBar({ onSelect }: { onSelect: (path: string) => void }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Array<{ path: string; name: string }>>([])
  const [open, setOpen] = useState(false)

  const doSearch = useCallback(async (q: string) => {
    if (!q.trim()) { setResults([]); return }
    try {
      const data = await searchFiles(q)
      setResults(data.results.slice(0, 15))
      setOpen(true)
    } catch { setResults([]) }
  }, [])

  useEffect(() => {
    const id = setTimeout(() => doSearch(query), 200)
    return () => clearTimeout(id)
  }, [query, doSearch])

  return (
    <div className="relative">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results.length > 0 && setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 200)}
        placeholder="Search files..."
        className="w-48 px-3 py-1.5 rounded text-[11px] font-mono bg-infra-800 border border-infra-600 text-infra-200 placeholder-infra-500 outline-none focus:border-accent-cyan transition-colors"
      />
      <AnimatePresence>
        {open && results.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="absolute top-full mt-1 right-0 w-72 rounded-lg border border-infra-700 overflow-hidden shadow-xl z-50"
            style={{ background: '#111620' }}
          >
            {results.map((r) => (
              <button
                key={r.path}
                onMouseDown={() => { onSelect(r.path); setOpen(false); setQuery('') }}
                className="w-full text-left px-3 py-2 text-[11px] font-mono text-infra-300 hover:bg-infra-700 hover:text-infra-100 transition-colors truncate border-b border-infra-700 last:border-0"
              >
                {r.name}
                <span className="ml-2 text-[9px] text-infra-500">{r.path}</span>
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('explorer')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const tick = useSimulationStore((s) => s.tick)
  const running = useSimulationStore((s) => s.running)
  const speed = useSimulationStore((s) => s.speed)

  useEffect(() => {
    if (!running) return
    const interval = 1000 / (60 * speed)
    const id = setInterval(tick, Math.max(16, interval))
    return () => clearInterval(id)
  }, [running, speed, tick])

  const handleSearchSelect = useCallback((path: string) => {
    setSelectedFile(path)
    setActiveTab('explorer')
  }, [])

  return (
    <div className="h-screen flex flex-col bg-infra-950 text-infra-200">
      <header className="flex items-center justify-between px-5 py-3 border-b border-infra-700 bg-infra-900">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-infra-400 hover:text-infra-200 transition-colors text-sm"
          >
            {sidebarOpen ? '\u25C1' : '\u25B7'}
          </button>
          <h1 className="text-sm font-bold font-mono text-accent-cyan tracking-wide">
            ENGINEERING KNOWLEDGE UNIVERSE
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <SearchBar onSelect={handleSearchSelect} />
          <nav className="flex gap-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-1.5 rounded text-[11px] font-mono uppercase tracking-wider transition-all ${
                  activeTab === tab.id
                    ? 'bg-accent-cyan text-infra-950 font-bold'
                    : 'text-infra-400 hover:text-infra-200'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <AnimatePresence>
          {sidebarOpen && (
            <motion.aside
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 260, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              className="border-r border-infra-700 overflow-hidden shrink-0"
              style={{ background: '#111620' }}
            >
              <div className="p-3">
                <FileTree onSelect={setSelectedFile} />
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        <main className="flex-1 overflow-y-auto p-5">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.15 }}
            >
              {activeTab === 'explorer' && (
                <div className="rounded-xl border border-infra-700 p-5 bg-infra-900">
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-[10px] font-mono text-infra-400 uppercase tracking-wider">
                      {selectedFile || 'No file selected'}
                    </div>
                    <div className="text-[9px] font-mono text-infra-500">
                      {selectedFile?.endsWith('.html') ? 'Interactive' : selectedFile?.endsWith('.md') ? 'Markdown' : ''}
                    </div>
                  </div>
                  <div className="border-t border-infra-700 pt-3">
                    <ErrorBoundary>
                      <FileContentViewer filePath={selectedFile} onSelect={setSelectedFile} />
                      <VisualizationGallery filePath={selectedFile} />
                    </ErrorBoundary>
                  </div>
                </div>
              )}

              {activeTab === 'topology' && (
                <ErrorBoundary>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                    <ServiceTopology />
                    <KafkaTopology />
                  </div>
                </ErrorBoundary>
              )}

              {activeTab === 'simulation' && (
                <ErrorBoundary>
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                    <div className="lg:col-span-2">
                      <InfrastructureCanvas />
                    </div>
                    <div>
                      <SimulationControls />
                    </div>
                  </div>
                </ErrorBoundary>
              )}

              {activeTab === 'dashboard' && (
                <ErrorBoundary>
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                    <div className="rounded-xl border border-infra-700 p-4 bg-infra-900">
                      <div className="text-[10px] font-mono text-infra-400 mb-2 uppercase tracking-wider">Latency by Entity</div>
                      <LatencyChart />
                    </div>
                    <div className="rounded-xl border border-infra-700 p-4 bg-infra-900">
                      <div className="text-[10px] font-mono text-infra-400 mb-2 uppercase tracking-wider">Resource Utilization</div>
                      <ThroughputGauge />
                    </div>
                    <div className="rounded-xl border border-infra-700 p-4 bg-infra-900 lg:col-span-3">
                      <div className="text-[10px] font-mono text-infra-400 mb-2 uppercase tracking-wider">Causality Chain</div>
                      <CausalityTimeline />
                    </div>
                  </div>
                </ErrorBoundary>
              )}

              {activeTab === 'machines' && (
                <ErrorBoundary>
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                    <StateMachineViewer
                      machine={kafkaBrokerMachine}
                      title="Kafka Broker"
                      events={[
                        { label: 'Start', event: { type: 'START' } },
                        { label: 'Crash', event: { type: 'CRASH' } },
                        { label: 'Restart', event: { type: 'RESTART' } },
                        { label: 'ISR Shrink', event: { type: 'ISR_SHRINK', size: 1 } },
                        { label: 'ISR Expand', event: { type: 'ISR_EXPAND', size: 3 } },
                        { label: 'Rebalance', event: { type: 'REBALANCE' } },
                        { label: 'Recover', event: { type: 'RECOVER' } },
                        { label: 'Fail', event: { type: 'FAIL' } },
                      ]}
                    />
                    <StateMachineViewer
                      machine={kubernetesPodMachine}
                      title="Kubernetes Pod"
                      events={[
                        { label: 'Schedule', event: { type: 'SCHEDULE', node: 'node-1' } },
                        { label: 'Pull Image', event: { type: 'PULL_IMAGE' } },
                        { label: 'Start', event: { type: 'START_CONTAINER' } },
                        { label: 'Ready', event: { type: 'READY' } },
                        { label: 'Crash', event: { type: 'CRASH' } },
                        { label: 'Restart', event: { type: 'RESTART' } },
                        { label: 'Evict', event: { type: 'EVICT' } },
                        { label: 'Fail', event: { type: 'FAIL' } },
                      ]}
                    />
                    <StateMachineViewer
                      machine={tcpConnectionMachine}
                      title="TCP Connection"
                      events={[
                        { label: 'SYN', event: { type: 'SYN' } },
                        { label: 'SYN-ACK', event: { type: 'SYN_ACK' } },
                        { label: 'ACK', event: { type: 'ACK' } },
                        { label: 'Send Data', event: { type: 'DATA' } },
                        { label: 'FIN', event: { type: 'FIN' } },
                        { label: 'RST', event: { type: 'RST' } },
                        { label: 'Timeout', event: { type: 'TIMEOUT' } },
                        { label: 'Packet Loss', event: { type: 'LOSS' } },
                      ]}
                    />
                  </div>
                </ErrorBoundary>
              )}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      <footer className="flex items-center justify-between px-5 py-2 border-t border-infra-700 bg-infra-900">
        <div className="flex items-center gap-4 text-[10px] font-mono text-infra-400">
          <span className="flex items-center gap-1">
            <span className={`w-1.5 h-1.5 rounded-full ${running ? 'bg-accent-green' : 'bg-infra-500'}`} />
            {running ? 'Running' : 'Paused'}
          </span>
          <span>Stack: React + PixiJS + ReactFlow + XState + Zustand + ECharts</span>
        </div>
        <div className="text-[10px] font-mono text-infra-500">
          md-courses interactive platform
        </div>
      </footer>
    </div>
  )
}

export default App
