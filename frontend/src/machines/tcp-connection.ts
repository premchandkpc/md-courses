import { setup } from 'xstate'

export const tcpConnectionMachine = setup({
  types: {} as {
    context: {
      srcPort: number
      dstPort: number
      seqNum: number
      ackNum: number
      congestionWindow: number
      ssthresh: number
      rtt: number
      retransmissions: number
      packetsInFlight: number
    }
    events:
      | { type: 'SYN' }
      | { type: 'SYN_ACK' }
      | { type: 'ACK' }
      | { type: 'DATA' }
      | { type: 'FIN' }
      | { type: 'RST' }
      | { type: 'TIMEOUT' }
      | { type: 'LOSS' }
      | { type: 'SLOW_START' }
      | { type: 'CONGESTION_AVOID' }
      | { type: 'FAST_RECOVERY' }
  },
}).createMachine({
  id: 'tcp-connection',
  initial: 'closed',
  context: ({ input }: { input?: { srcPort?: number; dstPort?: number } }) => ({
    srcPort: input?.srcPort ?? 40000,
    dstPort: input?.dstPort ?? 80,
    seqNum: 0,
    ackNum: 0,
    congestionWindow: 1,
    ssthresh: 65535,
    rtt: 0,
    retransmissions: 0,
    packetsInFlight: 0,
  }),
  states: {
    closed: {
      on: { SYN: 'synSent' },
    },
    synSent: {
      on: {
        SYN_ACK: 'established',
        RST: 'closed',
        TIMEOUT: 'closed',
      },
    },
    established: {
      initial: 'slowStart',
      states: {
        slowStart: {
          on: {
            LOSS: { target: 'fastRecovery', actions: 'handleLoss' },
            CONGESTION_AVOID: 'congestionAvoidance',
          },
        },
        congestionAvoidance: {
          on: {
            LOSS: { target: 'fastRecovery', actions: 'handleLoss' },
            SLOW_START: 'slowStart',
          },
        },
        fastRecovery: {
          on: {
            SLOW_START: 'slowStart',
            CONGESTION_AVOID: 'congestionAvoidance',
          },
        },
      },
      on: {
        DATA: { actions: 'incrementSeq' },
        FIN: 'finWait1',
        RST: 'closed',
      },
    },
    finWait1: {
      on: {
        ACK: 'finWait2',
        RST: 'closed',
      },
    },
    finWait2: {
      on: {
        FIN: 'timeWait',
        RST: 'closed',
      },
    },
    timeWait: {
      on: {
        ACK: 'closed',
      },
    },
  },
})
