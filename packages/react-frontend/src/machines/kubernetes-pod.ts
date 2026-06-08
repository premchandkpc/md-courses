import { setup } from 'xstate'

export const kubernetesPodMachine = setup({
  types: {} as {
    context: {
      podName: string
      nodeName: string
      namespace: string
      restarts: number
      cpuUsage: number
      memoryUsage: number
      ready: boolean
    }
    events:
      | { type: 'SCHEDULE'; node: string }
      | { type: 'PULL_IMAGE' }
      | { type: 'START_CONTAINER' }
      | { type: 'READY' }
      | { type: 'FAIL' }
      | { type: 'CRASH' }
      | { type: 'RESTART' }
      | { type: 'EVICT' }
      | { type: 'DELETE' }
      | { type: 'UPDATE' }
    input: { podName?: string; namespace?: string }
  },
  actions: {
    assignNode: () => {},
    markReady: () => {},
    incrementRestarts: () => {},
  },
}).createMachine({
  id: 'kubernetes-pod',
  initial: 'pending',
  context: ({ input }: { input?: { podName?: string; namespace?: string } }) => ({
    podName: input?.podName ?? 'pod-unknown',
    nodeName: '',
    namespace: input?.namespace ?? 'default',
    restarts: 0,
    cpuUsage: 0,
    memoryUsage: 0,
    ready: false,
  }),
  states: {
    pending: {
      on: {
        SCHEDULE: { target: 'scheduled', actions: 'assignNode' },
        FAIL: 'failed',
        DELETE: 'terminated',
      },
    },
    scheduled: {
      on: {
        PULL_IMAGE: 'imagePulling',
        FAIL: 'failed',
      },
    },
    imagePulling: {
      on: {
        START_CONTAINER: 'containerCreating',
        FAIL: 'imagePullBackoff',
      },
    },
    containerCreating: {
      on: {
        READY: { target: 'running', actions: 'markReady' },
        FAIL: 'crashLoopBackoff',
        CRASH: 'crashLoopBackoff',
      },
    },
    running: {
      entry: 'markReady',
      on: {
        CRASH: 'crashLoopBackoff',
        UPDATE: { target: 'scheduled' },
        FAIL: 'failed',
        EVICT: 'evicted',
        DELETE: 'terminated',
      },
    },
    crashLoopBackoff: {
      on: {
        RESTART: { target: 'containerCreating', actions: 'incrementRestarts' },
        FAIL: 'failed',
        DELETE: 'terminated',
      },
    },
    imagePullBackoff: {
      on: {
        PULL_IMAGE: 'imagePulling',
        DELETE: 'terminated',
      },
    },
    evicted: {
      on: {
        SCHEDULE: { target: 'scheduled', actions: 'assignNode' },
        DELETE: 'terminated',
      },
    },
    failed: {
      on: {
        RESTART: { target: 'pending' },
        DELETE: 'terminated',
      },
    },
    terminated: { type: 'final' },
  },
})
