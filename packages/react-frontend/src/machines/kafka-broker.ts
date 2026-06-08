import { setup } from 'xstate'

export const kafkaBrokerMachine = setup({
  types: {} as {
    context: {
      brokerId: number
      partitionCount: number
      leaderCount: number
      isrSize: number
      underReplicated: number
      bytesInPerSec: number
      bytesOutPerSec: number
    }
    events:
      | { type: 'START' }
      | { type: 'CRASH' }
      | { type: 'RESTART' }
      | { type: 'ELECTION' }
      | { type: 'ISR_SHRINK'; size: number }
      | { type: 'ISR_EXPAND'; size: number }
      | { type: 'REBALANCE' }
      | { type: 'RECOVER' }
      | { type: 'FAIL' }
    input: { brokerId?: number }
  },
  actions: {
    resetMetrics: () => {},
    updateIsr: () => {},
    startRebalance: () => {},
  },
}).createMachine({
  id: 'kafka-broker',
  initial: 'stopped',
  context: ({ input }: { input?: { brokerId?: number } }) => ({
    brokerId: input?.brokerId ?? 1,
    partitionCount: 6,
    leaderCount: 2,
    isrSize: 3,
    underReplicated: 0,
    bytesInPerSec: 0,
    bytesOutPerSec: 0,
  }),
  states: {
    stopped: {
      on: { START: 'healthy' },
    },
    healthy: {
      entry: 'resetMetrics',
      on: {
        CRASH: 'dead',
        ISR_SHRINK: { target: 'degraded', actions: 'updateIsr' },
        REBALANCE: 'rebalancing',
      },
    },
    degraded: {
      on: {
        CRASH: 'dead',
        ISR_SHRINK: { actions: 'updateIsr' },
        ISR_EXPAND: { target: 'healthy', actions: 'updateIsr' },
        REBALANCE: 'rebalancing',
        FAIL: 'critical',
      },
    },
    critical: {
      on: {
        CRASH: 'dead',
        RECOVER: { target: 'degraded' },
        REBALANCE: 'rebalancing',
      },
    },
    rebalancing: {
      entry: 'startRebalance',
      on: {
        RECOVER: { target: 'healthy' },
        FAIL: 'critical',
        CRASH: 'dead',
      },
    },
    dead: {
      on: {
        RESTART: { target: 'healthy', actions: 'resetMetrics' },
      },
    },
  },
})
